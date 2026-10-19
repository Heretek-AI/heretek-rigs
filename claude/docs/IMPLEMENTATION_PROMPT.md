# IMPLEMENTATION PROMPT: build the Heretek fleet on openrig (heretek-rigs)

## 1. Mission

You are building `heretek-rigs`: the 51 Heretek-Crew agents re-homed as openrig Pi seats running
`opencode-go/muse-spark-1.3-contributor`, organised as 7 static rigs plus 1 dynamic omni rig, with per-seat
skills, MCP servers and enforced permissions. Everything the build depends on was verified by a planning session
on 2026-10-19 with the exact pinned versions below; this file contains the verified facts, the reference code
(already run), the layout and the milestones.

**Read this whole file before writing any code.** Your training data is out of date for every tool here
(openrig 0.6.11, Pi 1.3.0, pi-permission-system 41.0.0, the Muse model). When this file and your memory
disagree, this file wins. When this file and the installed tool disagree, the tool wins: write the discrepancy in
`docs/NOTES.md` and stop to report it.

## 2. How to work

1. Do the milestones in order (section 6). Do not start milestone N+1 until every acceptance check of milestone N
   passes exactly as written.
2. After each milestone: `git add <the exact files you changed>` (never `git add -A` or `git add .`), then
   `git commit -m "M<N>: <title>"`. One commit per milestone minimum.
3. Never skip, delete, weaken or `.skip` a test or an acceptance check to make it pass. If a check is wrong, write
   why in `docs/NOTES.md` and stop.
4. Never invent an API, flag, config key or file format. Look it up in this order: (a) this file; (b) the tool's
   `--help` output; (c) the installed package source under `node_modules/` (for Pi: `docs/*.md` inside
   `@earendil-works/pi-coding-agent`; for the permission system: `docs/configuration.md` inside
   `@gotgenes/pi-permission-system`; for openrig: `daemon/dist/` inside `@openrig/cli`); (d) a throwaway
   experiment in `.scratch/`.
5. Log every discovery, surprise and discrepancy in `docs/NOTES.md` as: date, what you expected, what happened,
   the exact command and its output.
6. If the same error survives 3 attempts, stop. Write in `docs/NOTES.md` what you tried, the exact commands and
   outputs, then report and wait.
7. Hard rules found by the planning spike (breaking one is a failed build):
   - Never put a secret in a file inside the repo, in `rig.yaml`, in an `env:` block, on a command line, or in a
     log. Secrets live only in `$HERETEK_SECRETS` (mode 0700 dir, 0600 files) and are referenced as
     `"!cat <absolute path>"`.
   - Never use `runtime: opencode` (it does not exist; validate passes, preflight fails).
   - Never use `builtin:yolo` or `builtin:open`. Never use `"ask"` in a permission config.
   - Never add a `guidance_merge` startup file. Charters go in the seat's `<agentDir>/AGENTS.md`.
   - Never pass `--rig-root .`; always pass an absolute path (`--rig-root "$PWD"`).
   - Never run `rig up` / `rig expand` / `rig add` for a seat before `scripts/seed-rig.mjs` has seeded it.
   - Never use `pkill -f` with a pattern that also matches your own shell command; kill by PID.
   - Never edit `LICENSE.md` (its content is the word `PLACEHOLDER`; the owner decides the licence).

## 3. Paths and setup

### 3.1 Paths

| What | Path |
|---|---|
| This repo (target) | `/home/john/Projects/heretek-rigs` |
| Heretek-Crew (source of roles) | `/home/john/Projects/Heretek-Crew`, checked out at commit `5ffb1fc` |
| Scratch (git-ignored) | `/home/john/Projects/heretek-rigs/.scratch/` |
| Pinned skill clones | `/home/john/Projects/heretek-rigs/.scratch/vendor/<owner>_<repo>` |
| Tools prefix (`$HERETEK_TOOLS`) | `$HOME/.local/share/heretek-rigs/tools` |
| Secrets (`$HERETEK_SECRETS`) | `$HOME/.config/heretek-rigs/secrets` (dir 0700, files 0600) |
| openrig home (`$OPENRIG_HOME`) | `$HOME/.openrig` (openrig default) |
| Fleet workspace (the repo the seats work on) | `$HERETEK_WORKSPACE`, default `/home/john/Projects/heretek-workspace` (a git repo) |

Work on a new branch: `git checkout -b feat/fleet-build` (from the branch that carries this file).

### 3.2 Toolchain (pinned; install exactly these)

```bash
node --version          # must print v22.19.0 or later 22.x, or v24.x (Pi needs >=22.19.0; openrig needs ^22 || ^24)
npm i -g @openrig/cli@0.6.11 @earendil-works/pi-coding-agent@1.3.0
rig --version           # prints: 0.6.11 (379f0a0d)
pi --version            # prints: 1.3.0
npm view @openrig/cli dist-tags --json   # shows "latest": "0.6.11" (rc 0.6.4-rc.1 is OLDER; never use it)

export HERETEK_TOOLS="$HOME/.local/share/heretek-rigs/tools"
mkdir -p "$HERETEK_TOOLS/pi-packages" "$HERETEK_TOOLS/mcp" "$HERETEK_TOOLS/bin" "$HERETEK_TOOLS/src"
npm i --prefix "$HERETEK_TOOLS/pi-packages" --omit=peer @gotgenes/pi-permission-system@41.0.0
npm i --prefix "$HERETEK_TOOLS/mcp" --no-audit --no-fund \
  @modelcontextprotocol/server-memory@1.0.0 codebase-memory-mcp@0.12.1 @upstash/context7-mcp@4.4.2 \
  @playwright/mcp@0.0.83 chrome-devtools-mcp@1.11.0 mcp-openapi-schema-explorer@1.3.5 \
  @mobilenext/mobile-mcp@1.0.12 kubernetes-mcp-server@0.0.67
ls "$HERETEK_TOOLS/mcp/node_modules/.bin"   # must list: chrome-devtools-mcp codebase-memory-mcp context7-mcp kubernetes-mcp-server mcp-openapi-schema-explorer mcp-server-memory mcp-server-mobile playwright-mcp
uv --version            # any uv; Python MCP servers run as `uvx <pkg>==<ver>`

export HERETEK_SECRETS="$HOME/.config/heretek-rigs/secrets"
mkdir -p "$HERETEK_SECRETS" && chmod 700 "$HERETEK_SECRETS"
# The human puts the real key here; you never see or print it:
#   printf '%s' "<key>" > "$HERETEK_SECRETS/opencode-go.key" && chmod 600 "$HERETEK_SECRETS/opencode-go.key"
```

`codebase-memory-mcp` has a postinstall (`node install.js`) that downloads its release binary from GitHub: do not
pass `--ignore-scripts` for that install.

### 3.3 Reference clones (pinned; the generator refuses any other commit)

```bash
cd /home/john/Projects/heretek-rigs && mkdir -p .scratch/vendor && cd .scratch/vendor
clone() { git clone -q "https://github.com/$1" "$2" && git -C "$2" checkout -q "$3" && echo "$2 $(git -C "$2" rev-parse --short=7 HEAD)"; }
clone obra/superpowers           obra_superpowers          bb92a77
clone trailofbits/skills         trailofbits_skills        5c99c03
clone getsentry/skills           getsentry_skills          f57ada2
clone anthropics/skills          anthropics_skills         dbd4588
clone vercel-labs/agent-skills   vercel-labs_agent-skills  063bee9
git -C /home/john/Projects/Heretek-Crew rev-parse --short=7 HEAD   # must print 5ffb1fc
```

If `git checkout <sha>` fails because the clone is shallow or the commit is unknown, stop and report (do not pick
another commit). The openrig-core skills come from the installed CLI, not from git:
`OPENRIG_CORE="$(npm root -g)/@openrig/cli/daemon/assets/plugins/openrig-core/skills"` (19 skill directories).

### 3.4 What is ported from where

| Source | Taken | Licence obligation |
|---|---|---|
| Heretek-Crew `roles/<id>/AGENTS.md` | Sections 1 to 3 of each charter (identity, chain of command, responsibilities), with "Paperclip" rewritten | Same repo family; keep the provenance line the generator writes |
| Heretek-Crew `roles/<id>/.opencode/skills/<skill>` | 62 role-specific skills + 7 shared non-superpowers skills | Keep each `SKILL.md` frontmatter `license:` as is |
| Heretek-Crew `roles/<id>/opencode/opencode.json` | Already translated into `fleet/fleet.yaml` (`permissions`, `mcp`) | n/a |
| obra/superpowers `skills/<id>` (full directories) | 7 skills Heretek-Crew truncated + 4 additions | MIT: copy root `LICENSE` into each skill dir (the generator does it) |
| trailofbits/skills | 22 skills (see `fleet/fleet.yaml`) | CC-BY-SA-4.0: copy root `LICENSE`, keep files unmodified (share-alike applies to changes) |
| getsentry/skills, anthropics/skills, vercel-labs/agent-skills | 10 skills (5 + 3 + 2) | Apache-2.0 / per-skill `LICENSE.txt` / MIT in frontmatter |
| `@openrig/cli@0.6.11` openrig-core skills | 12 of the 19 | Apache-2.0: copy `@openrig/cli/LICENSE` into each |

## 4. Verified facts

### 4.1 openrig 0.6.11

- Binary is `rig` (not `openrig`). Runtimes: `claude-code`, `codex`, `pi`, `omp`, `terminal`, `stub`. **No
  `opencode` runtime.**
- `rig spec validate <rig.yaml> --json` checks syntax only. It printed `{"valid":true,"errors":[]}` for
  `runtime: opencode`. `rig spec preflight <rig.yaml> --json` is the real gate; it printed
  `{"ready":false,"errors":["a.x: unsupported runtime \"opencode\"", ...]}`. Always run both.
- Rig spec errors captured verbatim (use them as negative test fixtures):

```text
pods[0].edges[0].kind: must be one of delegates_to, spawned_by, can_observe, collaborates_with, escalates_to (got "reviews")
edges[0].to: "other-rig.z" does not resolve to a pod member
extra: unknown key "extra"; refusing the spec because normalization would otherwise discard it and alter the requested topology
pods[0].members[0].id: must not contain dots (got "x.y")
pods[0].members[0].permission_policy: 'locked' is a built-in policy name — use 'builtin:locked' (the builtin: prefix is mandatory; bare names never resolve, no shadowing)
```

- RigSpec: `version: "0.2"`, `name`, `summary`, optional `culture_file`, `docs`, `pods[]` (`id`, `label`,
  `members[]`, `edges[]`), rig-level `edges[]` using `pod.member` addresses. Member keys: `id`, `agent_ref`
  (`local:<relative>` or `path:<absolute>`), `profile`, `runtime`, `cwd`, optional `model`, `effort`,
  `permission_policy`, `env`, `role`, `restore_policy`. Ids may not contain `.` or `@`.
- Session name is `<pod>-<member>@<rig>`; it is also the `rig send` address.
- Edges never cross rigs. There is no `reviews` kind: use `can_observe`.
- `rig spec audit <rig.yaml> --json` is advisory. Without `culture_file` it reports `missing_culture`; with it, only
  `missing_startup_context` (rig-level startup files) remains, which this fleet accepts.
