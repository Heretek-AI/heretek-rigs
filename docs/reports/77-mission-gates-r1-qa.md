# QA report — 77-mission-gates rework cycle 1 (Refs #77, PR #131 review follow-up)

Branch `fix/77-mission-gates-r1`, tip `94ec266` (cycle base `00f78bc`).
Worktree `.lane/trees/77-mission-gates-r1`. Verifier wrote nothing except
this report and the QA-R5 red-proof appendix; no commits, no pushes.
Claims below verified against `docs/reports/77-mission-gates-rework-1.md`
(trusted as a checklist, not as evidence).

## 1. Per-check results (all real outputs, unmodified tree unless noted)

| # | Check | Result |
|---|---|---|
| 1 | `./scripts/verify-rigs.sh --check-only` | PASS — exit 0, `SUMMARY: 37 checks passed, 0 failed`; `[PASS] V29 mission-gate ownership (77-mission-gates S2) green: stalled diff + charter markers in 9 leaves + refusal guard + 19 corpus tests pass + S0 evidence present`. All `== V1 ... V29` headers present in order; V1–V28 titles unrenamed, V29 appended. |
| 2 | `make test` | PASS — exit 0, `Ran 561 tests in 110.585s / OK` (matches the claimed 561-family: 558 prior + 3 new `TestProductionRecoveryWiring`). |
| 3a | `python3 -m unittest tests.test_mission_gates -v` | PASS — exit 0, `Ran 19 tests / OK` (16 prior + 3 `TestProductionRecoveryWiring`: sweep-retains-snapshot/refuses, permits-once-moved, refuses-when-unreadable). |
| 3b | `python3 -m unittest tests.test_sweep_typed_blocks` | PASS — exit 0, `Ran 54 tests / OK` (neighbor suite; `run_sweep` report change causes no regression). |
| 3c | `python3 -m unittest tests.test_mission_gates_prefix` | PASS — exit 0, `Ran 6 tests / OK` (bonus; S0/fixture pins still green). |
| 4 | `python3 scripts/audit_loop.py --self-test` | PASS — `SELF-TEST PASSED` (fail-closed sentinel vs 20 adversarial vectors; static/schema/digest/security checks green). |
| 5 | `python3 scripts/generate-rigs.py --check-idempotent` | PASS — exit 0, `idempotence check passed (two consecutive runs byte-identical)`. Side effect was provenance-only churn (`resolvedCommit` + `canonicalUrl` b17d83d → 94ec266, 16 registry files; zero non-provenance lines) — verified via `git diff`, reverted via `git checkout -- registry/`; status clean. |
| 6 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md docs/evidence/77-mission-gates-runbook.md` | PASS — no output, exit 1 (zero secret-shaped strings). |
| 7a | Runbook Flow B queue form (H1) | PASS — `runbook.md:32` shows `rig queue create --json --verify --gate qa-seat --destination qa-seat@rig --body-file /tmp/gate-note.md` (permitted form, no bare create); lines 35-36 carry the copy-the-ID-from-`--json`-output instruction (never retyped; bare output advisory-only and denied in-seat); lines 55-58 carry the V22 parenthetical. `--gate` count = 2 (>= 1). Conforms to `AGENTS.md:30`. |
| 7b | QA report table pipes (H2) | PASS — header `\| # \| Check \| Result \|` = 4 pipe-segments (3 cells); row 7 (`Safety audit ...`, file line 24) = 4 pipe-segments. `&#124;` entities render as pipes without splitting cells. |
| 8 | Production wiring (H3), code + behavioral | PASS — code: `run_sweep` retains `report["recovery_guards"][qid] = {flagged_qitem, flagged_snapshot}` only for rows that reached a successfully evaluated non-`unpark` verdict from `evaluate_row` (the stay-blocked branch at that site); the four fail-closed/retry/`unpark`-failure stay-blocked sites (unreadable flagged row; unreadable blocker/verdict qitem; `DataSourceError` from `evaluate_row`; `unpark`-write failure) append to `stay_blocked` without populating `recovery_guards` (`sweep-typed-blocks.py` stay-blocked branches); `request_recovery_dismissal` re-reads via `client.fetch_show`, invokes `check_recovery_dismissal`, logs, returns-or-raises, performs no write, fails closed on unreadable rows. Behavioral (independent scratch drive `/tmp/opencode/qa-r1-wiring.py`, not the rework's tests): retained keys `['flagged_qitem', 'flagged_snapshot']`, qid match, snapshot == flag-time; unchanged-row dismissal REFUSED with zero writes; after owner action (`statusCell` advance) dismissal `permitted`, still zero writes. |

## 2. Red-proofs (QA-R5 series appended to `docs/evidence/77-mission-gates/red-proofs.log`; priors untouched)

| ID | Sabotage | RED (must fail) | GREEN (restored) |
|---|---|---|---|
| QA-R5a (REQ-M3 wiring) | Guard CALL neutered in `request_recovery_dismissal` (direct `permitted` return; `check_recovery_dismissal` itself intact) in `scripts/sweep-typed-blocks.py` | Independent scratch drive: `UNCHANGED-DISMISSAL: PERMITTED (BAD)` through the real `run_sweep` → retained-snapshot → close-time-gate flow, exit 0 | `git checkout` + `cmp` byte-identical → `UNCHANGED-DISMISSAL: REFUSED (GOOD)` + `CHANGED-DISMISSAL: permitted`, zero writes both ways |
| QA-R5b (full battery) | Closure bullet removed from 1 of 9 rendered leaves | Full verify exit 1: three `[FAIL] V29 ... lost charter marker` lines + digest mismatches; `SUMMARY: 35 checks passed, 5 failed` | `git checkout` + `cmp` byte-identical → `[PASS] V29 ...` + `SUMMARY: 37 checks passed, 0 failed`, exit 0 |

No vacuous checks: every sabotaged gate went RED and every restore went GREEN.
Adjacent observation (logged in red-proofs.log, not a finding): removing only
the bullet TITLE in the `specs/` source leaf trips the shared-skill tree-hash
lock (`34 passed, 1 failed`, exit 1) rather than V29 — V29 keys on the three
marker strings, the hash lock keys on bytes. Both layers fail closed.

## 3. Findings

No blocking findings. F-series: none.

- The rework's three H1–H3 claims reproduce exactly (queue form, pipe
  entities, wiring + 19/561 counts). H4 decline is out of scope per tasking.
- Pre-existing note (not introduced by this cycle): the wave-0 QA report's
  row-2 text still says `Ran 16 tests` for the mission-gates corpus while the
  tree now ships 19 — stale prose in a superseded report, superseded by this
  report; V29 itself cites 19. Left untouched (not mine to rewrite history).

## 4. Final tree state

`git status --short` shows exactly the two intended files, both mine
(this report plus the red-proofs.log appendix). All sabotage reverted and
proven (`cmp` byte-identical + clean status after each restore). Nothing
under `specs/`, `rigs/`, `rosters/`, `registry/`, `openspec/` modified.
No commits, no pushes.

(Refs #77; issue stays open by design.)
