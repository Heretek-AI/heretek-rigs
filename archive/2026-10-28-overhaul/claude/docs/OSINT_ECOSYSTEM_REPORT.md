# OSINT Ecosystem Report: Heretek-Crew to heretek-rigs on openrig

Research date: 2026-10-18/19 (UTC). This report was written by the planning session and is the evidence base for
`docs/IMPLEMENTATION_PROMPT.md` (the build brief) and `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` (the audit). Every
version, flag and behaviour below was checked by running the tool or reading its published artefact. Anything that
could not be checked is listed in section 9.

Machine-readable outputs that go with this report:

- `fleet/fleet.yaml`: all 51 roles with rig, pod, edges, policy, thinking level, skills, MCP bindings and the
  translated permission rules.
- `fleet/mcp-servers.yaml`: the pinned MCP server catalog with install command, status and secret handling.

## 1. Inputs inspected

| Source | Ref inspected | What was taken from it |
|---|---|---|
| Heretek-AI/Heretek-Crew | `5ffb1fc` (2026-10-18) | 51 roles: `roles/<id>/AGENTS.md` charters (316 KB total), `roles/<id>/opencode/opencode.json` (model, MCP, fs and shell allows), `roles/<id>/.opencode/skills/*` (108 skill copies, 76 unique), `roles-catalog/ROLE_CATALOG_50.md`, `SUPPORTING_SERVICES.md`, `docker-compose.sidecars.yml`, `AUDIT_REPORT_FINDINGS.md` |
| Heretek-AI/heretek-rigs | `02f9c24` (main) | Only `LICENSE.md`, whose whole content is the word `PLACEHOLDER` |
| Heretek-AI/openrig (fork) | `0376204` | 10 commits behind upstream `d4741c9`, 0 ahead. Read daemon sources for the Pi adapter, rig-spec and agent-spec validators |
| mvschwarz/openrig (upstream) | `d4741c9` | Same, plus `specs/agents`, rig/agent/bundle docs |
| `@openrig/cli` on npm | `0.6.11` (latest; dist-tag `rc` = `0.6.4-rc.1`) | Installed and run. Binary is `rig`, `rig --version` prints `0.6.11 (379f0a0d)`, engines node `^22 \|\| ^24`, Apache-2.0 |
| `@earendil-works/pi-coding-agent` on npm | `1.3.0` | Installed and run. Binary is `pi`, node `>=22.19.0`. The old `@mariozechner/pi-coding-agent` is deprecated |
| Official MCP registry | `https://registry.modelcontextprotocol.io/v0.1/servers?search=<x>&version=latest` | Server names, versions, package identifiers |
| npm, PyPI, GitHub | registry JSON, `git ls-remote` | Versions, publish dates, licences, repositories |

## 2. Headline findings (read these first)

1. **openrig has no OpenCode runtime.** Its runtimes are `claude-code`, `codex`, `pi`, `omp`, `terminal` and
   `stub`. The fleet therefore runs on `runtime: pi`, with Pi's own `opencode-go` provider serving
   `opencode-go/muse-spark-1.3-contributor`. A rig spec with `runtime: opencode` passes `rig spec validate`
   (`{"valid":true}`) and only fails at `rig spec preflight` (`a.x: unsupported runtime "opencode"`).
2. **openrig does not forward `OPENCODE_API_KEY` to Pi seats.** The Pi child environment is a fixed allow-list
   (PATH, HOME, USER, LOGNAME, TERM, LANG, LC_ALL, SHELL, TMPDIR, some `OPENRIG_*`, `PI_CODING_AGENT_DIR`,
   `PI_CODING_AGENT_SESSION_DIR`), and `PI_PROVIDER_ENV_VARS` names only openrouter, zai, kimi-coding and minimax.
   The working answer is a per-seat `auth.json` with a command-backed key:
   `{"opencode-go":{"type":"api_key","key":"!cat /abs/path/opencode-go.key"}}`. `pi auth check` reports `ready`,
   and openrig preflight states "Credentials are checked for the managed seat before Pi starts".
3. **openrig records `permission_policy` for Pi but enforces nothing.** `builtin:yolo` maps to `--approve`. Every
   other policy, and no policy at all, maps to the floor, `--no-approve` (project `.pi/*` and `.agents/skills` are
   ignored). Real enforcement comes from the Pi package `@gotgenes/pi-permission-system@41.0.0`, configured per seat.
4. **`pi-permission-system` 41.0.0 does not normalise `..` in path rules.** With `path_write: {"*":"deny",
   "docs/*":"allow"}`, a `write` to `docs/../evil.md` succeeded and created `evil.md` in the repo root. Adding
   `"*..*":"deny"` as the last `path_write` rule denied it (`Denied by policy: 'path_write' ... (rule '*..*')`), and
   the same rule also denied an `edit` of `docs/../.git/config`. Every seat config must end with that rule.
5. **`guidance_merge` collides when seats share a cwd.** openrig writes a managed block named after the file
   (`guidance/role.md`) into `<cwd>/AGENTS.md`. Two seats in one cwd overwrite each other's block, and the second
   seat silently received the first seat's role. The fix is a per-seat charter in `<agentDir>/AGENTS.md` (Pi loads
   it into the system prompt; verified) and no `guidance_merge` file at all.
