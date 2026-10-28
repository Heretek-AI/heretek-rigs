ST-1R (B1 follow-ups, reassigned after scoped handback). Full spec: docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-1. Premise evidence from qa-load-stress-tester handback qitem-20261021155527-46779bc3:

- B1 merged state present via generated mirrors (grafana mcp-grafana 2.0.2 with GRAFANA_URL and GRAFANA_SERVICE_ACCOUNT_TOKEN secret refs).
- render-seat.py scoped names at lines 314-317.
- load-stress-tester runtime mcp.json carries only k6 plus codebase-memory, no grafana. Binding still needed.
- sabotage-qa-tester runtime policy-enforcement.json still carries stale pins pi-lsp-extension 1.4.0 and pi-ast-grep 0.1.0. Bump still needed.

Goal: bind grafana MCP to load-stress-tester (check sabotage-qa-tester charter before deciding its binding, record decision either way); bump sabotage-qa-tester pi_packages to @narumitw/pi-lsp@0.49.10 and @nicknisi/pi-ast-grep@0.3.1 with rendered allows intact.

Steps: confirm fleet edit scope first (hand back with verbatim denial if denied, S02 precedent); verify merged main state at source; edit; regen plus verify-rigs.sh --check-only must read 22 passed 0 failed; write ledger docs/sprints/SELF-TAKEOVER-ST1.md; file commit-request queue item to OPERATOR (exact file list, verify output, sign-off request).

Constraints: no commit, push, merge; no hand-edited generated leaves; root AGENTS.md never touched. Prior row: qitem-20261021155438-17c7bd79e62951c9. Source slice: qitem-20261021155313-fe1742ceba05b628.
