ST-6 (B6 MCP connectivity). Full spec: docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-6.

Goal: run pi mcp list on the host; report reachability for codebase-memory-mcp 0.12.1 and context7-mcp 4.4.2 (reachable / unreachable + error text, secrets redacted). Coordinate the 6 context7 consumers if needed.

Hard rule:BLOCKED on credentials means report it, never invent credentials, tokens, URLs, or secret files. No secret material in outputs, files, or command lines. Report verdicts on this item when done. Source slice: qitem-20261021155313-fe1742ceba05b628.
