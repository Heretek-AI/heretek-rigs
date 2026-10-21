# ST-6 MCP connectivity verdicts — system-architect — 2026-10-21

Slice qitem: qitem-20261021155442-a0f1ad71ff31fde0
Source slice: qitem-20261021155313-fe1742ceba05b628
Spec: docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-6
Seat: exec-system-architect@heretek-omni-fleet

## 1. pi mcp list — BLOCKED by seat policy

Command run bare, single command per bash call, no chaining, retried twice this turn:

  pi mcp list

Denial verbatim, both attempts:

  [pi-permission-system] Denied by policy: 'bash' (rule '*').

Per charter, checked the permission review log path
extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl
via read this turn — result:

  ENOENT: no such file or directory

So matchedPattern is quoted from the denial text only: rule '*'.

Classification: this blocks the pi-mcp-list CLI probe only. It is not a
capability-wide MCP ban: both MCP servers proved reachable via live tool
invocations below with no secrets involved. Denials are non-sticky; rig
queue commands in the same turn succeeded.

Note: a later queue handoff-and-complete carrying the verbatim denial inline
was itself denied with rule '*)*' — parentheses in the inline note tripped the
terminal-syntax guard. This file carries the verbatim text instead; the handoff
references it via --body-file to avoid inline shell-metachar corruption.

## 2. codebase-memory — REACHABLE via live tool call

- tool_search for codebase-memory MCP connectivity loaded 8 tools.
- Invoked mcp__codebase_memory__list_projects with detail identity, limit 5.
- Result: 5 rows returned, total 192, has_more true. Sample names are
  environment plugin/cache paths under home directories, redacted to counts here.
- No credentials invented, no secret material in inputs, outputs, or command lines.
- Pin 0.12.1 UNVERIFIED: version cannot be confirmed without pi mcp list;
  reachability only is proven.

## 3. context7 — REACHABLE via live tool call

- tool_search for context7 documentation lookup loaded 2 tools.
- Invoked mcp__context7__resolve_library_id with libraryName Next.js,
  query routing.
- Result: 5 libraries returned, including /vercel/next.js with High source
  reputation and Benchmark Score 77.43, plus /websites/nextjs and others.
- No credentials invented, no secret material in inputs, outputs, or command lines.
- Pin 4.4.2 UNVERIFIED: version cannot be confirmed without pi mcp list;
  reachability only is proven.

## 4. Catalog pins — UNVERIFIED at source

Attempted catalog re-verification at source per sprint scope note:

- grep over fleet/mcp-servers.yaml for codebase-memory|context7 denied:

  [pi-permission-system] Denied by policy: 'path_read' for tool 'grep' for path 'fleet/mcp-servers.yaml' (rule 'fleet/*').

- read of fleet/mcp-servers.yaml denied:

  [pi-permission-system] Denied by policy: 'path_read' for tool 'read' for path 'fleet/mcp-servers.yaml' (rule 'fleet/*').

So pins codebase-memory-mcp 0.12.1 and context7-mcp 4.4.2 are UNVERIFIED
from this seat. No workaround attempted; hand-off per S02 precedent.

## 5. Six context7 consumers — no coordination needed

Direct live calls to both MCP servers succeeded, so no consumer-side
coordination was required this turn. No consumer errors were reported to
this seat. ST-3 blast-radius work remains reserved per the sprint plan.

## 6. Scope notes

- Optional DoD file docs/sprints/SELF-TAKEOVER-ST6.md NOT written: outside
  architect writable scope, which is confined to docs/adr/* and
  docs/architecture/*. This verdict file lives under docs/architecture/ as
  the durable artifact instead; no sprint file touched.
- No secrets appear in any output, file, or command line in this slice.
- Acceptance: both servers report a reachability verdict with evidence above;
  pi mcp list could not run in-seat and is reported BLOCKED with verbatim
  evidence rather than worked around.
