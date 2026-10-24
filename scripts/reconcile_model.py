#!/usr/bin/env python3
"""reconcile_model.py — shared tracker-vs-queue row model (issues #39, #57).

Importable home of the reconcile row semantics: markdown-table parsing
(parse_tracker), Status-cell normalization (normalize_tracker), note-id
extraction (recorded_note_ids), queue-terminal detection (queue_terminal),
per-row diffing (diff_row), paste-ready cell shapes (propose_cell,
normalize_proposal_note), the fresh-out guard (refuse_out_path,
write_out_exclusive), and the read-only rig fetchers (check_allowed,
run_rig). Both scripts/reconcile.py (the diff command) and
scripts/generate_trackers.py (the proposal emitter) consume THIS module;
no command may own a parallel parser, normalizer, or enum-mapping (REQ-G5).

Behavior-identical to the former inline implementation in
scripts/reconcile.py: the G-T1 refactor moved these definitions verbatim.
The locked tracker enum is STAGED, DISPATCHED, PARKED, QA PASS, PLACED,
DONE, CLOSED + OTHER(<raw>); the queue terminal signal is entry/last-transition
state ONLY (note text never terminal). A QA PASS affirmation — in a queue note or
a tracker cell — counts only when the text opens with `QA PASS` and carries no
negator (not/no/never/n't), fail token, or pending token (pending/awaiting/re-run); `placed`/`closed` arms are likewise
void under negation (`NOT placed` affirms nothing).
"""

import json
import os
import re
import subprocess
from pathlib import Path

TERMINAL_QUEUE_STATES = {
    "closed",
    "done",
    "handed_off",
    "handed-off",
    "complete",
    "completed",
}

# M7 (#84): an affirmation counts only when the text OPENS with QA PASS
# (anchored — mid-cell "… QA PASS …" prose affirms nothing) and carries no
# negator or fail token ("QA pass NOT granted", "QA PASS failed" affirm
# nothing). Same rule for queue notes and tracker cells.
QA_PASS_ANCHORED_RE = re.compile(r"^QA PASS\b", re.IGNORECASE)
# `no` followed by a hyphen is a compound closure token (`no-follow-on`,
# `no-op`), not a negation of the pass (#105 review).
_NEGATOR_RE = re.compile(r"\b(not|never)\b|\bno\b(?!-)|n['\u2019]t\b", re.IGNORECASE)
_FAIL_TOKEN_RE = re.compile(r"\b(fail|failed|fails|failure|failing)\b", re.IGNORECASE)
# #105 review: a deferred pass ("QA PASS pending re-run", "QA PASS (awaiting
# gate)") is not a pass yet — fail closed on these too.
_PENDING_TOKEN_RE = re.compile(
    r"\b(pending|awaiting|await|re-?run|tbd|wip|in[- ]progress|provisional|conditional)\b",
    re.IGNORECASE,
)


def _affirmative_qa_pass(text):
    """True only for an un-negated, un-failed opening `QA PASS`."""
    stripped = (text or "").strip()
    if not QA_PASS_ANCHORED_RE.search(stripped):
        return False
    if _NEGATOR_RE.search(stripped):
        return False
    if _FAIL_TOKEN_RE.search(stripped):
        return False
    if _PENDING_TOKEN_RE.search(stripped):
        return False
    return True


NOTE_ID_RES = (
    re.compile(r"[Nn]ote[s]?\s+(\d+)"),
    re.compile(r"\((\d{2,})\)"),
    re.compile(r"\+(\d{2,})"),
)
NO_QITEM_CELLS = {"", "\u2014", "-", "n/a", "none"}
QITEM_RE = re.compile(r"qitem-\d{14}-[0-9a-f]+")
TRACKER_OUT_BASENAME_RE = re.compile(r"dispatch-tracker\.md$", re.IGNORECASE)


class ReconcileError(Exception):
    """A fail-closed finding (exit 2 class)."""


