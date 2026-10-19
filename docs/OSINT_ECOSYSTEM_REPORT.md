# OSINT Ecosystem Report: Heretek-Crew to `heretek-rigs` on OpenRig + Pi + OpenCode Go

Research date: 2026-10-18/19 (UTC). This unified report synthesizes the empirical runtime, security, and ecosystem findings from both candidate planning spikes (`claude/` and `gemini/`) along with zero-trust source audits of `@openrig/cli@0.6.11`, `@earendil-works/pi-coding-agent@1.3.0`, `@gotgenes/pi-permission-system@41.0.0`, `pi-lsp-extension@1.4.0`, `pi-ast-grep@0.1.0`, and `Heretek-AI/Heretek-Crew@5ffb1fc`.

It serves as the authoritative evidence base for:
- `fleet/fleet.yaml`: Canonical machine-readable catalog of all 51 roles with rig, pod, edges, policy, thinking level, skills, Pi packages, MCP bindings, and translated permission rules.
- `fleet/mcp-servers.yaml`: Pinned MCP server catalog with install command, verification status, exposure mode, and command-backed secret handling (`"!cat @SECRETS@/<file>"`).
- `docs/OPENRIG_MUSE_GO_ARCHITECTURE.md`: Ground-truth runtime and bundle architecture specification.
- `PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md`: Self-contained milestone implementation brief.
- `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` & `PROMPT_FLEET_AUDIT_REMEDIATION.md`: Three-subagent adversarial audit and fail-closed remediation prompts driven by `scripts/audit_loop.py`.

---

## 1. Inputs Inspected

| Source | Ref Inspected | What Was Taken From It |
|---|---|---|
| `Heretek-AI/Heretek-Crew` | `5ffb1fc` / `0b41346` (2026-10-18, zero diff in `roles/`) | 51 roles: `roles/<id>/AGENTS.md` charters (316 KB total), `roles/<id>/opencode/opencode.json` (model, MCP, `fs` and `shell` allows), `roles/<id>/.opencode/skills/*` (108 skill copies, 76 unique), `roles-catalog/ROLE_CATALOG_50.md`, `SUPPORTING_SERVICES.md`, `docker-compose.sidecars.yml` (1,025 lines, 7 profiles), `AUDIT_REPORT_FINDINGS.md` |
| `Heretek-AI/heretek-rigs` | `02f9c24` (`main`) | Target repository root (`LICENSE.md` with `PLACEHOLDER` preserved untouched) |
| `mvschwarz/openrig` (upstream) | `d4741c9` / `@openrig/cli@0.6.11` | Daemon sources (`pi-runtime-adapter.ts`, `pi-runner-protocol.ts`, `rigspec-schema.ts`, `agent-manifest.ts`), CLI bundler (`bundle-check.ts`, `specs.ts`, `policy.ts`), and 6 v1 JSON Schemas (`docs/reference/schemas/*.v1.schema.json` + `fixtures/identity-vectors.json`) |
| `@openrig/cli` on npm | `0.6.11` (`latest`; dist-tag `rc` = `0.6.4-rc.1`) | Installed and run. Binary is `rig` (`packages/cli/package.json:24-27`), `rig --version` prints `0.6.11 (379f0a0d)`, engines node `^22 \|\| ^24`, Apache-2.0 |
| `@earendil-works/pi-coding-agent` on npm | `1.3.0` (`@earendil-works/pi-ai@1.3.0`) | Installed and unpacked. Binary is `pi`, node `>=22.19.0`. Built-in `opencode-go` provider and `muse-spark-1.3-contributor` model verified in `dist/bundle/chunks/chunk-66G7ITPS.js`. Old `@mariozechner/pi-coding-agent` is deprecated |
| `@gotgenes/pi-permission-system` on npm | `41.0.0` (2026-10-17) | Unpacked and tested against Pi 1.3.0 (`src/access-intent/tool-kind.ts`, `src/policy/wildcard-matcher.ts`, `docs/configuration.md`) |
| `pi-lsp-extension` & `pi-ast-grep` on npm | `1.4.0` & `0.1.0` | Unpacked and audited registered `pi.registerTool(...)` names and file-mutation surfaces |
| Official MCP Registry, npm, PyPI, GitHub | Live queries (`2026-10-18/19`) | Verified package existence, versions, publish dates, licenses, and repository provenance |

---

## 2. Headline Findings (Read These First)

