# Implementation report: topology-fix (stage topology-fix)

- Stage: topology-fix
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/topology-fix`
  (branch `fix/topology-render-gates`, base `main@939fc9d`)
- Spec: `openspec/changes/topology-fix/` (proposal.md, specs/topology-render/spec.md,
  design.md, tasks.md)
- Scope implemented: T1–T3 + acceptance T4. Report task: T5 (this file).
  NOT committed (coordinator commits).

## Files changed (3; no generated trees touched)

1. `scripts/topology.py`
   - T1 (REQ-F2): merged the duplicated check-6 loops (~L130-145) into a single
     guarded loop. The guarded `try: with open(rig_path) as fh:
     ry = yaml.safe_load(fh) / except (OSError, yaml.YAMLError)` read is now
     the read path for the member-validation logic; the second loop with the
     unguarded `open()` (leaked handle, unhandled exception path) is removed.
     Bidirectional member comparison unchanged.
   - T2 (REQ-F3): `render_bipartite` package nodes/edges now use full pin
     identity `p` — `"pkg:{p}"` with `[label="{short_pkg(p)}", shape=diamond]`
     and edges `"seat:{mid}" -> "pkg:{p}"` (both passed through the existing
     `dot_escape` helper). Removed `short = p.split("@")[0]` identity.
2. `docs/USER_GUIDE.md` (§ Fleet Wiring & Topography): trigger sentence now
   states push-to-`main` path-scoped + pull-request path-scoped + manual
   `workflow_dispatch`; artifact statement retained and made precise
   (SVGs + `graph.json` + `matrix.md`, 30-day retention).
3. `.github/workflows/topology.yml`: line-1 header comment now reads
   "on push to main (path-scoped), pull_request (path-scoped), and manual
   workflow_dispatch" — no CI behavior change.

Untouched as required: `specs/`, `rigs/`, `rosters/`, `registry/`, `fleet/`
(no regen required, no digest impact). `openspec/` untracked dir is the
pre-existing change proposal, not my output.

## Verification (T4 acceptance, from the worktree)

- `make verify` → exit 0, `SUMMARY: 22 checks passed, 0 failed` (all V1–V6
  stages PASS, 7/7 unit tests).
- `make topology OUT=/tmp/topo-fix` → exit 0; `graph.json` 238 nodes /
  1069 edges; org-chart + per-rig + bipartite SVGs rendered; only expected
  advisory WARN (50 omni-divergent `reports_to`).
- `grep -rn '"pkg:"' /tmp/topo-fix/bipartite-*.dot` → no matches (exit 1):
  zero empty-name nodes.
- Scoped nodes present in all 7 per-rig bipartite files, e.g.
  `"pkg:@gotgenes/pi-permission-system@41.0.0"
  [label="pi-permission-system", shape=diamond]` (12 hits in
  bipartite-executive-and-architecture.dot; 8–22 per file across all 7).
- Static gates: `grep -c '6\. rig.yaml members' scripts/topology.py` == 1;
  `rg "every push/PR" docs/USER_GUIDE.md .github/workflows/topology.yml`
  returns nothing; `python3 -c "ast.parse(...)"` syntax OK.
- `git status --short`: exactly the 3 intended modified files
  (plus pre-existing untracked `openspec/` proposal).

## Self-audit / deferred

- Nothing deferred: T1–T3 + T4 done, no stubs, no skipped checks, no new
  checks added, no gate renumbering.
- QA red-proofs (T5 follow-on) and drift-guard audit are out of scope for
  this stage — left for the QA/audit stages.
- Note: `render_bipartite` applies `dot_escape` to node IDs/labels; pins in
  the fixed allowlist contain no `"` or newlines (validated by check 5), so
  output is byte-identical to raw interpolation for the current tree.