- AgentSpec: `name`, `version` (quoted string), `description`, `defaults.runtime`, `defaults.model`, `imports[]`
  (`ref: local:<dir>`; an imported spec may not import), `profiles.<name>.uses` (`skills`, `guidance`, `subagents`,
  `plugins`, `runtime_resources`), `resources.skills[]` (`id`, `path`), `startup.files[]` (`path`,
  `delivery_hint`, `required`), `startup.actions[]` (`slash_command`, `send_text`, `startup_proof`; `shell` is
  rejected). `rig agent validate <agent.yaml> --json` checks syntax only.
- A member that sets no `model` inherits `defaults.model` from its agent.yaml. Verified on a launched seat: the
  runner process carried `--model opencode-go/muse-spark-1.3-contributor --no-approve --cwd <workspace>`.
- `permission_policy` for Pi: `builtin:yolo` becomes `--approve`; everything else becomes `--no-approve` (the
  floor: project `.pi/*` and `.agents/skills` are ignored). openrig does not enforce tools for Pi. Preflight prints
  `blue.appsec-engineer: permission_policy ref="builtin:locked" origin=builtin launch_posture=floor`.
- Plugins are not projected for Pi. Declared skills are projected into `<agentDir>/skills/`: shared ones as
  `heretek-shared:<id>`, a role's own as `<id>`.
- `rig up <rig.yaml> --cwd <workspace> --yes --json` returned `"status":"completed"` and launched all 7 seats of the
  security rig. openrig writes two managed blocks into `<workspace>/AGENTS.md` (`CULTURE-default.md` and
  `openrig-start.md`) and warns that the file is untracked. That shared block is identical for every seat; the
  role charter does not go there.
- `guidance_merge` writes a managed block named `guidance/role.md` into `<cwd>/AGENTS.md`; with two seats in one
  cwd the second overwrote the first and the first seat received the wrong role. This is why the fleet never uses it.
- Pi seat state: `$OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent`. Files placed there before launch survive
  launch and `rig down` / `rig up <rig> --existing`. openrig adds `models-store.json`, `skills/` and `sessions/`.
- Pi child env is a fixed allow-list (PATH, HOME, USER, LOGNAME, TERM, LANG, LC_ALL, SHELL, TMPDIR, some
  `OPENRIG_*`, `PI_CODING_AGENT_DIR`, `PI_CODING_AGENT_SESSION_DIR`). `OPENCODE_API_KEY` is **not** forwarded to Pi
  seats (only to `omp` seats, behind `recovery.provider_auth_env_allowlist`). Hence the per-seat `auth.json`.
- `rig expand <RIG-ID> <pod.yaml> --rig-root <ABS> --json` needs the rig **ID** (a ULID such as
  `01M58RYN1C7QBXGQPYF1YGAMJ2`, from `rig ps --json | jq -r '.[] | select(.name=="<rig>") | .rigId'`). Passing
  the rig name printed `{"ok":false,"error":"Rig \"heretek-omni-fleet\" not found"}`. `rig add` accepts a name or
  an ID: `rig add <rig> <pod> <member.yaml> --rig-root <ABS>`.
- Expanding a 6-seat pod made the CLI print `Request to http://127.0.0.1:7655/api/rigs/<id>/expand timed out after
  5000ms` and `The command's outcome is UNKNOWN`, yet all 6 seats were running a moment later. After any timeout,
  check `rig ps --nodes --rig <rig>` before retrying; never retry blindly.
- `--rig-root .` resolves against the daemon's cwd, not your shell's. Always pass an absolute path.
- `rig bundle check <folder>` is advisory and reports agents outside the rig folder as `referenced_files ...
  outside the bundle folder`; `rig bundle create` (needs the daemon) vendors them into the archive. This repo keeps
  agents in `specs/agents/` and accepts that finding.

### 4.2 Pi 1.3.0

- Model: `opencode-go/muse-spark-1.3-contributor`, api `openai-responses`, base URL
  `https://opencode.ai/inference/go/v1`, context 1,048,576, max output 131,072. Thinking levels: off, minimal,
  low, medium, high, xhigh. **`max` is unsupported.**
- `<agentDir>/auth.json` with `{"opencode-go":{"type":"api_key","key":"!cat /abs/path/opencode-go.key"}}`:
  `pi auth check` reports `ready`. The `!` form runs the command when Pi needs the key.
- `<agentDir>/settings.json` keys used: `defaultProvider`, `defaultModel`, `defaultThinkingLevel`,
  `defaultTools`, `packages`, `quietStartup`. `defaultTools` replaces the default tool list; built-in names are
  `read`, `bash`, `powershell`, `edit`, `write`, `grep`, `find`, `ls`, plus `codemode` and `tool_search`.
- `<agentDir>/AGENTS.md` is loaded into the seat's system prompt (verified: the launched appsec seat's session
  contains its charter text).
- `<agentDir>/mcp.json`: `{"mcpServers":{"<name>":{command,args,env,cwd,url,headers,exposure,description,timeout,enabled}}}`.
  `env` and `headers` values may be `${NAME}` or a whole-value `!command`; **`args` never expand `!command`**.
  Legacy SSE is rejected. Tools are named `mcp__<server>__<tool>` with non `[A-Za-z0-9_]` characters turned into `_`
  (server `codebase-memory` gives `mcp__codebase_memory__...`).
- Exposure: `codemode` (default; needs the `codemode` tool), `deferred` (loaded by `tool_search`), `direct`
  (declared to the model), `hidden`. This fleet uses only `deferred` and `direct`.
- `PI_CODING_AGENT_DIR=<dir> pi mcp list --json` prints `{"servers":[...],"errors":[]}`; each server has `name`,
  `state` (`connected` / `failed`), `tools` (array) and `error`. Verified connected: memory (tool call returned the
  graph), codebase-memory (17 tools), context7 (2), playwright (25), chrome-devtools (32), mobile (34), openapi
  (0 tools, resources only). `kubernetes-mcp-server --read-only` fails closed with `no current-context is set`.
  `semgrep mcp -t stdio` needs `https://semgrep.dev` at startup.
- `pi -p` (print mode) sometimes does not exit after the agent settles. Always wrap it in `timeout` and read the
  JSON events instead of relying on the exit code (`rc=124` is normal).

### 4.3 pi-permission-system 41.0.0 (the enforcement layer)

- Loaded as a Pi package from a local path in `settings.json` `packages`; config at
  `<agentDir>/extensions/pi-permission-system/config.json`.
- Surfaces: `*`, `read`, `write`, `edit`, `grep`, `find`, `ls`, `bash` (map), `path` (map), `path_read`,
  `path_write` (map), `external_directory`, `mcp` (map), `skill` (map), any other tool by name (e.g. `tool_search`).
- **Inside a map, the last matching rule wins.** Put the catch-all first and guards last.
- A config that fails to parse falls back to `ask` for everything. `promptTimeoutMs` makes an unanswered prompt a
  deny. Seats have nobody to answer, so this fleet never writes `ask` and always sets `promptTimeoutMs: 60000`.
- Verified results (mock model, one tool call each):

| Call | Rule set | Result text |
|---|---|---|
| `write src/evil.ts` | `path_write: {"*":"deny", ...}` | `[pi-permission-system] Denied by policy: 'path_write' for tool 'write' for path 'src/evil.ts' (rule '*').` |
| `write docs/security/advisories/SEC-1.md` | `"docs/security/advisories/*":"allow"` | `Successfully wrote to docs/security/advisories/SEC-1.md` |
| `write docs/a/b.md` | `"docs/*":"allow"` | allowed (`*` crosses `/`) |
| `write <absolute cwd>/docs/abs.md` | `"docs/*":"allow"` | allowed (absolute paths are matched relative to cwd) |
| `write docs/../evil.md` | `"docs/*":"allow"` without a guard | **allowed, file created: the bypass** |
| `write docs/security/advisories/../../../evil.md` | guard `"*..*":"deny"` last | `Denied by policy: 'path_write' ... (rule '*..*')` |
| `write AGENTS.md` | `"AGENTS.md":"deny"` | `Denied by policy: 'path_write' ... (rule 'AGENTS.md')` |
| `read docs/../.env` | `path: {"*.env":"deny"}` | `Denied by policy: 'path_read' for tool 'read' for path 'docs/../.env' (rule '*.env')` |
| `bash echo hi; touch pwned` | `bash: {"*":"deny","echo *":"allow"}` | `Denied by policy: 'bash' (rule '*').` (compound commands are parsed) |
| `bash git diff --output=x.txt` | fleet allow-list (no `git diff*`) | `Denied by policy: 'bash' (rule '*').` |
| `bash curl -s https://example.com` | fleet allow-list | `Denied by policy: 'bash' (rule '*').` |
| `read <agentDir>/skills/<id>/SKILL.md` | `external_directory: "deny"` | allowed (skills still load) |
| `tool_search` | top-level `"*":"deny"` only | `Tool tool_search not found` |
| `tool_search` | plus `"tool_search":"allow"` | `Loaded 8 tools. They are available from your next call: ...` |
| `mcp__memdirect__read_graph` | `mcp: {"*":"deny","memdirect":"allow"}` | returned `{"entities":[],"relations":[]}` |
| `mcp__memory__read_graph` | server not in the `mcp` map | `Tool mcp__memory__read_graph not found` |

### 4.4 The model, live

Not verified here (the planning container could not reach `opencode.ai`). Heretek-Crew's
`docs/reports/first-agent-run-evidence.md` shows a successful run on this exact model id through OpenCode. A launched
seat without network shows `"errorMessage":"Connection error."` with `auto_retry_start` events in its session JSONL:
that is what "no network" looks like, not a config error.

### 4.5 Not verified, be careful

Check each of these in the milestone named, and write the answer in `docs/NOTES.md`:

| Item | Milestone | How to check |
|---|---|---|
| Live inference on the Muse model through a seat | M8 | `rig send` a prompt, then `rig capture` the reply |
| `pi-permission-system` inside a launched seat (all gate probes used `pi -p`) | M8 | Ask the seat to write `src/zz.txt`; expect the denial text in its transcript |
| `postgres-mcp==0.3.0 --access-mode=restricted` spelling | M10 | `uvx postgres-mcp==0.3.0 --help` |
| radare2-mcp 1.9.0 build path and `-R` flag | M10 | Build per `fleet/mcp-servers.yaml` `install`; `r2mcp -h` |
| semgrep MCP startup on a networked host | M10 | `pi mcp list --json` for the appsec seat |
| GitHub remote `/x/<toolset>/readonly` lists read tools only | M10 | `pi mcp list --json` with a PAT; no tool named `create_*`, `update_*`, `delete_*`, `merge_*`, `push_*` |
| AWS, Postgres, ClickHouse, Redis, Prometheus, Qdrant, k6, Terraform, DuckDB servers | M10 | `pi mcp list --json` per seat with local or dummy backends |
| Pi exposes MCP resources (openapi server has 0 tools) | M10 | If the seat cannot read the spec through MCP, set `enabled: false` for openapi and note it |

## 5. Target layout

Files marked (given) already exist on this branch. Files marked (ref) must be created **byte-for-byte** from the
reference code in section 6. Everything under `specs/`, `rigs/` and `fleet/skills-lock.json` is generated by
`scripts/gen-specs.mjs`: never hand-edit generated files; change the generator or `fleet/fleet.yaml` and regenerate.

