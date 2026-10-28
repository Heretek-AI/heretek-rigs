# Proposal: docs-write-scopes — role-natural documentation write grants
Status: scope approved (operator "fix this once and for all", 2026-10-22).
Root cause (verified read-only): mission deliverables live in docs/brief,
docs/architecture, docs/design-system, but 6 of 7 Phase-0 author roles hold
write scope only on code/staging dirs. Only exec-system-architect
(docs/architecture/*) can deliver its slice. Every docs-producing mission
(godot-webui P0, asset-manager P0, all future) stalls on write denials and
funnels through operator relay. The scribe role (delivery-tech-docs-lead)
already holds docs/* — the machinery exists; the gap is author-area grants.

## Change
Extend path_write for the six author roles to cover their documentation
area (least privilege, mission-agnostic — works for every future mission):
- exec-product-director: + docs/brief/*
- build-ts-node-fullstack: + docs/architecture/*
- design-ui-ux-designer: + docs/design-system/*
- design-design-system-eng: + docs/design-system/*
- design-ux-research-analyst: + docs/design-system/*
- design-a11y-specialist: + docs/design-system/*
- exec-system-architect: unchanged (already covered)
No other changes: no commit verbs added anywhere (all git verbs stay
read-only), no root AGENTS.md exposure (docs/* patterns do not match it),
no MCP/bash changes, no regen-exempt edits.

## Acceptance
1. generate-rigs.py clean regen; verify-rigs.sh 22/0; test_render_seat 7/7.
2. Rendered seat configs contain the new grants (seed dry-run grep).
3. Post-merge reseed + relaunch: each of the six roles can write its area;
   overreach still denied (ts-node cannot write docs/brief/; NOBODY gains
   git stage/commit; root AGENTS.md untouched by all).
4. Currently-blocked asset-manager slices deliver their own files, no relay.
