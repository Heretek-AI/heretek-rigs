# auth-envelope Specification

## Purpose
TBD - created by archiving change 2026-10-29-15-auth-envelope. Update Purpose after archive.

## Requirements

### Requirement: REQ-E1 — standing envelopes bind premise to landing

A pre-authorization envelope MUST bind the exact TPM-verified diff hash plus scope paths plus a mandatory expiry window plus a single-use nonce (replay refused, redacted log). The envelope is an authorization artifact only: it MUST never self-execute and MUST never auto-commit — landing still requires its actor. Envelopes MUST be red-proven: permitting drift/scope-breach/expiry/replay restores the #15 incident in fixture.

#### Scenario: clean envelope validates

- GIVEN an envelope whose diff hash matches the landing diff, whose scope paths cover the landing file-set, unexpired, unused nonce
- WHEN landing validation runs
- THEN the landing is authorized (no auto-execution; the actor still performs it).

#### Scenario: drifted premise refused

- GIVEN the landing diff differs by even one line from the envelope's bound diff hash (the 11-file vs one-liner pattern)
- WHEN landing validation runs
- THEN the landing is refused fail-closed with a redacted log line; the row keeps its state.

#### Scenario: scope breach refused

- GIVEN a landing file-set reaching outside the envelope's scope paths
- WHEN landing validation runs
- THEN the landing is refused fail-closed with a redacted log line.

#### Scenario: expired or replayed envelope refused

- GIVEN an envelope past its expiry window, or a nonce already consumed
- WHEN landing validation runs
- THEN the landing is refused fail-closed with a redacted log line; the nonce store is never rewound.

### Requirement: REQ-E2 — premise drift counts as stalled with premise-age attribution

The reconciler MUST classify a row whose landing diff drifted from its authorized premise (or which carries an open authorization with no matching envelope) as a stalled diff (not silent), routing for human review with premise-age attribution attached. Attribution MUST be propose-only (report only, inputs for #17, never writes tracker or queue state). Clean premises (landing matches premise) MUST stay quiet. This MUST be red-proven: removing the classification returns the fixture to silent.

#### Scenario: drifted premise flagged

- GIVEN the #15-pattern fixture (authorized one-liner premise; live 11-file diff; premise aged past the round-trip)
- WHEN the reconciler runs
- THEN it emits the stalled premise-drift diff naming the drifted paths and the premise age.

#### Scenario: clean premise stays quiet

- GIVEN a landing diff identical to its authorized premise within the envelope window
- WHEN the reconciler runs
- THEN no premise-drift diff is emitted for that row.

#### Scenario: premise-age attribution is report-only

- GIVEN a drifted row with premise/verify/landing timestamps
- WHEN attribution runs
- THEN it reports premise age at landing (inputs for #17) and writes no tracker or queue state.

### Requirement: REQ-E3 — no self-execution, no auto-commit

No envelope, classifier, or guard in this change may commit, land, or advance a row: the never-`done` and never-auto-commit rules stand. A refused landing MUST leave the flagged row untouched and MUST be closable only by a human after the row state changes (owner re-verifies: fresh premise, narrowed scope, or explicit hold). This MUST be red-proven: allowing dismissal without row state change restores silent burial in fixture.

#### Scenario: refused landing leaves state untouched

- GIVEN a refused landing (drift/scope/expiry/replay)
- WHEN the refusal is recorded
- THEN the row state is byte-identical and the refusal is logged redacted; nothing is committed.

#### Scenario: recovery requires row state change

- GIVEN a refused landing whose row state is byte-identical to flag time
- WHEN something attempts to close the recovery item
- THEN the close is refused; it succeeds only after the row state changed.

### Requirement: REQ-E4 — V31 gate and test corpus

The change MUST append a V31 verify block (new block, never renumber/reword V1–V30) and MUST ship corpus covering REQ-E1/E2 fixtures. V31 MUST be FAIL-ONLY pre-fix (fixtures drift-silent and envelope-absent on the unpatched tree) and PASS post-fix.

#### Scenario: FAIL-ONLY pre-fix proof recorded

- GIVEN the unpatched tree plus the S0 fixtures
- WHEN they run
- THEN the drifted premise is NOT flagged stalled and no envelope validates; both transcripts preserved in `docs/evidence/15-auth-envelope-prefix.md`.

#### Scenario: post-fix gates green

- WHEN `./scripts/verify-rigs.sh --check-only` runs on the patched tree
- THEN the summary is 39 passed, 0 failed with V31 PASS and V1–V30 intact,
- AND `make test` exits 0 with zero failures.
