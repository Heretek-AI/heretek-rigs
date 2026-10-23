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
  reconcile.py --tracker PATH [--tracker PATH...] --queue-list FILE --transitions FILE [--out FILE]
  reconcile.py --tracker PATH [--tracker PATH...] --live [--rig-bin BIN] [--rig NAME | --all] [--out FILE]

  --queue-list is a file holding `rig queue list --json` output (a JSON list
  of objects with qitemId/state). --transitions is a file holding a JSON
  object mapping qitemId -> list of {transitionId, state, transitionNote, ts}
  (assembled from per-qitem `rig queue transitions --json <qitem>` calls).
  --live fetches both over the rig CLI with the pinned --json read-only verbs
  (list/show/transitions only); anything else is refused.

  --out writes the reviewable proposal to a file OUTSIDE the mission repo.
  --out pointing at an input tracker is refused fail-closed.

Exit codes: 0 = in sync (every parsed row agrees); 1 = diffs found (TPM
approval required); 2 = fail-closed error (unreadable tracker, unparseable
row, unparseable queue JSON, unreachable queue/rig, --out refusal).

Mapping table (tracker Status cell, case-insensitive substring rules):
  QA PASS signal   "qa pass" in cell            (never bare "awaiting QA")
  PLACED signal    "placed" in cell
  CLOSED signal    "closed" in cell
  DONE signal      word "done" in cell
  STAGED signal    "staged" in cell
  DISPATCHED       "dispatched" in cell
  PARKED signal    "parked" in cell UNLESS "blocker satisfied" also present
                   (the converged "parked-on-QA blocker satisfied" annotation)
  Recorded notes   "note NNN" / "notes NNN" (incl. "+MMM" chains) and bare
                   "(NNN)" parentheticals, e.g. "row note 885", "(1083)"
Queue terminal signal (per qitem): queue state in TERMINAL_QUEUE_STATES, or
the latest (max transitionId) transition state in TERMINAL_QUEUE_STATES, or
its note matching QA PASS|placed|closed|handed-off (case-insensitive).
Diff classes:
  stale-state                        queue terminal, tracker enum not terminal
                                     (STAGED/DISPATCHED, or terminal claimed
                                     while the queue is not terminal)
  parked-satisfied-but-tracker-silent queue terminal, tracker PARKED without
                                     the blocker-satisfied annotation
  missing-convergence-annotation     queue terminal, tracker enum terminal but
                                     the latest queue transition id is not
                                     recorded in the cell
  tracker-row-without-qitem          row records no qitem (em-dash/empty) or
                                     the qitem has no queue entry (suggesting
                                     removal/closure review, never dropped)
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TERMINAL_QUEUE_STATES = {
    "closed",
    "done",
    "handed_off",
    "handed-off",
    "complete",
    "completed",
}
TERMINAL_NOTE_RE = re.compile(
    r"qa\s*pass|placed|closed|handed[_\s-]?off|\bdone\b", re.IGNORECASE
)
NOTE_ID_RES = (
    re.compile(r"[Nn]ote[s]?\s+(\d+)"),
    re.compile(r"\((\d{2,})\)"),
    re.compile(r"\+(\d{2,})"),
)
NO_QITEM_CELLS = {"", "\u2014", "-", "n/a", "none"}
QITEM_RE = re.compile(r"qitem-\d{14}-[0-9a-f]+")


class ReconcileError(Exception):
    """A fail-closed finding (exit 2 class)."""


def load_json_file(path, what):
    try:
        text = Path(path).read_text()
    except OSError as exc:
        raise ReconcileError(f"UNREADABLE {what} '{path}' ({exc})")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReconcileError(f"UNPARSEABLE {what} '{path}' (invalid JSON: {exc})")


def split_row(line):
    cells = line.strip().split("|")
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def is_separator(cells):
    return bool(cells) and all(re.fullmatch(r":?-+:?", c.strip()) for c in cells)


