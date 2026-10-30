#!/usr/bin/env python3
"""reconcile.py — tracker-vs-queue reconcile diff command (issue #39).

Read-only: parses hand-maintained dispatch tracker markdown tables
(docs/sprints/wave*-dispatch-tracker.md + phase0-dispatch-tracker.md) and
compares each slice row against machine-readable queue state. Every mismatch
is reported as a row-level diff naming the tracker file, the row (slice +
qitem), the tracker-side value, and the queue-side value, plus a paste-ready
proposed replacement Status cell for TPM approval. The command NEVER modifies
a tracker or any queue state (REQ-R2); applying all approved proposals is
checkable by re-running to an "in sync" empty diff (REQ-R3).

Usage:
  reconcile.py --tracker PATH [--tracker PATH...] --queue-list FILE --transitions FILE [--envelopes FILE] [--out FILE]
  reconcile.py --tracker PATH [--tracker PATH...] --live [--rig-bin BIN] [--rig NAME | --all] [--out FILE]

  --queue-list is a file holding `rig queue list --json` output (a JSON list
  of objects with qitemId/state). --transitions is a file holding a JSON
  object mapping qitemId -> list of {transitionId, state, transitionNote, ts}
  (assembled from per-qitem `rig queue transitions --json <qitem>` calls).
  --live fetches both over the rig CLI with the pinned --json read-only verbs
  (list/show/transitions only); anything else is refused.

  --out writes the reviewable proposal to a FRESH non-tracker file OUTSIDE
  the mission repo. --out pointing at an input tracker, at any
  tracker-shaped path (a *dispatch-tracker.md filename or anything inside
  a sprints/ tracker directory), or at any existing file is refused
  fail-closed (exit 2, destination bytes untouched).

Exit codes: 0 = in sync (every parsed row agrees); 1 = diffs found (TPM
approval required); 2 = fail-closed error (unreadable tracker, unparseable
row, unparseable queue JSON, unreachable queue/rig, --out refusal).

Row-model home: scripts/reconcile_model.py. This command consumes the shared
model (REQ-G5); the definitions below are imports, not a second
implementation. Mapping table, diff classes, and fail-closed behavior are
documented in reconcile_model.py and the issue #39 spec.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reconcile_model import (  # noqa: E402
    QITEM_RE,
    ReconcileError,
    check_allowed,
    diff_row,
    is_separator,
    load_json_file,
    normalize_proposal_note,
    normalize_tracker,
    parse_tracker,
    propose_cell,
    queue_terminal,
    recorded_note_ids,
    refuse_out_path,
    render_diff,
    run_rig,
    split_row,
    write_out_exclusive,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diff dispatch tracker tables against queue state (issue #39). Read-only."
    )
    parser.add_argument("--tracker", action="append", required=True)
    parser.add_argument("--queue-list", default=None)
    parser.add_argument("--transitions", default=None)
    parser.add_argument(
        "--envelopes",
        default=None,
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--rig-bin", default="rig")
    parser.add_argument("--rig", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    try:
        if args.out:
            refuse_out_path(args.out, args.tracker)
        rows = []
        for tracker in args.tracker:
            rows.extend(parse_tracker(tracker))
        if args.live:
            scope = ["--rig", args.rig] if args.rig else ["-A"]
            qlist = run_rig(args.rig_bin, ["queue", "list", "--json", *scope])
            if not isinstance(qlist, list):
                raise ReconcileError(
                    "UNREACHABLE QUEUE (rig queue list: expected a JSON list)"
                )
            queue_by_id = {e.get("qitemId"): e for e in qlist if isinstance(e, dict)}
            transitions_by_id = {}
            for row in rows:
                m = QITEM_RE.search(row["qitem"])
                if not m:
                    continue
                trail = run_rig(
                    args.rig_bin, ["queue", "transitions", "--json", m.group(0)]
                )
                if not isinstance(trail, list):
                    raise ReconcileError(
                        f"UNREACHABLE QUEUE (rig queue transitions {m.group(0)}: "
                        f"expected a JSON list)"
                    )
                transitions_by_id[m.group(0)] = trail
        else:
            if not args.queue_list or not args.transitions:
                parser.error(
                    "--queue-list and --transitions are required without --live"
                )
            qlist = load_json_file(args.queue_list, "QUEUE LIST")
            trans = load_json_file(args.transitions, "TRANSITIONS")
            if not isinstance(qlist, list):
                raise ReconcileError(
                    f"UNPARSEABLE QUEUE LIST '{args.queue_list}' (expected a JSON list)"
                )
            if not isinstance(trans, dict):
                raise ReconcileError(
                    f"UNPARSEABLE TRANSITIONS '{args.transitions}' (expected a JSON object)"
                )
            queue_by_id = {e.get("qitemId"): e for e in qlist if isinstance(e, dict)}
            transitions_by_id = trans
        if args.envelopes:
            envelopes = load_json_file(args.envelopes, "ENVELOPES")
            if not isinstance(envelopes, dict):
                raise ReconcileError(
                    f"UNPARSEABLE ENVELOPES '{args.envelopes}' (expected a JSON object)"
                )
            envelope_by_id = envelopes
        else:
            envelope_by_id = None

        diffs = []
        for row in rows:
            diff = diff_row(
                row, queue_by_id, transitions_by_id, envelope_by_id=envelope_by_id
            )
            if diff is not None:
                diffs.append(render_diff(row, diff))
        if diffs:
            report = (
                f"reconcile: {len(args.tracker)} tracker(s) vs queue state "
                f"({len(queue_by_id)} queue rows)\n"
                + "\n".join(diffs)
                + f"\nreconcile: {len(diffs)} diff(s) across {len(rows)} row(s); "
                f"TPM approval required \u2014 no files modified."
            )
            if args.out:
                write_out_exclusive(args.out, report + "\n")
            print(report)
            return 1
        summary = (
            f"reconcile: in sync \u2014 {len(rows)} rows across "
            f"{len(args.tracker)} tracker(s) agree with queue state."
        )
        if args.out:
            write_out_exclusive(args.out, summary + "\n")
        print(summary)
        return 0
    except ReconcileError as exc:
        print(f"reconcile: FAILED: {exc}", file=sys.stderr)
        return 2
    except (AttributeError, TypeError, ValueError, KeyError) as exc:
        detail = " ".join(str(exc).split())
        print(
            f"reconcile: FAILED: malformed input ({type(exc).__name__}: {detail})",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
