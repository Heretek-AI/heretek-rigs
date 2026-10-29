# 81-seat-idle rework-1 QA (PR #132 findings F1–F5) — Refs #81

Worktree: `.lane/trees/81-seat-idle`, branch `feat/81-seat-idle`,
commit `367cb45` (fix record `docs/reports/81-seat-idle-r1-fixes.md`).
Tree was clean at QA start; no code or test file touched by QA.
Do NOT commit — coordinator commits. No pushes. Refs #81 (never Closes #81).
No Unity binding (repo has no Unity project).

## Verdict: PASS with three coverage-gap advisories (F2/F3/F4 unpinned)

All five rework behaviors verified present and causal. The full acceptance
suite is green on the rework tree. Sabotage proofs (details in
`docs/evidence/81-seat-idle/red-proofs.log`, QA-R1…R5 entries):

- **F1 — PINNED, non-vacuous.** Altering the Transcript 3
  invocation-result line turns the new frozen test RED (exit 1,
  `FAILED (failures=1)`); restore → 10/10 prefix tests GREEN.
- **F2 — BEHAVIOR REAL, committed suite vacuous.** Removing the
  `_WAKE_NOTE_RE` gate makes a heartbeat-only trail report
  `wake_ts 2026-10-23T21:34:20.000Z` (probe RED, exit 1, right reason);
  restore → probe GREEN (`wake_ts None`, release trail `53.0s`).
  But the committed 34 tests stay GREEN under the sabotage — no committed
  check pins heartbeat-only → `wake_ts None`.
- **F3 — BEHAVIOR REAL, committed suite vacuous.** Removing the
  `stalled-idle-park` early return restores `PROPOSED-CELL` + `converged`
  output (probe RED, exit 1, right reason); restore → probe GREEN
  (review-only; other classes keep `PROPOSED-CELL`). Committed 34 tests
  stay GREEN under the revert; V30 has no render-shape assertion.
- **F4 — BEHAVIOR REAL, committed suite vacuous.** Neutering
  `_is_non_work_only` excludes the mixed note `claimed; verdict recorded,
  findings filed` from work evidence in both paths (probe RED, exit 1,
  right reason); restore → probe GREEN. Committed 34 tests stay GREEN —
  no fixture uses a genuinely mixed trail note.
- **F5 — prose-only, vacuous as expected.** Restoring the wrong
  `(+53s, +22s park-to-wake)` arithmetic keeps all 34 tests and all five
  V30 evidence markers GREEN. Arithmetic independently verified by hand:
  claim 21:33:29 → wake 21:34:53 = **84s**; park 21:34:00 → wake = **53s**.
  Both `WAKE_TS` constants byte-identical
  (`2026-10-23T21:34:53.000Z` in `tests/test_seat_idle_prefix.py:56`
  and `tests/test_seat_idle.py:58`).

## Checks run (all exit 0 on the unmodified tree)

- `python3 -m unittest tests.test_seat_idle tests.test_seat_idle_prefix` → 34 tests OK.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 38 checks passed, 0 failed`, V30 PASS.
- `make test` → 596 tests OK (105s).
- `python3 scripts/generate-rigs.py --check-idempotent` → pass (registry
  `resolvedCommit` re-lag only — known accepted provenance artifact —
  restored via `git checkout -- registry/`, status clean).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`.
- Post-sabotage re-confirm: 34-test subset OK + verify `SUMMARY: 38
  passed, 0 failed`, V30 PASS; `git status --short` shows only this report
  and the `red-proofs.log` append.

## Advisories (coordinator/implementer decides; QA adds no code)

1. F2/F3/F4 have no committed regression pins. Recommended (one test
   each, following existing style): heartbeat-only trail →
   `wake_ts None` / `park_to_wake_s None`; `render_diff` idle-park →
   `assertNotIn PROPOSED-CELL` + `assertIn SUGGESTED (not paste-ready)`;
   mixed trail note → `trail_has_work_action True` + `work_ts` set.
2. `docs/reports/81-seat-idle-implementation.md:18` still repeats the
   pre-fix `wake +53s` figure (noted in the fix record as left for the
   coordinator; out of QA scope, no edit made).
3. F5 interval prose will remain unpinned by design (evidence prose, not
   behavior) — recorded here for completeness, not as a defect.

## Files changed by QA (2, uncommitted)

- `docs/evidence/81-seat-idle/red-proofs.log` (appended QA-R1…R5 entries)
- `docs/reports/81-seat-idle-r1-qa.md` (this report)
