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
    for s in seats:
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
