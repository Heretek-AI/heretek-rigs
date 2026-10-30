# auth-envelope Specification — F4 Amendment Delta

This change is a MODIFIED delta: it ADDS REQ-E5 only. It does NOT touch
REQ-E1, REQ-E2, REQ-E3, or REQ-E4 text. The REQ-E2 clean-quiet scenario and
its corpus pins (`test_clean_premise_stays_quiet`,
`test_reconcile_end_to_end_clean_quiet`) stay byte-intact; REQ-E5 is opt-in
and fires only where an envelope lookup exists, so the default
(empty/absent lookup) keeps clean premises quiet by construction.

## ADDED Requirements

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