1. **OpenRig has no `opencode` runtime (`rig` is the CLI binary).** OpenRig's supported runtimes (`packages/daemon/src/domain/rigspec-schema.ts:12-20`) are `claude-code`, `codex`, `pi`, `omp`, `terminal`, and `stub`. The fleet runs on `runtime: pi`, with Pi 1.3.0's built-in `opencode-go` provider serving `opencode-go/muse-spark-1.3-contributor:high`. A rig spec with `runtime: opencode` passes `rig spec validate` (`{"valid":true}`) and only fails at `rig spec preflight` (`unsupported runtime "opencode"`).
2. **OpenRig strips `OPENCODE_API_KEY` from `runtime: pi` seats (`pi-runner-protocol.ts:111-117`).** The Pi child environment is a fixed allow-list (`PATH`, `HOME`, `USER`, `LOGNAME`, `TERM`, `LANG`, `LC_ALL`, `SHELL`, `TMPDIR`, `OPENRIG_*`, `PI_CODING_AGENT_DIR`, `PI_CODING_AGENT_SESSION_DIR`), and `PI_PROVIDER_ENV_VARS` forwards only `OPENROUTER_API_KEY`, `ZAI_API_KEY`, `KIMI_API_KEY`, and `MINIMAX_API_KEY` (`OMP_PROVIDER_ENV_VARS` at line 143 forwards `OPENCODE_API_KEY` for `runtime: omp`). The working, zero-leak solution is a per-seat `<agentDir>/auth.json` (mode `0600`) with a command-backed key: `{"opencode-go":{"type":"api_key","key":"!cat /abs/path/opencode-go.key"}}`.
3. **OpenRig records `permission_policy` for Pi but delegates runtime enforcement (`policy.ts:34-41`).** `builtin:yolo` maps to `--approve`; every other policy (`builtin:locked`, `builtin:standard`) maps to the floor, `--no-approve` (project `.pi/*` and `.agents/skills` are ignored). Real runtime enforcement requires `@gotgenes/pi-permission-system@41.0.0` configured per seat at `<agentDir>/extensions/pi-permission-system/config.json`. (By contrast, `@vtstech/pi-security@1.3.2` hardcodes `path.join(os.homedir(), ".pi", "agent", "security.json")` in `security.js:19-34`, ignoring `$PI_CODING_AGENT_DIR` completely.)
4. **`@gotgenes/pi-permission-system@41.0.0` does not normalize `..` in path rules.** With `path_write: {"*":"deny", "docs/*":"allow"}`, a `write` to `docs/../evil.md` succeeds and creates `evil.md` in the repo root because `wildcard-matcher.ts` matches glob strings before lexical `..` resolution. Adding `"*..*":"deny"` as the **last** rule in `path_write` and `path` (since last matching rule wins) blocks all `..` traversal attempts (`Denied by policy: 'path_write' ... (rule '*..*')`).
5. **Mutating extension tools (`code_rewrite`, `lsp_rename`, `lsp_code_actions`) bypass `path_write` unless denied by tool name.** In `@gotgenes/pi-permission-system@41.0.0` (`src/access-intent/tool-kind.ts:33-55`), only native `read`/`write`/`edit`/`grep`/`find`/`ls` are classified as `ToolKind = "path"` and checked against `path_write`. Extension tools (`classifyToolKind() === "extension"`) are checked only by tool name in the top-level `permission` map. Therefore, for roles loading `pi-lsp-extension@1.4.0` and `pi-ast-grep@0.1.0`, read-only AST/LSP tools (`ast_grep`, `ast_search`, `code_overview`, `lsp_diagnostics`, `lsp_hover`, `lsp_definition`, `lsp_references`, `lsp_symbols`, `lsp_completions`) are explicitly set to `"allow"`, while mutating extension tools (`code_rewrite`, `lsp_rename`, `lsp_code_actions`) are explicitly set to `"deny"` across all 51 seats so 100% of file writes go through native `write`/`edit` and are gated by `path_write` + `"*..*":"deny"`.
6. **`guidance_merge` collides when multiple seats share `<cwd>` (`pi-runtime-adapter.ts:442-503`).** OpenRig merges `guidance` resources (`merge: managed_block`) into `<cwd>/AGENTS.md` keyed by `blockId = entry.effectiveId` (`<!-- OPENRIG:BEGIN:role -->`), skipping only `if (blockId === "rig-role")`. Two seats sharing `cwd: "."` overwrite each other's role block. The fix is `uses.guidance: []` (and zero `guidance_merge` startup files), seeding each seat's charter directly into `<agentDir>/AGENTS.md`.
7. **`checkBundleFolder` (`bundle-check.ts:41-105`) forbids both external `../../` paths AND `openrig-home:` local plugin paths.** `bundle-check.ts:41` checks `fs.realpathSync` containment inside `rigs/<rig>/`, rejecting `agent_ref: "local:../../specs/agents/..."`. Furthermore, `bundle-check.ts:98` runs `fileRead(entry.source.path, dir)` whenever a plugin has `source.kind === "local"`, which causes `path: "openrig-home:plugins/openrig-core"` to fail with `"Declared file is missing, unreadable or outside the bundle folder"`. Materializing `rigs/<rig>/agents/_shared` and `rigs/<rig>/agents/<role>` (with `local:agents/<role>` and `local:../_shared`) and omitting `plugins` (which `PiRuntimeAdapter.projectEntry` at line 480 skips anyway) achieves `[]` (0 findings) on `rig bundle check` across all 8 rigs.
8. **Two Heretek-Crew MCP pins are unsafe/broken.** `r2mcp==0.2.5` on PyPI is an unrelated `"CLI para gestao de servidores MCP via rest2mcp gateway"`, not radare2 (replaced with `radareorg/radare2-mcp@1.9.0` with `-R` read-only flag). `aws-mcp@1.0.2` on npm has no repository and no release since 2025-01 (replaced with `awslabs.aws-api-mcp-server==1.5.6` with `READ_OPERATIONS_ONLY=true`).
9. **Heretek-Crew truncated 7 `obra/superpowers@bb92a77` skills.** Seven shared skills in `Heretek-Crew` kept only `SKILL.md` and dropped helper files (`systematic-debugging` has 11 files upstream vs 1 in `Heretek-Crew`). `heretek-rigs` vendors the full upstream directories from pinned git SHAs and locks their tree hashes in `fleet/skills-lock.json`.
10. **There are 51 roles, not 50.** `static-analysis-lead` (Role 37 in `Heretek-Crew`) and `ai-red-teamer` (Role 51) are both included in full (`static-analysis-lead` in `qa-and-verification-gauntlet`, `ai-red-teamer` in `defensive-sec-and-red-team`).