def parse_tracker(path):
    """Parse the Slices table of one tracker; fail closed with named errors."""
    try:
        lines = Path(path).read_text().splitlines()
    except OSError as exc:
        raise ReconcileError(f"UNREADABLE TRACKER '{path}' ({exc})")
    start = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("#") and "slic" in s.lower():
            start = i
            break
    if start is None:
        raise ReconcileError(f"NO SLICE TABLE in '{path}' (no Slices heading)")
    header_idx = None
    for i in range(start, len(lines)):
        if lines[i].strip().startswith("|") and "status" in lines[i].lower():
            header_idx = i
            break
    if header_idx is None:
        raise ReconcileError(f"NO SLICE TABLE in '{path}' (no Status header row)")
    header = split_row(lines[header_idx])
    lowered = [c.lower() for c in header]
    if "status" not in lowered or not any("qitem" in c for c in lowered):
        raise ReconcileError(
            f"TRACKER HEADER '{path}:{header_idx + 1}' lacks required "
            f"Slice/qitem/Status columns (got {header})"
        )
    try:
        slice_idx = lowered.index("slice")
    except ValueError:
        slice_idx = 0
    qitem_idx = next(i for i, c in enumerate(lowered) if "qitem" in c)
    status_idx = lowered.index("status")
    if header_idx + 1 >= len(lines) or not is_separator(
        split_row(lines[header_idx + 1])
    ):
        raise ReconcileError(
            f"UNPARSEABLE TABLE '{path}:{header_idx + 1}' (missing separator row)"
        )
    rows = []
    for lineno, line in enumerate(lines[header_idx + 2 :], start=header_idx + 3):
        if not line.strip().startswith("|"):
            break
        cells = split_row(line)
        if len(cells) != len(header):
            first = cells[0] if cells else "?"
            raise ReconcileError(
                f"UNPARSEABLE ROW '{path}:{lineno}' (expected {len(header)} "
                f"cells, got {len(cells)}; first cell '{first}')"
            )
        if not cells[slice_idx]:
            raise ReconcileError(f"UNPARSEABLE ROW '{path}:{lineno}' (empty slice id)")
        rows.append(
            {
                "file": str(path),
                "line": lineno,
                "slice": cells[slice_idx],
                "qitem": cells[qitem_idx],
                "status": cells[status_idx],
            }
        )
    if not rows:
        raise ReconcileError(f"NO SLICE ROWS in '{path}' (empty Slices table)")
    return rows


def normalize_tracker(cell):
    low = cell.lower()
    return {
        "qa_pass": "qa pass" in low,
        "placed": "placed" in low,
        "closed": "closed" in low or re.search(r"\bdone\b", low) is not None,
        "staged": "staged" in low,
        "dispatched": "dispatched" in low,
        "parked": "parked" in low and "blocker satisfied" not in low,
    }


def recorded_note_ids(cell):
    ids = set()
    for rx in NOTE_ID_RES:
        ids.update(int(m) for m in rx.findall(cell))
    return ids


def queue_terminal(entry, transitions):
    trail = transitions if isinstance(transitions, list) else []
    latest = max(trail, key=lambda t: t.get("transitionId", -1)) if trail else {}
    state = str(entry.get("state", "")).lower() if isinstance(entry, dict) else ""
    tstate = str(latest.get("state", "")).lower()
    note = str(latest.get("transitionNote", ""))
    latest_id = latest.get("transitionId")
    terminal = (
        state in TERMINAL_QUEUE_STATES
        or tstate in TERMINAL_QUEUE_STATES
        or bool(TERMINAL_NOTE_RE.search(note))
    )
    return terminal, latest_id, latest


def check_allowed(argv):
    if (
        len(argv) >= 3
        and argv[0] == "queue"
        and argv[1] in ("list", "transitions")
        and "--json" in argv
    ):
        return
    raise ReconcileError(f"refusing non-read-only rig invocation: {argv}")


