# Delta spec: topology render + gate docs

## MODIFIED Requirements

### REQ-F1: Workflow trigger documentation MUST match `topology.yml:15-35`
`docs/USER_GUIDE.md` (§ Fleet Wiring & Topography) and the
`.github/workflows/topology.yml` header comment MUST describe the actual
triggers: `push` to `main` limited to the listed paths, `pull_request`
limited to the listed paths, and manual `workflow_dispatch` — and MUST NOT
claim the job runs "on every push/PR". The artifact-upload statement
(SVGs + `graph.json` + `matrix.md`, 30-day retention) MUST be retained and
MUST remain accurate.

### REQ-F2: Single guarded rig.yaml member-validation loop
`scripts/topology.py` check 6 MUST iterate the rig list (fleet rigs + omni)
exactly once. The guarded file read (handling `OSError` /
`yaml.YAMLError` with `rep.fail(...)` + `continue`) MUST be the read path
for the member-validation logic. There MUST NOT be a second loop that
re-opens the same files, and file handles MUST be closed (context manager
or equivalent). Gate outcomes on the current tree MUST be unchanged
(same PASS/FAIL set — verified by `make verify` 22/0 before and after).

### REQ-F3: Bipartite package nodes MUST use full pin identity
In `render_bipartite`, package node IDs and seat→package edge endpoints
MUST use the full package string `p` (e.g.
`@gotgenes/pi-permission-system@41.0.0`), so distinct pins are distinct
nodes. Human-readable short labels MAY be shown via the existing
`short_pkg(p)` helper as the DOT `label` attribute. There MUST be no
`"pkg:"` empty-name node in any rendered `bipartite-*.dot`.
