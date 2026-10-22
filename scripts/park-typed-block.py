#!/usr/bin/env python3
"""Park-time guard for typed-external blocks (remediate-38-unblock, REQ-BU1/BU4).

Thin validating wrapper over `rig queue block`. A typed-external park
(`external:<what>` / `fold:<what>` / `auth:<what>`) is rejected unless it
carries BOTH:

  1. a machine-checkable satisfaction predicate:
       SATISFY-WHEN: <what evidence> VIA <where it lands>
     (the predicate travels in the park transition note -- the sweep's
     carrier -- so re-evaluation is a check, not a judgment call); and
  2. a live wake: --wake-watchdog <id>, --sweep-covered (this sweep's
     transitions-cursor coverage), or a live blocker qitem in --on.
     --wake-after alone is rejected (timer-only wakes are the #38 shape).

Human-seat and live-qitem parks pass through unwrapped (resolve covers leg-1
human parks; live qitem blockers already self-wake).

--dry-run prints the exact `rig queue block` argv and executes nothing.
"""

import argparse
import re
import subprocess
import sys

PREDICATE_RE = re.compile(
    r"^\s*SATISFY-WHEN:\s*\S.{10,}?\s+VIA\s+\S.{2,}\s*$", re.IGNORECASE | re.DOTALL
)

TYPED_PREFIXES = ("external:", "fold:", "auth:")


def is_typed_blocker(blocker):
    return isinstance(blocker, str) and blocker.startswith(TYPED_PREFIXES)


def looks_like_qitem(blocker):
    return (
        isinstance(blocker, str)
        and re.fullmatch(r"qitem-[0-9a-f-]+", blocker) is not None
    )


def plan(argv):
    """Validate and build the rig argv. Returns {exit, argv|None, stderr}.

    Never executes rig; main() executes only on exit 0 without --dry-run.
    """
    parser = argparse.ArgumentParser(
        description="Guarded park for typed-external blocks (REQ-BU1/BU4).",
        # No option-prefix matching: an abbreviation such as --dry-ru must
        # never silently parse (a missed dry-run flag would be a LIVE op).
        allow_abbrev=False,
    )
    parser.add_argument("qitemId")
    parser.add_argument("--on", required=True)
    parser.add_argument("--predicate", default=None)
    parser.add_argument("--note", default=None)
    parser.add_argument("--continuation", default=None)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--evidence-ref", default=None)
    parser.add_argument("--wake-watchdog", default=None)
    parser.add_argument("--wake-after", default=None)
    parser.add_argument("--sweep-covered", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not is_typed_blocker(args.on):
        rig_argv = ["rig", "queue", "block", args.qitemId, "--on", args.on]
        if args.note:
            rig_argv += ["--note", args.note]
        if args.continuation:
            rig_argv += ["--continuation", args.continuation]
        if args.wake_watchdog:
            rig_argv += ["--wake-watchdog", args.wake_watchdog]
        if args.wake_after:
            rig_argv += ["--wake-after", args.wake_after]
        if args.json:
            rig_argv.append("--json")
        return {
            "exit": 0,
            "argv": rig_argv,
            "stderr": "",
            "stdout": "non-typed park: pass-through (no predicate rule)\n",
            "dry_run": args.dry_run,
        }

    # Typed-external park: predicate is mandatory (REQ-BU1 rejection rule).
    if not args.predicate or not PREDICATE_RE.match(args.predicate):
        return {
            "exit": 2,
            "argv": None,
            "stderr": "error: typed-external park requires a predicate "
            "(--predicate 'SATISFY-WHEN: <what evidence> VIA <where it lands>'); "
            "no HELD row created\n",
            "stdout": "",
        }
    # Live wake is mandatory; --wake-after alone is not a live wake (REQ-BU4).
    # An empty --wake-watchdog value wakes nobody, so it is not a live wake.
    live_wake = (
        bool(args.wake_watchdog) or args.sweep_covered or looks_like_qitem(args.on)
    )
    if not live_wake:
        hint = (
            "--wake-after is a backstop, never the only wake for typed blocks; "
            "add --wake-watchdog <id> or --sweep-covered"
        )
        return {
            "exit": 2,
            "argv": None,
            "stderr": f"error: typed-external park needs a live wake: {hint}; "
            f"no HELD row created\n",
            "stdout": "",
        }

    note = " ".join(part for part in [args.predicate, args.note] if part).strip()
    rig_argv = ["rig", "queue", "block", args.qitemId, "--on", args.on, "--note", note]
    continuation_bits = []
    if args.continuation:
        continuation_bits.append(args.continuation)
    if args.sweep_covered:
        continuation_bits.append("sweep-covered: transitions-cursor re-evaluation")
    if continuation_bits:
        rig_argv += ["--continuation", " ".join(continuation_bits)]
    if args.wake_watchdog:
        rig_argv += ["--wake-watchdog", args.wake_watchdog]
    if args.wake_after:
        rig_argv += ["--wake-after", args.wake_after]
    if args.json:
        rig_argv.append("--json")
    return {
        "exit": 0,
        "argv": rig_argv,
        "stderr": "",
        "stdout": "typed-external park accepted (predicate + live wake)\n",
        "dry_run": args.dry_run,
    }


def main(argv=None):
    result = plan(argv if argv is not None else sys.argv[1:])
    if result["stderr"]:
        sys.stderr.write(result["stderr"])
    if result["exit"] != 0:
        return result["exit"]
    if result.get("dry_run"):
        sys.stdout.write(" ".join(result["argv"]) + "\n")
        return 0
    proc = subprocess.run(result["argv"])
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
