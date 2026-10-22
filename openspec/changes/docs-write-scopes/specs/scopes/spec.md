# Delta spec: author documentation write scopes

## ADDED Requirements

### REQ-S1: product-director brief scope
exec-product-director path_write MUST include `docs/brief/*` alongside the
existing `docs/product/*`. Rationale: the brief slice target is
docs/brief/product-brief-v0.1.md across missions.

### REQ-S2: pipeline architecture scope
build-ts-node-fullstack path_write MUST include `docs/architecture/*`
alongside existing `src/*` and `package.json`. Rationale: co-owns the
architecture pipeline slice with system-architect.

### REQ-S3: design-system scopes
design-ui-ux-designer, design-design-system-eng, design-ux-research-analyst,
and design-a11y-specialist path_write MUST each include
`docs/design-system/*` alongside their existing entries. Rationale: all four
design slices target docs/design-system/.

## MODIFIED Requirements

### REQ-G1: guards unchanged
No role gains git stage/commit/push verbs, no bash_allow changes, no MCP
changes. Root AGENTS.md MUST remain outside every role's write scope.
verify-rigs.sh MUST remain 22 checks, 0 failed, with no renumbering.
