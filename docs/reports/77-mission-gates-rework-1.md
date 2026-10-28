# Rework report — 77-mission-gates, rework cycle 1 (Refs #77)

Branch `fix/77-mission-gates-r1`, base `main @ 00f78bc`. Addresses the
three PR #131 review findings (H1–H3; H4 review-tool promotion declined
as out of scope). Findings below were treated as untrusted: every
path/line re-verified against current code before acting.

## Verdict table

| ID | Verdict | Evidence |
|---|---|---|
| H1 (runbook Flow B gate-creation form) | FIXED, docs-only | `docs/evidence/77-mission-gates-runbook.md:32` showed `rig queue create --gate qa-seat --destination qa-seat@rig --note "..."` — bare create, denied in-seat per V22 (`AGENTS.md:30`: bare `rig queue create` denies in-seat; `--json --verify` required; qitem IDs copied from `--json` output only, never retyped). Now `rig queue create --json --verify --gate qa-seat --destination qa-seat@rig --body-file /tmp/gate-note.md` plus copy-from-JSON instruction (`runbook.md:32-40`) and a V22 parenthetical (`runbook.md:55-58`). `--gate` count = 2 (>= 1, charter-check floor preserved). |
| H2 (QA report table pipes) | FIXED, docs-only | `docs/reports/77-mission-gates-qa.md:24` row-7 cell held literal pipes inside code spans (`` `queue (update\|close)` ``, `` `--state (done\|complete\|closed)` ``) splitting the row. Replaced with `&#124;` entities (render as `\|`, no cell split, content preserved). Verified: header and row 7 both parse to 5 pipe-segments (3 cells). |
| H3 (wire check_recovery_dismissal into production) | CONFIRMED DEFECT → WIRED + E2E-TESTED + RED-PROVEN | Pre-fix trace: `check_recovery_dismissal` / `snapshot_row_state` / `RecoveryDismissalRefused` defined at `scripts/sweep-typed-blocks.py:213-282` with call sites ONLY in `tests/test_mission_gates.py` (unit-level) and the V29 block in `scripts/verify-rigs.sh:3156-3189` — zero invocations in `run_sweep` or any recovery-close path. Dead code in production = REQ-M3 spec-conformance defect. No close hook existed (and none invented): `check_allowed` (`sweep-typed-blocks.py:108-121`) refuses every queue write except unpark-to-in-progress; D2 forbids bot close-to-done. Narrowest refusal point implemented: `run_sweep` retains `report["recovery_guards"][qid]` per evaluated stay-blocked row (`sweep-typed-blocks.py`, stay-blocked branch); new `request_recovery_dismissal(client, ...)` re-reads via `fetch_show`, invokes the guard, logs, returns-or-raises, performs no write, fails closed on unreadable rows. Behavior otherwise preserved (unpark/stay-blocked/dry-run/cursor paths untouched; `tests.test_sweep_typed_blocks` 54/54 still green). E2E proof: `TestProductionRecoveryWiring` (3 tests) drives `run_sweep` → retained snapshot → close-time gate. Red-proofs R1-a (guard neutered → `AssertionError: RecoveryDismissalRefused not raised`, 1 failure) and R1-b (retention removed → `KeyError`, 3 errors), both restored byte-identical → 19/19 GREEN, appended to `docs/evidence/77-mission-gates/red-proofs.log`. |
| H4 (`coderabbit review --agent`) | DECLINED | Review-tool promotion, out of scope per tasking. |

## Files changed

- `docs/evidence/77-mission-gates-runbook.md` (H1 Flow B form + V22 note; Flow C wiring paragraph)
- `docs/reports/77-mission-gates-qa.md` (H2 pipe entities in row 7)
- `scripts/sweep-typed-blocks.py` (H3: `request_recovery_dismissal` + `recovery_guards` retention; additive only — no V-gate marker touched)
- `tests/test_mission_gates.py` (H3: `SweepRecoveryClient` + `stuck_typed_row` + `TestProductionRecoveryWiring`, 16 → 19 tests)
- `docs/evidence/77-mission-gates/red-proofs.log` (R1-a / R1-b entries appended, priors untouched)

Nothing under `specs/`, `rigs/`, `rosters/`, `registry/`, `openspec/` hand-edited (no regen needed — no generator inputs changed).

## Acceptance outputs

- `./scripts/verify-rigs.sh --check-only`: exit 0 — `SUMMARY: 37 checks passed, 0 failed`, V29 PASS (now cites 19 corpus tests).
- `make test`: exit 0 — `Ran 561 tests / OK` (558 prior + 3 new `TestProductionRecoveryWiring`).
- `python3 -m unittest tests.test_mission_gates -v`: exit 0 — `Ran 19 tests / OK`.
- `python3 -m unittest tests.test_mission_gates_prefix -v`: exit 0 — `Ran 6 tests / OK`.
- `python3 -m unittest tests.test_sweep_typed_blocks`: exit 0 — `Ran 54 tests / OK` (neighbor suite, run_sweep report change regression check).
- `python3 scripts/audit_loop.py --self-test`: `SELF-TEST PASSED`.
- `python3 scripts/generate-rigs.py --check-idempotent`: exit 0; the run temporarily changed provenance fields (`resolvedCommit` + `canonicalUrl`) in 16 registry files, those changes were reverted via `git checkout -- registry/`, and the final tree has no registry diff (status shows only the 5 intended files).
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md docs/evidence/77-mission-gates-runbook.md`: no output (exit 1).

## Self-audit notes

- Anything unfinished: nothing. All three findings addressed; H4 deliberately declined per scope.
- Risk call (stated plainly): H3 adds a production-called path (`fetch_show` + guard) to a fail-closed security-relevant flow. Mitigations: additive-only code, no new write verbs, no allowlist changes, unreadable-fails-closed, redaction via the single-source `_redact_for_log`, two red-proofs, neighbor suite green.
- Secrets: dummy fixture ids only; no bearer material; secrets grep clean.
- No pushes performed (coordinator owns PR actions).

(Refs #77; issue stays open by design.)
