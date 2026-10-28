# Delta spec: overhaul-bump

## ADDED Requirements

### Requirement: REQ-BUMP1 — pinned 0.7.4 toolchain with ledger
The build host toolchain MUST run `@openrig/cli@0.7.4` (`rig --version` → `0.7.4`). A bump ledger `docs/sprints/CLI-0.7.4-BUMP.md` MUST record the version output, the published tarball sha256 (`d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1`), every pin location updated, and the verify result.

#### Scenario: version and ledger present
- When `rig --version` runs on the build host it prints `0.7.4`, and `docs/sprints/CLI-0.7.4-BUMP.md` contains the version string, the tarball SHA, and the green verify output.

### Requirement: REQ-BUMP2 — green tree on bumped toolchain
`make verify` MUST be green on the bumped toolchain with no gate renames and SUMMARY frozen at 35. `generate-rigs.py --check-idempotent` MUST pass (idempotence-with-0.7.4-vendor deferred to Wave B: the default resolver now sources installed 0.7.4 skills per `generate-rigs.py:623-643`, so a run here would vendor Wave B content; this wave holds by empty leaf diff) and `audit_loop.py --self-test` MUST print SELF-TEST PASSED.

#### Scenario: gates hold the bump
- When the full gate suite runs after the bump, `SUMMARY: 35 checks passed, 0 failed` plus V22/V23/V24 info lines, idempotence-with-0.7.4-vendor deferred to Wave B (empty leaf diff), and self-test passes.

## MODIFIED Requirements

### Requirement: REQ-G1 — append-only, generator rule
New coverage MUST be new appended blocks (or new scripts), never renumber/reword of V1–V24. `specs/` `rigs/` `rosters/` `registry/` MUST change only via `generate-rigs.py`.

#### Scenario: gates intact
- When `make verify` runs after this change, V1–V24 pass unrenamed and SUMMARY stays frozen.