```text
heretek-rigs/
├── LICENSE.md                      (given) PLACEHOLDER; do not edit
├── README.md                       what the fleet is, how to seed and launch (M12)
├── package.json                    (ref) yaml@2.9.1 only; scripts check/test/gen/gate
├── package-lock.json               npm install output
├── .gitignore                      .scratch/, node_modules/
├── Makefile                        thin wrappers: check, test, gen, gate, seed RIG=<id>
├── fleet/
│   ├── fleet.yaml                  (given) 51 roles: rig, pod, edges, policy, thinking, skills, MCP, permissions
│   ├── mcp-servers.yaml            (given) 20 pinned MCP servers + 3 dropped
│   └── skills-lock.json            (generated) source, path and tree hash of every vendored shared skill
├── docs/
│   ├── IMPLEMENTATION_PROMPT.md    (given) this file
│   ├── OSINT_ECOSYSTEM_REPORT.md   (given) evidence and per-role mapping
│   └── NOTES.md                    your discovery log
├── PROMPT_ADVERSARIAL_FLEET_AUDIT.md (given) the audit to run after you finish
├── scripts/
│   ├── mock-openai.mjs             (ref) deterministic OpenAI-compatible mock for gate tests
│   ├── gate-run.sh                 (ref) run Pi once against the mock with one forced tool call
│   ├── gate-role.sh                (ref) 7 allow/deny probes for one role's rendered config
│   ├── render-seat.mjs             (ref) write one seat's agentDir files
│   ├── seed-rig.mjs                (ref) render every seat in a rig, pod fragment or member fragment
│   ├── gen-specs.mjs               (ref) generate specs/, rigs/, skills-lock.json
│   └── check-fleet.mjs             (ref) static invariants
├── tests/
│   └── render-seat.test.mjs        (ref) node:test contract for render-seat
├── specs/agents/                   (generated)
│   ├── _shared/agent.yaml          heretek-shared: declares 62 vendored skills
│   ├── _shared/skills/<id>/        vendored skill dirs (+ LICENSE where the source had one at root only)
│   └── <domain>/<role>/            51 of these; domain in fleet.yaml (executive, web-design, languages,
│       ├── agent.yaml              security, cloud-sre, data-ai, qa, gamedev, operations)
│       ├── guidance/role.md        ported charter (becomes the seat's AGENTS.md via render-seat)
│       ├── startup/context.md      one-line send_text startup context
│       └── skills/<id>/            role-local Heretek-Crew skills
├── rigs/                           (generated)
│   ├── <rig>/rig.yaml              7 static rigs (+ CULTURE.md, README.md)
│   └── heretek-omni-fleet/
│       ├── rig.yaml                command pod: exec-director, tpm-scrum-lead, system-architect
│       ├── pods/<pod>.yaml         15 pod fragments for rig expand
│       └── members/<role>.yaml     51 member fragments for rig add
└── .github/workflows/ci.yml        M11
```

`package.json` (ref):

```json
{
  "name": "heretek-rigs",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "description": "The Heretek fleet as openrig Pi seats",
  "engines": { "node": ">=22.19.0 <25" },
  "scripts": {
    "check": "node scripts/check-fleet.mjs",
    "test": "node --test tests/*.test.mjs",
    "gen": "node scripts/gen-specs.mjs",
    "gate": "bash scripts/gate-role.sh"
  },
  "dependencies": {
    "yaml": "2.9.1"
  }
}
```

## 6. Milestones

### M0: Toolchain and clones

**Do:** sections 3.2 and 3.3 exactly. Create `.gitignore` with two lines: `.scratch/` and `node_modules/`.
Create `docs/NOTES.md` with a heading `# NOTES` and one entry recording the outputs of `node --version`,
`rig --version`, `pi --version`, `uv --version` and the five clone SHAs.

**Acceptance:**
- `rig --version` prints `0.6.11 (379f0a0d)`; `pi --version` prints `1.3.0`.
- `ls "$HERETEK_TOOLS/pi-packages/node_modules/@gotgenes/pi-permission-system/package.json"` exists and
  `jq -r .version` on it prints `41.0.0`.
- Each clone prints its pinned SHA; `git -C /home/john/Projects/Heretek-Crew rev-parse --short=7 HEAD` prints `5ffb1fc`.
- `ls "$OPENRIG_CORE" | wc -l` prints `19`.

### M1: Re-run the gate spike yourself

Learn how Pi and the permission system behave before building on them.

**Do:** create `package.json` (above), run `npm install`, then create these two files verbatim.

#### File: scripts/mock-openai.mjs

```js
// Deterministic OpenAI-compatible chat-completions mock for gate tests.
// Turn 1 (no tool message yet): emits one tool call taken from MOCK_TOOL / MOCK_ARGS.
// Turn 2+: emits a final text that echoes the last tool result, so the test can grep it.
import http from "node:http";
import fs from "node:fs";
const port = Number(process.env.MOCK_PORT ?? 18080);
const log = process.env.MOCK_LOG ?? "/dev/null";
const tool = process.env.MOCK_TOOL ?? "bash";
const args = process.env.MOCK_ARGS ?? JSON.stringify({ command: "echo hi" });
function sse(res, chunks) {
  res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache" });
  for (const c of chunks) res.write(`data: ${JSON.stringify(c)}\n\n`);
  res.end("data: [DONE]\n\n");
}
const base = { id: "mock-1", object: "chat.completion.chunk", created: 0, model: "mock" };
http.createServer((req, res) => {
  let body = "";
  req.on("data", (d) => (body += d));
  req.on("end", () => {
    fs.appendFileSync(log, body + "\n");
    if (req.url?.endsWith("/models")) { res.writeHead(200, { "content-type": "application/json" }); return res.end('{"data":[{"id":"mock"}]}'); }
    const msgs = JSON.parse(body || "{}").messages ?? [];
    const toolMsgs = msgs.filter((m) => m.role === "tool");
    if (toolMsgs.length === 0) {
      return sse(res, [
        { ...base, choices: [{ index: 0, delta: { role: "assistant", tool_calls: [{ index: 0, id: "call_1", type: "function", function: { name: tool, arguments: args } }] }, finish_reason: null }] },
        { ...base, choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }] },
      ]);
    }
    const last = toolMsgs[toolMsgs.length - 1];
    const text = typeof last.content === "string" ? last.content : JSON.stringify(last.content);
    sse(res, [
      { ...base, choices: [{ index: 0, delta: { role: "assistant", content: "TOOL_RESULT<<" + text.slice(0, 400) + ">>" }, finish_reason: null }] },
      { ...base, choices: [{ index: 0, delta: {}, finish_reason: "stop" }] },
    ]);
  });
}).listen(port, "127.0.0.1", () => console.log(`mock listening ${port}`));
```

#### File: scripts/gate-run.sh

```bash
#!/usr/bin/env bash
# usage: gate-run.sh <agentDir> <workdir> <tool> <json-args>
# The mock port is read from <agentDir>/models.json (providers.mock.baseUrl).
set -euo pipefail
A=$1; W=$2; TOOL=$3; ARGS=$4
HERE=$(cd "$(dirname "$0")" && pwd)
PORT=$(node -e 'const m=require(process.argv[1]);console.log(new URL(m.providers.mock.baseUrl).port)' "$A/models.json")
LOG=$(mktemp)
MOCK_PORT=$PORT MOCK_TOOL=$TOOL MOCK_ARGS=$ARGS MOCK_LOG=$LOG node "$HERE/mock-openai.mjs" >/dev/null &
MP=$!
trap 'kill $MP 2>/dev/null || true; rm -f "$LOG"' EXIT
for _ in $(seq 1 50); do (echo > /dev/tcp/127.0.0.1/"$PORT") 2>/dev/null && break; sleep 0.1; done
cd "$W"
set +e
OUT=$(env -i PATH="$PATH" HOME="$HOME" PI_CODING_AGENT_DIR="$A" timeout "${GATE_TIMEOUT:-30}" pi --no-session --no-approve --mode json -p "go" 2>&1)
RC=$?
set -e
echo "rc=$RC"
printf '%s\n' "$OUT" | grep -o '"type":"tool_execution_end".\{0,400\}' | head -3
```

Then build a throwaway agent dir in `.scratch/gate-agent` by hand:

```bash
A=.scratch/gate-agent; W=.scratch/gate-work; mkdir -p "$A/extensions/pi-permission-system" "$W" && git -C "$W" init -q
cat > "$A/models.json" <<'EOF'
{"providers":{"mock":{"baseUrl":"http://127.0.0.1:18082/v1","api":"openai-completions","apiKey":"mock","models":[{"id":"mock-model"}]}}}
EOF
cat > "$A/settings.json" <<EOF
{"defaultProvider":"mock","defaultModel":"mock-model","quietStartup":true,"packages":["$HERETEK_TOOLS/pi-packages/node_modules/@gotgenes/pi-permission-system"]}
EOF
cat > "$A/extensions/pi-permission-system/config.json" <<'EOF'
{"promptTimeoutMs":10000,"permission":{"*":"deny","read":"allow","grep":"allow","find":"allow","ls":"allow","write":"allow","edit":"allow","bash":{"*":"deny","echo *":"allow"},"path":{"*":"allow","*.env":"deny"},"path_write":{"*":"deny","docs/*":"allow"},"external_directory":"deny"}}
EOF
chmod +x scripts/gate-run.sh
GATE_TIMEOUT=25 bash scripts/gate-run.sh "$A" "$W" write '{"path":"docs/ok.md","content":"x"}'
GATE_TIMEOUT=25 bash scripts/gate-run.sh "$A" "$W" write '{"path":"src/evil.ts","content":"x"}'
GATE_TIMEOUT=25 bash scripts/gate-run.sh "$A" "$W" write '{"path":"docs/../evil.md","content":"x"}'
ls "$W"     # evil.md IS there: this is the dot-dot bypass. Now add the guard and repeat:
node -e 'const f=process.argv[1],c=JSON.parse(require("fs").readFileSync(f));c.permission.path_write["*..*"]="deny";require("fs").writeFileSync(f,JSON.stringify(c))' "$A/extensions/pi-permission-system/config.json"
rm -f "$W/evil.md"; GATE_TIMEOUT=25 bash scripts/gate-run.sh "$A" "$W" write '{"path":"docs/../evil.md","content":"x"}'
```

**Acceptance (all from the output above):**
- `docs/ok.md` prints a `tool_execution_end` line containing `Successfully wrote to docs/ok.md`.
- `src/evil.ts` prints `Denied by policy: 'path_write' for tool 'write' for path 'src/evil.ts' (rule '*')`.
- Before the guard, `docs/../evil.md` is written and `ls` shows `evil.md`; after the guard the line contains
  `(rule '*..*')` and `evil.md` does not exist.
- Write the four outputs into `docs/NOTES.md`. If any differs, stop: the package version or Pi version is not the pinned one.

### M2: Fleet data checks

**Do:** create `scripts/check-fleet.mjs` verbatim.

#### File: scripts/check-fleet.mjs

