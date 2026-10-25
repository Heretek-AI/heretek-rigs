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
import re
import subprocess
from pathlib import Path

USAGE = """usage: seed-rig.py <rig.yaml | pod-fragment.yaml | member-fragment.yaml> [--rig <rig-id>] [--pod <pod-id>] [--dry-run] [--allow-missing-secrets]
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
