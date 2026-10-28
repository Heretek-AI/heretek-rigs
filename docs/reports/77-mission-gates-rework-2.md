# Rework report — 77-mission-gates, rework cycle 2 (Refs #77)

Branch `fix/77-mission-gates-r2`, base `main @ e7a53be`. Addresses the
four PR #131 review findings (M1–M4; M5 review-tool promotion declined
as out of scope). Findings were treated as untrusted: every path/line
re-verified against current code before acting. Minimal diffs; no
V-gate text touched; nothing under `specs/`, `rigs/`, `rosters/`,
`registry/`, `openspec/` hand-edited.

## Verdict table

| ID | Verdict | Evidence |
|---|---|---|
| M1 (Production wiring report row overclaims `recovery_guards` scope) | CONFIRMED IMPRECISION → FIXED, docs-only | `docs/reports/77-mission-gates-r1-qa.md:23` row 8 said `run_sweep` retains `report["recovery_guards"][qid]` "per stay-blocked row". Code truth re-traced in `scripts/sweep-typed-blocks.py`: FIVE separate `report["stay_blocked"].append(qid)` sites — lines 814 (unreadable flagged-row transitions), 836 (unreadable blocker/verdict qitem), 877 (`DataSourceError` from `evaluate_row`), 899 (`unpark`-write failure), 907 (`evaluate_row` non-`unpark` verdict) — and ONLY the last (907) is followed by the `recovery_guards` retention (916). The other four append to `stay_blocked` WITHOUT populating `recovery_guards`. Row 8 now states the accurate scope: retained only for rows that reached a successfully evaluated non-`unpark` verdict from `evaluate_row`; the four fail-closed/retry/`unpark`-failure sites do not populate it. |
| M2 ("no semantic change" / "exact-shape callers" in r1-verification.md:33-36) | SKIP — cited claim text does not exist at the cited lines | Read `docs/reports/77-mission-gates-r1-verification.md` in full. Lines 33-36 describe the `run_sweep` diff mechanics (report key + 5-line retention block) and contain no "no semantic change" statement and no text about callers. Grep for `no semantic\|exact-shape\|caller` over the file returns exactly ONE hit: line 42 (`54/54 GREEN confirms no semantic change to existing paths`), a separate accurate statement about the neighbor-suite regression result, not a claim about exact-shape callers. Nothing to fix without inventing a claim; left untouched. |
| M3 (`--check-idempotent` result omits intermediate provenance churn) | CONFIRMED OMISSION → FIXED, docs-only | `docs/reports/77-mission-gates-rework-1.md:35` said "exit 0, no registry churn (status shows only the 5 intended files)" — accurate about the FINAL state but silent about the intermediate temp-churn. Now states: the run temporarily changed provenance fields (`resolvedCommit` + `canonicalUrl`) in 16 registry files, those changes were reverted via `git checkout -- registry/`, and the final tree has no registry diff — matching what `docs/reports/77-mission-gates-r1-qa.md` row 5 already records. |
| M4 (unreadable-row handler logs raw `DataSourceError`) | CONFIRMED DEFECT → FIXED + CORPUS-TESTED + RED-PROVEN | `scripts/sweep-typed-blocks.py:311-316`: the `except DataSourceError` branch interpolated `{exc}` RAW into the refusal LOG line while the RAISED `RecoveryDismissalRefused` message already omitted it — violating the wave's secrets rule (every new log path through `_redact_for_log`) and the REQ-M4 redaction guarantee. Fix (one token): log line now interpolates `{redact(str(exc))}` via the `redact` already bound at the function top; message shape, raised text, and refusal semantics unchanged. New corpus test `TestProductionRecoveryWiring.test_close_time_unreadable_log_line_redacted` proves a secret-shaped (`"A"*45`) `DataSourceError` is redacted in the log line (contains "unreadable at close time" + "redacted", zero `[A-Za-z0-9_-]{40,}` runs) while the raised message is unchanged in shape. Red-proof R2-a appended to `docs/evidence/77-mission-gates/red-proofs.log` (priors untouched): redaction reverted → test RED showing the raw 45-char run verbatim in the log line → restored `cmp` byte-identical → 20/20 GREEN. |
| M5 (`coderabbit review --agent`) | DECLINED | Review-tool promotion, out of scope per tasking. |

## Files changed

- `scripts/sweep-typed-blocks.py` (M4: `{exc}` → `{redact(str(exc))}` in the unreadable-row log line; one line, additive redaction only)
- `tests/test_mission_gates.py` (M4: `test_close_time_unreadable_log_line_redacted`, 19 → 20 tests)
- `docs/evidence/77-mission-gates/red-proofs.log` (R2 entry appended, priors byte-preserved)
- `docs/reports/77-mission-gates-r1-qa.md` (M1 row-8 scope wording)
- `docs/reports/77-mission-gates-rework-1.md` (M3 idempotence-result wording)
- `docs/reports/77-mission-gates-rework-2.md` (this report)

Nothing under `specs/`, `rigs/`, `rosters/`, `registry/`, `openspec/` modified (no regen needed — no generator inputs changed).

## Acceptance outputs

- `./scripts/verify-rigs.sh --check-only`: exit 0 — `SUMMARY: 37 checks passed, 0 failed`, V29 PASS (now cites 20 corpus tests; V-gate text untouched by this cycle — the count is computed by the script).
- `make test`: exit 0 — `Ran 562 tests / OK` (561 prior + 1 new redaction test).
- `python3 -m unittest tests.test_mission_gates -v`: exit 0 — `Ran 20 tests / OK`.
- `python3 -m unittest tests.test_sweep_typed_blocks -v`: exit 0 — `Ran 54 tests / OK` (neighbor suite, no regression).
- `python3 scripts/audit_loop.py --self-test`: `SELF-TEST PASSED`.
- `python3 scripts/generate-rigs.py --check-idempotent`: exit 0 — `idempotence check passed (two consecutive runs byte-identical)`. Side effect was provenance-only churn (`resolvedCommit` + `canonicalUrl`, 16 registry files, zero non-provenance lines — verified via `git diff`) — reverted via `git checkout -- registry/`; final status clean. (On the dirty pre-commit worktree the same command refuses by design, exit 2, "refusing to bake provenance on a dirty checkout".) No registry file hand-edited at any point.
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md docs/evidence/77-mission-gates-runbook.md`: no output (exit 1, clean).

## Self-audit notes

- Anything unfinished: nothing. The `--check-idempotent` byte-identical proof was taken on the clean committed tree (exit 0, two runs byte-identical; 16-file provenance re-stamp verified provenance-only and reverted; final status clean).
- Risk call (stated plainly): M4 touches a fail-closed security-relevant log path. Mitigations: one-token change reusing the bound `redact` choke point, message shape and raise semantics preserved, dedicated corpus test, red-proof R2-a, neighbor suite green.
- Secrets: dummy fixture ids/runs only (`"A"*45` scratch run inside the test, never a real bearer); evidence-path secrets grep clean.
- No pushes performed (coordinator owns PR actions). Commit carries `Refs #77` (issue stays open by design; never `Closes #77`).

(Refs #77; issue stays open by design.)