6. **Plugins are not projected for Pi.** `plugins: [shared:openrig-core]` gives a Pi seat nothing. The six core
   skills the fleet needs must be vendored as declared skill resources. Source: the 19 skills shipped inside the
   `@openrig/cli@0.6.11` tarball at `daemon/assets/plugins/openrig-core/skills/` (Apache-2.0).
7. **Two Heretek-Crew MCP pins are not what they claim.** `r2mcp==0.2.5` on PyPI is an unrelated "CLI para gestao
   de servidores MCP via rest2mcp gateway", not radare2. `aws-mcp@1.0.2` on npm has no repository, an ISC licence
   and no release since 2025-01. Both are replaced (section 5).
8. **Heretek-Crew truncated the superpowers skills.** Seven shared skills are byte-identical copies of
   `obra/superpowers@bb92a77` `SKILL.md` files, but the supporting files were dropped (for example
   `systematic-debugging` has 11 files upstream and 1 in Heretek-Crew). The fleet vendors the full directories.
9. **There are 51 roles, not 50.** The rig list in the request omits `static-analysis-lead`; it is placed in the QA
   gauntlet rig.

## 3. Runtime and model

| Item | Value | Evidence |
|---|---|---|
| Model ref | `opencode-go/muse-spark-1.3-contributor` ("Muse Spark 1.3 Contributor") | `pi` models store |
| API | `openai-responses`, base URL `https://opencode.ai/inference/go/v1` | Pi provider table |
| Context / output | 1,048,576 / 131,072 tokens | Pi provider table |
| Cost (per Pi table) | input 0.1, output 0.2 | Pi provider table |
| Thinking levels | off, minimal, low, medium, high, xhigh. `max` is `null` (unsupported) | `thinkingLevelMap` |
| Key variable | `OPENCODE_API_KEY` (shared by OpenCode Zen and Go) | Pi provider docs |
| Prior evidence | Heretek-Crew `docs/reports/first-agent-run-evidence.md` shows a successful run on this exact model id | Heretek-Crew repo |
| Live inference here | Not possible: `opencode.ai` returns proxy 403 from the planning container | section 9 |

Seat wiring that was run end to end with a live openrig daemon (`rig daemon start --no-kernel`):

- `defaults.runtime: pi` and `defaults.model` in `agent.yaml` are inherited by members that set neither. The
  launched runner process carried `--model opencode-go/muse-spark-1.3-contributor` and `--no-approve`
  (`profile-resolver.ts`: `member.model ?? profile.preferences.model ?? spec.defaults.model`).
- Pi seat state lives at `$OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent` (`OPENRIG_HOME` defaults to
  `~/.openrig`). Files written there before `rig up` (`auth.json`, `settings.json`, `mcp.json`, `AGENTS.md`,
  `extensions/pi-permission-system/config.json`) survive launch and `rig down` / `rig up <rig> --existing`.
- openrig writes `models-store.json` and projects declared skills into `agent/skills/<id>`: shared skills as
  `heretek-shared:<id>`, a role's own skills as bare `<id>`.
- `settings.json` keys used: `defaultProvider`, `defaultModel`, `defaultThinkingLevel`, `defaultTools`, `packages`,
  `quietStartup`. `defaultTools` restricts the declared tool list (verified in the system prompt `tools` section).
- Dynamic scaling works: `rig expand <rig> <pod.yaml> --rig-root <ABS>` and `rig add <rig> <pod> <member.yaml>
  --rig-root <ABS>`. A relative `--rig-root .` resolves against the daemon's cwd, not the shell's.

## 4. Pi packages (pi-package ecosystem)

`npm search keywords:pi-package` reports **12,301** packages (2026-10-18). Searches were run for mcp, permission,
guard, sandbox, secret, lsp, lint, ast-grep, tree-sitter, compaction, semgrep and openrig. Monthly downloads are from
the npm search API.

### Rubric

Each candidate is scored 0 to 3 on four pillars. **Maintenance/provenance:** named repo, licence, release in the last
30 days, download base. **openrig/pi ergonomics:** works under `--no-approve` from the agent dir, no TUI dependency,
no overlap with what openrig already does. **Token efficiency:** what it adds to every prompt. **Security/blast
radius:** what it can reach, mapped to the seat posture (locked = auditors and red team, standard = builders).

