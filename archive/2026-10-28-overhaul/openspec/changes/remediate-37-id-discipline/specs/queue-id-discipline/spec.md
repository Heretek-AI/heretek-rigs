# Delta spec: seat-side qitem ID discipline

## ADDED Requirements

### Requirement: REQ-37-A1 — charter teaches --json ID copy
Generated seat charters (via `scripts/generate-rigs.py` queue primer) MUST
instruct seats to run `rig queue list` with `--json` whenever an ID will be
reused, and to copy the `qitem-…` value verbatim from that JSON output.

#### Scenario: charter primer mandates JSON copy
- Given a freshly regenerated seat charter,
- When the seat reads its queue primer,
- Then the primer contains a `--json` list example AND a never-retype-ID rule.

### Requirement: REQ-37-A2 — operator guides show --json forms
`docs/USER_GUIDE.md`, `README.md`, and the root `AGENTS.md` queue-workflow row
MUST show `--json` on every `rig queue list` / `show` example and MUST state
that qitem IDs are copied from `--json` output, never retyped.

#### Scenario: no bare queue read examples remain
- Given the patched guides,
- When an operator greps for bare `rig queue list` / `rig queue show` examples,
- Then every read example carries `--json` (or an explicit statement that the
  bare form's IDs MUST NOT be retyped).

### Requirement: REQ-37-A3 — live copy-paste proof
After implementation, an ID copied from plain `rig queue list` output MUST
succeed in `rig queue show <id>` with zero `qitem_not_found` failures,
confirming list output carries full IDs and the discipline holds.

#### Scenario: copied ID resolves first try
- Given a live fleet with queued items,
- When an operator copies an ID from list output into `queue show`,
- Then the show succeeds without not-found errors.

## MODIFIED Requirements

### Requirement: REQ-37-M1 — bare charter primer updated
The existing bare ``rig queue list`` primer in `scripts/generate-rigs.py`
(~line 701) MUST be updated in place (followed by deterministic regen —
never hand-edit `specs/`, `rigs/`, `rosters/`, or `registry/`).

#### Scenario: regen carries the new primer
- Given the patched generator plus a regen run,
- When `make verify` runs,
- Then all checks still pass (22/0) and rendered leaves contain the new primer.
