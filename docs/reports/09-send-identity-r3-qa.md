# 09-send-identity-r3 QA report (wave 09-send-identity-r3, PR #128 threads)

Date: 2026-10-28. Worktree: `.lane/trees/09-send-identity-r3`
(branch `fix/09-send-identity-r3`, tip `849f197`, cycle base `8ac5ca6`).
Verifier: acceptance verifier, read-from-disk, no commits, no pushes.
All sabotage temporary and reverted; `git status --short` proven clean
after each revert.

Scope: rework cycle 3 claims in
`docs/reports/09-send-identity-rework-3.md` (G1 rotation failure-modes
doc, G2 reuse-branch mode guard, G3 seed/render gate alignment, G4 stale
sender-binding thread, G5 CodeQL group-readable fixture). Spec:
`openspec/specs/send-identity/spec.md` (REQ-S1...S4).

## Spec-compliance review (stricter guard + narrowed gate vs REQ-S1...S4)

- G2 reuse guard (`scripts/send_identity.py:167-186`): valid-file reuse
  (0600 regular file) still returns 0 with the reuse ok-line -- the
  attested/unattested flows and valid reuse per REQ-S1/S2 are unchanged
  (proven: `test_issue_reuses_matching_grant_and_file` green, and under
  sabotage-(a) valid reuse still passed while only the refusal test
  failed). The guard only narrows the previously-unsafe path. No spec
  violation.
- G3 narrowed seed gate (`seat_needs_sender_binding` = `seat_needs_grant`
  with `opt_in=False`): bound seats issue exactly as before; unbound seats
  (with or without opt-in) now get no binding -- matching the renderer,
  which emits no `send-identity.json` entry for them. No bound-seat
  behavior change; no REQ-S1 violation (unattested seats stay UNVERIFIED
  per spec, exactly as today).

## Per-check results (current tip, real outputs)

1. `./scripts/verify-rigs.sh --check-only` -- PASS.
   `SUMMARY: 36 checks passed, 0 failed`, V28
   `[PASS] V28 send-identity attestation (09-send-identity S1) green:
   binding rules + !cat render + 28 corpus tests pass + S0 evidence present`,
   exit 0. V1-V27 headers unrenamed (V19...V27 blocks intact,
   V23/V24/V25/V26/V27 FAIL-ONLY markers frozen).
2. `make test` -- PASS. `Ran 536 tests ... OK`, exit 0 (123s).
3. `python3 -m unittest tests.test_send_identity -v` -- PASS.
   `Ran 28 tests ... OK`, exit 0 (incl. new
   `test_reuse_of_non_0600_binding_file_refuses`). Gate-alignment tests
   `python3 -m unittest tests.test_identity_m1.SeatNeedsSenderBindingTests -v`
   -- PASS, 3/3 OK, exit 0.
4. `python3 scripts/audit_loop.py --self-test` -- PASS.
   `SELF-TEST PASSED`, exit 0.
5. `python3 scripts/generate-rigs.py --check-idempotent` -- PASS.
   `idempotence check passed (two consecutive runs byte-identical)`,
   exit 0. Side effect: 16 `registry/` files gained provenance-only diffs
   (`resolvedCommit`/`canonicalUrl` cb3ba9a->849f197); verified
   provenance-only via diff sweep, then `git checkout -- registry/`;
   `git status --short` clean.
6. `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md`
   -- PASS. No output, exit 1 (clean, no bearer-shaped runs).
7. Docs/behavior spot-checks -- all HOLD:
   (a) rotation.md:68-81 states missing->disabled-entry (degraded, rc=0)
   vs unreadable->die (both modes); matches `secret_ok` at
   `scripts/render-seat.py:780-816` (symlink/wrong-mode/wrong-owner/
   unsafe-open `die`, only absence returns False).
   (b) fixture masks in `tests/test_send_identity.py`: `os.chmod` only at
   :221/:255, both `0o400` (`& 0o077 == 0`, no group/other bits); other
   masks are `0o700` dirs and `0o600` files; :188 asserts `0o600`. No
   group/other-bit file mask.
   (c) G4-stale claim: `expected_sender` required kwarg
   (`scripts/send_identity.py:311`), sender-mismatch denial (:359-362),
   cross-seat test `test_cross_seat_secret_cannot_authenticate_other_sender`
   (`tests/test_send_identity.py:349-364`) present and green (28/28). All
   10 in-repo `verify_attestation` call sites are in the test corpus and
   pass `expected_sender`; no production caller yet (relay is future work).
   `verify_attestation` untouched by this cycle, as claimed.

## Red-proof table (appended as QA-R4a/b/c to `docs/evidence/09-send-identity/red-proofs.log`; priors untouched)

- QA-R4a: reuse-branch 0600 guard removed (`scripts/send_identity.py`).
  RED verbatim: `AssertionError: 0 == 0`, 1 test FAILED exit 1; full corpus
  `Ran 28 ... FAILED (failures=1)` -- ONLY the reuse-refusal test fails,
  valid reuse still passes. GREEN on `git checkout --` restore:
  `Ran 28 tests ... OK` exit 0, status clean.
- QA-R4b: `seat_needs_sender_binding` body replaced with `return True`
  (`scripts/seed-rig.py`). RED verbatim:
  `AssertionError: True is not false`,
  `Ran 3 tests ... FAILED (failures=2)` exit 1
  (`test_unbound_role_needs_no_sender_binding`,
  `test_opted_in_unbound_role_gets_grant_but_no_sender_binding`). GREEN on
  restore: 3/3 OK exit 0, status clean.
- QA-R4c: `SENDER_BINDING_GRANT_SUFFIX` `/send-identity` -> `/sender-binding`
  (`scripts/send_identity.py`). `./scripts/verify-rigs.sh --check-only`
  RED verbatim:
  `[FAIL] V28/09-send-identity: binding grant name must scope the sender
  with /send-identity (got 'blue-probe@test-rig/sender-binding')`
  plus `[FAIL] V28/09-send-identity: tests.test_send_identity failed:`;
  `SUMMARY: 35 checks passed, 2 failed` exit 1. GREEN on restore:
  `SUMMARY: 36 checks passed, 0 failed`, V28 PASS, exit 0, status clean.

No vacuous acceptance check found.

## Findings

No blocking findings (no F-items). All rework-3 claims verified:

- G1 FIXED (docs-only): doc failure-mode section consistent with
  `secret_ok` ground truth. No sabotage cycle applicable (doc-only).
- G2 FIXED + red-proofed (QA-R4a).
- G3 FIXED + red-proofed (QA-R4b).
- G4 SKIPPED-STALE upheld: evidence on disk as claimed; thread predates
  the rework-1 landing; `verify_attestation` untouched.
- G5 FIXED (fixture mask): 0400 carries no group/other bits; refusal keys
  on exact `!= 0o600` so 0400 provably refuses; suite green. No local
  CodeQL re-scan possible (substitute validation stated plainly, as in
  the rework-3 report).

## Final tree state

`git status --short` shows only:

- `M docs/evidence/09-send-identity/red-proofs.log` (appended QA-R4a/b/c)
- `?? docs/reports/09-send-identity-r3-qa.md` (this report)

Nothing failed, nothing skipped.
