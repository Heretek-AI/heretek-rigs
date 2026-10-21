# Proposal: topology-fix — verify-then-fix for 3 confirmed render/gate defects

## Status
Scope approved for execution (operator "Execute", 2026-10-22). All three
premises verified read-only on `main@939fc9d` before authoring; finding F3
additionally reproduced via `make topology` render output.

## Motivation
PR #5 (fleet-topology refresh, merged as `939fc9d`) shipped three defects
flagged in review and confirmed by the operator session:

- **F1 — inaccurate trigger docs.** `docs/USER_GUIDE.md` (§ Fleet Wiring,
  ~L398-399) and the header comment of `.github/workflows/topology.yml`
  (line 1) claim the job runs "on every push/PR". Actual triggers:
  `push` to `main` path-scoped, `pull_request` path-scoped, plus
  `workflow_dispatch`. A push to `main` touching only `docs/` does not
  trigger it; neither does a push to a feature branch.
- **F2 — duplicated check-6 loop.** `scripts/topology.py:130-145`: the first
  loop opens every `rigs/<id>/rig.yaml` with a guarded read and discards the
  result; the second loop re-iterates the same rigs and re-reads with an
  unguarded `open()` (no close, leaks the handle, unhandled exception path).
- **F3 — scoped-package node collision (rendered, live).**
  `scripts/topology.py:348-351` keys bipartite graph nodes/edges on
  `p.split("@")[0]`, which is `""` for every scoped pin
  (e.g. `@gotgenes/pi-permission-system@41.0.0`, used fleet-wide).
  Rendered output contains 116 lines of empty `"pkg:"` nodes/edges across all
  7 per-rig bipartite `.dot` files — multiple seats collapse onto one broken
  node. Proof: `/tmp/topo-verify/bipartite-*.dot` from `make topology`
  on unmodified `main`.

## Boundaries
- Touch ONLY: `scripts/topology.py`, `docs/USER_GUIDE.md`,
  `.github/workflows/topology.yml` (comment line only).
- No fleet catalog changes (`fleet/`, `specs/`, `rigs/`, `rosters/`,
  `registry/` untouched — no regen required, no digest impact).
- No behavior change to fail-closed gate outcomes: identical PASS/FAIL on
  the current tree; only duplicate work removed and node identity fixed.

## Non-goals
- PR #4 rebase / arm64 QEMU verdict, S02 workspace, godot-webui Phase 0,
  MCP pin freshness, org-sync standards (#34).
- No new checks, no renumbering of `verify-rigs.sh` gates.

## Acceptance (see tasks.md)
1. `make verify` → `SUMMARY: 22 checks passed, 0 failed`.
2. `make topology OUT=<tmp>` → exit 0; zero `"pkg:"` empty-name nodes in
   any `bipartite-*.dot`; scoped packages appear as distinct nodes.
3. QA red-proofs recorded: each fix re-broken (sabotage) and observed to
   fail its check, then reverted.
