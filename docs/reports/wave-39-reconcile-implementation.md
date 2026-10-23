# Wave 39 Reconcile — implementation report

Stage: `wave-39-reconcile` (change `remediate-39-reconcile`, issue #39).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile`
Branch: `remediate/39-reconcile`.

## Claims

- Implemented `scripts/reconcile.py`: a read-only tracker-vs-queue reconcile
  DIFF command (REQ-R1..R4). Never modifies a tracker or queue state; emits
  paste-ready proposed replacement Status cells + suggested queue-note
  appends for TPM approval; exit 0 + "in sync" iff every parsed row agrees,
  exit 1 on diffs, exit 2 on fail-closed errors.
- All three drift classes from the issue are flagged distinctly and proven
  by failing-then-passing tests: `stale-state`, `missing-convergence-annotation`,
  `parked-satisfied-but-tracker-silent`, plus `tracker-row-without-qitem`
  (REQ-R4 scenario: named diff, never a silent drop).
- `make reconcile TRACKER=... [OUT=...]` wired (live `--json` read-only
  queue verbs); `make verify` SUMMARY is **26/0** (25 audit-baselined checks
  untouched + exactly one appended V10 block, no renumbering); `make test`
  runs 89 tests green (incl. 19 new); `openspec validate
  remediate-39-reconcile` passes.
- Red-proof: sabotaging the stale-state rule fails 2 tests; restored file
  returns to 19/19 green.

## Tracker-shape grounding (read-only, mission repo)

Parsed live (never written) from
`/home/john/Projects/heretek-asset-manager/docs/sprints/`:

- `wave1-dispatch-tracker.md` (converged): `## Slices` table, columns
  `Slice | Owner seat | Output | Slice qitem | Status`; converged cells read
  e.g. `QA PASS + PLACED 6/6 canonical (wave1-qa-report; operator note
  appended; OBS-01 resolved — WHY in row note 885)` and `... operator note
  appended — parked-on-QA blocker satisfied`; slice qitems are
  `qitem-YYYYMMDDHHMMSS-<hex>`; statuses span STAGED/DISPATCHED/PARKED/
  QA PASS/PLACED/DONE/CLOSED + prose annotations.
- `phase0-dispatch-tracker.md`: same 5-column shape with `Output file |
  Slice qitem` columns and DELIVERED/awaiting-gate states (non-terminal rows
  vs non-terminal queue = in sync, no over-reporting).
- `wave2-dispatch-tracker.md`: operator-executed `W2-01` row records `—`
  for Slice qitem → classified `tracker-row-without-qitem` with reason
  "no qitem recorded in row", fail-closed per REQ-R4 (never silently
  skipped), TPM resolves by recording a qitem or confirming operator
  ownership.
- Queue JSON shape grounded in `tests/fixtures/live-health/` +
  `scripts/live-health.py`: `queue list --json` → list of
  `{qitemId, state, ...}`; `queue transitions --json <qitem>` → list of
  `{transitionId, state, transitionNote, ts}`. `--live` shells only these
  two read-only verbs with `--json` enforced (mirrors `check_allowed`
  discipline); offline `--queue-list/--transitions` files serve tests and
  air-gapped runs.

Mapping table implemented (see `scripts/reconcile.py` docstring): QA PASS =
`"qa pass"` substring (bare "awaiting QA" never matches); PARKED counts only
without the "blocker satisfied" annotation; recorded note ids from `note
NNN` / `(NNN)` / `+MMM`; queue-terminal = closed/done/handed_off/complete
state OR terminal latest-transition state/note (QA PASS|placed|closed|
handed-off). Note-freshness is evaluated at convergence checkpoints only
(terminal queue rows); in-flight rows on both sides agree — no new row
semantics invented beyond the spec's four diff classes.

## No-mission-write record

- The mission repo saw zero writes: only `read` calls against its tracker
  files. All fixtures are synthetic in `/tmp` (tests) or inline in the
  verify block (`mkdtemp`, removed afterwards).
- `scripts/reconcile.py` opens trackers read-only; `--out` is refused
  fail-closed (exit 2, destination bytes untouched) when it resolves to an
  input tracker, to any tracker-shaped path (`*dispatch-tracker.md` or
  inside a `sprints/` directory, regardless of the input set), or to ANY
  existing file — enforced up-front plus `O_EXCL` exclusive-create at both
  write sites (rework-1 closes the exact-match-only gap: the auditor's
  `--tracker <scratch> --out <tracker byte-copy>` repro now exits 2 with
  the victim md5-identical). Fresh non-tracker `--out` paths still write
  (exit 1 on diffs / 0 in sync); read-only proven by byte-comparison in
  both the unit tests and the V10 verify block.
- `git status` in this worktree shows only: `M Makefile`, `M
  scripts/verify-rigs.sh`, `?? scripts/reconcile.py`, `??
  tests/test_reconcile.py`, plus this report.

## Files changed

- `scripts/reconcile.py` (new, +x): parser (real table parser, not regex),
  mapping table, four diff classes, proposal renderer with
  `PROPOSED-CELL:::` machine-readable lines for the T4 replay, offline +
  `--live` queue sources, fail-closed errors, `--out` refusal.
- `tests/test_reconcile.py` (new, 19 tests): drifted pre-convergence Wave-1
  replica (7 rows), converged pair, read-only + paste-ready proposals,
  F1 `--out` refusal quartet (scratch tracker byte-copy, tracker-named
  fresh path + sprints/ location, existing non-tracker file, fresh-path
  write-through) alongside the original exact-match test,
  fail-closed set (missing tracker, unparseable row naming file:line,
  missing qitem, unreachable queue), T4 replay-to-zero, live-mode fake-rig
  pair.
- `Makefile`: `reconcile` target + `test_reconcile.py` in `test`.
- `scripts/verify-rigs.sh`: appended V10 block only (one `ok()`).

## Verification outputs (exact commands, exit codes)

- `python3 -m unittest tests/test_reconcile.py -v` → 19 tests, OK
  (15 original + 4 F1 refusal tests).
- Sabotage run (stale-state rule disabled) → FAILED (failures=2);
  restored → OK.
- `make verify` → `SUMMARY: 26 checks passed, 0 failed` (exit 0) +
  advisory live-health output (unchanged behavior).
- `make test` → `Ran 85 tests ... OK` (exit 0).
- `openspec validate remediate-39-reconcile` → `Change
  'remediate-39-reconcile' is valid`.

## Skipped / deferred (stated plainly)

- Full generation (option (a), trackers-as-a-view): explicitly deferred per
  the principal decision and tasks.md T6 — reconcile now, generate later.
  T6 follow-up filed as
  https://github.com/Heretek-AI/heretek-rigs/issues/57
  (`gh issue create` exit 0; body = the deferred `remediate-39-generate`
  design sketch from `design.md`: generate-tracker-from-queue deferred
  scope, reconcile-diff as prerequisite, TPM-approval requirement).
  tasks.md T6 checked off with the URL recorded in-package.
- `docs/reports/remediate-39-reconcile-implementation.md` (tasks.md T6
  filename): written instead as `docs/reports/wave-39-reconcile-implementation.md`
  per the stage binding (`docs/reports/<stage>-implementation.md`).
- No QA dispatch, no merge, no push (per instructions).
