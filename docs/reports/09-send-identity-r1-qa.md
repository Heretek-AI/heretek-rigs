# 09-send-identity-r1 — QA acceptance report (wave 9 rework cycle 1, Refs #9)

Verifier: acceptance-verifier subagent, 2026-10-28.
Worktree: `.lane/trees/09-send-identity-r1`, branch `fix/09-send-identity-r1`,
tip `1915d5b` at QA start. No commits made; no pushes. All sabotage fully
reverted — `git status --short` shows only this report and the appended
`docs/evidence/09-send-identity/red-proofs.log` entries (QA-R2 series).

Spec: `openspec/specs/send-identity/spec.md` (REQ-S1...S4, still normative).
Implementation claims verified against (not trusted from)
`docs/reports/09-send-identity-rework-1.md`. Prior battery
`docs/reports/09-send-identity-qa.md` treated as UNVERIFIED context and
re-run independently below.

## Per-check GREEN results (baseline, unmodified tree @ 1915d5b)

| # | Check | Result |
|---|-------|--------|
| 1 | `./scripts/verify-rigs.sh --check-only` | GREEN — `SUMMARY: 36 checks passed, 0 failed`, `[PASS] V28 send-identity attestation (09-send-identity S1) green: binding rules + !cat render + 26 corpus tests pass + S0 evidence present`, exit 0. V1–V28 `== V... ==` headers present in order; V22/V23/V24 titles intact (`Bare Queue/Send Deny`, `Per-Seat MCP Bearer Grants (107-identity M1)`, `Rotation Runbook Step-3 --rig Mandate (107-identity R1)`). V1–V27 unrenamed (spot-checked header anchors). |
| 2 | `make test` | GREEN — `Ran 531 tests ... OK`, exit 0. 22 suites (`tests/test_*.py` count 22). Matches rework-1 claim (530 + 1 new cross-seat test). |
| 3 | `python3 -m unittest tests.test_send_identity -v` | GREEN — `Ran 26 tests ... OK`, exit 0; 26 `ok` lines, zero FAIL/ERROR/skip. NEW cross-seat test present by name and passing: `test_cross_seat_secret_cannot_authenticate_other_sender (tests.test_send_identity.AttestationVerifyTests...) ... ok` (denial line: `sender mismatch: attestation sender 'seat-b@test-rig' != 'seat-a@test-rig'`). All four REQ-S2 classes still present: `test_spoofed_claimed_source_is_ignored`, `test_replay_of_valid_attestation_is_rejected`, `test_cross_rig_presentation_fails_scope`, `test_fleet_declares_exact_bare_deny_triple` + `test_rendered_maps_deny_bare_send_allow_addressed_send`. |
| 4 | `python3 scripts/audit_loop.py --self-test` | GREEN — `SELF-TEST PASSED`, exit 0 (incl. 20 adversarial vectors PASS). |
| 5 | `python3 scripts/generate-rigs.py --check-idempotent` | GREEN — `idempotence check passed (two consecutive runs byte-identical)`, exit 0. Post-run registry re-stamp is sanctioned provenance-only (16 files, 24+/24- lines, every non-header diff line a `resolvedCommit`/`canonicalUrl` embed — verified via `git diff` filter showing zero other lines), reverted with `git checkout -- registry/`; status clean. |
| 6 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md` | GREEN — no output, exit 1 (zero unredacted bearer-shaped strings). |
| 7 | Docs fixes | GREEN — (a) `AGENTS.md:73` docs-map points at `openspec/changes/archive/2026-10-28-09-send-identity/` (F1 fixed). (b) `HANDOFF.md:18` states `36 checks passed, 0 failed`; the remaining `35` mentions (lines 53, 67) are historical narrative (M5/V19 history, FAIL-ONLY record), not live expectations (F8 fixed). (c) Rotation runbook: every `rig mcp token revoke` form is name-only (no `--seat`/`--rig`); every `rig mcp token add` mint carries `--seat` + `--rig` (F2 fixed). Failure-modes paragraph states exit-2 strict render vs disabled-entry degraded render (F3). |

## Red-proof summary (all GREEN->RED->GREEN, verbatim outputs in red-proofs.log QA-R2 series)

- QA-R2a (F5 fix, `expected_sender` check removed): RED `AssertionError: 'attested' != 'unverified'` (`FAILED (failures=1)`, exit 1) on the new cross-seat test → restored 26/26 OK.
- QA-R2b (F6 V28 skip-floor, injected `@unittest.skip`): corpus alone `OK (skipped=1)` exit 0; fixed V28 RED `[FAIL] V28... skipped 1 test(s) (skips must not count toward the corpus threshold)`, `SUMMARY: 35 checks passed, 1 failed`, exit 1. Old counting-skips form (`elif _v28_ran < 20`) with the same skip stays GREEN 36/0 — proving the pre-F6 hole was real and the fix closes it. Restored 36/0.
- QA-R2c (V28 gate, module removed): RED `SUMMARY: 35 checks passed, 4 failed`, exit 1 → restored 36/0.
- QA-R2d (secrets grep, injected 47-char token): RED grep exit 0 with line → exit 1 clean after revert.

**Vacuous checks: none.** The F5 fix, the F6 fix, the V28 gate, and the
secrets grep all turn RED under targeted sabotage and GREEN on clean
restore. (The pre-F6 counting form is the only green-under-sabotage
behavior observed, and it is the removed code — retained in the log as
the vacuity proof for F6, not a live check.)

## Findings

No blocking findings. F1...: none raised.

Notes (non-blocking, for coordinator awareness):
- N1: `docs/IMPLEMENTATION_PROMPT.md:29,37` still states the old live count
  (35). It is a wave-scoped prompt doc outside the rework-1 brief (which
  required only HANDOFF.md, now fixed); V19 does not scan it. Left
  untouched — coordinator to decide if a later wave owns it.
- N2: `make test` wall time ~104s (531 tests); run once for baseline only.
- N3: one post-restore `./scripts/verify-rigs.sh --check-only` rerun exceeded
  the 120s tool window under load (no output captured); immediate retry
  completed 36/0 exit 0 with the tree untouched. Environmental, not a defect.
