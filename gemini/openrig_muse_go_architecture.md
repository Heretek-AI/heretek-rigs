# OpenRig + Pi + OpenCode Go (Muse Spark 1.3 Contributor) Architecture Specification

**Target Repository:** [Heretek-AI/heretek-rigs](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FHeretek-AI%2Fheretek-rigs)
**Target Framework:** [mvschwarz/openrig](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fmvschwarz%2Fopenrig) (`v0.6.11`, Commit `d4741c9dc3ed899f0b39dc4b13d571407ee986d4`)
**Coding Agent Runtime:** [earendil-works/pi](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fearendil-works%2Fpi) (`runtime: pi` & `runtime: omp`)
**Model & Provider:** [Muse Spark 1.3 Contributor](https://www.google.com/search?q=https%3A%2F%2Fopencode.ai%2Fdata%2Fmeta%2Fmuse-spark-1-3-contributor) via [OpenCode Go](https://www.google.com/search?q=https%3A%2F%2Fopencode.ai%2Fv2%2Fdocs%2Fconsole%2Fgo%2F) (`opencode-go/muse-spark-1.3-contributor:high`)

## 1. Spoonfeeder Phase 1 & Phase 3 Ground-Truth Verdict Table

Every architectural claim below was verified directly against the source code of `openrig@0.6.11`, `Heretek-Crew`, `pi-coding-agent`, and OpenCode Go documentation before authoring the implementation brief.

| # | Claim / Assumption Handed to Us | Verdict | Empirical Evidence (`file:line` or Command Output) |
| :--- | :--- | :--- | :--- |
| **1** | "The OpenRig CLI binary is named `openrig` (`openrig bundle`, `openrig preflight`, `openrig doctor`, etc.)." | **FALSE — Binary is `rig` (`openrig-tui` for TUI)** | `openrig/packages/cli/package.json:24-27` declares `"bin": { "rig": "dist/bin-wrapper.js", "openrig-tui": "tui/dist/main.js" }`. `docs/as-built/cli-reference.md:31` confirms all 87 top-level registrations and 356 command objects sit under `rig` (`rig bundle create`, `rig bundle check`, `rig preflight`, `rig doctor`, `rig skill loadout`, `rig skill audit`, `rig package validate`, `rig mcp serve`, `rig policy list`, `rig agent validate`, `rig spec validate`). |
| **2** | "`Heretek-Crew/roles-catalog/ROLE_CATALOG_50.md` has 50 roles." | **FALSE — It has 51 roles (`static-analysis-lead` + `ai-red-teamer`)** | `Heretek-Crew/roles-catalog/ROLE_CATALOG_50.md:1` states `# Enterprise Fleet Specification: 51 Autonomous Agent Roles`. `ls Heretek-Crew/roles/` has 51 directories. The user's Rig 1–7 prompt list included Role 51 (`ai-red-teamer` in Rig 7) but omitted Role 37 (`static-analysis-lead` from Rig 6). Restoring `static-analysis-lead` to Rig 6 (`qa-and-verification-gauntlet`) achieves 100% parity (51/51 roles). |
| **3** | "In OpenRig, setting `OPENCODE_API_KEY` in `rig.yaml` `env:` or the daemon environment passes the key to `runtime: pi` seats." | **FALSE — `buildPiChildEnv` strips `OPENCODE_API_KEY` for `runtime: pi` (only `runtime: omp` forwards it!)** | `openrig/packages/daemon/src/adapters/pi-runner-protocol.ts:102-147`: `PI_PROVIDER_ENV_VARS` only forwards `openrouter` (`OPENROUTER_API_KEY`), `zai` (`ZAI_API_KEY`), `kimi-coding` (`KIMI_API_KEY`), and `minimax` (`MINIMAX_API_KEY`). By contrast, `OMP_PROVIDER_ENV_VARS` (line 133) includes `"opencode-go": "OPENCODE_API_KEY"`. Furthermore, `rig.yaml` `env:` is explicitly forbidden from holding secrets (`docs/reference/rig-spec.md:308`). Therefore, `runtime: pi` seats MUST read their OpenCode Go credentials and model definition from `$PI_CODING_AGENT_DIR/{auth.json,models.json}` (`~/.openrig/state/pi/<session>/agent/`), provisioned by `scripts/bootstrap-pi-seats.sh`. |
| **4** | "OpenRig projects `resources.plugins`, `resources.subagents`, and `resources.runtime_resources` from `agent.yaml` into `runtime: pi` seats." | **FALSE — `PiRuntimeAdapter.projectEntry` skips plugins, subagents, and runtime_resources** | `openrig/packages/daemon/src/adapters/pi-runtime-adapter.ts:357-395`: `projectEntry()` only handles `entry.category === "guidance"` (merged into `<cwd>/AGENTS.md`) and `entry.category === "skill"` (copied into `$PI_CODING_AGENT_DIR/skills/<effectiveId>`). Line 392 states: `// Plugins / subagents / runtime resources have no Pi projection target at MVP (PRD §7 out-of-scope) — an honest skip`. Consequently, OpenRig operating skills (`openrig-operating-model`, `mission-slice-sop`, `delegating-work`, `queue-handoff`, `refocusing`, `seat-continuity-and-handover`) MUST be declared as `resources.skills` in `specs/agents/shared/agent.yaml` (not solely relied upon via `plugins: [shared:openrig-core]`) so `runtime: pi` and `runtime: omp` seats actually receive them! |
| **5** | "A rig's `rig.yaml` in `rigs/<rig-slug>/rig.yaml` can reference `agent_ref: local:../../specs/agents/<domain>/<role>` or use symlinks and pass `rig bundle check`." | **FALSE — `checkBundleFolder` requires all refs to resolve inside the rig folder with no symlinks** | `openrig/packages/cli/src/lib/bundle-check.ts:40-93`: `within(full)` resolves `fs.realpathSync(full)` and rejects any path outside `root` (`rigs/<rig-slug>`) with `"Declared file is missing, unreadable or outside the bundle folder"`. `packages/cli/src/commands/specs.ts:44` (`assertTreeHasNoSymlinks`) throws `"Spec directories must not contain symlinks"`. Therefore, `scripts/generate-rigs.py` generates the canonical Master Catalog at `specs/agents/<domain>/<role-slug>/` AND materializes real directory copies into `rigs/<rig-slug>/agents/<role-slug>/` and `rigs/<rig-slug>/agents/shared/`, verified for byte-for-byte parity by `scripts/verify-rigs.sh`. |
| **6** | "OpenRig `permission_policy` (`builtin:locked`, `builtin:standard`, `builtin:auto`) enforces tool and shell restrictions inside `runtime: pi`." | **FALSE — OpenRig policies are recorded metadata; Pi requires harness-native enforcement** | `openrig/packages/cli/src/commands/policy.ts:10-14` (`HONESTY_PIN`): `"OpenRig records posture into RigSpec; harness-native permissions enforce — never runtime enforcement."` And `docs/reference/rig-spec.md:258`: `"Pi has no permission policy. --approve and --no-approve set Pi's resource trust."` Under `builtin:locked` / `builtin:standard` / `builtin:auto`, OpenRig launches `pi` with `--no-approve` (which ignores untrusted project-local `.pi/settings.json`). Therefore, real enforcement on Pi seats requires: (a) `@vtstech/pi-security` + `pi-mcp-adapter` `includeTools`/`excludeTools` configured in the seat's trusted `$PI_CODING_AGENT_DIR`, and (b) explicit permission tables in `guidance/role.md` and `runtime/policy-enforcement.json`. |
| **7** | "Python `yaml.safe_load` can validate `registry-entry.v1` YAML files directly with `jsonschema.Draft202012Validator`." | **FALSE — Unquoted YAML dates become `datetime.date` objects and fail JSON Schema `type: string`** | Verified via live spike against `openrig/docs/reference/schemas/fixtures/valid/registry/openrig-dev.yaml`: `review.date: 2026-10-04` parses in PyYAML (YAML 1.1) as `datetime.date(2026, 10, 4)`, causing `Draft202012Validator` to fail with `datetime.date(2026, 10, 4) is not of type 'string'`. Normalizing via `json.loads(json.dumps(raw, default=str))` in `scripts/verify-rigs.sh` passes all 13 valid and 14 invalid upstream fixtures 100%. |

## 2. Wiring `openrig` + `pi` + `OpenCode Go (Muse Spark 1.3 Contributor)`

### 2.1 OpenCode Go & Muse Spark 1.3 Contributor Specifications
Per [OpenCode Go Documentation](https://www.google.com/search?q=https%3A%2F%2Fopencode.ai%2Fv2%2Fdocs%2Fconsole%2Fgo%2F), [Muse Spark 1.3 Contributor Telemetry](https://www.google.com/search?q=https%3A%2F%2Fopencode.ai%2Fdata%2Fmeta%2Fmuse-spark-1-3-contributor), and [Pi Models Catalog](https://www.google.com/search?q=https%3A%2F%2Fpi.dev%2Fmodels%2Fopencode%2Fmuse-spark-1-3-contributor-free):
- **Provider ID**: `opencode-go` (in OpenCode v2 `opencode.jsonc`, `runtime: omp`, and `pi` with `pi-opencode-go-provider` / custom `models.json`)
- **Model ID**: `muse-spark-1.3-contributor`
- **Canonical OpenRig / Pi Model String**: `opencode-go/muse-spark-1.3-contributor:high`
  - Note on Pi thinking level suffix (`docs/reference/rig-spec.md:332`): OpenRig does not pass a member's `effort` field to `runtime: pi`. Instead, Pi reads `:high` (one of `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`) from the suffix of `model: opencode-go/muse-spark-1.3-contributor:high` and maps it through `thinkingLevelMap` while recording the base model ID `muse-spark-1.3-contributor`.
- **Direct API Protocol & Endpoint**:
  - **Protocol**: OpenAI Responses API (`"api": "openai-responses"`, `@ai-sdk/openai`)
  - **Base URL**: `https://opencode.ai/inference/go/openai/v1` (Full Responses endpoint: `https://opencode.ai/inference/go/openai/v1/responses`)
  - **Models Discovery Endpoint**: `https://opencode.ai/inference/go/v1/models`
  - **Usage Endpoint**: `https://opencode.ai/zen/go/v1/usage`
- **Model Capabilities & Token Economics**:
  - **Context Window**: `1,048,576` tokens (1M)
  - **Max Output Tokens**: `131,072` tokens (131K)
  - **Modalities**: Text, Image (`["text", "image"]`)
  - **Pricing on OpenCode Go**: `$0.10 / 1M` input tokens, `$0.20 / 1M` output tokens, `$0.002 / 1M` cached read tokens (95% average cache hit ratio; ~$0.0011 average session cost)
  - **Go Plan Allowances**: Go ($10/mo) includes $60/mo Muse Spark 1.3 Contributor usage (~45,300 requests / 5h, 113,300 / wk, 226,600 / mo); Go Plus ($40/mo) includes $120/mo (~90,600 requests / 5h, 226,600 / wk, 453,200 / mo). Rolling windows: 5h = 20% of monthly limit, weekly = 50%, monthly = 100%.
  - **Required Session Affinity Headers**: `x-opencode-session` (stable session ID per conversation) and custom `User-Agent` / `x-opencode-client` (`sendSessionIdHeader: true`, `sessionAffinityFormat: "openai-nosession"`).

### 2.2 End-to-End Execution & State Flow in OpenRig

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ OpenRig Daemon (@openrig/daemon v0.6.11)                                          │
│                                                                                   │
│  1. Reads rigs/<rig-slug>/rig.yaml (version: "0.2")                               │
│  2. Resolves member agent_ref -> rigs/<rig-slug>/agents/<role-slug>/agent.yaml    │
│  3. Projects guidance -> <cwd>/AGENTS.md (managed blocks, never overwrites base)  │
│  4. Projects skills (shared + custom) -> $OPENRIG_HOME/state/pi/<session>/agent/  │
│  5. Spawns pane-hosted pi-runner.js inside tmux session <pod>-<member>@<rig>      │
└───────────────────────────────────────┬───────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ OpenRig Pi Runner (packages/daemon/dist/adapters/pi-runner.js)                    │
│                                                                                   │
│  Spawns: pi --mode rpc --session-dir <sessionsDir> --name <sessionName>           │
│             --no-approve --model opencode-go/muse-spark-1.3-contributor:high      │
│                                                                                   │
│  Env Boundary (buildPiChildEnv):                                                  │
│    PI_CODING_AGENT_DIR = ~/.openrig/state/pi/<pod>-<member>@<rig>/agent           │
│    PI_CODING_AGENT_SESSION_DIR = ~/.openrig/state/pi/<pod>-<member>@<rig>/sessions│
│    OPENRIG_SESSION_NAME, OPENRIG_NODE_ID, OPENRIG_URL, PATH, HOME, ...            │
└───────────────────────────────────────┬───────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ Seat Agent Directory ($PI_CODING_AGENT_DIR — Provisioned by bootstrap-pi-seats.sh)│
│                                                                                   │
│  ├── models.json       (Declares provider "opencode-go" -> openai-responses API)  │
│  ├── auth.json         (0600 mode: {"opencode-go": {"type":"api_key","key":...}}) │
│  ├── settings.json     (Loads pi-mcp-adapter, pi-opencode-go-provider, role pkgs) │
│  ├── mcp.json          (Role-scoped MCP servers + includeTools/excludeTools)      │
│  ├── lsp.json          (Role-scoped gopls / pyright / clangd / rust-analyzer)     │
│  └── skills/<id>/      (Projected OpenRig core SOP skills + domain SKILL.md)      │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Dual-Runtime Compatibility (`runtime: pi` Default + `runtime: omp` / `claude-code` / `codex` Presets)
Every rig in `heretek-rigs` ships a `configurations.yaml` (`openrig.bundle-configurations/v1`) beside `rig.yaml` declaring four presets:
1. `recommended` (matches `rig.yaml` as authored: every seat runs `runtime: pi` with `model: opencode-go/muse-spark-1.3-contributor:high`).
2. `all-pi` (explicit alias for all-Pi seats).
3. `all-omp` (runs every seat on `runtime: omp` — Oh My Pi — where `OMP_PROVIDER_ENV_VARS` natively forwards `OPENCODE_API_KEY` from the daemon environment when `OPENCODE_API_KEY` is listed in `recovery.provider_auth_env_allowlist`).
4. `all-claude` and `all-codex` (cross-harness presets for mixed-fleet testing).

## 3. Repository Architecture & Directory Layout

```text
heretek-rigs/
├── README.md                                     # Root architecture, quickstart, and 8-rig index
├── Makefile                                      # Build, generate, verify, bundle, sidecar, and audit targets
├── .env.example                                  # Fail-closed template for OPENCODE_API_KEY and sidecar secrets
├── docker-compose.sidecars.yml                   # Digest-pinned sidecars across 7 profiles + segmented networks
├── PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md # Master milestone-by-milestone prompt for OpenCode
├── PROMPT_ADVERSARIAL_FLEET_AUDIT.md             # Three-subagent (Alpha/Beta/Gamma) zero-trust audit prompt
├── PROMPT_FLEET_AUDIT_REMEDIATION.md             # Paired fail-closed remediation loop prompt
├── docs/
│   ├── OSINT_ECOSYSTEM_REPORT.md                 # Ecosystem evaluation & 51-Agent Master Mapping Matrix
│   ├── OPENRIG_MUSE_GO_ARCHITECTURE.md           # This architectural & runtime wiring specification
│   └── NOTES.md                                  # Empirical probe log & implementation ledger
├── schemas/                                      # Exact copies of OpenRig v1 JSON Schemas for offline verification
│   ├── bundle-common.v1.schema.json
│   ├── bundle-configurations.v1.schema.json
│   ├── bundle-behaviour.v1.schema.json
│   ├── bundle-status.v1.schema.json
│   ├── registry-entry.v1.schema.json
│   └── run-record.v1.schema.json
├── policies/
│   ├── heretek-readonly-audit.policy.md          # Custom config-surface deny-by-default policy for auditors
│   └── heretek-builder-standard.policy.md        # Custom config-surface builder policy gating remote/destructive ops
├── rosters/
│   └── heretek-omni-fleet.json                   # OpenRig v1 Roster mapping all 51 seats, capabilities & engagement
├── scripts/
│   ├── generate-rigs.py                          # Deterministic generator for all 51 agents, 8 rigs, and views
│   ├── verify-rigs.sh                            # Self-testing verification gate (schemas, digests, parity, security)
│   ├── bootstrap-pi-seats.sh                     # Seeds $OPENRIG_HOME/state/pi/<seat>/agent/{models,auth,settings,mcp}.json
│   └── audit_loop.py                             # Automated OpenCode implementation/audit/remediation runner (3x pass)
├── specs/
│   └── agents/
│       ├── shared/                               # Shared AgentSpec pool (version: "1.0")
│       │   ├── agent.yaml
│       │   ├── skills/                           # Core OpenRig SOP skills + process/PM/pod skills
│       │   └── runtime/                          # Claude/Codex/Pi runtime fragments
│       ├── executive/                            # 6 roles (exec-director .. ux-research-analyst)
│       ├── game-dev/                             # 6 roles (engine-systems-eng .. tech-artist-pipeline)
│       ├── web-ui-ux/                            # 6 roles (ui-ux-designer .. brand-copy-spec)
│       ├── language-specialists/                 # 8 roles (rust-systems-spec .. android-mobile-spec)
│       ├── cloud-sre/                            # 6 roles (cloud-platform-eng .. cache-streaming-eng)
│       ├── qa-verification/                      # 6 roles (e2e-browser-qa .. release-qa-officer, incl. static-analysis-lead)
│       ├── security-forensics/                   # 7 roles (threat-modeler .. ai-red-teamer)
│       ├── data-ai/                              # 4 roles (data-pipeline-eng .. analytics-metrics-eng)
│       └── ops-maintenance/                      # 2 roles (dependency-patcher, git-drift-coord)
├── rigs/
│   ├── executive-and-architecture/               # Rig 1 (6 seats across governance, architecture pods)
│   ├── fullstack-and-web-studio/                 # Rig 2 (11 seats across backend, frontend, ux-brand pods)
│   ├── systems-and-mobile-foundry/               # Rig 3 (4 seats across systems, mobile pods)
│   ├── game-dev-and-sim-rig/                     # Rig 4 (6 seats across engine-sim, gameplay-art pods)
│   ├── cloud-sre-and-data-platform/              # Rig 5 (11 seats across infra-sre, data-stores, ai-mlops pods)
│   ├── qa-and-verification-gauntlet/             # Rig 6 (6 seats across active-qa, gate-review pods)
│   ├── defensive-sec-and-red-team/               # Rig 7 (7 seats across sec-audit, re-redteam pods)
│   └── heretek-omni-fleet/                       # Rig 8 (All 51 seats across 9 departmental pods)
└── registry/
    ├── status.json                               # Public status file (openrig.status-rule/v1 + RFC 8785 bodyDigest)
    ├── entries/<rig-slug>.yaml                   # Registry entries (openrig.registry-entry/v1)
    └── views/<rig-slug>/behaviour.json           # Before-install behaviour views (openrig.bundle-behaviour/v1)
```

## 4. OpenRig Schema & Validation Rules Reference

### 4.1 `rig.yaml` (Version `"0.2"`, Pod-Aware)
Every `rigs/<rig-slug>/rig.yaml` must obey `RigSpecSchema.validate()` in `packages/daemon/src/domain/rigspec-schema.ts`:
- **Allowed top-level keys only** (`RIG_KEYS`): `version`, `name`, `summary`, `culture_file`, `permission_policy`, `managed_blocks`, `docs`, `startup`, `services`, `workspace`, `pods`, `edges`, `non_interruptive`, `env`. Any unknown key is rejected!
- **Allowed pod keys only** (`POD_KEYS`): `id`, `label`, `summary`, `continuity_policy`, `startup`, `members`, `edges`. Pod `id` must not contain `.` or `@`.
- **Allowed member keys only** (`MEMBER_KEYS`): `id`, `label`, `agent_ref`, `profile`, `runtime`, `codex_config_profile`, `model`, `effort`, `role`, `permission_policy`, `cwd`, `restore_policy`, `compaction_strategy`, `mechanic`, `startup`, `session_source`, `starter_ref`, `env`.
- **Pod-local edges vs. Cross-pod edges**:
  - `pods[i].edges` MUST use **unqualified** member IDs (`from: exec-director`, `to: product-director`) within the same pod.
  - Top-level `edges` MUST use **fully-qualified** `pod.member` IDs (`from: governance.tpm-scrum-lead`, `to: architecture.system-architect`) across **different** pods.
  - Valid edge kinds: `delegates_to`, `spawned_by`, `can_observe`, `collaborates_with`, `escalates_to`.
  - `delegates_to` and `spawned_by` enforce topological launch order and must be a strict DAG (zero cycles).
- **`permission_policy`**: Must be `builtin:locked`, `builtin:standard`, `builtin:open`, `builtin:yolo`, `builtin:auto`, `none`, or a safe relative path (`policies/heretek-readonly-audit.policy.md`). Never bare `locked` or `standard`.

### 4.2 `agent.yaml` (Version `"1.0"`)
Every `specs/agents/<domain>/<role-slug>/agent.yaml` (and vendored `rigs/<rig-slug>/agents/<role-slug>/agent.yaml`) must obey `validateAgentSpec()` in `packages/daemon/src/domain/agent-manifest.ts`:
- `name` and `version: "1.0"` (quoted string!) are required.
- `defaults.lifecycle.execution_mode` must be `"interactive_resident"` (`wake_on_demand` is rejected).
- `defaults.lifecycle.compaction_strategy` must be one of `"default-compaction"`, `"managed-compaction"`, `"handover"`, `"apprentice-handover"`.
- `defaults.lifecycle.restore_policy` must be `"resume_if_possible"`, `"relaunch_fresh"`, or `"checkpoint_only"`.
- `resources.hooks` and `profiles.<name>.uses.hooks` are **refused** (hooks ship inside plugins).
- In `rigs/<rig-slug>/agents/<role-slug>/agent.yaml`, `imports` uses `ref: "local:../shared"` and `version: "1.0"` so that `rig bundle check rigs/<rig-slug>` resolves all imports strictly inside `rigs/<rig-slug>/`.

### 4.3 Cryptographic Digest Rules (`configurationId`, `packageDigest`, `bodyDigest`)
Verified against `openrig/docs/reference/schemas/fixtures/identity-vectors.json`:
1. **`configurationId`**: Every member's `pod.member=runtime`, sorted by `pod.member` in UTF-16 code-unit order, joined with `,` (no whitespace).
2. **`packageDigest`**: `{ "algorithm": "sha256", "value": "<64-hex>", "coverage": "openrig.package-digest/v1" }`, where `value` is SHA-256 over UTF-8 lines `JSON.stringify(path) + "\t" + sha256 + "\n"` sorted by `path` in UTF-16 code-unit order across all packaged files (excluding `bundle.yaml`, `.DS_Store`, `Thumbs.db`, `.gitkeep`).
3. **`status.json` `bodyDigest`**: Lowercase hex SHA-256 over RFC 8785 (JCS) canonical JSON (`json.dumps(obj_without_bodyDigest, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')`).

## 5. Sidecar Docker Compose Integration & Network Segmentation

`heretek-rigs` ships `docker-compose.sidecars.yml` at the repository root (and links it into rig `services:` blocks when sidecar profiles are active):
- **Loopback-Only Host Publishes**: Every UI/inspection port (`searxng` `:8888`, `firecrawl` `:3002`, `browserless` `:3003`, `mitmproxy` `:8081`, `hound` `:6081`, `qdrant` `:6333`, `neo4j` `:7474`, `litellm` `:4000`, `mailpit` `:8025`, `minio` `:9001`, `wiremock` `:8089`, `jaeger` `:16686`, `docker-android` `:5555`/`:6080`) binds strictly to `127.0.0.1`.
- **Network Segmentation**:
  - `heretek`: Core, web-research, ai-gateway, qa-testing, and observability services.
  - `heretek-devsec`: Isolates `ghidra` (`:1337`) and `radare2` (`:9090`), mounting `./workspaces/binaries:/samples:ro`.
  - `heretek-mobile`: Isolates privileged `docker-android` (`/dev/kvm`). Enforced by `Makefile` `guard-profiles` which refuses co-scheduling `mobile` with `devsec` or `web-research`.
- **Read-Only Docker Socket Firewall**: `tecnativa/docker-socket-proxy:0.5.0` enforces `POST: "0"`, `BUILD: "0"`, `EXEC: "0"`, `VOLUMES: "0"`, `NETWORKS: "0"`, `AUTH: "0"`.
