# QA report: topology-fix (commit deced5f)

- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/topology-fix`
- Commit verified: `deced5f feat(topology-fix): merge check-6 loop, full-pin bipartite nodes, accurate trigger docs` (parent `939fc9d`)
- Scope: `openspec/changes/topology-fix/` (proposal, specs/topology-render/spec.md, design.md, tasks.md T1-T5)
- Programmer report checked: `docs/reports/topology-fix-implementation.md` -- claims verified independently below (not trusted).
- Verdict: **PASS** -- all acceptance checks green on the unmodified tree; all three red-proofs demonstrate fail-closed gates; no vacuous checks; tree restored to deced5f content (tracked files identical).

## Acceptance results (unmodified tree)

| # | Check | Command | Expected | Observed | Result |
|---|-------|---------|----------|----------|--------|
| A1 | Full gate suite | `make verify` | `SUMMARY: 22 checks passed, 0 failed`, exit 0 | 22 passed / 0 failed, exit 0 | PASS |
| A2a | Topology render | `make topology OUT=/tmp/topo-qa` | exit 0 | exit 0; `graph.json` 238 nodes / 1069 edges; org-chart + per-rig + bipartite SVGs rendered; only expected advisory WARN (50 omni-divergent `reports_to`) | PASS |
| A2b | No empty pkg nodes | `grep -rn '"pkg:"' /tmp/topo-qa/bipartite-*.dot` | no matches (exit 1) | no matches, exit 1 | PASS |
| A2c | Scoped pins distinct | `grep -c 'pkg:@gotgenes' bipartite-executive-and-architecture.dot` | nonzero | 12; present in all 7 per-rig files, e.g. `"pkg:@gotgenes/pi-permission-system@41.0.0" [label="pi-permission-system", shape=diamond]` | PASS |
| A3 | Trigger-docs gate | `rg "every push/PR" docs/USER_GUIDE.md .github/workflows/topology.yml` | no matches (exit 1) | no matches, exit 1 | PASS |

Programmer-report cross-check: T1 single guarded check-6 loop confirmed (`grep -c '6. rig.yaml members'` == 1, no unguarded rig.yaml `open`); T2 full-pin identity with `short_pkg` labels confirmed; T3 guide + workflow header wording confirmed (push-to-`main` path-scoped + PR path-scoped + `workflow_dispatch`, 30-day artifact retention retained); boundary holds (only the 3 intended files differ vs `939fc9d`; `specs/`, `rigs/`, `rosters/`, `registry/`, `fleet/` untouched).

## Red-proof summary (all sabotage reverted; see `docs/evidence/topology-fix/red-proofs.log`)

| Finding | Sabotage | RED signal observed | Revert + re-verify | Vacuous? |
|---------|----------|---------------------|--------------------|----------|
| F3 node collision | Restored `p.split("@")[0]` identity in `render_bipartite` | `grep '"pkg:"'` exit 0 with **116** empty-node lines across 7 files (matches proposal finding verbatim) | `git checkout` restores; grep exit 1, scoped nodes back | No |
| F2 duplicated loop | Re-inserted pre-fix second `# 6.` loop with unguarded `open()` | Structural gate `test $(grep -c '6. rig.yaml members') -eq 1` FAILS (count 2); unguarded-open pattern present; probe shows unhandled OSError path. `make verify` stayed 22/0 under pure duplication -- expected per spec identical-outcomes boundary | `git checkout` restores; count 1, gate PASS, `make verify` 22/0 | No |
| F1 trigger wording | Restored "every push/PR" in `docs/USER_GUIDE.md` | `rg "every push/PR"` exit 0 with match (gate RED) | `git checkout` restores; exit 1, no matches | No |

## Tree state

- `git status --short`: clean except the two new untracked QA artifacts (this report + `docs/evidence/topology-fix/red-proofs.log`).
- `git diff deced5f --stat`: empty -- all tracked files byte-identical to deced5f. Implementation files unmodified by QA.
- Nothing committed (coordinator commits evidence per stage protocol).
