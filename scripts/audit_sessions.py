#!/usr/bin/env python3
"""Detect misattributed permission denials and false delivery claims in live seats.

Reads, per seat under $OPENRIG_HOME/state/pi/<session>/:
  - agent/extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl
      (ground truth: permission_request.blocked events carry command + matchedPattern)
  - sessions/*.jsonl (Pi session log; only assistant-authored text blocks are
    scanned for capability claims -- user/tool text never counts)
and optionally scans a seat <workspace> docs dir for DISPATCHED-without-qitem
delivery claims.

Flags:
  1. MISATTRIBUTED_DENIAL: assistant text claims a rig/queue/send capability is
     absent, a bash-surface blocked event exists, and the live config still
     allows the rig surface. Cited evidence is the correlated bash event(s).
  2. FALSE_DELIVERY_CLAIM: docs contain DISPATCHED with no qitem- id.

Findings are leads for operator review (exit 1), not verdicts: claim matching is
heuristic and delivery flags do not cross-check live queue state. Secret-shaped
substrings are redacted from all output. Exit 2 on environment/usage errors
(missing seat root, zero seats, bad workspace).

Usage:
  python3 scripts/audit_sessions.py [--openrig-home DIR] [--workspace DIR]
      [--out report.md]
"""
import argparse
import glob
import json
import os
import re
import sys

# NOTE: deliberately excludes bare "bash denied" prose -- seats legitimately
# report real command-scoped denials that way (e.g. status reports). Only claim
# shapes asserting a *capability* is absent count here.
BAN_CLAIM_RES = [
    re.compile(r"no\s+(live\s+)?(queue|send|rig)\s+(surface|access|rights)", re.I),
    re.compile(r"(can't|cannot|unable to)\s+(run|use|invoke).*queue", re.I),
    re.compile(r"tool[\s-]?wide\s+ban", re.I),
    re.compile(r"no alternate .*surface", re.I),
]
DISPATCHED_RE = re.compile(r"DISPATCHED")
QITEM_RE = re.compile(r"qitem-[0-9a-z\-]+")
# Secret-shaped substrings redacted from finding output (Comment 1).
SECRET_RES = [
    re.compile(r"(ghp_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9\-]{8,}|AKIA[0-9A-Z]{16}|xox[bp]-?[A-Za-z0-9\-]+)"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/=]+"),
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
]
MAX_EVIDENCE_CHARS = 160
MAX_EXCERPTS = 5


def redact(s):
    if not isinstance(s, str):
        s = str(s)
    for rx in SECRET_RES:
        s = rx.sub("[REDACTED]", s)
    if len(s) > MAX_EVIDENCE_CHARS:
        s = s[:MAX_EVIDENCE_CHARS] + "..."
    return s


def iter_assistant_text(path):
    """Yield assistant-authored text blocks, streaming (bounded memory)."""
    try:
        fh = open(path)
    except FileNotFoundError:
        return
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "message":
                continue
            msg = entry.get("message", {})
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", [])
            parts = []
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text", "")
                    if isinstance(t, str):
                        parts.append(t)
            if parts:
                yield "\n".join(parts)


def load_blocked_events(path):
    """Stream review-log blocked events without retaining the whole log."""
    try:
        fh = open(path)
    except FileNotFoundError:
        return
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("event") == "permission_request.blocked":
                yield entry


def audit_seat(seat_dir, findings):
    session = os.path.basename(seat_dir)
    agent = os.path.join(seat_dir, "agent")
    review_log = os.path.join(agent, "extensions", "pi-permission-system", "logs",
                              "pi-permission-system-permission-review.jsonl")
    config_path = os.path.join(agent, "extensions", "pi-permission-system", "config.json")
    # Correlate on the bash surface only: other surfaces' denials (ls/read path
    # guards, etc.) say nothing about rig/queue capability. Cap retained events.
    bash_denied = [e for e in load_blocked_events(review_log)
                   if e.get("toolName") == "bash"][:MAX_EXCERPTS]
    if not bash_denied:
        return
    n_claims = 0
    for text in iter_assistant_text_stream(seat_dir):
        for rx in BAN_CLAIM_RES:
            if rx.search(text):
                n_claims += 1
                break
    if not n_claims:
        return
    try:
        bash_map = json.load(open(config_path))["permission"].get("bash", {})
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        bash_map = {}
    rig_surface = sorted(k for k, v in bash_map.items() if v == "allow" and k.startswith("rig "))
    if not rig_surface:
        return
    ev = "; ".join(
        f"command={redact(e.get('command'))!r} matchedPattern={e.get('matchedPattern')!r}"
        for e in bash_denied
    )
    findings.append(
        f"MISATTRIBUTED_DENIAL {session}: assistant claims rig/queue capability "
        f"absent but config allows rig surface {rig_surface}; correlated bash "
        f"denial(s): {ev}."
    )


def iter_assistant_text_stream(seat_dir):
    for path in sorted(glob.glob(os.path.join(seat_dir, "sessions", "*.jsonl"))):
        yield from iter_assistant_text(path)


def audit_docs(workspace, findings):
    for path in sorted(glob.glob(os.path.join(workspace, "**", "*.md"), recursive=True)):
        if "/node_modules/" in path or "/.git/" in path:
            continue
        try:
            with open(path) as f:
                content = f.read()
        except (FileNotFoundError, UnicodeDecodeError, PermissionError):
            continue
        if DISPATCHED_RE.search(content) and not QITEM_RE.search(content):
            findings.append(
                f"FALSE_DELIVERY_CLAIM {path}: contains DISPATCHED with no qitem- id."
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--openrig-home",
                    default=os.environ.get("OPENRIG_HOME", os.path.expanduser("~/.openrig")))
    ap.add_argument("--workspace", default="",
                    help="Seat workspace docs dir to scan; empty skips the docs scan "
                         "(the repo's own docs legitimately discuss DISPATCHED).")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    state = os.path.join(args.openrig_home, "state", "pi")
    if not os.path.isdir(state):
        print(f"audit_sessions: seat root missing or not a directory: {state}", file=sys.stderr)
        sys.exit(2)
    seats = sorted(d for d in glob.glob(os.path.join(state, "*")) if os.path.isdir(d))
    if not seats:
        print(f"audit_sessions: zero seat directories under {state}; nothing audited", file=sys.stderr)
        sys.exit(2)
    if args.workspace:
        if not os.path.isdir(args.workspace):
            print(f"audit_sessions: workspace missing or not a directory: {args.workspace}",
                  file=sys.stderr)
            sys.exit(2)

    findings = []
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
