ST-1P (ST-1 proposal package, operator-authorized rule 2026-10-21). Full spec: operator relay qitem-20261021160234-e304e6d8e1094b9a (held by TPM) plus docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-1.

Goal: author ONE proposal file in your writable scope (docs/architecture/ suggested name ST-1-PROPOSAL-2026-10-21.md) covering the two ST-1 hunks, per the operator format:
1. Target path plus exact hunk with 3-plus context lines, old and new quoted verbatim. Hunk A: grafana binding for load-stress-tester in fleet/fleet.yaml (B2 ledger one-line shape; load-tester handback qitem-20261021155527-46779bc3 premise). Hunk B: sabotage-qa-tester pi_packages pin swap, old pi-lsp-extension@1.4.0 and pi-ast-grep@0.1.0, new @narumitw/pi-lsp@0.49.10 and @nicknisi/pi-ast-grep@0.3.1 (B1 ledger section 2).
2. Evidence basis per hunk line (mirror path plus line, ledger section, merged commit). Mark UNVERIFIED anything not directly read. Never reconstruct catalog structure from memory.
3. State explicitly what you could NOT check (render output, verify gate, cross-seat impact).
4. If any hunk cannot be stated exactly, say which line and why instead. Approximate diffs will be rejected. A precise handback beats an approximate diff.

Constraints: write only inside your scope (docs/adr, docs/architecture); read-only elsewhere; no commits, pushes, merges; no secrets. Report the proposal path on this item when on disk, or the precise cannot-state verdict with reasons. Source slice: qitem-20261021155313-fe1742ceba05b628.
