# Implementation report: docs-write-scopes (T1–T4)
Branch: fix/docs-write-scopes (from main bae5d3a).

## T1 — fleet.yaml edit (6 insertions, surgical, python-applied with assertions)
- exec-product-director: + docs/brief/*
- build-ts-node-fullstack: + docs/architecture/*
- design-ui-ux-designer: + docs/design-system/*
- design-design-system-eng: + docs/design-system/*
- design-ux-research-analyst: + docs/design-system/*
- design-a11y-specialist: + docs/design-system/*
- exec-system-architect: unchanged (already docs/architecture/*).
No other fleet.yaml lines touched. No bash/MCP/git-verb changes anywhere.

## T2 — regen
HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py exit 0
("wrote 51 specialist AgentSpecs, 68 shared skills, 8 RigBundles...").
Regenerated leaves: registry/entries+views+status, rigs/*/agents/*/guidance/role.md
+ runtime/pi-permission-config.json. Verified sample:
rigs/*/agents/ui-ux-designer/runtime/pi-permission-config.json contains
docs/design-system (both rig copies).

## T3 — acceptance
- make verify: SUMMARY 22 checks passed, 0 failed.
- tests/test_render_seat.py: 7/7 passed (inside verify).
- seed dry-run (rig.all-51.yaml): 51 ok. Live state/pi configs NOT touched
  (dry-run only) — running fleet still enforces old policy until post-merge
  reseed + relaunch. Post-merge live proof is T5 (QA-owned).

## T4 — notes for QA/drift-guard
- Guards to red-proof: no git stage/commit verbs added (all roles read-only
  git); AGENTS.md deny intact in rendered path rules; ts-node still lacks
  docs/brief/* (least-privilege holds); fleet.yaml diff is exactly +6 lines.
- Non-finding: full-file regen noise across registry/views is deterministic
  replay (same class as topology-fix observation).
- Bounce warning: reseed/relaunch kills in-memory author drafts — TPM
  collect-drafts qitem must land first (check before T5).
