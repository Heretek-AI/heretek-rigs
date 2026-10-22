# QA verdict: wave-38-unblock (remediate-38-unblock, commit 40bc8b5)

## Verdict: QA-CLEAN (no blocking findings; one non-blocking observation F1)

## Checks run (all on unmodified tree except sabotage, all reverted)
| # | Check | Command | Result |
|---|---|---|---|
| 1 | Wave-1 gate intact | `make verify` | PASS — SUMMARY 22 passed / 0 failed, exit 0; live-health advisory WARN only |
| 2 | Full suite | `make test` | PASS — 42 tests OK, exit 0 |
| 3 | Live-health suite | `python3 -m unittest tests/test_live_health.py` | PASS — 21 tests OK |
| 4 | Spec validity | `openspec validate remediate-38-unblock` | PASS — valid |
| 5a | REQ-BU7 baseline stuck shape | T1 test (recorded W1-03 shape ends blocked) | PASS |
| 5b | REQ-BU2 replay unparks via spec route | test_replay_w103_shape_unparks_with_spec_route | PASS + sabotage-sensitive (S7/Sa family) |
| 5c | REQ-BU5 idempotency | test_rerun_is_idempotent_no_duplicate_unpark | PASS |
| 5d | REQ-BU5 dry-run purity | test_dry_run_reports_but_mutates_nothing | PASS + RED-proven (S7, RC=1) |
| 5e | REQ-BU5 never-done | test_sweep_never_emits_done | PASS + RED-proven (S5c+d, RC=1); two independent guards |
| 5f | REQ-BU3 satisfy convention + malformed | TestSatisfyConvention + evaluation tests | PASS + RED-proven (S4, RC=1) |
| 5g | REQ-BU5 ambiguity/re-arm/pending/bare-assertion | 4 fail-closed tests | PASS + each RED-proven (Sa, S3b, S2b, S1; RC=1 each) |
| 5h | REQ-BU5 dangling ref | test_dangling_..._names_ref | PASS + RED-proven (Sd, RC=1) |
| 5i | REQ-BU1/BU4 park guard | 6 TestParkWrapper tests | PASS + RED-proven (S6, S6b; RC=1) |
| 6 | Live read-only dry-run | `scripts/sweep-typed-blocks.py --dry-run` | PASS — 9 evaluated / 4 would-unpark (incl. W1-03 t927, W1-04 t1065) / 5 stay-blocked; unparked=0; both W1 rows confirmed still `blocked` after |
| 7 | Structural incapacity (no done) | builder/guard probe | PASS — done refused at 2 layers |
| 8 | Degraded-input paths (d) | D1/D2/D3 ad-hoc exercises | PASS — SKIP + stay-blocked + {} cursor, no crashes |
| 9 | Makefile diff | `git diff 69f2514..HEAD -- Makefile` | PASS — 1-line test-target extension only; verify-rigs.sh untouched |
| 10 | Anti-stub | grep audit | CLEAN |

## Findings
- F1 (non-blocking observation): `NEGATIONS` tuple in sweep-typed-blocks.py is never referenced — `_word_hits` hardcodes its own negation set (`no|zero|without|none|not`; omits still/pending/awaiting, which is load-bearing for the W2-06 fix via the citation/authority gate instead). Dead constant only; no behavior impact. Suggest removing or wiring it in a follow-up.
- No vacuous checks: all 9 sabotage injections produced RED (RC=1); two naive sabotages (S2, S3, S5a) stayed green for documented structural reasons and were superseded by gate-accurate sabotages that went RED.

## Deferred / out-of-stage (correctly not executed)
- Live pilot unpark runs (runbook §4, operator-executed; --reopen pilot risk recorded in implementation report).
- Watchdog-job/cron wiring (documented recommendation only; creating live jobs would mutate live state).

## Evidence
- `docs/evidence/wave-38-unblock/red-proofs.log` (this stage's full sabotage + live-read record).
- Implementation claims verified: file list matches `git show --stat HEAD`; upstream issue URL recorded (report cites mvschwarz/openrig#1785); no-live-mutation record corroborated (live rows still blocked post-QA; only --dry-run invocations ran).

## State
- `git status --short` shows only untracked `docs/evidence/wave-38-unblock/` + this report. No commits made. Sabotage-only edits, all reverted.
