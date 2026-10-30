# Bump

## Purpose
Pinned OpenRig CLI toolchain upgrades with ledger pinning, tarball hash verification, and green verification gates.

## Requirements

### Requirement: REQ-G1 — append-only, generator rule
New coverage MUST be new appended blocks (or new scripts), never renumber/reword of V1–V31. `specs/` `rigs/` `rosters/` `registry/` MUST change only via `generate-rigs.py`.

#### Scenario: gates intact
- When `make verify` runs after this change, V1–V31 pass unrenamed and SUMMARY stays frozen at 39.

### Requirement: REQ-BUMP1 — pinned 0.7.4 toolchain with ledger
**Status: SUPERSEDED by REQ-BUMP3** — 0.7.5 toolchain promoted; retained for history, no longer normative.
The build host toolchain MUST run `@openrig/cli@0.7.4` (`rig --version` → `0.7.4`). A bump ledger `docs/sprints/CLI-0.7.4-BUMP.md` MUST record the version output, the published tarball sha256 (`d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1`), every pin location updated, and the verify result.

#### Scenario: version and ledger present
- When `rig --version` runs on the build host it prints `0.7.4`, and `docs/sprints/CLI-0.7.4-BUMP.md` contains the version string, the tarball SHA, and the green verify output.

### Requirement: REQ-BUMP2 — green tree on bumped toolchain
**Status: SUPERSEDED by REQ-BUMP4** — SUMMARY 39 / 0.7.5 gates promoted; retained for history, no longer normative.
`make verify` MUST be green on the bumped toolchain with no gate renames and SUMMARY frozen at 35. `generate-rigs.py --check-idempotent` MUST pass (idempotence-with-0.7.4-vendor deferred to Wave B: the default resolver now sources installed 0.7.4 skills per `generate-rigs.py:623-643`, so a run here would vendor Wave B content; this wave holds by empty leaf diff) and `audit_loop.py --self-test` MUST print SELF-TEST PASSED.

#### Scenario: gates hold the bump
- When the full gate suite runs after the bump, `SUMMARY: 35 checks passed, 0 failed` plus V22/V23/V24 info lines, idempotence-with-0.7.4-vendor deferred to Wave B (empty leaf diff), and self-test passes.

### Requirement: REQ-BUMP3 — pinned 0.7.5 toolchain with ledger
The build host toolchain MUST run `@openrig/cli@0.7.5` (`rig --version` →
`0.7.5 (b57c4da3)`). A bump ledger `docs/sprints/CLI-0.7.5-BUMP.md` MUST
record the version output, the published tarball sha256
(`22d67c2c7e0d0ab4a5ec9faac0a725d54f9ead2c0f71564985cf4ae240bb9754`,
re-verified by two independent fetches), every pin location updated (the 8
true-pin files), the 0.7.4→0.7.5 tarball-diff disposition (zero
generator-input changes: MEMBER_KEYS identical, run-record byte-identical,
queue-handoff skill-body delta deferred), and the verify result.

#### Scenario: version and ledger present
- When `rig --version` runs on the build host it prints `0.7.5`, and
  `docs/sprints/CLI-0.7.5-BUMP.md` contains the version string, the tarball
  SHA with two-fetch evidence, the 8 true-pin files, and the green verify
  output.

### Requirement: REQ-BUMP4 — green tree on bumped toolchain
`./scripts/verify-rigs.sh --check-only` MUST be green on the bumped toolchain
with no gate added, renumbered, or reworded and SUMMARY frozen at 39
(V18 fail-closed `rig --version` gate MUST assert `0.7.5`; V13 MUST assert
`ARG OPENRIG_VERSION=0.7.5`). `generate-rigs.py --check-idempotent` MUST exit
0 byte-identical (no generator input changed, so no regen is owed) and
`audit_loop.py --self-test` MUST print SELF-TEST PASSED. `make test` MUST
pass with ≥634 tests and 0 failures.

#### Scenario: gates hold the bump
- When the full gate suite runs after the bump, `SUMMARY: 39 checks passed, 0
  failed` with V18/V13 asserting the 0.7.5 pins, idempotence exit 0, and
  self-test passes.