```js
#!/usr/bin/env node
// Static invariants of fleet/fleet.yaml, fleet/mcp-servers.yaml and the generated tree. Exit 1 on any failure.
import fs from "node:fs";
import path from "node:path";
import YAML from "yaml";

const fail = [];
const check = (ok, msg) => { if (!ok) fail.push(msg); };
const fleet = YAML.parse(fs.readFileSync("fleet/fleet.yaml", "utf8"));
const mcp = YAML.parse(fs.readFileSync("fleet/mcp-servers.yaml", "utf8")).servers;
const roles = Object.keys(fleet.roles);

check(roles.length === 51, `expected 51 roles, got ${roles.length}`);
check(fleet.rigs.length === 7, `expected 7 static rigs, got ${fleet.rigs.length}`);
const placed = fleet.rigs.flatMap((r) => r.pods.flatMap((p) => p.members));
check(placed.length === 51 && new Set(placed).size === 51, `each role must sit in exactly one static seat (${placed.length} seats)`);
for (const id of roles) check(placed.includes(id), `role ${id} has no seat`);

const KINDS = new Set(["delegates_to", "spawned_by", "can_observe", "collaborates_with", "escalates_to"]);
for (const rig of fleet.rigs) {
  const members = new Map(rig.pods.flatMap((p) => p.members.map((m) => [`${p.id}.${m}`, p.id])));
  for (const p of rig.pods) {
    check(p.members[0] === p.lead, `${rig.id}/${p.id}: lead must be the first member`);
    for (const e of p.edges) {
      check(KINDS.has(e.kind), `${rig.id}/${p.id}: bad edge kind ${e.kind}`);
      check(p.members.includes(e.from) && p.members.includes(e.to), `${rig.id}/${p.id}: edge ${e.from}->${e.to} leaves the pod`);
    }
  }
  for (const e of rig.edges) {
    check(KINDS.has(e.kind), `${rig.id}: bad edge kind ${e.kind}`);
    check(members.has(e.from) && members.has(e.to), `${rig.id}: edge ${e.from}->${e.to} must be pod.member inside this rig`);
  }
}
for (const [id, r] of Object.entries(fleet.roles)) {
  const seat = fleet.rigs.find((x) => x.id === r.rig)?.pods.find((p) => p.id === r.pod);
  check(seat?.members.includes(id), `${id}: rig/pod fields disagree with the rigs list`);
  check(r.session === `${r.pod}-${id}@${r.rig}`, `${id}: session must be <pod>-<member>@<rig>`);
  check(["builtin:locked", "builtin:standard"].includes(r.permission_policy), `${id}: policy ${r.permission_policy} not allowed`);
  check(["high", "xhigh", "medium"].includes(r.thinking), `${id}: thinking ${r.thinking} not supported by the model`);
  for (const b of r.mcp) check(mcp[b.server], `${id}: MCP server ${b.server} missing from fleet/mcp-servers.yaml`);
  for (const g of r.permissions.path_write) check(!g.includes("..") && !g.startsWith("/"), `${id}: path_write ${g} must be repo-relative`);
  for (const p of r.permissions.bash_allow) {
    check(!/^(curl|wget|sh|bash|python3? -c|node -e|eval|sudo)\b/.test(p), `${id}: bash allow ${p} is a general interpreter or network tool`);
    check(p !== "*", `${id}: bash allow * is forbidden`);
  }
  const base = path.join("specs/agents", r.domain, id);
  if (fs.existsSync("specs/agents")) {
    check(fs.existsSync(path.join(base, "agent.yaml")), `${id}: missing ${base}/agent.yaml`);
    check(fs.existsSync(path.join(base, "guidance/role.md")), `${id}: missing ${base}/guidance/role.md`);
    for (const s of r.skills.role_local) check(fs.existsSync(path.join(base, "skills", s.id, "SKILL.md")), `${id}: missing role skill ${s.id}`);
    for (const s of [...r.skills.openrig_core, ...r.skills.shared.map((x) => x.id)])
      check(fs.existsSync(path.join("specs/agents/_shared/skills", s, "SKILL.md")), `${id}: missing shared skill ${s}`);
  }
}
for (const [name, s] of Object.entries(mcp)) {
  for (const v of [...Object.values(s.env ?? {}), ...Object.values(s.headers ?? {})])
    check(typeof v !== "string" || !/(ghp_|github_pat_|sk-|AKIA|xox[bp]-)/.test(v), `${name}: literal secret-looking value`);
  for (const x of s.args ?? []) check(!String(x).startsWith("!"), `${name}: !command in args is never expanded by Pi`);
  check(!/latest/.test(s.pin ?? ""), `${name}: floating pin ${s.pin}`);
}
const tracked = fs.existsSync("rigs") ? fs.readdirSync("rigs") : [];
for (const r of tracked) {
  const f = path.join("rigs", r, "rig.yaml");
  if (!fs.existsSync(f)) continue;
  const text = fs.readFileSync(f, "utf8");
  check(!/^\s*env:/m.test(text), `${f}: env: is not secret storage and is not used by this fleet`);
  check(!/builtin:(yolo|open)/.test(text), `${f}: yolo/open policies are forbidden`);
  check(!/runtime: (?!pi\b)/.test(text), `${f}: every seat must be runtime: pi`);
}
if (fail.length) { for (const m of fail) console.error(`FAIL ${m}`); process.exit(1); }
console.log(`check-fleet: OK (${roles.length} roles, ${fleet.rigs.length} static rigs, ${Object.keys(mcp).length} MCP servers)`);
```

**Acceptance:**
- `node scripts/check-fleet.mjs` prints `check-fleet: OK (51 roles, 7 static rigs, 20 MCP servers)` (before
  `specs/` exists it skips the spec-file checks).
- Sabotage proof (do it in `.scratch`, not in the repo): copy `fleet/` to `.scratch/bad/fleet/`, append
  `curl *` to `roles.appsec-engineer.permissions.bash_allow` and add an edge of kind `reviews` to the first rig, then
  run `node ../../scripts/check-fleet.mjs` from `.scratch/bad`. It must
  exit 1 and print `FAIL executive-and-architecture: bad edge kind reviews` and
  `FAIL appsec-engineer: bash allow curl * is a general interpreter or network tool`.

### M3: Seat renderer

**Do:** create `scripts/render-seat.mjs` and `tests/render-seat.test.mjs` verbatim.

#### File: scripts/render-seat.mjs

```js
#!/usr/bin/env node
// Render one Pi seat's agent dir (auth.json, settings.json, mcp.json, AGENTS.md,
// extensions/pi-permission-system/config.json) from fleet/fleet.yaml + fleet/mcp-servers.yaml.
// Run it BEFORE `rig up` / `rig expand` / `rig add`: openrig keeps these files and only adds
// models-store.json and skills/.
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { parseArgs } from "node:util";
import YAML from "yaml";

const USAGE = `usage: render-seat.mjs --role <role-id> --rig <rig-id> --pod <pod-id> [options]
  --member <id>          member id in the rig (default: the role id)
  --fleet <file>         default fleet/fleet.yaml
  --mcp <file>           default fleet/mcp-servers.yaml
  --charter <file>       default specs/agents/<domain>/<role>/guidance/role.md
  --out <dir>            default $OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent
  --model-provider <p>   default opencode-go (tests use: mock)
  --model-id <id>        default muse-spark-1.3-contributor (tests use: mock-model)
  --allow-missing-secrets  write servers whose secret files are missing with "enabled": false
  --dry-run              print the files as JSON instead of writing them
  --help`;

const { values: a } = parseArgs({
  options: {
    role: { type: "string" }, rig: { type: "string" }, pod: { type: "string" }, member: { type: "string" },
    fleet: { type: "string", default: "fleet/fleet.yaml" }, mcp: { type: "string", default: "fleet/mcp-servers.yaml" },
    charter: { type: "string" }, out: { type: "string" },
    "model-provider": { type: "string", default: "opencode-go" },
    "model-id": { type: "string", default: "muse-spark-1.3-contributor" },
    "allow-missing-secrets": { type: "boolean", default: false },
    "dry-run": { type: "boolean", default: false }, help: { type: "boolean", default: false },
  },
});
if (a.help) { console.log(USAGE); process.exit(0); }
for (const k of ["role", "rig", "pod"]) if (!a[k]) { console.error(`error: --${k} is required\n${USAGE}`); process.exit(2); }

const die = (msg) => { console.error(`error: ${msg}`); process.exit(2); };
const home = os.homedir();
const OPENRIG_HOME = process.env.OPENRIG_HOME ?? path.join(home, ".openrig");
const TOOLS = path.resolve(process.env.HERETEK_TOOLS ?? path.join(home, ".local/share/heretek-rigs/tools"));
const SECRETS = path.resolve(process.env.HERETEK_SECRETS ?? path.join(home, ".config/heretek-rigs/secrets"));
const PPS = path.join(TOOLS, "pi-packages/node_modules/@gotgenes/pi-permission-system");

const fleet = YAML.parse(fs.readFileSync(a.fleet, "utf8"));
const catalog = YAML.parse(fs.readFileSync(a.mcp, "utf8")).servers;
const role = fleet.roles[a.role] ?? die(`unknown role ${a.role}`);
const member = a.member ?? a.role;
for (const id of [a.pod, member]) if (/[.@]/.test(id)) die(`pod/member ids must not contain '.' or '@': ${id}`);
const session = `${a.pod}-${member}@${a.rig}`;
const seatDir = path.join(OPENRIG_HOME, "state/pi", session);
const out = path.resolve(a.out ?? path.join(seatDir, "agent"));
const charterFile = a.charter ?? path.join("specs/agents", role.domain, a.role, "guidance/role.md");

function secretOk(file) {
  const p = path.join(SECRETS, file);
  if (!fs.existsSync(p)) return false;
  const mode = fs.statSync(p).mode & 0o777;
  if (mode & 0o077) die(`${p} is mode ${mode.toString(8)}; run: chmod 600 ${p}`);
  return true;
}
const subst = (v) => (typeof v === "string"
  ? v.replaceAll("@TOOLS@", TOOLS).replaceAll("@SECRETS@", SECRETS).replaceAll("@SEAT@", seatDir) : v);

// 1. auth.json: command-backed key; the key file itself never leaves $HERETEK_SECRETS.
const files = {};
if (a["model-provider"] === "opencode-go") {
  if (!secretOk("opencode-go.key")) die(`missing ${path.join(SECRETS, "opencode-go.key")} (chmod 600)`);
  files["auth.json"] = { "opencode-go": { type: "api_key", key: `!cat ${path.join(SECRETS, "opencode-go.key")}` } };
}

// 2. mcp.json
const mcpServers = {};
const mcpAllow = { "*": "deny" };
let deferred = false;
for (const b of role.mcp) {
  const s = catalog[b.server] ?? die(`role ${a.role} binds unknown MCP server ${b.server}`);
  const need = s.required_secrets ?? [];
  const missing = need.filter((f) => !secretOk(f));
  const entry = { description: subst(s.description).replace("{toolset}", b.toolset ?? ""), exposure: s.exposure };
  if (s.transport === "http") {
    entry.url = s.url_template.replace("{toolset}", b.toolset ?? "repos");
    entry.headers = Object.fromEntries(Object.entries(s.headers ?? {}).map(([k, v]) => [k, subst(v)]));
  } else {
    entry.command = subst(s.command);
    entry.args = (s.args ?? []).map(subst);
    if (entry.args.some((x) => x.startsWith("!"))) die(`${b.server}: Pi never expands !command in args`);
    if (s.env) entry.env = Object.fromEntries(Object.entries(s.env).map(([k, v]) => [k, subst(v)]));
  }
  for (const f of s.optional_secrets ?? []) {
    if (!secretOk(f)) for (const [k, v] of Object.entries(entry.env ?? {})) if (v.includes(f)) delete entry.env[k];
  }
  if (missing.length) {
    if (!a["allow-missing-secrets"]) die(`${b.server} needs ${missing.map((f) => path.join(SECRETS, f)).join(", ")}`);
    entry.enabled = false;
    console.error(`warn: ${session}: ${b.server} disabled, missing secrets: ${missing.join(", ")}`);
  }
  mcpServers[b.server] = entry;
  mcpAllow[b.server] = "allow";
  if (s.exposure === "deferred") deferred = true;
}
files["mcp.json"] = { mcpServers };

// 3. settings.json
const tools = ["read", "grep", "find", "ls", "bash", "edit", "write"];
if (deferred) tools.push("tool_search");
files["settings.json"] = {
  defaultProvider: a["model-provider"],
  defaultModel: a["model-id"],
  defaultThinkingLevel: role.thinking,
  defaultTools: tools,
  packages: [PPS],
  quietStartup: true,
};

// 4. pi-permission-system config. Last matching rule wins inside each map, so guards go LAST.
const pathWrite = { "*": "deny" };
for (const g of role.permissions.path_write) pathWrite[g] = "allow";
Object.assign(pathWrite, { ".git/*": "deny", "*/.git/*": "deny", "AGENTS.md": "deny", ".pi/*": "deny",
  ".agents/*": "deny", "*..*": "deny" });
const bash = { "*": "deny" };
for (const p of role.permissions.bash_allow) bash[p] = "allow";
const permission = {
  "*": "deny",
  read: "allow", grep: "allow", find: "allow", ls: "allow", write: "allow", edit: "allow",
  bash,
  path: { "*": "allow", "*.env": "deny", "*.env.*": "deny", "*.env.example": "allow", "*.pem": "deny",
    "*.key": "deny", "*id_rsa*": "deny", "*/secrets/*": "deny", "*..*": "deny" },
  path_write: pathWrite,
  mcp: mcpAllow,
  external_directory: "deny",
};
if (deferred) permission.tool_search = "allow";
files["extensions/pi-permission-system/config.json"] = { promptTimeoutMs: 60000, permission };

// 5. AGENTS.md: the role charter plus this seat's addresses. Never use guidance_merge (shared-cwd collision).
if (!fs.existsSync(charterFile)) die(`missing charter ${charterFile}`);
const esc = role.reports_to;
const addr = [
  `## Seat`,
  ``,
  `- You are \`${a.role}\` in seat \`${session}\` (rig \`${a.rig}\`, pod \`${a.pod}\`).`,
  `- Model: ${a["model-provider"]}/${a["model-id"]}, thinking ${role.thinking}. Recorded policy: ${role.permission_policy}.`,
  esc ? `- Escalate with: \`rig send ${esc.address} "<message>"\` (${esc.role}${esc.same_rig ? ", same rig" : ", other rig"}).` : `- You are the top of the escalation chain; escalate to the human.`,
  `- Writable paths: ${role.permissions.path_write.map((g) => `\`${g}\``).join(", ") || "none"}. Everything else is read-only.`,
  ``,
].join("\n");
files["AGENTS.md"] = fs.readFileSync(charterFile, "utf8").trimEnd() + "\n\n" + addr;

if (a["dry-run"]) { console.log(JSON.stringify(files, null, 2)); process.exit(0); }
for (const [rel, body] of Object.entries(files)) {
  const p = path.join(out, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, typeof body === "string" ? body : JSON.stringify(body, null, 2) + "\n", { mode: 0o600 });
  fs.chmodSync(p, 0o600);
}
console.log(`rendered ${session} -> ${out}`);
```

