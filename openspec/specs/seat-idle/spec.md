# seat-idle Specification

## Purpose
TBD - created by archiving change 2026-10-28-81-seat-idle. Update Purpose after archive.

## Requirements

### Requirement: REQ-I1 — charter claim plus first action is one turn

The seat charter MUST state: claiming a qitem and the first work action are one turn — a seat MUST NOT end its turn immediately after the claim while holding an open obligation. The rule MUST live in the seat skill charter, authored via generator inputs (`fleet/skill-patches/` + regen, never hand-edited leaves).

#### Scenario: claim without action violates the charter

- GIVEN a seat that claimed a qitem and holds 1 open obligation with no work action recorded
- WHEN the turn boundary is evaluated
- THEN the charter directs the seat to continue with the first action (no park-at-prompt after claim).

#### Scenario: charter rule is generated, not hand-edited

- GIVEN the charter change
- WHEN `generate-rigs.py` runs
- THEN every rendered leaf carrying the rule matches the generator input exactly (zero hand-edited leaves).

### Requirement: REQ-I2 — claim-then-park counts as stalled with latency attribution

The reconciler MUST classify a claim-then-park pattern (claim recorded, no work action, parked-at-prompt while holding an open obligation) as an idle-park stalled diff (not silent), routing for human review with park-to-wake vs work latency attribution attached. Attribution MUST be propose-only (report only, never writes tracker or queue state). Legitimate idle (no open obligation) and live-gate waiting MUST stay quiet. This MUST be red-proven: removing the classification returns the fixture to silent.

#### Scenario: claim-then-park pattern flagged

- GIVEN the #81-pattern fixture (claim in seconds, "Handoff received" prose, then parked-at-prompt watchdog line while holding 1 open obligation, no work action)
- WHEN the reconciler runs
- THEN it emits the idle-park stalled diff naming the parked obligation and attaches park-to-wake vs work attribution.

#### Scenario: legitimate idle stays quiet

- GIVEN parked-at-prompt prose with NO open obligation
- WHEN the reconciler runs
- THEN no idle-park diff is emitted for that row.

#### Scenario: latency attribution is report-only

- GIVEN a flagged idle-park row with claim/work/wake timestamps
- WHEN attribution runs
- THEN it reports park-to-wake share vs work share (inputs for #15/#17) and writes no tracker or queue state.

### Requirement: REQ-I3 — daemon handoffs carry a distinct source, never operator

Daemon-originated recovery handoffs MUST carry a distinct source label (e.g. `daemon:stuck-sweep`) and MUST NOT present as `From: operator`. A daemon handoff presenting as `operator` MUST be refused or relabeled to the daemon source with a redacted log line, preserving the wave-9 operator trust model (operator relays arrive via `send-authenticated.sh` with a human-ref). This MUST be red-proven: allowing the operator label restores the #81 collision in fixture.

#### Scenario: operator-labeled daemon handoff refused or relabeled

- GIVEN a stuck-sweep recovery handoff of daemon origin labeled `From: operator`
- WHEN source validation runs
- THEN the operator label is refused or relabeled to the distinct daemon source; the handoff is never recorded as an operator relay and the refusal is logged redacted.

#### Scenario: genuine operator relay untouched

- GIVEN an operator relay arriving via `send-authenticated.sh` with a human-ref
- WHEN source validation runs
- THEN wave-9 attestation handling is unchanged (attested/unverified/rejected preserved).

### Requirement: REQ-I4 — V30 gate and test corpus

The change MUST append a V30 verify block (new block, never renumber/reword V1–V29) and MUST ship corpus covering REQ-I2/I3 fixtures. V30 MUST be FAIL-ONLY pre-fix (fixtures silent or mislabeled on the unpatched tree) and PASS post-fix.

#### Scenario: FAIL-ONLY pre-fix proof recorded

- GIVEN the unpatched tree plus the S0 fixtures
- WHEN they run
- THEN the claim-then-park parent is NOT flagged idle-park and the operator-labeled daemon handoff passes unlabeled; both transcripts preserved in `docs/evidence/81-seat-idle-prefix.md`.

#### Scenario: post-fix gates green

- WHEN `./scripts/verify-rigs.sh --check-only` runs on the patched tree
- THEN the summary is 38 passed, 0 failed with V30 PASS and V1–V29 intact,
- AND `make test` exits 0 with zero failures.
