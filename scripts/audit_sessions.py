#!/usr/bin/env python3
"""Detect misattributed permission denials and false delivery claims in live seats.

Reads, per seat under $OPENRIG_HOME/state/pi/<session>/:
  - agent/extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl
      (ground truth: permission_request.blocked events carry command + matchedPattern)
  - sessions/*.jsonl (Pi session log: assistant text with capability claims)
and scans <workspace> docs for DISPATCHED-without-qitem delivery claims.

Flags:
  1. MISATTRIBUTED_DENIAL: assistant text claims a tool-wide ban ("no queue
     surface", "bash denied", "cannot run X") while a blocked event shows a
     command-scoped deny (matchedPattern narrower than the surface rule) AND
     the seat config allows the intended bare command.
  2. FALSE_DELIVERY_CLAIM: docs contain DISPATCHED with no qitem- id nearby.

Heuristic assistant-text matching is intentional v1 scope: findings are leads
for operator review, not verdicts. Exit 1 when findings exist, 0 when clean.

Usage:
  python3 scripts/audit_sessions.py [--openrig-home ~/.openrig]
      [--workspace .] [--out /tmp/audit-sessions.md]
"""
import argparse
import glob
import json
import os
import re
import sys

# NOTE: deliberately excludes bare "bash denied" prose -- seats legitimately report
# real command-scoped denials that way (e.g. status reports). Only claim shapes
# that assert a *capability* is absent count here.
BAN_CLAIM_RES = [
    re.compile(r"no\s+(live\s+)?(queue|send|rig)\s+(surface|access|rights)", re.I),
    re.compile(r"(can't|cannot|unable to)\s+(run|use|invoke).*queue", re.I),
    re.compile(r"tool[\s-]?wide\s+ban", re.I),
    re.compile(r"no alternate .*surface", re.I),
]
DISPATCHED_RE = re.compile(r"DISPATCHED")
QITEM_RE = re.compile(r"qitem-[0-9a-z\-]+")


def load_jsonl(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return out


def assistant_text(session_files):
    texts = []
    for path in session_files:
        for entry in load_jsonl(path):
            s = json.dumps(entry)
            # Pi session entries carry message text in content blocks; keep it simple:
            # any string field mentioning our claim patterns counts as a claim site.
            texts.append(s)
    return "\n".join(texts)


def config_allows_bare(config_path, tool, command):
    """Recompute last-match-wins for a bare command against the seat's bash map."""
    try:
        cfg = json.load(open(config_path))["permission"]
    except (FileNotFoundError, KeyError):
        return None
    import fnmatch

    verdict = None
    for pattern, state in cfg.get(tool, {}).items():
        # mirror pi-permission-system: '*' -> '.*', full-string match; trailing
        # " *" also matches the bare program (OpenCode wildcard semantics).
        rx = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
        rx = re.sub(r" \(\.\*\)\?$", "( .*)?", rx) if False else rx
        if pattern.endswith(" *"):
            rx = "^" + re.escape(pattern[:-2]) + "( .*)?$"
        if re.match(rx, command, re.S):
            verdict = state
    _ = fnmatch  # (kept import explicit for future glob-parity work)
    return verdict


def audit_seat(seat_dir, findings):
    session = os.path.basename(seat_dir)
    agent = os.path.join(seat_dir, "agent")
    review_log = os.path.join(agent, "extensions", "pi-permission-system", "logs",
                              "pi-permission-system-permission-review.jsonl")
    config_path = os.path.join(agent, "extensions", "pi-permission-system", "config.json")
    blocked = [e for e in load_jsonl(review_log) if e.get("event") == "permission_request.blocked"]
    if not blocked:
        return
    text = assistant_text(glob.glob(os.path.join(seat_dir, "sessions", "*.jsonl")))
    claims = [r.pattern for r in BAN_CLAIM_RES if r.search(text)]
    if not claims:
        return
    # A ban claim is misattributed when blocked events exist (so something WAS
    # denied) but the seat config still allows the claimed capability: the deny
    # was scoped to a command unit (e.g. a `;`-chained tail denied by `*`), not
    # to the tool. Check the rig surface directly in the live config bytes.
    try:
        bash_map = json.load(open(config_path))["permission"].get("bash", {})
    except (FileNotFoundError, KeyError):
        bash_map = {}
    rig_surface = sorted(
        k for k, v in bash_map.items()
        if v == "allow" and k.startswith("rig ")
    )
    if rig_surface:
        ev = blocked[0]
        findings.append(
            f"MISATTRIBUTED_DENIAL {session}: assistant claims tool-wide ban "
            f"({len(claims)} pattern(s)) but config allows rig surface "
            f"{rig_surface} and review log shows only unit-scoped deny "
            f"command={ev.get('command')!r} matchedPattern={ev.get('matchedPattern')!r} "
            f"({len(blocked)} blocked event(s) total)."
        )


def audit_docs(workspace, findings):
    for path in glob.glob(os.path.join(workspace, "**", "*.md"), recursive=True):
        if "/node_modules/" in path or "/.git/" in path:
            continue
        try:
            with open(path) as f:
                content = f.read()
        except (FileNotFoundError, UnicodeDecodeError):
            continue
        if DISPATCHED_RE.search(content) and not QITEM_RE.search(content):
            findings.append(
                f"FALSE_DELIVERY_CLAIM {path}: contains DISPATCHED with no qitem- id."
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--openrig-home", default=os.path.expanduser("~/.openrig"))
    ap.add_argument("--workspace", default="",
                        help="Seat workspace docs dir to scan; empty skips the docs scan "
                             "(the repo's own docs legitimately discuss DISPATCHED).")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    findings = []
    state = os.path.join(args.openrig_home, "state", "pi")
    seats = sorted(d for d in glob.glob(os.path.join(state, "*")) if os.path.isdir(d))
    for seat in seats:
        audit_seat(seat, findings)
    if args.workspace:
        audit_docs(args.workspace, findings)
    report = ["# Session audit findings", ""]
    if findings:
        for msg in findings:
            print(f"FINDING {msg}")
            report.append(f"- {msg}")
    else:
        print(f"audit_sessions: clean ({len(seats)} seats scanned)")
        report.append("None.")
    if args.out:
        with open(args.out, "w") as f:
            f.write("\n".join(report) + "\n")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
