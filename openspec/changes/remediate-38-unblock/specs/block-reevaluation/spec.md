# Delta spec: event-driven re-evaluation of typed-external blocks

## ADDED Requirements

### Requirement: REQ-BU1 — Park-time satisfaction predicate for typed-external blockers
Every row parked on a typed non-qitem blocker (`external:<what>`,
`fold:<what>`, `auth:<what>`) MUST record a machine-checkable satisfaction
predicate at park time: WHAT evidence satisfies the block and WHERE it lands
(blocking qitem id, verdict artifact path, or explicit-follow-up convention).
The predicate MUST travel with the row (transition note and/or `--summary`/
`--continuation` fields — implementer picks the exact carrier, documents it,
and the sweep MUST read that carrier and no other). A typed-external park
without a predicate MUST be rejected by the seat runbook (operator-visible
error, not silent park).

#### Scenario: Predicate-less park is rejected
- WHEN a seat attempts a typed-external park with no machine-checkable
  predicate in the documented carrier THEN the runbook path rejects it with
  an operator-visible error and no HELD row is created.

### Requirement: REQ-BU2 — Note-landed re-evaluation sweep
A repo-side sweep (new script under `scripts/`, plus its scheduling —
watchdog-job attachment and/or cadence definition, implementer picks and
documents) MUST re-evaluate each HELD row carrying a typed-external blocker
when either trigger fires: (a) a note/transition lands on the parked row
itself, or (b) a note/transition lands on the blocker referenced by the
predicate (blocking qitem, verdict row). Trigger detection MUST key on the
append-only `transitions` log (cursor per row, no timestamp-guessing). If the
predicate is satisfied, the sweep MUST unpark via the existing route only:
`update --state in-progress --reopen` with an audit note citing the
satisfying evidence. If not satisfied, the sweep MUST record the evaluation
(transition note or sweep log — implementer picks, QA-observable) with NO
state change.

#### Scenario: Verdict note unparks without operator surgery
- WHEN a note lands on a parked-on-verdict row (or on its blocking verdict
  qitem) AND the predicate is satisfied THEN the next sweep run unparks the
  row to `in-progress` via `update --state in-progress --reopen` with an
  evidence-citing audit note, with no operator-issued `--state` change.

### Requirement: REQ-BU3 — Explicit satisfy record without state surgery
An operator or seat MUST be able to record blocker-satisfaction explicitly
using only existing verbs: a defined note convention (e.g.
`SATISFIED: <blocker> <evidence-ref>` — exact string fixed by the
implementer and documented in the runbook) appended via `update` (note-only,
no `--state`). The sweep MUST treat a well-formed satisfy record as
predicate-met on its next run, bounded by one sweep cycle. Malformed satisfy
records MUST be ignored with a recorded evaluation, never acted on.

#### Scenario: Satisfy note unparks within one cycle; malformed does not
- WHEN a well-formed satisfy note lands THEN the row unparks within one
  sweep cycle; WHEN a malformed satisfy note lands THEN the row stays
  blocked with a recorded evaluation.

### Requirement: REQ-BU4 — No timer-only wakes for typed-external blocks
A typed-external HELD row MUST NOT rely solely on `--wake-after`. At park
time the row MUST carry at least one live wake: a live blocker qitem in
`--on`, an attached watchdog job, or sweep coverage per REQ-BU2. The seat
runbook MUST state this as a park-time checklist item.

#### Scenario: Timer-only park is a checklist violation
- WHEN a typed-external park is created with only `--wake-after` and no
  live blocker qitem, watchdog job, or sweep coverage THEN it violates the
  documented park-time checklist (observable in review/audit).

### Requirement: REQ-BU5 — Fail-closed evaluation, auditable trail
Every re-evaluation MUST append to the audit trail (row transition note or
sweep log). Ambiguous, partial, or contradictory evidence MUST resolve to
stay-blocked + recorded evaluation. The sweep MUST support a log-only
(`--dry-run`) mode that reports would-unpark rows without mutating state.
The sweep MUST NEVER close a row as `done` — unpark targets `in-progress`
only; `done` requires the verdict/acceptance path. The sweep MUST be
idempotent across reruns (per-row transition cursor; a satisfied predicate
MUST NOT produce duplicate unpark transitions).

#### Scenario: Ambiguity stays blocked; reruns do not duplicate
- WHEN evidence is ambiguous THEN the row stays blocked with a recorded
  evaluation; WHEN the sweep reruns over an already-unparked row THEN no
  duplicate unpark transition is emitted AND no run ever emits `state=done`.

### Requirement: REQ-BU6 — Upstream `satisfy` request tracked, never assumed
An upstream `@openrig/cli` feature request for a `satisfy` transition
(typed-blocker satisfaction recording durable evidence + unpark + owner
nudge, mirroring `resolve` for leg-1 parks) MUST be filed with the W1-03/
W1-04 evidence, and its URL/number MUST be recorded in the change's report.
The repo-side sweep MUST NOT assume the verb exists; if it later lands,
adoption is a separate change.

#### Scenario: Sweep works with today's CLI
- WHEN the upstream `satisfy` verb does not exist THEN the sweep still
  unparks via existing verbs AND the upstream request URL is recorded in
  the implementation report.

### Requirement: REQ-BU7 — Returnable replay
A parked-on-verdict row MUST transition to in-progress (or onward to `done`
via the normal acceptance path) within one sweep cycle of the verdict note
landing, with no operator-issued `--state` change. QA MUST replay the
W1-03/W1-04 shape (blocked row + landed verdict evidence + unblock note) and
observe the unpark.

#### Scenario: W1-03/W1-04 shape unparks on replay
- WHEN a blocked row with landed verdict evidence and an unblock note (the
  W1-03/W1-04 shape) is replayed THEN the row reaches `in-progress` within
  one sweep cycle with zero operator `--state` intervention.