---

## 3. Runtime and Model Verification

| Item | Verified Value | Source / Evidence |
|---|---|---|
| Model ref (Pi store) | `opencode-go/muse-spark-1.3-contributor` ("Muse Spark 1.3 Contributor") | `@earendil-works/pi-coding-agent@1.3.0` `dist/bundle/chunks/chunk-66G7ITPS.js` |
| Spec model string | `opencode-go/muse-spark-1.3-contributor:high` | `splitThinkingSuffix` in `chunk-66G7ITPS.js` parses `:high` / `:xhigh` |
| API & Base URL | `openai-responses`, `https://opencode.ai/inference/go/v1` | Built-in `opencode-go` provider in Pi 1.3.0 |
| Context / Max Output | `1,048,576` / `131,072` tokens | Pi 1.3.0 provider table |
| Cost (per 1M tokens) | Input `$0.10`, Output `$0.20`, Cache Read `$0.002`, Cache Write `$0` | Pi 1.3.0 provider table |
| Thinking levels | `off`, `minimal`, `low`, `medium`, `high`, `xhigh` (`max` is `null` / unsupported) | `thinkingLevelMap` in `chunk-66G7ITPS.js` |
| Session affinity | `sessionAffinityFormat: "openai-nosession"` | `compat` block in `chunk-66G7ITPS.js` |
| Seat state directory | `$OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent` | `packages/daemon/src/adapters/pi-runtime-adapter.ts:115-128` |

---

## 4. Pi Packages (`pi-package` Ecosystem Rubric)

`npm search keywords:pi-package` reports **12,301** packages (2026-10-18). Each candidate was scored 0–3 on four pillars: **Maintenance/Provenance**, **OpenRig/Pi Ergonomics**, **Token Efficiency**, and **Security/Blast Radius**.

| Package | Version / License / Last Publish | Monthly DL | Prov. | Ergo. | Tokens | Security | Fleet Decision |
|---|---|---|---|---|---|---|---|
| `@gotgenes/pi-permission-system` | `41.0.0` / MIT / 2026-10-17 | 66,164 | 3 | 3 | 3 | 3 | **Adopt, every seat.** Fails closed, hides denied tools, gates `bash`/`path`/`path_write`/`mcp`/`skill`/`external_directory` with `"*..*":"deny"` guard |
| `pi-lsp-extension` | `1.4.0` / MIT / 2026-04 | — | 3 | 3 | 3 | 3 | **Adopt on 21 builder/code-analysis seats.** Registers read-only `lsp_diagnostics`, `lsp_hover`, `lsp_definition`, `lsp_references`, `lsp_symbols`, `lsp_completions`, `code_overview`, `ast_search` (allowed) and mutating `code_rewrite`, `lsp_rename`, `lsp_code_actions` (explicitly denied in `pi-permission-system` so all edits pass through `path_write`) |
| `pi-ast-grep` | `0.1.0` / MIT / 2026-03 | — | 2 | 3 | 3 | 3 | **Adopt on 21 builder/code-analysis seats.** Registers read-only `ast_grep` structural AST search tool |
| `pi-lsp` | `0.1.7` / MIT / 2026-03 | — | 2 | 1 | 2 | 2 | **Reject.** Registers the exact same 5 tool names (`lsp_diagnostics`, `lsp_hover`, `lsp_definition`, `lsp_references`, `lsp_symbols`) as `pi-lsp-extension@1.4.0`, causing duplicate registration collisions |
| `@vtstech/pi-security` | `1.3.2` / GPL-3.0 / 2026-02 | — | 2 | 0 | 3 | 1 | **Reject.** Hardcodes `~/.pi/agent/security.json` (`security.js:19-34`), ignoring `$PI_CODING_AGENT_DIR` |
| `pi-mcp-adapter` | `5.3.2` / MIT / 2026-10-17 | 1,561,819 | 3 | 1 | 2 | 2 | **Reject.** Redundant: Pi 1.3.0 has native built-in MCP (`<agentDir>/mcp.json`, verified via `pi mcp list --json`) |
| `pi-subagents` | `0.79.1` / MIT / 2026-10-18 | 583,251 | 3 | 1 | 2 | 1 | **Reject.** Delegation belongs to OpenRig (`rig queue`, `rig send`); `pi-subagents` opens an unaudited second delegation channel |
| `pi-web-access` | `0.42.0` / MIT / 2026-10-17 | 755,303 | 3 | 2 | 2 | 1 | **Reject.** Unscoped outbound web egress; web research seats use loopback SearXNG/Firecrawl sidecars |