#### File: tests/render-seat.test.mjs

```js
// node --test tests/ : render-seat.mjs output contract (no daemon, no network).
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const secrets = fs.mkdtempSync(path.join(os.tmpdir(), "hr-secrets-"));
fs.chmodSync(secrets, 0o700);
fs.writeFileSync(path.join(secrets, "opencode-go.key"), "dummy", { mode: 0o600 });
const env = { ...process.env, HERETEK_SECRETS: secrets, HERETEK_TOOLS: "/opt/hr-tools", OPENRIG_HOME: "/tmp/hr-openrig" };
const render = (...args) => JSON.parse(execFileSync(process.execPath,
  ["scripts/render-seat.mjs", ...args, "--dry-run", "--allow-missing-secrets"], { env, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }));

test("appsec-engineer: auth is a command-backed key, never a literal", () => {
  const f = render("--role", "appsec-engineer", "--rig", "defensive-sec-and-red-team", "--pod", "blue");
  assert.deepEqual(f["auth.json"], { "opencode-go": { type: "api_key", key: `!cat ${path.join(secrets, "opencode-go.key")}` } });
});

test("appsec-engineer: settings pin model, thinking and the permission package", () => {
  const s = render("--role", "appsec-engineer", "--rig", "defensive-sec-and-red-team", "--pod", "blue")["settings.json"];
  assert.equal(s.defaultProvider, "opencode-go");
  assert.equal(s.defaultModel, "muse-spark-1.3-contributor");
  assert.equal(s.defaultThinkingLevel, "high");
  assert.deepEqual(s.packages, ["/opt/hr-tools/pi-packages/node_modules/@gotgenes/pi-permission-system"]);
  assert.ok(s.defaultTools.includes("tool_search"), "deferred MCP needs tool_search");
});

test("appsec-engineer: permission config fails closed and ends path_write with the dot-dot guard", () => {
  const c = render("--role", "appsec-engineer", "--rig", "defensive-sec-and-red-team", "--pod", "blue")["extensions/pi-permission-system/config.json"];
  assert.equal(c.permission["*"], "deny");
  assert.equal(c.permission.bash["*"], "deny");
  assert.equal(c.permission.external_directory, "deny");
  assert.equal(c.promptTimeoutMs, 60000);
  const keys = Object.keys(c.permission.path_write);
  assert.equal(keys[0], "*");
  assert.equal(keys.at(-1), "*..*");
  assert.equal(c.permission.path_write["docs/security/advisories/*"], "allow");
  assert.deepEqual(c.permission.mcp, { "*": "deny", semgrep: "allow", "codebase-memory": "allow" });
  assert.ok(!JSON.stringify(c).includes('"ask"'), "no ask rules: a seat has nobody to answer");
});

test("product-director: github is read-only on its toolset and disabled without a PAT", () => {
  const m = render("--role", "product-director", "--rig", "executive-and-architecture", "--pod", "exec")["mcp.json"].mcpServers;
  assert.equal(m.github.url, "https://api.githubcopilot.com/mcp/x/issues/readonly");
  assert.equal(m.github.enabled, false);
  assert.match(m.github.headers.Authorization, /^!echo Bearer \$\(cat .*github\.pat\)$/);
});

test("missing secret without --allow-missing-secrets is a hard error", () => {
  const r = spawnSync(process.execPath, ["scripts/render-seat.mjs", "--role", "product-director", "--rig",
    "executive-and-architecture", "--pod", "exec", "--dry-run"], { env, encoding: "utf8" });
  assert.equal(r.status, 2);
  assert.match(r.stderr, /github needs .*github\.pat/);
});

test("a world-readable key file is refused", () => {
  fs.chmodSync(path.join(secrets, "opencode-go.key"), 0o644);
  const r = spawnSync(process.execPath, ["scripts/render-seat.mjs", "--role", "appsec-engineer", "--rig",
    "defensive-sec-and-red-team", "--pod", "blue", "--dry-run"], { env, encoding: "utf8" });
  fs.chmodSync(path.join(secrets, "opencode-go.key"), 0o600);
  assert.equal(r.status, 2);
  assert.match(r.stderr, /is mode 644; run: chmod 600/);
});

test("ids with dots are refused", () => {
  const r = spawnSync(process.execPath, ["scripts/render-seat.mjs", "--role", "appsec-engineer", "--rig", "x",
    "--pod", "blue.team", "--dry-run"], { env, encoding: "utf8" });
  assert.equal(r.status, 2);
  assert.match(r.stderr, /must not contain/);
});
```

Algorithm of `render-seat.mjs`, so you can debug it: (1) load the role from `fleet/fleet.yaml`; (2) refuse ids with
`.`/`@`; (3) `auth.json` = command-backed key, refusing a missing key or one with group/other permission bits;
(4) `mcp.json` = one entry per bound server from `fleet/mcp-servers.yaml` with `@TOOLS@`/`@SECRETS@`/`@SEAT@`
replaced by absolute paths, GitHub URL built per toolset, servers with missing required secrets refused or (with
`--allow-missing-secrets`) written with `enabled: false`; (5) `settings.json` with the model, thinking level, tool
list (+`tool_search` when any server is deferred) and the local package path; (6) permission config: top-level
deny, read/search/write/edit allowed as tools, `bash` and `path_write` as deny-all plus the role's allows plus the
guards **last**, `path` secret denies, `mcp` deny-all plus the bound servers, `external_directory` deny,
`promptTimeoutMs` 60000; (7) `AGENTS.md` = `specs/agents/<domain>/<role>/guidance/role.md` plus a seat block with
the escalation address; (8) files written mode 0600.