def run_rig(rig_bin, args, timeout=60):
    check_allowed(args)
    try:
        proc = subprocess.run(
            [rig_bin, *args], capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise ReconcileError(
            f"UNREACHABLE QUEUE (rig binary not found at {rig_bin}: {exc})"
        )
    except subprocess.TimeoutExpired:
        raise ReconcileError(f"UNREACHABLE QUEUE (rig {' '.join(args)} timed out)")
    if proc.returncode != 0:
        raise ReconcileError(
            f"UNREACHABLE QUEUE (rig {' '.join(args)} exited {proc.returncode}: "
            f"{proc.stderr.strip()[:300]})"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ReconcileError(
            f"UNREACHABLE QUEUE (rig {' '.join(args)} output unparseable as JSON: {exc})"
        )


def propose_cell(row, latest_id, latest_note, parked):
    if parked:
        return (
            f"QA PASS + PLACED canonical (queue note {latest_id}: {latest_note}; "
            f"operator note appended \u2014 parked-on-QA blocker satisfied)"
        )
    return (
        f"QA PASS + PLACED canonical (queue note {latest_id}: {latest_note}; "
        f"operator note appended)"
    )


def diff_row(row, queue_by_id, transitions_by_id):
    cell = row["status"]
    qitem_raw = row["qitem"].strip()
    if qitem_raw in NO_QITEM_CELLS:
        return {
            "class": "tracker-row-without-qitem",
            "reason": "no qitem recorded in row (operator-executed row?)",
            "tracker": cell,
            "queue": "(no qitem recorded)",
            "proposal": (
                "Record the slice qitem in the Slice qitem column or confirm "
                "operator-owned closure; suggested Status once owned: QA PASS + "
                "PLACED canonical (queue note pending; operator note appended)"
            ),
        }
    m = QITEM_RE.search(qitem_raw)
    qid = m.group(0) if m else qitem_raw
    entry = queue_by_id.get(qid)
    if entry is None:
        return {
            "class": "tracker-row-without-qitem",
            "reason": f"queue has no entry for {qid} (suggest removal/closure review)",
            "tracker": cell,
            "queue": "(no queue entry)",
            "proposal": (
                f"Confirm {row['slice']} closure/removal with the TPM, or re-queue "
                f"and record the new qitem; suggested Status once re-owned: QA PASS "
                f"+ PLACED canonical (queue note pending; operator note appended)"
            ),
        }
    trail = transitions_by_id.get(qid, [])
    terminal, latest_id, latest = queue_terminal(entry, trail)
    latest_note = str(latest.get("transitionNote", "")) if latest else ""
    norm = normalize_tracker(cell)
    enum_terminal = norm["qa_pass"] or norm["placed"] or norm["closed"]
    if terminal:
        if not enum_terminal:
            if norm["parked"]:
                return {
                    "class": "parked-satisfied-but-tracker-silent",
                    "reason": "queue shows the QA blocker satisfied; tracker still PARKED",
                    "tracker": cell,
                    "queue": f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})",
                    "proposal": propose_cell(row, latest_id, latest_note, parked=True),
                }
            return {
                "class": "stale-state",
                "reason": "queue is QA-passed/placed/closed; tracker state is stale",
                "tracker": cell,
                "queue": f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})",
                "proposal": propose_cell(row, latest_id, latest_note, parked=False),
            }
        if latest_id is not None and latest_id not in recorded_note_ids(cell):
            return {
                "class": "missing-convergence-annotation",
                "reason": (
                    f"queue latest transition {latest_id} not recorded in tracker cell "
                    f"(recorded {sorted(recorded_note_ids(cell))})"
                ),
                "tracker": cell,
                "queue": f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})",
                "proposal": (
                    f"{cell} (queue note {latest_id}: {latest_note}; "
                    f"operator note appended)"
                ),
            }
        return None
    if enum_terminal:
        return {
            "class": "stale-state",
            "reason": f"tracker claims terminal while queue is {entry.get('state')}",
            "tracker": cell,
            "queue": f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})",
            "proposal": (
                f"Re-verify {row['slice']} with QA, or correct the tracker cell; "
                f"queue-side evidence: {latest_note or entry.get('state')}"
            ),
        }
    return None


def render_diff(row, diff):
    header = (
        f"DIFF [{diff['class']}] {row['file']}:{row['line']} "
        f"slice {row['slice']} qitem {row['qitem'].strip()}"
    )
    return "\n".join(
        [
            header,
            f"  reason:  {diff['reason']}",
            f"  tracker: {diff['tracker']}",
            f"  queue:   {diff['queue']}",
            "  PROPOSED Status cell:",
            f"    {diff['proposal']}",
            f"PROPOSED-CELL:::{diff['proposal']}",
            f"  SUGGESTED queue-note append on {row['qitem'].strip()}: "
            f"Tracker row {row['slice']} converged: {diff['tracker']} -> "
            f"{diff['proposal']}",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diff dispatch tracker tables against queue state (issue #39). Read-only."
    )
    parser.add_argument("--tracker", action="append", required=True)
    parser.add_argument("--queue-list", default=None)
    parser.add_argument("--transitions", default=None)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--rig-bin", default="rig")
    parser.add_argument("--rig", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    try:
        if args.out:
            for tracker in args.tracker:
                try:
                    if Path(args.out).resolve() == Path(tracker).resolve():
                        raise ReconcileError(
                            f"refusing to write proposal to input tracker path '{tracker}' "
                            f"(proposals go OUTSIDE the mission repo for TPM review)"
                        )
                    # Fail closed before doing any work, while the tracker exists check is cheap.
                except ReconcileError:
                    raise
                except OSError as exc:
                    raise ReconcileError(f"UNUSABLE --out '{args.out}' ({exc})")
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

        diffs = []
        for row in rows:
            diff = diff_row(row, queue_by_id, transitions_by_id)
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
                try:
                    Path(args.out).write_text(report + "\n")
                except OSError as exc:
                    raise ReconcileError(f"UNWRITABLE --out '{args.out}' ({exc})")
            print(report)
            return 1
        summary = (
            f"reconcile: in sync \u2014 {len(rows)} rows across "
            f"{len(args.tracker)} tracker(s) agree with queue state."
        )
        if args.out:
            try:
                Path(args.out).write_text(summary + "\n")
            except OSError as exc:
                raise ReconcileError(f"UNWRITABLE --out '{args.out}' ({exc})")
        print(summary)
        return 0
    except ReconcileError as exc:
        print(f"reconcile: FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
