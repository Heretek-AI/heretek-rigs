#!/usr/bin/env python3
"""generate_trackers.py — emit dispatch-tracker proposals from queue state (issue #57).

Read-only proposal emitter: diffs one mission-side dispatch tracker against
machine-readable queue state and emits a paste-ready proposal covering every
diffed row (full-replacement Status cells) plus an unchanged-row listing.
The command NEVER modifies a tracker or any queue state (REQ-G2); the TPM
applies approved cells by hand, and convergence is checkable by re-running
scripts/reconcile.py over a scratch patched copy to an "in sync" exit 0
(REQ-G3).

Usage:
  generate_trackers.py --tracker PATH --queue-list FILE --transitions FILE [--out FILE]
  generate_trackers.py --tracker PATH --live [--rig-bin BIN] [--rig NAME] [--out FILE]

  --queue-list is a file holding `rig queue list --json` output (a JSON list
  of objects with qitemId/state). --transitions is a file holding a JSON
  object mapping qitemId -> list of {transitionId, state, transitionNote, ts}.
  --live fetches both over the rig CLI with the pinned --json read-only verbs
  (list/transitions only; anything else is refused). Bare queue output (JSON
  plus a human trailer) MUST NOT be parsed: it fails JSON decoding and lands
  in the fail-closed path, never in a partial diff.

  --out writes the proposal to a FRESH non-tracker path (same refuse rule as
  reconcile: input tracker, *dispatch-tracker.md, sprints/ dirs, existing
  files refused fail-closed with O_EXCL re-check at write time).

Queue-to-tracker mapping table (locked enum STAGED, DISPATCHED, PARKED,
QA PASS, PLACED, DONE, CLOSED + OTHER(<raw>)):
  terminal queue (entry state or latest-transition state in
  closed/done/handed_off/handed-off/complete/completed — note text is never
  terminal) => propose the QA PASS + PLACED canonical cell (exact design Q8
  shapes via the shared propose_cell). A queue note or tracker cell counts
  as a QA affirmation only when it opens with `QA PASS` and carries no
  negator (not/no/never/n't) or fail token.
  non-terminal queue => no terminal proposal; a terminal tracker claim
  becomes a Re-verify proposal carrying NEEDS-HUMAN-REVIEW.
Tracker prose matching no enum arm => OTHER(<raw>) + NEEDS-HUMAN-REVIEW
quoting both-side evidence; the status is NEVER guessed, the run stays
non-zero, and the row is excluded from convergence replay. Rows without a
qitem (or whose qitem has no queue entry) => tracker-row-without-qitem +
NEEDS-HUMAN-REVIEW; the row MUST NOT vanish from the output.

Exit codes: 0 = in sync (every parsed row agrees: enum terminal + latest
queue note recorded); 1 = proposals/review diffs found (TPM approval
required); 2 = fail-closed error (unreadable tracker, unparseable row,
unparseable/unreachable/EMPTY queue listing, malformed input, --out
refusal). An EMPTY queue list ([]) is a named exit-2 failure: it MUST NEVER
report "in sync".

Row-model home: scripts/reconcile_model.py. This emitter consumes the shared
model (REQ-G5); the names below are imports, not a second implementation.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reconcile_model import (  # noqa: E402
    NO_QITEM_CELLS,
    QITEM_RE,
    ReconcileError,
    check_allowed,
    diff_row,
    load_json_file,
    normalize_proposal_note,
    normalize_tracker,
    parse_tracker,
    propose_cell,
    queue_terminal,
    recorded_note_ids,
    refuse_out_path,
    run_rig,
    write_out_exclusive,
)

# Queue-side signal -> tracker-side meaning (display + branch contract).
# Terminal detection itself is queue_terminal() from the shared model — state
# ONLY, never note text; this table only names the mapping for proposal readers.
QUEUE_TO_TRACKER_MAP = (
    "terminal queue (entry or latest-transition state in "
    "closed/done/handed_off/handed-off/complete/completed; note text never "
    "terminal) => QA PASS + PLACED canonical cell; "
    "non-terminal queue => no terminal proposal "
    "(terminal tracker claims become Re-verify + NEEDS-HUMAN-REVIEW)"
)

PASTE_READY_CLASSES = frozenset(
    {
        "stale-state",
        "parked-satisfied-but-tracker-silent",
        "missing-convergence-annotation",
    }
)


def tracker_enum_arm(cell):
    """Name the locked enum arm for a tracker Status cell (shared normalizer).

    Returns one of STAGED, DISPATCHED, PARKED, QA PASS, PLACED, DONE/CLOSED,
    or OTHER(<raw>) with the raw cell quoted verbatim. Never coerces: an
    unmatched cell is always OTHER, never a guessed arm.
    """
    norm = normalize_tracker(cell)
    if norm["qa_pass"]:
        return "QA PASS"
    if norm["placed"]:
        return "PLACED"
    if norm["closed"]:
        return "DONE/CLOSED"
    if norm["staged"]:
        return "STAGED"
    if norm["dispatched"]:
        return "DISPATCHED"
    if norm["parked"]:
        return "PARKED"
    return f"OTHER({cell.strip()})"


def queue_side_of(row, queue_by_id, transitions_by_id):
    """Best-effort queue evidence for a row (shared terminal detection)."""
    qitem_raw = row["qitem"].strip()
    if qitem_raw in NO_QITEM_CELLS:
        return None, [], "(no qitem recorded)"
    m = QITEM_RE.search(qitem_raw)
    qid = m.group(0) if m else qitem_raw
    entry = queue_by_id.get(qid)
    if entry is None:
        return None, [], "(no queue entry)"
    trail = transitions_by_id.get(qid, [])
    terminal, latest_id, latest = queue_terminal(entry, trail)
    raw_note = str(latest.get("transitionNote", "")) if latest else ""
    evidence = f"state={entry.get('state')} latest_transition={latest_id} ({raw_note})"
    return entry, trail, evidence


def render_proposal(row, arm, queue_mapping, diff, review):
    """Render one proposal block: paste-ready cell or NEEDS-HUMAN-REVIEW."""
    header = (
        f"DIFF [{diff['class']}] {row['file']}:{row['line']} "
        f"slice {row['slice']} qitem {row['qitem'].strip()}"
    )
    lines = [
        header,
        f"  tracker-enum:  {arm}",
        f"  queue-mapping: {queue_mapping}",
        f"  reason:  {diff['reason']}",
        f"  tracker: {diff['tracker']}",
        f"  queue:   {diff['queue']}",
    ]
    if review:
        lines.append(
            "  NEEDS-HUMAN-REVIEW: TPM decide; guessed-status nowhere. "
            f"Tracker evidence: '{diff['tracker']}'. "
            f"Queue evidence: '{diff['queue']}'."
        )
        lines.append(f"  SUGGESTED (not paste-ready): {diff['proposal']}")
    else:
        lines.append("  PROPOSED Status cell:")
        lines.append(f"    {diff['proposal']}")
        lines.append(f"PROPOSED-CELL:::{diff['proposal']}")
        lines.append(
            f"  SUGGESTED queue-note append on {row['qitem'].strip()}: "
            f"Tracker row {row['slice']} converged: {diff['tracker']} -> "
            f"{diff['proposal']}"
        )
    return "\n".join(lines)


def render_unchanged(row, arm, latest_id, latest_recorded):
    if latest_id is None:
        note = "(no queue transitions recorded)"
    elif latest_recorded:
        note = f"(queue note {latest_id} recorded)"
    else:
        note = (
            f"(queue latest {latest_id}; queue non-terminal, "
            f"no convergence note required)"
        )
    return (
        f"UNCHANGED {row['file']}:{row['line']} slice {row['slice']} "
        f"qitem {row['qitem'].strip()} enum {arm} {note}"
    )


def build_proposal(tracker, queue_by_id, transitions_by_id):
    """Diff every row; return (blocks, unchanged, n_review). Never writes."""
    rows = parse_tracker(tracker)
    blocks = []
    unchanged = []
    n_review = 0
    for row in rows:
        cell = row["status"]
        arm = tracker_enum_arm(cell)
        entry, trail, evidence = queue_side_of(row, queue_by_id, transitions_by_id)
        if arm.startswith("OTHER("):
            # Unknown prose: NEVER coerced to a guessed enum, NEVER passed
            # to diff_row (which would propose a canonical cell for a
            # terminal queue). Always a review diff, always non-zero.
            diff = {
                "class": "other-prose",
                "reason": (
                    "tracker Status prose matches no locked enum arm; "
                    "status NEVER guessed"
                ),
                "tracker": cell,
                "queue": evidence,
                "proposal": (
                    f"TPM: classify '{cell.strip()}' against the locked enum "
                    f"(STAGED, DISPATCHED, PARKED, QA PASS, PLACED, DONE, CLOSED) "
                    f"or record the slice qitem; queue-side evidence: {evidence}"
                ),
            }
            blocks.append(
                render_proposal(
                    row, arm, "WITHHELD — TPM judgment required", diff, True
                )
            )
            n_review += 1
            continue
        diff = diff_row(row, queue_by_id, transitions_by_id)
        if diff is None:
            terminal, latest_id, _ = (
                queue_terminal(entry, trail) if entry is not None else (False, None, {})
            )
            unchanged.append(
                render_unchanged(
                    row, arm, latest_id, latest_id in recorded_note_ids(cell)
                )
            )
            continue
        if diff["class"] == "tracker-row-without-qitem":
            blocks.append(
                render_proposal(
                    row, arm, "WITHHELD — TPM judgment required", diff, True
                )
            )
            n_review += 1
            continue
        terminal, latest_id = (
            queue_terminal(entry, trail)[:2] if entry is not None else (False, None)
        )
        if diff["class"] in PASTE_READY_CLASSES and terminal and latest_id is not None:
            blocks.append(
                render_proposal(
                    row,
                    arm,
                    "terminal => QA PASS + PLACED canonical",
                    diff,
                    False,
                )
            )
        elif diff["class"] in PASTE_READY_CLASSES and terminal:
            # Terminal by entry state alone with NO transition trail (Q7/Q8):
            # a paste-ready cell would cite a nonexistent "queue note None",
            # so the row routes to human review with no paste marker and a
            # no-evidence proposal naming both-side evidence.
            review_diff = dict(diff)
            review_diff["proposal"] = (
                "TPM: confirm the terminal queue state with QA and record "
                "the closing transition note before pasting a canonical "
                f"cell; queue-side evidence: {evidence}; status NEVER guessed"
            )
            blocks.append(
                render_proposal(
                    row,
                    arm,
                    "terminal-state without transition evidence => "
                    "NEEDS-HUMAN-REVIEW, no paste-ready cell",
                    review_diff,
                    True,
                )
            )
            n_review += 1
        else:
            # Stale-terminal (tracker claims terminal while the queue is not
            # terminal): re-verify guidance, never a pasted terminal cell.
            blocks.append(
                render_proposal(
                    row,
                    arm,
                    "non-terminal => Re-verify, no terminal proposal",
                    diff,
                    True,
                )
            )
            n_review += 1
    return blocks, unchanged, n_review


def load_inputs(args):
    """Load queue state from files or --live; fail closed with named errors."""
    if args.live:
        scope = ["--rig", args.rig] if args.rig else ["-A"]
        qlist = run_rig(args.rig_bin, ["queue", "list", "--json", *scope])
        if not isinstance(qlist, list):
            raise ReconcileError(
                "UNREACHABLE QUEUE (rig queue list: expected a JSON list)"
            )
        if not qlist:
            raise ReconcileError(
                "EMPTY QUEUE LIST (rig queue list returned []; an empty queue "
                "MUST NEVER report in sync — re-fetch rig queue list --json)"
            )
        queue_by_id = {e.get("qitemId"): e for e in qlist if isinstance(e, dict)}
        transitions_by_id = {}
        rows_hint = parse_tracker(args.tracker)
        for row in rows_hint:
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
        return queue_by_id, transitions_by_id
    if not args.queue_list or not args.transitions:
        raise ReconcileError(
            "--queue-list and --transitions are required without --live"
        )
    qlist = load_json_file(args.queue_list, "QUEUE LIST")
    trans = load_json_file(args.transitions, "TRANSITIONS")
    if not isinstance(qlist, list):
        raise ReconcileError(
            f"UNPARSEABLE QUEUE LIST '{args.queue_list}' (expected a JSON list)"
        )
    if not qlist:
        raise ReconcileError(
            f"EMPTY QUEUE LIST '{args.queue_list}' (parsed to []; an empty queue "
            f"MUST NEVER report in sync — re-fetch rig queue list --json)"
        )
    if not isinstance(trans, dict):
        raise ReconcileError(
            f"UNPARSEABLE TRANSITIONS '{args.transitions}' (expected a JSON object)"
        )
    queue_by_id = {e.get("qitemId"): e for e in qlist if isinstance(e, dict)}
    return queue_by_id, trans


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Emit dispatch-tracker proposals from queue state (issue #57). Read-only."
    )
    parser.add_argument("--tracker", required=True)
    parser.add_argument("--queue-list", default=None)
    parser.add_argument("--transitions", default=None)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--rig-bin", default="rig")
    parser.add_argument("--rig", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    try:
        if args.out:
            refuse_out_path(args.out, [args.tracker])
        queue_by_id, transitions_by_id = load_inputs(args)
        rows = parse_tracker(args.tracker)
        blocks, unchanged, n_review = build_proposal(
            args.tracker, queue_by_id, transitions_by_id
        )
        if blocks:
            report = (
                f"generate-trackers: 1 tracker(s) vs queue state "
                f"({len(queue_by_id)} queue rows)\n"
                f"queue→tracker mapping: {QUEUE_TO_TRACKER_MAP}\n"
                + "\n".join(blocks)
                + "\n"
                + "\n".join(unchanged)
                + ("\n" if unchanged else "")
                + f"generate-trackers: {len(blocks)} proposal(s) across "
                f"{len(rows)} row(s) ({len(unchanged)} unchanged, "
                f"{n_review} NEEDS-HUMAN-REVIEW); TPM approval required "
                f"\u2014 no files modified."
            )
            if args.out:
                write_out_exclusive(args.out, report + "\n")
            print(report)
            return 1
        summary = (
            f"generate-trackers: in sync \u2014 {len(rows)} rows across "
            f"1 tracker(s) agree with queue state.\n" + "\n".join(unchanged)
        )
        if args.out:
            write_out_exclusive(args.out, summary + "\n")
        print(summary)
        return 0
    except ReconcileError as exc:
        print(f"generate-trackers: FAILED: {exc}", file=sys.stderr)
        return 2
    except (AttributeError, TypeError, ValueError, KeyError) as exc:
        detail = " ".join(str(exc).split())
        print(
            f"generate-trackers: FAILED: malformed input ({type(exc).__name__}: {detail})",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
