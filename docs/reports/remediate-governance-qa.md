# QA report — remediate-governance (Wave 3: M6-M8, audit #66)

- Stage: `remediate-governance`, worktree `.lane/trees/remediate-governance`, branch `remediate/audit-66-p0-p1-governance`
- Scope: M6 (`scripts/audit_loop.py`, #79), M7 (`scripts/sweep-typed-blocks.py` #83 + `scripts/reconcile_model.py` #84), M8 (`scripts/check-envelope.py`, #92). No Unity binding.
- Implementation report: `docs/reports/remediate-governance-implementation.md` (3 milestone commits `59786ed`, `6bbd59b`, `330f862` + stage-report commit `bc4776c`)
- Evidence: `docs/evidence/remediate-governance/qa-run.log` (commands + outputs), `docs/evidence/remediate-governance/red-proofs.log` (4 sabotages + restores)
- Verdict: **PASS** — all 10 checks green, 4/4 sabotages RED with clean restore, 0 vacuous checks. Tree left with implementation commits intact; only `docs/evidence/` added by QA (no commits made by QA).

## Per-check results

| # | Check | Result |
|---|---|---|
| M6.1 | `python3 scripts/audit_loop.py --self-test` exits 0, 15 vectors (7 kept + 8 new), each asserting FINDINGS_DETECTED | PASS — `SELF-TEST PASSED ... 15 adversarial test vectors`. New vectors cover: `##` depth-2 with colon, `###` without colon, `####` deep header, bold/emoji/paren BROKEN cells, P1 Defect-Matrix cell, sabotage non-yes row. Pre-fix MISS in NOTES (scratch red_m6.py, 8/8 MISS), independently re-verified by sabotage 1. |
| M6.2 | Spot-check hardened matchers live (each returns FINDINGS_DETECTED) | PASS — `## HR-x` no-colon, `**BROKEN**`, P1 matrix cell, sabotage non-yes row all FINDINGS_DETECTED with specific reasons. |
| M7.3 | #83 cases A (self-written SATISFIED) and B (token-overlap blocker + legacy-overlap note) stay-blocked | PASS — both unit tests OK; full TestAuthBlockerHardening 11/11 OK. Overlap fixture asserts non-empty token overlap in-test (non-vacuous by construction). |
| M7.4 | #84 fixture (QA pass NOT granted; NOT placed, state in-progress) exits 1 NEEDS-HUMAN-REVIEW — run live | PASS — live CLI: `scripts/reconcile.py` rc=1 stale-state (tracker claims terminal while queue is in-progress); `scripts/generate_trackers.py` rc=1 NEEDS-HUMAN-REVIEW, zero PROPOSED-CELL::: markers. |
| M7.5 | make test sweep + reconcile suites pass; new overlap/TPM/negation tests non-vacuous | PASS — `Ran 248 tests ... OK`. New: 11 sweep + 7 reconcile. Sabotage 2 makes case B unpark (RED); sabotage 3 makes 3 negation tests fail exit-0 in-sync (RED). |
| M7.6 | Non-auth paths unchanged (auth-only gating) | PASS — new logic behind `is_auth` guard; overlap kept for non-auth, operator-only authority in else branch; scope-guard test OK. |
| M8.7 | PUSH-to-main inversion: REFUSE rc=1, inverted test passes, NOTES one-liner present | PASS — live PUSH-main rc=1 trunk refusal; bare-main + M8 PUSH tests OK; NOTES line 281 reason recorded. No other test weakened (69/69 OK). |
| M8.8 | Representative #92 rows live REFUSE each; derivation table present | PASS — 8 live rows rc=1 (leading-dot, .git, expired-min multi-deadline, issued-after-now, unknown seat, non-TPM verifier, non-link audit, PUSH main). Live-min control correctly ACCEPTs (min governs). Rows 1-20 + 2 controls table matches NOTES row list. |
| M8.9 | Full make test (248) + verify-rigs.sh --check-only (28/0) | PASS — `Ran 248 tests ... OK`; `SUMMARY: 28 checks passed, 0 failed.` |
| M8.10 | verify-rigs.sh, Makefile, render-seat.py, seat-sandbox.sh, send-authenticated.sh, fleet/fleet.yaml untouched | PASS — `git diff main...HEAD -- <those six>` empty. |

## Red-proof results (all RED, all restored green)

| Sabotage | Injected defect | Re-run | Result | Restore proof |
|---|---|---|---|---|
| 1 (M6) | HR_HEADER_RE to pre-fix exactly-### + colon shape | audit_loop.py --self-test | RED exit 1: M6 vector V1 missed (## HR-4.1 to NO_FINDINGS) | checkout, self-test exit 0 |
| 2 (M7 sweep) | evaluate_row to pre-fix overlap OR-branch for all parks | case A + B tests | RED exit 1: case B unpark != stay-blocked. Case A still blocked — actor gate holds independently | checkout, 11/11 OK |
| 3 (M7 reconcile) | queue_terminal to state-OR-qa-pass-note | TestNegationAwareTerminal | RED exit 1, 3 failures: both #84 fixtures exit 0 in sync (exact pre-fix misclassification) | checkout, 7/7 OK |
| 4 (M8) | Trunk set to (HEAD,) only | PUSH main/master/bare-main tests | RED exit 1, 3 failures, each rc=0 ACCEPT | checkout, 69/69 OK |

Final `git status --short` shows only `?? docs/evidence/remediate-governance/` (QA logs). No vacuous checks found.

## Limitations — merge-blocker assessment

All three are stated in the implementation report and grounded in NOTES; none is a merge-blocker:

1. **Bare-TPM ambiguity** (a second TPM-role seat would make the shorthand ambiguous; today exactly one tpm/scrum seat, ids fleet-derived and pinned in-test). **M10 follow-up.** Shorthand matches the envelope template; retirement condition recorded.
2. **xyz123 accepts as a named human** (no human registry; free text outside void-set/fleet-sets is audit-recorded as a named party). **M10 follow-up.** Every machine-checkable case refuses; residual needs a human-registry source (out of M8 scope).
3. **QA PASS, no issues-style cells now non-terminal** (spec-literal negator list; canonical cells never contain such tokens, 248/248 green proves no regression). **Not a blocker — fail-closed is the safe direction** for ambiguous prose.