| Package | Version / licence / last publish | Monthly dl | Prov. | Ergo. | Tokens | Security | Decision |
|---|---|---|---|---|---|---|---|
| `@gotgenes/pi-permission-system` | 41.0.0 / MIT / 2026-10-17 | 66,164 | 3 | 3 | 3 | 3 | **Adopt, every seat.** Fails closed, hides denied tools, gates bash/path/mcp/skill/external_directory. Verified gates listed in 4.1 |
| `pi-mcp-adapter` | 5.3.2 / MIT / 2026-10-17 | 1,561,819 | 3 | 1 | 2 | 2 | Reject. Pi 1.3.0 has built-in MCP (`<agentDir>/mcp.json`, verified) |
| `pi-subagents` | 0.79.1 / MIT / 2026-10-18 | 583,251 | 3 | 1 | 2 | 1 | Reject. Delegation is openrig's job (queues, `rig send`); subagents add an unaudited second delegation path |
| `pi-web-access` | 0.42.0 / MIT / 2026-10-17 | 755,303 | 3 | 2 | 2 | 1 | Reject for now: open web egress for every seat. Revisit for `ux-research-analyst` only |
| `pi-lens` | 4.4.3 / MIT / 2026-10-11 | 93,795 | 3 | 2 | 2 | 2 | Candidate for builders, evaluated in a late optional milestone; runs language servers and linters |
| `@narumitw/pi-lsp` | 0.49.10 / MIT / 2026-10-15 | 10,817 | 2 | 2 | 2 | 2 | Alternative to pi-lens; not both |
| `@nicknisi/pi-ast-grep` | 0.3.1 / MIT / 2026-10-18 | 457 | 1 | 2 | 3 | 2 | Watch; too young |
| `pi-hashline-readmap` | 0.16.1 / MIT / 2026-10-14 | 1,632 | 2 | 2 | 3 | 3 | Watch |
| `@erichll/pi-sandbox` | 0.27.0 / Apache-2.0 / 2026-10-18 | 3,927 | 2 | 1 | 3 | 3 | Watch for the red-team pod (bwrap/Seatbelt); not spiked |
| `pi-permission-modes` | 2.4.3 / MIT / 2026-10-18 | 1,885 | 2 | 1 | 3 | 2 | Reject: overlaps pi-permission-system |
| `cc-safety-net` | 2.6.14 / MIT / 2026-10-18 | 54,328 | 3 | 2 | 3 | 2 | Reject: overlaps the bash gate |
| `@casualjim/pi-heimdall` | 0.3.16 / MIT / 2026-10-18 | 2,384 | 1 | 2 | 3 | 2 | Watch (secret scanning of tool output) |
| `pi-cache-optimizer` | 2.10.2 / MIT / 2026-10-18 | n/a | 2 | 2 | 3 | 3 | Watch; measure before adopting |
| `@langfuse/pi-observability-plugin` | 0.1.2 / MIT / 2026-08-31 | 323,802 | 3 | 2 | 3 | 1 | Defer: ships transcripts to a Langfuse server |
| `pi-otel` | 0.3.0 / Apache-2.0 / 2026-09-13 | n/a | 2 | 2 | 3 | 2 | Defer, same reason |
| `@juicesharp/rpiv-todo` | 2.13.9 | 179,266 | 2 | 2 | 2 | 3 | Reject: openrig queues already carry the work list |

### 4.1 pi-permission-system behaviour verified with a mock model

A deterministic OpenAI-compatible mock (`scripts/mock-openai.mjs` in the brief) made Pi call exactly one tool with
fixed arguments, under `pi --no-session --no-approve --mode json -p go` with the package loaded from a local path.

| Probe | Result |
|---|---|
| `bash rm -rf` outside the cwd | Denied (`external_directory`) |
| `bash echo hi`, `bash git status` | Allowed (`"echo *"`, `"git status*"`) |
| `bash echo hi; touch pwned` | Denied (`bash` rule `*`); no file created |
| `bash echo $(cat .env)` | Denied |
| `bash` redirect into `src/x.ts` | Denied (`path_write`) |
| `bash curl ...` | Denied (`bash` rule `*`) |
| `write src/evil.ts` | Denied (`path_write`) |
| `write docs/security/advisories/SEC-1.md` | Allowed |
| `write docs/a/b.md` with `docs/*` | Allowed: `*` crosses `/` |
| `write <abs cwd>/docs/abs.md` | Allowed: absolute paths are matched relative to the cwd |
| `write docs/../evil.md` | **Allowed without a guard; file created.** Denied once `"*..*":"deny"` is the last `path_write` rule |
| `write docs/../../escape.md` | Denied by the `*..*` rule |
| `read docs/../.env` | Denied (`path_read`, rule `*.env`) |
| `edit docs/../.git/config` | Denied by the `*..*` rule |
| `read <agentDir>/skills/demo-skill/SKILL.md` with `external_directory: deny` | Allowed: skill loading still works |
| `tool_search` with top-level `"*":"deny"` | `Tool tool_search not found`. Works once `"tool_search":"allow"` is set |
| `mcp__memdirect__read_graph` (exposure `direct`, `mcp: {"*":"deny","memdirect":"allow"}`) | Allowed, returned the graph |
| `mcp__memory__read_graph` (server not in the `mcp` allow map) | `Tool ... not found` (hidden) |

Config facts from the package docs (`docs/configuration.md`): within a surface map the **last matching rule wins**;
a parse failure falls back to `ask` for every category; `promptTimeoutMs` turns an unanswered prompt into a deny;
the `mcp` surface matches `server`, `server:tool`, `server_tool` and `mcp__<server>__<tool>`.

## 5. MCP servers

Every Heretek-Crew MCP pin was checked against npm/PyPI and the official registry. Full install details, exposure and
secret handling are in `fleet/mcp-servers.yaml`.

