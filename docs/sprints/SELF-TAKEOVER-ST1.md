# SELF-TAKEOVER-ST1 — Grafana binding + sabotage pin bump (APPLIED by operator)

- Slice qitem: qitem-20261021155438-17c7bd79e62951c9 (ST-1), reassigned ST-1R
  qitem-20261021155543-cd413bc9, ST-1RR; proposal package
  docs/architecture/ST-1-PROPOSAL-2026-10-21.md (CANNOT-STATE, honored).
- Source slice: qitem-20261021155313-fe1742ceb (self-takeover brief).
- Operator rule: qitem-20261021160234-e304e6d8e1094b9a (proposal packages).
- Human authorization: operator session 2026-10-21 ("you can apply them").
- **Implementation: OPERATOR-EXECUTED, not seat-executed.** Three seats
  attempted ST-1 and handed back with verbatim fleet/* denials (no seat holds
  catalog write). The fleet specified the change (handbacks + proposal with
  ledger citations); the operator applied the exact hunks below, regenerated,
  verified, and commits. No seat edited, committed, or verified anything here.

## Applied hunks (fleet/fleet.yaml only, 3+/2-)

Hunk 1 — load-stress-tester seat mcp binding (B2-deferred one-line follow-up):
```
     mcp:
     - server: k6
     - server: codebase-memory
+    - server: grafana
```
Grafana appended last per B1 convention (analytics seat: codebase-memory,
clickhouse, grafana). Catalog entry verified present before editing:
fleet/mcp-servers.yaml `grafana: pin: oci:docker.io/grafana/mcp-grafana:2.0.2`.

Hunk 2 — sabotage-qa-tester ROLE block pi_packages (B2-deferred pending B1
render fix, which is merged on main):
```
-    - pi-lsp-extension@1.4.0
-    - pi-ast-grep@0.1.0
+    - '@narumitw/pi-lsp@0.49.10'
+    - '@nicknisi/pi-ast-grep@0.3.1'
```
Exact B1 quoted format. Edit scoped to the sabotage-qa-tester role block
(charter ref roles/sabotage-qa-tester/AGENTS.md in-block); the identical
legacy pin lines in ~19 other role blocks were NOT touched (out of ST-1
scope; each is a separate per-seat decision).

## Sabotage-qa-tester grafana binding decision: NOT BOUND (recorded)

ST-1 asked for a charter-checked decision either way. The deferred scope
(B2 ledger) named the load-stress-tester binding only; no charter need for a
sabotage grafana binding was demonstrated in any handback, and the sabotage
charter (mutation/sabotage testing, tests/chaos/* + docs/qa/*) shows no
dashboard-datasource requirement. Binding it would exceed the deferred
scope. If a need is demonstrated later, it is a new slice.

## Verification (operator-run; fleet bash-denies these tools)

- Regen: clean-tree-plus-own-edits regen with HERETEK_RIGS_ALLOW_DIRTY=1
  (dirt is exactly the two catalog hunks above; stated per AGENTS.md).
- Verify gate target: ./scripts/verify-rigs.sh --check-only → 22/0.
- Rendered proof targets: regenerated load-stress-tester runtime mcp.json
  carries grafana; sabotage-qa-tester rendered policy keeps 9 AST/LSP allows
  with 3 mutating tools denied (B1 render-fix behavior).
- Results recorded below after execution.

## Results (operator-executed 2026-10-21)

- Regen: `generate-rigs.py` with HERETEK_RIGS_ALLOW_DIRTY=1 (dirt was exactly
  the two catalog hunks) → "wrote 51 specialist AgentSpecs, 64 shared skills,
  8 RigBundles, Roster, and Registry views".
- Verify: `./scripts/verify-rigs.sh --check-only` → 22 checks passed, 0 failed.
- Rendered proof: load-stress-tester runtime mcp.json carries grafana entry
  byte-identical in shape to sre-incident-eng's (same docker-based command
  from B1's catalog design); sabotage-qa-tester rendered policy keeps 9/9
  AST/LSP allows with all 3 mutating tools denied.
- Deviation note: no agency-programmer/agency-qa/agency-drift-guard subagents
  were available in the operator session (tool guard rejected subagent calls
  for role "build"); the operator applied the hunks directly under explicit
  human authorization, with exact-match fail-closed editing, and verified via
  the automated gate + rendered greps. Human merge review remains the gate.
