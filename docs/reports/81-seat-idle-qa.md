# QA report — 81-seat-idle (Refs #81)

Verifier run 2026-10-29 in worktree `.lane/trees/81-seat-idle` at HEAD
`9461324` (implementation `2bf02ac` + clean-regen leaves `9461324`).
Baseline `git status --short` was clean on entry; generator provenance
clean (no DIRTY stamps — committed-tree regen, unlike the dev-dirt
self-audit in the implementation report).

## Checks run (all exit 0 on the unmodified tree)

| Stage | Command | Result |
|---|---|---|
| S0 | `python3 -m unittest tests.test_seat_idle_prefix -v` | 9 OK, exit 0 |
| S0 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/81-seat-idle-prefix.md` | exit 1 (clean) |
| S1 | `python3 -m unittest tests.test_seat_idle -v` | 24 OK, exit 0 |
| S1/S2/S3 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 38 checks passed, 0 failed`, V30 PASS, exit 0 |
| S1/S3 | `python3 scripts/generate-rigs.py --check-idempotent` | byte-identical, exit 0 (run twice) |
| S2 | `make test` | `Ran 595 tests OK`, exit 0 |
| S2 | `python3 scripts/audit_loop.py --self-test` | `SELF-TEST PASSED`, exit 0 (one transient exit-1 observed on first invocation, all lines PASS; immediate re-run exit 0 — rerun-confirmed green, see note) |
| S3 | `grep -c daemon:stuck-sweep runbook` / `grep -c park-to-wake runbook` | 6 / 5 (both >= 1) |
| S3 | secret-scan over prefix + runbook + red-proofs.log | all exit 1 (zero 40+ runs) |

Note on the transient: the first `audit_loop.py --self-test` invocation
exited 1 while printing only `[PASS]` lines; the two subsequent runs
(including a clean-redirected run) exited 0 with `SELF-TEST PASSED`. The
self-test shells out to `verify-rigs.sh` and prompt/file checks; the
single blip did not reproduce and no tree state changed between runs.
Recorded here, not hidden.

Note on idempotence: `--check-idempotent` rewrites registry
`resolvedCommit` stamps to current HEAD (`9461324`, the known one-commit
re-lag — committed leaves pin `2bf02ac`). This dirtied 16 registry files;
reverted via `git checkout -- registry/` and status confirmed clean.
Verify's 38/0 was proven on the committed tree both before and after.

## Red-proofs (QA live sabotage, all logged in `docs/evidence/81-seat-idle/red-proofs.log`)

| Check | Sabotage | RED (right reason) | Restore |
|---|---|---|---|
| S1a flagged classification | `return None` top of `stalled_idle_park_diff` | `test_mission_a_pattern_flagged_stalled` FAIL, `unexpectedly None` (silent), exit 1 | checkout, corpus 24 OK |
| S1b/S1c quiet guards | same S1a sabotage | both quiet tests OK under sabotage (quiet both ways, non-vacuous) | 24 OK incl. both-ways tests |
| S1d daemon source | early `persisted` return in daemon arm of `validate_handoff_source` | TestDaemonSource 3 failures, operator collision, exit 1 | checkout, 5 OK |
| S2 dismissal guard | `if ... == ...:` → `if False:` in `check_recovery_dismissal` | `RecoveryDismissalRefused not raised`, exit 1 | checkout, 4 OK |
| V30 gate | rename `def attribute_idle_latency` | verify exit 1, `37 passed, 1 failed`, V30 FAIL | checkout, 38/0 V30 PASS |

Vacuous checks: **none**. Every acceptance check failed under targeted
sabotage and passed on restore. `git status --short` after all reverts
showed only the two intended QA files (this report + red-proofs.log
append); all sabotage edits fully reverted.

## Verdict

`VERDICT: PASS` — S0→S3 acceptance green, red-proofs non-vacuous,
evidence secret-clean, tree clean apart from this report and the
red-proofs log append. Refs #81 (never Closes #81). No commits made;
coordinator to commit.
