# Delta spec: machine-parseable queue output discipline

## ADDED Requirements

### Requirement: REQ-44-A1 — every queue example carries --json
All `rig queue list` / `show` / `create` examples in generated seat charters
(`scripts/generate-rigs.py`), `docs/USER_GUIDE.md`, `README.md`, and the root
`AGENTS.md` queue-workflow row MUST use `--json`, and MUST carry a statement
that bare output mixes JSON with a human trailer and MUST NOT be parsed.

#### Scenario: documented flags parse first try
- Given the patched docs and charters,
- When an operator copy-pastes a documented queue command,
- Then `json.load(stdout)` succeeds on the first try (no `Extra data` error).

### Requirement: REQ-44-A2 — upstream issue filed with byte-exact evidence
The implementer MUST draft an upstream issue against `mvschwarz/openrig`
requesting both stdout notices (bounded-preview trailer `queue.js:1115-1117`
and compact notice `queue.js:1118-1123`) move to stderr, citing the
transitions-notice-on-stderr precedent (`queue.js:1116-1143` region), MUST
file it (`gh` or web), and MUST record the filed issue URL in this change
package (proposal.md append or tasks.md evidence line).

#### Scenario: one upstream issue, linked locally
- Given the filed upstream issue URL recorded in this package,
- When a reviewer opens it,
- Then its body contains the byte-exact trailer bytes, the failing
  `json.load(stdout)` reproduction, the stderr precedent, and the request
  covering BOTH notices — and `remediate-42-create-receipt` references the
  SAME URL (single shared issue, no duplicates).

### Requirement: REQ-44-A3 — parse-first-try returnable
Copy-pasting the issue's originally failing commands with the documented
`--json` flags MUST parse first try.

#### Scenario: tonight's failing commands now parse
- Given the exact `queue show` / `queue list` commands from #44's evidence,
- When re-run with the documented `--json` flags,
- Then JSON parsing succeeds with no `Extra data` failure.

## MODIFIED Requirements

### Requirement: REQ-44-M1 — bare examples replaced in place
Existing bare queue examples in charters and guides MUST be edited in place
(generator + regen for charters — never hand-edit `specs/`, `rigs/`,
`rosters/`, or `registry/`).

#### Scenario: regen keeps the tree green
- Given the patched generator plus a regen run,
- When `make verify` runs,
- Then all checks still pass (22/0).
