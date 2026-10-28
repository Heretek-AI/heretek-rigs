ST-1RR (B1 follow-ups, second reassignment). Full spec: docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-1. You hold the exact context: TOOLING-B1-RIG5.md shows you did this class of edit before (dependency-patcher pi_packages bump plus render-seat.py scoped-name fix).

Premise evidence (two fail-closed handbacks, no workarounds):
- qa-load-stress-tester handback qitem-20261021155527-46779bc3: B1 merged state present via generated mirrors (grafana mcp-grafana 2.0.2 with secret refs); render-seat.py scoped names at lines 314-317; load-stress-tester mcp.json lacks grafana (binding needed); sabotage-qa-tester policy-enforcement.json still has stale pins pi-lsp-extension 1.4.0 and pi-ast-grep 0.1.0 (bump needed).
- system-architect handback qitem-20261021155601-d0144464: fleet read denied in-seat, no edits made, steelman recommends a seat already holding fleet read plus write scope.

Goal: bind grafana MCP to load-stress-tester (check sabotage-qa-tester charter before deciding its binding, record decision either way); bump sabotage-qa-tester pi_packages to @narumitw/pi-lsp@0.49.10 and @nicknisi/pi-ast-grep@0.3.1 with rendered allows intact.

Steps: confirm fleet edit scope first (hand back with verbatim denial if denied, S02 precedent, no workaround); verify merged main state at source; edit; regen plus verify-rigs.sh --check-only must read 22 passed 0 failed; write ledger docs/sprints/SELF-TAKEOVER-ST1.md; file commit-request queue item to OPERATOR (exact file list, verify output, sign-off request).

Constraints: no commit, push, merge; no hand-edited generated leaves; root AGENTS.md never touched. Chain: qitem-20261021155438-17c7bd79e62951c9, qitem-20261021155527-46779bc3, qitem-20261021155543-cd413bc9, qitem-20261021155601-d0144464. Source slice: qitem-20261021155313-fe1742ceba05b628.