**Acceptance:**
- `node scripts/render-seat.mjs --help` prints the usage starting `usage: render-seat.mjs --role`.
- With a throwaway charter (the real ones appear in M4):
  `echo "# t" > .scratch/charter.md && node scripts/render-seat.mjs --role appsec-engineer --rig defensive-sec-and-red-team --pod blue --charter .scratch/charter.md --model-provider mock --model-id mock-model --dry-run | jq -r '."extensions/pi-permission-system/config.json".permission.path_write | keys_unsorted | last'`
  prints `*..*`. (Use `keys_unsorted`: jq's `keys` sorts and hides the order that matters.)
- The unit tests run in M4, once the charters exist.

### M4: Generate the specs and rigs

**Do:** create `scripts/gen-specs.mjs` verbatim and run it.

#### File: scripts/gen-specs.mjs

```js
#!/usr/bin/env node
// Generate specs/agents/** (52 AgentSpecs incl. _shared), rigs/*/rig.yaml, the omni fragments and
// fleet/skills-lock.json from fleet/fleet.yaml and pinned local checkouts. Never touches the network.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import { parseArgs } from "node:util";
import YAML from "yaml";

const USAGE = `usage: gen-specs.mjs --crew <Heretek-Crew checkout> --vendor <dir of pinned clones> --openrig-core <skills dir> [--out .] [--dry-run]`;
const { values: a } = parseArgs({ options: {
  crew: { type: "string" }, vendor: { type: "string" }, "openrig-core": { type: "string" },
  out: { type: "string", default: "." }, "dry-run": { type: "boolean", default: false }, help: { type: "boolean", default: false },
} });
if (a.help) { console.log(USAGE); process.exit(0); }
const die = (m) => { console.error(`error: ${m}`); process.exit(2); };
for (const k of ["crew", "vendor", "openrig-core"]) if (!a[k]) die(`--${k} is required\n${USAGE}`);

const OUT = path.resolve(a.out);
const fleet = YAML.parse(fs.readFileSync(path.join(OUT, "fleet/fleet.yaml"), "utf8"));
const MODEL = fleet.model.ref;

// Pinned sources. A checkout at any other commit is refused.
const PINS = {
  "heretek-crew": { dir: path.resolve(a.crew), sha: "5ffb1fc" },
  superpowers: { dir: path.join(a.vendor, "obra_superpowers"), sha: "bb92a77", repo: "obra/superpowers" },
  tob: { dir: path.join(a.vendor, "trailofbits_skills"), sha: "5c99c03", repo: "trailofbits/skills" },
  sentry: { dir: path.join(a.vendor, "getsentry_skills"), sha: "f57ada2", repo: "getsentry/skills" },
  anthropic: { dir: path.join(a.vendor, "anthropics_skills"), sha: "dbd4588", repo: "anthropics/skills" },
  vercel: { dir: path.join(a.vendor, "vercel-labs_agent-skills"), sha: "063bee9", repo: "vercel-labs/agent-skills" },
};
for (const [k, p] of Object.entries(PINS)) {
  const head = execFileSync("git", ["-C", p.dir, "rev-parse", "--short=7", "HEAD"], { encoding: "utf8" }).trim();
  if (head !== p.sha) die(`${k} checkout ${p.dir} is at ${head}, expected ${p.sha}`);
}
const CORE_DIR = path.resolve(a["openrig-core"]);
const CORE_LICENSE = path.resolve(CORE_DIR, "../../../../../LICENSE"); // @openrig/cli/LICENSE (Apache-2.0)
if (!fs.existsSync(CORE_LICENSE)) die(`missing ${CORE_LICENSE}`);

const writes = new Map(); // abs path -> string | {copyDir}
const put = (rel, body) => writes.set(path.join(OUT, rel), body);
const yamlOut = (o) => YAML.stringify(o, { lineWidth: 0 });

function treeHash(dir) {
  const h = crypto.createHash("sha256");
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).sort((x, y) => x.name.localeCompare(y.name)).forEach((e) => {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p); else { h.update(path.relative(dir, p) + "\0"); h.update(fs.readFileSync(p)); }
  });
  walk(dir);
  return "sha256:" + h.digest("hex");
}
function findSkill(src, id) {
  const p = PINS[src];
  if (src === "tob") {
    const plugins = path.join(p.dir, "plugins");
    for (const pl of fs.readdirSync(plugins)) {
      const d = path.join(plugins, pl, "skills", id);
      if (fs.existsSync(path.join(d, "SKILL.md"))) return d;
    }
    return die(`tob skill ${id} not found`);
  }
  if (src === "heretek-crew") {
    for (const r of fs.readdirSync(path.join(p.dir, "roles"))) {
      const d = path.join(p.dir, "roles", r, ".opencode/skills", id);
      if (fs.existsSync(path.join(d, "SKILL.md"))) return d;
    }
    return die(`heretek-crew skill ${id} not found`);
  }
  const d = path.join(p.dir, "skills", id);
  if (!fs.existsSync(path.join(d, "SKILL.md"))) die(`${src} skill ${id} not found at ${d}`);
  return d;
}
function rootLicense(src) {
  for (const n of ["LICENSE", "LICENSE.md", "LICENSE.txt"]) {
    const f = path.join(PINS[src].dir, n);
    if (fs.existsSync(f)) return f;
  }
  return null;
}

// ---- shared skill pool (heretek-shared) ----
const lock = { version: 1, skills: {} };
const shared = new Map(); // id -> {src, dir}
const addShared = (id, src, dir) => {
  const prev = shared.get(id);
  if (prev && prev.src !== src) die(`skill id collision: ${id} from ${prev.src} and ${src}`);
  shared.set(id, { src, dir });
};
for (const r of Object.values(fleet.roles)) {
  for (const id of r.skills.openrig_core) addShared(id, "openrig-core", path.join(CORE_DIR, id));
  for (const s of r.skills.shared) addShared(s.id, s.source, findSkill(s.source, s.id));
}
for (const [id, { src, dir }] of [...shared].sort()) {
  if (!fs.existsSync(path.join(dir, "SKILL.md"))) die(`missing ${dir}/SKILL.md`);
  const rel = `specs/agents/_shared/skills/${id}`;
  put(rel, { copyDir: dir });
  const hasLicense = fs.readdirSync(dir).some((n) => /^LICEN[CS]E/i.test(n));
  let licenseFile = null;
  if (!hasLicense) {
    licenseFile = src === "openrig-core" ? CORE_LICENSE : (PINS[src]?.repo ? rootLicense(src) : null);
    if (licenseFile) put(`${rel}/LICENSE`, { copyFile: licenseFile });
  }
  lock.skills[id] = {
    source: src === "openrig-core" ? "npm:@openrig/cli@0.6.11 daemon/assets/plugins/openrig-core/skills" : `${PINS[src].repo ?? "Heretek-AI/Heretek-Crew"}@${PINS[src].sha}`,
    path: src === "openrig-core" ? id : path.relative(PINS[src].dir, dir),
    tree: treeHash(dir),
    license_file: hasLicense ? "in-tree" : (licenseFile ? "LICENSE (copied from source root)" : "none (see SKILL.md frontmatter)"),
  };
}
put("specs/agents/_shared/agent.yaml", yamlOut({
  name: "heretek-shared", version: "1.0", description: "Heretek fleet shared skill pool (vendored, pinned)",
  resources: { skills: [...shared.keys()].sort().map((id) => ({ id, path: `skills/${id}` })) },
  profiles: {},
}));

// ---- one AgentSpec per role ----
function charter(id, r) {
  const src = fs.readFileSync(path.join(PINS["heretek-crew"].dir, "roles", id, "AGENTS.md"), "utf8");
  const sec = (n) => { const m = src.match(new RegExp(`^## ${n}\\. [^\\n]*\\n[\\s\\S]*?(?=^## \\d+\\. |(?![\\s\\S]))`, "m")); return m ? m[0].trimEnd() : die(`${id}: section ${n} missing`); };
  const wake = (src.match(/^- \*\*Catalog wake policy\*\*: (.*)$/m) ?? [, "on assignment"])[1];
  const fix = (s) => s.replaceAll("Paperclip ticket", "openrig queue item").replaceAll("via Paperclip", "via `rig queue` / `rig send`").replaceAll("Paperclip", "openrig");
  const mcp = r.mcp.length ? r.mcp.map((b) => `- \`${b.server}\`${b.toolset ? ` (GitHub \`${b.toolset}\` toolset, read-only)` : ""}: tools are named \`mcp__${b.server.replaceAll("-", "_")}__<tool>\`.`).join("\n") : "- None. Use the built-in read/grep/find/ls tools and the bash allow-list.";
  const skills = [...r.skills.openrig_core, ...r.skills.shared.map((s) => s.id), ...r.skills.role_local.map((s) => s.id)].map((s) => `- \`${s}\``).join("\n");
  const esc = r.reports_to ? `\`rig send ${r.reports_to.address} "<message>"\`` : "the human operator (`messaging-the-human` skill)";
  return [
    `# ${r.title} (\`${id}\`): Agent Charter`,
    ``,
    `> Department: ${r.department}. Rig \`${r.rig}\`, pod \`${r.pod}\`${r.pod_lead ? " (pod lead)" : ""}. Ported from Heretek-AI/Heretek-Crew@5ffb1fc \`roles/${id}/AGENTS.md\`.`,
    ``,
    fix(sec(1)), ``, fix(sec(2)), ``, fix(sec(3)), ``,
    `## 4. MCP Servers & Tool Access`, ``, mcp, ``,
    `## 5. Skills`, ``, `Load a skill by reading its SKILL.md when the task matches its description.`, ``, skills, ``,
    `## 6. Coordination on openrig`, ``,
    `- Work arrives as openrig queue items and \`rig send\` messages; follow \`queue-handoff\` and \`mission-slice-sop\`.`,
    `- Escalate blockers to ${esc}.`,
    `- Writes are confined to: ${r.permissions.path_write.map((g) => `\`${g}\``).join(", ") || "nothing (read-only seat)"}. A denial from pi-permission-system is final: hand off, never work around it.`,
    `- Verification commands you may run: ${r.permissions.bash_allow.filter((p) => !p.startsWith("rig ") && !p.startsWith("git ")).map((p) => `\`${p}\``).join(", ") || "read-only git only"}.`,
    `- Wake policy: ${wake}.`,
    ``,
    `## 7. Non-Negotiables`, ``,
    `- Zero stubs: no placeholder functions, no dummy returns, no swallowed errors.`,
    `- Fail closed: on an invalid state, stop with a descriptive error.`,
    `- Never read or print secrets (.env, keys, tokens); never pass secrets on a command line.`,
    `- Report completion with artifact paths and the exact verification commands and their results.`,
    ``,
  ].join("\n");
}
const ref = (id) => `heretek-shared:${id}`;
for (const [id, r] of Object.entries(fleet.roles)) {
  const base = `specs/agents/${r.domain}/${id}`;
  for (const s of r.skills.role_local) put(`${base}/skills/${s.id}`, { copyDir: findSkill("heretek-crew", s.id) });
  put(`${base}/guidance/role.md`, charter(id, r));
  put(`${base}/startup/context.md`, `You are ${id} (${r.title}). Your charter and seat address are in your system prompt. Run \`rig whoami\` and check your queue before starting work.\n`);
  const spec = {
    name: id, version: "1.0", description: r.title,
    defaults: { runtime: "pi", model: MODEL },
    imports: [{ ref: "local:../../_shared" }],
    profiles: { default: { uses: {
      skills: [...r.skills.openrig_core.map(ref), ...r.skills.shared.map((s) => ref(s.id)), ...r.skills.role_local.map((s) => s.id)],
      guidance: [], subagents: [], plugins: [], runtime_resources: [],
    } } },
    resources: r.skills.role_local.length ? { skills: r.skills.role_local.map((s) => ({ id: s.id, path: `skills/${s.id}` })) } : {},
    startup: { files: [{ path: "startup/context.md", delivery_hint: "send_text", required: true }], actions: [] },
  };
  put(`${base}/agent.yaml`, yamlOut(spec));
}

// ---- rigs ----
const CULTURE = [
  "# Heretek fleet culture", "",
  "- Evidence over assertion: every claim of done carries the command that proves it and its output.",
  "- Zero stubs, fail closed, least privilege. A permission denial is a hand-off, never a puzzle to get around.",
  "- Small slices: one queue item, one verifiable outcome. Hand off with `rig queue` and say what is next.",
  "- Secrets never appear in messages, files, transcripts or command lines.", "",
].join("\n");
const member = (id) => {
  const r = fleet.roles[id];
  return { id, agent_ref: `local:../../specs/agents/${r.domain}/${id}`, profile: "default", runtime: "pi",
    cwd: ".", permission_policy: r.permission_policy };
};
const podOut = (p) => ({ id: p.id, label: p.label, members: p.members.map(member), edges: p.edges });
for (const rig of fleet.rigs) {
  put(`rigs/${rig.id}/rig.yaml`, yamlOut({ version: "0.2", name: rig.id, summary: rig.title, culture_file: "CULTURE.md",
    docs: [{ path: "README.md" }], pods: rig.pods.map(podOut), edges: rig.edges }));
  put(`rigs/${rig.id}/CULTURE.md`, CULTURE);
  put(`rigs/${rig.id}/README.md`, `# ${rig.title}\n\nSeats: ${rig.pods.flatMap((p) => p.members).join(", ")}.\nSeed seats with scripts/seed-rig.sh ${rig.id} before rig up.\n`);
}
const omni = fleet.omni;
put(`rigs/${omni.id}/rig.yaml`, yamlOut({ version: "0.2", name: omni.id, summary: omni.title, culture_file: "CULTURE.md",
  docs: [{ path: "README.md" }], pods: [podOut(omni.core_pod)], edges: [] }));
