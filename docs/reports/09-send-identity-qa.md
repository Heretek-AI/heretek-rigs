# 09-send-identity — QA acceptance report (wave 9, Refs #9)

Verifier: acceptance-verifier subagent, 2026-10-28.
Worktree: `.lane/trees/09-send-identity`, branch `feat/09-send-identity`,
tip `e04a7f8` at QA start. No commits made; no pushes. All sabotage fully
reverted — `git status --short` shows only this report and the appended
`docs/evidence/09-send-identity/red-proofs.log` entries.

Spec: `openspec/changes/2026-10-28-09-send-identity/specs/send-identity/spec.md`
(REQ-S1…S4). Implementation claims verified against (not trusted from)
`docs/reports/09-send-identity-implementation.md`. Programmer red-proofs in
`docs/evidence/09-send-identity/red-proofs.log` treated as UNVERIFIED and
re-run independently (see QA-R1…QA-R7 there).

## Per-check GREEN results (baseline, unmodified tree)

| # | Check | Result |
|---|-------|--------|
| 1 | `./scripts/verify-rigs.sh --check-only` | GREEN — `SUMMARY: 36 checks passed, 0 failed`, `[PASS] V28 send-identity attestation (09-send-identity S1) green: binding rules + !cat render + 25 corpus tests pass + S0 evidence present`. All V1–V28 `== V… ==` headers present in order; V22/V23/V24 titles intact (`Bare Queue/Send Deny`, `Per-Seat MCP Bearer Grants (107-identity M1)`, `Rotation Runbook Step-3 --rig Mandate (107-identity R1)`). No V1–V27 renumber/reword (spot-checked headers + `grep -n "V22\.\|V23\.\|V24\."` line anchors). |
| 2 | `make test` | GREEN — `Ran 530 tests … OK`, exit 0. 22 suites (`tests/test_*.py` count 22). Matches implementation-report claim (505 pre-existing + 25 wave). |
| 3 | `python3 -m unittest tests.test_send_identity -v` | GREEN — `Ran 25 tests … OK`, exit 0; 25 `ok` lines, zero FAIL/ERROR. All four REQ-S2 classes present: `test_spoofed_claimed_source_is_ignored`, `test_replay_of_valid_attestation_is_rejected`, `test_cross_rig_presentation_fails_scope`, `test_fleet_declares_exact_bare_deny_triple` + `test_rendered_maps_deny_bare_send_allow_addressed_send`. |
| 4 | `python3 scripts/audit_loop.py --self-test` | GREEN — `SELF-TEST PASSED`, exit 0 (incl. 20 adversarial vectors PASS). |
| 5 | `python3 scripts/generate-rigs.py --check-idempotent` | GREEN — `idempotence check passed (two consecutive runs byte-identical)`, exit 0. Post-run registry re-stamp is sanctioned provenance-only (32 `resolvedCommit` lines + `canonicalUrl` HEAD embeds, zero other diff lines — verified via `git diff` filter), reverted with `git checkout -- registry/`. |
| 6 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md` | GREEN — no output, exit 1 (zero unredacted bearer-shaped strings). |
| 7 | Evidence files | GREEN — both exist. Spoof file contains the accepted-forgery line (`accepted forged sender: red-ai-red-teamer@defensive-sec-and-red-team`, 2 matches). Rotation file: `--seat` ×7, `--rig` ×8, rig-less mint forms 0 (S3 pipeline `grep -n 'mcp token add\|sender.*add' … | grep -v -- '--rig' | wc -l` → 0; the two `--rig`-less `revoke` lines are daemon-output verbatim hints, not operator mint commands). S3 rotation verdict lines present verbatim (`old attestation under key 2: unverified None`, `new attestation under key 2: attested blue-probe@test-rig`). |

Drift-guard `docs/reports/09-send-identity-verification.md` read from disk ends
`VERDICT: PASS` (noted, not re-executed — coordinator triad input).

## Red-proof summary (all GREEN→RED→GREEN, verbatim outputs in red-proofs.log)

- QA-R1 (V28 gate, module removed): RED `SUMMARY: 35 checks passed, 4 failed`, exit 1 → restored 36/0.
- QA-R2 (`make test`, corpus assertion inverted): RED `FAILED (failures=1)`, make Error 1, exit 2 → restored `Ran 530 … OK`.
- QA-R3a (spoofed `--source`): RED `AssertionError: 'red-actor@other-rig' != 'blue-probe@test-rig'` → 25/25 OK.
- QA-R3b (replay): RED `AssertionError: 'attested' != 'rejected'` → 25/25 OK.
- QA-R3c (cross-rig): RED `AssertionError: 'attested' != 'unverified'` → 25/25 OK.
- QA-R3d (bare-send): RED `AssertionError: Lists differ: ['a11y-specialist'] != []` → 25/25 OK.
- QA-R4 (self-test): RED `AssertionError: Parser failed to catch false NO_FINDINGS…`, exit 1 → `SELF-TEST PASSED`.
- QA-R5 (idempotence, nondeterministic tail): RED `error: non-idempotent generation`, exit 2 → byte-identical PASS. (Dirty guard fired first by design; used documented `HERETEK_RIGS_ALLOW_DIRTY=1` dev path.)
- QA-R6 (secrets grep, injected 47-char token): RED grep exit 0 with line → exit 1 clean after revert.
- QA-R7 (S0 evidence removed): RED `[FAIL] V28… S0 evidence file unreadable`, exit 1 → 36/0.

**Vacuous checks: none.** Every acceptance check and every REQ-S2 forgery class
turns RED under targeted sabotage and GREEN on clean restore.

## Findings

No blocking findings. F1…: none raised.

Notes (non-blocking, for coordinator awareness):
- N1: `HANDOFF.md` / `docs/IMPLEMENTATION_PROMPT.md` still state the old live
  count (35) per the implementation report — V19 does not scan them; left
  untouched as coordinator-owned state. Not a wave-9 defect.
- N2: `make test` wall time ~104s per run (530 tests); QA ran it 3× (baseline,
  R2-RED, R2-restore) — all as recorded.
- N3: V28's non-idempotence message prints `(diff keys: [])` when only file
  *contents* differ (key sets identical) — cosmetic; exit code is correct.
  Suggest richer diff output in a later wave, not this one.
