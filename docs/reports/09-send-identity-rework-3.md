# 09-send-identity rework-3 report (PR #128 review threads, Refs #9)

Date: 2026-10-28. Worktree: `.lane/trees/09-send-identity-r3`
(branch `fix/09-send-identity-r3`, base `main @ 8ac5ca6`).
Final allowed cycle (3 of 3) — complete but minimal.

## Verdict table

| Finding | Verdict | Evidence |
|---|---|---|
| G1 rotation doc: missing vs unreadable | FIXED (docs-only) | Scratch matrix (dummy keys, `/tmp/opencode/g1-scratch`): missing+degraded rc=0 disabled entry; missing+strict rc=2; 0640+degraded rc=2 (`...key is mode 640; run: chmod 600 ...`); 0640+strict rc=2. Ground truth `secret_ok` at `scripts/render-seat.py:780-816` (symlink/wrong-mode/wrong-owner/unsafe-open `die` in both modes; only absence returns False). Doc `docs/evidence/09-send-identity-rotation.md:68-81` rewritten to distinguish. |
| G2 reuse branch: 0600 regular-file check | FIXED + red-proofed | `scripts/send_identity.py:167-186` (`os.lstat` + `S_ISREG` + exact `0o600`, `_fail` closed, grant left intact); new `test_reuse_of_non_0600_binding_file_refuses` (`tests/test_send_identity.py`). Sabotage (guard removed) → RED `AssertionError: 0 == 0`; restore → GREEN 9/9. Logged RP-R3-G2. |
| G3 seed gate vs render gate | FIXED + red-proofed | Divergence demonstrated: seed `scripts/seed-rig.py:533-537` gated on `seat_needs_grant(..., opt_in=env)` while render `_bound09` (`scripts/render-seat.py:1010-1015`) has no opt-in — opt-in unbound seats got unusable bindings. Fix: `seat_needs_sender_binding` (`scripts/seed-rig.py:186-198` = `seat_needs_grant(..., opt_in=False)`) + gated call (`:566-588`, skip prints ok-line). New `SeatNeedsSenderBindingTests` (3 tests, `tests/test_identity_m1.py`). Sabotage (`return True`) → RED `True is not false` (2 failures); restore → 3/3 OK. Logged RP-R3-G3. |
| G4 verify_attestation expected_sender | SKIPPED — STALE | On disk: `expected_sender` required kwarg (`scripts/send_identity.py:294`), sender-mismatch denial (`:342-346`), all 10 in-repo call sites pass `expected_sender` (grep 10/10), `test_cross_seat_secret_cannot_authenticate_other_sender` (`tests/test_send_identity.py:329-344`) green. Landed in rework-1 for identical F5; thread reviewed head `12ee2ba` predates it. `verify_attestation` untouched. |
| G5 CodeQL alert 99 (0o640 group bit) | FIXED (fixture mask) | `tests/test_send_identity.py:237`: `0o640` → `0o400`. Refusal keys on exact `!= 0o600` (`scripts/send_identity.py:178` reuse, `:201` pre-mint) so 0400 provably refuses; 0400 has no group/other bits (`& 0o077 == 0`). Suite proves it: pre-mint + new reuse tests (both 0400) GREEN. CodeQL cannot run locally — substitute: full corpus green + mask sweep (no group/other-bit file masks in `tests/test_send_identity.py`). 0o644 fixtures in `tests/test_identity_m1.py:271-282` are wave-107 seat-grant tests, pre-existing, not alert 99 — untouched. Logged RP-R3-G5. |
| G6 `coderabbit review --agent` | SKIPPED — out of scope | Review-tool promotion; coordinator owns review actions. |

## Files changed

- `scripts/send_identity.py` (+17): G2 reuse-branch 0600-regular-file guard.
- `scripts/seed-rig.py` (+48/-): `seat_needs_sender_binding` helper + gated
  `issue_sender_binding` call with skip ok-line.
- `tests/test_send_identity.py` (+24/-): G2 refusal test (0400) + G5 mask 0640→0400.
- `tests/test_identity_m1.py` (+25): `SeatNeedsSenderBindingTests` (3 tests).
- `docs/evidence/09-send-identity-rotation.md`: G1 missing-vs-unreadable rewrite.
- `docs/evidence/09-send-identity/red-proofs.log` (+59): RP-R3-G2/G3/G5 entries.

No V-gate text changes. No edits under `specs/`, `rigs/`, `rosters/`,
`registry/`, `openspec/` (no regen needed — no catalog/generator change).

## Acceptance (all green)

- `./scripts/verify-rigs.sh --check-only`: `SUMMARY: 36 checks passed, 0 failed`, V28 PASS (`... 28 corpus tests pass ...`), exit 0.
- `make test`: `Ran 536 tests ... OK`, exit 0.
- `python3 -m unittest tests.test_send_identity -v`: `Ran 28 tests ... OK`, exit 0.
- `python3 scripts/audit_loop.py --self-test`: `SELF-TEST PASSED`, exit 0.
- `python3 scripts/generate-rigs.py --check-idempotent`: dirty-guard exit 2
  pre-commit (by design); post-commit rerun byte-identical PASS, exit 0.
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md`: no output, exit 1 (clean).

## Commits

- (this cycle) `fix(09-send-identity): address PR #128 review threads G1/G2/G3/G5 (Refs #9)` on `fix/09-send-identity-r3`.

## Self-audit notes

- G4 untouched deliberately (stale thread; evidence above).
- G5: no local CodeQL re-scan possible; substitute validation stated plainly.
- G1 doc-only: no sabotage cycle applicable; scratch matrix is the proof.
- Secrets: dummy keys only in scratch/tests; no real credentials touched.
- No pushes (coordinator owns PR actions); no `--force`.