put(`rigs/${omni.id}/CULTURE.md`, CULTURE);
put(`rigs/${omni.id}/README.md`, `# ${omni.title}\n\nCore pod: ${omni.core_pod.members.join(", ")}. Attach pods with \`rig expand ${omni.id} pods/<pod>.yaml --rig-root "$PWD"\` and single seats with \`rig add ${omni.id} <pod> members/<role>.yaml --rig-root "$PWD"\`, after seeding each new seat.\n`);
for (const rig of fleet.rigs) for (const p of rig.pods) put(`rigs/${omni.id}/pods/${p.id}.yaml`, yamlOut(podOut(p)));
for (const id of Object.keys(fleet.roles)) put(`rigs/${omni.id}/members/${id}.yaml`, yamlOut(member(id)));
put("fleet/skills-lock.json", JSON.stringify(lock, null, 2) + "\n");

// ---- write ----
if (a["dry-run"]) { for (const k of [...writes.keys()].sort()) console.log(path.relative(OUT, k)); process.exit(0); }
for (const dir of ["specs/agents", `rigs`]) fs.rmSync(path.join(OUT, dir), { recursive: true, force: true });
for (const [p, body] of writes) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  if (typeof body === "string") fs.writeFileSync(p, body);
  else if (body.copyDir) fs.cpSync(body.copyDir, p, { recursive: true, dereference: true });
  else fs.copyFileSync(body.copyFile, p);
}
console.log(`wrote ${writes.size} entries: ${Object.keys(fleet.roles).length} roles, ${shared.size} shared skills, ${fleet.rigs.length + 1} rigs`);
```

```bash
node scripts/gen-specs.mjs --crew /home/john/Projects/Heretek-Crew --vendor .scratch/vendor --openrig-core "$OPENRIG_CORE"
```

**Acceptance:**
- It prints `wrote 418 entries: 51 roles, 62 shared skills, 8 rigs` (the planning run's exact line). If the number
  differs, list what differs in NOTES before continuing.
- `find specs -name agent.yaml | wc -l` prints `52`; `ls specs/agents/_shared/skills | wc -l` prints `62`.
- `node scripts/check-fleet.mjs` prints `check-fleet: OK ...` (now including the spec-file checks).
- `git status --porcelain specs rigs fleet/skills-lock.json` shows only additions; running the generator a second
  time produces no diff (`git diff --stat` empty after `git add`).
- `grep -rl "Paperclip" specs/agents/*/*/guidance/role.md | wc -l` prints `0`.
- `node --test tests/*.test.mjs` prints `# pass 7` and `# fail 0`. (Node 22: `node --test tests/` fails with
  `Cannot find module .../tests`; always pass the glob.)

### M5: Gate every role

**Do:** create `scripts/gate-role.sh` verbatim and `chmod +x scripts/*.sh`.

#### File: scripts/gate-role.sh

```bash
#!/usr/bin/env bash
# Gate-test one role's rendered pi-permission-system config with the mock model.
# usage: scripts/gate-role.sh <role-id>    (run from the repo root; needs pi on PATH)
set -euo pipefail
if [[ "${1:-}" == "--help" || $# -ne 1 ]]; then echo "usage: scripts/gate-role.sh <role-id>"; exit 2; fi
ROLE=$1
ROOT=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
PORT=$((18100 + RANDOM % 800))
read -r RIG POD FIRST < <(node -e '
  const Y=require("yaml"),fs=require("fs");const f=Y.parse(fs.readFileSync("fleet/fleet.yaml","utf8"));
  const r=f.roles[process.argv[1]]; if(!r){console.error("unknown role");process.exit(2)}
  const g=(r.permissions.path_write[0]||"").replace(/\*.*$/,"");
  console.log(r.rig, r.pod, g===""?"-":g);' "$ROLE")
A="$TMP/agent"; W="$TMP/work"
mkdir -p "$W" && git -C "$W" init -q
HERETEK_SECRETS="$TMP/secrets" node scripts/render-seat.mjs --role "$ROLE" --rig "$RIG" --pod "$POD" \
  --model-provider mock --model-id mock-model --out "$A" --allow-missing-secrets >/dev/null 2>"$TMP/render.err"
printf '{"providers":{"mock":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"mock","models":[{"id":"mock-model"}]}}}\n' "$PORT" > "$A/models.json"
fails=0
expect() { # expect <allow|deny> <tool> <json-args> <label>
  local want=$1 tool=$2 args=$3 label=$4 out
  out=$(bash "$ROOT/scripts/gate-run.sh" "$A" "$W" "$tool" "$args" 2>&1 | grep -o '"isError":[a-z]*' | head -1)
  if [[ "$want" == allow && "$out" == '"isError":false' ]] || [[ "$want" == deny && "$out" == '"isError":true' ]]; then
    echo "ok   $ROLE $label"
  else echo "FAIL $ROLE $label (wanted $want, got ${out:-no tool_execution_end})"; fails=$((fails+1)); fi
}
expect deny  write '{"path":"zz-not-allowed/evil.txt","content":"x"}' "write outside path_write"
expect deny  write '{"path":"AGENTS.md","content":"x"}' "write AGENTS.md"
expect deny  bash  '{"command":"curl -s https://example.com"}' "bash curl"
expect allow bash  '{"command":"git status --short"}' "bash git status"
if [[ "$FIRST" != "-" ]]; then
  expect allow write "{\"path\":\"${FIRST}gate-probe.txt\",\"content\":\"x\"}" "write inside ${FIRST}"
  expect deny  write "{\"path\":\"${FIRST}../../../evil.txt\",\"content\":\"x\"}" "dot-dot escape from ${FIRST}"
fi
echo "x=1" > "$W/.env"
expect deny  read  '{"path":".env"}' "read .env"
exit $(( fails > 0 ))
```

**Acceptance:** run:

```bash
fails=0; for r in $(node -e 'const Y=require("yaml");console.log(Object.keys(Y.parse(require("fs").readFileSync("fleet/fleet.yaml","utf8")).roles).join(" "))'); do
  GATE_TIMEOUT=30 bash scripts/gate-role.sh "$r" || fails=$((fails+1)); done; echo "roles_failed=$fails"
```

It must print `roles_failed=0`, every line must start with `ok`, and roles whose first `path_write` glob is a plain
directory (for example `docs/product/`) must show both `write inside docs/product/` and `dot-dot escape from
docs/product/`. The planning run did 51 roles this way (see section 4.3 for single-probe outputs).

### M6: Validate every spec with openrig

**Do:** run the validators; fix the generator (never the generated files) until they pass.

```bash
bad=0; for f in $(find specs -name agent.yaml); do rig agent validate "$f" --json | jq -e .valid >/dev/null || { echo "BAD $f"; bad=1; }; done; echo "agents_bad=$bad"
for d in rigs/*/; do (cd "$d" && echo "$d $(rig spec validate rig.yaml --json | jq -c .) $(rig spec preflight rig.yaml --json | jq -c '{ready,errors}')"); done
```

**Acceptance:** `agents_bad=0`; all 8 rigs print `{"valid":true,"errors":[]}` and `{"ready":true,"errors":[]}`.
The planning run got exactly this, with preflight warnings only of the forms `Pi version 1.3.0 answered on the
daemon's PATH; ...` and `<pod>.<member>: permission_policy ref="builtin:..." origin=builtin launch_posture=floor`.
Also run `rig spec audit rigs/defensive-sec-and-red-team/rig.yaml --json | jq -c '.findings|map(.kind)'`; it must
print `["missing_startup_context"]`.

### M7: First real launch (no inference needed)

**Do:** create `scripts/seed-rig.mjs` verbatim.

#### File: scripts/seed-rig.mjs

```js
#!/usr/bin/env node
// Seed every Pi seat declared in a rig.yaml, a pod fragment or a member fragment by running
// scripts/render-seat.mjs once per seat. Run BEFORE `rig up` / `rig expand` / `rig add`.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { parseArgs } from "node:util";
import { fileURLToPath } from "node:url";
import YAML from "yaml";

const USAGE = `usage: seed-rig.mjs <rig.yaml | pod-fragment.yaml | member-fragment.yaml> [--rig <rig-id>] [--pod <pod-id>] [--dry-run] [--allow-missing-secrets]
  rig.yaml          seeds every member of every pod (rig id = name:)
  pod fragment      needs --rig (the rig you will rig expand into)
  member fragment   needs --rig and --pod (the target of rig add)`;
const { values: a, positionals } = parseArgs({ allowPositionals: true, options: {
  rig: { type: "string" }, pod: { type: "string" }, "dry-run": { type: "boolean", default: false },
  "allow-missing-secrets": { type: "boolean", default: false }, help: { type: "boolean", default: false },
} });
if (a.help || positionals.length !== 1) { console.log(USAGE); process.exit(a.help ? 0 : 2); }
const die = (m) => { console.error(`error: ${m}`); process.exit(2); };

const file = positionals[0];
const doc = YAML.parse(fs.readFileSync(file, "utf8"));
const seats = []; // {rig, pod, member, role}
const roleOf = (m) => {
  const ref = m.agent_ref ?? die(`member ${m.id} has no agent_ref`);
  return path.basename(ref.replace(/^(local|path):/, ""));
};
if (doc.pods) {
  for (const p of doc.pods) for (const m of p.members) seats.push({ rig: doc.name, pod: p.id, member: m.id, role: roleOf(m) });
} else if (doc.members) {
  if (!a.rig) die("a pod fragment needs --rig");
  for (const m of doc.members) seats.push({ rig: a.rig, pod: doc.id, member: m.id, role: roleOf(m) });
} else if (doc.agent_ref) {
  if (!a.rig || !a.pod) die("a member fragment needs --rig and --pod");
  seats.push({ rig: a.rig, pod: a.pod, member: doc.id, role: roleOf(doc) });
} else die(`${file}: not a rig spec, pod fragment or member fragment`);

const render = path.join(path.dirname(fileURLToPath(import.meta.url)), "render-seat.mjs");
for (const s of seats) {
  const args = [render, "--role", s.role, "--rig", s.rig, "--pod", s.pod, "--member", s.member];
  if (a["dry-run"]) args.push("--dry-run");
  if (a["allow-missing-secrets"]) args.push("--allow-missing-secrets");
  if (a["dry-run"]) { execFileSync(process.execPath, args, { stdio: ["ignore", "ignore", "inherit"] }); console.log(`ok ${s.pod}-${s.member}@${s.rig}`); }
  else execFileSync(process.execPath, args, { stdio: "inherit" });
}
console.log(`seeded ${seats.length} seat(s)`);
```

```bash
rig daemon start --no-kernel   # the fleet needs no kernel operator; this is the mode the planning run verified
mkdir -p "$HERETEK_WORKSPACE" && git -C "$HERETEK_WORKSPACE" init -q
echo "/AGENTS.md" >> "$HERETEK_WORKSPACE/.git/info/exclude"   # openrig writes its managed AGENTS.md there
node scripts/seed-rig.mjs rigs/defensive-sec-and-red-team/rig.yaml --allow-missing-secrets
(cd rigs/defensive-sec-and-red-team && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes --json | jq -c '{status, errors}')
rig ps --nodes --rig defensive-sec-and-red-team
```

