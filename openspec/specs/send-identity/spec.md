# send-identity Specification

## Purpose
TBD - created by archiving change 2026-10-28-09-send-identity. Update Purpose after archive.

## Requirements

### Requirement: REQ-S1 — grant-bound sender attestation with seed issuance

The system MUST issue a per-seat sender binding at seed time reusing the `issue_seat_grant` issuance discipline
(scope `--seat` + `--rig`, 0600 store, fail-closed parse, revoke-on-fail) and MUST render it as a `!cat` reference,
never an inline secret. The relay MUST verify attestation server-side and MUST ignore client-supplied sender claims.

#### Scenario: attested send accepted with proven sender

- GIVEN a seat with a matching sender binding (seat+rig scope, 0600 store)
- WHEN a send arrives bearing a valid, fresh attestation
- THEN the receiver records the attested sender identity and the message is NOT held UNVERIFIED.

#### Scenario: unattested send held UNVERIFIED (no availability regression)

- GIVEN a send with no attestation (legacy path)
- WHEN it arrives at a seat
- THEN the seat holds it as UNVERIFIED exactly as today (`docs/USER_GUIDE.md:224-225`).

### Requirement: REQ-S2 — forgery refusals

The system MUST refuse the four forgery classes. Each MUST be red-proven: a sabotage run that re-introduces the
forgery MUST turn the corresponding check red, and the clean tree MUST be green.

#### Scenario: spoofed --source ignored

- GIVEN an attested sender `blue-probe@test-rig`
- WHEN a send claims `--source red-actor@other-rig` (or a forged fleet-id)
- THEN the claim is ignored; the recorded sender is the attested one (or UNVERIFIED if no valid attestation).

#### Scenario: replay rejected

- GIVEN a previously accepted attested send
- WHEN its attestation is presented a second time
- THEN the replay is rejected with a redacted log line (no secret material in the log).

#### Scenario: cross-rig impersonation impossible

- GIVEN a binding for seat A scoped to rig X
- WHEN it is presented as seat B (any rig) or as seat A on rig Y
- THEN verification fails (scope rule: seat+rigs==[rig], cf. `_grant_scope_matches`).

#### Scenario: bare-send bypass still denied

- GIVEN the V22 in-seat triple (`rig queue list`, `rig queue create`, `rig send`)
- WHEN any seat map is rendered or verified
- THEN bare `rig send` remains denied in-seat and addressed `rig send <session>` remains allowed (V22 intact).

### Requirement: REQ-S3 — V28 gate and test corpus

The change MUST append a V28 verify block (new block, never renumber or reword V1–V27) and MUST ship
`tests/test_send_identity.py` with the four forgery classes covered. V28 MUST be FAIL-ONLY pre-fix
(spoof succeeds on the unpatched tree) and PASS post-fix.

#### Scenario: FAIL-ONLY pre-fix proof recorded

- GIVEN the unpatched tree plus the S0 scratch spike
- WHEN the spike runs
- THEN forged sender is accepted and the transcript is preserved verbatim in `docs/evidence/09-send-identity-spoof.md`.

#### Scenario: post-fix gates green

- WHEN `./scripts/verify-rigs.sh --check-only` runs on the patched tree
- THEN the summary is 36 passed, 0 failed with V28 PASS and V1–V27 intact,
- AND `python3 -m unittest tests.test_send_identity -v` exits 0,
- AND `make test` exits 0 with zero failures.

### Requirement: REQ-S4 — rotation runbook and secrets discipline

The change MUST ship a sender-binding rotation runbook (revoke + re-add with `--seat` + `--rig`, V24-style mandate)
executed live in scratch, and MUST keep all secrets discipline: 0600 stores, `!cat` renders, `_redact_for_log`
on every new log path, dummy keys in tests/scratch, zero unredacted bearer-shaped strings in evidence.

#### Scenario: rotation executed

- WHEN the runbook `docs/evidence/09-send-identity-rotation.md` steps run in an isolated scratch env
- THEN revoke + re-add succeeds with `--seat` and `--rig` on every mint command and zero rig-less forms,
- AND no real credential appears in any command, file, report, or log.