### 4.1 `@gotgenes/pi-permission-system@41.0.0` Gate Probes Verified Against Mock Model

| Probe | Rule Set | Verified Result |
|---|---|---|
| `write src/evil.ts` | `path_write: {"*":"deny", ...}` | `[pi-permission-system] Denied by policy: 'path_write' for tool 'write' for path 'src/evil.ts' (rule '*').` |
| `write docs/security/advisories/SEC-1.md` | `"docs/security/advisories/*":"allow"` | `Successfully wrote to docs/security/advisories/SEC-1.md` |
| `write docs/../evil.md` | `"docs/*":"allow"` **without** `*..*` guard | **Allowed, file created in repo root (the `..` traversal bypass)** |
| `write docs/security/advisories/../../../evil.md` | `"*..*":"deny"` placed **last** in `path_write` | `Denied by policy: 'path_write' ... (rule '*..*')` |
| `write AGENTS.md` | `"AGENTS.md":"deny"` after role allows | `Denied by policy: 'path_write' ... (rule 'AGENTS.md')` |
| `read .env` / `read docs/../.env` | `path: {"*":"allow", "*.env":"deny", "*..*":"deny"}` | `Denied by policy: 'path_read' for tool 'read' ... (rule '*.env')` |
| `bash echo hi; touch pwned` | `bash: {"*":"deny", "echo *":"allow"}` | `Denied by policy: 'bash' (rule '*').` (compound commands decomposed) |
| `bash curl -s https://example.com` | Fleet `bash` allow-list | `Denied by policy: 'bash' (rule '*').` |
| `code_rewrite` / `lsp_rename` / `lsp_code_actions` | Top-level `"code_rewrite":"deny"` | Denied/hidden so extension tools cannot write files outside `path_write` |
| `tool_search` | `"tool_search":"allow"` (when deferred MCP bound) | `Loaded N tools. They are available from your next call: ...` |

---

## 5. MCP Server Catalog (`fleet/mcp-servers.yaml`)

Every Heretek-Crew MCP server was audited against npm, PyPI, and the official MCP registry:

| Heretek-Crew Pin | Audit Finding | Synthesized Fleet Decision (`fleet/mcp-servers.yaml`) |
|---|---|---|
| `npx -y codebase-memory-mcp@0.12.1` | Healthy (DeusData, MIT). Postinstall downloads release binary | Keep (`npm:codebase-memory-mcp@0.12.1`, `exposure: deferred`). **Connected** via `pi mcp list` (17 tools) |
| `npx -y @upstash/context7-mcp@4.4.2` | Healthy (MIT) | Keep (`npm:@upstash/context7-mcp@4.4.2`, `exposure: deferred`). **Connected** (2 tools) |
| `npx -y @cyanheads/git-mcp-server@2.15.3` | Healthy | Drop: read-only `git` commands via `pi-permission-system` `bash` allow-list save context tokens |
| `npx -y @modelcontextprotocol/server-github@2025.4.8` | **Deprecated on npm** | Replace with official remote `https://api.githubcopilot.com/mcp/x/{toolset}/readonly` with `"!echo Bearer $(cat @SECRETS@/github.pat)"` |
| `npx -y @modelcontextprotocol/server-memory@1.0.0` | Official, current | Keep (`npm:@modelcontextprotocol/server-memory@1.0.0`, `MEMORY_FILE_PATH: "@SEAT@/memory.jsonl"`, `exposure: direct`). **Connected** |
| `npx -y @executeautomation/playwright-mcp-server@1.0.12` | Unofficial third-party | Replace with Microsoft `npm:@playwright/mcp@0.0.83 --headless --isolated`. **Connected** (25 tools) |
| `npx -y chrome-devtools-mcp@1.11.0` | Healthy (Google, Apache-2.0) | Keep (`npm:chrome-devtools-mcp@1.11.0 --headless --isolated`). **Connected** (32 tools) |
| `npx -y @mobilenext/mobile-mcp@1.0.11` | One patch behind | Bump to `npm:@mobilenext/mobile-mcp@1.0.12`. **Connected** (34 tools) |
| `npx -y mcp-openapi-schema-explorer@1.3.5` | Healthy (MIT) | Keep (`npm:mcp-openapi-schema-explorer@1.3.5 openapi/openapi.yaml`, `exposure: direct`). **Connected** |
| `semgrep mcp --transport stdio` | Exists in `semgrep==1.181.0` | Keep (`uvx semgrep==1.181.0 mcp -t stdio`, `exposure: deferred`) |
| `uvx r2mcp==0.2.5` | **NOT radare2** (unrelated Portuguese `rest2mcp` gateway CLI on PyPI) | Replace with `git:https://github.com/radareorg/radare2-mcp@1.9.0` compiled to `@TOOLS@/bin/r2mcp` with `-R` (read-only mode) |
| `npx -y @modelcontextprotocol/server-filesystem@1.0.0` | Pointed at Paperclip-only `/paperclip/workspaces/binaries` | Drop: Pi's native `read`/`grep`/`find`/`ls` are already gated by `pi-permission-system` |
| `npx -y aws-mcp@1.0.2` | **No repository, ISC, last publish 2025-01** | Replace with `uvx awslabs.aws-api-mcp-server==1.5.6` with `READ_OPERATIONS_ONLY=true` |
| `uvx mcp-server-duckdb==1.1.0` | Stale (2025-05) | Replace with `uvx mcp-server-motherduck==1.1.0 --db-path :memory:` |
| `npx -y @modelcontextprotocol/server-postgres@0.6.2` | **Deprecated on npm** | Replace with `uvx postgres-mcp==0.3.0 --access-mode=restricted` (`DATABASE_URI: "!cat @SECRETS@/postgres-readonly.uri"`) |
| `uvx mcp-server-kubernetes==0.1.6` | Stale (2025-03) | Replace with `npm:kubernetes-mcp-server@0.0.67 --read-only` (fails closed without kubeconfig context) |
| `uvx docker-mcp==0.2.0` | Stale (2024-12), daemon-level access | Drop: use GET-only `tecnativa/docker-socket-proxy:0.5.0` sidecar and scoped bash allows |
| `uvx k6-mcp-server==2.2.0` | Exists on PyPI | Keep (`uvx k6-mcp-server==2.2.0`, `exposure: direct`) |
| `uvx mcp-server-qdrant==0.8.1` | Official (Apache-2.0) | Keep (`uvx mcp-server-qdrant==0.8.1`, `QDRANT_LOCAL_PATH: "@SEAT@/qdrant"`, `exposure: direct`) |
| Added telemetry/infra servers | Missing in legacy catalog | Added `prometheus-mcp-server==1.6.2`, `mcp-clickhouse==0.7.0` (`CLICKHOUSE_ALLOW_WRITE_ACCESS=false`), `redis-mcp-server==0.5.1`, and `hashicorp/terraform-mcp-server:1.0.0` |

---

## 6. Skills Provenance & `openrig-core` Loadout

| Source Repository | Pinned Commit / Version | License | Count & Usage |
|---|---|---|---|
| `@openrig/cli@0.6.11` (`daemon/assets/plugins/openrig-core/skills/`) | `0.6.11` | Apache-2.0 | 12 core SOP skills vendored into `specs/agents/_shared/skills/` (`openrig-operating-model`, `mission-slice-sop`, `delegating-work`, `queue-handoff`, `refocusing`, `seat-continuity-and-handover` on all 51 seats; plus `messaging-the-human`, `orienting-to-an-inherited-seat`, `session-compaction-and-restore` on all 15 pod leads; plus `openrig-user`, `forming-an-openrig-mental-model`, `agent-operated-workflows` on `exec-director` and `tpm-scrum-lead`) |
| `obra/superpowers` | `bb92a77` | MIT | 11 full skill directories (restoring supporting files truncated in `Heretek-Crew`, with root `LICENSE` copied into each skill directory) |
| `trailofbits/skills` | `5c99c03` | CC-BY-SA-4.0 | 22 security, static analysis, fuzzing, and property-testing skills (vendored unmodified with root `LICENSE` copied) |
| `getsentry/skills` | `f57ada2` | Apache-2.0 | 5 skills (`security-review`, `gha-security-review`, `skill-scanner`, `find-bugs`, `document-api-endpoint`) |
| `anthropics/skills` | `dbd4588` | Per-skill `LICENSE.txt` | 3 skills (`webapp-testing`, `frontend-design`, `doc-coauthoring`) |
| `vercel-labs/agent-skills` | `063bee9` | MIT | 2 skills (`web-design-guidelines`, `react-best-practices`) |
| `Heretek-AI/Heretek-Crew` (`roles/*/.opencode/skills`) | `5ffb1fc` | Per-file frontmatter | 7 shared non-superpowers skills + 62 role-local specialist skills |

