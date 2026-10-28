# Rework-cycle-1 drift-guard verification — Wave C provisioning-gate-74 (CodeQL fix, Refs #74)

- Stage/wave id: `provisioning-gate-74` rework-cycle-1 drift-guard (audit only; no code fixed, no code changed by auditor).
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/provisioning-gate-74`
- Branch: `feat/provisioning-gate-74` @ `19fa735` (T3 `ac44602` + fix `941ff77` + QA evidence `19fa735`).
- Date (UTC): 2026-10-25.
- Spec read from disk: `openspec/changes/provisioning-gate-74/specs/provisioning-gate/spec.md` (REQ-P1/P2/P3/P4/G1). AGENTS.md read from disk (one-rule + conventions + secrets rules).
- Unity binding: N/A (no Unity content in this repo).

## 1. Fix-scope audit (read from disk, checked against code)

- Fix commit `941ff77` touches exactly one production file: `scripts/render-seat.py` (+6/−1), confined to the REQ-P1 MCP warn block at `:606-618`. It introduces `_raw74` (raw catalog `command` leading token, e.g. `@TOOLS@/bin/r2mcp`) and logs it instead of the substituted absolute artifact `_art74` (CodeQL `py/clear-text-logging-sensitive-data`). Commit message says `Refs #74`, never `Closes #74`.
- Warn still names server + seat + artifact and is still loud: auditor re-ran the QA fixture render (dummy 0600 secrets, bare tools fixture + `@gotgenes` stub under `/tmp/opencode/dg74-*`, `PATH` stripped to emptybin) — `render-seat.py --role binary-reverse-eng --rig defensive-sec-and-red-team --pod red --dry-run --allow-missing-secrets` → exit 0, stderr carries `warn: red-binary-reverse-eng@defensive-sec-and-red-team: radare2 disabled, missing tool artifact: @TOOLS@/bin/r2mcp`, 10 `missing tool artifact` warns total, `radare2` entry renders `"enabled": false`. Leak scan of full stderr: 0 hits for the tmpdir path (`/tmp/opencode/dg74`), 0 host-absolute secrets/tools paths. REQ-P1 satisfied (degrade-loudly, never silent).
- Pre-existing warns untouched (confirmed by read + `git diff ac44602..HEAD`): `:507` (`warn: {session}: opencode-go.key missing, auth disabled`) and `:597` (`warn: {session}: {srv_name} disabled, missing secrets: ...`) byte-identical to T3.
- No renumber/reword: `git diff main...feat/provisioning-gate-74 -- scripts/verify-rigs.sh` shows a single appended V16 block (`== V16. Provisioning Existence Gate (#74) ==` at former `:2044`); V1–V15 untouched. Auditor re-run confirms `SUMMARY: 32 checks passed, 0 failed` (31 baseline + V16).
- No provisioning claims: `grep -n "install:" scripts/render-seat.py scripts/seed-rig.py scripts/live-health.py scripts/verify-rigs.sh` → no matches (exit 1). `git diff main...feat/provisioning-gate-74 -- fleet/` → 0 lines (no catalog/pin changes).
- No `Closes #74` posture: repo-wide grep finds `Closes #74` only inside `never Closes #74` disclaimers (spec `spec.md:20`, evidence `§7` footer, T3 report prose) — not claims. Both fix and evidence commits say `Refs #74`.
- No hand-edits under generated leaves: `git diff --name-only main...feat/provisioning-gate-74` = `docs/`, `docs/evidence/`, `docs/reports/`, `scripts/`, `tests/` only — zero entries under `specs/`, `rigs/`, `rosters/`, `registry/`. No regen required (no catalog-adjacent change). `git diff --name-only ac44602..HEAD` = `docs/evidence/wave-c-provisioning-gate.md` + `scripts/render-seat.py` only.

## 2. Re-run (auditor-executed, real output, inside worktree)

- `./scripts/verify-rigs.sh --check-only`: `SUMMARY: 32 checks passed, 0 failed`, exit 0, incl. `[PASS] Provisioning existence gate (#74) green`.
- `python3 -m pytest tests/test_render_seat.py tests/test_seed_rig.py tests/test_live_health.py tests/test_policy_verifier.py`: **81 passed** (10.31s), exit 0 — matches QA §7a exactly.
- `python3 -m pytest tests/test_build_canary.py`: **12 failed, 11 passed** — matches T2's recorded 12/11 baseline exactly (T3 report §3 cites T2's clean-main-worktree proof at merge-base `f2f97f6`; environment/dependency shape, unrelated to this change). Out of scope per stage instructions; verdict NOT failed for it. Re-run was quick (~29s) so taken for direct confirmation.

## 3. Red-proof evidence audit (QA commit `19fa735`, `docs/evidence/wave-c-provisioning-gate.md` §7)

- Direction (a), missing command → loud degradation: sabotage (`command: uvx` → `/nonexistent-qa74-rework1-sabotage` in `fleet/mcp-servers.yaml`) produced exit-0 degraded render, semgrep `"enabled": false`, stderr naming server + seat + raw catalog token; restored via `git checkout`, status empty. Non-vacuous (behavioral, observable degrade at the fixed warn site). Auditor's independent fixture render above corroborates the loud-degrade property post-fix.
- Direction (b), silenced warn → verify must RED: warn `print(...)` replaced with `pass` produced verify exit 1, `30 passed, 4 failed`, with exact signatures — V16 string-gate FAIL, both missing-direction behavioral FAILs (`uvx`, `r2mcp`), plus `TestProvisioningGate74.test_missing_mcp_binary_disables_loudly` failure; restore returns 32/0 + 81 passed, status clean. Non-vacuous (gate fails when the property is removed, at the exact fixed lines).
- Restore proofs logged after each sabotage (`git checkout -- <file>` → `git status --short` empty; verify + pytest back to green). QA changed no production/test files (evidence-only commit on top of fix).
- `git status --short` at audit time: **clean** (empty output, exit 0).

## 4. Findings

None. Fix confined to the `:606-613` warn block, still names server/seat/artifact, still loud, provably free of host-absolute secrets/tools paths in stderr. No stubs, no vacuous checks, no failing in-scope commands, no missing deliverables, no renumber, no install recipes/pins, no `Closes #74` posture, no generated-leaf hand-edits. T2's 12 pre-existing canary failures unchanged and out of scope.

Report path: `docs/reports/wave-c-provisioning-gate-rework1-verification.md` (new addendum; T3 report left untouched). Not committed per instructions.

VERDICT: PASS
