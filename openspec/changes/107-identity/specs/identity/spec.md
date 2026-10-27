# Delta spec: 107-identity

## ADDED Requirements

### Requirement: REQ-I0 — live spike evidence first
The change MUST begin with a live M0 spike against the installed `rig` 0.7.2 (`8b180689`) and MUST record the outcome in `docs/evidence/107-identity-m0.md` before M1 automation is designed. M1 MUST follow the spike winner; if the queue half proves daemon-blocked, no repo-side queue grants SHALL be built.

#### Scenario: spike log gates M1
- When the implementer finishes M0, `docs/evidence/107-identity-m0.md` contains the exact commands plus Bearer-allow (200), bad-token 401, revoked-token 401, and `rig_whoami` authenticated-vs-declared outputs and the queue-half probe result, and M1's design section cites which winner it follows.

### Requirement: REQ-I1 — per-seat MCP bearer grants with seed issuance
Seat MCP-over-HTTP access MUST require a per-seat bearer grant (`rig mcp token add <name> --seat <session> --rig <rig>`, hash-only storage). Issuance MUST run at seed time (`seed-rig.py`), but ONLY for seats whose role binds a catalog entry marked `seat_grant: true` (or via explicit opt-in); unmarked HTTP entries and stdio servers are unchanged and receive no grant. Issuance stores the once-printed token under the secrets dir and renders it into the seat's MCP client config via the existing `!cat` pattern. A seat's grant MUST NOT reach another seat's rigs/roots (scoped to the seat's own managed rig via `--rig`; no `--root/--workspace/--owner` per M0 outcome).

#### Scenario: cross-seat bearer denied
- When a request presents seat A's token for seat B's scope, the MCP HTTP adapter refuses with 401/`out_of_scope` and the red-proof log records the exact refusal.

### Requirement: REQ-I2 — revoke-based rotation runbook
Rotation MUST be documented as revoke + re-add (`rig mcp token revoke <name>` effective on the next request; already-handed-over work stays with its owners). The runbook MUST be executed live end-to-end and a revoked token MUST 401.

#### Scenario: revoked token refused
- When a previously valid token is revoked and presented again, the server refuses (401) and the evidence log records the exact output.

### Requirement: REQ-I3 — queue-half disposition on evidence
The queue/send spoofability half (`OPENRIG_SESSION_NAME` bare-leading form) MUST be dispositioned on M0 evidence: repo-side fix with a green gate if M0 shows it possible, otherwise a documented-upstream-blocked note citing the exact probe output. Upstream filing SHALL NOT occur without principal authorization.

#### Scenario: blocked half documented, not built
- When M0 shows the daemon still trusts the loopback seat header, `docs/evidence/107-identity-queue.md` records the probe output and the upstream-blocked verdict, and no queue-identity code is added.

## MODIFIED Requirements

### Requirement: REQ-G1 — append-only, generator rule
New coverage MUST be new appended blocks (or new scripts), never renumber/reword of V1–V22. `specs/` `rigs/` `rosters/` `registry/` MUST change only via `generate-rigs.py`; `yaml.safe_load` MUST be used for any YAML parsing.

#### Scenario: gates intact
- When `make verify` runs after this change, V1–V22 pass unrenamed and SUMMARY stays frozen.