Total shared skills in `specs/agents/_shared/skills/` (and locked in `fleet/skills-lock.json`): **62**.

---

## 7. Complete 51-Role Fleet Mapping & Permission Posture

All **16 read-only/docs-only roles** (`exec-director`, `product-director`, `system-architect`, `tpm-scrum-lead`, `git-drift-coord`, `tech-docs-lead`, `ux-research-analyst`, `sre-incident-eng`, `release-qa-officer`, `threat-modeler`, `appsec-engineer`, `cloud-sec-auditor`, `compliance-auditor`, `ai-red-teamer`, `binary-reverse-eng`, `firmware-sec-analyst`) plus the 2 QA gate/mutation roles (`static-analysis-lead`, `sabotage-qa-tester`) carry `permission_policy: builtin:locked` (**18 `builtin:locked` roles total**). The remaining 33 engineering/active-QA roles carry `permission_policy: builtin:standard`.

| # | Role ID | Static Rig / Pod | Lead | Policy | Thinking | Pi Packages | MCP Servers | Writable Globs (`path_write`) |
|---|---|---|---|---|---|---|---|---|
| 1 | `exec-director` | `executive-and-architecture` / `exec` | yes | `builtin:locked` | `xhigh` | `pi-permission-system` | `github(issues, ro)`, `memory` | `docs/executive/*` |
| 2 | `product-director` | `executive-and-architecture` / `exec` | no | `builtin:locked` | `high` | `pi-permission-system` | `github(issues, ro)`, `memory` | `docs/product/*` |
| 3 | `system-architect` | `executive-and-architecture` / `exec` | no | `builtin:locked` | `xhigh` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory`, `context7` | `docs/adr/*`, `docs/architecture/*` |
| 4 | `tpm-scrum-lead` | `executive-and-architecture` / `delivery` | yes | `builtin:locked` | `high` | `pi-permission-system` | `github(issues, ro)`, `memory` | `docs/sprints/*` |
| 5 | `git-drift-coord` | `executive-and-architecture` / `delivery` | no | `builtin:locked` | `high` | `pi-permission-system` | `codebase-memory` | `docs/ops/*` |
| 6 | `tech-docs-lead` | `executive-and-architecture` / `delivery` | no | `builtin:locked` | `high` | `pi-permission-system` | `codebase-memory` | `docs/*`, `docs/*.md` |
| 7 | `ts-node-fullstack` | `fullstack-and-web-studio` / `build` | yes | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory`, `context7` | `src/*`, `tests/*` |
| 8 | `python-backend-spec` | `fullstack-and-web-studio` / `build` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory`, `context7` | `src/*`, `tests/*`, `alembic/*` |
| 9 | `go-backend-eng` | `fullstack-and-web-studio` / `build` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory`, `context7` | `cmd/*`, `internal/*`, `pkg/*`, `go.mod`, `go.sum` |
| 10 | `java-kotlin-eng` | `fullstack-and-web-studio` / `build` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `src/main/*`, `src/test/*`, `build.gradle*`, `pom.xml` |
| 11 | `ui-ux-designer` | `fullstack-and-web-studio` / `design` | yes | `builtin:standard` | `high` | `pi-permission-system` | `chrome-devtools`, `playwright` | `src/components/*`, `docs/design/*` |
| 12 | `design-system-eng` | `fullstack-and-web-studio` / `design` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `chrome-devtools`, `codebase-memory` | `src/components/*`, `src/styles/*`, `tokens/*` |
| 13 | `fe-perf-eng` | `fullstack-and-web-studio` / `design` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `chrome-devtools`, `playwright` | `src/*`, `next.config.*`, `vite.config.*` |
| 14 | `a11y-specialist` | `fullstack-and-web-studio` / `design` | no | `builtin:standard` | `high` | `pi-permission-system` | `playwright`, `chrome-devtools` | `tests/a11y/*`, `docs/a11y/*` |
| 15 | `mobile-web-eng` | `fullstack-and-web-studio` / `design` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `chrome-devtools`, `playwright` | `src/components/*`, `src/styles/*`, `public/manifest.json` |
| 16 | `brand-copy-spec` | `fullstack-and-web-studio` / `design` | no | `builtin:standard` | `high` | `pi-permission-system` | none | `locales/*`, `docs/copy/*` |
| 17 | `ux-research-analyst` | `fullstack-and-web-studio` / `design` | no | `builtin:locked` | `high` | `pi-permission-system` | `duckdb`, `github(issues, ro)` | `docs/research/*` |
| 18 | `rust-systems-spec` | `systems-and-mobile-foundry` / `systems` | yes | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory`, `context7` | `crates/*`, `src/*`, `benches/*`, `Cargo.toml`, `Cargo.lock` |
| 19 | `cpp-lowlevel-eng` | `systems-and-mobile-foundry` / `systems` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `src/*`, `include/*`, `tests/*`, `CMakeLists.txt` |
| 20 | `android-mobile-spec` | `systems-and-mobile-foundry` / `mobile` | yes | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `mobile`, `codebase-memory` | `android/*`, `app/src/*`, `build.gradle.kts`, `settings.gradle.kts` |
| 21 | `ios-mobile-spec` | `systems-and-mobile-foundry` / `mobile` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `ios/*`, `Sources/*`, `Tests/*`, `Package.swift` |
| 22 | `engine-systems-eng` | `game-dev-and-sim-rig` / `engine` | yes | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `engine/*`, `src/engine/*` |
| 23 | `physics-sim-eng` | `game-dev-and-sim-rig` / `engine` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `physics/*`, `src/physics/*` |
| 24 | `graphics-shader-eng` | `game-dev-and-sim-rig` / `engine` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `shaders/*`, `src/render/*` |
| 25 | `game-systems-dev` | `game-dev-and-sim-rig` / `gameplay` | yes | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `gameplay/*`, `src/gameplay/*` |
| 26 | `game-ai-dev` | `game-dev-and-sim-rig` / `gameplay` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `ai/*`, `src/ai/*` |
| 27 | `tech-artist-pipeline` | `game-dev-and-sim-rig` / `gameplay` | no | `builtin:standard` | `high` | `pi-permission-system` | none | `assets/*`, `tools/asset-pipeline/*` |
| 28 | `cloud-platform-eng` | `cloud-sre-and-data-platform` / `platform` | yes | `builtin:standard` | `high` | `pi-permission-system` | `aws`, `codebase-memory`, `terraform` | `infra/terraform/*`, `infra/opentofu/*` |
| 29 | `k8s-orchestrator` | `cloud-sre-and-data-platform` / `platform` | no | `builtin:standard` | `high` | `pi-permission-system` | `kubernetes` | `k8s/*`, `charts/*` |
| 30 | `dependency-patcher` | `cloud-sre-and-data-platform` / `platform` | no | `builtin:standard` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `uv.lock`, `Cargo.toml`, `Cargo.lock`, `go.mod`, `go.sum` |
| 31 | `sre-incident-eng` | `cloud-sre-and-data-platform` / `sre` | yes | `builtin:locked` | `high` | `pi-permission-system` | `prometheus` | `docs/incidents/*`, `docs/runbooks/*` |
| 32 | `observability-eng` | `cloud-sre-and-data-platform` / `sre` | no | `builtin:standard` | `high` | `pi-permission-system` | `codebase-memory`, `prometheus` | `monitoring/*`, `otel/*`, `dashboards/*` |
| 33 | `dba-specialist` | `cloud-sre-and-data-platform` / `data` | yes | `builtin:standard` | `high` | `pi-permission-system` | `postgres`, `codebase-memory` | `migrations/*`, `sql/*` |
| 34 | `cache-streaming-eng` | `cloud-sre-and-data-platform` / `data` | no | `builtin:standard` | `high` | `pi-permission-system` | `redis` | `src/cache/*`, `src/streaming/*`, `config/redis/*` |
| 35 | `data-pipeline-eng` | `cloud-sre-and-data-platform` / `data` | no | `builtin:standard` | `high` | `pi-permission-system` | `duckdb`, `codebase-memory` | `pipelines/*`, `dbt/*` |
| 36 | `analytics-metrics-eng` | `cloud-sre-and-data-platform` / `data` | no | `builtin:standard` | `high` | `pi-permission-system` | `codebase-memory`, `clickhouse` | `analytics/*`, `sql/clickhouse/*` |
| 37 | `mlops-serving-eng` | `cloud-sre-and-data-platform` / `ml` | yes | `builtin:standard` | `high` | `pi-permission-system` | none | `serving/*`, `benchmarks/llm/*` |
| 38 | `vector-rag-spec` | `cloud-sre-and-data-platform` / `ml` | no | `builtin:standard` | `high` | `pi-permission-system` | `qdrant`, `codebase-memory` | `rag/*`, `evals/rag/*` |
| 39 | `release-qa-officer` | `qa-and-verification-gauntlet` / `qa` | yes | `builtin:locked` | `high` | `pi-permission-system` | `github(pull_requests, ro)` | `docs/releases/*` |
| 40 | `e2e-browser-qa` | `qa-and-verification-gauntlet` / `qa` | no | `builtin:standard` | `high` | `pi-permission-system` | `playwright`, `chrome-devtools` | `tests/e2e/*`, `playwright.config.*` |
| 41 | `api-contract-tester` | `qa-and-verification-gauntlet` / `qa` | no | `builtin:standard` | `high` | `pi-permission-system` | `openapi` | `tests/contract/*`, `openapi/*` |
| 42 | `load-stress-tester` | `qa-and-verification-gauntlet` / `qa` | no | `builtin:standard` | `high` | `pi-permission-system` | `k6`, `codebase-memory` | `tests/load/*`, `k6/*` |
| 43 | `sabotage-qa-tester` | `qa-and-verification-gauntlet` / `qa` | no | `builtin:locked` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `codebase-memory` | `tests/chaos/*`, `docs/qa/*` |
| 44 | `static-analysis-lead` | `qa-and-verification-gauntlet` / `qa` | no | `builtin:locked` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `semgrep`, `codebase-memory` | `*.eslintrc.json`, `*eslint.config.js`, `rules/*`, `biome.json`, `ruff.toml` |
| 45 | `threat-modeler` | `defensive-sec-and-red-team` / `blue` | yes | `builtin:locked` | `xhigh` | `pi-permission-system` | `codebase-memory`, `github(repos, ro)` | `docs/security/threat-models/*` |
| 46 | `appsec-engineer` | `defensive-sec-and-red-team` / `blue` | no | `builtin:locked` | `high` | `pi-permission-system`, `pi-lsp-extension`, `pi-ast-grep` | `semgrep`, `codebase-memory` | `docs/security/advisories/*` |
| 47 | `cloud-sec-auditor` | `defensive-sec-and-red-team` / `blue` | no | `builtin:locked` | `high` | `pi-permission-system` | `aws`, `codebase-memory` | `docs/security/cloud/*` |
| 48 | `compliance-auditor` | `defensive-sec-and-red-team` / `blue` | no | `builtin:locked` | `high` | `pi-permission-system` | `github(repos, ro)` | `sbom/*`, `docs/compliance/*` |
| 49 | `ai-red-teamer` | `defensive-sec-and-red-team` / `red` | yes | `builtin:locked` | `xhigh` | `pi-permission-system` | `codebase-memory`, `context7` | `docs/security/ai-redteam/*` |
| 50 | `binary-reverse-eng` | `defensive-sec-and-red-team` / `red` | no | `builtin:locked` | `xhigh` | `pi-permission-system` | `radare2` | `docs/protocols/*`, `docs/forensics/*` |
| 51 | `firmware-sec-analyst` | `defensive-sec-and-red-team` / `red` | no | `builtin:locked` | `high` | `pi-permission-system` | `radare2` | `docs/security/firmware/*` |

---

## 8. Multi-Profile Sidecar Architecture (`docker-compose.sidecars.yml`)

Ported from `Heretek-Crew/docker-compose.sidecars.yml` with 7 opt-in profiles, loopback-only host binds (`127.0.0.1:`), digest/version pins (zero `:latest`), fail-closed `:?` secret guards, and isolated bridge networks:

| Profile | Services | Network Isolation & Hardening |
|---|---|---|
| `web-research` | `searxng`, `searxng-redis`, `firecrawl`, `firecrawl-redis`, `firecrawl-rabbitmq`, `firecrawl-nuq-postgres`, `firecrawl-playwright`, `browserless` | `heretek` bridge; `127.0.0.1:8888`, `127.0.0.1:3002`, `127.0.0.1:3000`; `firecrawl` healthcheck probes `/e2e-test` |
| `qa-testing` | `piston`, `mailpit`, `mitmproxy`, `localstack`, `wiremock`, `act-runner`, `docker-socket-proxy` | `docker-socket-proxy` (`tecnativa/docker-socket-proxy:0.5.0`) mounts `/var/run/docker.sock:ro` with `POST=0`, `BUILD=0`, `EXEC=0`, `VOLUMES=0`, `NETWORKS=0`, `AUTH=0` |
| `devsec` | `ghidra`, `radare2`, `sonarqube`, `sonarqube-db` | `ghidra` and `radare2` isolated on `heretek-devsec` bridge with `./workspaces/binaries:/samples:ro` |
| `observability` | `victoria-metrics`, `grafana`, `loki`, `tempo`, `otel-collector` | Loopback-only telemetry ports |
| `ai-gateway` | `qdrant`, `neo4j`, `litellm`, `ollama`, `minio` | Authenticated via `:?` fail-closed guards in `.env` |
| `mobile` | `docker-android` | Isolated on `heretek-mobile` bridge; `Makefile` `guard-profiles` refuses to co-schedule `mobile` with `devsec` or `web-research` |
