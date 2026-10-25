#!/usr/bin/env python3
"""render-seat.py — Render one Pi seat's isolated agentDir for OpenRig + OpenCode Go.

Renders into $OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent/ (all files mode 0600):
  1. auth.json: command-backed API key ("!cat <SECRETS>/opencode-go.key"), never a literal secret.
  2. models.json: OpenCode Go provider definition (api: openai-responses, model: muse-spark-1.3-contributor).
  3. mcp.json: Pi built-in MCP config from fleet/mcp-servers.yaml with @TOOLS@, @SECRETS@, @SEAT@ resolved.
  4. settings.json: defaultProvider, defaultModel, defaultThinkingLevel, defaultTools, packages, quietStartup.
  5. extensions/pi-permission-system/config.json: fail-closed @gotgenes/pi-permission-system@41.0.0 rules with
     mandatory "*..*": "deny" placed LAST in path_write and path, read-only AST/LSP tools allowed where configured,
     and mutating AST/LSP tools (code_rewrite, lsp_rename, lsp_code_actions) explicitly denied.
  6. AGENTS.md: Role charter from specs/agents/<domain>/<role>/guidance/role.md plus seat address & escalation block
     (avoiding OpenRig's shared-<cwd> guidance_merge collision).
"""

import os
import shutil
import sys

try:
    import yaml
except ImportError:
    if shutil.which("uv") and not os.environ.get("_HERETEK_UV_REEXEC"):
        os.environ["_HERETEK_UV_REEXEC"] = "1"
        os.execvp(
            "uv",
            [
                "uv",
                "run",
                "--quiet",
                "--with",
                "pyyaml",
                "--with",
                "jsonschema",
                "python3",
                *sys.argv,
            ],
        )
    raise

import argparse
import json
import re
import shlex
from pathlib import Path

USAGE = """usage: render-seat.py --role <role-id> --rig <rig-id> --pod <pod-id> [options]
  --member <id>            member id in the rig (default: the role id)
  --fleet <file>           default fleet/fleet.yaml
  --mcp <file>             default fleet/mcp-servers.yaml
  --charter <file>         default specs/agents/<domain>/<role>/guidance/role.md
  --out <dir>              default $OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent
  --model-provider <p>     default opencode-go (tests use: mock)
  --model-id <id>          default muse-spark-1.3-contributor (tests use: mock-model)
  --allow-missing-secrets  write servers whose secret files are missing with "enabled": false
  --dry-run                print the rendered files as JSON instead of writing them
  --help"""

READONLY_AST_LSP_TOOLS = [
    "ast_grep",
    "ast_search",
    "code_overview",
    "lsp_diagnostics",
    "lsp_hover",
    "lsp_definition",
    "lsp_references",
    "lsp_symbols",
    "lsp_completions",
]

MUTATING_AST_LSP_TOOLS = [
    "code_rewrite",
    "lsp_rename",
    "lsp_code_actions",
]

# S2a/M9 (#69, #72): single source of truth for the terminal bash denies
# emitted LAST into every seat's bash map (last-match-wins) and mirrored in
# scripts/verify-rigs.sh `_TERMINAL_BASH_DENIES`. verify-rigs V13 asserts the
# two tuples are ordered-identical, so weakening either side flips the gate.
TERMINAL_BASH_DENIES = (
    "*--output=*",
    "*--output *",
    "*--output\t*",
    "*--output-junit*",
    "*--output-log*",
    "*;*",
    "*|*",
    "*>*",
    "*<*",
    "*&*",
    "*`*",
    "*$*",
    "*(*",
    "*)*",
    "* -p*",
    "*\t-p*",
    "*--patch*",
    "*--full-diff*",
    "*--textconv*",
    # M5 (#69) git-diff read-bypass family: -u/-U/--unified/--cc and
    # the spaced -c/-m/-W flag forms plus git's word/binary/raw
    # diff-output flags (same last-match-wins rationale as -p).
    "* -u*",
    "*\t-u*",
    "* -U*",
    "*\t-U*",
    "*--unified*",
    "*--cc*",
    "* -c *",
    "*\t-c *",
    "* -c\t*",
    "*\t-c\t*",
    "* -m *",
    "*\t-m *",
    "* -m\t*",
    "*\t-m\t*",
    "* -W*",
    "*\t-W*",
    "*--function-context*",
    "*--word-diff*",
    "*--color-words*",
    "*--binary*",
    "*--raw*",
    # M5 (#72/#93) identity-forgery forms: a leading VAR= assignment is
    # stripped by pps before matching (F9), so this catches only the
    # `env VAR=...` form at the policy layer; the leading-assignment
    # form is closed in scripts/send-authenticated.sh instead.
    "*OPENRIG_SESSION_NAME=*",
    "*OPENRIG_URL=*",
)


