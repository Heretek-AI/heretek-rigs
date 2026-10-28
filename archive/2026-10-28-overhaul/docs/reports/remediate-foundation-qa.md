# QA report: remediate-foundation (Wave 1, audit #66 M0-M3)

- Stage/wave: remediate-foundation
- Worktree: /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-foundation
- QA date (UTC): 2026-10-24
- Implementation report reviewed: docs/reports/remediate-foundation-implementation.md
- Spec: docs/REMEDIATION_IMPLEMENTATION_PROMPT.md (M0-M3, F1-F6, Gotchas 1-8)
- Head: 3d9851a (implementation commits intact; no QA edits to tracked files)

## Verdict: PASS (all acceptance checks green; every check red-proofed; no vacuous checks)

| # | Check | Command (run literally in worktree) | Result |
|---|---|---|---|
| 1 | verify-rigs | `./scripts/verify-rigs.sh --check-only` | PASS — `SUMMARY: 28 checks passed, 0 failed.` (exit 0; N=28 = 27 baseline + V12) |
| 2 | make test | `make test` | PASS — `Ran 208 tests`, `OK`; 10/10 suites present (render_seat, sweep_typed_blocks, regen_gate, queue_id_discipline, queue_json_discipline, reconcile, generate_trackers, build_canary, check_envelope, live_health) |
| 3a | M2 missing-pps dies | `HERETEK_TOOLS=/nonexistent HERETEK_SECRETS=$(mktemp -d) python3 scripts/render-seat.py --role exec-director --rig executive-and-architecture --pod exec --allow-missing-secrets --out $(mktemp -d)` | PASS — `error: /nonexistent/... is mandatory`, exit 2 (`--allow-missing-secrets` is no escape) |
| 3b | M2 real-tools render | real-HERETEK_TOOLS render, same args | PASS — exit 0, `rendered exec-exec-director@executive-and-architecture` |
| 4 | M1 evidence in NOTES | `docs/NOTES.md` M1 section | PASS — allowed shows `MARKER-SHELLPATH-HIT: date +%s` + exit_code 0; denied shows `Denied by policy` + isError true with no marker (enforcer-first); not-hot-reloaded rollout note present |
| 5 | V12 names missing binary, clean tree green | verify-rigs output `grep "command not found"` | PASS — 19 per-seat [NOTE] lines incl. `server 'radare2' command not found: .../tools/bin/r2mcp`; SUMMARY still 28/0 |

## F1-F6 / Gotchas spot-checks (scope-relevant at M0-M3)

- F1 (shellPath hook): reproduced per M1 NOTES evidence; no contrary finding.
- F2 (bwrap): M1 corpus recorded; `scripts/seat-sandbox.sh` correctly ABSENT (M4 scope, not this stage).
- F3 (terminal-deny mirror): render tuple and verify-rigs :588 tuple in sync — proven operationally by red-proof 1.
- F4 (audit_loop): untouched at this stage (M7 scope); no claim made.
- F5 (verify structure): V12 appended after V11, V1-V11 unrenamed/unreworded (cosmetic note: V6 ok() text still reads `7/7 unit tests` while the suite runs 9 — left untouched per the never-reword rule; cosmetic only).
- F6 (Makefile orphans): all 3 named orphans wired (line 38); `test_manifest_closure.py` / `test_policy_verifier.py` remain unwired — explicitly out of brief scope, recorded not hidden.
- Gotcha 3 (mirror sync): see F3. Gotcha 4 (no safe_dump on fleet.yaml): generate-rigs.py only READS fleet/fleet.yaml (line 529); write_yaml/safe_dump used solely for generated leaves — holds. Gotcha 6 (quietStartup): no reliance on startup notices; M2 asserts at render time.

## Red-proofs (all sabotages reverted; tree clean)

Full log: `docs/evidence/remediate-foundation/red-proofs.log`. Each: break -> run -> RED -> `git checkout -- <file>` -> diff-identical -> green.

1. **Render deny removal** (`"*--textconv*",` deleted) -> RED (`[FAIL] ... must emit terminal "*--textconv*"`, `[FAIL] tests/test_render_seat.py ... KeyError`, `27 passed, 2 failed`, exit 1) -> revert -> 28/0. Not vacuous.
2. **M2 version pin `41.0.0`->`99.9.9`** -> real-tools render RED (`version 41.0.0, need 41.0.0`, exit 2) -> revert -> exit 0. (Missing-path arm: check 3a, exit 2.) Not vacuous.
3. **Unwire `test_live_health` from Makefile** -> `Ran 187 tests` (was 208), suite count 9 != 10. NOTE: unittest still exits 0/OK, so the criterion must be the suite COUNT — a bare "ends OK" assertion would be vacuous for this defect class. Revert -> 10 suites, 208 OK.
4. **V12 naming**: (a) 19 naming [NOTEs] incl. radare2 with clean-tree 28/0, CONFIRMED; (b) suppressing [NOTE] print stays green — informational BY DESIGN per the documented M3 severity decision (host tooling -> M9); (c) neutering the M2-guard die string RED on two fronts (unit test `test_missing_pps_is_hard_error_despite_allow_missing_secrets` + V12 source assert, `26 passed, 2 failed`, exit 1) -> revert -> 28/0.

## Vacuous checks: none.

## Worktree state

`git status --short` shows only `?? docs/evidence/remediate-foundation/` (this QA's log) plus this report file. No tracked files modified; implementation commits untouched — evidence ready for coordinator commit.
