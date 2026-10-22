#!/usr/bin/env python3
"""manifest-closure.py — stage-time manifest-closure lint (issue #40).

Parse-only, offline: every binary invoked by a staged ``package.json``
``scripts`` entry or a staged pipeline/workflow ``run:`` step MUST resolve to
a declared dependency (own or workspace-root manifest, own ``bin`` entries,
or a binary->package alias grounded below), or to an entry in the checked-in
operator-runner tool allowlist. Every staged ``tsconfig*.json`` ``types``
entry MUST resolve to a declared ``@types/<name>`` package or to a declared
package that ships its own types.

Anything else fails closed: non-zero exit naming the binary/package, the
invoking script or ``run:`` step, and the package it was found in. ``PATH``
is never consulted (the GLOBAL-eslint-10.11.0 leak class). No network, no
``node_modules`` probing — the defect class is "resolves by accident on this
machine", so the check is manifest-text-only.

Usage:
  manifest-closure.py [--allowlist FILE] [--staged] [PATH ...]

  PATH entries are files or directories. Directories are walked for
  ``package.json``, ``tsconfig*.json`` and workflow YAML (under a
  ``workflows`` / ``.github/workflows`` directory); ``node_modules``,
  ``.git`` and build-output trees are never descended. With ``--staged``
  the git index (``git diff --cached``) supplies the file list and blob
  contents, so the check runs at stage time before QA handoff. With no
  PATH and no ``--staged``, the current directory tree is scanned.

Exit codes: 0 = closure holds; 1 = undeclared binary / unreadable manifest /
indirection cycle; 2 = usage or environment error (unknown allowlist file,
git failure). Sections below map to specs/manifest-closure/spec.md:
REQ-C1 entry points, REQ-C2 resolution, REQ-C3 allowlist/fail-closed,
REQ-C5 tsconfig `types`.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ALLOWLIST = SCRIPT_DIR.parent / "fleet" / "allowed-system-tools.txt"

# REQ-C2(a): binaries whose npm package name differs from the bin name.
# Grounded read-only in the live fixed state (mission repo, 2026-10-22):
# `tsc` is provided by the `typescript` package (web/e2e/tests typecheck),
# `playwright` is provided by `@playwright/test` (e2e script). Everything
# else resolves by exact dep-name match (eslint, prettier, vite, vitest,
# turbo), so this table stays minimal and reviewable instead of guessing.
BIN_ALIASES = {
    "tsc": "typescript",
    "playwright": "@playwright/test",
}

# Package-manager prefixes whose remainder is a workspace script reference
# (REQ-C1). `run` is accepted after npm/yarn for `npm run <script>` shape.
PM_PREFIXES = {"pnpm", "npm", "yarn", "npx"}
PM_SKIP_FLAGS = {
    "--filter": True,
    "-F": True,
    "--workspace": True,
    "-w": True,
    "--dir": True,
    "-C": True,
}
# pnpm/npm/yarn built-in subcommands: these invoke the manager itself
# (which must be allowlisted), never a workspace script.
PM_BUILTINS = {
    "install",
    "add",
    "remove",
    "uninstall",
    "update",
    "upgrade",
    "run",
    "exec",
    "exe",
    "dln",
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
# One-shot execution subcommands: `pnpm dlx <pkg>` / `npx <pkg>` fetch
# without a pinned backing dependency — the classic hole. Always undeclared.
ONE_SHOT_SUBCOMMANDS = {"dlx", "x"}

# Shell builtins that can never be "declared" in a manifest; skipping them is
# not a hole (no package provides them, every runner shell supplies them).
SHELL_BUILTINS = {"cd", "echo"}

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

MAX_INDIRECTION_DEPTH = 32


class ClosureError(Exception):
    """A single fail-closed finding (exit 1 class)."""


def load_json_text(text, origin):
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ClosureError(f"UNREADABLE MANIFEST '{origin}' (invalid JSON: {exc})")


def read_text_file(path):
    try:
        return Path(path).read_text()
    except IsADirectoryError:
        raise ClosureError(f"UNREADABLE MANIFEST '{path}' (is a directory)")
    except FileNotFoundError:
        raise ClosureError(f"UNREADABLE MANIFEST '{path}' (not found)")
    except PermissionError as exc:
        raise ClosureError(f"UNREADABLE MANIFEST '{path}' ({exc})")
    except OSError as exc:
        raise ClosureError(f"UNREADABLE MANIFEST '{path}' ({exc})")


def split_segments(body):
    """Split a script/run body on shell chaining operators (REQ-C1).

    Quote-aware: operators inside single/double quotes (e.g. the `;` in
    `echo "a; b"`) never split. Unbalanced quotes fall back to treating
    the rest of the body as one segment rather than mis-splitting.
    """
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
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


def first_token(segment):
    """First meaningful token of a segment.

    Skips env assignments (`FOO=bar`), redirections (`2>&1`, `> file`)
    with their targets, fd numbers, and GitHub `${{ }}` expressions.
    Returns None when the segment invokes nothing checkable.
    """
    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        tokens = segment.split()
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if not token or token.startswith("$") or "${{" in token:
            return None
        if _is_env_assignment(token):
            continue
        if "<" in token or ">" in token:
            if token.rstrip().endswith((">", "<")) or re.fullmatch(
                r"\d*[<>]+&?\d*", token
            ):
                skip_next = True  # dangling operator: next token is its target
            continue
        if re.fullmatch(r"\d+", token):
            continue
        return token
    return None


def own_bin_names(pkg_doc):
    """Binary names the package itself provides via its `bin` field."""
    name = pkg_doc.get("name", "")
    short = name.split("/")[-1] if name else ""
    bins = set()
    bin_field = pkg_doc.get("bin")
    if isinstance(bin_field, str):
        if short:
            bins.add(short)
    elif isinstance(bin_field, dict):
        bins.update(bin_field.keys())
    return bins


def declared_names(pkg_doc, root_doc):
    """All dependency names visible to a package (own + workspace root)."""
    names = set()
    for doc in (pkg_doc, root_doc):
        if not isinstance(doc, dict):
            continue
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            section_map = doc.get(section)
            if isinstance(section_map, dict):
                names.update(section_map.keys())
    return names


def types_resolves(entry, pkg_doc, root_doc):
    """REQ-C5: a tsconfig `types` entry resolves iff @types/<entry> is
    declared, or the entry's own package is declared (ships its own types,
    e.g. `@playwright/test`, `vite/client` -> `vite`)."""
    if not isinstance(entry, str) or not entry:
        return False
    if entry.startswith("@types/"):
        wanted = {entry}
    else:
        head = entry.split("/")[0]
        if entry.startswith("@"):
            parts = entry.split("/")
            head = "/".join(parts[:2]) if len(parts) >= 2 else entry
        wanted = {f"@types/{entry}", f"@types/{head}", entry, head}
    return bool(wanted & declared_names(pkg_doc, root_doc))


def workflow_run_steps(yaml_text, origin):
    """Yield (job/step label, run body) pairs from workflow YAML."""
    try:
        import yaml
    except ImportError:
        raise ClosureError(f"UNREADABLE WORKFLOW '{origin}' (PyYAML unavailable)")
    try:
        doc = yaml.safe_load(yaml_text)
    except Exception as exc:
        raise ClosureError(f"UNREADABLE WORKFLOW '{origin}' ({exc})")
    if not isinstance(doc, dict):
        return
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            body = step.get("run")
            if isinstance(body, str) and body.strip():
                label = step.get("name") or step.get("id") or "run"
                yield f"{job_name}/{label}", body


class ClosureChecker:
    def __init__(self, allowlist):
        self.allowlist = set(allowlist)
        self.findings = []
        self.packages = {}  # Path -> doc
        self.root_doc = None
        self.entry_points = 0

    def note(self, message):
        self.findings.append(message)

    def add_package(self, path, doc):
        self.packages[Path(path)] = doc
        if self.root_doc is None or len(Path(path).parts) < len(
            getattr(self, "root_path", Path(path)).parts
        ):
            self.root_doc = doc
            self.root_path = Path(path)

    def binary_resolves(self, binary, pkg_doc):
        if binary in SHELL_BUILTINS:
            return True
        if binary in self.allowlist:
            return True
        if binary in declared_names(pkg_doc, self.root_doc):
            return True
        if binary in own_bin_names(pkg_doc):
            return True
        target = BIN_ALIASES.get(binary)
        if target and target in declared_names(pkg_doc, self.root_doc):
            return True
        return False

    def check_binary(self, binary, invoker, pkg_name, pkg_path):
        pkg_doc = self.packages.get(Path(pkg_path), {})
        if not self.binary_resolves(binary, pkg_doc):
            self.note(
                f"UNDECLARED BINARY '{binary}' (invoked by {invoker} "
                f"in package '{pkg_name}' {pkg_path})"
            )

    def resolve_pm_tokens(self, args, manager, invoker, pkg_name, pkg_path, chain):
        """Resolve tokens following a pnpm/npm/yarn/npx prefix (REQ-C1).

        `args` excludes the manager prefix itself. A head naming a workspace
        script recurses (cycle-checked); a manager built-in resolves to the
        manager binary (must be allowlisted); a one-shot subcommand (dlx/x)
        or an otherwise unknown head fails closed.
        """
        idx = 0
        while idx < len(args) and args[idx] == "run":
            idx += 1
        positional = []
        skip_next = False
        for token in args[idx:]:
            if skip_next:
                skip_next = False
                continue
            if token in PM_SKIP_FLAGS:
                skip_next = True
                continue
            if token.startswith("-"):
                continue
            positional.append(token)
        if not positional:
            return
        head, rest = positional[0], positional[1:]
        if head in ONE_SHOT_SUBCOMMANDS:
            if rest:
                self.note(
                    f"UNDECLARED ONE-SHOT PACKAGE '{rest[0]}' (invoked by "
                    f"{invoker} in package '{pkg_name}' {pkg_path}; "
                    f"npx/pnpm-dlx fetch without a pinned backing dependency)"
                )
            else:
                self.note(
                    f"UNDECLARED BINARY '{head}' (invoked by {invoker} "
                    f"in package '{pkg_name}' {pkg_path})"
                )
            return
        if head in PM_BUILTINS:
            self.check_binary(manager, invoker, pkg_name, pkg_path)
            return
        # Otherwise the head names a workspace script: recurse into every
        # package defining it (REQ-C1), failing closed on indirection
        # cycles (design.md fail-closed modes). Checking all definers is
        # the fail-closed direction: a second definer's body could invoke
        # an undeclared binary the first definer never touches.
        matched = False
        for path, doc in self.packages.items():
            scripts = doc.get("scripts")
            if not (isinstance(scripts, dict) and head in scripts):
                continue
            matched = True
            key = (str(path), head)
            if key in chain:
                trail = " -> ".join([f"{p}#{s}" for p, s in chain] + [f"{path}#{head}"])
                self.note(
                    f"INDIRECTION CYCLE '{head}' (script indirection cycle: "
                    f"{trail}; invoked by {invoker} in package "
                    f"'{pkg_name}' {pkg_path})"
                )
                continue
            self.check_script_body(
                scripts[head],
                f"script '{head}' ({invoker})",
                doc.get("name", "?"),
                str(path),
                chain + [key],
            )
        if not matched:
            self.check_binary(head, invoker, pkg_name, pkg_path)

    def check_script_body(self, body, invoker, pkg_name, pkg_path, chain):
        if len(chain) > MAX_INDIRECTION_DEPTH:
            trail = " -> ".join(f"{p}#{s}" for p, s in chain)
            self.note(
                f"INDIRECTION CYCLE/DEPTH EXCEEDED at {invoker} "
                f"in package '{pkg_name}' ({trail})"
            )
            return
        for segment in split_segments(body):
            binary = first_token(segment)
            if not binary:
                continue
            if binary in PM_PREFIXES:
                try:
                    tokens = shlex.split(segment, posix=True)
                except ValueError:
                    tokens = segment.split()
                self.resolve_pm_tokens(
                    tokens[1:], tokens[0], invoker, pkg_name, pkg_path, chain
                )
            elif binary == "cargo":
                # REQ-C2(c): cargo subcommands ride the toolchain's cargo.
                self.check_binary("cargo", invoker, pkg_name, pkg_path)
            else:
                self.check_binary(binary, invoker, pkg_name, pkg_path)

    def check_package(self, path, doc):
        pkg_name = doc.get("name", "?")
        scripts = doc.get("scripts")
        if isinstance(scripts, dict):
            for script_name, body in scripts.items():
                if not isinstance(body, str):
                    continue
                self.entry_points += 1
                self.check_script_body(
                    body,
                    f"script '{script_name}'",
                    pkg_name,
                    str(path),
                    [(str(path), script_name)],
                )

    def check_workflow(self, path, text):
        for label, body in workflow_run_steps(text, str(path)):
            self.entry_points += 1
            pkg_name = (
                self.root_doc.get("name", "workflow")
                if isinstance(self.root_doc, dict)
                else "workflow"
            )
            root_path = str(getattr(self, "root_path", path))
            self.check_script_body(
                body,
                f"run: step '{label}' in {Path(path).name}",
                pkg_name,
                root_path,
                [("workflow", label)],
            )

    def check_tsconfig(self, path, doc):
        if not isinstance(doc, dict):
            return
        entries = doc.get("compilerOptions", {})
        if not isinstance(entries, dict):
            return
        types_list = entries.get("types")
        if not isinstance(types_list, list):
            return
        pkg_doc = self.packages.get(Path(path).parent / "package.json", {})
        if not pkg_doc:
            # Nearest ancestor package owns this tsconfig.
            for candidate in reversed(Path(path).parents):
                if candidate / "package.json" in self.packages:
                    pkg_doc = self.packages[candidate / "package.json"]
                    break
        pkg_name = pkg_doc.get("name", "?") if pkg_doc else "?"
        for entry in types_list:
            self.entry_points += 1
            if not types_resolves(entry, pkg_doc, self.root_doc):
                wanted = f"@types/{entry}"
                self.note(
                    f"UNDECLARED TYPES ENTRY '{wanted}' (referenced by "
                    f"tsconfig '{path}' in package '{pkg_name}')"
                )

    def pkg_sort_key(self, path):
        return (len(Path(path).parts), str(path))


def discover_tree(root):
    """Walk a directory for manifests; never descends into SKIP_DIRS."""
    manifests, tsconfigs, workflows = [], [], []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune before descending: never enter dependency, VCS, or
        # build-output trees; keep .github so workflow YAML is discovered.
        dirnames[:] = [
            d
            for d in sorted(dirnames)
            if d not in SKIP_DIRS and (not d.startswith(".") or d == ".github")
        ]
        for filename in sorted(filenames):
            full = Path(dirpath) / filename
            if filename == "package.json":
                manifests.append(full)
            elif filename.startswith("tsconfig") and filename.endswith(".json"):
                tsconfigs.append(full)
            elif filename.endswith((".yml", ".yaml")) and "workflows" in full.parts:
                workflows.append(full)
    return manifests, tsconfigs, workflows


def staged_files():
    """Return [(path, blob text)] for staged manifests (REQ-C4 hook point)."""
    try:
        names = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ClosureError(f"STAGED SCAN FAILED (git unavailable: {exc})")
    if names.returncode != 0:
        raise ClosureError(f"STAGED SCAN FAILED ({names.stderr.strip()})")
    selected = []
    for name in names.stdout.split("\0"):
        if not name:
            continue
        base = Path(name).name
        is_manifest = base == "package.json"
        is_tsconfig = base.startswith("tsconfig") and base.endswith(".json")
        is_workflow = (
            name.endswith((".yml", ".yaml")) and "workflows" in Path(name).parts
        )
        if is_manifest or is_tsconfig or is_workflow:
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
            raise ClosureError(
                f"UNREADABLE MANIFEST '{name}' (cannot read staged blob)"
            )
        blobs.append((name, shown.stdout))
    return blobs


def load_allowlist(path):
    try:
        text = Path(path).read_text()
    except OSError as exc:
        raise ClosureError(
            f"MISSING ALLOWLIST '{path}' ({exc}; refusing to default-allow)"
        )
    entries = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            entries.add(stripped)
    if not entries:
        raise ClosureError(f"MISSING ALLOWLIST '{path}' (no entries parsed)")
    return entries


def check_loaded(checker, manifests, tsconfigs, workflows):
    for path, text in manifests:
        doc = load_json_text(text, str(path))
        if not isinstance(doc, dict):
            raise ClosureError(f"UNREADABLE MANIFEST '{path}' (not an object)")
        checker.add_package(path, doc)
    # Root = shallowest manifest (workspace root sees all deps, REQ-C2(b)).
    ordered = sorted(checker.packages, key=checker.pkg_sort_key)
    if ordered:
        checker.root_doc = checker.packages[ordered[0]]
        checker.root_path = ordered[0]
    for path in ordered:
        checker.check_package(path, checker.packages[path])
    for path, text in workflows:
        checker.check_workflow(path, text)
    for path, text in tsconfigs:
        # Follow relative `extends` so a `types` entry in a base config is
        # still attributed (bare-package extends stay with the tsc gate).
        chain = [(path, text)]
        seen = {str(path)}
        merged_types = None
        merged_doc = None
        while chain:
            current, current_text = chain.pop()
            doc = load_json_text(current_text, str(current))
            if not isinstance(doc, dict):
                raise ClosureError(f"UNREADABLE MANIFEST '{current}' (not an object)")
            if merged_doc is None:
                merged_doc = doc
                compiler = doc.get("compilerOptions")
                if isinstance(compiler, dict) and isinstance(
                    compiler.get("types"), list
                ):
                    merged_types = list(compiler["types"])
            extends = doc.get("extends")
            if (
                isinstance(extends, str)
                and (extends.startswith(".") or extends.startswith("/"))
                and merged_types is None
            ):
                candidate = (Path(current).parent / extends).resolve()
                if candidate.suffix != ".json":
                    candidate = Path(str(candidate) + ".json")
                if str(candidate) not in seen and candidate.exists():
                    seen.add(str(candidate))
                    chain.append((candidate, read_text_file(candidate)))
        if merged_doc is not None and merged_types is not None:
            probe = {"compilerOptions": {"types": merged_types}}
            checker.check_tsconfig(path, probe)
        elif merged_doc is not None:
            checker.check_tsconfig(path, merged_doc)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Stage-time manifest-closure lint (issue #40)."
    )
    parser.add_argument("paths", nargs="*", help="files or directories to scan")
    parser.add_argument(
        "--allowlist",
        default=str(DEFAULT_ALLOWLIST),
        help="checked-in operator-runner tool allowlist",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="scan staged (git index) manifests instead of the worktree",
    )
    args = parser.parse_args(argv)

    try:
        allowlist = load_allowlist(args.allowlist)
    except ClosureError as exc:
        print(exc, file=sys.stderr)
        return 2

    checker = ClosureChecker(allowlist)
    try:
        if args.staged:
            if args.paths:
                print("--staged takes no PATH arguments", file=sys.stderr)
                return 2
            staged = staged_files()
            manifests = [
                (name, text)
                for name, text in staged
                if Path(name).name == "package.json"
            ]
            tsconfigs = [
                (name, text)
                for name, text in staged
                if Path(name).name.startswith("tsconfig") and name.endswith(".json")
            ]
            workflows = [
                (name, text)
                for name, text in staged
                if name.endswith((".yml", ".yaml"))
            ]
            if not manifests and not tsconfigs and not workflows:
                print("manifest-closure: no staged manifests; zero undeclared.")
                return 0
            check_loaded(checker, manifests, tsconfigs, workflows)
        else:
            roots = [Path(p) for p in args.paths] if args.paths else [Path.cwd()]
            manifests, tsconfigs, workflows = [], [], []
            for root in roots:
                if not root.exists():
                    print(f"SCAN PATH MISSING '{root}'", file=sys.stderr)
                    return 2
                if root.is_file():
                    name = root.name
                    text = read_text_file(root)
                    if name == "package.json":
                        manifests.append((str(root), text))
                    elif name.startswith("tsconfig") and name.endswith(".json"):
                        tsconfigs.append((str(root), text))
                    elif name.endswith((".yml", ".yaml")):
                        workflows.append((str(root), text))
                    else:
                        print(f"SCAN PATH NOT A MANIFEST '{root}'", file=sys.stderr)
                        return 2
                else:
                    found = discover_tree(root)
                    manifests.extend((str(p), read_text_file(p)) for p in found[0])
                    tsconfigs.extend((str(p), read_text_file(p)) for p in found[1])
                    workflows.extend((str(p), read_text_file(p)) for p in found[2])
            if not manifests and not tsconfigs and not workflows:
                print("manifest-closure: no manifests found; zero undeclared.")
                return 0
            check_loaded(checker, manifests, tsconfigs, workflows)
    except ClosureError as exc:
        print(exc, file=sys.stderr)
        return 1

    if checker.findings:
        for finding in checker.findings:
            print(finding)
        print(
            f"manifest-closure: {len(checker.findings)} undeclared "
            f"reference(s) across {checker.entry_points} entry point(s)."
        )
        return 1
    print(
        f"manifest-closure: {checker.entry_points} entry point(s) checked; "
        "zero undeclared."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
