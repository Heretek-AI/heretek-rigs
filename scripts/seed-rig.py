#!/usr/bin/env python3
"""seed-rig.py — Seed every Pi seat declared in a rig.yaml, pod fragment, or member fragment.

Invokes scripts/render-seat.py once per seat. Run BEFORE `rig up`, `rig expand`, or `rig add`.
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
import subprocess
from pathlib import Path

USAGE = """usage: seed-rig.py <rig.yaml | pod-fragment.yaml | member-fragment.yaml> [--rig <rig-id>] [--pod <pod-id>] [--dry-run] [--allow-missing-secrets] [--refresh-policy-only]
  rig.yaml          seeds every member of every pod (rig id = name:)
  pod fragment      needs --rig (the rig you will rig expand into)
  member fragment   needs --rig and --pod (the target of rig add)"""


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


# provisioning-gate-74 (#74, REQ-P2/P4): read-only stage-time existence
# gate. Same resolution as scripts/render-seat.py (shutil.which +
# path-exists, no installs/pulls/network) applied to each staged seat's
# bound MCP commands + bash-grant leading binaries. Degrade-loudly with
# the same warn shape as the render gate (REQ-P1): never silent, never a
# hard fail (the renderer itself stays the per-seat authority).
def _resolve_artifact74(command) -> tuple:
    if not isinstance(command, str) or not command.strip():
        return (False, str(command))
    first = command.strip()
    if Path(first).is_absolute():
        return (shutil.which(first) is not None, first)
    if "/" in first:
        return (shutil.which(first) is not None, first)
    return (shutil.which(first) is not None, first)


def _bash_leading74(pattern) -> str | None:
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


def stage_time_provisioning_warns(
    role_id, session, role, mcp_servers, tools_dir
) -> list:
    """Return stage-time warn lines (without the trailing newline) for one
    seat. Pure read-only resolution; callers print each line to stderr."""
    warns = []
    for binding in role.get("mcp", []) or []:
        srv_name = binding.get("server")
        server = mcp_servers.get(srv_name, {})
        if server.get("transport") == "http" or "command" not in server:
            continue
        raw = str(server["command"]).replace("@TOOLS@", tools_dir)
        ok, artifact = _resolve_artifact74(raw)
        if not ok:
            warns.append(
                f"warn: {session}: {srv_name} missing tool artifact "
                f"at stage time: {artifact}"
            )
    for pattern in role.get("permissions", {}).get("bash_allow", []) or []:
        binary = _bash_leading74(pattern)
        if binary is not None and shutil.which(binary) is None:
            warns.append(
                f"warn: {session}: bash grant {pattern!r} missing tool "
                f"artifact at stage time: {binary}"
            )
    return warns


def role_of(m: dict) -> str:
    ref = m.get("agent_ref")
    if not ref:
        die(f"member {m.get('id')} has no agent_ref")
    cleaned = re.sub(r"^(local|path):", "", str(ref))
    return Path(cleaned).name


# 107-identity M1 (REQ-I1): seed-time per-seat grant issuance.
# `seed-rig.py` runs `rig mcp token add <session> --seat <session>` (M0-proven
# seat-only scope: no --rig/--root/--workspace/--owner flags), stores the
# once-printed token under the secrets dir (0600, same pattern as
# github.pat), and render-seat.py wires it into the seat's MCP client config
# via the existing `!echo Bearer $(cat ...)` header form. stdio stays default.
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,}$")


def _render_seat_mod():
    """Load scripts/render-seat.py as a module: single source of truth for
    the per-seat grant token filename (never duplicated here)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "render_seat_grants", Path(__file__).resolve().parent / "render-seat.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_issued_token(output: str, grant_name: str) -> str | None:
    """Extract the once-printed token from `rig mcp token add` stdout.

    Fail-closed: anything but the exact `Token for <name>,` first line plus
    a token-shaped second line yields None — callers revoke the minted grant
    and die, so a grant with an unknown token never lingers.
    """
    lines = [ln.strip() for ln in (output or "").splitlines() if ln.strip()]
    if len(lines) < 2:
        return None
    if not lines[0].startswith(f"Token for {grant_name},"):
        return None
    if _TOKEN_RE.fullmatch(lines[1]) is None:
        return None
    return lines[1]