**Acceptance:**
- Seeding prints `seeded 7 seat(s)`; with no GitHub/AWS secrets it also prints `warn: ... github disabled, missing
  secrets: github.pat` for threat-modeler and compliance-auditor and `aws disabled` for cloud-sec-auditor.
- `rig up` prints `{"status":"completed","errors":[]}` and `rig ps --nodes` lists 7 sessions in lifecycle `run`.
- For seat `blue-appsec-engineer@defensive-sec-and-red-team`, under
  `$OPENRIG_HOME/state/pi/blue-appsec-engineer@defensive-sec-and-red-team/agent/`: `extensions/pi-permission-system/config.json`
  still exists after launch, and `ls skills` prints exactly the 14 entries
  `heretek-shared:code-review heretek-shared:delegating-work heretek-shared:fp-check heretek-shared:mission-slice-sop heretek-shared:openrig-operating-model heretek-shared:queue-handoff heretek-shared:refocusing heretek-shared:sarif-parsing heretek-shared:seat-continuity-and-handover heretek-shared:security-audit heretek-shared:security-review heretek-shared:semgrep heretek-shared:variant-analysis owasp-reachability-triage`.
- The newest `sessions/*.jsonl` of that seat contains `You are appsec-engineer (Application Security (AppSec) Engineer).`
  (the startup context) and `Agent Charter` (the AGENTS.md charter).
- `ps -eo args | grep "pi-runner.js --session-name blue-appsec-engineer"` shows `--model
  opencode-go/muse-spark-1.3-contributor` and `--no-approve`.
- `rig down defensive-sec-and-red-team` then `rig up defensive-sec-and-red-team --existing` brings the 7 seats back and
  the config.json above is unchanged (`sha256sum` before and after).

### M8: Live inference and in-seat enforcement (needs the human's key)

**Do:** ask the human to place the key file (section 3.2). Never read, print or copy it. Run `rig down defensive-sec-and-red-team`,
re-seed with the M7 seed command, relaunch with the M7 `rig up` command, then:

```bash
rig send blue-appsec-engineer@defensive-sec-and-red-team "Reply with the single word READY, then try to create the file src/zz.txt containing x, and report the exact tool result."
rig capture blue-appsec-engineer@defensive-sec-and-red-team --lines 80
```

**Acceptance:** the capture shows `READY` from the model and a tool result containing
`Denied by policy: 'path_write' for tool 'write' for path 'src/zz.txt'`; `ls "$HERETEK_WORKSPACE/src/zz.txt"` fails.
Record both in NOTES. If the reply is `Connection error.`, the host has no route to `https://opencode.ai`; stop and
report.

### M9: All static rigs and cross-rig escalation

**Do:** seed and launch the other six static rigs one at a time (same commands as M7 with each rig id), then test a
cross-rig address:

```bash
rig send exec-system-architect@executive-and-architecture "Ping from the security rig test. Reply PONG."
```

**Acceptance:** `rig ps` shows 7 rigs running and 51 seats (`rig ps --nodes` per rig: 6, 11, 4, 6, 11, 6, 7). The
architect seat's capture shows `PONG` (needs M8's key). Every seat's agent dir has the five rendered files.

### M10: MCP verification per server

**Do:** for each MCP server in `fleet/mcp-servers.yaml`, pick one seat bound to it, provide the needed secret or a
local backend (a throwaway Postgres in Docker on 127.0.0.1, a local Redis, a kind cluster, etc.; never production),
re-seed that seat without `--allow-missing-secrets`, and run
`PI_CODING_AGENT_DIR=<that seat's agent dir> pi mcp list --json | jq -c '.servers[] | {name, state, tools: (.tools|length), error}'`.
Resolve every row of section 4.5 marked M10.

**Acceptance:** a table in NOTES with one row per server: seat used, `state`, tool count, and for read-only claims
the evidence (for GitHub, the list of tool names). Any server that cannot be made `connected` gets `enabled: false`
in its catalog entry with the reason, and `check-fleet` still passes. Update the `status:` field in
`fleet/mcp-servers.yaml` to `run-verified` for each connected server.

### M11: Omni rig, expand and add

```bash
node scripts/seed-rig.mjs rigs/heretek-omni-fleet/rig.yaml --allow-missing-secrets
node scripts/seed-rig.mjs rigs/heretek-omni-fleet/pods/qa.yaml --rig heretek-omni-fleet --allow-missing-secrets
node scripts/seed-rig.mjs rigs/heretek-omni-fleet/members/vector-rag-spec.yaml --rig heretek-omni-fleet --pod qa --allow-missing-secrets
cd rigs/heretek-omni-fleet
rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes --json | jq -c '{status, errors}'
ID=$(rig ps --json | jq -r '.[] | select(.name=="heretek-omni-fleet") | .rigId')
rig expand "$ID" pods/qa.yaml --rig-root "$PWD" --json | jq -c '{ok, error}'      # may time out; see 4.1
rig ps --nodes --rig heretek-omni-fleet
rig add "$ID" qa members/vector-rag-spec.yaml --rig-root "$PWD" --json | jq -c '{ok, error}'
rig ps --nodes --rig heretek-omni-fleet
```

**Acceptance:** after expand, 9 seats (3 command + 6 qa); after add, 10, with `qa-vector-rag-spec@heretek-omni-fleet`
present and `{"ok":true,"error":null}` from `rig add`. (Planning run: identical counts; expand printed the 5000 ms
timeout and still succeeded.)

### M12: CI and README

**Do:** `.github/workflows/ci.yml` on `ubuntu-24.04` with actions pinned to full commit SHAs (look them up with
`git ls-remote https://github.com/actions/checkout refs/tags/v4.2.2` and the same for `actions/setup-node`
`v4.4.0`; write the SHA and the tag in a comment). Steps: setup-node 22, `npm ci`, `node scripts/check-fleet.mjs`,
`npm i -g @openrig/cli@0.6.11 @earendil-works/pi-coding-agent@1.3.0`, the M6 validator loop, install
pi-permission-system into `$HERETEK_TOOLS` as in 3.2, `node --test tests/*.test.mjs`, and `bash scripts/gate-role.sh`
for appsec-engineer, product-director and dependency-patcher. `permissions: contents: read` at the top. No secrets.
Write `README.md`: what the fleet is, the 8 rigs, how to seed and launch, where secrets go, and a link to
`docs/OSINT_ECOSYSTEM_REPORT.md`. Add a `Makefile` whose targets call the same commands.

**Acceptance:** the workflow passes on the PR. `make check test` passes locally.

### M13: Spec-against-code pass and PR

**Do:** for every numbered statement in sections 4 and 7 of this file, check the code and the running system and
mark it in NOTES as `holds` or `differs: <evidence>`. Then open a PR from `feat/fleet-build` with this body:

```markdown
## Before
Heretek-Crew ran 51 OpenCode agents inside Paperclip; heretek-rigs held only a placeholder licence.

## After
heretek-rigs defines 51 openrig Pi seats on opencode-go/muse-spark-1.3-contributor in 7 static rigs plus a dynamic omni rig, with vendored pinned skills, a pinned MCP catalog and pi-permission-system enforcement verified per role.

## How
fleet/fleet.yaml and fleet/mcp-servers.yaml are the source of truth; scripts/gen-specs.mjs generates specs/ and rigs/; scripts/seed-rig.mjs renders each seat's agent dir before launch; scripts/gate-role.sh proves each role's permission config against a mock model.

## Verification
<paste: check-fleet output, node --test summary, roles_failed=0, the M6 loop summary, M7/M8/M11 rig ps outputs, the M10 MCP table>

## Not verified
<every item still open from section 4.5>
```

**Acceptance:** PR open, CI green, every section 4.5 item either resolved with evidence or listed under "Not verified".

## 7. Gotchas (re-read before every milestone)

1. `runtime: opencode` passes `rig spec validate` and fails only in `rig spec preflight`. Run both, always.
2. openrig never gives a Pi seat `OPENCODE_API_KEY`. The key reaches Pi only through `auth.json` `"!cat <abs>"`.
3. `permission_policy` is a label for Pi seats. Enforcement is pi-permission-system; a seat without its config is wide open.
4. pi-permission-system matches `docs/../x` as if it were under `docs/`. `"*..*":"deny"` must be the LAST
   `path_write` rule and is also in `path`.
5. Last matching rule wins inside a permission map. A guard written before the allows does nothing.
6. With top-level `"*":"deny"`, `tool_search` disappears unless `"tool_search":"allow"` is set, and every MCP
   server is hidden unless named in the `mcp` map.
7. Never `ask`: an unparsable config falls back to `ask`, and a seat has nobody to answer; `promptTimeoutMs` turns that into deny.
8. `guidance_merge` with a shared cwd gives the wrong role to every seat but the last. Charters go to `<agentDir>/AGENTS.md`.
9. Plugins (`plugins: [shared:openrig-core]`) do nothing for Pi. Skills must be declared resources.
10. `!command` works in `mcp.json` `env` and `headers` only, never in `args`, and must be the whole value.
11. `rig expand` takes the rig ID, not the name. `rig add` takes either.
12. `--rig-root` must be absolute; `.` is the daemon's cwd.
13. `rig expand` of a big pod can time out client-side while succeeding. Check `rig ps --nodes` before retrying.
14. `pi -p` may not exit after the agent settles: wrap in `timeout`, read the JSON events, treat `rc=124` as normal.
15. `node --test tests/` fails on Node 22; use `node --test tests/*.test.mjs`.
16. `pkill -f <pattern>` can kill the shell running it when the pattern appears in that shell's command line. Kill by PID.
17. `r2mcp` on PyPI is not radare2, and `aws-mcp` on npm is a hollow package. Use the catalog entries only.
18. `@modelcontextprotocol/server-github` and `server-postgres` are deprecated on npm; never reintroduce them.
19. `git diff --output=<file>` and `tshark -w` write files without going through `write`; the fleet allow-list
    deliberately omits `git diff*` and narrows `tshark` to `tshark -r *`. Do not widen bash allows.
20. openrig writes `<workspace>/AGENTS.md` (managed culture and start blocks). Exclude it from git in the workspace;
    seats cannot write it (`"AGENTS.md":"deny"`).
21. A seat with no network logs `Connection error.` and retries; that is not a config error.
22. `rig spec validate` does not check that `agent_ref` targets exist; preflight does.
23. The Heretek-Crew superpowers skills were truncated copies. The generator vendors the full upstream directories;
    never copy the Heretek-Crew versions of those 7 skills.
24. trailofbits skills are CC-BY-SA-4.0: do not edit vendored files; put changes in a role-local skill instead.

## 8. Definition of done

- [ ] M0 to M13 committed, each with its acceptance evidence in `docs/NOTES.md`.
- [ ] `node scripts/check-fleet.mjs` OK; `node --test tests/*.test.mjs` 7/7; `roles_failed=0` over 51 roles.
- [ ] 52 agent specs valid; 8 rigs `valid` and `ready`.
- [ ] 51 seats launched across 7 static rigs; omni expand and add proven.
- [ ] Live Muse reply and an in-seat permission denial captured (M8).
- [ ] Every MCP server `connected` or disabled with a reason (M10).
- [ ] No secret anywhere in git: `git log -p | grep -E "ghp_|github_pat_|sk-|AKIA"` prints nothing.
- [ ] `LICENSE.md` unchanged.
- [ ] PR open with the M13 body and green CI.