# #106 commandEffects overlay (REQ-C1/C2): declarative allow-effects for two
# `rig queue` argv positions. The terminal bash denies above stay frozen
# (REQ-G1) — the overlay scopes the exception to these argv positions and
# never loosens a deny. Scope roots stay cwd-relative descriptors (never
# baked absolute host paths: the #67 worktree-stale lesson). Enforcement
# points re-check at use time; every error denies (fail-closed, REQ-C3).
NOTE_VALUE_PATTERN = r"^[A-Za-z0-9 _\-/.:|]+$"
NOTE_VALUE_RE = re.compile(NOTE_VALUE_PATTERN)
BODY_FILE_MAX_BYTES = 262144
BODY_FILE_SCRATCH_RE = re.compile(r"^/var/tmp/seatjail\.\d+(?:/.*)?$")
NOTE_VALUE_DENY_TOKENS = (
    ";",
    "$",
    "`",
    "$(",
    "OPENRIG_SESSION_NAME=",
    "OPENRIG_URL=",
)


def is_note_value_allowed(value) -> bool:
    """REQ-C1: `--note` single-argv value allows literal `| / . - _ :` plus
    alphanumerics and space, never as shell control (argv, not `sh -c`)."""
    if not isinstance(value, str) or not value:
        return False
    if "\n" in value or "\r" in value:
        return False
    for tok in NOTE_VALUE_DENY_TOKENS:
        if tok in value:
            return False
    return NOTE_VALUE_RE.fullmatch(value) is not None


def _expanded_scope_roots(cwd_resolved: str, path_write) -> list:
    """REQ-C2 scope roots: realpath(cwd) plus each path_write entry's
    literal base resolved under cwd. Glob-only entries collapse onto the
    cwd root; `..`/absolute entries are skipped (fail-closed)."""
    roots = []
    if cwd_resolved:
        roots.append(cwd_resolved.rstrip("/") or "/")
    for entry in path_write or []:
        e = str(entry)
        if e.startswith("/") or ".." in e.split("/"):
            continue
        base = e
        cut = len(base)
        for i, ch in enumerate(base):
            if ch in "*?[":
                cut = i
                break
        base = base[:cut].rstrip("/")
        if "/" in base:
            base = base.rsplit("/", 1)[0]
        else:
            base = ""
        if not base:
            continue
        cand = os.path.normpath(os.path.join(cwd_resolved, base))
        if cand not in roots:
            roots.append(cand)
    return roots


def classify_body_file(
    raw_path: str,
    *,
    cwd_resolved: str,
    expanded_roots: list,
    is_regular_file: bool,
    size_bytes,
    resolved_path,
) -> tuple:
    """REQ-C2/C3 pure verdict: (verdict, reason) with verdict in
    {"allow-effect", "deny"}. Scope-resolution error, missing file,
    oversize, symlink escape, `..` escape, and absolute /tmp all deny."""
    if not raw_path or not resolved_path:
        return ("deny", "scope-resolution error or missing file")
    if not is_regular_file:
        return ("deny", "not a regular file")
    if size_bytes is None or size_bytes > BODY_FILE_MAX_BYTES:
        return ("deny", "oversize or unknown size (limit 256KiB)")
    resolved = os.path.normpath(resolved_path)
    if BODY_FILE_SCRATCH_RE.match(resolved):
        return ("allow-effect", "pid-namespaced scratch scope")
    for root in expanded_roots or []:
        r = os.path.normpath(root)
        if resolved == r or resolved.startswith(r.rstrip("/") + "/"):
            return ("allow-effect", "in-scope root")
    if resolved == "/tmp" or resolved.startswith("/tmp/"):
        return ("deny", "absolute /tmp path outside scope")
    return ("deny", "outside own scope")


def check_body_file_path(raw_path: str, *, cwd: str, path_write) -> tuple:
    """REQ-C2 filesystem check (fail-closed): realpath + regular-file +
    size + scope. Best-effort at check time; enforcement rechecks at use."""
    import stat as _stat

    if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path:
        return ("deny", "empty or invalid path")
    try:
        cwd_resolved = os.path.realpath(cwd)
    except OSError:
        return ("deny", "scope-resolution error (cwd)")
    try:
        resolved = os.path.realpath(raw_path)
    except OSError:
        return ("deny", "scope-resolution error or missing file")
    try:
        st = os.stat(resolved)
    except OSError:
        return ("deny", "scope-resolution error or missing file")
    roots = _expanded_scope_roots(cwd_resolved, path_write)
    return classify_body_file(
        raw_path,
        cwd_resolved=cwd_resolved,
        expanded_roots=roots,
        is_regular_file=_stat.S_ISREG(st.st_mode),
        size_bytes=st.st_size,
        resolved_path=resolved,
    )


