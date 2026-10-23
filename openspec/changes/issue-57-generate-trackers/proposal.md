# Proposal: issue-57-generate-trackers — generate dispatch-tracker proposals from queue state

## Status

Spec-only proposal (no implementation). Deferred option (a) from issue #39 /
change `remediate-39-reconcile` (tasks.md T6), tracked as
[heretek-rigs #57](https://github.com/Heretek-AI/heretek-rigs/issues/57)
("generate dispatch trackers from queue state"). The reconcile-diff command
(`scripts/reconcile.py`, REQ-R1..R4, 28/28 `test_reconcile` green) shipped
first and is the prerequisite: it produces the drift corpus that justifies
generation. This change MUST consume the reconcile row model rather than
reinventing it (plan Q5). All premises below were verified read-only from
disk in this worktree (`scripts/reconcile.py`, `tests/test_reconcile.py`,
`gh issue view 57`); no code was touched.

## Motivation

The reconcile diff converted drift discovery into TPM review, but the last
mile is still hand-toil: after every QA+placement turn the operator pastes 7
converged Status cells (plus queue-note appends) by hand from `PROPOSED-CELL`
markers. The Wave-1 evidence (issue #39: 7 rows hand-edited + 7 notes
appended) recurs every wave. A generator that emits the full converged
tracker content — every row, paste-ready, with queue-note evidence attached —
turns approval into a byte-comparable review instead of 7 manual pastes.

## Boundaries (at IMPLEMENTATION time; this change ships spec only)

- Touch ONLY: a new `scripts/generate_trackers.py` command, one `Makefile`
  target, and read-only parsing of mission-side dispatch trackers
  (`Slice | Owner seat | Output | Slice qitem | Status`, `qitem-<ts>-<hex>`).
  Trackers remain human-owned markdown.
- The existing `make generate` target already deterministically generates
  the fleet (`fleet/fleet.yaml` → 51 AgentSpecs / 8 RigBundles / Roster /
  Registry); the tracker wiring MUST use a distinct target name
  (`make generate-tracker`) so the fleet gate is never shadowed or
  overloaded. No changes to `fleet/`, `specs/`, `rigs/`, `rosters/`,
  `registry/`.
- This change itself ships ONLY the spec package
  (`openspec/changes/issue-57-generate-trackers/` + minimal `AGENTS.md`
  discipline patch). The generator is NOT implemented here; the
  importable-module refactor of `reconcile.py` is specified as G-T1 work,
  not performed now.

## Non-goals (explicit)

- Auto-applying generated output to trackers, or any write to queue state
  (queue is the authority on status; tracker rows are the thing corrected;
  TPM approval required — plan Q4, extends reconcile REQ-R2).
- Cross-wave rollup: per-tracker rows only; a parent row is emitted only on
  its own qitem diff (plan Q9).
- Fixing the queue CLI default output (issue #44 territory): the generator
  consumes explicitly machine-readable `--json` output as-is.

## Acceptance (see tasks.md)

After a QA+placement turn, `generate_trackers.py` emits a proposal whose
Status cells, applied to a scratch copy of the tracker, re-run through
`scripts/reconcile.py` to zero diffs (exit 0 "in sync") — with zero
hand-authored cell text by the operator. Returnable from #57: tracker and
queue agree with zero hand-edits (the edits become approvals of a generated
proposal, not discoveries or pastes).
