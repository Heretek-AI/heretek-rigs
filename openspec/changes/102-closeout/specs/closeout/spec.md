# Delta spec: 102-closeout

## ADDED Requirements

### Requirement: REQ-C18 — bare queue/send deny in seat maps
Seat bash maps rendered from `fleet/fleet.yaml` MUST deny bare `rig queue list`, bare `rig queue create` without `--json --verify`, and bare `rig send`. The `--json --verify` forms MUST continue to allow where the seat holds the `rig queue *` / `rig send *` grant. `AGENTS.md` MUST carry a one-line operator gate stating bare forms are denied in-seat (extending the existing `--json --verify` discipline). A new appended verify block MUST assert the deny (no renumber of V1–V21).

#### Scenario: bare forms deny, disciplined forms allow
- When the seat-map gate runs after implementation, bare `rig queue list`, bare `rig queue create` without `--json --verify`, and bare `rig send` are denied in-seat while `--json --verify` forms allow, with red-proofs recorded in both directions.

### Requirement: REQ-C25 — all-51 canonical statement
Docs MUST state `rig spec validate` (V18 `scripts/verify-rigs.sh:2442-2454`) is canonical for `rigs/heretek-omni-fleet/rig.all-51.yaml`, and `rig bundle check` covering only the 8 `rig.yaml` files (`:2419-2428`) is intentional. No code change in this requirement.

#### Scenario: canonical statement present
- When the docs are grepped after implementation, the canonical statement exists and V18 passes on `rig.all-51.yaml`.

### Requirement: REQ-CWS — writing-skills vendor fix
The dangling `superpowers:writing-skills` reference in `specs/agents/_shared/skills/test-driven-development/writing-good-tests.md:51` MUST be resolved via the `fleet/skill-patches/` + `generate-rigs.py` regen path. Direct hand-edits of `specs/` are FORBIDDEN. After regen, `grep -rn 'superpowers:writing-skills' specs/ fleet/` MUST return zero hits and the skill loader MUST report 68/68 with no DIAG.

#### Scenario: zero dangling refs, loader green
- When the grep and loader run after implementation, zero hits are returned and 68/68 skills load with no diagnostics.

### Requirement: REQ-CDAG — local DAG evidence note
A local evidence note `docs/evidence/102-closeout-dag.md` MUST record the local `delegates_to/spawned_by` cycle check (`scripts/verify-rigs.sh:896`) outcome and the decision for local-note-only (no upstream filing). No upstream issue/PR SHALL be filed in this change.

#### Scenario: evidence note exists
- When the evidence path is listed after implementation, `docs/evidence/102-closeout-dag.md` exists and cites the real cycle-gate line.

## MODIFIED Requirements

### Requirement: REQ-G1 — append-only, generator rule
New coverage MUST be new appended blocks (or new scripts), never renumber/reword of V1–V21. `specs/` `rigs/` `rosters/` `registry/` MUST change only via `generate-rigs.py`; `yaml.safe_load` MUST be used for any YAML parsing (no `yaml.load`).

#### Scenario: gates intact
- When `make verify` runs after this change, V1–V21 pass unrenamed and SUMMARY stays frozen.
