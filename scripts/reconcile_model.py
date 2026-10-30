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
state ONLY (note text never terminal). Awaiting-gate prose with no live
gate qitem is the stalled-awaiting-gate diff class (issue #77, REQ-M2):
gateless waiting fails convergence as stalled, never as silent agreement.
A QA PASS affirmation — in a queue note or
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

# 77-mission-gates (REQ-M2): a Status cell waits on a gate in prose when it
# names a gate alongside a waiting verb ("standing by for gate", "awaiting
# gate verdict"). Ordinary waits ("awaiting QA", "blocked on QA gate" with
# no waiting verb) do NOT match — the waiting verb is required so parked /
# staged rows are never over-flagged.
_AWAITING_GATE_RE = re.compile(
    r"(awaiting|waiting for|standing by for)\b.{0,60}\bgate\b",
    re.IGNORECASE,
)

# 81-seat-idle (REQ-I2): a seat is parked-at-prompt while holding an open
# obligation when the prose carries an idle-at-prompt arbitration marker
# alongside a nonzero open-obligation count (the Mission-A watchdog line:
# "You are parked (arbitrated: idle at prompt) while holding 1 open
# obligation"; a tracker cell may state the count bare: "1 open
# obligation"). Both halves are required — obligation-free idle ("queue
# exhausted", "waiting for the baton") and zero-obligation parks never
# match, so legitimate idle stays quiet.
_IDLE_AT_PROMPT_RE = re.compile(r"idle at prompt", re.IGNORECASE)
_OPEN_OBLIGATION_RE = re.compile(r"(\d+)\s+open obligations?", re.IGNORECASE)

# 81-seat-idle (REQ-I2): trail notes that are NOT first-work-action evidence.
# A claim ("claimed"), a handoff receipt ("Handoff received — pulling the
# queue item"), and any parked/watchdog arbitration line are motion without
# work. A work action is any other non-empty note (verdict recorded, files
# filed, QA prose) — conservative: only the known non-work classes are
# excluded, so an unfamiliar note counts as work and keeps the row quiet.
_NON_WORK_NOTE_RES = (
    re.compile(r"\bclaimed\b", re.IGNORECASE),
    re.compile(r"handoff received", re.IGNORECASE),
    re.compile(r"idle at prompt", re.IGNORECASE),
    re.compile(r"\bparked\b", re.IGNORECASE),
    re.compile(r"watchdog", re.IGNORECASE),
)

# 81-seat-idle rework-1 (F4): positive first-work-action markers. A trail
# note that mixes a known non-work event with genuine work evidence (e.g.
# "claimed; verdict recorded, findings filed") counts as work — only a
# note with non-work events and NO work action is excluded, so mixed
# notes stay eligible as work evidence. Tokens grounded in the S0/S1
# corpus vocabulary (verdict filed, QA PASS, PLACED/DONE).
_WORK_ACTION_RE = re.compile(
    r"\b(verdict|filed|files|QA PASS|PLACED|DONE)\b", re.IGNORECASE
)

# 81-seat-idle rework-1 (F2): wake/release prose. A post-park note counts
# as wake evidence only when it names a wake or release event (woken,
# release, resumed, unparked). A watchdog heartbeat or any other note
# lacking wake/release prose is not wake evidence — wake_ts stays unset.
_WAKE_NOTE_RE = re.compile(
    r"\b(wake|woken|woke|released?|resumed?|unparked?)\b", re.IGNORECASE
)


def _is_non_work_only(note):
    """True when a trail note carries only known non-work events (issue #81).

    A mixed note (non-work event alongside work evidence) is NOT
    non-work-only — it counts as a first work action. A note with no
    known non-work event is work by the standing conservative rule
    (unfamiliar notes keep the row quiet). Shared by
    trail_has_work_action and attribute_idle_latency (rework-1 F4).
    """
    if not any(rx.search(note) for rx in _NON_WORK_NOTE_RES):
        return False
    return not bool(_WORK_ACTION_RE.search(note))


def is_idle_park_prose(cell):
    """True when prose shows parked-at-prompt while holding an open
    obligation (issue #81, REQ-I2).

    Pure predicate for the stalled-idle-park diff class: claim-then-park
    with no work action fails convergence as stalled, never as silent
    agreement. Obligation-free idle never matches.
    """
    text = cell or ""
    if not _IDLE_AT_PROMPT_RE.search(text):
        return False
    match = _OPEN_OBLIGATION_RE.search(text)
    if match is None:
        return False
    try:
        return int(match.group(1)) >= 1
    except (ValueError, IndexError):
        return False


def is_awaiting_gate_prose(cell):
    """True when a tracker Status cell waits on a gate in prose (issue #77).

    Pure predicate for the stalled-awaiting-gate diff class: awaiting-gate
    prose with NO live gate qitem reference fails convergence as stalled,
    never as silent agreement.
    """
    return bool(_AWAITING_GATE_RE.search(cell or ""))


class ReconcileError(Exception):
    """A fail-closed finding (exit 2 class)."""


def _git_work_trees(path):
    """Git work trees holding `path`, judged from both its lexical location
    and its resolved target (a tracker symlink can point out of its repo)."""
    found = set()
    try:
        starts = {Path(os.path.abspath(path)).parent, Path(path).resolve().parent}
    except OSError:
        return found
    for here in starts:
        for candidate in (here, *here.parents):
            if os.path.lexists(candidate / ".git"):
                try:
                    found.add(candidate.resolve())
                except OSError:
                    found.add(candidate)
                break
    return found


def refuse_out_path(out, trackers):
    """Fail-closed --out guard (REQ-R2): a proposal must never land on a tracker.

    Refuses (exit 2 via ReconcileError, destination bytes untouched): an --out
    that resolves to any input --tracker path; any tracker-shaped destination
    (a *dispatch-tracker.md filename, or anything inside a sprints/ tracker
    directory) regardless of the input set; any destination inside the git
    work tree that holds an input tracker; and ANY existing file at the
    destination. Only a fresh non-tracker path outside the mission repo
    passes.
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
    # #102: the documented promise is OUTSIDE the mission repo, so an --out
    # inside the git work tree that holds any input tracker is refused too.
    for tracker in trackers:
        for repo in _git_work_trees(tracker):
            if resolved == repo or repo in resolved.parents:
                raise ReconcileError(
                    f"refusing to write proposal inside the mission repo '{repo}' "
                    f"(proposals go OUTSIDE the mission repo for TPM review)"
                )
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


def diff_row(row, queue_by_id, transitions_by_id, envelope_by_id=None):
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
    # Tail: delegate gateless-awaiting-gate detection to the shared
    # classifier (also consumed by generate_trackers.py, REQ-G5), then the
    # 81-seat-idle claim-then-park classifier (same sharing rule: no
    # parallel idle-park mapping anywhere), then the 15-auth-envelope
    # premise-drift classifier (same sharing rule: no parallel premise
    # mapping anywhere).
    stalled = stalled_awaiting_gate_diff(row, queue_by_id, transitions_by_id)
    if stalled is not None:
        return stalled
    stalled = stalled_idle_park_diff(row, queue_by_id, transitions_by_id)
    if stalled is not None:
        return stalled
    return stalled_premise_drift_diff(
        row, queue_by_id, transitions_by_id, envelope_by_id=envelope_by_id
    )


def stalled_awaiting_gate_diff(row, queue_by_id, transitions_by_id):
    """Shared stalled-awaiting-gate classifier (issue #77, REQ-M2).

    Returns the stalled diff when the row's Status waits on a gate in prose
    with NO live gate qitem reference, else None. A --gate qitem with a
    live owner (non-terminal state + a destination session) exempts the row:
    the gate owner owns next action. Pure classification — propose-only
    (REQ-R2), no row state written, never done/complete/closed by this
    module. Both reconcile.py (via diff_row's tail) and
    generate_trackers.py (OTHER-arm carve-out, review-only render) consume
    THIS helper; no command may own a parallel gate mapping (REQ-G5).
    """
    cell = row["status"]
    if not is_awaiting_gate_prose(cell):
        return None
    qitem_raw = row["qitem"].strip()
    if qitem_raw in NO_QITEM_CELLS:
        return None
    m = QITEM_RE.search(qitem_raw)
    qid = m.group(0) if m else qitem_raw
    entry = queue_by_id.get(qid)
    if entry is None:
        queue_evidence = "(no queue entry)"
    else:
        trail = transitions_by_id.get(qid, [])
        _, latest_id, latest = queue_terminal(entry, trail)
        latest_note = str(latest.get("transitionNote", "")) if latest else ""
        queue_evidence = (
            f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})"
        )
    gate_refs = [q for q in QITEM_RE.findall(cell) if q != qid]
    for ref in gate_refs:
        gate_entry = queue_by_id.get(ref)
        if gate_entry is None:
            continue
        gate_trail = transitions_by_id.get(ref, [])
        gate_terminal, _, _ = queue_terminal(gate_entry, gate_trail)
        if not gate_terminal and gate_entry.get("destinationSession"):
            return None
    return {
        "class": "stalled-awaiting-gate",
        "reason": (
            "tracker waits on a gate with no live gate qitem recorded "
            "(no gate owner named; the destination seat owns next action)"
        ),
        "tracker": cell,
        "queue": queue_evidence,
        "proposal": (
            f"Close {row['slice']} done with a closure reason once its "
            f"acceptance evidence is on the row, or create a --gate qitem "
            f"with a live owner and record it here; standing by with no "
            f"gate row is stalled, never a false positive"
        ),
    }


def trail_has_claim(trail):
    """True when the queue trail records a claim (issue #81, REQ-I2)."""
    for transition in trail or []:
        note = str((transition or {}).get("transitionNote") or "")
        if _NON_WORK_NOTE_RES[0].search(note):
            return True
    return False


def trail_has_work_action(trail):
    """True when the queue trail records a first work action (issue #81).

    Only the known non-work classes (claim, handoff receipt,
    parked/watchdog arbitration) are excluded — and only when the note
    carries no work action alongside them; a mixed note (non-work event
    plus work evidence) counts as work, so mixed notes stay eligible as
    work evidence (rework-1 F4). Any other non-empty note counts as work,
    so an unfamiliar note keeps the row quiet (fail-closed against
    over-flagging, never against silence).
    """
    for transition in trail or []:
        note = str((transition or {}).get("transitionNote") or "").strip()
        if not note:
            continue
        if _is_non_work_only(note):
            continue
        return True
    return False


def _parse_ts(value):
    """Parse an ISO-8601 Z timestamp to epoch seconds; None when unparseable."""
    import datetime as _datetime

    try:
        text = str(value or "").strip().replace("Z", "+00:00")
        return _datetime.datetime.fromisoformat(text).timestamp()
    except (ValueError, TypeError, OverflowError):
        return None


def attribute_idle_latency(trail):
    """Report park-to-wake vs work latency for an idle-park row (issue #81).

    Pure report field (inputs for #15/#17): claim_ts is the first claim
    note, park_ts the first idle-park-prose note, work_ts the first work
    note (None when no work action exists), wake_ts the first post-park
    wake/release note (None while still parked: a watchdog heartbeat or
    any other post-park note without wake/release prose is not wake
    evidence). Seconds
    deltas are floats; park_to_wake_s is None while the seat is still
    parked. Report only — never writes tracker or queue state.
    """
    claim_ts = park_ts = work_ts = wake_ts = None
    parked_seen = False
    for transition in trail or []:
        note = str((transition or {}).get("transitionNote") or "")
        ts = str((transition or {}).get("ts") or "")
        if claim_ts is None and _NON_WORK_NOTE_RES[0].search(note):
            claim_ts = ts or None
        if not parked_seen and is_idle_park_prose(note):
            park_ts = ts or None
            parked_seen = True
            continue
        if parked_seen and wake_ts is None and not is_idle_park_prose(note):
            # Rework-1 F2: only a wake/release note counts as wake
            # evidence — a watchdog heartbeat or other note lacking
            # wake/release prose leaves wake_ts unset (still parked).
            if _WAKE_NOTE_RE.search(note):
                wake_ts = ts or None
        if work_ts is None:
            stripped = note.strip()
            if stripped and not _is_non_work_only(note):
                work_ts = ts or None
    claim_s = _parse_ts(claim_ts)
    park_s = _parse_ts(park_ts)
    wake_s = _parse_ts(wake_ts)
    work_s_ts = _parse_ts(work_ts)
    if claim_s is not None and park_s is not None:
        claim_to_park_s = park_s - claim_s
    else:
        claim_to_park_s = None
    if park_s is not None and wake_s is not None:
        park_to_wake_s = wake_s - park_s
    else:
        park_to_wake_s = None
    if claim_s is not None and work_s_ts is not None:
        work_s = work_s_ts - claim_s
    else:
        work_s = 0
    if park_to_wake_s is None:
        note = (
            "park-to-wake vs work: seat still parked (wake pending); "
            f"claim-to-park {claim_to_park_s}s, work share {work_s}s"
        )
    else:
        note = (
            "park-to-wake vs work: park-to-wake "
            f"{park_to_wake_s}s vs work {work_s}s "
            f"(claim-to-park {claim_to_park_s}s)"
        )
    return {
        "claim_ts": claim_ts,
        "park_ts": park_ts,
        "wake_ts": wake_ts,
        "work_ts": work_ts,
        "claim_to_park_s": claim_to_park_s,
        "park_to_wake_s": park_to_wake_s,
        "work_s": work_s,
        "note": note,
    }


def stalled_idle_park_diff(row, queue_by_id, transitions_by_id):
    """Shared stalled-idle-park classifier (issue #81, REQ-I2).

    Returns the stalled diff when the row is claim-then-park: a claim is
    recorded, no work action exists in the trail, and the tracker cell or
    the latest queue note shows parked-at-prompt while holding an open
    obligation — with park-to-wake vs work attribution attached. Obligation-
    free idle and live-gate waiting return None (stay quiet). Pure
    classification — propose-only (REQ-R2), no row state written, never
    done/complete/closed by this module. Both reconcile.py (via diff_row's
    tail) and generate_trackers.py (OTHER-arm carve-out, review-only
    render) consume THIS helper; no command may own a parallel idle-park
    mapping (REQ-G5).
    """
    cell = row["status"]
    qitem_raw = row["qitem"].strip()
    if qitem_raw in NO_QITEM_CELLS:
        return None
    m = QITEM_RE.search(qitem_raw)
    qid = m.group(0) if m else qitem_raw
    entry = queue_by_id.get(qid)
    if entry is None:
        return None
    trail = transitions_by_id.get(qid, [])
    terminal, latest_id, latest = queue_terminal(entry, trail)
    if terminal:
        return None
    if not trail_has_claim(trail):
        return None
    if trail_has_work_action(trail):
        return None
    # The obligation state is read from the tracker cell (the row's
    # declared state): parked-at-prompt while holding an open obligation.
    # The queue trail proves claim and worklessness; the cell proves the
    # park is obligation-bearing. Obligation-free idle and live-gate
    # waiting cells never satisfy this and stay quiet.
    if not is_idle_park_prose(cell):
        return None
    parked_evidence = cell
    latest_note = str((latest or {}).get("transitionNote") or "")
    queue_evidence = (
        f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})"
    )
    attribution = attribute_idle_latency(trail)
    return {
        "class": "stalled-idle-park",
        "reason": (
            "seat claimed then parked idle at prompt while holding an open "
            f"obligation with no work action recorded (parked: {parked_evidence})"
        ),
        "tracker": cell,
        "queue": queue_evidence,
        "proposal": (
            f"Route {row['slice']} for human review: the owner claimed and "
            f"parked without a first work action ({attribution['note']}); "
            f"the owner owns next action (first work action or handoff), "
            f"never a parked prompt while holding the obligation"
        ),
        "attribution": attribution,
    }


# 15-auth-envelope (REQ-E2): the authorized premise vs the live landing.
#
# A row carrying an authorized premise (TPM-verified diff hash + scope
# paths + premise/verify timestamps in the tracker Status cell) whose
# landing diff (latest queue-note landing record) drifted from that
# premise — or which carries an open authorization with no matching
# landing record at all — fails convergence as stalled, never as silent
# agreement. Clean premises (landing hash identical, landing file-set
# inside scope) stay quiet; rows declaring no premise never match.
# Pure classification + report-only premise-age attribution (inputs for
# #17) — propose-only (REQ-R2), no row state written, never
# done/complete/closed by this module.
_PREMISE_RE = re.compile(
    r"authorized premise\s+([0-9a-fA-F]{8,64})\s+scope\s+([^;]+)",
    re.IGNORECASE,
)
_PREMISE_AT_RE = re.compile(r"premise at\s+([^\s;]+)", re.IGNORECASE)
_VERIFY_AT_RE = re.compile(r"verified at\s+([^\s;]+)", re.IGNORECASE)
_LANDING_RE = re.compile(
    r"landing diff\s+([0-9a-fA-F]{8,64})\s+paths\s+([^\s;]+)"
    r"(?:\s+at\s+([^\s;]+))?",
    re.IGNORECASE,
)


def _premise_scope_paths(raw):
    """Split a premise scope list on commas/whitespace; drop empties."""
    return [part for part in re.split(r"[,\s]+", (raw or "").strip()) if part]


def _parse_premise(cell):
    """Extract the authorized premise from a tracker Status cell.

    Returns {"diff_hash", "scope", "premise_ts", "verify_ts"} or None
    when the cell declares no premise (rows without an authorization
    never match the drift class).
    """
    match = _PREMISE_RE.search(cell or "")
    if match is None:
        return None
    scope = _premise_scope_paths(match.group(2))
    if not scope:
        return None
    premise_ts = _PREMISE_AT_RE.search(cell or "")
    verify_ts = _VERIFY_AT_RE.search(cell or "")
    return {
        "diff_hash": match.group(1).lower(),
        "scope": scope,
        "premise_ts": premise_ts.group(1) if premise_ts else None,
        "verify_ts": verify_ts.group(1) if verify_ts else None,
    }


def _parse_landing(note):
    """Extract the landing record from a queue trail note.

    Returns {"diff_hash", "paths", "landing_ts"} or None when the note
    carries no landing record (an open authorization with no matching
    envelope/landing record yet).
    """
    match = _LANDING_RE.search(note or "")
    if match is None:
        return None
    paths = _premise_scope_paths(match.group(2))
    if not paths:
        return None
    return {
        "diff_hash": match.group(1).lower(),
        "paths": paths,
        "landing_ts": match.group(3),
    }


def _scope_covers(scope_paths, landing_paths):
    """Landing paths NOT covered by the premise scope (empty when covered).

    A scope entry covers its exact path and, when it names a directory
    (trailing `/`), everything beneath it. Anything else is a breach.
    Fail-closed before any prefix comparison: a landing path carrying a
    `..` segment (e.g. `src/extra/../outside`) can share a scope
    directory prefix while resolving outside it, so each such path is
    reported uncovered (mirrors the envelope-side rule in
    auth_envelope._scope_covers).
    """
    uncovered = []
    for path in landing_paths:
        if isinstance(path, str) and ".." in path.split("/"):
            uncovered.append(path)
            continue
        covered = False
        for entry in scope_paths:
            if entry.endswith("/"):
                if path == entry.rstrip("/") or path.startswith(entry):
                    covered = True
                    break
            elif path == entry:
                covered = True
                break
        if not covered:
            uncovered.append(path)
    return uncovered


def attribute_premise_age(premise_ts, verify_ts, landing_ts):
    """Report premise age at landing (issue #15, inputs for #17).

    Pure report field: premise age (landing minus premise) and
    verify-to-landing spread in seconds, plus a one-line note. Report
    only — never writes tracker or queue state, never advances rows.
    Unparseable timestamps yield None ages (still flagged by the
    classifier; the age is unknown, not zero).
    """
    premise_s = _parse_ts(premise_ts)
    verify_s = _parse_ts(verify_ts)
    landing_s = _parse_ts(landing_ts)
    if premise_s is not None and landing_s is not None:
        premise_age_s = landing_s - premise_s
    else:
        premise_age_s = None
    if verify_s is not None and landing_s is not None:
        verify_to_landing_s = landing_s - verify_s
    else:
        verify_to_landing_s = None
    if premise_age_s is None:
        note = (
            "premise age unknown at landing "
            f"(premise {premise_ts} -> landing {landing_ts})"
        )
    else:
        note = (
            f"premise age {premise_age_s}s at landing "
            f"(premise {premise_ts} -> landing {landing_ts})"
        )
    return {
        "premise_ts": premise_ts,
        "verify_ts": verify_ts,
        "landing_ts": landing_ts,
        "premise_age_s": premise_age_s,
        "verify_to_landing_s": verify_to_landing_s,
        "note": note,
    }


def stalled_envelope_absence_diff(
    row, premise, landing, queue_evidence, envelope_by_id=None
):
    """Shared envelope-presence gating classifier (issue #134, REQ-E5).

    Returns the stalled diff when the row's landing is CLEAN (hash
    identical, file-set inside scope — established by the caller) but the
    consulted envelope lookup holds no envelope matching the row's
    premise, with premise-age attribution attached. Pure classification —
    propose-only (REQ-R2), read-only against the lookup (no store
    rewrites), no row state written, never done/complete/closed by this
    module. Opt-in by construction: an absent (None) or empty lookup is
    never gating, so the REQ-E2 clean-quiet default is preserved. A
    lookup entry bound to a different premise hash is no envelope.
    Consumed by stalled_premise_drift_diff's clean-landing tail; no
    command may own a parallel envelope-presence mapping.
    """
    if not envelope_by_id:
        return None
    qitem_raw = row["qitem"].strip()
    m = QITEM_RE.search(qitem_raw)
    qid = m.group(0) if m else qitem_raw
    record = envelope_by_id.get(qid)
    if record is not None:
        if isinstance(record, dict):
            for key in ("premise_hash", "diff_hash", "premise"):
                if key in record and str(record[key]).lower() != premise["diff_hash"]:
                    break
            else:
                return None
            detail = (
                "the consulted envelope registry binds that qitem to a "
                "different premise (a wrong-premise envelope is no envelope)"
            )
        else:
            return None
    else:
        detail = (
            "the consulted envelope registry holds no matching envelope "
            "(open authorization with no envelope bound)"
        )
    attribution = attribute_premise_age(
        premise["premise_ts"],
        premise["verify_ts"],
        landing["landing_ts"],
    )
    return {
        "class": "stalled-envelope-absence",
        "reason": (
            "row carries a clean landing for premise "
            f"{premise['diff_hash']} but {detail}"
        ),
        "tracker": row["status"],
        "queue": queue_evidence,
        "proposal": (
            f"Route {row['slice']} for human review: the landing matches "
            f"premise {premise['diff_hash']} yet no envelope bound to that "
            f"premise is on record ({landing['landing_ts']} landing); the "
            "owner owns next action (mint a matching envelope, fresh "
            "premise, or explicit hold)"
        ),
        "attribution": attribution,
    }


def stalled_premise_drift_diff(
    row, queue_by_id, transitions_by_id, envelope_by_id=None
):
    """Shared premise-drift classifier (issue #15, REQ-E2).

    Returns the stalled diff when the row's landing diff drifted from its
    authorized premise (hash mismatch or scope breach), or when the row
    carries an open authorization with no matching landing record — with
    premise-age attribution attached. Clean premises and rows declaring
    no premise return None (stay quiet) unless the opt-in REQ-E5
    envelope-presence gate fires (a populated envelope_by_id lookup with
    no envelope matching the premise; absent/empty lookup stays quiet).
    Pure classification —
    propose-only (REQ-R2), no row state written, never done/complete/
    closed by this module. Both reconcile.py (via diff_row's tail) and
    generate_trackers.py (OTHER-arm carve-out, review-only render)
    consume THIS helper; no command may own a parallel premise mapping.
    """
    cell = row["status"]
    premise = _parse_premise(cell)
    if premise is None:
        return None
    qitem_raw = row["qitem"].strip()
    if qitem_raw in NO_QITEM_CELLS:
        return None
    m = QITEM_RE.search(qitem_raw)
    qid = m.group(0) if m else qitem_raw
    entry = queue_by_id.get(qid)
    if entry is None:
        return None
    trail = transitions_by_id.get(qid, [])
    terminal, latest_id, latest = queue_terminal(entry, trail)
    if terminal:
        return None
    latest_note = str((latest or {}).get("transitionNote") or "")
    queue_evidence = (
        f"state={entry.get('state')} latest_transition={latest_id} ({latest_note})"
    )
    # Bind the newest recognized landing record anywhere in the trail
    # (a clean landing followed by a non-landing note still binds it):
    # scan newest-to-oldest and take the first transitionNote that
    # _parse_landing recognizes, instead of parsing only latest_note.
    landing = None
    ordered = sorted(
        trail if isinstance(trail, list) else [],
        key=lambda t: t.get("transitionId", -1) if isinstance(t, dict) else -1,
        reverse=True,
    )
    for item in ordered:
        note = item.get("transitionNote") if isinstance(item, dict) else ""
        candidate = _parse_landing(str(note or ""))
        if candidate is not None:
            landing = candidate
            break
    attribution = attribute_premise_age(
        premise["premise_ts"],
        premise["verify_ts"],
        landing["landing_ts"] if landing else None,
    )
    if landing is None:
        return {
            "class": "stalled-premise-drift",
            "reason": (
                "row carries an open authorization with no matching landing "
                "record (no landing diff on the queue trail to bind the "
                f"premise {premise['diff_hash']} to)"
            ),
            "tracker": cell,
            "queue": queue_evidence,
            "proposal": (
                f"Route {row['slice']} for human review: the authorized "
                f"premise names diff {premise['diff_hash']} scope "
                f"{', '.join(premise['scope'])} but no landing record binds "
                f"it ({attribution['note']}); the owner owns next action "
                f"(fresh premise, narrowed scope, or explicit hold)"
            ),
            "attribution": attribution,
        }
    uncovered = _scope_covers(premise["scope"], landing["paths"])
    drifted = landing["diff_hash"] != premise["diff_hash"]
    if not drifted and not uncovered:
        # Clean landing: REQ-E2 stays quiet by default; the opt-in REQ-E5
        # presence gate fires only against a consulted (populated) lookup.
        return stalled_envelope_absence_diff(
            row, premise, landing, queue_evidence, envelope_by_id
        )
    if drifted and uncovered:
        reason = (
            f"landing diff {landing['diff_hash']} drifted from authorized "
            f"premise {premise['diff_hash']} and reaches outside scope: "
            f"{', '.join(uncovered)}"
        )
    elif drifted:
        reason = (
            f"landing diff {landing['diff_hash']} drifted from authorized "
            f"premise {premise['diff_hash']}"
        )
    else:
        reason = (
            "landing file-set breaches the authorized scope "
            f"(premise {premise['diff_hash']}): {', '.join(uncovered)}"
        )
    return {
        "class": "stalled-premise-drift",
        "reason": reason,
        "tracker": cell,
        "queue": queue_evidence,
        "proposal": (
            f"Route {row['slice']} for human review: {reason} "
            f"({attribution['note']}); the owner owns next action "
            f"(fresh premise, narrowed scope, or explicit hold)"
        ),
        "attribution": attribution,
    }


def render_diff(row, diff):
    header = (
        f"DIFF [{diff['class']}] {row['file']}:{row['line']} "
        f"slice {row['slice']} qitem {row['qitem'].strip()}"
    )
    lines = [
        header,
        f"  reason:  {diff['reason']}",
        f"  tracker: {diff['tracker']}",
        f"  queue:   {diff['queue']}",
    ]
    # 81-seat-idle (REQ-I2): the idle-park diff carries its park-to-wake
    # vs work attribution as report lines (propose-only inputs for
    # #15/#17, never state writes).
    attribution = diff.get("attribution")
    if isinstance(attribution, dict) and attribution.get("note"):
        lines.append(f"  attribution: {attribution['note']}")
    # 81-seat-idle rework-1 (F3) + 15-auth-envelope (REQ-E2/REQ-E5): the
    # stalled-idle-park, stalled-premise-drift, and stalled-envelope-absence
    # diffs route for human review — never a paste-ready cell. Render their
    # review-routing proposals as SUGGESTED (not paste-ready): no
    # PROPOSED-CELL marker and no "converged" queue-note suggestion (the
    # row has not converged). Every other diff class keeps the existing
    # output below.
    if diff.get("class") in (
        "stalled-idle-park",
        "stalled-premise-drift",
        "stalled-envelope-absence",
    ):
        lines += [
            "  NEEDS-HUMAN-REVIEW: TPM decide; owner owns next action.",
            f"  SUGGESTED (not paste-ready): {diff['proposal']}",
        ]
        return "\n".join(lines)
    lines += [
        "  PROPOSED Status cell:",
        f"    {diff['proposal']}",
        f"PROPOSED-CELL:::{diff['proposal']}",
        f"  SUGGESTED queue-note append on {row['qitem'].strip()}: "
        f"Tracker row {row['slice']} converged: {diff['tracker']} -> "
        f"{diff['proposal']}",
    ]
    return "\n".join(lines)
