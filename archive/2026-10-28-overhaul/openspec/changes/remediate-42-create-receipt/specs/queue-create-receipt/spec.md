# Delta spec: agent-safe queue create receipt

## ADDED Requirements

### Requirement: REQ-42-A1 — create --json --verify is the only agent-safe form
Charters (`scripts/generate-rigs.py`), `docs/USER_GUIDE.md`, `README.md`, and
the root `AGENTS.md` queue-workflow row MUST present
`rig queue create --json --verify` (or `--full`) as the only agent-safe
create form, and MUST state that bare `create` output is a human advisory,
not proof of persistence.

#### Scenario: single create yields identity and state
- Given the documented flags,
- When an agent runs one `create --json --verify`,
- Then stdout yields the qitemId and row state with no follow-up `show`.

### Requirement: REQ-42-A2 — send-authenticated.sh parses the receipt
`scripts/send-authenticated.sh` (the sole local create wrapper) MUST invoke
create with the agent-safe flags and MUST parse the JSON receipt to extract
`qitemId` and state, failing closed (non-zero exit, no silent pass) when the
receipt does not parse as JSON.

#### Scenario: unparseable receipt fails closed
- Given a create whose stdout is not valid JSON,
- When the wrapper runs,
- Then it exits non-zero and reports the raw stdout for diagnosis instead of
  claiming delivery.

### Requirement: REQ-42-A3 — shared upstream issue reference
This package MUST reference the SAME single upstream issue URL filed via
`remediate-44-json-trailer` (tasks T4/T5), whose request covers the
stdout-purity principle for the create receipt (single JSON receipt/row on
stdout, human hint to stderr). No second upstream issue SHALL be filed.

#### Scenario: exactly one upstream issue across both changes
- Given the recorded URLs in both packages,
- When a reviewer compares them,
- Then they are identical (one issue, two local references).

## MODIFIED Requirements

### Requirement: REQ-42-M1 — bare create examples replaced in place
Existing bare `rig queue create` examples in charters and guides MUST be
edited in place (generator + regen for charters — never hand-edit `specs/`,
`rigs/`, `rosters/`, or `registry/`).

#### Scenario: regen keeps the tree green
- Given the patched generator plus a regen run,
- When `make verify` runs,
- Then all checks still pass (22/0).
