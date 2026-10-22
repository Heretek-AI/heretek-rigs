#!/usr/bin/env python3
"""policy-verifier.py — stage-time policy-text verifier (issue #41).

Parse-only, offline: policy authored as text (lint tables, workflow commands)
is validated at stage time, before the enforcing gate first runs, so defects
like the W1-03 ``cast_lossy`` unknown lint hide no longer.

Two policy-text classes, one invocation (REQ-P1 + REQ-P2, REQ-P3):

(a) Lint-table names vs the toolchain. Every staged TOML's
    ``[workspace.lints.*]`` / ``[lints.*]`` entries MUST name a lint the
    pinned toolchain provides. The authority is a checked-in known-lint
    snapshot (``--known-lints``) carrying the toolchain pin it was taken
    from — never whatever happens to be installed on the runner, so results
    are deterministic and reviewable as a diff. ``--pin-file`` defaults to
    the checked-in toolchain pin, so a mismatch between the snapshot pin
    and the repo toolchain pin fails as a stale snapshot on EVERY
    invocation, not only when a pin flag is passed explicitly.

(b) Workflow ``run:`` steps vs package scripts. Every staged
    pipeline/workflow ``run:`` step invoking ``pnpm|npm|yarn <name>`` MUST
    resolve ``<name>`` to a ``scripts`` entry in a staged ``package.json``
    (same package or workspace root). A ``run:`` command that duplicates what
    a package script already names (``pnpm eslint .`` where ``lint`` exists)
    MUST fail citing the script — the step should invoke the script instead.
    Every ``cargo <args>`` step MUST start with a known cargo subcommand or
    a ``[alias]`` from a staged ``.cargo/config.toml``.

Anything else fails closed: unknown lint names, unresolvable ``run:``
references, unreadable policy TOML/YAML, missing snapshot, or a stale
snapshot pin are non-zero exits naming the file and line. ``PATH`` is never
consulted, no network is touched, no ``node_modules``/``target`` probing —
the defect class is "text nothing executes is text nothing checks", so the
check is manifest-text-only. The verifier never edits policy files.

Usage:
  policy-verifier.py [--known-lints FILE] [--expect-pin PIN | --pin-file FILE]
                     [--staged] [PATH ...]

  PATH entries are files or directories. Directories are walked for
  ``package.json``, ``*.toml`` and workflow YAML (under a ``workflows`` /
  ``pipelines`` / ``.github/workflows`` directory); ``node_modules``,
  ``.git`` and build-output trees are never descended. With ``--staged``
  the git index (``git diff --cached``) supplies the file list and blob
  contents, so the check runs at stage time before QA handoff. With no
  PATH and no ``--staged``, the current directory tree is scanned.

Exit codes: 0 = every policy reference resolves; 1 = unknown lint /
unresolvable run: reference / unreadable policy file / missing or stale
snapshot; 2 = usage or environment error (unknown snapshot file, git
failure). Sections below map to specs/policy-verifier/spec.md:
REQ-P1 lint names, REQ-P2 run: resolution, REQ-P3 single command/offline/
fail-closed, REQ-P4 additive gating (this file plus one make target plus
one verify-rigs.sh block; no existing check renumbered).

The small shell-tokenizer below intentionally mirrors the splitting rules
of scripts/manifest-closure.py instead of importing it: the two gates must
stay separately invokable (design.md), so a Wave-40 refactor can never
silently change Wave-41 verdicts. Shared shape, separate verdicts.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_KNOWN_LINTS = SCRIPT_DIR / "policy-verifier.known-lints.txt"
DEFAULT_PIN_FILE = SCRIPT_DIR / "policy-verifier.toolchain-pin"

# REQ-P2: package-manager prefixes whose remainder is a workspace script
# reference. `npx` is deliberately excluded: it executes binaries, which is
# the manifest-closure (#40) domain; this verifier resolves script names.
PM_MANAGERS = {"pnpm", "npm", "yarn"}
PM_SKIP_FLAGS = {
    "--filter": True,
    "-F": True,
    "--workspace": True,
    "-w": True,
    "--dir": True,
    "-C": True,
}
# pnpm/npm/yarn built-in subcommands: these invoke the manager itself, never
# a workspace script.
PM_BUILTINS = {
    "install",
    "add",
    "remove",
    "uninstall",
    "update",
    "upgrade",
    "run",
    "exec",
    "fetch",
    "store",
    "audit",
    "publish",
    "pack",
    "info",
    "view",
    "list",
    "ls",
    "outdated",
    "prune",
    "dedupe",
    "link",
    "unlink",
    "init",
    "login",
    "logout",
    "whoami",
    "config",
    "set",
    "get",
    "delete",
    "bin",
    "root",
    "prefix",
    "cache",
    "doctor",
}
# pnpm/npm/yarn default lifecycle commands: if a same-named workspace
# script exists the manager runs it; if not, the manager's own default
# command applies. Either way there is no UNRESOLVABLE SCRIPT finding.
PM_DEFAULT_COMMANDS = {
    "test",
    "start",
    "stop",
    "restart",
}
# Short manager aliases, verified against the documented alias sets
# (npm/pnpm/yarn `t` runs the `test` script). Kept to this named set only.
PM_ALIASES = {
    "t": "test",
}
# GitHub Actions `${{ ... }}` expression placeholder (REQ-P2): replaced
# BEFORE splitting so expressions containing shell separators stay single
# tokens. Scope is `${{ }}` only — `$VAR`/tokenize behavior untouched.
GH_EXPR_RE = re.compile(r"\$\{\{.*?\}\}")
GH_EXPR_PLACEHOLDER = "__GH_EXPR__"
# One-shot execution subcommands fetch without a pinned backing script.
ONE_SHOT_SUBCOMMANDS = {"dlx", "x"}

# REQ-P2: cargo subcommands the reconciled workflow (and everyday use)
# relies on. Stable toolchain surface, not guessed project state; anything
# else must come from a staged `.cargo/config.toml` [alias] or fail.
KNOWN_CARGO_SUBCOMMANDS = {
    "build",
    "test",
    "check",
    "clippy",
    "fmt",
    "run",
    "doc",
    "new",
    "init",
    "add",
    "remove",
    "update",
    "publish",
    "install",
    "uninstall",
    "search",
    "login",
    "logout",
    "package",
    "clean",
    "metadata",
    "tree",
    "vendor",
    "verify-project",
    "generate-lockfile",
    "locate-project",
    "pkgid",
    "yank",
    "owner",
    "bench",
    "rustc",
    "rustdoc",
    "fix",
    "report",
    "help",
}

# Lint-table tools this verifier qualifies (mirrors the cargo lint-table
# namespace; anything else in a lints position fails as an unknown tool).
LINT_TOOLS = {"clippy", "rust", "rustc", "rustdoc"}

# Directories never descended during a tree walk.
SKIP_DIRS = {
    "node_modules",
    ".git",
    "target",
    "dist",
    "build",
    "__pycache__",
    ".venv",
}


class PolicyError(Exception):
    """A single fail-closed finding (exit 1 class)."""


def split_segments(body):
    """Split a script/run body on shell chaining operators.

    Join backslash-newline continuations BEFORE splitting, and skip the
    remainder of a line when an unquoted `#` begins a word (shell comment
    to EOL). Quote-aware: operators inside single/double quotes never
    split. Unbalanced quotes fall back to treating the rest of the body as
    one segment rather than mis-splitting.
    """
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\\\n", "")
    segments = []
    current = []
    quote = None
    i = 0
    while i < len(normalized):
        ch = normalized[i]
        if quote:
            current.append(ch)
            if ch == "\\" and quote == '"':
                if i + 1 < len(normalized):
                    current.append(normalized[i + 1])
                    i += 1
            elif ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            current.append(ch)
        elif ch == "#":
            prior = "".join(current)
            if not prior or prior[-1] in (" ", "\t", ";", "|", "&", "(", "`"):
                while i < len(normalized) and normalized[i] != "\n":
                    i += 1
                continue
            current.append(ch)
        elif ch in ("\n", ";", "|", "&"):
            segments.append("".join(current))
            current = []
            while i + 1 < len(normalized) and normalized[i + 1] in ("|", "&"):
                i += 1
        else:
            current.append(ch)
        i += 1
    segments.append("".join(current))
    return [s.strip() for s in segments if s.strip()]


def _is_env_assignment(token):
    if "=" not in token or token.startswith(("-", ".", "/", "@")):
        return False
    name, _, _ = token.partition("=")
    return bool(name) and name[0].isalpha() and name.replace("_", "").isalnum()


def tokenize(segment):
    """Split a segment into shell tokens, dropping env/redirection noise."""
    try:
        raw = shlex.split(segment, posix=True)
    except ValueError:
        raw = segment.split()
    tokens = []
    skip_next = False
    for token in raw:
        if skip_next:
            skip_next = False
            continue
        if token in (">", ">>", "<", "<<", ">&", "&>"):
            skip_next = True
            continue
        if re.fullmatch(r"\d*", token) and token != "":
            continue
        if token.startswith(">") or token.startswith("<"):
            continue
        if token == "2>&1" or token.endswith(">&1"):
            continue
        if token.startswith("${{") or token.startswith("$") or token == "}}":
            continue
        if _is_env_assignment(token):
            continue
        tokens.append(token)
    return tokens


def normalize_command(text):
    """Collapse whitespace so equivalent commands compare equal."""
    return " ".join(text.split())


TABLE_RE = re.compile(r"^\s*\[([^\]#]+)\]\s*(?:#.*)?$")
KEY_RE = re.compile(r"^\s*([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*=")


def _table_parts(header):
    return [p.strip().strip("'\"") for p in header.strip().split(".")]


def scan_lint_entries(text, origin):
    """Yield (tool, name, lineno) for lint-table entries (REQ-P1).

    Line numbers come from a text scan (tomllib reports no positions);
    every entry is cross-checked against the parsed document so text inside
    comments or string literals can never report a finding. Unparseable
    TOML raises PolicyError (fail closed).
    """
    try:
        doc = tomllib.loads(text)
    except Exception as exc:
        raise PolicyError(f"UNREADABLE POLICY '{origin}' (invalid TOML: {exc})")
    if not isinstance(doc, dict):
        raise PolicyError(f"UNREADABLE POLICY '{origin}' (not a TOML table)")
    entries = []
    current = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        table_match = TABLE_RE.match(line)
        if table_match:
            current = _table_parts(table_match.group(1))
            continue
        key_match = KEY_RE.match(line)
        if not key_match or current is None:
            continue
        raw_key = key_match.group(1)
        tool = name = None
        if len(current) == 3 and current[0] == "workspace" and current[1] == "lints":
            tool, name = current[2], raw_key
        elif len(current) == 2 and current[0] == "lints":
            tool, name = current[1], raw_key
        elif (
            len(current) == 2
            and current[0] == "workspace"
            and current[1] == "lints"
            and "." in raw_key
        ):
            maybe_tool, _, maybe_name = raw_key.partition(".")
            tool, name = maybe_tool, maybe_name
        elif len(current) == 1 and current[0] == "lints" and "." in raw_key:
            maybe_tool, _, maybe_name = raw_key.partition(".")
            tool, name = maybe_tool, maybe_name
        if tool is None:
            continue
        # Cross-check against the parsed document: the table and the key
        # must really exist there (kills comment/string false positives).
        node = doc
        for part in current:
            if not isinstance(node, dict) or part not in node:
                node = None
                break
            node = node[part]
        if not isinstance(node, dict):
            continue
        first, _, _ = raw_key.partition(".")
        if first not in node and raw_key not in node:
            continue
        entries.append((tool, name, lineno))
    return entries


RUN_RE = re.compile(r"^(?P<indent>\s*)(?:-\s*)?run\s*:(?P<rest>.*)$")
BLOCK_SCALAR_RE = re.compile(r"^\s*[|>][+-]?\s*(?:#.*)?$")


def scan_run_steps(text, origin):
    """Yield (lineno, run body) pairs from workflow YAML (REQ-P2).

    A regex line scan (not a YAML parse) preserves exact file:line
    diagnostics for every ``run:`` body shape. Both inline
    (``run: pnpm lint``) and block-scalar (``run: |``) bodies are
    collected. Structural validity is enforced separately by
    ``check_workflow`` via ``yaml.safe_load`` (fail closed), so this
    scanner only runs on well-formed documents.
    """
    try:
        lines = text.splitlines()
    except Exception as exc:
        raise PolicyError(f"UNREADABLE WORKFLOW '{origin}' ({exc})")
    steps = []
    i = 0
    while i < len(lines):
        match = RUN_RE.match(lines[i])
        if not match:
            i += 1
            continue
        lineno = i + 1
        rest = match.group("rest").strip()
        if BLOCK_SCALAR_RE.match(match.group("rest")):
            key_indent = lines[i].index("run")
            body_lines = []
            j = i + 1
            while j < len(lines):
                candidate = lines[j]
                if not candidate.strip():
                    j += 1
                    continue
                indent = len(candidate) - len(candidate.lstrip())
                if indent <= key_indent:
                    break
                body_lines.append(candidate.strip())
                j += 1
            body = "\n".join(body_lines)
            i = j
        else:
            body = rest
            # Inline `run:` quoting: remove ONE matching pair of outer
            # single/double quotes so `run: "pnpm lint"` checks the command,
            # not the quotes. Interior (YAML-escaped) quotes are preserved.
            # Block-scalar bodies never pass through here — untouched.
            if len(body) >= 2 and (
                (body.startswith('"') and body.endswith('"'))
                or (body.startswith("'") and body.endswith("'"))
            ):
                body = body[1:-1]
            i += 1
        if body and not body.lstrip().startswith("#"):
            steps.append((lineno, body))
    return steps


def parse_known_lints_text(text, origin):
    """Parse snapshot text (shared by worktree and git-index reads)."""
    pin = None
    names = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("pin:"):
            if pin is None:
                pin = stripped[4:].strip()
            continue
        names.add(stripped)
    if not names:
        raise PolicyError(
            f"MISSING KNOWN-LINT SNAPSHOT '{origin}' (no lint entries parsed)"
        )
    return pin, names


def _repo_relative(path_str):
    """Repo-relative path for --staged index reads, or None if outside."""
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if top.returncode != 0:
        return None
    toplevel = Path(top.stdout.strip())
    candidate = Path(path_str)
    try:
        absolute = (
            candidate.resolve()
            if candidate.is_absolute()
            else (Path.cwd() / candidate).resolve()
        )
    except OSError:
        return None
    try:
        return str(absolute.relative_to(toplevel.resolve()))
    except ValueError:
        return None


def _read_index_text(rel):
    """Return the git-index blob for a repo-relative path, or None."""
    try:
        shown = subprocess.run(
            ["git", "show", f":{rel}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise PolicyError(f"STAGED SCAN FAILED (git unavailable: {exc})")
    if shown.returncode != 0:
        return None
    return shown.stdout


def _is_tracked(rel):
    try:
        proc = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", rel],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise PolicyError(f"STAGED SCAN FAILED (git unavailable: {exc})")
    return proc.returncode == 0


def load_indexed_text_or_worktree(path_str, kind):
    """Authority text for --staged runs: the git INDEX blob wins.

    The snapshot and pin are stage-time authorities, so in --staged mode
    they must reflect what is staged, not unstaged worktree edits. When
    the path maps to a tracked repo file the index blob
    (``git show :<path>``) is authoritative; when the path is untracked
    or outside the repo the worktree file is used. A tracked-but-
    unreadable index blob fails closed. Worktree/index divergence is
    resolved in favour of the index (documented, no silent worktree
    influence on staged validation).
    """
    rel = _repo_relative(path_str)
    if rel is None:
        return None
    indexed = _read_index_text(rel)
    if indexed is not None:
        return indexed
    if _is_tracked(rel):
        raise PolicyError(
            f"UNREADABLE POLICY '{path_str}' (cannot read indexed {kind} blob; "
            "failing closed rather than falling back to the worktree)"
        )
    return None


def load_known_lints(path):
    """Load the known-lint snapshot (REQ-P1 authority) from the worktree."""
    try:
        text = Path(path).read_text()
    except OSError as exc:
        raise PolicyError(
            f"MISSING KNOWN-LINT SNAPSHOT '{path}' ({exc}; refusing to "
            "resolve lint names against the local toolchain)"
        )
    return parse_known_lints_text(text, path)


def load_known_lints_staged(path_str):
    """Load the snapshot for --staged runs: the git INDEX blob wins."""
    indexed = load_indexed_text_or_worktree(path_str, "snapshot")
    if indexed is not None:
        return parse_known_lints_text(indexed, f"{path_str} (git index)")
    return load_known_lints(path_str)


def parse_toolchain_pin_text(text, origin):
    """Parse pin text: TOML channel first, else first non-comment line."""
    try:
        doc = tomllib.loads(text)
        channel = doc.get("toolchain", {}).get("channel")
        if isinstance(channel, str) and channel.strip():
            return channel.strip()
    except Exception:
        pass
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    raise PolicyError(f"UNREADABLE TOOLCHAIN PIN '{origin}' (empty)")


def read_toolchain_pin(pin_file):
    """Read the repo toolchain pin (plain text or rust-toolchain.toml).

    `#` comment lines are ignored so the pin file can carry a header
    documenting the manual refresh process.
    """
    try:
        text = Path(pin_file).read_text()
    except OSError as exc:
        raise PolicyError(f"UNREADABLE TOOLCHAIN PIN '{pin_file}' ({exc})")
    return parse_toolchain_pin_text(text, pin_file)


def read_toolchain_pin_staged(pin_file):
    """Read the pin for --staged runs: the git INDEX blob wins."""
    indexed = load_indexed_text_or_worktree(pin_file, "pin")
    if indexed is not None:
        return parse_toolchain_pin_text(indexed, f"{pin_file} (git index)")
    return read_toolchain_pin(pin_file)


def load_package_json(text, origin):
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PolicyError(f"UNREADABLE POLICY '{origin}' (invalid JSON: {exc})")
    if not isinstance(doc, dict):
        raise PolicyError(f"UNREADABLE POLICY '{origin}' (not an object)")
    return doc


def load_aliases(text, origin):
    """Collect cargo [alias] names from a .cargo/config.toml (REQ-P2)."""
    try:
        doc = tomllib.loads(text)
    except Exception as exc:
        raise PolicyError(f"UNREADABLE POLICY '{origin}' (invalid TOML: {exc})")
    aliases = doc.get("alias", {})
    if not isinstance(aliases, dict):
        return set()
    return {name for name in aliases if isinstance(name, str)}


class PolicyChecker:
    def __init__(self, known_lints):
        self.known_lints = known_lints
        self.findings = []
        self.packages = {}  # path string -> doc
        self.aliases = set()
        self.root_key = None
        self.files_checked = 0

    def note(self, message):
        self.findings.append(message)

    def add_package(self, path, doc):
        key = str(path)
        self.packages[key] = doc
        if self.root_key is None or len(Path(key).parts) < len(
            Path(self.root_key).parts
        ):
            self.root_key = key

    def script_names(self):
        names = {}
        for key, doc in self.packages.items():
            scripts = doc.get("scripts")
            if isinstance(scripts, dict):
                for name in scripts:
                    names.setdefault(name, key)
        # Workspace root first: a root script shadows same-named package
        # scripts for step resolution and duplicate citations.
        if self.root_key is not None and self.root_key in self.packages:
            root_scripts = self.packages[self.root_key].get("scripts") or {}
            if isinstance(root_scripts, dict):
                for name in root_scripts:
                    names[name] = self.root_key
        return names

    def script_bodies(self):
        bodies = []
        for key, doc in self.packages.items():
            scripts = doc.get("scripts")
            if isinstance(scripts, dict):
                for name, body in scripts.items():
                    if isinstance(body, str) and body.strip():
                        bodies.append((name, key, normalize_command(body)))
        return bodies

    def check_toml(self, path, text):
        self.files_checked += 1
        for tool, name, lineno in scan_lint_entries(text, path):
            qualified = f"{tool}::{name}"
            if tool not in LINT_TOOLS:
                self.note(
                    f"UNKNOWN LINT TOOL '{tool}' at {path}:{lineno} "
                    f"(lint table [{tool}] is not a known cargo lint tool)"
                )
            elif qualified not in self.known_lints and name not in self.known_lints:
                self.note(
                    f"UNKNOWN LINT '{qualified}' at {path}:{lineno} "
                    f"(no such lint in the pinned toolchain snapshot)"
                )

    def check_run_body(self, path, lineno, body):
        # GitHub `${{ ... }}` expressions become a non-dollar placeholder
        # BEFORE splitting, so separators inside an expression (e.g.
        # `${{ a || b }}`) never split the step. Diagnostics still cite the
        # original body text.
        sanitized = GH_EXPR_RE.sub(GH_EXPR_PLACEHOLDER, body)
        for segment in split_segments(sanitized):
            tokens = tokenize(segment)
            if not tokens:
                continue
            head = tokens[0]
            if head in PM_MANAGERS:
                self.check_pm_step(path, lineno, body, head, tokens[1:])
            elif head == "cargo":
                self.check_cargo_step(path, lineno, tokens[1:])
            else:
                # Bare commands belong to the manifest-closure (#40)
                # binary domain — except an exact duplicate of a package
                # script body, which this verifier owns (REQ-P2).
                normalized = normalize_command(segment)
                for script_name, _, script_body in self.script_bodies():
                    if normalized == script_body:
                        self.note(
                            f"DUPLICATE RUN COMMAND '{segment.strip()}' at "
                            f"{path}:{lineno} (package script '{script_name}' "
                            f"already names this command; use it instead)"
                        )
                        break

    def check_pm_step(self, path, lineno, body, manager, args):
        positional = []
        skip_next = False
        for token in args:
            if skip_next:
                skip_next = False
                continue
            if token in PM_SKIP_FLAGS:
                skip_next = True
                continue
            if token.startswith("-"):
                continue
            positional.append(token)
        while positional and positional[0] == "run":
            positional.pop(0)
        if not positional:
            return
        # `yarn workspace <name> <cmd>`: skip the workspace + name tokens
        # and resolve <cmd> as the script.
        if manager == "yarn" and positional[0] == "workspace":
            if len(positional) < 3:
                return
            positional = positional[2:]
        # Short aliases resolve to their canonical command first.
        if positional and positional[0] in PM_ALIASES:
            positional = [PM_ALIASES[positional[0]]] + positional[1:]
        if not positional:
            return
        head, rest = positional[0], positional[1:]
        # Dynamic script position (`pnpm ${{ matrix.script }}`): content
        # cannot be verified — skip the step with no finding.
        if head == GH_EXPR_PLACEHOLDER:
            return
        names = self.script_names()
        # Manager default commands: a same-named workspace script wins when
        # present; otherwise the manager's default applies. No finding
        # either way.
        if head in PM_DEFAULT_COMMANDS:
            return
        if head in PM_BUILTINS:
            return
        if head in ONE_SHOT_SUBCOMMANDS:
            self.note(
                f"UNRESOLVABLE SCRIPT '{head}' at {path}:{lineno} "
                f"(run: {body.strip()}; one-shot fetch without a pinned "
                f"package script)"
            )
            return
        if head in names:
            return
        remainder = normalize_command(" ".join([head] + rest))
        for script_name, _, script_body in self.script_bodies():
            if remainder == script_body:
                self.note(
                    f"DUPLICATE RUN COMMAND '{manager} {remainder}' at "
                    f"{path}:{lineno} (package script '{script_name}' "
                    f"already names this command; use "
                    f"`{manager} {script_name}` instead)"
                )
                return
        self.note(
            f"UNRESOLVABLE SCRIPT '{head}' at {path}:{lineno} "
            f"(run: {body.strip()}; no staged package.json scripts entry "
            f"names '{head}')"
        )

    def check_cargo_step(self, path, lineno, args):
        positional = [t for t in args if not t.startswith("-")]
        positional = [t for t in positional if not t.startswith("+")]
        if not positional:
            # Flag-only invocation (`cargo --version`): the toolchain
            # itself, nothing to resolve.
            return
        head = positional[0]
        # Dynamic subcommand position (`cargo ${{ matrix.tool }}`): content
        # cannot be verified — skip the step with no finding.
        if head == GH_EXPR_PLACEHOLDER:
            return
        if head in KNOWN_CARGO_SUBCOMMANDS or head in self.aliases:
            return
        self.note(
            f"UNKNOWN CARGO SUBCOMMAND '{head}' at {path}:{lineno} "
            f"(run: cargo {' '.join(args)}; not a known subcommand or "
            f"staged .cargo/config.toml alias)"
        )

    def check_workflow(self, path, text):
        self.files_checked += 1
        try:
            import yaml
        except ImportError:
            raise PolicyError(
                f"UNREADABLE WORKFLOW '{path}' (PyYAML unavailable for validation)"
            )
        try:
            yaml.safe_load(text)
        except Exception as exc:
            raise PolicyError(f"UNREADABLE WORKFLOW '{path}' (invalid YAML: {exc})")
        for lineno, body in scan_run_steps(text, path):
            self.check_run_body(path, lineno, body)


def discover_tree(root):
    """Walk a directory for policy files; never descends into SKIP_DIRS."""
    manifests, tomls, workflows = [], [], []
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            full = str(Path(current) / name)
            if name == "package.json":
                manifests.append(full)
            elif name.endswith(".toml"):
                tomls.append(full)
            elif name.endswith((".yml", ".yaml")) and (
                "workflows" in Path(full).parts or "pipelines" in Path(full).parts
            ):
                workflows.append(full)
    return manifests, tomls, workflows


def staged_files():
    """Return [(path, blob text)] for staged policy files (REQ-P4 hook)."""
    try:
        names = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise PolicyError(f"STAGED SCAN FAILED (git unavailable: {exc})")
    if names.returncode != 0:
        raise PolicyError(f"STAGED SCAN FAILED ({names.stderr.strip()})")
    selected = []
    for name in names.stdout.split("\0"):
        if not name:
            continue
        base = Path(name).name
        is_manifest = base == "package.json"
        is_toml = name.endswith(".toml")
        is_workflow = name.endswith((".yml", ".yaml")) and (
            "workflows" in Path(name).parts or "pipelines" in Path(name).parts
        )
        if is_manifest or is_toml or is_workflow:
            selected.append(name)
    blobs = []
    for name in selected:
        shown = subprocess.run(
            ["git", "show", f":{name}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if shown.returncode != 0:
            raise PolicyError(f"UNREADABLE POLICY '{name}' (cannot read staged blob)")
        blobs.append((name, shown.stdout))
    return blobs


def index_tracked_manifests(exclude):
    """Tracked context for --staged runs.

    Staging just a workflow must not lose the workspace-root manifest's
    script context, nor a committed `.cargo/config.toml`'s aliases. Both
    context classes join resolution but are never checked for findings
    themselves (no check_toml on config files here). Returns
    [(path, blob text)]; the caller routes package.json entries through
    add_package and config entries through load_aliases.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise PolicyError(f"STAGED SCAN FAILED (git unavailable: {exc})")
    if proc.returncode != 0:
        raise PolicyError(f"STAGED SCAN FAILED ({proc.stderr.strip()})")
    context = []
    for name in proc.stdout.split("\0"):
        if not name or name in exclude:
            continue
        is_manifest = Path(name).name == "package.json"
        is_cargo_config = (
            Path(name).name == "config.toml" and ".cargo" in Path(name).parts
        )
        if not (is_manifest or is_cargo_config):
            continue
        shown = subprocess.run(
            ["git", "show", f":{name}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if shown.returncode != 0:
            raise PolicyError(f"UNREADABLE POLICY '{name}' (cannot read indexed blob)")
        context.append((name, shown.stdout))
    return context


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Stage-time policy-text verifier (issue #41)."
    )
    parser.add_argument(
        "--known-lints",
        default=str(DEFAULT_KNOWN_LINTS),
        help="checked-in known-lint snapshot (default: scripts/ file)",
    )
    pin_group = parser.add_mutually_exclusive_group()
    pin_group.add_argument(
        "--expect-pin",
        default=None,
        help="repo toolchain pin the snapshot must carry",
    )
    pin_group.add_argument(
        "--pin-file",
        default=str(DEFAULT_PIN_FILE),
        help="file holding the repo toolchain pin (default: scripts/ "
        "policy-verifier.toolchain-pin, so every invocation enforces "
        "snapshot freshness)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="scan staged (git index) policy files instead of the worktree",
    )
    parser.add_argument("paths", nargs="*", help="files or directories to scan")
    args = parser.parse_args(argv)

    if args.staged and args.paths:
        print("--staged takes no PATH arguments", file=sys.stderr)
        return 2

    try:
        expect_pin = args.expect_pin
        if args.staged:
            # Stage-time authorities come from the git INDEX so unstaged
            # worktree edits cannot silently alter staged validation.
            if expect_pin is None and args.pin_file is not None:
                expect_pin = read_toolchain_pin_staged(args.pin_file)
            snapshot_pin, known_lints = load_known_lints_staged(args.known_lints)
        else:
            if expect_pin is None and args.pin_file is not None:
                expect_pin = read_toolchain_pin(args.pin_file)
            snapshot_pin, known_lints = load_known_lints(args.known_lints)
        if expect_pin is not None and snapshot_pin != expect_pin:
            print(
                f"policy-verifier: STALE KNOWN-LINT SNAPSHOT "
                f"'{args.known_lints}' (snapshot pin "
                f"'{snapshot_pin}' != repo toolchain pin "
                f"'{expect_pin}'; refresh the snapshot from the pinned "
                f"toolchain and re-run)",
                file=sys.stderr,
            )
            return 1
    except PolicyError as exc:
        print(f"policy-verifier: {exc}", file=sys.stderr)
        return 1

    checker = PolicyChecker(known_lints)

    try:
        if args.staged:
            staged = staged_files()
            if not staged:
                print("policy-verifier: no staged policy files; nothing to resolve.")
                return 0
            staged_names = {name for name, _ in staged}
            context = index_tracked_manifests(staged_names)
            manifests = [(n, t) for n, t in staged if Path(n).name == "package.json"]
            tomls = [(n, t) for n, t in staged if n.endswith(".toml")]
            workflows = [
                (n, t)
                for n, t in staged
                if n.endswith((".yml", ".yaml"))
                and ("workflows" in Path(n).parts or "pipelines" in Path(n).parts)
            ]
            for path, text in list(manifests) + context:
                if Path(path).name == "package.json":
                    checker.add_package(path, load_package_json(text, path))
                elif Path(path).name == "config.toml" and ".cargo" in Path(path).parts:
                    checker.aliases |= load_aliases(text, path)
            ordered = sorted(
                checker.packages,
                key=lambda p: (len(Path(p).parts), str(p)),
            )
            if ordered:
                checker.root_key = ordered[0]
            for path, text in tomls:
                checker.check_toml(path, text)
                if ".cargo" in Path(path).parts:
                    checker.aliases |= load_aliases(text, path)
            for path, text in workflows:
                checker.check_workflow(path, text)
        else:
            roots = args.paths or ["."]
            manifest_paths, toml_paths, workflow_paths = [], [], []
            for entry in roots:
                if Path(entry).is_file():
                    name = Path(entry).name
                    if name == "package.json":
                        manifest_paths.append(str(entry))
                    elif str(entry).endswith(".toml"):
                        toml_paths.append(str(entry))
                    elif str(entry).endswith((".yml", ".yaml")):
                        workflow_paths.append(str(entry))
                    else:
                        print(
                            f"policy-verifier: skipping non-policy file '{entry}'",
                            file=sys.stderr,
                        )
                elif Path(entry).is_dir():
                    m, t, w = discover_tree(str(entry))
                    manifest_paths += m
                    toml_paths += t
                    workflow_paths += w
                else:
                    print(
                        f"policy-verifier: no such file or directory '{entry}'",
                        file=sys.stderr,
                    )
                    return 2
            for path in sorted(manifest_paths):
                try:
                    with open(path, encoding="utf-8") as handle:
                        text = handle.read()
                except OSError as exc:
                    raise PolicyError(f"UNREADABLE POLICY '{path}' ({exc})")
                checker.add_package(path, load_package_json(text, path))
            ordered = sorted(
                checker.packages,
                key=lambda p: (len(Path(p).parts), str(p)),
            )
            if ordered:
                checker.root_key = ordered[0]
            for path in sorted(toml_paths):
                try:
                    with open(path, encoding="utf-8") as handle:
                        text = handle.read()
                except OSError as exc:
                    raise PolicyError(f"UNREADABLE POLICY '{path}' ({exc})")
                checker.check_toml(path, text)
                if ".cargo" in Path(path).parts:
                    checker.aliases |= load_aliases(text, path)
            for path in sorted(workflow_paths):
                try:
                    with open(path, encoding="utf-8") as handle:
                        text = handle.read()
                except OSError as exc:
                    raise PolicyError(f"UNREADABLE WORKFLOW '{path}' ({exc})")
                checker.check_workflow(path, text)
    except PolicyError as exc:
        print(f"policy-verifier: {exc}", file=sys.stderr)
        return 1

    if checker.findings:
        for finding in checker.findings:
            print(f"policy-verifier: {finding}", file=sys.stderr)
        print(
            f"policy-verifier: {len(checker.findings)} finding(s) in "
            f"{checker.files_checked} file(s); policy text does not resolve.",
            file=sys.stderr,
        )
        return 1
    print(
        f"policy-verifier: all {checker.files_checked} staged policy "
        f"file(s) resolve against the pinned authority."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