def _list_grant_names(rig_bin: str):
    """Return the set of existing grant names, or None when `rig` cannot list."""
    try:
        proc = subprocess.run(
            [rig_bin, "mcp", "token", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        grants = json.loads(proc.stdout).get("grants", [])
    except (ValueError, AttributeError):
        return None
    if not isinstance(grants, list):
        return None
    return {str(g.get("name")) for g in grants if isinstance(g, dict)}


def _revoke_grant(rig_bin: str, session: str) -> bool:
    try:
        proc = subprocess.run(
            [rig_bin, "mcp", "token", "revoke", session],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def issue_seat_grant(
    session: str,
    secrets_dir: str,
    rig_bin: str = "rig",
    allow_missing_secrets: bool = False,
) -> int:
    """Issue (or reuse) the seat's MCP HTTP bearer grant.

    Returns 0 on issued/reused (or loud degrade under
    --allow-missing-secrets), 2 on fatal. The token itself is never printed.
    """
    render_mod = _render_seat_mod()
    token_path = Path(secrets_dir) / render_mod.seat_grant_token_filename(session)

    def _fail(msg: str) -> int:
        if allow_missing_secrets:
            print(
                f"warn: {session}: seat grant not issued ({msg}), continuing degraded",
                file=sys.stderr,
            )
            return 0
        print(f"error: {session}: seat grant issuance failed: {msg}", file=sys.stderr)
        return 2

    for _ in range(2):
        names = _list_grant_names(rig_bin)
        if names is None:
            return _fail(f"cannot list grants via {rig_bin}")
        if session in names:
            if token_path.is_symlink():
                # HR-4.3: a secrets dir entry that is a symlink is untrusted —
                # remove it and re-issue rather than reusing or following it.
                try:
                    token_path.unlink()
                except OSError as e:
                    return _fail(f"cannot remove symlinked {token_path.name}: {e}")
                print(
                    f"warn: {session}: {token_path.name} was a symlink; removed, re-issuing",
                    file=sys.stderr,
                )
            elif token_path.is_file():
                print(
                    f"ok {session}: seat grant already issued (reuse {token_path.name})"
                )
                return 0
            else:
                print(
                    f"warn: {session}: grant exists but {token_path.name} is missing; re-issuing",
                    file=sys.stderr,
                )
            if not _revoke_grant(rig_bin, session):
                return _fail(f"cannot revoke stale grant {session}")
            continue
        # No grant yet: mint a seat-only grant (M0 winner: no scope flags).
        try:
            proc = subprocess.run(
                [rig_bin, "mcp", "token", "add", session, "--seat", session],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            return _fail(f"token add failed: {e}")
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            if "already has a grant" in detail:
                continue
            return _fail(f"token add failed: {detail}")
        token = parse_issued_token(proc.stdout, session)
        if token is None:
            _revoke_grant(rig_bin, session)
            print(
                f"error: {session}: token add printed unparseable output; minted grant revoked",
                file=sys.stderr,
            )
            return 2
        try:
            fd = os.open(
                token_path,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            with os.fdopen(fd, "w") as fh:
                fh.write(token)
        except OSError as e:
            _revoke_grant(rig_bin, session)
            print(
                f"error: {session}: cannot store grant token: {e}; minted grant revoked",
                file=sys.stderr,
            )
            return 2
        print(f"ok {session}: seat grant issued ({token_path.name})")
        return 0
    return _fail("grant state did not converge after retry")


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(USAGE)
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("target", nargs="?")
    parser.add_argument("--rig")
    parser.add_argument("--pod")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-missing-secrets", action="store_true")
    parser.add_argument("--refresh-policy-only", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or not args.target:
        print(USAGE)
        sys.exit(2)

    target_path = Path(args.target)
    if not target_path.exists():
        die(f"missing file {target_path}")
    doc = yaml.safe_load(target_path.read_text()) or {}

    seats = []
    if "pods" in doc:
        for p in doc["pods"]:
            for m in p.get("members", []):
                seats.append(
                    {
                        "rig": doc["name"],
                        "pod": p["id"],
                        "member": m["id"],
                        "role": role_of(m),
                    }
                )
    elif "members" in doc:
        if not args.rig:
            die("a pod fragment needs --rig")
        for m in doc["members"]:
            seats.append(
                {
                    "rig": args.rig,
                    "pod": doc["id"],
                    "member": m["id"],
                    "role": role_of(m),
                }
            )
    elif "agent_ref" in doc:
        if not args.rig or not args.pod:
            die("a member fragment needs --rig and --pod")
        seats.append(
            {
                "rig": args.rig,
                "pod": args.pod,
                "member": doc["id"],
                "role": role_of(doc),
            }
        )
    else:
        die(f"{target_path}: not a rig spec, pod fragment or member fragment")

    render_script = Path(__file__).resolve().parent / "render-seat.py"
    # provisioning-gate-74 (#74, REQ-P2): load the fleet catalog + MCP
    # catalog once for the stage-time gate. Unreadable catalogs degrade to
    # a single named warn (the renderer re-checks per seat anyway).
    _repo74 = Path(__file__).resolve().parent.parent
    _fleet74, _mcp74 = {}, {}
    try:
        _fleet74 = yaml.safe_load((_repo74 / "fleet" / "fleet.yaml").read_text()) or {}
        _mcp74 = (
            yaml.safe_load((_repo74 / "fleet" / "mcp-servers.yaml").read_text()) or {}
        ).get("servers", {})
    except Exception as _e74:
        print(f"warn: stage-time provisioning gate unchecked: {_e74}", file=sys.stderr)
    _tools74 = os.environ.get(
        "HERETEK_TOOLS", str(Path.home() / ".local/share/heretek-rigs/tools")
    )
    _roles74 = _fleet74.get("roles", {}) if isinstance(_fleet74, dict) else {}
    # 107-identity M1 (REQ-I1): seed-time per-seat grant issuance runs before
    # each seat's render (strict render needs the token file to exist).
    # Skipped for --dry-run (no side effects) and --refresh-policy-only
    # (policy refresh never mints grants).
    _secrets_dir = os.environ.get(
        "HERETEK_SECRETS", str(Path.home() / ".config/heretek-rigs/secrets")
    )
    _issue_grants = not (args.dry_run or args.refresh_policy_only)
    _rig_bin = shutil.which("rig") or "rig"
    for s in seats:
        _session74 = f"{s['pod']}-{s['member']}@{s['rig']}"
        _role74 = _roles74.get(s["role"])
        if _role74 is None:
            print(
                f"warn: {_session74}: unknown role {s['role']} at stage time",
                file=sys.stderr,
            )
        else:
            for _w74 in stage_time_provisioning_warns(
                s["role"], _session74, _role74, _mcp74, _tools74
            ):
                print(_w74, file=sys.stderr)
        if _issue_grants:
            _grc = issue_seat_grant(
                _session74,
                _secrets_dir,
                rig_bin=_rig_bin,
                allow_missing_secrets=args.allow_missing_secrets,
            )
            if _grc != 0:
                sys.exit(_grc)
        cmd = [
            sys.executable,
            str(render_script),
            "--role",
            s["role"],
            "--rig",
            s["rig"],
            "--pod",
            s["pod"],
            "--member",
            s["member"],
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.allow_missing_secrets:
            cmd.append("--allow-missing-secrets")
        if args.refresh_policy_only:
            cmd.append("--policy-only")
        if args.dry_run:
            proc = subprocess.run(cmd, stdout=subprocess.DEVNULL)
            if proc.returncode != 0:
                sys.exit(proc.returncode)
            print(f"ok {s['pod']}-{s['member']}@{s['rig']}")
        else:
            proc = subprocess.run(cmd)
            if proc.returncode != 0:
                sys.exit(proc.returncode)

    print(f"seeded {len(seats)} seat(s)")


if __name__ == "__main__":
    main()
