# QA report — 77-mission-gates rework cycle 2 (Refs #77, PR #131 review follow-up)

Branch `fix/77-mission-gates-r2`, tip `131ec04` (cycle base `e7a53be`).
Worktree `.lane/trees/77-mission-gates-r2`. Verifier wrote nothing except
this report and the QA-R6 red-proof appendix; no commits, no pushes.
Claims below verified against `docs/reports/77-mission-gates-rework-2.md`
(trusted as a checklist, not as evidence).

## 1. Per-check results (all real outputs, unmodified tree unless noted)

| # | Check | Result |
|---|---|---|
| 1 | `./scripts/verify-rigs.sh --check-only` | PASS — exit 0, `SUMMARY: 37 checks passed, 0 failed`; `[PASS] V29 mission-gate ownership (77-mission-gates S2) green: stalled diff + charter markers in 9 leaves + refusal guard + 20 corpus tests pass + S0 evidence present`. All `== V1 ... V29` headers present in order; V1–V28 titles unrenamed, V29 appended. V29's own redaction assertion (`refusal log line carries an unredacted bearer-shaped run`, V29 block in verify-rigs.sh) still present and green. |
| 2 | `make test` | PASS — exit 0, `Ran 562 tests in 108.449s / OK` (matches the claimed 562-family: 561 prior + 1 new redaction test). |
| 3a | `python3 -m unittest tests.test_mission_gates -v` | PASS — exit 0, `Ran 20 tests / OK` (19 prior + new `TestProductionRecoveryWiring.test_close_time_unreadable_log_line_redacted`, confirmed by name in verbose output). |
| 3b | `python3 -m unittest tests.test_sweep_typed_blocks` | PASS — exit 0, `Ran 54 tests / OK` (neighbor suite, no regression). |
| 4 | `python3 scripts/audit_loop.py --self-test` | PASS — `SELF-TEST PASSED` (fail-closed sentinel vs 20 adversarial vectors; static/schema/digest/security checks green). |
| 5 | `python3 scripts/generate-rigs.py --check-idempotent` | PASS — exit 0, `idempotence check passed (two consecutive runs byte-identical)`. Side effect was provenance-only churn (`resolvedCommit` + `canonicalUrl`, 16 registry files, zero non-provenance lines — verified via `git diff` excluding only those two fields, empty remainder) — reverted via `git checkout -- registry/`; final registry diff zero, status clean. |
| 6 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md docs/evidence/77-mission-gates-runbook.md` | PASS — no output, exit 1 (zero secret-shaped strings). |
| 7a | Docs-precision M1 (r1-qa.md row 8 scope) | PASS — row 8 (`docs/reports/77-mission-gates-r1-qa.md:23`) now states `recovery_guards` retained "only for rows that reached a successfully evaluated non-unpark verdict from evaluate_row" and does NOT claim every stay-blocked row populates it. Cross-checked against code: FIVE `report["stay_blocked"].append(qid)` sites in `scripts/sweep-typed-blocks.py` at lines 814, 836, 877, 899, 907 — and ONLY 907 is followed by the `recovery_guards` retention (line 916); the other four continue without populating it. Wording matches code truth. |
| 7b | Docs-precision M3 (rework-1.md idempotence wording) | PASS — `docs/reports/77-mission-gates-rework-1.md:35` now states the run "temporarily changed provenance fields (resolvedCommit + canonicalUrl) in 16 registry files, those changes were reverted via git checkout -- registry/, and the final tree has no registry diff". Matches the independently observed behavior this cycle (16 files, provenance-only, reverted, clean). |
| 7c | Docs-precision M2 (SKIP) | PASS (no-op verified) — cited claim text ("no semantic change" / "exact-shape callers") does not exist at `r1-verification.md:33-36`; the file was left untouched as claimed. No invented fix. |

## 2. Red-proofs (QA-R6 series appended to `docs/evidence/77-mission-gates/red-proofs.log`; priors untouched)

| ID | Sabotage | RED (must fail) | GREEN (restored) |
|---|---|---|---|
| QA-R6a (M4 redaction) | `{redact(str(exc))}` to `{exc}` in the unreadable-row log line (`scripts/sweep-typed-blocks.py:315`; raised message untouched) | `test_close_time_unreadable_log_line_redacted` FAILED exit 1: `AssertionError: 'redacted' not found in '... flagged row unreadable at close time: daemon blew up, bearer leaked: AAAA(45-char run); ...'` — raw secret-shaped run verbatim in the log line | `cp` + `cmp` byte-identical (sha256 d739edcb pre/post match) to `Ran 20 tests / OK` |
| QA-R6b (full battery: V29) | `class RecoveryDismissalRefused` to `class RecoveryDismissalREFUSED_REMOVED` in `scripts/sweep-typed-blocks.py` | Full verify exit 1: `[FAIL] V29/77-mission-gates: scripts/sweep-typed-blocks.py lost refusal marker 'class RecoveryDismissalRefused'` (fail-closed, no SUMMARY) | `cp` + `cmp` byte-identical to `[PASS] V29 ... 20 corpus tests pass ...` + `SUMMARY: 37 checks passed, 0 failed`, exit 0 |

No vacuous checks: every sabotaged gate went RED and every restore went GREEN with verbatim outputs.

## 3. Findings

No blocking findings. F-series: none.

- The rework's M1–M4 claims reproduce exactly (scoped row-8 wording, M2 skip justification, 16-file churn wording, one-token redaction + 20/562 counts + R2-a red-proof).
- M5 decline is out of scope per tasking.
- Awareness note, not a finding against this cycle: `scripts/sweep-typed-blocks.py` still interpolates raw `{exc}` into SKIP/STAY-BLOCKED log lines at the four non-retention stay-blocked sites — outside this cycle's scope (M4 covered only the refusal log path per the REQ-M4 redaction guarantee).

## 4. Final tree state

`git status --short` shows exactly the two intended files, both mine
(this report plus the red-proofs.log QA-R6 appendix). All sabotage reverted and
proven (`cmp` byte-identical + sha256 match + clean status after each restore). Nothing
under `specs/`, `rigs/`, `rosters/`, `registry/`, `openspec/` modified.
No commits, no pushes.

(Refs #77; issue stays open by design.)