| Heretek-Crew pin | Finding | Fleet decision |
|---|---|---|
| `npx -y codebase-memory-mcp@0.12.1` | Healthy (DeusData, MIT, in registry). Postinstall downloads a release binary | Keep; installed into a shared prefix. **Connected** via `pi mcp list` (17 tools) |
| `npx -y @upstash/context7-mcp@4.4.2` | Healthy | Keep. **Connected** (2 tools) |
| `npx -y @cyanheads/git-mcp-server@2.15.3` | Healthy | Drop: read-only git through the gated bash allow-list costs fewer tokens |
| `npx -y @modelcontextprotocol/server-github@2025.4.8` | **Deprecated on npm** | Replace with the official remote `https://api.githubcopilot.com/mcp/x/<toolset>/readonly` |
| `npx -y @modelcontextprotocol/server-memory@1.0.0` | Official, current | Keep for coordinators. **Connected**, tool call verified |
| `npx -y @executeautomation/playwright-mcp-server@1.0.12` | Third-party | Replace with Microsoft `@playwright/mcp@0.0.83`. **Connected** (25 tools) |
| `npx -y chrome-devtools-mcp@1.11.0` | Healthy (Google, Apache-2.0) | Keep. **Connected** (32 tools) |
| `npx -y @mobilenext/mobile-mcp@1.0.11` | One release behind | Bump to 1.0.12. **Connected** (34 tools) |
| `npx -y mcp-openapi-schema-explorer@1.3.5` | Healthy | Keep. **Connected**, but exposes resources only (0 tools); see section 9 |
| `semgrep mcp --transport stdio` | Exists in `semgrep==1.181.0` | Keep. Startup calls `https://semgrep.dev/api/auth/oauth2/...`; failed here behind the proxy |
| `uvx r2mcp==0.2.5` | **Not radare2** (unrelated PyPI package) | Replace with `radareorg/radare2-mcp` via `r2pm -Uci r2mcp`, run `r2pm -r r2mcp -R` (read-only) |
| `npx -y @modelcontextprotocol/server-filesystem@1.0.0 /paperclip/workspaces/binaries` | Path only exists in the Paperclip container | Drop: Pi's read/grep/find/ls are gated by the permission system |
| `npx -y aws-mcp@1.0.2` | **No repository, ISC, last publish 2025-01** | Replace with `awslabs.aws-api-mcp-server==1.5.6` with `READ_OPERATIONS_ONLY=true` |
| `uvx mcp-server-duckdb==1.1.0` | Last release 2025-05 | Replace with `mcp-server-motherduck==1.1.0 --db-path :memory:` |
| `npx -y @modelcontextprotocol/server-postgres@0.6.2 ${POSTGRES_READONLY_URL}` | **Deprecated on npm** | Replace with `postgres-mcp==0.3.0 --access-mode=restricted` (crystaldba, MIT; last release 2025-05, flagged stale) |
| `uvx mcp-server-kubernetes==0.1.6` | Last release 2025-03 | Replace with `kubernetes-mcp-server@0.0.67 --read-only` (containers org, Apache-2.0). Fails closed without a kubeconfig context (verified) |
| `uvx docker-mcp==0.2.0` | Last release 2024-12; daemon-level access | Drop |
| `uvx k6-mcp-server==2.2.0` | Last release 2025-09 | Keep, flagged |
| `uvx mcp-server-qdrant==0.8.1` | Official | Keep, local path mode |
| (none) | | Add `prometheus-mcp-server==1.6.2` (observability, SRE), `mcp-clickhouse==0.7.0` (analytics, read-only default), `redis-mcp-server==0.5.1` (cache), `hashicorp/terraform-mcp-server:1.0.0` (cloud platform) |

Rules the fleet applies to every MCP binding:

- Read-only modes wherever the server has one (GitHub `/readonly`, Kubernetes `--read-only`, AWS
  `READ_OPERATIONS_ONLY=true`, Postgres `restricted`, ClickHouse write access `false`, radare2 `-R`).
- No secret in `rig.yaml`, `env:` or git. Secrets are whole-value commands in `mcp.json`: `"!cat <abs file>"`
  (env and headers only; Pi does not expand `!command` in `args`).