def build_command_effects(path_write) -> list:
    """REQ-C1/C2 declarative overlay rendered into every seat's permission
    output. Role-specific write roots ride along as descriptors only."""
    return [
        {
            "id": "note-effect",
            "argv": ["rig", "queue", "--note"],
            "match": {
                "position": "single-argv-value",
                "pattern": NOTE_VALUE_PATTERN,
                "execModel": "argv-not-shell",
            },
            "covers": [
                "rig queue create --note",
                "rig queue block --note",
                "rig queue update --reopen --note",
                "park-typed-block.py relay",
                "sweep-typed-blocks.py relay",
            ],
            "denyWhen": list(NOTE_VALUE_DENY_TOKENS) + ["newline", "carriage-return"],
            "effect": "allow-effect",
        },
        {
            "id": "body-file-effect",
            "argv": ["rig", "queue", "--body-file"],
            "scope": {
                "cwd": "realpath(CWD)",
                "writeRootsSource": "permissions.path_write",
                "writeRoots": list(path_write or []),
                "scratch": "/var/tmp/seatjail.<pid>.*",
            },
            "constraints": {
                "regularFileOnly": True,
                "maxBytes": BODY_FILE_MAX_BYTES,
                "noSymlinkEscape": True,
                "noDotDotEscape": True,
                "noAbsoluteTmp": True,
            },
            "covers": [
                "rig queue create --body-file",
                "send-authenticated.sh --source staged relay",
            ],
            "effect": "allow-effect-if-in-scope-else-deny",
        },
    ]


def _sandbox_bind_roots(path_write):
    """Map pps path_write globs to jail write roots (M4, #68; #105 review).

    The bubblewrap wrapper (scripts/seat-sandbox.sh) reads two entry kinds:
    a pure directory grant (`src/*`, `tests/chaos/*`) becomes `src/`, which
    is bound read-write; anything else (`package.json`, `docs/*.md`,
    `*package-lock.json`) stays a file pattern, and only EXISTING regular
    files matching it are bound in place. Nothing ever maps to the whole
    seat cwd. pi-permission-system remains the fine-grained gate; the jail
    adds cwd-containment, no network, and masked secret stores.
    """
    roots = []
    for entry in path_write or []:
        e = entry
        if e.endswith("/*") and not any(c in e[:-2] for c in "*?["):
            e = e[:-2].rstrip("/") + "/"
        if e in ("", "/", "./"):
            continue
        if e not in roots:
            roots.append(e)
    return roots


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


# provisioning-gate-74 (#74, REQ-P1/P4): read-only existence gate for bound
# tool artifacts. Resolution is shutil.which + path-exists ONLY — no
# installs, no pulls, no network. Factors shared by scripts/render-seat.py
# (render time) and scripts/seed-rig.py (stage time) so both layers degrade
# with the same warn shape. Never silent: unresolvable artifacts always warn.
def resolve_tool_artifact(command: str) -> tuple:
    """Resolve one MCP `command` value read-only.

    Absolute paths must be executable on disk (shutil.which requires
    executability for slash-paths too); bare names must resolve via
    shutil.which (same PATH the seat will see). The trimmed command is
    treated as ONE complete executable path (no whitespace split; args
    live in args:, never in command:). Returns (ok, artifact)
    where artifact is the command path that was checked.
    """
    if not isinstance(command, str) or not command.strip():
        return (False, str(command))
    first = command.strip()
    if Path(first).is_absolute():
        return (shutil.which(first) is not None, first)
    if "/" in first:
        return (shutil.which(first) is not None, first)
    return (shutil.which(first) is not None, first)


def bash_leading_binary(pattern: str):
    """Leading binary of a bash_allow pattern, or None when the pattern is
    a glob/deny form (leading token starts with a glob/metachar) or empty.
    A trailing glob suffix (e.g. `rabin2*`) is cut: the binary is the
    literal prefix. Callers resolve the returned binary with shutil.which."""
    if not isinstance(pattern, str) or not pattern.strip():
        return None
    first = pattern.strip().split()[0]
    if not first:
        return None
    cut = len(first)
    for i, ch in enumerate(first):
        if ch in "*?[]{}()$`;&|<>'\"!#~\\":
            cut = i
            break
    candidate = first[:cut]
    if not candidate:
        return None
    if "/" in candidate:
        return None
    return candidate


