# Delta spec: overhaul-c

## ADDED Requirements

### Requirement: REQ-C6 — archive with exclusions
Stale-only content MUST move to `archive/2026-10-28-overhaul/` preserving relative paths via `git mv`: the 22 pre-overhaul `openspec/changes/` folders (all except `102-closeout`, `107-identity`, `overhaul-bump`, `overhaul-a`, `overhaul-b`), `docs/reports/` + `docs/evidence/` entries not matching `*102-closeout*`, `*107-identity*`, `*overhaul-*` (plus `rotation.md` stays regardless), `claude/`, `gemini/`, `docs/sprints/` (except `docs/sprints/CLI-0.7.4-BUMP.md`, the live 0.7.4 toolchain ledger required at that path by `openspec/specs/bump/spec.md`), `docs/architecture/`, `docs/ops/`, `docs/perf/`, `docs/PROMPT_*`, `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md`, `REMEDIATION_LOG.md`, `st2p-proposal-package-lock.json`, `HANDOFF_CLAUDE_AUDIT.md`, `PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md`, `PROMPT_FLEET_AUDIT_REMEDIATION.md`, tracked `.opencode/` files. `.gitignore` MUST gain `.opencode/`, `.lane/`, `st2p-proposal-package-lock.json`. Every moved path MUST resolve in history (`git log --follow` works); every keep-list path MUST be byte-identical before/after.

#### Scenario: stale gone, live intact
- When the move completes, `test ! -e` passes for every stale path, keep-list files are byte-identical, and moved files retain history.

### Requirement: REQ-C7 — audit prompt placement
`docs/IMPLEMENTATION_PROMPT.md` MUST be written fresh from the reconciled plan and current gates (the pre-#122 upload MUST NOT be placed verbatim). The existing root `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` MUST be kept as-is. `scripts/audit_loop.py` MUST reference the new prompt path in its constant, help text, and execution read, and its remediation message MUST NOT cite the archived `REMEDIATION_LOG.md` path as live.

#### Scenario: self-test green on new paths
- When `audit_loop --self-test` runs, it passes referencing the placed prompt, and no code path reads an archived location as live input.

### Requirement: REQ-C8 — regen + full gates on archived tree
After the move, a clean-tree regen MUST produce no unexpected leaf changes (moves touch no generator inputs), `--check-idempotent` MUST pass, `make verify` MUST be green (35/0 + V22–V27, SUMMARY frozen), `make test` MUST run all suites with 0 failures, and `make topology OUT=/tmp/topology-c` MUST exit 0.

#### Scenario: archived tree fully green
- When all five commands run on the archived tree, every one exits 0.

## MODIFIED Requirements

### Requirement: REQ-G1 — append-only, generator rule
Gate/file-list updates (HR-8.4 list, AGENTS.md/README maps) MUST be surgical text edits, never renumber/reword of V1–V27. `specs/` `rigs/` `rosters/` `registry/` MUST change only via `generate-rigs.py`.

#### Scenario: gates intact
- When `make verify` runs after this change, V1–V27 pass unrenamed and SUMMARY stays frozen.