- `exposure: deferred` for large servers (needs `"tool_search":"allow"` in the seat's permission config) and `direct`
  for small ones. No seat uses the default `codemode`, which would need the `codemode` tool and a scripting surface.
- Each seat's `mcp` permission map is `{"*":"deny", "<server>":"allow", ...}` for exactly its bound servers.

## 6. Permission translation from OpenCode to pi-permission-system

Heretek-Crew `opencode.json` files carry `fs:write` allows and `shell` allows. They translate as follows (the
generator in the brief does this; the result is already in `fleet/fleet.yaml`):

| OpenCode rule | pi-permission-system rule |
|---|---|
| `fs:write` glob with `**` | `path_write` glob with `*` (`*` crosses `/`; verified) |
| `shell` allow pattern | `bash` allow pattern after a `"*":"deny"` catch-all |
| (implicit) | `path_write` ends with `"*..*":"deny"`, `".git/*":"deny"`, `"*/.git/*":"deny"`, `"AGENTS.md":"deny"`, `".pi/*":"deny"`, `".agents/*":"deny"` |
| (implicit) | `path` denies `*.env`, `*.env.*`, `*.pem`, `*.key`, `*id_rsa*`, `*/secrets/*` (with `*.env.example` allowed) |
| (implicit) | `external_directory: "deny"`, `promptTimeoutMs: 60000`, no `ask` anywhere |

Rewrites applied to individual shell allows:

| Heretek-Crew pattern | Fleet pattern | Why |
|---|---|---|
| `npm install*`, `npm update*` | `npm install --ignore-scripts*`, `npm ci --ignore-scripts*`, `npm update --ignore-scripts*` | Lifecycle scripts run arbitrary code from the registry |
| `uv run*` | `uv run pytest*`, `uv run ruff*`, `uv run mypy*` | `uv run` executes anything |
| `r2 -q*` | `r2 -e cfg.sandbox=true -q*` | radare2 `!cmd` runs shell commands; the sandbox blocks it |
| `git diff*`, `git log*` | `git diff --stat*`, `git diff --name-only*`, `git log --oneline*` | `git diff --output=<file>` writes files outside the path gate |
| `tshark*` | `tshark -r *` | `tshark -w` writes capture files |
| `adb connect docker-android*` | removed | Sidecar host name from the Paperclip compose stack |
| `curl -s http://piston:2000/...` | removed; `npx stryker run*`, `cargo mutants*`, `mutmut run*` added | The Piston sidecar does not exist in openrig; mutation tools run locally |
| (all seats) | `rig whoami*`, `rig ps*`, `rig queue *`, `rig send *`, `rig capture *`, `rig transcript *`, `git status*`, `git show --stat*` | openrig coordination and read-only git |

## 7. Skills

### 7.1 Sources

| Repository | HEAD inspected | Licence | Used for |
|---|---|---|---|
| `@openrig/cli@0.6.11` tarball, `daemon/assets/plugins/openrig-core/skills/` | 0.6.11 | Apache-2.0 | 19 openrig-core skills (this copy differs from upstream main; vendor from the tarball) |
| obra/superpowers | `bb92a77` | MIT | 7 skills Heretek-Crew already used (full directories) plus 4 additions |
| trailofbits/skills | `5c99c03` | CC-BY-SA-4.0 | Security and testing skills (share-alike: vendored files keep that licence) |
| getsentry/skills | `f57ada2` | Apache-2.0 | security-review, gha-security-review, skill-scanner, find-bugs, document-api-endpoint |
| anthropics/skills | `dbd4588` | Per skill (`LICENSE.txt` in each) | webapp-testing, frontend-design, doc-coauthoring |
| vercel-labs/agent-skills | `063bee9` | MIT in skill frontmatter (no root licence) | web-design-guidelines, react-best-practices |
| vercel-labs/skills (`find-skills`) | `13e4063` | MIT | CLI only. `skills@1.7.2 --agent pi` installs into project `.agents/skills/`, which `--no-approve` ignores, so the fleet does not use it to install; `skills.sh` returned 403 here |
| Heretek-AI/heretek-skills | `37a1354` | n/a | spoonfeeder, adversarial-audit-prompt (used to write the planning prompts, not loaded into seats) |
| Heretek-AI/Heretek-Crew `roles/*/.opencode/skills` | `5ffb1fc` | per file | 76 unique skills: 14 shared across roles (all copies byte-identical), 62 role-specific |

Pi loads a skill from a directory containing `SKILL.md` with `name` (lowercase, digits, hyphens, at most 64 chars) and
`description` (at most 1024 chars). Malformed files and skills without a description are skipped; on a name
collision the first one wins with a warning. Pi does not require the directory name to match `name`.

### 7.2 openrig-core loadout

| Skill | Bytes | Seats |
|---|---|---|
| openrig-operating-model | 24,942 | all 51 |
| mission-slice-sop | 8,282 | all 51 |
| delegating-work | 4,773 | all 51 |
| queue-handoff | 10,457 | all 51 |
| refocusing | 3,455 | all 51 |
| seat-continuity-and-handover | 10,244 | all 51 |
| messaging-the-human, orienting-to-an-inherited-seat, session-compaction-and-restore | 8,259 / 18,107 / 8,955 | the 15 pod leads (exec-director and tpm-scrum-lead are among them) |
| openrig-user, forming-an-openrig-mental-model, agent-operated-workflows | 69,847 / 16,122 / 4,150 | exec-director and tpm-scrum-lead (they operate the `rig` CLI) |

Skills cost only their name and description in the system prompt until the model reads one, so the core loadout is
cheap; `openrig-user` is large and stays with the two coordinators.

## 8. Fleet architecture and per-role mapping

Eight rigs. Rigs 1 to 7 are static; rig 8 (`heretek-omni-fleet`) is a command pod plus pod fragments and member
fragments that `rig expand` and `rig add` attach on demand. Edges never cross rigs (openrig rejects
`other-rig.z` with `does not resolve to a pod member`), so cross-rig escalation goes through seat addresses
(`rig send <pod>-<member>@<rig>`) written into each charter. There is no `reviews` edge kind (`must be one of
delegates_to, spawned_by, can_observe, collaborates_with, escalates_to`); review relationships use `can_observe`.

| Rig | Pods (lead first) | Seats |
|---|---|---|
| executive-and-architecture | exec (exec-director, product-director, system-architect); delivery (tpm-scrum-lead, git-drift-coord, tech-docs-lead) | 6 |
| fullstack-and-web-studio | build (ts-node-fullstack, python-backend-spec, go-backend-eng, java-kotlin-eng); design (ui-ux-designer, design-system-eng, fe-perf-eng, a11y-specialist, mobile-web-eng, brand-copy-spec, ux-research-analyst) | 11 |
| systems-and-mobile-foundry | systems (rust-systems-spec, cpp-lowlevel-eng); mobile (android-mobile-spec, ios-mobile-spec) | 4 |
| game-dev-and-sim-rig | engine (engine-systems-eng, physics-sim-eng, graphics-shader-eng); gameplay (game-systems-dev, game-ai-dev, tech-artist-pipeline) | 6 |
| cloud-sre-and-data-platform | platform (cloud-platform-eng, k8s-orchestrator, dependency-patcher); sre (sre-incident-eng, observability-eng); data (dba-specialist, cache-streaming-eng, data-pipeline-eng, analytics-metrics-eng); ml (mlops-serving-eng, vector-rag-spec) | 11 |
| qa-and-verification-gauntlet | qa (release-qa-officer, e2e-browser-qa, api-contract-tester, load-stress-tester, sabotage-qa-tester, static-analysis-lead) | 6 |
| defensive-sec-and-red-team | blue (threat-modeler, appsec-engineer, cloud-sec-auditor, compliance-auditor); red (ai-red-teamer, binary-reverse-eng, firmware-sec-analyst) | 7 |
| heretek-omni-fleet | command (exec-director, tpm-scrum-lead, system-architect) + 15 pod fragments + 51 member fragments | 3 + on demand |
| **Total static** | 15 pods | **51** |

Policy posture: `builtin:locked` is recorded for the 7 security seats plus static-analysis-lead, sabotage-qa-tester and
release-qa-officer (they judge other seats' work); `builtin:standard` for every builder. `builtin:yolo` and
`builtin:open` are never used. The recorded policy is documentation for openrig; the per-seat pi-permission-system
config is the enforcement.

Every seat also gets the six openrig-core skills from section 7.2 (pod leads and coordinators get more).
`[source]` marks a third-party skill; unmarked skills come from Heretek-Crew.

| # | Role | Rig / pod | Lead | Policy | Thinking | MCP servers | Domain skills (shared + role-local) |
|---|------|-----------|------|--------|----------|-------------|--------------------------------------|
| 1 | `exec-director` | executive-and-architecture / exec | yes | standard | xhigh | github(issues, ro), memory | dispatching-parallel-agents [superpowers], executive-okr-decomposition |
| 2 | `product-director` | executive-and-architecture / exec |  | standard | high | github(issues, ro), memory | brainstorming [superpowers], writing-plans [superpowers], epic-roadmap-authoring |
| 3 | `system-architect` | executive-and-architecture / exec |  | standard | xhigh | codebase-memory, context7 | brainstorming [superpowers], writing-plans [superpowers], executing-plans [superpowers], madr-architecture-decision |
| 4 | `tpm-scrum-lead` | executive-and-architecture / delivery | yes | standard | high | github(issues, ro), memory | dispatching-parallel-agents [superpowers], git-flow, planning-with-files, sprint-ticket-decomposition |
| 5 | `git-drift-coord` | executive-and-architecture / delivery |  | standard | high | codebase-memory | git-flow, using-git-worktrees [superpowers], finishing-a-development-branch [superpowers], worktree-rebase-orchestration |
| 6 | `tech-docs-lead` | executive-and-architecture / delivery |  | standard | high | codebase-memory | doc-coauthoring [anthropic], docs-as-code-synchronization |
| 7 | `ts-node-fullstack` | fullstack-and-web-studio / build | yes | standard | high | codebase-memory, context7 | nextjs-dev, systematic-debugging [superpowers], tailwind-ui, test-driven-development [superpowers], typescript-astro, react-best-practices [vercel], receiving-code-review [superpowers], end-to-end-type-safe-fullstack |
| 8 | `python-backend-spec` | fullstack-and-web-studio / build |  | standard | high | codebase-memory, context7 | systematic-debugging [superpowers], test-driven-development [superpowers], modern-python [tob], property-based-testing [tob], fastapi-async-development |
| 9 | `go-backend-eng` | fullstack-and-web-studio / build |  | standard | high | codebase-memory, context7 | systematic-debugging [superpowers], test-driven-development [superpowers], receiving-code-review [superpowers], go-expert, idiomatic-go-service-development |
| 10 | `java-kotlin-eng` | fullstack-and-web-studio / build |  | standard | high | codebase-memory | systematic-debugging [superpowers], test-driven-development [superpowers], receiving-code-review [superpowers], spring-boot-virtual-thread-tuning |
| 11 | `ui-ux-designer` | fullstack-and-web-studio / design | yes | standard | high | chrome-devtools, playwright | tailwind-ui, typescript-astro, frontend-design [anthropic], web-design-guidelines [vercel], tailwind-ui-prototyping |
| 12 | `design-system-eng` | fullstack-and-web-studio / design |  | standard | high | chrome-devtools, codebase-memory | tailwind-ui, typescript-astro, impeccable-taste, storybook-component-tokenization |
| 13 | `fe-perf-eng` | fullstack-and-web-studio / design |  | standard | high | chrome-devtools, playwright | react-best-practices [vercel], core-web-vitals-profiling |
| 14 | `a11y-specialist` | fullstack-and-web-studio / design |  | standard | high | playwright, chrome-devtools | web-design-guidelines [vercel], wcag-axe-audit-automation |
| 15 | `mobile-web-eng` | fullstack-and-web-studio / design |  | standard | high | chrome-devtools, playwright | nextjs-dev, tailwind-ui, typescript-astro, web-design-guidelines [vercel], mobile-viewport-emulation-audit |
| 16 | `brand-copy-spec` | fullstack-and-web-studio / design |  | standard | high | none | actionable-microcopy-refactoring, humanizer |
| 17 | `ux-research-analyst` | fullstack-and-web-studio / design |  | standard | high | duckdb, github(issues, ro) | feedback-clustering-analysis |
| 18 | `rust-systems-spec` | systems-and-mobile-foundry / systems | yes | standard | high | codebase-memory, context7 | systematic-debugging [superpowers], test-driven-development [superpowers], rust-review [tob], cargo-fuzz [tob], rust-async-service-hardening |
| 19 | `cpp-lowlevel-eng` | systems-and-mobile-foundry / systems |  | standard | high | codebase-memory | systematic-debugging [superpowers], test-driven-development [superpowers], c-review [tob], address-sanitizer [tob], libfuzzer [tob], modern-cpp-sanitizer-verification |
| 20 | `android-mobile-spec` | systems-and-mobile-foundry / mobile | yes | standard | high | mobile, codebase-memory | artemis-android-ui-exploration, jetpack-compose-state-hoisting |
| 21 | `ios-mobile-spec` | systems-and-mobile-foundry / mobile |  | standard | high | codebase-memory | swiftui-concurrency-implementation |
| 22 | `engine-systems-eng` | game-dev-and-sim-rig / engine | yes | standard | high | codebase-memory | cache-conscious-ecs-design |
| 23 | `physics-sim-eng` | game-dev-and-sim-rig / engine |  | standard | high | codebase-memory | collision-broadphase-optimization |
| 24 | `graphics-shader-eng` | game-dev-and-sim-rig / engine |  | standard | high | codebase-memory | shader-compilation-and-validation |
| 25 | `game-systems-dev` | game-dev-and-sim-rig / gameplay | yes | standard | high | codebase-memory | gameplay-state-machine-implementation |
| 26 | `game-ai-dev` | game-dev-and-sim-rig / gameplay |  | standard | high | codebase-memory | behavior-tree-authoring |
| 27 | `tech-artist-pipeline` | game-dev-and-sim-rig / gameplay |  | standard | high | none | gltf-asset-optimization |
| 28 | `cloud-platform-eng` | cloud-sre-and-data-platform / platform | yes | standard | high | aws, codebase-memory, terraform | opentofu-plan-and-validation |
| 29 | `k8s-orchestrator` | cloud-sre-and-data-platform / platform |  | standard | high | kubernetes | helm-chart-security-hardening |
| 30 | `dependency-patcher` | cloud-sre-and-data-platform / platform |  | standard | high | codebase-memory | supply-chain-risk-auditor [tob], automated-lockfile-patching |
| 31 | `sre-incident-eng` | cloud-sre-and-data-platform / sre | yes | standard | high | prometheus | blameless-incident-triage-and-postmortem |
| 32 | `observability-eng` | cloud-sre-and-data-platform / sre |  | standard | high | codebase-memory, prometheus | prometheus-rule-validation |
| 33 | `dba-specialist` | cloud-sre-and-data-platform / data | yes | standard | high | postgres, codebase-memory | zero-downtime-migration-audit |
| 34 | `cache-streaming-eng` | cloud-sre-and-data-platform / data |  | standard | high | redis | kafka-topic-and-consumer-tuning |
| 35 | `data-pipeline-eng` | cloud-sre-and-data-platform / data |  | standard | high | duckdb, codebase-memory | duckdb-dbt-pipeline-execution |
| 36 | `analytics-metrics-eng` | cloud-sre-and-data-platform / data |  | standard | high | codebase-memory, clickhouse | clickhouse-schema-and-aggregation-optimization |
| 37 | `mlops-serving-eng` | cloud-sre-and-data-platform / ml | yes | standard | high | none | vllm-serving-benchmarking |
| 38 | `vector-rag-spec` | cloud-sre-and-data-platform / ml |  | standard | high | qdrant, codebase-memory | rag-retrieval-evaluation |
| 39 | `release-qa-officer` | qa-and-verification-gauntlet / qa | yes | locked | high | github(pull_requests, ro) | code-review, requesting-code-review [superpowers], tdd, verification-before-completion [superpowers], finishing-a-development-branch [superpowers], find-bugs [sentry], release-readiness-audit |
| 40 | `e2e-browser-qa` | qa-and-verification-gauntlet / qa |  | standard | high | playwright, chrome-devtools | requesting-code-review [superpowers], verification-before-completion [superpowers], webapp-testing [anthropic], playwright-page-object-automation |
| 41 | `api-contract-tester` | qa-and-verification-gauntlet / qa |  | standard | high | openapi | requesting-code-review [superpowers], tdd, verification-before-completion [superpowers], document-api-endpoint [sentry], dotnet-expert, openapi-contract-verification |
| 42 | `load-stress-tester` | qa-and-verification-gauntlet / qa |  | standard | high | k6, codebase-memory | k6-stress-scenario-execution |
| 43 | `sabotage-qa-tester` | qa-and-verification-gauntlet / qa |  | locked | high | codebase-memory | requesting-code-review [superpowers], verification-before-completion [superpowers], mutation-testing [tob], property-based-testing [tob], adversarial-mutation-sabotage |
| 44 | `static-analysis-lead` | qa-and-verification-gauntlet / qa |  | locked | high | semgrep, codebase-memory | code-review, semgrep [tob], semgrep-rule-creator [tob], semgrep-rule-variant-creator [tob], codeql [tob], sarif-parsing [tob], custom-semgrep-rule-authoring |
| 45 | `threat-modeler` | defensive-sec-and-red-team / blue | yes | locked | xhigh | codebase-memory, github(repos, ro) | security-audit, entry-point-analyzer [tob], audit-context-building [tob], stride-threat-modeling |
| 46 | `appsec-engineer` | defensive-sec-and-red-team / blue |  | locked | high | semgrep, codebase-memory | code-review, security-audit, semgrep [tob], sarif-parsing [tob], variant-analysis [tob], fp-check [tob], security-review [sentry], owasp-reachability-triage |
| 47 | `cloud-sec-auditor` | defensive-sec-and-red-team / blue |  | locked | high | aws, codebase-memory | security-audit, gha-security-review [sentry], agentic-actions-auditor [tob], iam-least-privilege-audit |
| 48 | `compliance-auditor` | defensive-sec-and-red-team / blue |  | locked | high | github(repos, ro) | supply-chain-risk-auditor [tob], spec-to-code-compliance [tob], sbom-generation-and-license-audit |
| 49 | `ai-red-teamer` | defensive-sec-and-red-team / red | yes | locked | xhigh | codebase-memory, context7 | skill-scanner [sentry], agentic-actions-auditor [tob], auditing-mcp-servers-for-tool-poisoning, detecting-ai-model-prompt-injection-attacks, detecting-indirect-prompt-injection, testing-for-system-prompt-leakage, testing-prompt-injection-in-rag-pipelines |
| 50 | `binary-reverse-eng` | defensive-sec-and-red-team / red |  | locked | xhigh | radare2 | dwarf-expert [tob], yara-rule-authoring [tob], radare2-defensive-disassembly, rea-evidence-based-decompilation |
| 51 | `firmware-sec-analyst` | defensive-sec-and-red-team / red |  | locked | high | radare2 | yara-rule-authoring [tob], dwarf-expert [tob], firmware-extraction-and-hardening-audit |

## 9. Not verified (and what to do about it)

| Item | Why not | What the build must do |
|---|---|---|
| Live inference on `opencode-go/muse-spark-1.3-contributor` | `opencode.ai` is blocked (proxy 403) in the planning container | First milestone with a real key: one seat, one prompt, capture the reply |
| `skills.sh` search via `find-skills` | 403 from the planning container | Not needed: skills are vendored from pinned git SHAs |
| radare2-mcp install and handshake | radare2 not installed here | Install with `r2pm -Uci r2mcp`, confirm `-R` read-only, record tool list |
| semgrep MCP handshake | Startup needs `https://semgrep.dev` | Run on a networked host; if it still needs a login, fall back to `semgrep scan` in bash only |
| GitHub remote MCP with a PAT | No PAT here | Confirm `/x/<toolset>/readonly` lists only read tools |
| AWS, Postgres, ClickHouse, Redis, Prometheus, Qdrant, k6, Terraform, DuckDB servers | Not run (registry checks only) | `pi mcp list --json` for each with dummy or local backends |
| `mcp-openapi-schema-explorer` usefulness | Connected with 0 tools (resources only); not checked whether Pi offers MCP resources to the model | Check in a seat; if unreachable, drop it and let the seat `read` the OpenAPI file |
| `--access-mode=restricted` spelling for postgres-mcp | README shows the access-mode concept and the `unrestricted` value | Run `uvx postgres-mcp==0.3.0 --help` |
| pi-permission-system under the openrig runner (tmux) rather than `pi -p` | All gate probes ran with `pi -p` | Re-run one deny probe inside a launched seat |
| `pi-lens` on a builder seat | Not spiked | Optional late milestone |

## 10. Reproduction notes

- Registry query: `curl -s "https://registry.modelcontextprotocol.io/v0.1/servers?search=<name>&version=latest"`.
- npm facts: `npm view <pkg>@<ver> version license repository.url time.modified deprecated bin scripts.postinstall`.
- PyPI facts: `curl -s https://pypi.org/pypi/<pkg>/json | jq '.info.version, .info.license'`.
- Pi MCP connection test: write `mcp.json` into a scratch agent dir, then
  `PI_CODING_AGENT_DIR=<dir> pi mcp list --json | jq -c '.servers[] | {name, state, tools: (.tools|length)}'`.
- Gate test: see `scripts/gate-run.sh` and `scripts/mock-openai.mjs` in `docs/IMPLEMENTATION_PROMPT.md`.