def build_seat_files(
    role_id: str,
    rig_id: str,
    pod_id: str,
    member_id: str,
    fleet_data: dict,
    mcp_catalog: dict,
    tools_dir: str,
    secrets_dir: str,
    seat_dir: str,
    charter_text: str,
    model_provider: str = "opencode-go",
    model_id: str = "muse-spark-1.3-contributor",
    allow_missing_secrets: bool = False,
    check_secret_fs: bool = True,
    sandbox_wrapper: str | None = None,
) -> dict:
    if role_id not in fleet_data.get("roles", {}):
        die(f"unknown role {role_id}")
    role = fleet_data["roles"][role_id]

    # HR-4.2 (fail-closed): --pod must be a real pod of --rig (fleet/fleet.yaml
    # is canonical). A phantom pod (e.g. --pod command --rig
    # executive-and-architecture, whose pods are exec/delivery) must die here
    # instead of rendering a seat no bootstrap target will ever materialize.
    _valid_pods = set()
    for _r in fleet_data.get("rigs", []):
        if _r.get("id") == rig_id:
            for _p in _r.get("pods", []):
                if _p.get("id"):
                    _valid_pods.add(_p["id"])
    _omni = fleet_data.get("omni", {})
    if rig_id == _omni.get("id", "heretek-omni-fleet"):
        _cp = _omni.get("core_pod", {})
        if _cp.get("id"):
            _valid_pods.add(_cp["id"])
        for _f in _omni.get("pod_fragments", []):
            if _f.get("pod"):
                _valid_pods.add(_f["pod"])
    if _valid_pods and pod_id not in _valid_pods:
        die(
            f"unknown pod {pod_id!r} for rig {rig_id} (valid pods: {sorted(_valid_pods)})"
        )

    for ident in (pod_id, member_id):
        if re.search(r"[.@]", ident):
            die(f"pod/member ids must not contain '.' or '@': {ident}")

    session = f"{pod_id}-{member_id}@{rig_id}"
    pps_pkg = str(
        Path(tools_dir) / "pi-packages/node_modules/@gotgenes/pi-permission-system"
    )
    # #67 (fail-closed): the permission extension is mandatory — a missing or
    # version-drifted pps must die at render time, never render a seat whose
    # settings.json packages[0] points at nothing. There is NO
    # --allow-missing-secrets escape for this (unlike secrets).
    if check_secret_fs and not (Path(pps_pkg) / "package.json").is_file():
        die(f"{pps_pkg} missing: @gotgenes/pi-permission-system is mandatory")
    if check_secret_fs:
        _pps_ver = json.loads((Path(pps_pkg) / "package.json").read_text()).get(
            "version"
        )
        if _pps_ver != "41.0.0":
            die(f"{pps_pkg} version {_pps_ver}, need 41.0.0")

    def secret_ok(filename: str) -> bool:
        if not check_secret_fs:
            return False
        p = Path(secrets_dir) / filename
        # HR-4.3 (fail-closed): reject symlinks before stat (TOCTOU / link-swap).
        # A secrets dir containing a symlink must never be trusted — die loudly.
        if p.is_symlink():
            die(f"{p} must not be a symlink")
        if not p.exists():
            return False
        try:
            st = p.stat()
        except FileNotFoundError:
            return False
        # HR-4.3 (fail-closed): ownership pin — secret files must be owned by
        # the invoking user. Group/world-readable is already rejected below;
        # a file owned by another uid (e.g. planted via shared /tmp) must die.
        try:
            euid = os.geteuid()
        except AttributeError:
            euid = None  # Windows: no geteuid, skip ownership pin
        if euid is not None and st.st_uid != euid:
            die(f"{p} must be owned by uid {euid} (got {st.st_uid})")
        mode = st.st_mode & 0o777
        if mode & 0o077:
            die(f"{p} is mode {oct(mode)[2:]}; run: chmod 600 {p}")
        # HR-4.3 (fail-closed): O_NOFOLLOW open proves the path is still a
        # regular file at use time (stat-then-use race / symlink swap).
        try:
            fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except FileNotFoundError:
            return False
        except OSError:
            die(f"{p} cannot be opened safely (symlink/race)")
        else:
            os.close(fd)
        return True

    def subst(val):
        if isinstance(val, str):
            return (
                val.replace("@TOOLS@", tools_dir)
                .replace("@SECRETS@", secrets_dir)
                .replace("@SEAT@", seat_dir)
            )
        return val

    files = {}

    # 1. auth.json & models.json
    if model_provider == "opencode-go":
        has_key = secret_ok("opencode-go.key")
        if not has_key and not allow_missing_secrets:
            die(f"missing {Path(secrets_dir) / 'opencode-go.key'} (chmod 600)")
        # HR-4.3 (fail-closed): never emit a silent dangling `!cat` for the
        # primary provider key — under --allow-missing-secrets an absent key
        # renders `"enabled": false` plus a stderr warning (mirroring the mcp
        # deferred-server path), so the seat is visibly degraded instead of
        # pointing at a nonexistent secret. No literal is ever materialized.
        if has_key:
            files["auth.json"] = {
                "opencode-go": {
                    "type": "api_key",
                    "key": f"!cat {Path(secrets_dir) / 'opencode-go.key'}",
                }
            }
        else:
            if check_secret_fs:
                print(
                    f"warn: {session}: opencode-go.key missing, auth disabled",
                    file=sys.stderr,
                )
            files["auth.json"] = {
                "opencode-go": {
                    "type": "api_key",
                    "key": f"!cat {Path(secrets_dir) / 'opencode-go.key'}",
                    "enabled": False,
                }
            }
        files["models.json"] = {
            "providers": {
                "opencode-go": {
                    "api": "openai-responses",
                    "baseUrl": "https://opencode.ai/inference/go/v1",
                    "models": [
                        {
                            "id": "muse-spark-1.3-contributor",
                            "name": "Muse Spark 1.3 Contributor",
                            "reasoning": True,
                            "input": ["text", "image"],
                            "thinkingLevelMap": {
                                "off": None,
                                "minimal": "minimal",
                                "low": "low",
                                "medium": "medium",
                                "high": "high",
                                "xhigh": "xhigh",
                                "max": None,
                            },
                            "contextWindow": 1048576,
                            "maxTokens": 131072,
                            "cost": {
                                "input": 0.10,
                                "output": 0.20,
                                "cacheRead": 0.002,
                                "cacheWrite": 0,
                            },
                            "compat": {
                                "supportsDeveloperRole": True,
                                "sendSessionIdHeader": True,
                                "supportsLongCacheRetention": True,
                                "sessionAffinityFormat": "openai-nosession",
                            },
                        }
                    ],
                }
            }
        }

    # 2. mcp.json
    mcp_servers = {}
    mcp_allow = {"*": "deny"}
    deferred = False
    for b in role.get("mcp", []):
        srv_name = b["server"]
        if srv_name not in mcp_catalog:
            die(f"role {role_id} binds unknown MCP server {srv_name}")
        s = mcp_catalog[srv_name]
        need = s.get("required_secrets", [])
        missing = [f for f in need if not secret_ok(f)]
        toolset = b.get("toolset", "")
        entry = {
            "description": subst(s["description"]).replace("{toolset}", toolset),
            "exposure": s["exposure"],
        }
        if s["transport"] == "http":
            entry["url"] = s["url_template"].replace("{toolset}", toolset or "repos")
            entry["headers"] = {k: subst(v) for k, v in s.get("headers", {}).items()}
        else:
            entry["command"] = subst(s["command"])
            entry["args"] = [subst(x) for x in s.get("args", [])]
            if any(str(x).startswith("!") for x in entry["args"]):
                die(f"{srv_name}: Pi never expands !command in args")
            if "env" in s:
                entry["env"] = {k: subst(v) for k, v in s["env"].items()}

        for opt_sec in s.get("optional_secrets", []):
            if not secret_ok(opt_sec) and "env" in entry:
                for k in list(entry["env"].keys()):
                    if opt_sec in str(entry["env"][k]):
                        del entry["env"][k]

        if missing:
            if not allow_missing_secrets:
                missing_paths = ", ".join(str(Path(secrets_dir) / f) for f in missing)
                die(f"{srv_name} needs {missing_paths}")
            entry["enabled"] = False
            if check_secret_fs:
                print(
                    f"warn: {session}: {srv_name} disabled, missing secrets: {', '.join(missing)}",
                    file=sys.stderr,
                )

        # provisioning-gate-74 (#74, REQ-P1/P4): read-only render-time
        # resolution of the bound stdio command (remote-http servers carry
        # no command and are excluded). Unresolvable entries render
        # enabled:false AND warn naming server, seat, and artifact — never
        # silent (mirrors the degraded-secrets path above).
        if s["transport"] != "http" and "command" in s:
            _ok74, _art74 = resolve_tool_artifact(entry.get("command", ""))
            if not _ok74:
                entry["enabled"] = False
                # CodeQL py/clear-text-logging-sensitive-data: log the raw
                # catalog template token (e.g. @TOOLS@/bin/r2mcp), never the
                # substituted absolute path derived from secrets/tools dirs.
                _raw74 = str(s.get("command", "")).strip().split()
                _raw74 = _raw74[0] if _raw74 else ""
                print(
                    f"warn: {session}: {srv_name} disabled, missing tool artifact: {_raw74}",
                    file=sys.stderr,
                )

        mcp_servers[srv_name] = entry
        mcp_allow[srv_name] = "allow"
        if s["exposure"] == "deferred":
            deferred = True

    files["mcp.json"] = {"mcpServers": mcp_servers}

    # 3. settings.json
    tools = ["read", "grep", "find", "ls", "bash", "edit", "write"]
    if deferred:
        tools.append("tool_search")

    packages = [pps_pkg]
    role_pkgs = role.get("pi_packages", ["@gotgenes/pi-permission-system@41.0.0"])
    has_ast_lsp = any(
        p.startswith(
            (
                "pi-lsp-extension",
                "pi-ast-grep",
                "@narumitw/pi-lsp",
                "@nicknisi/pi-ast-grep",
            )
        )
        for p in role_pkgs
    )
    for pkg in role_pkgs:
        if pkg.startswith("@gotgenes/pi-permission-system"):
            continue
        pkg_name = (
            pkg.split("@")[0]
            if not pkg.startswith("@")
            else "@" + pkg[1:].split("@")[0]
        )
        candidate = Path(tools_dir) / "pi-packages/node_modules" / pkg_name
        if candidate.exists():
            packages.append(str(candidate))

    files["settings.json"] = {
        "defaultProvider": model_provider,
        "defaultModel": model_id,
        "defaultThinkingLevel": role["thinking"],
        "defaultTools": tools,
        "packages": packages,
        "quietStartup": True,
        # M4 (#68): route pi's bash tool through the bubblewrap jail. A
        # missing shellPath fails closed (no /bin/bash fallback), and the
        # wrapper must sit outside every seat's write scope (Gotcha 5).
        # Generated reference leaves pass the `@RIGS@` placeholder so they
        # never depend on where the repo is checked out (#105 review).
        "shellPath": sandbox_wrapper
        or str(Path(__file__).resolve().parent / "seat-sandbox.sh"),
    }

    # M4 (#68): per-seat sandbox env for the wrapper. The pi-runner child env
    # is deny-by-default (no HERETEK_* crosses into the pi agent process),
    # but PI_CODING_AGENT_DIR always points at this agent dir, so the wrapper
    # loads sandbox.env from there (see scripts/seat-sandbox.sh bootstrap).
    _bind_roots = _sandbox_bind_roots(role["permissions"]["path_write"])
    files["sandbox.env"] = (
        f"HERETEK_SANDBOX_WRITE={shlex.quote(':'.join(_bind_roots))}\n"
        f"HERETEK_SECRET_STORE={shlex.quote(secrets_dir)}\n"
    )

    # 4. extensions/pi-permission-system/config.json
    # Last matching rule wins inside each map; guards MUST go LAST.
    path_write = {"*": "deny"}
    for g in role["permissions"]["path_write"]:
        path_write[g] = "allow"
    for guard_k in (
        ".git/*",
        "*/.git/*",
        "AGENTS.md",
        "*/AGENTS.md",
        ".pi/*",
        "*/.pi/*",
        ".agents/*",
        "*/.agents/*",
        "fleet/*",
        "scripts/*",
        "*..*",
    ):
        path_write.pop(guard_k, None)
        path_write[guard_k] = "deny"

    bash_map = {"*": "deny"}
    for p in role["permissions"]["bash_allow"]:
        # HR-5.5 (fail-closed): never emit a shell-metachar allowlist entry —
        # `; & | $` backticks, parens, newlines, redirections (`>`, `<`),
        # backslash, `!`, `#`, `~`, braces, brackets, `?`, or CR could chain
        # out of a trailing-* prefix under prefix-glob matcher semantics.
        if re.search(r"[;&|$`()\n><\\!#~{}\[\]?\r]", p) or "$(" in p:
            die(f"{role_id}: bash_allow pattern contains shell metachar: {p!r}")
        # HR-5.5-render-output-allow (fail-closed): `--output=` smuggles a file
        # write past path_write under prefix-glob matcher semantics — reject at
        # generation time, not only in the verifier (direct render-seat.py use
        # must never materialize the escape).
        if "--output" in p:
            die(
                f"{role_id}: bash_allow pattern contains forbidden --output write-escape: {p!r}"
            )
        bash_map[p] = "allow"
    # HR-5.5 (fail-closed): prefix-glob matcher semantics — a live command
    # appending `--output=/tmp/x` (or `;`, `|`, `>`, `<`, `&`, backtick,
    # `$()`, subshell parens) to an allowed trailing-* prefix would still
    # match the allow prefix under prefix-glob matcher semantics. Terminal
    # deny rules placed LAST (last-match-wins, same as path_write/path guards)
    # ensure any command containing those substrings is denied even when it
    # starts with an allowed prefix. Legitimate allows contain none of these
    # substrings (fleet verified metachar-free), so the clean fleet renders
    # unchanged except for these added terminal denies. Newline (`\n`) cannot
    # be expressed as a portable glob and stays covered by the generation-time
    # metachar die above plus Pi's own compound-command decomposition
    # (docs/OSINT_ECOSYSTEM_REPORT.md gate probes); live `&`/backtick/`$()`
    # semantics remain UNVERIFIED pending a hostile-corpus run through the
    # installed @gotgenes/pi-permission-system@41.0.0 (HR-5.5-enforcement-gap).
    # HR-5.5-git-patch-read-bypass (fail-closed): patch-output flags smuggle
    # full file contents past path read-denies under prefix-glob matcher
    # semantics (e.g. `git log --oneline -p -- fleet/fleet.yaml` matches the
    # `git log --oneline*` allow while `fleet/*` stays `"deny"` in `path`).
    # Deny the patch-output flag family LAST for the same reason. Residual
    # (documented, P3): `--stat`/`--name-only` output is metadata-only (no
    # file contents); path-qualified git commands such as
    # `git show --stat HEAD -- fleet/fleet.yaml` still match their allow
    # prefix. Blast radius stays capped at tracked content — secrets live
    # untracked in $HERETEK_SECRETS (4.3/4.4) and the `*.env`/`*id_rsa*`
    # direct-read denies still hold.
    # HR-5.5-tab-p-suffix-gap (fail-closed): `* -p*` is space-anchored, so a
    # tab-separated `git log --oneline<TAB>-p` matches the allow but no deny
    # under last-match-wins substring-glob semantics. The `"*\t-p*"` tab
    # variant closes the gap (JSON `\t` decodes to TAB at match time).
    # S2a/M9: the deny tuple lives in module-level TERMINAL_BASH_DENIES
    # (single source of truth, asserted identical to the verify-rigs
    # mirror in V13).
    for _deny_pat in TERMINAL_BASH_DENIES:
        bash_map[_deny_pat] = "deny"
    # provisioning-gate-74 (#74, REQ-P1/P4): read-only render-time
    # resolution of each bash_allow leading binary (r2/rabin2/tshark and
    # friends). Missing binaries warn naming seat, grant, and artifact —
    # never silent. The allow entry is kept (policy unchanged): the warn is
    # the loud degradation, and provisioning the binary silences it.
    for p in role["permissions"]["bash_allow"]:
        _bin74 = bash_leading_binary(p)
        if _bin74 is not None and shutil.which(_bin74) is None:
            print(
                f"warn: {session}: bash grant {p!r} missing tool artifact: {_bin74}",
                file=sys.stderr,
            )

    permission = {
        "*": "deny",
        "read": "allow",
        "grep": "allow",
        "find": "allow",
        "ls": "allow",
        "write": "allow",
        "edit": "allow",
    }
    if has_ast_lsp:
        for t_ro in READONLY_AST_LSP_TOOLS:
            permission[t_ro] = "allow"
    for t_mut in MUTATING_AST_LSP_TOOLS:
        permission[t_mut] = "deny"
    if deferred:
        permission["tool_search"] = "allow"

    permission["bash"] = bash_map
    permission["path"] = {
        "*": "allow",
        "*.env": "deny",
        "*.env.*": "deny",
        "*.env.example": "allow",
        "*.pem": "deny",
        "*.key": "deny",
        "*id_rsa*": "deny",
        "*kubeconfig*": "deny",
        "*/secrets/*": "deny",
        # HR-5.2 (fail-closed): the same dot-directory/file guard block as
        # path_write — reads of .git/.pi/.agents metadata, seat charters, and
        # the fleet toolchain itself must deny (live corpus: gate-role.sh
        # .pi/.agents read probes). Guards sit before terminal "*..*".
        ".git/*": "deny",
        "*/.git/*": "deny",
        "AGENTS.md": "deny",
        "*/AGENTS.md": "deny",
        ".pi/*": "deny",
        "*/.pi/*": "deny",
        ".agents/*": "deny",
        "*/.agents/*": "deny",
        "fleet/*": "deny",
        "scripts/*": "deny",
        # HR-5.3 (fail-closed): explicit denies for every secret-filename suffix
        # in fleet/mcp-servers.yaml so coverage never depends on the secrets
        # dir containing a `/secrets/` segment (default $HERETEK_SECRETS has none).
        "*.pat": "deny",
        "*.uri": "deny",
        "*.profile": "deny",
        "*.region": "deny",
        "*.host": "deny",
        "*.password": "deny",
        "*.credentials": "deny",
        "*.config": "deny",
        # HR-5.3 (fail-closed): credential-bearing URL/user filename suffixes
        # (e.g. prometheus.url, clickhouse.user) must never be readable even
        # outside any */secrets/* path.
        "*.url": "deny",
        "*.user": "deny",
        "*..*": "deny",
    }
    permission["path_write"] = path_write
    permission["mcp"] = mcp_allow
    permission["external_directory"] = "deny"

    files["extensions/pi-permission-system/config.json"] = {
        "promptTimeoutMs": 60000,
        "permission": permission,
        "commandEffects": build_command_effects(role["permissions"]["path_write"]),
    }

    # 5. AGENTS.md: role charter + seat block (never use guidance_merge on shared cwd)
    esc = role.get("reports_to")
    esc_line = (
        f'- Escalate with: `rig send {esc["address"]} "<message>"` ({esc["role"]}{", same rig" if esc.get("same_rig") else ", other rig"}).'
        if esc
        else "- You are the top of the escalation chain; escalate to the human."
    )
    writable_str = (
        ", ".join(f"`{g}`" for g in role["permissions"]["path_write"]) or "none"
    )
    addr_block = "\n".join(
        [
            "## Seat",
            "",
            f"- You are `{role_id}` in seat `{session}` (rig `{rig_id}`, pod `{pod_id}`).",
            f"- Model: {model_provider}/{model_id}, thinking {role['thinking']}. Recorded policy: {role['permission_policy']}.",
            esc_line,
            f"- Writable paths: {writable_str}. Everything else is read-only.",
            "",
        ]
    )
    files["AGENTS.md"] = charter_text.rstrip() + "\n\n" + addr_block
    return files


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(USAGE)
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--role")
    parser.add_argument("--rig")
    parser.add_argument("--pod")
    parser.add_argument("--member")
    parser.add_argument("--fleet", default="fleet/fleet.yaml")
    parser.add_argument("--mcp", default="fleet/mcp-servers.yaml")
    parser.add_argument("--charter")
    parser.add_argument("--out")
    parser.add_argument("--model-provider", default="opencode-go")
    parser.add_argument("--model-id", default="muse-spark-1.3-contributor")
    parser.add_argument("--allow-missing-secrets", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown:
        die(f"unknown arguments: {' '.join(unknown)}\n{USAGE}")
    for req in ("role", "rig", "pod"):
        if not getattr(args, req):
            die(f"--{req} is required\n{USAGE}")

    home = Path.home()
    openrig_home = Path(
        os.environ.get("OPENRIG_HOME", str(home / ".openrig"))
    ).resolve()
    tools_dir = str(
        Path(
            os.environ.get(
                "HERETEK_TOOLS", str(home / ".local/share/heretek-rigs/tools")
            )
        ).resolve()
    )
    secrets_dir = str(
        Path(
            os.environ.get(
                "HERETEK_SECRETS", str(home / ".config/heretek-rigs/secrets")
            )
        ).resolve()
    )

    fleet_data = yaml.safe_load(Path(args.fleet).read_text())
    mcp_catalog = yaml.safe_load(Path(args.mcp).read_text())["servers"]
    if args.role not in fleet_data.get("roles", {}):
        die(f"unknown role {args.role}")
    role = fleet_data["roles"][args.role]
    member_id = args.member or args.role
    session = f"{args.pod}-{member_id}@{args.rig}"
    seat_dir = str(openrig_home / "state/pi" / session)
    out_dir = Path(args.out).resolve() if args.out else Path(seat_dir) / "agent"
    charter_path = (
        Path(args.charter)
        if args.charter
        else Path("specs/agents") / role["domain"] / args.role / "guidance/role.md"
    )
    if not charter_path.exists():
        die(f"missing charter {charter_path}")

    files = build_seat_files(
        role_id=args.role,
        rig_id=args.rig,
        pod_id=args.pod,
        member_id=member_id,
        fleet_data=fleet_data,
        mcp_catalog=mcp_catalog,
        tools_dir=tools_dir,
        secrets_dir=secrets_dir,
        seat_dir=seat_dir,
        charter_text=charter_path.read_text(),
        model_provider=args.model_provider,
        model_id=args.model_id,
        allow_missing_secrets=args.allow_missing_secrets,
        check_secret_fs=True,
    )

    if args.dry_run:
        print(json.dumps(files, indent=2, ensure_ascii=False))
        return

    for rel, body in files.items():
        p = out_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        content = (
            body
            if isinstance(body, str)
            else json.dumps(body, indent=2, ensure_ascii=False) + "\n"
        )
        p.write_text(content)
        os.chmod(p, 0o600)
    (Path(seat_dir) / "sessions").mkdir(parents=True, exist_ok=True)
    print(f"rendered {session} -> {out_dir}")


if __name__ == "__main__":
    main()
