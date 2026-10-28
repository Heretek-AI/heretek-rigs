## ADDED Requirements

### Requirement: REQ-M1 — charter closure ownership

The seat charter MUST state: the destination seat closes its own row (`done` + closure reason) once its acceptance evidence is on the row, unless a `--gate <role>` qitem exists with a live owner. The rule MUST live in the mission-slice-sop skill, authored via generator inputs (never hand-edited leaves).

#### Scenario: owner closes with evidence on the row

- GIVEN a destination seat whose acceptance evidence is recorded on its row and no live gate qitem
- WHEN the seat ends its turn
- THEN the charter directs it to close the row `done` with a closure reason (no "standing by" prose).

#### Scenario: live gate exempts

- GIVEN a `--gate <role>` qitem with a live owner on the row
- WHEN convergence is evaluated
- THEN the row is not flagged for gateless waiting (the gate owner owns next action).

### Requirement: REQ-M2 — gateless awaiting-gate counts as stalled

The reconciler MUST classify a parent row with awaiting-gate prose and NO gate qitem reference as a stalled diff (not silent OTHER), routing for human review with the gate missing named explicitly. This MUST be red-proven: removing the classification returns the fixture to silent-OTHER.

#### Scenario: B2 pattern flagged

- GIVEN the B2-pattern fixture (verdict recorded, "standing by for gate" prose, no gate qitem)
- WHEN the reconciler runs
- THEN it emits the stalled-awaiting-gate diff (non-zero exit preserved) naming the missing gate.

#### Scenario: gated waiting stays quiet

- GIVEN awaiting-gate prose WITH a live gate qitem
- WHEN the reconciler runs
- THEN no stalled-awaiting-gate diff is emitted for that row.

### Requirement: REQ-M3 — recovery not dismissible without state change

Closing a stuck-recovery item while the flagged row's state is unchanged since flag time MUST be refused (fail-closed, redacted log). This MUST be red-proven: allowing dismissal restores the B2 outcome in fixture.

#### Scenario: dismissal without change refused

- GIVEN a flagged row whose state is byte-identical to flag time
- WHEN something attempts to close the recovery item
- THEN the close is refused; the flagged row keeps its state and the refusal is logged.

#### Scenario: dismissal with change allowed

- GIVEN the flagged row's state changed since flag time (owner acted: gate created, row advanced, verdict+closure recorded)
- WHEN the recovery item is closed
- THEN the close succeeds.

### Requirement: REQ-M4 — V29 gate and test corpus

The change MUST append a V29 verify block (new block, never renumber/reword V1–V28) and MUST ship corpus covering REQ-M2/M3 fixtures. V29 MUST be FAIL-ONLY pre-fix (B2 fixture silent on the unpatched tree) and PASS post-fix.

#### Scenario: FAIL-ONLY pre-fix proof recorded

- GIVEN the unpatched tree plus the S0 fixtures
- WHEN they run
- THEN the gateless parent is NOT flagged stalled and dismissal-without-change succeeds; both transcripts preserved in `docs/evidence/77-mission-gates-prefix.md`.

#### Scenario: post-fix gates green

- WHEN `./scripts/verify-rigs.sh --check-only` runs on the patched tree
- THEN the summary is 37 passed, 0 failed with V29 PASS and V1–V28 intact,
- AND `make test` exits 0 with zero failures.
