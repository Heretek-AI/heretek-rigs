# Delta spec: overhaul-b

## ADDED Requirements

### Requirement: REQ-B4 — 0.7.4 contract sync
`schemas/rigspec-keys.pinned.json` and the verify MEMBER_KEYS gate MUST include `codex_permissions` immediately after `claude_permissions`. `schemas/run-record.v1.schema.json` MUST be vendored byte-identical to the published 0.7.4 tarball file (sha256 `b3c7ac64fd9dd51152888c99fdbcadd85cddebebb2d38253864bff054da3fde7`) with a `contract-schemas.sha256` entry, covered by the contract suite. `messaging-the-human` + `queue-handoff` SKILL.md MUST be synced from the published tarball through the generator path (never hand-edited leaves), followed by a full clean-tree regen.

#### Scenario: contracts green
- When the contract suite + regen + idempotence run, all pass with digests self-consistent and no DIRTY stamps.

### Requirement: REQ-B5 — test wiring, canary, V19
`make test` MUST run every `tests/test_*.py` suite via `unittest discover`. `test_canary_scope_only` MUST pass on a full clone AND when `a33f3bb` is unresolvable (fixture fallback), with the expected-role set updated to the post-#121 reality. V19 MUST compare against the canonical gate total, not `passes + 1`, so one host failure cannot trip doc-drift gates. V12 MUST emit `[NOTE]` (not fail) when `bwrap` is absent and `HERETEK_ALLOW_NO_BWRAP=1`, staying mandatory otherwise.

#### Scenario: full suite green, no cascade
- When `make test` runs, every suite executes with 0 failures/errors; when one early host check fails, only its own gate fails.

## MODIFIED Requirements

### Requirement: REQ-G1 — append-only, generator rule
New coverage MUST be new appended blocks (or new scripts), never renumber/reword of V1–V27. `specs/` `rigs/` `rosters/` `registry/` MUST change only via `generate-rigs.py`; `yaml.safe_load` only; never `yaml.safe_dump` on `fleet/fleet.yaml`.

#### Scenario: gates intact
- When `make verify` runs after this change, V1–V27 pass unrenamed and SUMMARY stays frozen.
