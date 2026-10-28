# Proposal: remediate-39-reconcile — tracker-vs-queue reconcile diff command

## Status
Spec-only proposal (no implementation). Addresses heretek-rigs issue #39
("Dispatch tracker docs drift from queue state; reconcile is manual
operator toil"). All premises verified read-only before authoring; no code
touched. This is HANDOFF.md option (b): a `reconcile` diff command for TPM
approval now; option (a) (generate tracker from queue, single source of
truth) is explicitly deferred to a follow-up change.

## Motivation
Hand-maintained dispatch tracker markdown drifts from queue reality within
the same night: rows read STAGED/awaiting QA after QA PASS + placement,
and only a manual operator edit pass restores truth. Two sources of truth,
no reconciliation. Evidence (Asset-Manager Wave 1, 2026-10-22):

- `docs/sprints/wave1-dispatch-tracker.md` read STAGED/awaiting QA
  (W1-01/02/06/07), PARKED (W1-04), DISPATCHED (W1-05) after all 7 slices
  were QA-passed and placed to 45 canonical paths (same pattern noted for
  the Phase-0 tracker: stale PARKED/blocked rows on delivered files).
- The operator hand-edited all 7 rows + appended queue notes to 7 slice
  rows + parent to converge them — pure toil, zero judgment.

No reconcile/generate tooling exists today (verified): `Makefile:16-79`
targets are `help generate idempotent verify test bootstrap-seats seed
gate audit-sessions topology guard-profiles sidecars-up sidecars-down
bundle-check audit-loop` — no tracker target; `scripts/` contains no
tracker/reconcile script.

## Boundaries
- Touch ONLY (at implementation time): a new `scripts/reconcile.*`
  command, one `Makefile` target, and (read-only) parsing of
  `docs/sprints/wave*-dispatch-tracker.md` + machine-readable queue
  listings. Trackers remain human-owned markdown; the command MUST NOT
  auto-edit them.
- Queue CLI itself is out of scope (#42/#44 territory): the command
  consumes machine-readable queue output as-is.
- No changes to `fleet/`, `specs/`, `rigs/`, `rosters/`, `registry/`.

## Non-goals (explicit deferral)
- Full generation (option (a), trackers-as-a-view): DEFERRED. This change
  proposes diffs for TPM approval; generation needs its own design tree
  (row-ownership, note-append semantics, parent-rollup rules) and its own
  change package. A follow-up `remediate-39-generate` change MAY supersede
  this one; until then this diff command is the control.
- Auto-applying diffs, editing queue state from tracker state (queue is
  the authority on status; tracker rows are the thing corrected), and
  cross-wave rollups beyond per-tracker diffs.

## Acceptance (see tasks.md)
After a QA+placement turn, running `reconcile` surfaces every drifted row
(the 7 Wave-1 row classes) as a proposed update; the TPM approves/applies
them; re-running `reconcile` reports an empty diff — with zero hand-diffing
by the operator. Returnable from #39: tracker and queue agree with zero
hand-edits (the edits become approvals of proposed diffs, not discoveries).
