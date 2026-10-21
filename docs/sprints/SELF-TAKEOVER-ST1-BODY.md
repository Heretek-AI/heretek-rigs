ST-1 (B1 follow-ups, now unblocked). Full spec: docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-1.

Goal: bind grafana MCP to load-stress-tester; bump sabotage-qa-tester pi_packages to scoped names. Verify merged main state first (grafana entry + render-seat.py scoped-name fix); if absent, hand back.

Steps: confirm fleet edit scope (hand back with verbatim denial if denied); bind grafana; bump pi-lsp-extension to @narumitw/pi-lsp@0.49.10 and pi-ast-grep to @nicknisi/pi-ast-grep@0.3.1; regen + verify-rigs.sh --check-only must read 22 passed 0 failed; write ledger docs/sprints/SELF-TAKEOVER-ST1.md; file commit-request queue item to OPERATOR (exact file list, verify output, sign-off request).

Constraints: no commit, push, merge; no hand-edited generated leaves; root AGENTS.md never touched. Source slice: qitem-20261021155313-fe1742ceba05b628.
