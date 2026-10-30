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

### Requirement: REQ-E5 — envelope-presence gating is opt-in on a consulted registry

The reconciler MUST classify a row with a clean landing (landing diff hash
identical to its authorized premise, landing file-set inside scope) as a
stalled envelope-absence diff routing for human review with premise-age
attribution attached, if and only if an envelope lookup was provided AND
that lookup holds no envelope matching the row's premise. When no lookup
was provided (absent) or the provided lookup is empty, the row MUST stay
quiet — the default preserves REQ-E2 clean-quiet. When the lookup holds a
matching envelope (row qitem present, bound premise hash identical), the
row MUST stay quiet. A lookup entry bound to a different premise hash MUST
NOT count as a matching envelope. Attribution MUST be propose-only (report
only, inputs for #17, never writes tracker or queue state). This MUST be
red-proven: removing the presence check (or emptying the lookup) returns
the fixture to silent. Nothing in this requirement self-executes, lands,
or advances a row: REQ-E3 never-`done`/never-auto-commit stands, and a
refused gating MUST leave the flagged row untouched, closable only by a
human after the row state changes.

#### Scenario: clean landing without a matching envelope stalls where a registry is consulted

- GIVEN the #15-pattern fixture with a clean landing (premise hash identical, paths in scope) AND a populated envelope lookup holding no envelope for the row's qitem
- WHEN the reconciler runs with that lookup
- THEN it emits the stalled envelope-absence diff naming the missing envelope and the premise age.

#### Scenario: quiet when no registry is consulted

- GIVEN the same clean-landing fixture
- WHEN the reconciler runs with no envelope lookup (absent) or an empty lookup
- THEN no envelope-absence diff is emitted for that row (REQ-E2 clean-quiet preserved).

#### Scenario: quiet when a matching envelope exists

- GIVEN the same clean-landing fixture AND an envelope lookup holding an envelope for the row's qitem bound to the premise hash
- WHEN the reconciler runs with that lookup
- THEN no envelope-absence diff is emitted for that row.

#### Scenario: mismatched envelope binding does not count

- GIVEN the same clean-landing fixture AND an envelope lookup whose entry for the row's qitem is bound to a different premise hash
- WHEN the reconciler runs with that lookup
- THEN it emits the stalled envelope-absence diff (a wrong-premise envelope is no envelope).

#### Scenario: envelope-absence attribution is report-only

- GIVEN a gated row with premise/verify/landing timestamps
- WHEN attribution runs
- THEN it reports premise age at landing (inputs for #17) and writes no tracker or queue state.

#### Scenario: red-proof for the presence check

- GIVEN the clean-landing-no-envelope fixture with a populated lookup
- WHEN the presence check is removed from the classifier (or the lookup is emptied at the call site)
- THEN the row reconciles silent (RED signature: no envelope-absence diff, exit 0 in sync)
- AND WHEN the check (and lookup) is restored byte-identical
- THEN the row stalls again (GREEN).