def refuse_out_path(out, trackers):
    """Fail-closed --out guard (REQ-R2): a proposal must never land on a tracker.

    Refuses (exit 2 via ReconcileError, destination bytes untouched): an --out
    that resolves to any input --tracker path; any tracker-shaped destination
    (a *dispatch-tracker.md filename, or anything inside a sprints/ tracker
    directory) regardless of the input set; and ANY existing file at the
    destination. Only a fresh non-tracker path passes.
    """
    try:
        resolved = Path(out).resolve()
    except OSError as exc:
        raise ReconcileError(f"UNUSABLE --out '{out}' ({exc})")
    for tracker in trackers:
        try:
            if resolved == Path(tracker).resolve():
                raise ReconcileError(
                    f"refusing to write proposal to input tracker path '{tracker}' "
                    f"(proposals go OUTSIDE the mission repo for TPM review)"
                )
        except ReconcileError:
            raise
        except OSError as exc:
            raise ReconcileError(f"UNUSABLE --out '{out}' ({exc})")
    if TRACKER_OUT_BASENAME_RE.search(resolved.name):
        raise ReconcileError(
            f"refusing to write proposal to tracker-shaped path '{out}' "
            f"(proposals go OUTSIDE the mission repo for TPM review)"
        )
    if "sprints" in {part.lower() for part in resolved.parts}:
        raise ReconcileError(
            f"refusing to write proposal inside a sprints tracker directory '{out}' "
            f"(proposals go OUTSIDE the mission repo for TPM review)"
        )
    if os.path.lexists(out) or resolved.exists():
        raise ReconcileError(
            f"refusing to overwrite existing file '{out}' "
            f"(proposals go to a fresh non-tracker path OUTSIDE the mission "
            f"repo for TPM review)"
        )


def write_out_exclusive(out, text):
    """Write the proposal to a fresh path; never overwrite (REQ-R2).

    The O_EXCL create re-checks at write time so a file that appeared after
    the up-front refuse_out_path() check is still refused, never clobbered.
    """
    try:
        fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ReconcileError(
            f"refusing to overwrite existing file '{out}' "
            f"(proposals go to a fresh non-tracker path OUTSIDE the mission "
            f"repo for TPM review)"
        )
    except OSError as exc:
        raise ReconcileError(f"UNWRITABLE --out '{out}' ({exc})")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
    except OSError as exc:
        raise ReconcileError(f"UNWRITABLE --out '{out}' ({exc})")


def load_json_file(path, what):
    try:
        text = Path(path).read_text(encoding="utf-8")
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
        lines = Path(path).read_text(encoding="utf-8").splitlines()
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
    # M7 (#84): negation-aware. qa_pass needs an affirmative opening QA PASS;
    # placed/closed are void under negation or fail tokens (so "NOT placed"
    # affirms nothing). staged/dispatched keep substring detection; parked
    # keeps the "blocker satisfied" carve-out.
    low = cell.lower()
    negated = (
        bool(_NEGATOR_RE.search(cell))
        or bool(_FAIL_TOKEN_RE.search(cell))
        or bool(_PENDING_TOKEN_RE.search(cell))
    )
    return {
        "qa_pass": _affirmative_qa_pass(cell),
        "placed": "placed" in low and not negated,
        "closed": ("closed" in low or re.search(r"\bdone\b", low) is not None)
        and not negated,
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
    # M7 (#84): terminal ONLY on state (entry or latest-transition state).
    # Note text — however QA-flavoured — is never terminal; negated notes
    # ("QA pass NOT granted") must not converge a row.
    trail = transitions if isinstance(transitions, list) else []
    latest = max(trail, key=lambda t: t.get("transitionId", -1)) if trail else {}
    state = str(entry.get("state", "")).lower() if isinstance(entry, dict) else ""
    tstate = str(latest.get("state", "")).lower()
    latest_id = latest.get("transitionId")
    terminal = state in TERMINAL_QUEUE_STATES or tstate in TERMINAL_QUEUE_STATES
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


def normalize_proposal_note(note):
    """Collapse a queue note to a single paste-safe line for proposals.

    Queue notes are interpolated into markdown table Status cells, where a
    raw `|` would split the row and embedded newlines/multi-space would
    break the proposal lines. `|` becomes `/` and every whitespace run
    (including newlines) collapses to a single space. Proposal insertions
    only — the `queue:` diagnostic fields keep the raw note byte-identical.
    """
    return " ".join(str(note).replace("|", "/").split())


def propose_cell(row, latest_id, latest_note, parked):
    note = normalize_proposal_note(latest_note)
    if parked:
        return (
            f"QA PASS + PLACED canonical (queue note {latest_id}: {note}; "
            f"operator note appended \u2014 parked-on-QA blocker satisfied)"
        )
    return (
        f"QA PASS + PLACED canonical (queue note {latest_id}: {note}; "
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
                    f"{cell} (queue note {latest_id}: "
                    f"{normalize_proposal_note(latest_note)}; "
                    f"operator note appended)"
                ),
            }
        return None
    if enum_terminal:
        evidence_note = normalize_proposal_note(latest_note)
        return {
            "class": "stale-state",
            "reason": f"tracker claims terminal while queue is {entry.get('state')}",
            "tracker": cell,
            "queue": f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})",
            "proposal": (
                f"Re-verify {row['slice']} with QA, or correct the tracker cell; "
                f"queue-side evidence: {evidence_note or entry.get('state')}"
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
