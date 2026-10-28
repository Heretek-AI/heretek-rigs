# Tasks: topology-fix

Execution waves: implement (T1–T3) → acceptance (T4) → evidence (QA) →
audit (drift-guard). Map 1:1 to `specs/topology-render/spec.md`.

- [ ] T1 — REQ-F2: merge the duplicated check-6 loops in
      `scripts/topology.py:130-166` into a single guarded loop; no second
      `open()` of the same files; handles closed via context manager.
      Testable: `make verify` stays 22/0; `rg "6\. rig.yaml members" -c
      scripts/topology.py` == 1.
- [ ] T2 — REQ-F3: `render_bipartite` uses full `p` for package node IDs and
      edge endpoints, `short_pkg(p)` as DOT `label` only.
      Testable: `make topology OUT=<tmp>` exit 0 and
      `grep -rn '"pkg:"' <tmp>/bipartite-*.dot` returns nothing, while
      `grep -c 'pkg:@gotgenes' <tmp>/bipartite-*.dot` is nonzero.
- [ ] T3 — REQ-F1: rewrite the trigger sentence in `docs/USER_GUIDE.md`
      (§ Fleet Wiring) and the line-1 header comment of
      `.github/workflows/topology.yml` to state push-to-main path-scoped +
      PR path-scoped + `workflow_dispatch`; keep the artifact statement.
      Testable: `rg "every push/PR" docs/USER_GUIDE.md
      .github/workflows/topology.yml` returns nothing.
- [ ] T4 — Acceptance: from the stage worktree, `make verify`
      (expect `SUMMARY: 22 checks passed, 0 failed`) and
      `make topology OUT=/tmp/topo-<stage>` (expect exit 0 + T2 grep
      conditions). Record outputs for QA.
- [ ] T5 — Report: write `docs/reports/topology-fix-implementation.md`
      in the stage worktree (files changed, verification outputs).
