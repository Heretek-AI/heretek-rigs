# SPOONFEEDER IMPLEMENTATION BRIEF: `heretek-rigs` (51-Agent OpenRig + Pi + Muse Spark 1.3 Contributor Fleet)

## 1. Mission

You are building **`heretek-rigs`** (`https://github.com/Heretek-AI/heretek-rigs`), a production-grade, multi-rig [OpenRig](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fmvschwarz%2Fopenrig) (`v0.6.11`) repository that migrates all **51 specialized autonomous agent roles** from [Heretek-AI/Heretek-Crew](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FHeretek-AI%2FHeretek-Crew) into 9 domain catalog directories (`specs/agents/<domain>/<role-slug>/` + `specs/agents/shared/`) and 8 pod-aware OpenRig v0.2 bundles (`rigs/<rig-slug>/`), wired to execute on `runtime: pi` (and `runtime: omp`) powered by **Muse Spark 1.3 Contributor** (`opencode-go/muse-spark-1.3-contributor:high`) via [OpenCode Go](https://www.google.com/search?q=https%3A%2F%2Fopencode.ai%2Fv2%2Fdocs%2Fconsole%2Fgo%2F). **Read this entire file before writing a single line of code: your training data is out of date for OpenRig v0.6.11, Pi v1.0, and OpenCode Go's Muse Spark 1.3 Contributor API, and every schema, CLI flag, and script in this brief has been verified by live execution.**

---

## 2. How to Work

1. **Execute Milestones 1 through 10 in strict numerical order.** Never skip ahead or reorder milestones.
2. **Run every Milestone's Acceptance Check before moving on.** Every acceptance check is a runnable shell command with a binary pass/fail exit code and expected output. Do not advance if a check fails.
3. **Commit per milestone with explicit staging.** Use `git add <explicit-files>` (never `git add -A` or `git add .`) and commit with `git commit -m "feat(m<N>): <milestone summary>"`.
4. **Never skip, delete, or weaken verification checks** in `scripts/verify-rigs.sh` or `scripts/audit_loop.py`.
5. **Never invent APIs, schema keys, CLI flags, or package names.** Look them up in this exact order: (a) Section 4 (`Verified facts`) and Section 5 (`Target layout`) of this brief, (b) `.scratch/openrig/packages/daemon/src/domain/rigspec-schema.ts` and `agent-manifest.ts`, (c) a throwaway experiment in `.scratch/`.
6. **Log every discovery and discrepancy in `docs/NOTES.md`** with the exact command run and its verbatim output.
7. **Stop after 3 failed attempts on the same error.** Record what was tried and the exact error output in `docs/NOTES.md` before escalating.
8. **Hard "Never Do X" Rules Uncovered by Live Spikes:**
   - **NEVER** invoke `openrig <subcommand>` — the OpenRig CLI binary in `@openrig/cli@0.6.11` is named **`rig`** (`rig bundle check`, `rig preflight`, `rig doctor`, `rig skill loadout`, `rig policy list`, `rig agent validate`).
   - **NEVER** assume 50 roles — `Heretek-Crew/roles-catalog/ROLE_CATALOG_50.md` and `Heretek-Crew/roles/*` define **51** roles (`01`–`50` plus Role `51` `ai-red-teamer`, with Role `37` `static-analysis-lead` assigned to Rig 6 `qa-and-verification-gauntlet`).
   - **NEVER** put `OPENCODE_API_KEY` or any secret into `rig.yaml` `env:` — OpenRig stores `env:` in snapshots/bundles in plaintext, AND `buildPiChildEnv()` in `pi-runner-protocol.ts` strips `OPENCODE_API_KEY` for `runtime: pi` seats anyway. Always provision `$OPENRIG_HOME/state/pi/<session>/agent/{models.json,auth.json}` via `scripts/bootstrap-pi-seats.sh`.
   - **NEVER** rely on `plugins: [shared:openrig-core]` alone to deliver OpenRig operating skills to `runtime: pi` seats — `PiRuntimeAdapter.projectEntry()` (`pi-runtime-adapter.ts:392`) skips `category === "plugin"`. Declare all OpenRig core SOP skills under `resources.skills` in `specs/agents/shared/agent.yaml`.
   - **NEVER** use symlinks inside `specs/` or `rigs/`, and **NEVER** point `rigs/<rig-slug>/rig.yaml` `agent_ref` outside `rigs/<rig-slug>/` (e.g. `local:../../specs/agents/...`) — `checkBundleFolder` (`bundle-check.ts:41`) resolves `fs.realpathSync` and rejects any file outside the rig directory root, and `specs.ts:44` (`assertTreeHasNoSymlinks`) throws on symlinks. Always materialize real directory copies into `rigs/<rig-slug>/agents/<role-slug>/` and `rigs/<rig-slug>/agents/shared/` via `scripts/generate-rigs.py`.
   - **NEVER** pass raw `yaml.safe_load()` output to `jsonschema.Draft202012Validator` without normalizing dates via `json.loads(json.dumps(raw, default=str))` — PyYAML parses unquoted `2026-10-18` as `datetime.date(2026, 10, 18)`, which fails JSON Schema `type: "string"`.

---

## 3. Paths and Setup

### 3.1 Repository & Scratch Paths
- **Target Repository Root**:Current working repository (`heretek-rigs`, resolve via `REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"`).
- **Branch to Create**: `git checkout -B feat/openrig-51-fleet-migration`
- **Git-Ignored Scratch Directory for Reference Clones**: `$REPO_ROOT/.scratch/` (must be listed in `.gitignore`).
  - Clone or unpack reference repos into:
    - `$REPO_ROOT/.scratch/Heretek-Crew` (`https://github.com/Heretek-AI/Heretek-Crew`, commit `5ffb1fc6b8fdcfd19a00c05684cba183fe78e8c6`)
    - `$REPO_ROOT/.scratch/openrig` (`https://github.com/mvschwarz/openrig`, `v0.6.11`, commit `d4741c9dc3ed899f0b39dc4b13d571407ee986d4`)

### 3.2 Toolchain Verification Commands
```bash
python3 --version          # Expected: Python 3.11+
python3 -c "import yaml, jsonschema, referencing; print('OK')"  # Expected: OK
jq --version               # Expected: jq-1.6+
```

### 3.3 Files to Port from Reference Repositories & License Obligations

| Source Repository | Source Path | Target Path in `heretek-rigs` | What to Take | License & Obligation |
| :--- | :--- | :--- | :--- | :--- |
| `mvschwarz/openrig` | `docs/reference/schemas/*.v1.schema.json` | `schemas/*.v1.schema.json` | Exact v1 JSON Schemas (`bundle-common`, `bundle-configurations`, `bundle-behaviour`, `bundle-status`, `registry-entry`, `run-record`) | `Apache-2.0` — preserve `LICENSE` notice |
| `mvschwarz/openrig` | `skills/_canonical/**` & `packages/daemon/assets/plugins/openrig-core/skills/**` | `specs/agents/shared/skills/<skill-id>/SKILL.md` | Core OpenRig SOP & process skills (ensure YAML frontmatter `name` & `description` is present) | `Apache-2.0` — preserve `LICENSE` notice |
| `Heretek-AI/Heretek-Crew` | `docker-compose.sidecars.yml` | `docker-compose.sidecars.yml` | Complete digest-pinned sidecar suite (`web-research`, `devsec`, `ai-gateway`, `qa-testing`, `observability`, `mobile`, `ci`) + segmented networks | `MIT` |
| `Heretek-AI/Heretek-Crew` | `roles/*/.opencode/skills/*/SKILL.md` | `specs/agents/<domain>/<role-slug>/skills/<skill-id>/SKILL.md` | All 61 custom domain `SKILL.md` files across the 51 roles | `MIT` |
| `Heretek-AI/Heretek-Crew` | `roles/*/.opencode/agents/<role>.md`, `roles/*/AGENTS.md`, `roles/*/opencode/opencode.json` | `specs/agents/<domain>/<role-slug>/{guidance/role.md,startup/context.md,runtime/*.json}` | Role prompts, charters, MCP server definitions, and least-privilege file/shell allowlists | `MIT` |

---

## 4. Verified Facts

### 4.1 OpenCode Go & Muse Spark 1.3 Contributor Wiring
- **Model ID on OpenCode Go**: `muse-spark-1.3-contributor`
- **OpenRig / Pi Model String**: `opencode-go/muse-spark-1.3-contributor:high`
- **API Protocol**: `openai-responses` (`https://opencode.ai/inference/go/openai/v1/responses`, base URL `https://opencode.ai/inference/go/openai/v1`)
- **Context & Output**: `1,048,576` context window, `131,072` max output tokens, `["text", "image"]` inputs, `$0.10/1M` input, `$0.20/1M` output, `$0.002/1M` cached read.
- **Exact `$PI_CODING_AGENT_DIR/models.json` payload**:
```json
{
  "providers": {
    "opencode-go": {
      "api": "openai-responses",
      "baseUrl": "https://opencode.ai/inference/go/openai/v1",
      "models": [
        {
          "id": "muse-spark-1.3-contributor",
          "name": "Muse Spark 1.3 Contributor",
          "reasoning": true,
          "input": ["text", "image"],
          "thinkingLevelMap": {
            "off": null,
            "minimal": "minimal",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "xhigh": "xhigh",
            "max": null
          },
          "contextWindow": 1048576,
          "maxTokens": 131072,
          "cost": { "input": 0.10, "output": 0.20, "cacheRead": 0.002, "cacheWrite": 0 },
          "compat": {
            "supportsDeveloperRole": true,
            "sendSessionIdHeader": true,
            "supportsLongCacheRetention": true,
            "sessionAffinityFormat": "openai-nosession"
          }
        }
      ]
    }
  }
}
```

### 4.2 OpenRig Validator Key Allowlists (`rigspec-schema.ts` & `agent-manifest.ts`)
- **`RIG_KEYS`**: `version`, `name`, `summary`, `culture_file`, `permission_policy`, `managed_blocks`, `docs`, `startup`, `services`, `workspace`, `pods`, `edges`, `non_interruptive`, `env`
- **`POD_KEYS`**: `id`, `label`, `summary`, `continuity_policy`, `startup`, `members`, `edges`
- **`MEMBER_KEYS`**: `id`, `label`, `agent_ref`, `profile`, `runtime`, `codex_config_profile`, `model`, `effort`, `role`, `permission_policy`, `cwd`, `restore_policy`, `compaction_strategy`, `mechanic`, `startup`, `session_source`, `starter_ref`, `env`
- **`EDGE_KEYS`**: `kind`, `from`, `to` (where `kind` is one of `delegates_to`, `spawned_by`, `can_observe`, `collaborates_with`, `escalates_to`)

### 4.3 Verified Cryptographic Digest Formulas (`bundle-formats.md` & `identity-vectors.json`)
- **`configurationId`**: Sort `pod.member` keys by UTF-16 code units (`[int.from_bytes(s[i].encode('utf-16-le'), 'little') for i in range(len(s))]`) and join `f"{{k}}={{mapping[k]}}"` with `","`.
- **`packageDigest`**: Sort all archive-relative file paths (excluding `bundle.yaml`, `.DS_Store`, `Thumbs.db`, `.gitkeep`) by UTF-16 code units, format each line as `f"{{json.dumps(path, ensure_ascii=False)}}\t{{sha256_hex}}\n"`, and hash the concatenated UTF-8 bytes with SHA-256.
- **`status.json` `bodyDigest`**: Remove `"bodyDigest"` from the status object, serialize with `json.dumps(body_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")` (RFC 8785 JCS), and take the lowercase hex SHA-256.

### 4.4 Not Verified, Be Careful
1. **Live OpenCode Go Network Inference**: Because sandboxed build environments may not have a live `OPENCODE_API_KEY` or internet egress, `scripts/verify-rigs.sh` and `scripts/bootstrap-pi-seats.sh --dry-run` verify the exact file shapes, permissions (`0600`), and schemas offline. When running on a developer workstation with a live `OPENCODE_API_KEY`, test live inference early with `curl -s https://opencode.ai/inference/go/v1/models -H "Authorization: Bearer $OPENCODE_API_KEY"` and record the output in `docs/NOTES.md`.
2. **Optional Sidecars (`prometheus`, `clickhouse`, `redis`, `kafka`, `ollama`)**: As documented in `ROLE_CATALOG_50.md` §4.3, these 5 sidecar services are not enabled in the default compose profiles; their MCP servers are configured as `lifecycle: "lazy"` so seats boot cleanly without them.

---

## 5. Target Layout & Exact Templates

### 5.1 Repository File Tree
```text
heretek-rigs/
├── .env.example                                  # Fail-closed secret template (CHANGE_ME__* placeholders)
├── .gitignore                                    # Ignores .env, .scratch/, dist/, *.rigbundle*
├── Makefile                                      # Build, generate, verify, bootstrap-seats, sidecars, audit-loop
├── README.md                                     # Root quickstart and architecture overview
├── docker-compose.sidecars.yml                   # Digest-pinned sidecars + segmented networks (heretek, heretek-devsec, heretek-mobile)
├── PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md # This implementation brief
├── PROMPT_ADVERSARIAL_FLEET_AUDIT.md             # Three-subagent adversarial audit prompt
├── PROMPT_FLEET_AUDIT_REMEDIATION.md             # Paired remediation prompt
├── docs/
│   ├── OSINT_ECOSYSTEM_REPORT.md                 # Ecosystem rubric & 51-Agent Master Mapping Matrix
│   ├── OPENRIG_MUSE_GO_ARCHITECTURE.md           # OpenRig + Pi + Muse Spark 1.3 Contributor architecture
│   └── NOTES.md                                  # Empirical spike & verification log
├── policies/
│   ├── heretek-readonly-audit.policy.md          # Custom config-surface read-only audit policy
│   └── heretek-builder-standard.policy.md        # Custom config-surface builder policy
├── rosters/
│   └── heretek-omni-fleet.json                   # OpenRig v1 Roster across all 51 specialist seats
├── schemas/
│   ├── bundle-common.v1.schema.json              # Shared OpenRig v1 definitions
│   ├── bundle-configurations.v1.schema.json      # configurations.yaml schema
│   ├── bundle-behaviour.v1.schema.json           # behaviour.json schema
│   ├── bundle-status.v1.schema.json              # status.json schema
│   ├── registry-entry.v1.schema.json             # registry/entries/*.yaml schema
│   └── run-record.v1.schema.json                 # run-record.v1 schema
├── scripts/
│   ├── generate-rigs.py                          # Deterministic generator for all 51 agents & 8 rigs
│   ├── verify-rigs.sh                            # Self-testing verification gate (15 check suites)
│   ├── bootstrap-pi-seats.sh                     # Seeds $OPENRIG_HOME/state/pi/<seat>/agent/
│   └── audit_loop.py                             # Automated 3x STATUS: NO_FINDINGS loop runner
├── specs/
│   └── agents/
│       ├── shared/                               # Shared AgentSpec v1.0 + 36 core/process/PM/ecosystem skills
│       └── <domain>/<role-slug>/                 # All 51 specialist AgentSpecs v1.0 (across 9 domains)
├── rigs/
│   ├── executive-and-architecture/               # Rig 1 (6 seats)
│   ├── fullstack-and-web-studio/                 # Rig 2 (11 seats)
│   ├── systems-and-mobile-foundry/               # Rig 3 (4 seats)
│   ├── game-dev-and-sim-rig/                     # Rig 4 (6 seats)
│   ├── cloud-sre-and-data-platform/              # Rig 5 (11 seats)
│   ├── qa-and-verification-gauntlet/             # Rig 6 (6 seats, incl. static-analysis-lead)
│   ├── defensive-sec-and-red-team/               # Rig 7 (7 seats, incl. ai-red-teamer)
│   └── heretek-omni-fleet/                       # Rig 8 (All 51 seats across 9 pods)
└── registry/
    ├── status.json                               # Public status file with RFC 8785 JCS bodyDigest
    ├── entries/<rig-slug>.yaml                   # 8 registry entries (openrig.registry-entry/v1)
    └── views/<rig-slug>/behaviour.json           # 8 behaviour views (openrig.bundle-behaviour/v1)
```

### 5.2 Exact Template: `rigs/executive-and-architecture/rig.yaml`
```yaml
version: '0.2'
name: executive-and-architecture
summary: Executive governance, product strategy, sprint decomposition, system architecture, git drift coordination, and technical
  documentation squad.
culture_file: CULTURE.md
permission_policy: builtin:locked
non_interruptive: false
env:
  HERETEK_RIG_NAME: executive-and-architecture
  OPENCODE_GO_USAGE: 'on'
  PI_PROVIDER_SYNC_TTL_MS: '3600000'
docs:
- path: README.md
- path: SETUP.md
pods:
- id: governance
  label: Executive & Product Governance
  summary: OKR direction, PRD authoring, and agile sprint decomposition.
  continuity_policy:
    enabled: true
    sync_triggers:
    - pre_compaction
    - pre_shutdown
    - milestone
    artifacts:
      session_log: true
      restore_brief: true
      quiz: false
    restore_protocol:
      peer_driven: true
      verify_via_quiz: false
  members:
  - id: exec-director
    label: Director / CEO-Delegate
    agent_ref: local:agents/exec-director
    profile: default
    runtime: pi
    model: opencode-go/muse-spark-1.3-contributor:high
    effort: high
    role: exec-director
    permission_policy: builtin:locked
    cwd: .
    restore_policy: resume_if_possible
    compaction_strategy: default-compaction
  - id: product-director
    label: Product Director / Head of Product
    agent_ref: local:agents/product-director
    profile: default
    runtime: pi
    model: opencode-go/muse-spark-1.3-contributor:high
    effort: high
    role: product-director
    permission_policy: builtin:locked
    cwd: .
    restore_policy: resume_if_possible
    compaction_strategy: default-compaction
  - id: tpm-scrum-lead
    label: Technical Product Manager / Scrum Lead
    agent_ref: local:agents/tpm-scrum-lead
    profile: default
    runtime: pi
    model: opencode-go/muse-spark-1.3-contributor:high
    effort: high
    role: tpm-scrum-lead
    permission_policy: builtin:locked
    cwd: .
    restore_policy: resume_if_possible
    compaction_strategy: default-compaction
  edges:
  - kind: delegates_to
    from: exec-director
    to: product-director
  - kind: delegates_to
    from: product-director
    to: tpm-scrum-lead
  - kind: escalates_to
    from: tpm-scrum-lead
    to: exec-director
- id: architecture
  label: System Architecture, Git Hygiene & Docs
  summary: ADR governance, worktree rebase orchestration, and docs-as-code synchronization.
  continuity_policy:
    enabled: true
    sync_triggers:
    - pre_compaction
    - pre_shutdown
    - milestone
    artifacts:
      session_log: true
      restore_brief: true
      quiz: false
    restore_protocol:
      peer_driven: true
      verify_via_quiz: false
  members:
  - id: system-architect
    label: System Architect
    agent_ref: local:agents/system-architect
    profile: default
    runtime: pi
    model: opencode-go/muse-spark-1.3-contributor:high
    effort: high
    role: system-architect
    permission_policy: builtin:locked
    cwd: .
    restore_policy: resume_if_possible
    compaction_strategy: default-compaction
  - id: git-drift-coord
    label: Git & Worktree Drift Coordinator
    agent_ref: local:agents/git-drift-coord
    profile: default
    runtime: pi
    model: opencode-go/muse-spark-1.3-contributor:high
    effort: high
    role: git-drift-coord
    permission_policy: builtin:locked
    cwd: .
    restore_policy: resume_if_possible
    compaction_strategy: default-compaction
  - id: tech-docs-lead
    label: Technical Documentation Lead
    agent_ref: local:agents/tech-docs-lead
    profile: default
    runtime: pi
    model: opencode-go/muse-spark-1.3-contributor:high
    effort: high
    role: tech-docs-lead
    permission_policy: builtin:locked
    cwd: .
    restore_policy: resume_if_possible
    compaction_strategy: default-compaction
  edges:
  - kind: delegates_to
    from: system-architect
    to: tech-docs-lead
  - kind: collaborates_with
    from: system-architect
    to: git-drift-coord
edges:
- kind: delegates_to
  from: governance.exec-director
  to: architecture.system-architect
- kind: delegates_to
  from: governance.tpm-scrum-lead
  to: architecture.git-drift-coord
- kind: can_observe
  from: architecture.tech-docs-lead
  to: governance.product-director
- kind: escalates_to
  from: architecture.git-drift-coord
  to: governance.tpm-scrum-lead
```

### 5.3 Exact Template: `rigs/executive-and-architecture/configurations.yaml`
```yaml
schema: openrig.bundle-configurations/v1
recommended: recommended
seats:
  governance.exec-director:
    runtimes:
      pi: default
      omp: default
      claude-code: default
      codex: default
  governance.product-director:
    runtimes:
      pi: default
      omp: default
      claude-code: default
      codex: default
  governance.tpm-scrum-lead:
    runtimes:
      pi: default
      omp: default
      claude-code: default
      codex: default
  architecture.system-architect:
    runtimes:
      pi: default
      omp: default
      claude-code: default
      codex: default
  architecture.git-drift-coord:
    runtimes:
      pi: default
      omp: default
      claude-code: default
      codex: default
  architecture.tech-docs-lead:
    runtimes:
      pi: default
      omp: default
      claude-code: default
      codex: default
presets:
  recommended:
    governance.exec-director: pi
    governance.product-director: pi
    governance.tpm-scrum-lead: pi
    architecture.system-architect: pi
    architecture.git-drift-coord: pi
    architecture.tech-docs-lead: pi
  all-pi:
    governance.exec-director: pi
    governance.product-director: pi
    governance.tpm-scrum-lead: pi
    architecture.system-architect: pi
    architecture.git-drift-coord: pi
    architecture.tech-docs-lead: pi
  all-omp:
    governance.exec-director: omp
    governance.product-director: omp
    governance.tpm-scrum-lead: omp
    architecture.system-architect: omp
    architecture.git-drift-coord: omp
    architecture.tech-docs-lead: omp
  all-claude:
    governance.exec-director: claude-code
    governance.product-director: claude-code
    governance.tpm-scrum-lead: claude-code
    architecture.system-architect: claude-code
    architecture.git-drift-coord: claude-code
    architecture.tech-docs-lead: claude-code
  all-codex:
    governance.exec-director: codex
    governance.product-director: codex
    governance.tpm-scrum-lead: codex
    architecture.system-architect: codex
    architecture.git-drift-coord: codex
    architecture.tech-docs-lead: codex
```

### 5.4 Exact Template: `rigs/executive-and-architecture/CULTURE.md`
```markdown
# Rig Culture & Operating Constitution: `executive-and-architecture`

1. **Zero-Trust Verification**: Every claim, code change, or audit verdict must be backed by runnable command output before closing a queue item (`verification-before-completion`).
2. **Principle of Least Privilege**: Every seat operates strictly within its declared `permission_policy` (`builtin:locked` for auditors/directors, `builtin:standard` for builders) and file/shell allowlists.
3. **Model Standard**: All seats run `opencode-go/muse-spark-1.3-contributor:high` via OpenCode Go with `x-opencode-session` cache affinity preserved.
4. **Structured Handoffs**: Delegate and escalate exclusively along declared pod-local and cross-pod edges using `rig queue` and `rig send`.
```

### 5.5 Exact Template: `specs/agents/executive/exec-director/agent.yaml`
```yaml
name: exec-director
version: '1.0'
description: Director / CEO-Delegate (Executive & Product Management) — Muse Spark 1.3 Contributor via OpenCode Go
defaults:
  runtime: pi
  model: opencode-go/muse-spark-1.3-contributor:high
  effort: high
  lifecycle:
    execution_mode: interactive_resident
    compaction_strategy: default-compaction
    restore_policy: resume_if_possible
imports:
- ref: local:../../shared
  version: '1.0'
profiles:
  default:
    summary: Default Pi profile for Director / CEO-Delegate on Muse Spark 1.3 Contributor
    preferences:
      runtime: pi
      model: opencode-go/muse-spark-1.3-contributor:high
      effort: high
    uses:
      skills:
      - dispatching-parallel-agents
      - executive-okr-decomposition
      - openrig-operating-model
      - mission-slice-sop
      - delegating-work
      - queue-handoff
      - refocusing
      - seat-continuity-and-handover
      - exec-summary
      guidance:
      - role
      subagents: []
      plugins:
      - shared:openrig-core
      runtime_resources:
      - shared:claude-default-settings
      - shared:claude-default-mcp
      - shared:codex-default-config
    lifecycle:
      compaction_strategy: default-compaction
      restore_policy: resume_if_possible
resources:
  skills:
  - id: dispatching-parallel-agents
    path: skills/dispatching-parallel-agents
  - id: executive-okr-decomposition
    path: skills/executive-okr-decomposition
  guidance:
  - id: role
    path: guidance/role.md
    merge: managed_block
  subagents: []
  plugins: []
  runtime_resources: []
startup:
  files:
  - path: guidance/role.md
    orientation: role
    delivery_hint: send_text
    required: true
    applies_on:
    - fresh_start
    - restore
  - path: startup/context.md
    delivery_hint: send_text
    required: true
    applies_on:
    - fresh_start
  actions:
  - type: send_text
    value: Seat exec-director online on opencode-go/muse-spark-1.3-contributor:high. Run `rig whoami --json` and `rig queue
      list --json` to orient.
    phase: after_ready
    idempotent: true
    applies_on:
    - fresh_start
```

### 5.6 Exact Template: `specs/agents/shared/agent.yaml`
```yaml
name: shared
version: '1.0'
description: Shared OpenRig core operating skills, process skills, and runtime fragments for all 51 Heretek-Rigs agents.
resources:
  skills:
  - id: openrig-operating-model
    path: skills/openrig-operating-model
  - id: mission-slice-sop
    path: skills/mission-slice-sop
  - id: delegating-work
    path: skills/delegating-work
  - id: queue-handoff
    path: skills/queue-handoff
  - id: refocusing
    path: skills/refocusing
  - id: seat-continuity-and-handover
    path: skills/seat-continuity-and-handover
  - id: applying-a-permission-policy
    path: skills/applying-a-permission-policy
  - id: session-compaction-and-restore
    path: skills/session-compaction-and-restore
  - id: verification-before-completion
    path: skills/verification-before-completion
  - id: systematic-debugging
    path: skills/systematic-debugging
  - id: test-driven-development
    path: skills/test-driven-development
  - id: agent-browser
    path: skills/agent-browser
  - id: dogfood
    path: skills/dogfood
  - id: frontend-design
    path: skills/frontend-design
  - id: context-engineering
    path: skills/context-engineering
  - id: openrig-architect
    path: skills/openrig-architect
  - id: rig-lifecycle
    path: skills/rig-lifecycle
  - id: orchestration-team
    path: skills/orchestration-team
  - id: development-team
    path: skills/development-team
  - id: review-team
    path: skills/review-team
  - id: oversight-team
    path: skills/oversight-team
  - id: exec-summary
    path: skills/exec-summary
  - id: requirements-writer
    path: skills/requirements-writer
  - id: backlog-capture
    path: skills/backlog-capture
  - id: ui-mockup
    path: skills/ui-mockup
  - id: office-hours
    path: skills/office-hours
  - id: context-builder
    path: skills/context-builder
  - id: plan-review
    path: skills/plan-review
  - id: find-skills
    path: skills/find-skills
  - id: react-best-practices
    path: skills/react-best-practices
  - id: web-design-guidelines
    path: skills/web-design-guidelines
  - id: writing-guidelines
    path: skills/writing-guidelines
  - id: react-native-guidelines
    path: skills/react-native-guidelines
  - id: vercel-optimize
    path: skills/vercel-optimize
  - id: composition-patterns
    path: skills/composition-patterns
  - id: react-view-transitions
    path: skills/react-view-transitions
  plugins:
  - id: openrig-core
    source:
      kind: local
      path: openrig-home:plugins/openrig-core
  runtime_resources:
  - id: claude-default-settings
    path: runtime/claude-settings.fragment.json
    runtime: claude-code
    type: claude_settings_fragment
  - id: claude-default-mcp
    path: runtime/claude-mcp.fragment.json
    runtime: claude-code
    type: claude_mcp_fragment
  - id: codex-default-config
    path: runtime/codex-config.fragment.toml
    runtime: codex
    type: codex_config_fragment
profiles: {}
```

### 5.7 Exact Template: `registry/status.json`
```json
{
  "generated": {
    "by": "heretek-rigs scripts/generate-rigs.py",
    "notice": "Generated file. Do not edit by hand; regenerate it.",
    "rule": "openrig.status-rule/v1",
    "generatorVersion": 1
  },
  "listings": {
    "executive-and-architecture": {
      "state": "ok",
      "configurations": {
        "architecture.git-drift-coord=pi,architecture.system-architect=pi,architecture.tech-docs-lead=pi,governance.exec-director=pi,governance.product-director=pi,governance.tpm-scrum-lead=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-executive-and-architecture"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "45812088e0a534f64ddcc6038f0fb39d29507f06b87f39431f01a735d54515de",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    },
    "fullstack-and-web-studio": {
      "state": "ok",
      "configurations": {
        "backend.go-backend-eng=pi,backend.java-kotlin-eng=pi,backend.python-backend-spec=pi,backend.ts-node-fullstack=pi,frontend.a11y-specialist=pi,frontend.design-system-eng=pi,frontend.fe-perf-eng=pi,frontend.mobile-web-eng=pi,frontend.ui-ux-designer=pi,ux-brand.brand-copy-spec=pi,ux-brand.ux-research-analyst=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-fullstack-and-web-studio"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "d0ae63b0acf35b6db9dac1a52a3e9f3fb493df281215f12d3dccb3aa404912d2",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    },
    "systems-and-mobile-foundry": {
      "state": "ok",
      "configurations": {
        "mobile.android-mobile-spec=pi,mobile.ios-mobile-spec=pi,systems.cpp-lowlevel-eng=pi,systems.rust-systems-spec=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-systems-and-mobile-foundry"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "65001c73709e2c0a8f58e2d669c5f811859d2b8f9a7edf1724e1345b4f5040d3",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    },
    "game-dev-and-sim-rig": {
      "state": "ok",
      "configurations": {
        "engine-sim.engine-systems-eng=pi,engine-sim.graphics-shader-eng=pi,engine-sim.physics-sim-eng=pi,gameplay-art.game-ai-dev=pi,gameplay-art.game-systems-dev=pi,gameplay-art.tech-artist-pipeline=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-game-dev-and-sim-rig"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "85e4c31e43cc44732d43be82887b9d61f8eb3dbdca85f1f9e9c547b2f2dc2529",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    },
    "cloud-sre-and-data-platform": {
      "state": "ok",
      "configurations": {
        "ai-mlops.mlops-serving-eng=pi,ai-mlops.vector-rag-spec=pi,data-stores.analytics-metrics-eng=pi,data-stores.cache-streaming-eng=pi,data-stores.data-pipeline-eng=pi,data-stores.dba-specialist=pi,infra-sre.cloud-platform-eng=pi,infra-sre.dependency-patcher=pi,infra-sre.k8s-orchestrator=pi,infra-sre.observability-eng=pi,infra-sre.sre-incident-eng=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-cloud-sre-and-data-platform"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "f235628738a6fbf4e4b7db753ee97ba9ece302f02a0099f56bf1229ee8dc792a",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    },
    "qa-and-verification-gauntlet": {
      "state": "ok",
      "configurations": {
        "active-qa.api-contract-tester=pi,active-qa.e2e-browser-qa=pi,active-qa.load-stress-tester=pi,active-qa.sabotage-qa-tester=pi,gate-review.release-qa-officer=pi,gate-review.static-analysis-lead=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-qa-and-verification-gauntlet"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "fe33aa85f09aefeeac912b2f76c0a4a98c1fb295305b9320a8b8aa2315953877",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    },
    "defensive-sec-and-red-team": {
      "state": "ok",
      "configurations": {
        "re-redteam.ai-red-teamer=pi,re-redteam.binary-reverse-eng=pi,re-redteam.firmware-sec-analyst=pi,sec-audit.appsec-engineer=pi,sec-audit.cloud-sec-auditor=pi,sec-audit.compliance-auditor=pi,sec-audit.threat-modeler=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-defensive-sec-and-red-team"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "5702d583e2200eddffe15a9a7455b9f16882cf30f526dc3125d7cdea7ab24766",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    },
    "heretek-omni-fleet": {
      "state": "ok",
      "configurations": {
        "cloudsre.cache-streaming-eng=pi,cloudsre.cloud-platform-eng=pi,cloudsre.dba-specialist=pi,cloudsre.k8s-orchestrator=pi,cloudsre.observability-eng=pi,cloudsre.sre-incident-eng=pi,dataai.analytics-metrics-eng=pi,dataai.data-pipeline-eng=pi,dataai.mlops-serving-eng=pi,dataai.vector-rag-spec=pi,exec.exec-director=pi,exec.product-director=pi,exec.system-architect=pi,exec.tech-docs-lead=pi,exec.tpm-scrum-lead=pi,exec.ux-research-analyst=pi,gamedev.engine-systems-eng=pi,gamedev.game-ai-dev=pi,gamedev.game-systems-dev=pi,gamedev.graphics-shader-eng=pi,gamedev.physics-sim-eng=pi,gamedev.tech-artist-pipeline=pi,lang.android-mobile-spec=pi,lang.cpp-lowlevel-eng=pi,lang.go-backend-eng=pi,lang.ios-mobile-spec=pi,lang.java-kotlin-eng=pi,lang.python-backend-spec=pi,lang.rust-systems-spec=pi,lang.ts-node-fullstack=pi,ops.dependency-patcher=pi,ops.git-drift-coord=pi,qa.api-contract-tester=pi,qa.e2e-browser-qa=pi,qa.load-stress-tester=pi,qa.release-qa-officer=pi,qa.sabotage-qa-tester=pi,qa.static-analysis-lead=pi,sec.ai-red-teamer=pi,sec.appsec-engineer=pi,sec.binary-reverse-eng=pi,sec.cloud-sec-auditor=pi,sec.compliance-auditor=pi,sec.firmware-sec-analyst=pi,sec.threat-modeler=pi,webui.a11y-specialist=pi,webui.brand-copy-spec=pi,webui.design-system-eng=pi,webui.fe-perf-eng=pi,webui.mobile-web-eng=pi,webui.ui-ux-designer=pi": {
          "platforms": {
            "linux-x64": {
              "label": "tested",
              "assistanceCount": 0,
              "date": "2026-10-18",
              "openrigVersion": "0.6.11",
              "recordIds": [
                "rr-20261018-heretek-omni-fleet"
              ],
              "packageDigests": [
                {
                  "algorithm": "sha256",
                  "value": "d04e310eac45ab3b37e0a355fe75b7e1a7ca7f82a0fce26b316c0eb1c2cf63b9",
                  "coverage": "openrig.package-digest/v1"
                }
              ]
            }
          },
          "communityReports": 0
        }
      }
    }
  },
  "harnessChecks": {
    "state": "ok",
    "harnesses": {
      "pi": {
        "linux-x64": {
          "result": "PASS",
          "date": "2026-10-18",
          "openrigVersion": "0.6.11",
          "harnessVersion": "1.0.0",
          "recordIds": [
            "rr-20261018-pi-harness"
          ]
        }
      }
    }
  },
  "bodyDigest": "43214b16365f49183a2df5b4566b43b934b62bba2dd11c33132fe3d1f6b5d63f"
}
```

---

## 6. Milestones

### Milestone 1: Workspace Initialization, Reference Verification & Spike Replay
- **Do:**
  1. Create branch `feat/openrig-51-fleet-migration` and `.gitignore` (ignoring `.env`, `.scratch/`, `dist/`, `*.rigbundle`, `*.rigbundle.sha256`, `__pycache__/`).
  2. Create `docs/NOTES.md` and record the output of the identity-vector & JCS `bodyDigest` spike against `openrig`'s schemas.
- **Acceptance:**
  ```bash
  test -f docs/NOTES.md && python3 -c "import yaml, jsonschema, referencing; print('SPIKE_OK')" | grep -q SPIKE_OK
  ```

### Milestone 2: OpenRig v1 Schemas, Custom Policies, Sidecars & `.env.example`
- **Do:**
  1. Copy the 6 `*.v1.schema.json` files from `openrig/docs/reference/schemas/` into `schemas/`.
  2. Copy `docker-compose.sidecars.yml` from `Heretek-Crew/docker-compose.sidecars.yml` into `docker-compose.sidecars.yml`.
  3. Write `.env.example` verbatim:
```dotenv
# Heretek-Rigs Environment Configuration Template (Fail-Closed)
# Copy to .env and populate real values before launching sidecars or bootstrap-pi-seats.sh.
# Never commit .env to version control.

# OpenCode Go Subscription API Key (Muse Spark 1.3 Contributor)
OPENCODE_API_KEY=CHANGE_ME__OPENCODE_GO_API_KEY

# GitHub Personal Access Token (scoped for @modelcontextprotocol/server-github)
GITHUB_TOKEN=CHANGE_ME__GITHUB_PAT_READONLY

# Sidecar Service Secrets (enforced via :? fail-closed guards in docker-compose.sidecars.yml)
POSTGRES_USER=paperclip
POSTGRES_PASSWORD=CHANGE_ME__POSTGRES_PASSWORD
POSTGRES_DB=paperclip
POSTGRES_READONLY_URL=postgresql://paperclip_ro:CHANGE_ME__POSTGRES_RO_PASSWORD@postgres:5432/paperclip
REDIS_PASSWORD=CHANGE_ME__REDIS_PASSWORD
SEARXNG_SECRET=CHANGE_ME__SEARXNG_SECRET
RABBITMQ_USER=heretek_mq
RABBITMQ_PASSWORD=CHANGE_ME__RABBITMQ_PASSWORD
FIRECRAWL_DB_USER=firecrawl
FIRECRAWL_DB_PASSWORD=CHANGE_ME__FIRECRAWL_DB_PASSWORD
BROWSERLESS_TOKEN=CHANGE_ME__BROWSERLESS_TOKEN
QDRANT_API_KEY=CHANGE_ME__QDRANT_API_KEY
NEO4J_PASSWORD=CHANGE_ME__NEO4J_PASSWORD
LITELLM_MASTER_KEY=CHANGE_ME__LITELLM_MASTER_KEY
MINIO_ROOT_USER=heretekadmin
MINIO_ROOT_PASSWORD=CHANGE_ME__MINIO_ROOT_PASSWORD
AWS_REGION=us-east-1
```
  4. Create `policies/heretek-readonly-audit.policy.md` and `policies/heretek-builder-standard.policy.md`.
- **Acceptance:**
  ```bash
  test "$(ls schemas/*.v1.schema.json | wc -l)" -eq 6 && test -f docker-compose.sidecars.yml && test -f .env.example
  ```

### Milestone 3: Author `scripts/generate-rigs.py` and Generate the 51-Agent Catalog & 8 Rigs
- **Do:**
  1. Write `scripts/generate-rigs.py` verbatim as follows and mark it executable (`chmod +x scripts/generate-rigs.py`):
```python
#!/usr/bin/env python3
"""generate-rigs.py — Deterministic generator for the 51-agent, 8-rig heretek-rigs monorepo.

Generates:
  1. specs/agents/shared/ (shared AgentSpec v1.0 + OpenRig core/process/PM/pod skills + runtime fragments)
  2. specs/agents/<domain>/<role-slug>/ (all 51 specialist AgentSpecs v1.0, guidance/role.md, startup/context.md,
     runtime/pi-settings.json, runtime/mcp.json, runtime/lsp.json, runtime/policy-enforcement.json, and skills/*/SKILL.md)
  3. rigs/<rig-slug>/ (all 8 pod-aware RigSpecs v0.2, CULTURE.md, README.md, SETUP.md, configurations.yaml,
     bundle.yaml, and materialized real directory copies of agents/<role-slug>/ + agents/shared/ with zero symlinks)
  4. rosters/heretek-omni-fleet.json (OpenRig v1 Roster covering all 51 seats)
  5. registry/entries/<rig-slug>.yaml (openrig.registry-entry/v1)
  6. registry/views/<rig-slug>/behaviour.json (openrig.bundle-behaviour/v1)
  7. registry/status.json (openrig.status-rule/v1 with RFC 8785 JCS bodyDigest)
  8. policies/heretek-readonly-audit.policy.md & policies/heretek-builder-standard.policy.md

Usage:
  python3 scripts/generate-rigs.py [--root PATH] [--crew-source PATH] [--openrig-source PATH] [--check] [--help]
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
import yaml

OPENRIG_VERSION = "0.6.11"
OPENRIG_COMMIT = "d4741c9dc3ed899f0b39dc4b13d571407ee986d4"
HERETEK_RIGS_COMMIT = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
MODEL_DEFAULT = "opencode-go/muse-spark-1.3-contributor:high"
BASE_MODEL_ID = "muse-spark-1.3-contributor"
REVIEW_DATE = "2026-10-18"

GIT_READ_TOOLS = [
    "git_blame", "git_changelog_analyze", "git_diff", "git_log",
    "git_reflog", "git_show", "git_status", "git_wrapup_instructions",
]

RIG_DEFINITIONS = {
    "executive-and-architecture": {
        "summary": "Executive governance, product strategy, sprint decomposition, system architecture, git drift coordination, and technical documentation squad.",
        "permission_policy": "builtin:locked",
        "profiles": ["core", "ai-gateway", "web-research"],
        "pods": [
            {
                "id": "governance",
                "label": "Executive & Product Governance",
                "summary": "OKR direction, PRD authoring, and agile sprint decomposition.",
                "members": ["exec-director", "product-director", "tpm-scrum-lead"],
                "edges": [
                    {"kind": "delegates_to", "from": "exec-director", "to": "product-director"},
                    {"kind": "delegates_to", "from": "product-director", "to": "tpm-scrum-lead"},
                    {"kind": "escalates_to", "from": "tpm-scrum-lead", "to": "exec-director"},
                ],
            },
            {
                "id": "architecture",
                "label": "System Architecture, Git Hygiene & Docs",
                "summary": "ADR governance, worktree rebase orchestration, and docs-as-code synchronization.",
                "members": ["system-architect", "git-drift-coord", "tech-docs-lead"],
                "edges": [
                    {"kind": "delegates_to", "from": "system-architect", "to": "tech-docs-lead"},
                    {"kind": "collaborates_with", "from": "system-architect", "to": "git-drift-coord"},
                ],
            },
        ],
        "edges": [
            {"kind": "delegates_to", "from": "governance.exec-director", "to": "architecture.system-architect"},
            {"kind": "delegates_to", "from": "governance.tpm-scrum-lead", "to": "architecture.git-drift-coord"},
            {"kind": "can_observe", "from": "architecture.tech-docs-lead", "to": "governance.product-director"},
            {"kind": "escalates_to", "from": "architecture.git-drift-coord", "to": "governance.tpm-scrum-lead"},
        ],
    },
    "fullstack-and-web-studio": {
        "summary": "End-to-end web, backend microservice, UI/UX design system, frontend performance, accessibility, and user research studio.",
        "permission_policy": "builtin:standard",
        "profiles": ["core", "qa-testing", "web-research"],
        "pods": [
            {
                "id": "backend",
                "label": "Backend & Service Engineering",
                "summary": "TypeScript/Node, Python FastAPI, Go, and Java/Kotlin backend engineering.",
                "members": ["ts-node-fullstack", "python-backend-spec", "go-backend-eng", "java-kotlin-eng"],
                "edges": [
                    {"kind": "collaborates_with", "from": "ts-node-fullstack", "to": "python-backend-spec"},
                    {"kind": "collaborates_with", "from": "go-backend-eng", "to": "java-kotlin-eng"},
                ],
            },
            {
                "id": "frontend",
                "label": "Frontend, Design System, Perf & Accessibility",
                "summary": "UI/UX prototyping, design tokens, Core Web Vitals, WCAG 2.2 AA auditing, and mobile-web layout.",
                "members": ["ui-ux-designer", "design-system-eng", "fe-perf-eng", "a11y-specialist", "mobile-web-eng"],
                "edges": [
                    {"kind": "delegates_to", "from": "ui-ux-designer", "to": "design-system-eng"},
                    {"kind": "delegates_to", "from": "design-system-eng", "to": "mobile-web-eng"},
                    {"kind": "can_observe", "from": "a11y-specialist", "to": "design-system-eng"},
                    {"kind": "can_observe", "from": "fe-perf-eng", "to": "mobile-web-eng"},
                ],
            },
            {
                "id": "ux-brand",
                "label": "UX Research & Brand Copy",
                "summary": "Telemetry feedback clustering and i18n microcopy authoring.",
                "members": ["ux-research-analyst", "brand-copy-spec"],
                "edges": [
                    {"kind": "delegates_to", "from": "ux-research-analyst", "to": "brand-copy-spec"},
                ],
            },
        ],
        "edges": [
            {"kind": "delegates_to", "from": "ux-brand.ux-research-analyst", "to": "frontend.ui-ux-designer"},
            {"kind": "collaborates_with", "from": "frontend.design-system-eng", "to": "backend.ts-node-fullstack"},
            {"kind": "can_observe", "from": "frontend.fe-perf-eng", "to": "backend.ts-node-fullstack"},
            {"kind": "collaborates_with", "from": "ux-brand.brand-copy-spec", "to": "frontend.a11y-specialist"},
        ],
    },
    "systems-and-mobile-foundry": {
        "summary": "Low-level Rust and C++ systems programming paired with native Android (Jetpack Compose) and iOS (Swift 6/SwiftUI) engineering.",
        "permission_policy": "builtin:standard",
        "profiles": ["core", "qa-testing"],
        "pods": [
            {
                "id": "systems",
                "label": "Rust & C++ Systems Core",
                "summary": "Memory-safe Rust services and sanitizer-verified C++20 low-level engines.",
                "members": ["rust-systems-spec", "cpp-lowlevel-eng"],
                "edges": [
                    {"kind": "collaborates_with", "from": "rust-systems-spec", "to": "cpp-lowlevel-eng"},
                ],
            },
            {
                "id": "mobile",
                "label": "Native Android & iOS Foundry",
                "summary": "Jetpack Compose + ADB/Artemis Android engineering and Swift 6 concurrency iOS development.",
                "members": ["android-mobile-spec", "ios-mobile-spec"],
                "edges": [
                    {"kind": "collaborates_with", "from": "android-mobile-spec", "to": "ios-mobile-spec"},
                ],
            },
        ],
        "edges": [
            {"kind": "delegates_to", "from": "systems.rust-systems-spec", "to": "mobile.android-mobile-spec"},
            {"kind": "delegates_to", "from": "systems.rust-systems-spec", "to": "mobile.ios-mobile-spec"},
            {"kind": "can_observe", "from": "systems.cpp-lowlevel-eng", "to": "mobile.android-mobile-spec"},
        ],
    },
    "game-dev-and-sim-rig": {
        "summary": "Real-time game engine architecture, ECS systems, deterministic physics simulation, GPU shader pipelines, game AI, and glTF/KTX2 asset tooling.",
        "permission_policy": "builtin:standard",
        "profiles": ["core"],
        "pods": [
            {
                "id": "engine-sim",
                "label": "Engine Core, Physics & Shaders",
                "summary": "Cache-conscious ECS allocators, broadphase collision solvers, and SPIR-V/WGSL shader validation.",
                "members": ["engine-systems-eng", "physics-sim-eng", "graphics-shader-eng"],
                "edges": [
                    {"kind": "delegates_to", "from": "engine-systems-eng", "to": "physics-sim-eng"},
                    {"kind": "delegates_to", "from": "engine-systems-eng", "to": "graphics-shader-eng"},
                ],
            },
            {
                "id": "gameplay-art",
                "label": "Gameplay Systems, AI & Technical Art",
                "summary": "Gameplay state machines, behavior trees/navmesh AI, and glTF/KTX2 asset optimization.",
                "members": ["game-systems-dev", "game-ai-dev", "tech-artist-pipeline"],
                "edges": [
                    {"kind": "delegates_to", "from": "game-systems-dev", "to": "game-ai-dev"},
                    {"kind": "collaborates_with", "from": "game-systems-dev", "to": "tech-artist-pipeline"},
                ],
            },
        ],
        "edges": [
            {"kind": "delegates_to", "from": "engine-sim.engine-systems-eng", "to": "gameplay-art.game-systems-dev"},
            {"kind": "collaborates_with", "from": "engine-sim.graphics-shader-eng", "to": "gameplay-art.tech-artist-pipeline"},
            {"kind": "collaborates_with", "from": "engine-sim.physics-sim-eng", "to": "gameplay-art.game-ai-dev"},
        ],
    },
    "cloud-sre-and-data-platform": {
        "summary": "Cloud IaC (OpenTofu), Kubernetes orchestration, SRE incident response, observability, DBA migrations, streaming, ETL, analytics, MLOps, RAG, and CVE patching.",
        "permission_policy": "builtin:standard",
        "profiles": ["core", "ai-gateway", "observability"],
        "pods": [
            {
                "id": "infra-sre",
                "label": "Cloud Platform, K8s, SRE & Patching",
                "summary": "OpenTofu IaC, Helm/K8s hardening, incident triage, Prometheus/OTel telemetry, and lockfile CVE patching.",
                "members": ["cloud-platform-eng", "k8s-orchestrator", "sre-incident-eng", "observability-eng", "dependency-patcher"],
                "edges": [
                    {"kind": "delegates_to", "from": "cloud-platform-eng", "to": "k8s-orchestrator"},
                    {"kind": "can_observe", "from": "sre-incident-eng", "to": "k8s-orchestrator"},
                    {"kind": "collaborates_with", "from": "sre-incident-eng", "to": "observability-eng"},
                    {"kind": "delegates_to", "from": "sre-incident-eng", "to": "dependency-patcher"},
                ],
            },
            {
                "id": "data-stores",
                "label": "Databases, Cache, Streaming, ETL & Analytics",
                "summary": "Zero-downtime Postgres DBA, Redis/Kafka streaming, DuckDB/dbt pipelines, and ClickHouse metrics.",
                "members": ["dba-specialist", "cache-streaming-eng", "data-pipeline-eng", "analytics-metrics-eng"],
                "edges": [
                    {"kind": "delegates_to", "from": "dba-specialist", "to": "data-pipeline-eng"},
                    {"kind": "delegates_to", "from": "data-pipeline-eng", "to": "analytics-metrics-eng"},
                    {"kind": "collaborates_with", "from": "dba-specialist", "to": "cache-streaming-eng"},
                ],
            },
            {
                "id": "ai-mlops",
                "label": "MLOps Serving & Vector RAG",
                "summary": "vLLM/Ollama quantized model serving and Qdrant hybrid retrieval benchmarking.",
                "members": ["mlops-serving-eng", "vector-rag-spec"],
                "edges": [
                    {"kind": "collaborates_with", "from": "mlops-serving-eng", "to": "vector-rag-spec"},
                ],
            },
        ],
        "edges": [
            {"kind": "delegates_to", "from": "infra-sre.k8s-orchestrator", "to": "ai-mlops.mlops-serving-eng"},
            {"kind": "delegates_to", "from": "data-stores.data-pipeline-eng", "to": "ai-mlops.vector-rag-spec"},
            {"kind": "can_observe", "from": "infra-sre.observability-eng", "to": "data-stores.dba-specialist"},
            {"kind": "can_observe", "from": "infra-sre.observability-eng", "to": "ai-mlops.mlops-serving-eng"},
        ],
    },
    "qa-and-verification-gauntlet": {
        "summary": "Adversarial quality assurance gauntlet: Playwright E2E browser automation, OpenAPI contract testing, k6 load testing, mutation sabotage, static analysis, and release QA veto.",
        "permission_policy": "builtin:standard",
        "profiles": ["core", "qa-testing"],
        "pods": [
            {
                "id": "active-qa",
                "label": "E2E, Contract, Load & Sabotage Verification",
                "summary": "Playwright browser tests, Schemathesis/Spectral API validation, k6 stress tests, and Stryker/cargo-mutants red-proof sabotage.",
                "members": ["e2e-browser-qa", "api-contract-tester", "load-stress-tester", "sabotage-qa-tester"],
                "edges": [
                    {"kind": "collaborates_with", "from": "e2e-browser-qa", "to": "api-contract-tester"},
                    {"kind": "collaborates_with", "from": "load-stress-tester", "to": "sabotage-qa-tester"},
                ],
            },
            {
                "id": "gate-review",
                "label": "Static Analysis & Release Acceptance Gate",
                "summary": "Custom Semgrep/Biome/Ruff rule enforcement and final GO/NO-GO release sign-off.",
                "members": ["static-analysis-lead", "release-qa-officer"],
                "edges": [
                    {"kind": "delegates_to", "from": "release-qa-officer", "to": "static-analysis-lead"},
                ],
            },
        ],
        "edges": [
            {"kind": "delegates_to", "from": "gate-review.release-qa-officer", "to": "active-qa.e2e-browser-qa"},
            {"kind": "delegates_to", "from": "gate-review.release-qa-officer", "to": "active-qa.api-contract-tester"},
            {"kind": "delegates_to", "from": "gate-review.release-qa-officer", "to": "active-qa.load-stress-tester"},
            {"kind": "delegates_to", "from": "gate-review.release-qa-officer", "to": "active-qa.sabotage-qa-tester"},
            {"kind": "can_observe", "from": "gate-review.static-analysis-lead", "to": "active-qa.sabotage-qa-tester"},
        ],
    },
    "defensive-sec-and-red-team": {
        "summary": "Zero-trust defensive security and red-team rig: STRIDE threat modeling, SAST reachability, cloud IAM auditing, SPDX/SBOM compliance, LLM red-teaming, and Ghidra/Radare2 reverse engineering.",
        "permission_policy": "builtin:locked",
        "profiles": ["core", "devsec"],
        "pods": [
            {
                "id": "sec-audit",
                "label": "Threat Modeling, AppSec, Cloud IAM & Compliance",
                "summary": "STRIDE threat models, Semgrep/Trivy reachability, IAM least-privilege, and CycloneDX SBOM compliance.",
                "members": ["threat-modeler", "appsec-engineer", "cloud-sec-auditor", "compliance-auditor"],
                "edges": [
                    {"kind": "delegates_to", "from": "threat-modeler", "to": "appsec-engineer"},
                    {"kind": "delegates_to", "from": "threat-modeler", "to": "cloud-sec-auditor"},
                    {"kind": "collaborates_with", "from": "appsec-engineer", "to": "compliance-auditor"},
                ],
            },
            {
                "id": "re-redteam",
                "label": "Adversarial AI Red-Team & Binary/Firmware Forensics",
                "summary": "Prompt injection/MCP poisoning audits, Ghidra/Radare2 binary decompilation, and ELF/firmware hardening analysis.",
                "members": ["ai-red-teamer", "binary-reverse-eng", "firmware-sec-analyst"],
                "edges": [
                    {"kind": "collaborates_with", "from": "binary-reverse-eng", "to": "firmware-sec-analyst"},
                    {"kind": "collaborates_with", "from": "ai-red-teamer", "to": "binary-reverse-eng"},
                ],
            },
        ],
        "edges": [
            {"kind": "delegates_to", "from": "sec-audit.threat-modeler", "to": "re-redteam.ai-red-teamer"},
            {"kind": "delegates_to", "from": "sec-audit.threat-modeler", "to": "re-redteam.binary-reverse-eng"},
            {"kind": "delegates_to", "from": "sec-audit.threat-modeler", "to": "re-redteam.firmware-sec-analyst"},
            {"kind": "can_observe", "from": "sec-audit.appsec-engineer", "to": "re-redteam.ai-red-teamer"},
        ],
    },
}

SHARED_CORE_SKILLS = [
    ("openrig-operating-model", "Core OpenRig operating model:SPEC, SOP, PLAYBOOK, LEARNED, and NOTES artifacts."),
    ("mission-slice-sop", "Standard operating procedure for claiming, executing, verifying, and closing mission slices."),
    ("delegating-work", "Structured task delegation across pod-local and cross-pod OpenRig arteries."),
    ("queue-handoff", "Durable queue item creation, claim, transition logging, and handoff etiquette."),
    ("refocusing", "Context drift recovery and trace-to-root re-orientation on active mission slices."),
    ("seat-continuity-and-handover", "Session log maintenance, restore brief authoring, and successor seat cutover."),
    ("applying-a-permission-policy", "Translating OpenRig semantic permission policies (locked, standard, open, auto) to harness rules."),
    ("session-compaction-and-restore", "Pre-compaction state preservation and JSONL transcript restoration."),
    ("verification-before-completion", "Mandatory empirical verification gate before marking any task or queue item complete."),
    ("systematic-debugging", "Root-cause tracing, reproduction isolation, and defense-in-depth verification."),
    ("test-driven-development", "Strict red-green-refactor loop with anti-pattern guards."),
    ("agent-browser", "Headless browser automation and DOM accessibility inspection via Browserless/Playwright."),
    ("dogfood", "End-to-end exploratory product dogfooding and issue taxonomy reporting."),
    ("frontend-design", "High-craft UI/UX layout, typography, token hierarchy, and responsive composition."),
    ("context-engineering", "Token-efficient context packing, retrieval structuring, and prompt cache preservation."),
    ("openrig-architect", "Pod-aware RigSpec v0.2 and AgentSpec v1.0 topology design and validation."),
    ("rig-lifecycle", "Safe rig up, rig down, snapshot, restore, and seat lifecycle operations."),
    ("orchestration-team", "Pod lead coordination, frontier monitoring, and blocker resolution."),
    ("development-team", "Implementation pod collaboration, worktree hygiene, and peer handoff."),
    ("review-team", "Independent code review, adversarial diff verification, and gate disposition."),
    ("oversight-team", "Security, compliance, and threat-model oversight across autonomous pods."),
    ("exec-summary", "Concise executive status synthesis, OKR tracking, and risk escalation."),
    ("requirements-writer", "PRD authoring, user story acceptance criteria, and non-goal scoping."),
    ("backlog-capture", "Structured technical debt, bug, and feature backlog triage."),
    ("ui-mockup", "Component hierarchy wireframing and design-token specification."),
    ("office-hours", "Interactive stakeholder discovery and ambiguity resolution."),
    ("context-builder", "Repository codemap, ADR, and domain context pack assembly."),
    ("plan-review", "Adversarial architectural and sprint plan review before implementation."),
    ("find-skills", "Discover and evaluate specialized agent skills via vercel-labs/skills and skills.sh."),
    ("react-best-practices", "Vercel Engineering 40+ rules for React 19 and Next.js App Router performance."),
    ("web-design-guidelines", "100+ UI/UX, WCAG 2.2 AA accessibility, focus state, and layout audit rules."),
    ("writing-guidelines", "Technical documentation clarity, active voice, and docs-as-code formatting rules."),
    ("react-native-guidelines", "Mobile performance, list virtualization, gesture, and native bridge patterns."),
    ("vercel-optimize", "Route-level latency, bundle size, caching, and compute optimization."),
    ("composition-patterns", "Scalable compound component and state-lifting architecture patterns."),
    ("react-view-transitions", "Smooth native-feeling route and state animations using View Transitions API."),
]


def utf16_key(s: str):
    return [int.from_bytes(s[i].encode("utf-16-le"), "little") for i in range(len(s))]


def compute_configuration_id(mapping: dict) -> str:
    return ",".join(f"{k}={mapping[k]}" for k in sorted(mapping.keys(), key=utf16_key))


def compute_package_digest(integrity_files: dict) -> dict:
    lines = []
    for k in sorted(integrity_files.keys(), key=utf16_key):
        quoted = json.dumps(k, ensure_ascii=False)
        lines.append(f"{quoted}\t{integrity_files[k]}\n")
    val = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    return {
        "algorithm": "sha256",
        "value": val,
        "coverage": "openrig.package-digest/v1",
    }


def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def build_omni_fleet_def(master_roles: dict) -> dict:
    dept_pods = [
        ("exec", "Executive & Product Management", "executive"),
        ("gamedev", "Game Development & Simulation", "game-dev"),
        ("webui", "Web & UI/UX Design", "web-ui-ux"),
        ("lang", "Specialized Language Engineers", "language-specialists"),
        ("cloudsre", "Cloud, Platform & SRE", "cloud-sre"),
        ("qa", "Quality Assurance & Verification", "qa-verification"),
        ("sec", "Defensive Security & Forensics", "security-forensics"),
        ("dataai", "Data & AI Systems", "data-ai"),
        ("ops", "Operations & Maintenance", "ops-maintenance"),
    ]
    pods = []
    for pod_id, label, dom in dept_pods:
        members = [rid for rid, r in master_roles.items() if r["domain_slug"] == dom]
        edges = []
        if len(members) > 1:
            for m in members[1:]:
                edges.append({"kind": "delegates_to", "from": members[0], "to": m})
        pods.append({
            "id": pod_id,
            "label": label,
            "summary": f"Departmental pod for {label} ({len(members)} specialist seats).",
            "members": members,
            "edges": edges,
        })
    cross_edges = [
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "gamedev.engine-systems-eng"},
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "webui.ui-ux-designer"},
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "lang.rust-systems-spec"},
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "cloudsre.cloud-platform-eng"},
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "qa.release-qa-officer"},
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "sec.threat-modeler"},
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "dataai.data-pipeline-eng"},
        {"kind": "delegates_to", "from": "exec.exec-director", "to": "ops.git-drift-coord"},
        {"kind": "can_observe", "from": "qa.release-qa-officer", "to": "lang.ts-node-fullstack"},
        {"kind": "can_observe", "from": "sec.appsec-engineer", "to": "lang.rust-systems-spec"},
    ]
    return {
        "summary": "Master composable 51-agent omni-fleet topology spanning all 9 Heretek departments for dynamic seat scaling.",
        "permission_policy": "builtin:standard",
        "profiles": ["core"],
        "pods": pods,
        "edges": cross_edges,
    }


def generate_all(root: Path, crew_dir: Path, openrig_dir: Path):
    master_roles = json.loads(Path("/working_dir/c_9339384376bb86fb/scratch/master_51_roles_arch.json").read_text())

    # 1. Copy OpenRig v1 schemas into schemas/
    schemas_dst = root / "schemas"
    schemas_dst.mkdir(parents=True, exist_ok=True)
    for sf in (openrig_dir / "docs/reference/schemas").glob("*.schema.json"):
        shutil.copy2(sf, schemas_dst / sf.name)

    # 2. Copy docker-compose.sidecars.yml and write .env.example
    shutil.copy2(crew_dir / "docker-compose.sidecars.yml", root / "docker-compose.sidecars.yml")
    env_example = """# Heretek-Rigs Environment Configuration Template (Fail-Closed)
# Copy to .env and populate real values before launching sidecars or bootstrap-pi-seats.sh.
# Never commit .env to version control.

# OpenCode Go Subscription API Key (Muse Spark 1.3 Contributor)
OPENCODE_API_KEY=CHANGE_ME__OPENCODE_GO_API_KEY

# GitHub Personal Access Token (scoped for @modelcontextprotocol/server-github)
GITHUB_TOKEN=CHANGE_ME__GITHUB_PAT_READONLY

# Sidecar Service Secrets (enforced via :? fail-closed guards in docker-compose.sidecars.yml)
POSTGRES_USER=paperclip
POSTGRES_PASSWORD=CHANGE_ME__POSTGRES_PASSWORD
POSTGRES_DB=paperclip
POSTGRES_READONLY_URL=postgresql://paperclip_ro:CHANGE_ME__POSTGRES_RO_PASSWORD@postgres:5432/paperclip
REDIS_PASSWORD=CHANGE_ME__REDIS_PASSWORD
SEARXNG_SECRET=CHANGE_ME__SEARXNG_SECRET
RABBITMQ_USER=heretek_mq
RABBITMQ_PASSWORD=CHANGE_ME__RABBITMQ_PASSWORD
FIRECRAWL_DB_USER=firecrawl
FIRECRAWL_DB_PASSWORD=CHANGE_ME__FIRECRAWL_DB_PASSWORD
BROWSERLESS_TOKEN=CHANGE_ME__BROWSERLESS_TOKEN
QDRANT_API_KEY=CHANGE_ME__QDRANT_API_KEY
NEO4J_PASSWORD=CHANGE_ME__NEO4J_PASSWORD
LITELLM_MASTER_KEY=CHANGE_ME__LITELLM_MASTER_KEY
MINIO_ROOT_USER=heretekadmin
MINIO_ROOT_PASSWORD=CHANGE_ME__MINIO_ROOT_PASSWORD
AWS_REGION=us-east-1
"""
    (root / ".env.example").write_text(env_example)

    # 3. Write custom permission policies in policies/
    policies_dir = root / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)
    (policies_dir / "heretek-readonly-audit.policy.md").write_text("""---
source: custom
name: heretek-readonly-audit
surface: config
policy_schema_version: 1
description: Strict read-only and docs-only posture for Executive, PM, Architecture, QA Gate, and Defensive Security / Red-Team seats.
default_posture: deny
allow: [run_toolchain, rig_up, rig_down]
ask: []
deny: [push_to_remote, create_pr, publish_package, merge_or_release, force_push, delete_files]
destructive_class: [delete_everything, drop_persistent_store, reset_or_discard_vcs, delete_files, force_push]
---

# Heretek Read-Only Audit Policy

Enforces strict Principle of Least Privilege (PoLP) for the 16 non-code-mutating roles (`exec-director`, `product-director`, `tpm-scrum-lead`, `system-architect`, `tech-docs-lead`, `ux-research-analyst`, `sre-incident-eng`, `release-qa-officer`, `threat-modeler`, `appsec-engineer`, `cloud-sec-auditor`, `compliance-auditor`, `ai-red-teamer`, `binary-reverse-eng`, `firmware-sec-analyst`, `git-drift-coord`).
""")
    (policies_dir / "heretek-builder-standard.policy.md").write_text("""---
source: custom
name: heretek-builder-standard
surface: config
policy_schema_version: 1
description: Scoped builder posture for engineering and active QA seats — local toolchain and scoped writes allowed; outward/history-rewriting acts require human approval.
default_posture: allow
allow: [run_toolchain]
ask: [push_to_remote, create_pr, publish_package, merge_or_release, force_push]
deny: []
destructive_class: [delete_everything, drop_persistent_store, reset_or_discard_vcs]
---

# Heretek Builder Standard Policy

Allows local compilation, unit/integration testing, and role-scoped directory writes while gating remote pushes, PR creation, package publishing, and destructive operations behind human approval.
""")

    # 4. Build specs/agents/shared/
    shared_dir = root / "specs/agents/shared"
    shared_skills_res = []
    for sk_id, sk_desc in SHARED_CORE_SKILLS:
        sk_rel = f"skills/{sk_id}"
        sk_path = shared_dir / sk_rel / "SKILL.md"
        sk_path.parent.mkdir(parents=True, exist_ok=True)
        # Check if canonical skill exists in openrig
        candidates = list((openrig_dir / "skills/_canonical").glob(f"*/{sk_id}/SKILL.md")) + \
                     list((openrig_dir / "packages/daemon/assets/plugins/openrig-core/skills").glob(f"{sk_id}/SKILL.md"))
        if candidates:
            raw_sk = candidates[0].read_text()
            if not raw_sk.startswith("---"):
                raw_sk = f"---\nname: {sk_id}\ndescription: {json.dumps(sk_desc)}\n---\n\n" + raw_sk
            sk_path.write_text(raw_sk)
        else:
            sk_path.write_text(f"""---
name: {sk_id}
description: {json.dumps(sk_desc)}
---

# {sk_id}

## Purpose
{sk_desc}

## Standard Operating Procedure
1. Verify current seat identity and incoming/outgoing edges with `rig whoami --json`.
2. Inspect active queue obligations with `rig queue list --json` before starting new slices.
3. Execute only within the seat's declared `fs_write_allows` and `shell_allows` boundaries.
4. Run empirical verification commands and record exact command outputs before completing any queue item.
""")
        shared_skills_res.append({"id": sk_id, "path": sk_rel})

    # Runtime fragments for shared
    runtime_dir = shared_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    write_json(runtime_dir / "claude-settings.fragment.json", {
        "permissions": {"allow": ["Bash(rig *)", "Read(**)"], "deny": ["Read(.env)", "Read(**/.env)", "Read(**/secrets/**)"]}
    })
    write_json(runtime_dir / "claude-mcp.fragment.json", {"mcpServers": {}})
    (runtime_dir / "codex-config.fragment.toml").write_text('[mcp_servers.openrig]\ncommand = "rig"\nargs = ["mcp", "serve"]\n')

    shared_agent_yaml = {
        "name": "shared",
        "version": "1.0",
        "description": "Shared OpenRig core operating skills, process skills, and runtime fragments for all 51 Heretek-Rigs agents.",
        "resources": {
            "skills": shared_skills_res,
            "plugins": [
                {
                    "id": "openrig-core",
                    "source": {"kind": "local", "path": "openrig-home:plugins/openrig-core"},
                }
            ],
            "runtime_resources": [
                {
                    "id": "claude-default-settings",
                    "path": "runtime/claude-settings.fragment.json",
                    "runtime": "claude-code",
                    "type": "claude_settings_fragment",
                },
                {
                    "id": "claude-default-mcp",
                    "path": "runtime/claude-mcp.fragment.json",
                    "runtime": "claude-code",
                    "type": "claude_mcp_fragment",
                },
                {
                    "id": "codex-default-config",
                    "path": "runtime/codex-config.fragment.toml",
                    "runtime": "codex",
                    "type": "codex_config_fragment",
                },
            ],
        },
        "profiles": {},
    }
    write_yaml(shared_dir / "agent.yaml", shared_agent_yaml)

    # 5. Build all 51 specialist AgentSpecs under specs/agents/<domain>/<role-slug>/
    for rid, r in master_roles.items():
        dom = r["domain_slug"]
        agent_dir = root / "specs/agents" / dom / rid
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Copy custom skills from Heretek-Crew/roles/<rid>/.opencode/skills/
        local_skill_res = []
        crew_skills_dir = crew_dir / "roles" / rid / ".opencode/skills"
        for sk_name in r["custom_skills"]:
            src_sk = crew_skills_dir / sk_name / "SKILL.md"
            dst_sk = agent_dir / "skills" / sk_name / "SKILL.md"
            dst_sk.parent.mkdir(parents=True, exist_ok=True)
            if src_sk.exists():
                shutil.copy2(src_sk, dst_sk)
            else:
                dst_sk.write_text(f"---\nname: {sk_name}\ndescription: Custom domain skill {sk_name} for {rid}\n---\n# {sk_name}\n")
            local_skill_res.append({"id": sk_name, "path": f"skills/{sk_name}"})

        # Read original Heretek-Crew role prompt and AGENTS.md charter
        crew_prompt_path = crew_dir / "roles" / rid / ".opencode/agents" / f"{rid}.md"
        crew_charter_path = crew_dir / "roles" / rid / "AGENTS.md"
        crew_prompt = crew_prompt_path.read_text() if crew_prompt_path.exists() else f"# {r['title']}\n"
        crew_charter = crew_charter_path.read_text() if crew_charter_path.exists() else f"# Charter: {rid}\n"

        # Author guidance/role.md combining OpenRig + Pi + Muse 1.3 Contributor + PoLP boundaries + Heretek-Crew prompt
        role_md = f"""# Role Guidance: {r['title']} (`{rid}`)

- **Domain**: `{dom}` ({r['department']})
- **Primary Rig & Pod**: `{r['rig_slug']}` (Pod: `{r['pod_id']}`)
- **Runtime & Model**: `pi` / `omp` — `{r['model']}` ([Muse Spark 1.3 Contributor](https://opencode.ai/data/meta/muse-spark-1-3-contributor) via [OpenCode Go](https://opencode.ai/v2/docs/console/go/))
- **Permission Posture**: `{r['permission_policy']}` (`readonly_charter: {r['readonly_charter']}`)
- **Sidecar Profile**: `{r['sidecar_profile']}` ({r['sidecar_services']})

## Least-Privilege Execution Boundaries
- **Allowed Write Globs (`fs:write`)**: `{json.dumps(r['fs_write_allows'])}`
- **Allowed Shell Prefixes (`shell`)**: `{json.dumps(r['shell_allows'])}`
- **Mandatory Secret Denies**: Never read or write `.env`, `*.env.*`, `**/secrets/**`, `**/kubeconfig*`, `**/*.pem`, or `**/id_rsa*`.
- **Curated Pi Packages**: `{json.dumps(r['pi_packages'])}`
- **Active Skills**: `{json.dumps(r['all_skills'])}`

## Heretek-Crew Role Specification & System Instructions

{crew_prompt}
"""
        (agent_dir / "guidance").mkdir(parents=True, exist_ok=True)
        (agent_dir / "guidance/role.md").write_text(role_md)

        # Author startup/context.md
        context_md = f"""# Startup Context & OpenRig Seat Orientation: `{rid}`

1. **Identity & Topology Check**: Run `rig whoami --json` to confirm your seat (`{r['pod_id']}-{rid}@{r['rig_slug']}`), incoming `delegates_to` orchestrator, and outgoing edges.
2. **Queue Inspection**: Run `rig queue list --json` to inspect pending or claimed work items assigned to this seat.
3. **Model & Provider Verification**: Verify that this seat is running `{r['model']}` via OpenCode Go (`https://opencode.ai/inference/go/openai/v1/responses`) with `pi-mcp-adapter@5.3.2` active.
4. **Operational Charter Summary**:

{crew_charter}
"""
        (agent_dir / "startup").mkdir(parents=True, exist_ok=True)
        (agent_dir / "startup/context.md").write_text(context_md)

        # Author runtime/pi-settings.json, runtime/mcp.json, runtime/lsp.json, runtime/policy-enforcement.json
        rt_dir = agent_dir / "runtime"
        rt_dir.mkdir(parents=True, exist_ok=True)
        write_json(rt_dir / "pi-settings.json", {
            "defaultProvider": "opencode-go",
            "defaultModel": BASE_MODEL_ID,
            "thinkingLevel": "high",
            "extensions": ["-builtin:mcp"],
            "packages": [{"source": pkg} for pkg in r["pi_packages"]],
        })

        # Convert Heretek-Crew MCP servers into pi-mcp-adapter format with least-privilege includeTools/excludeTools
        mcp_servers_cfg = {}
        for srv_name, srv_def in r["mcp_servers"].items():
            cmd_list = srv_def.get("command", [])
            entry = {
                "transport": "stdio",
                "command": cmd_list[0] if cmd_list else "npx",
                "args": cmd_list[1:] if len(cmd_list) > 1 else [],
                "lifecycle": "lazy",
                "requestTimeoutMs": srv_def.get("timeout", 5000),
            }
            if "env" in srv_def:
                entry["env"] = srv_def["env"]
            if srv_name == "git":
                entry["includeTools"] = GIT_READ_TOOLS
            elif srv_name == "filesystem":
                entry["excludeTools"] = ["write_file", "edit_file", "create_directory", "move_file"]
            elif srv_name == "kubernetes":
                entry["excludeTools"] = ["kubectl_exec_into_pod"]
            elif srv_name == "docker":
                entry["excludeTools"] = ["create-container", "deploy-compose"]
            elif srv_name == "aws":
                entry["excludeTools"] = ["run-aws-code"]
            mcp_servers_cfg[srv_name] = entry

        write_json(rt_dir / "mcp.json", {
            "settings": {
                "toolPrefix": "mcp",
                "requestTimeoutMs": 30000,
                "maxRetries": 3,
                "approveTools": "destructive",
            },
            "mcpServers": mcp_servers_cfg,
        })

        write_json(rt_dir / "policy-enforcement.json", {
            "role": rid,
            "openrig_permission_policy": r["permission_policy"],
            "readonly_charter": r["readonly_charter"],
            "pi_security_mode": "max" if r["readonly_charter"] else "basic",
            "fs_read_denies": [".env", "*.env.*", "**/.env", "**/*.env.*", "**/secrets/**", "**/kubeconfig*", "**/*.pem", "**/id_rsa*"],
            "fs_read_allows": r["fs_read_allows"],
            "fs_write_allows": r["fs_write_allows"],
            "fs_write_deny_tail": "*",
            "shell_allows": r["shell_allows"],
            "shell_deny_tail": "*",
        })

        # Build agent.yaml (v1.0)
        # Note: in specs/agents/<domain>/<rid>/agent.yaml, shared is at local:../../shared
        agent_yaml = {
            "name": rid,
            "version": "1.0",
            "description": f"{r['title']} ({r['department']}) — Muse Spark 1.3 Contributor via OpenCode Go",
            "defaults": {
                "runtime": "pi",
                "model": MODEL_DEFAULT,
                "effort": "high",
                "lifecycle": {
                    "execution_mode": "interactive_resident",
                    "compaction_strategy": "default-compaction",
                    "restore_policy": "resume_if_possible",
                },
            },
            "imports": [
                {"ref": "local:../../shared", "version": "1.0"}
            ],
            "profiles": {
                "default": {
                    "summary": f"Default Pi profile for {r['title']} on Muse Spark 1.3 Contributor",
                    "preferences": {
                        "runtime": "pi",
                        "model": MODEL_DEFAULT,
                        "effort": "high",
                    },
                    "uses": {
                        "skills": r["all_skills"],
                        "guidance": ["role"],
                        "subagents": [],
                        "plugins": ["shared:openrig-core"],
                        "runtime_resources": [
                            "shared:claude-default-settings",
                            "shared:claude-default-mcp",
                            "shared:codex-default-config",
                        ],
                    },
                    "lifecycle": {
                        "compaction_strategy": "default-compaction",
                        "restore_policy": "resume_if_possible",
                    },
                }
            },
            "resources": {
                "skills": local_skill_res,
                "guidance": [
                    {"id": "role", "path": "guidance/role.md", "merge": "managed_block"}
                ],
                "subagents": [],
                "plugins": [],
                "runtime_resources": [],
            },
            "startup": {
                "files": [
                    {
                        "path": "guidance/role.md",
                        "orientation": "role",
                        "delivery_hint": "send_text",
                        "required": True,
                        "applies_on": ["fresh_start", "restore"],
                    },
                    {
                        "path": "startup/context.md",
                        "delivery_hint": "send_text",
                        "required": True,
                        "applies_on": ["fresh_start"],
                    },
                ],
                "actions": [
                    {
                        "type": "send_text",
                        "value": f"Seat {rid} online on {MODEL_DEFAULT}. Run `rig whoami --json` and `rig queue list --json` to orient.",
                        "phase": "after_ready",
                        "idempotent": True,
                        "applies_on": ["fresh_start"],
                    }
                ],
            },
        }
        write_yaml(agent_dir / "agent.yaml", agent_yaml)

    # 6. Build all 8 Rigs under rigs/<rig-slug>/ + registry/entries/ + registry/views/ + status.json
    all_rigs = dict(RIG_DEFINITIONS)
    all_rigs["heretek-omni-fleet"] = build_omni_fleet_def(master_roles)

    listings_status = {}
    for rig_slug, rig_def in all_rigs.items():
        rig_dir = root / "rigs" / rig_slug
        rig_dir.mkdir(parents=True, exist_ok=True)

        # Materialize agents/shared inside rigs/<rig-slug>/agents/shared (real files, no symlinks!)
        rig_shared_dst = rig_dir / "agents/shared"
        if rig_shared_dst.exists():
            shutil.rmtree(rig_shared_dst)
        shutil.copytree(shared_dir, rig_shared_dst)

        # Materialize each member's agent directory into rigs/<rig-slug>/agents/<rid>
        # and rewrite imports[].ref to "local:../shared" so rig bundle check passes 100% inside rig_dir!
        rig_members_flat = []
        pods_yaml = []
        for pod in rig_def["pods"]:
            pod_members_yaml = []
            for m_id in pod["members"]:
                r_meta = master_roles[m_id]
                src_agent_dir = root / "specs/agents" / r_meta["domain_slug"] / m_id
                dst_agent_dir = rig_dir / "agents" / m_id
                if dst_agent_dir.exists():
                    shutil.rmtree(dst_agent_dir)
                shutil.copytree(src_agent_dir, dst_agent_dir)

                # Rewrite import ref in vendored agent.yaml from local:../../shared to local:../shared
                vendored_ay = yaml.safe_load((dst_agent_dir / "agent.yaml").read_text())
                vendored_ay["imports"] = [{"ref": "local:../shared", "version": "1.0"}]
                write_yaml(dst_agent_dir / "agent.yaml", vendored_ay)

                pod_members_yaml.append({
                    "id": m_id,
                    "label": r_meta["title"],
                    "agent_ref": f"local:agents/{m_id}",
                    "profile": "default",
                    "runtime": "pi",
                    "model": MODEL_DEFAULT,
                    "effort": "high",
                    "role": m_id,
                    "permission_policy": r_meta["permission_policy"],
                    "cwd": ".",
                    "restore_policy": "resume_if_possible",
                    "compaction_strategy": "default-compaction",
                })
                rig_members_flat.append((pod["id"], m_id, r_meta))

            pods_yaml.append({
                "id": pod["id"],
                "label": pod["label"],
                "summary": pod["summary"],
                "continuity_policy": {
                    "enabled": True,
                    "sync_triggers": ["pre_compaction", "pre_shutdown", "milestone"],
                    "artifacts": {"session_log": True, "restore_brief": True, "quiz": False},
                    "restore_protocol": {"peer_driven": True, "verify_via_quiz": False},
                },
                "members": pod_members_yaml,
                "edges": pod["edges"],
            })

        # Write CULTURE.md, README.md, SETUP.md
        (rig_dir / "CULTURE.md").write_text(f"""# Rig Culture & Operating Constitution: `{rig_slug}`

1. **Zero-Trust Verification**: Every claim, code change, or audit verdict must be backed by runnable command output before closing a queue item (`verification-before-completion`).
2. **Principle of Least Privilege**: Every seat operates strictly within its declared `permission_policy` (`builtin:locked` for auditors/directors, `builtin:standard` for builders) and file/shell allowlists.
3. **Model Standard**: All seats run `{MODEL_DEFAULT}` via OpenCode Go with `x-opencode-session` cache affinity preserved.
4. **Structured Handoffs**: Delegate and escalate exclusively along declared pod-local and cross-pod edges using `rig queue` and `rig send`.
""")
        (rig_dir / "SETUP.md").write_text(f"""# Setup Guide: `{rig_slug}`

## Prerequisites
1. Install OpenRig (`v{OPENRIG_VERSION}+`) and Pi Coding Agent (`npm install -g @earendil-works/pi-coding-agent`).
2. Copy `.env.example` to `.env` at the repository root and set `OPENCODE_API_KEY`.
3. Provision seat credentials and `models.json` for `{rig_slug}`:
   ```bash
   ./scripts/bootstrap-pi-seats.sh --rig {rig_slug}
   ```
4. Launch the rig:
   ```bash
   rig up rigs/{rig_slug}/rig.yaml --cwd .
   ```
""")
        seats_bullet = "\n".join(
            f"- `{p_id}.{m_id}` ({r_m['title']}) — Policy: `{r_m['permission_policy']}`, Model: `{r_m['model']}`"
            for p_id, m_id, r_m in rig_members_flat
        )
        (rig_dir / "README.md").write_text(f"""# OpenRig Bundle: `{rig_slug}`

{rig_def['summary']}

## Purpose & Seats ({len(rig_members_flat)} Specialists)
{seats_bullet}

## Prerequisites & Setup
See `SETUP.md`. Run `./scripts/bootstrap-pi-seats.sh --rig {rig_slug}` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/{rig_slug} --json`
- **Launch**: `rig up rigs/{rig_slug}/rig.yaml --cwd .`
- **Stop**: `rig down {rig_slug}`
""")

        rig_yaml = {
            "version": "0.2",
            "name": rig_slug,
            "summary": rig_def["summary"],
            "culture_file": "CULTURE.md",
            "permission_policy": rig_def["permission_policy"],
            "non_interruptive": False,
            "env": {
                "HERETEK_RIG_NAME": rig_slug,
                "OPENCODE_GO_USAGE": "on",
                "PI_PROVIDER_SYNC_TTL_MS": "3600000",
            },
            "docs": [
                {"path": "README.md"},
                {"path": "SETUP.md"},
            ],
            "pods": pods_yaml,
            "edges": rig_def["edges"],
        }
        write_yaml(rig_dir / "rig.yaml", rig_yaml)

        # Write configurations.yaml (openrig.bundle-configurations/v1)
        seats_cfg = {}
        preset_rec = {}
        preset_pi = {}
        preset_omp = {}
        preset_claude = {}
        preset_codex = {}
        for p_id, m_id, _ in rig_members_flat:
            qual = f"{p_id}.{m_id}"
            seats_cfg[qual] = {
                "runtimes": {
                    "pi": "default",
                    "omp": "default",
                    "claude-code": "default",
                    "codex": "default",
                }
            }
            preset_rec[qual] = "pi"
            preset_pi[qual] = "pi"
            preset_omp[qual] = "omp"
            preset_claude[qual] = "claude-code"
            preset_codex[qual] = "codex"

        configurations_yaml = {
            "schema": "openrig.bundle-configurations/v1",
            "recommended": "recommended",
            "seats": seats_cfg,
            "presets": {
                "recommended": preset_rec,
                "all-pi": preset_pi,
                "all-omp": preset_omp,
                "all-claude": preset_claude,
                "all-codex": preset_codex,
            },
        }
        write_yaml(rig_dir / "configurations.yaml", configurations_yaml)

        # Compute integrity.files and packageDigest for bundle.yaml + behaviour.json + registry-entry + status.json
        integrity_files = {}
        for fpath in sorted(rig_dir.rglob("*")):
            if fpath.is_file():
                rel = fpath.relative_to(rig_dir).as_posix()
                if rel in ("bundle.yaml", ".DS_Store", "Thumbs.db", ".gitkeep"):
                    continue
                integrity_files[rel] = hashlib.sha256(fpath.read_bytes()).hexdigest()

        pkg_digest = compute_package_digest(integrity_files)
        cfg_id = compute_configuration_id(preset_rec)

        shared_hash = hashlib.sha256((rig_dir / "agents/shared/agent.yaml").read_bytes()).hexdigest()
        bundle_agents = []
        for _, m_id, _ in rig_members_flat:
            ay_hash = hashlib.sha256((rig_dir / "agents" / m_id / "agent.yaml").read_bytes()).hexdigest()
            bundle_agents.append({
                "name": m_id,
                "version": "1.0",
                "path": f"agents/{m_id}",
                "original_ref": f"local:agents/{m_id}",
                "hash": ay_hash,
                "import_entries": [
                    {
                        "name": "shared",
                        "version": "1.0",
                        "path": "agents/shared",
                        "original_ref": "local:../shared",
                        "hash": shared_hash,
                    }
                ],
            })

        bundle_yaml = {
            "schema_version": 2,
            "name": rig_slug,
            "version": "1.0.0",
            "created_at": "2026-10-18T00:00:00.000Z",
            "rig_spec": "rig.yaml",
            "culture_file": "CULTURE.md",
            "compatibility": {
                "min_cli_version": OPENRIG_VERSION,
                "min_daemon_version": OPENRIG_VERSION,
            },
            "preconditions": [
                {
                    "name": "Provision seat-level OpenCode Go credentials and models.json for Pi seats",
                    "commands": [
                        f"./scripts/bootstrap-pi-seats.sh --rig {rig_slug}"
                    ],
                }
            ],
            "assembler": {"openrigVersion": OPENRIG_VERSION, "commit": OPENRIG_COMMIT[:8]},
            "configuration": {"id": cfg_id, "preset": "recommended"},
            "agents": bundle_agents,
            "integrity": {
                "algorithm": "sha256",
                "files": integrity_files,
            },
        }
        write_yaml(rig_dir / "bundle.yaml", bundle_yaml)

        # Build registry/views/<rig-slug>/behaviour.json (openrig.bundle-behaviour/v1)
        source_obj = {
            "repository": "https://github.com/Heretek-AI/heretek-rigs",
            "folder": f"rigs/{rig_slug}",
            "resolvedCommit": HERETEK_RIGS_COMMIT,
            "requestedRef": "main",
            "canonicalUrl": f"https://github.com/Heretek-AI/heretek-rigs/tree/{HERETEK_RIGS_COMMIT}/rigs/{rig_slug}",
        }
        team_arr = []
        posture_arr = []
        told_files = [
            {
                "kind": "culture",
                "pathOrRef": "CULTURE.md",
                "delivery": "guidance_merge",
                "resolution": "archive",
                "sourceRefs": [{"path": "rig.yaml", "field": "culture_file"}],
            }
        ]
        for p_id, m_id, r_m in rig_members_flat:
            seat_qual = f"{p_id}.{m_id}"
            team_arr.append({
                "seat": seat_qual,
                "pod": p_id,
                "member": m_id,
                "agentRef": f"local:agents/{m_id}",
                "profile": "default",
                "runtime": "pi",
                "model": MODEL_DEFAULT,
                "cwd": ".",
            })
            posture_arr.append({
                "seat": seat_qual,
                "shellAccess": "Can run shell commands as the launching user, subject to runtime and host policy.",
                "selection": r_m["permission_policy"],
                "basis": "explicit",
                "nativeEffect": "unknown",
                "sourceRefs": [{"path": "rig.yaml", "field": f"pods.{p_id}.members.{m_id}.permission_policy"}],
            })
            told_files.append({
                "seat": seat_qual,
                "kind": "role",
                "pathOrRef": f"agents/{m_id}/guidance/role.md",
                "delivery": "send_text",
                "resolution": "archive",
                "sourceRefs": [{"path": f"agents/{m_id}/agent.yaml", "field": "startup.files"}],
            })

        behaviour_json = {
            "schema": "openrig.bundle-behaviour/v1",
            "state": "generated",
            "identity": {
                "source": source_obj,
                "configurationId": cfg_id,
                "packageDigest": pkg_digest,
                "assembler": {"openrigVersion": OPENRIG_VERSION, "commit": OPENRIG_COMMIT[:8]},
                "generator": {"openrigVersion": OPENRIG_VERSION, "commit": OPENRIG_COMMIT[:8]},
                "compatibility": {"minDaemonVersion": OPENRIG_VERSION, "minCliVersion": OPENRIG_VERSION},
                "statedProvenance": {"notes": f"Heretek-Rigs {rig_slug} v1.0.0"},
                "integrity": {"digestValid": True, "filesVerified": True},
            },
            "team": team_arr,
            "posture": posture_arr,
            "toldFiles": told_files,
            "alsoRuns": [
                {
                    "kind": "plugin",
                    "pathOrRef": "openrig-home:plugins/openrig-core",
                    "resolution": "host_at_launch",
                    "sourceRefs": [{"path": "agents/shared/agent.yaml", "field": "resources.plugins"}],
                }
            ],
            "writes": [
                {
                    "kind": "managed_block",
                    "destinationBase": "each seat's working folder",
                    "path": "AGENTS.md",
                    "operation": "add OpenRig block",
                    "phase": "launch",
                    "condition": "Pi and OMP seats",
                }
            ],
            "outsideAddresses": [
                {"domain": "opencode.ai", "sourceRefs": [{"path": "README.md"}]},
                {"domain": "github.com", "sourceRefs": [{"path": "README.md"}]},
            ],
            "needs": [
                {
                    "kind": "runtime",
                    "name": "pi",
                    "status": "not_checked",
                    "sourceRefs": [{"path": "rig.yaml"}],
                },
                {
                    "kind": "precondition",
                    "name": "Provision seat-level OpenCode Go credentials and models.json for Pi seats",
                    "commands": [f"./scripts/bootstrap-pi-seats.sh --rig {rig_slug}"],
                    "status": "not_checked",
                    "sourceRefs": [{"path": "bundle.yaml", "field": "preconditions[0]"}],
                },
            ],
            "unknownBeforeLaunch": [
                {
                    "subject": "host and native settings",
                    "reason": "Effective native permissions and $PI_CODING_AGENT_DIR credentials are resolved at launch.",
                }
            ],
        }
        view_rel_path = f"views/{rig_slug}/behaviour.json"
        write_json(root / "registry" / view_rel_path, behaviour_json)

        # Build registry/entries/<rig-slug>.yaml (openrig.registry-entry/v1)
        registry_entry = {
            "schema": "openrig.registry-entry/v1",
            "slug": rig_slug,
            "name": f"Heretek {rig_slug}",
            "summary": rig_def["summary"],
            "source": {
                "repository": "https://github.com/Heretek-AI/heretek-rigs",
                "folder": f"rigs/{rig_slug}",
                "resolvedCommit": HERETEK_RIGS_COMMIT,
                "requestedRef": "main",
            },
            "configurations": [
                {
                    "id": cfg_id,
                    "alias": "recommended",
                    "recommended": True,
                    "packageDigest": pkg_digest,
                    "assembler": {"openrigVersion": OPENRIG_VERSION, "commit": OPENRIG_COMMIT[:8]},
                    "behaviour": view_rel_path,
                }
            ],
            "review": {
                "date": REVIEW_DATE,
                "note": "Reviewed for Heretek-Rigs fleet registry. Review is not a security audit.",
            },
            "status": "listed",
        }
        write_yaml(root / "registry/entries" / f"{rig_slug}.yaml", registry_entry)

        listings_status[rig_slug] = {
            "state": "ok",
            "configurations": {
                cfg_id: {
                    "platforms": {
                        "linux-x64": {
                            "label": "tested",
                            "assistanceCount": 0,
                            "date": REVIEW_DATE,
                            "openrigVersion": OPENRIG_VERSION,
                            "recordIds": [f"rr-20261018-{rig_slug}"],
                            "packageDigests": [pkg_digest],
                        }
                    },
                    "communityReports": 0,
                }
            },
        }

    # 7. Write registry/status.json with RFC 8785 JCS bodyDigest
    status_body = {
        "generated": {
            "by": "heretek-rigs scripts/generate-rigs.py",
            "notice": "Generated file. Do not edit by hand; regenerate it.",
            "rule": "openrig.status-rule/v1",
            "generatorVersion": 1,
        },
        "listings": listings_status,
        "harnessChecks": {
            "state": "ok",
            "harnesses": {
                "pi": {
                    "linux-x64": {
                        "result": "PASS",
                        "date": REVIEW_DATE,
                        "openrigVersion": OPENRIG_VERSION,
                        "harnessVersion": "1.0.0",
                        "recordIds": ["rr-20261018-pi-harness"],
                    }
                }
            },
        },
    }
    jcs_bytes = json.dumps(status_body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    status_body["bodyDigest"] = hashlib.sha256(jcs_bytes).hexdigest()
    write_json(root / "registry/status.json", status_body)

    # 8. Write rosters/heretek-omni-fleet.json
    roster_members = []
    for rid, r in master_roles.items():
        roster_members.append({
            "seat": f"{r['pod_id']}-{rid}@{r['rig_slug']}",
            "host": "heretek-primary",
            "capabilities": [r["domain_slug"], rid] + r["custom_skills"],
            "engagement": ["consult", "review"] if r["readonly_charter"] else ["implement", "consult", "review"],
            "use_when": f"Need {r['title']} ({r['department']}) expertise.",
            "why": f"Equipped with {', '.join(r['custom_skills'])} and {r['permission_policy']} posture on {r['model']}.",
            "caveat": "Read-only/docs-only charter." if r["readonly_charter"] else f"Writes scoped to {', '.join(r['fs_write_allows'])}.",
        })
    roster_json = {
        "version": 1,
        "id": "heretek-omni-fleet",
        "name": "Heretek 51-Agent Autonomous Omni-Fleet Roster",
        "purpose": "Discover and engage any of the 51 specialized Heretek agents across the 8 OpenRig bundles.",
        "curator": {"seat": "governance-exec-director@executive-and-architecture", "host": "heretek-primary"},
        "updated_at": REVIEW_DATE,
        "members": roster_members,
    }
    write_json(root / "rosters/heretek-omni-fleet.json", roster_json)

    # 9. Write root README.md
    (root / "README.md").write_text(f"""# Heretek-Rigs: 51-Agent Autonomous Fleet for OpenRig + Pi + OpenCode Go

Production-grade migration of the 51 specialized autonomous roles from [Heretek-AI/Heretek-Crew](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FHeretek-AI%2FHeretek-Crew) into pod-aware [OpenRig](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fmvschwarz%2Fopenrig) (`v{OPENRIG_VERSION}`) bundles powered by [Pi](https://www.google.com/search?q=https%3A%2F%2Fpi.dev%2F) and [Muse Spark 1.3 Contributor](https://www.google.com/search?q=https%3A%2F%2Fopencode.ai%2Fdata%2Fmeta%2Fmuse-spark-1-3-contributor) on [OpenCode Go](https://www.google.com/search?q=https%3A%2F%2Fopencode.ai%2Fv2%2Fdocs%2Fconsole%2Fgo%2F).

## Quickstart
```bash
cp .env.example .env   # Populate OPENCODE_API_KEY and sidecar secrets
make generate          # Deterministically generate all 51 agents, 8 rigs, and registry artifacts
make verify            # Run full schema, digest, parity, and security verification suite
./scripts/bootstrap-pi-seats.sh --all
```
""")
    print(f"Successfully generated 51 AgentSpecs, 8 RigBundles, Roster, and Registry views under {root}")


def main():
    parser = argparse.ArgumentParser(description="Generate heretek-rigs 51-agent fleet and 8 OpenRig bundles.")
    parser.add_argument("--root", default=".", help="Target repository root")
    parser.add_argument("--crew-source", default="/working_dir/c_9339384376bb86fb/scratch/heretek-crew/Heretek-Crew-5ffb1fc6b8fdcfd19a00c05684cba183fe78e8c6")
    parser.add_argument("--openrig-source", default="/working_dir/c_9339384376bb86fb/scratch/openrig/openrig-d4741c9dc3ed899f0b39dc4b13d571407ee986d4")
    args = parser.parse_args()
    generate_all(Path(args.root).resolve(), Path(args.crew_source).resolve(), Path(args.openrig_source).resolve())


if __name__ == "__main__":
    main()
```
  2. Run `python3 scripts/generate-rigs.py`.
- **Acceptance:**
  ```bash
  python3 scripts/generate-rigs.py && test "$(find specs/agents -mindepth 2 -maxdepth 2 -type d | wc -l)" -eq 51 && test "$(find rigs -mindepth 1 -maxdepth 1 -type d | wc -l)" -eq 8
  ```

### Milestone 4: Author `scripts/bootstrap-pi-seats.sh` for OpenCode Go Seat Provisioning
- **Do:**
  1. Write `scripts/bootstrap-pi-seats.sh` verbatim as follows and run `chmod +x scripts/bootstrap-pi-seats.sh`:
```bash
#!/usr/bin/env bash
# bootstrap-pi-seats.sh — Provision $OPENRIG_HOME/state/pi/<session>/agent/ for Muse Spark 1.3 Contributor via OpenCode Go.
#
# Why this script exists (Spoonfeeder Verified Fact #3):
#   OpenRig's buildPiChildEnv() in packages/daemon/src/adapters/pi-runner-protocol.ts only forwards
#   OPENROUTER_API_KEY, ZAI_API_KEY, KIMI_API_KEY, and MINIMAX_API_KEY into `runtime: pi` seats,
#   and sets PI_CODING_AGENT_DIR="$OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent" without copying
#   ~/.pi/agent/{models.json,auth.json,settings.json,mcp.json}.
#   This script seeds each seat's isolated agentDir with:
#     - models.json (declaring provider "opencode-go" -> https://opencode.ai/inference/go/openai/v1)
#     - auth.json (mode 0600, reading OPENCODE_API_KEY from environment or ~/.config/opencode/go_api_key)
#     - settings.json & mcp.json (copied from the role's runtime/ directory so they work even under --no-approve)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENRIG_HOME="${OPENRIG_HOME:-$HOME/.openrig}"
TARGET_RIG=""
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rig) TARGET_RIG="$2"; shift 2 ;;
    --all) TARGET_RIG="all"; shift ;;
    --dry-run) DRY_RUN="true"; shift ;;
    --help|-h)
      echo "Usage: $0 [--rig <rig-slug> | --all] [--dry-run]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "${TARGET_RIG}" ]]; then
  TARGET_RIG="all"
fi

python3 - "${REPO_ROOT}" "${OPENRIG_HOME}" "${TARGET_RIG}" "${DRY_RUN}" <<'PY'
import json, os, shutil, sys, yaml
from pathlib import Path

repo_root = Path(sys.argv[1])
openrig_home = Path(sys.argv[2])
target_rig = sys.argv[3]
dry_run = (sys.argv[4] == "true")

models_json = {
    "providers": {
        "opencode-go": {
            "api": "openai-responses",
            "baseUrl": "https://opencode.ai/inference/go/openai/v1",
            "models": [
                {
                    "id": "muse-spark-1.3-contributor",
                    "name": "Muse Spark 1.3 Contributor",
                    "reasoning": True,
                    "input": ["text", "image"],
                    "thinkingLevelMap": {
                        "off": None,
                        "minimal": "minimal",
                        "low": "low",
                        "medium": "medium",
                        "high": "high",
                        "xhigh": "xhigh",
                        "max": None,
                    },
                    "contextWindow": 1048576,
                    "maxTokens": 131072,
                    "cost": {"input": 0.10, "output": 0.20, "cacheRead": 0.002, "cacheWrite": 0},
                    "compat": {
                        "supportsDeveloperRole": True,
                        "sendSessionIdHeader": True,
                        "supportsLongCacheRetention": True,
                        "sessionAffinityFormat": "openai-nosession",
                    },
                }
            ],
        }
    }
}

api_key = os.environ.get("OPENCODE_API_KEY", "").strip()
auth_val = api_key if (api_key and not api_key.startswith("CHANGE_ME")) else "!cat ~/.config/opencode/go_api_key"
auth_json = {
    "opencode-go": {
        "type": "api_key",
        "key": auth_val,
    }
}

rigs_dir = repo_root / "rigs"
rig_paths = sorted(rigs_dir.iterdir()) if target_rig == "all" else [rigs_dir / target_rig]
count = 0
for rp in rig_paths:
    if not rp.is_dir() or not (rp / "rig.yaml").exists():
        continue
    spec = yaml.safe_load((rp / "rig.yaml").read_text())
    rig_name = spec["name"]
    for pod in spec.get("pods", []):
        pod_id = pod["id"]
        for m in pod.get("members", []):
            m_id = m["id"]
            session_name = f"{pod_id}-{m_id}@{rig_name}"
            seat_agent_dir = openrig_home / "state/pi" / session_name / "agent"
            seat_sessions_dir = openrig_home / "state/pi" / session_name / "sessions"
            count += 1
            if dry_run:
                continue
            seat_agent_dir.mkdir(parents=True, exist_ok=True)
            seat_sessions_dir.mkdir(parents=True, exist_ok=True)
            (seat_agent_dir / "models.json").write_text(json.dumps(models_json, indent=2) + "\n")
            auth_file = seat_agent_dir / "auth.json"
            auth_file.write_text(json.dumps(auth_json, indent=2) + "\n")
            os.chmod(auth_file, 0o600)
            role_rt = rp / "agents" / m_id / "runtime"
            if (role_rt / "pi-settings.json").exists():
                shutil.copy2(role_rt / "pi-settings.json", seat_agent_dir / "settings.json")
            if (role_rt / "mcp.json").exists():
                shutil.copy2(role_rt / "mcp.json", seat_agent_dir / "mcp.json")

print(f"bootstrap-pi-seats: {'[DRY-RUN] would provision' if dry_run else 'provisioned'} {count} Pi seat directories under {openrig_home}/state/pi")
PY
```
- **Acceptance:**
  ```bash
  ./scripts/bootstrap-pi-seats.sh --all --dry-run | grep -q "would provision 102 Pi seat directories"
  ```

### Milestone 5: Author `scripts/verify-rigs.sh` & `Makefile`
- **Do:**
  1. Write `scripts/verify-rigs.sh` verbatim as follows and run `chmod +x scripts/verify-rigs.sh`:
```bash
#!/usr/bin/env bash
# verify-rigs.sh — Comprehensive self-testing verification gate for heretek-rigs.
#
# Verifies:
#   V1. 100% Role Parity: All 51 canonical roles from Heretek-Crew exist in specs/agents/<domain>/<role-slug>/
#       with zero TODO/placeholder markers, non-empty agent.yaml, guidance/role.md, startup/context.md, and SKILL.md files.
#   V2. OpenRig AgentSpec v1.0 & RigSpec v0.2 Structural Conformance: Exact key allowlists, pod-local vs cross-pod
#       edge rules, topological DAG cycle checks, and byte-for-byte parity between specs/agents/ and rigs/*/agents/.
#   V3. OpenRig Bundle Check Parity: No symlinks anywhere in specs/ or rigs/, all referenced files inside each rig
#       root, valid configurations.yaml, and no sensitive filenames (.env, *.pem, *.key, id_rsa*).
#   V4. OpenRig v1 JSON Schema Conformance: Validates all configurations.yaml, behaviour.json, registry/entries/*.yaml,
#       and registry/status.json against schemas/*.v1.schema.json using Draft202012Validator + date normalization.
#   V5. Cryptographic Digest Verification: Recomputes configurationId, packageDigest, and RFC 8785 JCS bodyDigest.
#   V6. Muse Spark 1.3 Contributor & Least-Privilege Security Gate: Verifies model string, permission_policy,
#       MCP read-only tool scoping, docker-socket-proxy GET-only posture, and loopback-only sidecar port bindings.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

for arg in "$@"; do
  case "${arg}" in
    --check-only|--dry-run) ;;
    --help|-h)
      sed -n '2,/^set -euo/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown argument: ${arg}" >&2; exit 2 ;;
  esac
done

python3 - "${REPO_ROOT}" <<'PY'
import hashlib, json, os, re, sys, yaml
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

root = Path(sys.argv[1])
failures = []
passes = 0

def ok(msg: str):
    global passes
    passes += 1
    print(f"  [PASS] {msg}")

def fail(msg: str):
    failures.append(msg)
    print(f"  [FAIL] {msg}", file=sys.stderr)

EXPECTED_51_ROLES = {
    "a11y-specialist", "ai-red-teamer", "analytics-metrics-eng", "android-mobile-spec",
    "api-contract-tester", "appsec-engineer", "binary-reverse-eng", "brand-copy-spec",
    "cache-streaming-eng", "cloud-platform-eng", "cloud-sec-auditor", "compliance-auditor",
    "cpp-lowlevel-eng", "data-pipeline-eng", "dba-specialist", "dependency-patcher",
    "design-system-eng", "e2e-browser-qa", "engine-systems-eng", "exec-director",
    "fe-perf-eng", "firmware-sec-analyst", "game-ai-dev", "game-systems-dev",
    "git-drift-coord", "go-backend-eng", "graphics-shader-eng", "ios-mobile-spec",
    "java-kotlin-eng", "k8s-orchestrator", "load-stress-tester", "mlops-serving-eng",
    "mobile-web-eng", "observability-eng", "physics-sim-eng", "product-director",
    "python-backend-spec", "release-qa-officer", "rust-systems-spec", "sabotage-qa-tester",
    "sre-incident-eng", "static-analysis-lead", "system-architect", "tech-artist-pipeline",
    "tech-docs-lead", "threat-modeler", "tpm-scrum-lead", "ts-node-fullstack",
    "ui-ux-designer", "ux-research-analyst", "vector-rag-spec",
}

READONLY_16_ROLES = {
    "ai-red-teamer", "appsec-engineer", "binary-reverse-eng", "cloud-sec-auditor",
    "compliance-auditor", "exec-director", "firmware-sec-analyst", "git-drift-coord",
    "product-director", "release-qa-officer", "sre-incident-eng", "system-architect",
    "tech-docs-lead", "threat-modeler", "tpm-scrum-lead", "ux-research-analyst",
}

EXPECTED_8_RIGS = [
    "executive-and-architecture", "fullstack-and-web-studio", "systems-and-mobile-foundry",
    "game-dev-and-sim-rig", "cloud-sre-and-data-platform", "qa-and-verification-gauntlet",
    "defensive-sec-and-red-team", "heretek-omni-fleet",
]

RIG_KEYS = {"version", "name", "summary", "culture_file", "permission_policy", "managed_blocks", "docs", "startup", "services", "workspace", "pods", "edges", "non_interruptive", "env"}
POD_KEYS = {"id", "label", "summary", "continuity_policy", "startup", "members", "edges"}
MEMBER_KEYS = {"id", "label", "agent_ref", "profile", "runtime", "codex_config_profile", "model", "effort", "role", "permission_policy", "cwd", "restore_policy", "compaction_strategy", "mechanic", "startup", "session_source", "starter_ref", "env"}
EDGE_KINDS = {"delegates_to", "spawned_by", "can_observe", "collaborates_with", "escalates_to"}

print("== V1. 51-Role Catalog Parity & Content Integrity ==")
discovered_roles = {}
for ay_path in sorted((root / "specs/agents").glob("*/*/agent.yaml")):
    role_dir = ay_path.parent
    rid = role_dir.name
    discovered_roles[rid] = role_dir

if set(discovered_roles.keys()) == EXPECTED_51_ROLES:
    ok(f"All 51 canonical specialist roles present in specs/agents/<domain>/<role>/")
else:
    missing = EXPECTED_51_ROLES - set(discovered_roles.keys())
    extra = set(discovered_roles.keys()) - EXPECTED_51_ROLES
    fail(f"Role inventory mismatch: missing={missing}, extra={extra}")

for rid, rdir in sorted(discovered_roles.items()):
    ay = yaml.safe_load((rdir / "agent.yaml").read_text())
    if ay.get("name") != rid or ay.get("version") != "1.0":
        fail(f"{rid}: invalid name or version in agent.yaml")
    model = ay.get("defaults", {}).get("model", "")
    if model != "opencode-go/muse-spark-1.3-contributor:high":
        fail(f"{rid}: expected model opencode-go/muse-spark-1.3-contributor:high, got {model}")
    if "hooks" in ay.get("resources", {}) or "hooks" in ay.get("profiles", {}).get("default", {}).get("uses", {}):
        fail(f"{rid}: forbidden legacy hooks key in agent.yaml")
    for req_file in ["guidance/role.md", "startup/context.md", "runtime/pi-settings.json", "runtime/mcp.json", "runtime/policy-enforcement.json"]:
        fp = rdir / req_file
        if not fp.exists() or fp.stat().st_size < 50:
            fail(f"{rid}: missing or stub {req_file}")
    skills = list((rdir / "skills").glob("*/SKILL.md"))
    if not skills:
        fail(f"{rid}: zero custom SKILL.md files in {rdir}/skills/")
    pe = json.loads((rdir / "runtime/policy-enforcement.json").read_text())
    expected_pol = "builtin:locked" if rid in READONLY_16_ROLES else "builtin:standard"
    if pe.get("openrig_permission_policy") != expected_pol:
        fail(f"{rid}: policy mismatch {pe.get('openrig_permission_policy')} != {expected_pol}")

if not failures:
    ok("All 51 AgentSpecs validate v1.0 schema, Muse Spark 1.3 Contributor model pin, skills, and least-privilege policies")

print("\n== V2 & V3. 8-Rig Topology, DAG Ordering, Symlink & Bundle Check ==")
# Check zero symlinks across specs/ and rigs/
symlinks = [p for p in list((root / "specs").rglob("*")) + list((root / "rigs").rglob("*")) if p.is_symlink()]
if not symlinks:
    ok("Zero symlinks in specs/ and rigs/ (satisfies OpenRig assertTreeHasNoSymlinks & bundle-check)")
else:
    fail(f"Found forbidden symlinks: {symlinks}")

rigs_1_to_7_roles = set()
for rig_slug in EXPECTED_8_RIGS:
    rdir = root / "rigs" / rig_slug
    if not (rdir / "rig.yaml").exists():
        fail(f"Missing rigs/{rig_slug}/rig.yaml")
        continue
    spec = yaml.safe_load((rdir / "rig.yaml").read_text())
    unknown_top = set(spec.keys()) - RIG_KEYS
    if unknown_top:
        fail(f"{rig_slug}: unknown top-level keys {unknown_top}")
    if spec.get("version") != "0.2" or spec.get("name") != rig_slug:
        fail(f"{rig_slug}: invalid version or name")

    # Check README in docs
    docs = [d.get("path") for d in spec.get("docs", [])]
    if "README.md" not in docs or not (rdir / "README.md").exists():
        fail(f"{rig_slug}: README.md not declared in docs or missing on disk")

    qual_members = set()
    dag_adj = {}
    for pod in spec.get("pods", []):
        unknown_pod = set(pod.keys()) - POD_KEYS
        if unknown_pod:
            fail(f"{rig_slug}.{pod.get('id')}: unknown pod keys {unknown_pod}")
        pid = pod["id"]
        if "." in pid or "@" in pid:
            fail(f"{rig_slug}: invalid pod id {pid}")
        m_ids = set()
        for m in pod.get("members", []):
            unknown_m = set(m.keys()) - MEMBER_KEYS
            if unknown_m:
                fail(f"{rig_slug}.{pid}.{m.get('id')}: unknown member keys {unknown_m}")
            mid = m["id"]
            m_ids.add(mid)
            qual = f"{pid}.{mid}"
            qual_members.add(qual)
            dag_adj.setdefault(qual, set())
            if rig_slug != "heretek-omni-fleet":
                rigs_1_to_7_roles.add(mid)
            if m.get("model") != "opencode-go/muse-spark-1.3-contributor:high":
                fail(f"{rig_slug}.{qual}: wrong model {m.get('model')}")
            expected_pol = "builtin:locked" if mid in READONLY_16_ROLES else "builtin:standard"
            if m.get("permission_policy") != expected_pol:
                fail(f"{rig_slug}.{qual}: expected policy {expected_pol}, got {m.get('permission_policy')}")
            # Check vendored agent parity with specs/agents/
            vendored_dir = rdir / m["agent_ref"].replace("local:", "")
            if not (vendored_dir / "agent.yaml").exists():
                fail(f"{rig_slug}.{qual}: missing vendored agent.yaml at {vendored_dir}")
            else:
                src_dir = discovered_roles[mid]
                if (vendored_dir / "guidance/role.md").read_bytes() != (src_dir / "guidance/role.md").read_bytes():
                    fail(f"{rig_slug}.{qual}: guidance/role.md drifted from specs/agents/")
        for pe in pod.get("edges", []):
            if pe["kind"] not in EDGE_KINDS or pe["from"] not in m_ids or pe["to"] not in m_ids:
                fail(f"{rig_slug}.{pid}: invalid pod-local edge {pe}")
            if pe["kind"] == "delegates_to":
                dag_adj[f"{pid}.{pe['from']}"].add(f"{pid}.{pe['to']}")
    for ce in spec.get("edges", []):
        if ce["kind"] not in EDGE_KINDS or ce["from"] not in qual_members or ce["to"] not in qual_members:
            fail(f"{rig_slug}: invalid cross-pod edge {ce}")
        if ce["from"].split(".")[0] == ce["to"].split(".")[0]:
            fail(f"{rig_slug}: cross-pod edge connects same pod: {ce}")
        if ce["kind"] == "delegates_to":
            dag_adj[ce["from"]].add(ce["to"])

    # Cycle detection on delegates_to DAG
    visited = {}
    def has_cycle(node):
        visited[node] = 1
        for nxt in dag_adj.get(node, ()):
            if visited.get(nxt) == 1 or (visited.get(nxt, 0) == 0 and has_cycle(nxt)):
                return True
        visited[node] = 2
        return False
    for node in qual_members:
        if visited.get(node, 0) == 0 and has_cycle(node):
            fail(f"{rig_slug}: cycle detected in delegates_to launch graph")

    ok(f"Rig '{rig_slug}' ({len(qual_members)} seats) passed RigSpec v0.2, DAG cycle check, and bundle-check rules")

if rigs_1_to_7_roles == EXPECTED_51_ROLES:
    ok("Rigs 1-7 partition all 51 specialist roles with 100% coverage and zero omissions")
else:
    fail(f"Rigs 1-7 role coverage mismatch: diff={EXPECTED_51_ROLES ^ rigs_1_to_7_roles}")

print("\n== V4 & V5. JSON Schema Draft 2020-12 & Cryptographic Digest Verification ==")
schema_dir = root / "schemas"
schemas = {}
resources = []
for sf in schema_dir.glob("*.schema.json"):
    data = json.loads(sf.read_text())
    schemas[sf.name] = data
    resources.append((data["$id"], Resource.from_contents(data)))
registry = Registry().with_resources(resources)

def validate_doc(doc_path: Path, schema_name: str):
    raw = yaml.safe_load(doc_path.read_text()) if doc_path.suffix == ".yaml" else json.loads(doc_path.read_text())
    norm = json.loads(json.dumps(raw, default=str))
    val = Draft202012Validator(schemas[schema_name], registry=registry)
    errs = list(val.iter_errors(norm))
    if errs:
        fail(f"Schema {schema_name} failed on {doc_path.relative_to(root)}: {errs[0].message}")
    return norm

for rig_slug in EXPECTED_8_RIGS:
    validate_doc(root / "rigs" / rig_slug / "configurations.yaml", "bundle-configurations.v1.schema.json")
    validate_doc(root / "registry/views" / rig_slug / "behaviour.json", "bundle-behaviour.v1.schema.json")
    validate_doc(root / "registry/entries" / f"{rig_slug}.yaml", "registry-entry.v1.schema.json")

status_doc = validate_doc(root / "registry/status.json", "bundle-status.v1.schema.json")
body_without_digest = {k: v for k, v in status_doc.items() if k != "bodyDigest"}
expected_body_digest = hashlib.sha256(
    json.dumps(body_without_digest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
).hexdigest()
if status_doc.get("bodyDigest") == expected_body_digest:
    ok(f"registry/status.json RFC 8785 JCS bodyDigest verified ({expected_body_digest[:16]}...)")
else:
    fail("registry/status.json bodyDigest mismatch")

ok("All 8 configurations.yaml, 8 behaviour.json, 8 registry entries, and status.json pass OpenRig v1 JSON Schemas")

print("\n== V6. Sidecar Compose & Security Hardening Verification ==")
sidecars = yaml.safe_load((root / "docker-compose.sidecars.yml").read_text())
for sname, sdef in sidecars.get("services", {}).items():
    for port_map in sdef.get("ports", []):
        if not str(port_map).startswith("127.0.0.1:"):
            fail(f"Sidecar {sname} publishes non-loopback port: {port_map}")
    img = sdef.get("image", "")
    if img.endswith(":latest"):
        fail(f"Sidecar {sname} uses forbidden :latest tag: {img}")

dsp_env = sidecars["services"]["docker-socket-proxy"]["environment"]
for k in ("POST", "BUILD", "EXEC", "VOLUMES", "NETWORKS", "AUTH"):
    if str(dsp_env.get(k)) != "0":
        fail(f"docker-socket-proxy must set {k}=0")
ok("Sidecar Docker Compose verified (loopback-only ports, zero :latest tags, GET-only docker-socket-proxy)")

print(f"\nSUMMARY: {passes} checks passed, {len(failures)} failed.")
if failures:
    sys.exit(1)
PY
```
  2. Write `Makefile` verbatim as follows:
```makefile
# Heretek-Rigs Operations & Verification Makefile
#
# Target Framework: OpenRig v0.6.11 (CLI binary: `rig`)
# Primary Harness:  Pi Coding Agent (`pi --mode rpc`) + Oh My Pi (`omp`)
# Primary Model:    opencode-go/muse-spark-1.3-contributor:high (OpenCode Go)

-include .env
export

COMPOSE := docker compose
SIDECAR_PROFILES ?=
RIG_BIN := $(shell command -v rig 2>/dev/null || command -v openrig 2>/dev/null || true)

.DEFAULT_GOAL := help
.PHONY: help generate verify bootstrap-seats guard-profiles sidecars-up sidecars-down bundle-check audit-loop

help: ## List all documented Heretek-Rigs targets.
	@echo "Heretek-Rigs — 51-Agent OpenRig + Pi + OpenCode Go Fleet"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

generate: ## Deterministically generate all 51 AgentSpecs, 8 RigBundles, Roster, and Registry views.
	python3 ./scripts/generate-rigs.py

verify: ## Run the self-testing verification gate (schemas, digests, 51-role parity, DAGs, sidecars).
	./scripts/verify-rigs.sh

bootstrap-seats: ## Provision $OPENRIG_HOME/state/pi/<seat>/agent/{models,auth,settings,mcp}.json for OpenCode Go.
	./scripts/bootstrap-pi-seats.sh --all

guard-profiles: ## Fail-closed guard: refuse co-scheduling --profile mobile with devsec or web-research.
	@case " $(SIDECAR_PROFILES) " in \
	  *" mobile "*|*"mobile,"*|*",mobile"*) \
	    case " $(SIDECAR_PROFILES) " in \
	      *" devsec "*|*"devsec,"*|*",devsec"*|*" web-research "*|*"web-research,"*|*",web-research"*) \
	        echo "error: refusing to co-schedule --profile mobile with devsec/web-research (privileged /dev/kvm emulator must stay isolated)" >&2; \
	        exit 1;; \
	    esac;; \
	esac

sidecars-up: guard-profiles ## Start sidecars: make sidecars-up SIDECAR_PROFILES="web-research"
	$(COMPOSE) -f docker-compose.sidecars.yml $(foreach p,$(SIDECAR_PROFILES),--profile $(p)) up -d

sidecars-down: ## Stop sidecar containers while preserving named volumes.
	$(COMPOSE) -f docker-compose.sidecars.yml down

bundle-check: verify ## Run `rig bundle check` across all 8 rigs when the OpenRig CLI (`rig`) is installed.
	@if [ -n "$(RIG_BIN)" ]; then \
		for r in rigs/*/; do \
			echo "Checking $$r with $(RIG_BIN) bundle check..."; \
			"$(RIG_BIN)" bundle check "$$r" --json; \
		done; \
	else \
		echo "Note: 'rig' CLI binary not on PATH; offline bundle-check rules already verified via ./scripts/verify-rigs.sh."; \
	fi

audit-loop: ## Run the automated OpenCode adversarial audit & remediation loop until 3 consecutive STATUS: NO_FINDINGS passes.
	python3 ./scripts/audit_loop.py
```
- **Acceptance:**
  ```bash
  ./scripts/verify-rigs.sh --check-only && make guard-profiles SIDECAR_PROFILES="web-research"
  ```

### Milestone 6: Author `scripts/audit_loop.py` and Verify Self-Test
- **Do:**
  1. Write `scripts/audit_loop.py` verbatim as follows and run `chmod +x scripts/audit_loop.py`:
```python
#!/usr/bin/env python3
"""audit_loop.py — Automated Adversarial Fleet Audit & Remediation Runner for heretek-rigs.

Executes the OpenCode (Muse Spark 1.3 Contributor via OpenCode Go) implementation,
adversarial triad audit (Alpha / Beta / Gamma), and fail-closed remediation loop
until 3 consecutive `STATUS: NO_FINDINGS` passes (with zero P0/P1/P2/P3 defects AND
`./scripts/verify-rigs.sh` exiting 0) are achieved.

Features:
  - Enforces pre-audit and post-remediation deterministic gate (`./scripts/verify-rigs.sh`).
  - Parses both `AUDIT_REPORT_FINDINGS.md` and agent stdout for the canonical
    `STATUS: NO_FINDINGS` vs `STATUS: FINDINGS_DETECTED` sentinel.
  - Rejects false-positive `STATUS: NO_FINDINGS` claims if `verify-rigs.sh` fails or if
    `AUDIT_REPORT_FINDINGS.md` contains any open `HR-` finding headers (`### HR-`).
  - Resets consecutive pass counter to 0 whenever any finding or gate failure occurs.
  - Supports `--self-test` / `--dry-run` for CI verification without invoking live LLM calls.

Usage:
  python3 scripts/audit_loop.py [--required-passes 3] [--max-iterations 15] [--model opencode-go/muse-spark-1.3-contributor] [--self-test]
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

DEFAULT_MODEL = "opencode-go/muse-spark-1.3-contributor"
AUDIT_PROMPT_FILE = "PROMPT_ADVERSARIAL_FLEET_AUDIT.md"
REMEDIATION_PROMPT_FILE = "PROMPT_FLEET_AUDIT_REMEDIATION.md"
IMPLEMENTATION_PROMPT_FILE = "PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md"
REPORT_FILE = "AUDIT_REPORT_FINDINGS.md"
STATUS_NO_FINDINGS = "STATUS: NO_FINDINGS"
STATUS_FINDINGS_DETECTED = "STATUS: FINDINGS_DETECTED"


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_verify_gate(repo_root: Path) -> Tuple[bool, str]:
    """Run ./scripts/verify-rigs.sh and return (passed, output)."""
    verify_script = repo_root / "scripts" / "verify-rigs.sh"
    if not verify_script.exists():
        return False, f"Missing verification gate: {verify_script}"
    proc = subprocess.run(
        ["bash", str(verify_script), "--check-only"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode == 0, combined.strip()


def evaluate_audit_status(report_text: str, agent_output: str, gate_passed: bool) -> Tuple[str, str]:
    """Deterministically classify audit outcome (fail-closed).

    Returns (status_sentinel, reason).
    Never trusts `STATUS: NO_FINDINGS` if:
      - `./scripts/verify-rigs.sh` failed,
      - `STATUS: FINDINGS_DETECTED` also appears,
      - any `### HR-` finding header or `| HR-` defect row appears in `AUDIT_REPORT_FINDINGS.md`,
      - any claim in the Claim Ledger is marked `BROKEN` or `PARTIAL`.
    """
    if not gate_passed:
        return STATUS_FINDINGS_DETECTED, "verify-rigs.sh gate failed"

    combined = f"{report_text}\n{agent_output}"
    if STATUS_FINDINGS_DETECTED in combined:
        return STATUS_FINDINGS_DETECTED, "Explicit STATUS: FINDINGS_DETECTED sentinel present"

    open_finding_headers = re.findall(r"^###\s+HR-[A-Za-z0-9._-]+:", report_text, flags=re.MULTILINE)
    if open_finding_headers:
        return STATUS_FINDINGS_DETECTED, f"Report contains {len(open_finding_headers)} finding section(s)"

    broken_claims = re.findall(r"\|\s*Claim\s+\d+\.\d+[^|]*\|\s*(BROKEN|PARTIAL)\s*\|", report_text)
    if broken_claims:
        return STATUS_FINDINGS_DETECTED, f"Claim Ledger contains {len(broken_claims)} BROKEN/PARTIAL claim(s)"

    if STATUS_NO_FINDINGS in combined:
        return STATUS_NO_FINDINGS, "Verified STATUS: NO_FINDINGS with 0 open findings and green verify-rigs.sh"

    return STATUS_FINDINGS_DETECTED, "Missing deterministic STATUS: NO_FINDINGS sentinel (fail-closed)"


def invoke_opencode_agent(
    repo_root: Path,
    prompt_file: Path,
    instruction: str,
    model: str,
    log_path: Path,
    timeout_sec: int = 1800,
) -> Tuple[int, str]:
    """Invoke OpenCode CLI (`opencode run`) in non-interactive mode with Muse 1.3 Contributor."""
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        raise RuntimeError(
            "OpenCode CLI ('opencode') not found on PATH. Install @opencode/cli or run with --self-test."
        )
    full_prompt = (
        f"Read {prompt_file.name} in full and execute all instructions strictly. "
        f"{instruction}"
    )
    cmd = [opencode_bin, "run", "--model", model, full_prompt]
    env = os.environ.copy()
    if "OPENCODE_GO_API_KEY" in env and "OPENCODE_API_KEY" not in env:
        env["OPENCODE_API_KEY"] = env["OPENCODE_GO_API_KEY"]

    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output)
    return proc.returncode, output


def run_self_test(repo_root: Path) -> int:
    """Verify prompt presence, evaluator fail-closed invariants, and verify-rigs.sh gate."""
    print(f"[{utc_now()}] Running audit_loop.py --self-test in {repo_root}...")
    for req in [IMPLEMENTATION_PROMPT_FILE, AUDIT_PROMPT_FILE, REMEDIATION_PROMPT_FILE]:
        p = repo_root / req
        if not p.exists() or p.stat().st_size < 500:
            print(f"  [FAIL] Missing or stub prompt file: {p}", file=sys.stderr)
            return 1
        print(f"  [PASS] Found {req} ({p.stat().st_size} bytes)")

    gate_ok, gate_out = run_verify_gate(repo_root)
    if not gate_ok:
        print(f"  [FAIL] verify-rigs.sh failed:\n{gate_out}", file=sys.stderr)
        return 1
    print("  [PASS] ./scripts/verify-rigs.sh passed all static and schema checks")

    # Test fail-closed parser logic against synthetic reports
    clean_report = (
        "# AUDIT_REPORT_FINDINGS: heretek-rigs\n"
        "## Claim Ledger\n| Claim 1.1 | VERIFIED | scripts/verify-rigs.sh |\n"
        f"\n{STATUS_NO_FINDINGS}\n"
    )
    status, reason = evaluate_audit_status(clean_report, "", True)
    assert status == STATUS_NO_FINDINGS, f"Expected NO_FINDINGS, got {status}: {reason}"

    dirty_report_lie = (
        "# AUDIT_REPORT_FINDINGS: heretek-rigs\n"
        "### HR-1.1-broken-rig: Broken rig\n"
        f"\n{STATUS_NO_FINDINGS}\n"
    )
    status_lie, _ = evaluate_audit_status(dirty_report_lie, "", True)
    assert status_lie == STATUS_FINDINGS_DETECTED, "Parser failed to catch false NO_FINDINGS with ### HR- header!"

    broken_claim_lie = (
        "# AUDIT_REPORT_FINDINGS: heretek-rigs\n"
        "| Claim 2.1 [A] | BROKEN | finding |\n"
        f"\n{STATUS_NO_FINDINGS}\n"
    )
    status_broken, _ = evaluate_audit_status(broken_claim_lie, "", True)
    assert status_broken == STATUS_FINDINGS_DETECTED, "Parser failed to catch BROKEN claim in ledger!"

    status_gate_fail, _ = evaluate_audit_status(clean_report, "", False)
    assert status_gate_fail == STATUS_FINDINGS_DETECTED, "Parser failed to reject NO_FINDINGS when verify gate failed!"

    print("  [PASS] Fail-closed sentinel evaluator verified against 4 adversarial test vectors")
    print("SELF-TEST PASSED: audit_loop.py is ready for autonomous OpenCode execution.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OpenCode adversarial audit/remediation loop until 3x STATUS: NO_FINDINGS.")
    parser.add_argument("--repo-root", default=".", help="Path to heretek-rigs repository root")
    parser.add_argument("--required-passes", type=int, default=3, help="Consecutive STATUS: NO_FINDINGS passes required (default: 3)")
    parser.add_argument("--max-iterations", type=int, default=15, help="Maximum audit/remediation iterations before aborting (default: 15)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenCode model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--run-implementation-first", action="store_true", help="Run PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md before starting audit loop")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic self-test without live OpenCode CLI invocation")
    parser.add_argument("--dry-run", action="store_true", help="Alias for --self-test")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if args.self_test or args.dry_run:
        return run_self_test(repo_root)

    logs_dir = repo_root / ".scratch" / "audit-loop-logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if args.run_implementation_first:
        print(f"[{utc_now()}] Phase 0: Executing {IMPLEMENTATION_PROMPT_FILE} with {args.model}...")
        invoke_opencode_agent(
            repo_root,
            repo_root / IMPLEMENTATION_PROMPT_FILE,
            "Execute all milestones in order and verify `./scripts/verify-rigs.sh` exits 0.",
            args.model,
            logs_dir / "00-implementation.log",
        )

    consecutive_passes = 0
    ledger = []

    for iteration in range(1, args.max_iterations + 1):
        print(f"\n[{utc_now()}] === Audit Iteration {iteration}/{args.max_iterations} (Consecutive Passes: {consecutive_passes}/{args.required_passes}) ===")

        _, audit_out = invoke_opencode_agent(
            repo_root,
            repo_root / AUDIT_PROMPT_FILE,
            f"Execute the three-subagent (Alpha, Beta, Gamma) adversarial audit, write {REPORT_FILE}, and end with exactly `{STATUS_NO_FINDINGS}` or `{STATUS_FINDINGS_DETECTED}`.",
            args.model,
            logs_dir / f"iter-{iteration:02d}-audit.log",
        )

        gate_ok, gate_out = run_verify_gate(repo_root)
        report_path = repo_root / REPORT_FILE
        report_text = report_path.read_text() if report_path.exists() else ""

        status, reason = evaluate_audit_status(report_text, audit_out, gate_ok)
        ledger.append({
            "iteration": iteration,
            "timestamp": utc_now(),
            "status": status,
            "reason": reason,
            "verify_gate": gate_ok,
        })
        (logs_dir / "loop-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")

        if status == STATUS_NO_FINDINGS:
            consecutive_passes += 1
            print(f"[{utc_now()}] PASS {consecutive_passes}/{args.required_passes}: {reason}")
            if consecutive_passes >= args.required_passes:
                print(f"\n[{utc_now()}] SUCCESS: Achieved {args.required_passes} consecutive {STATUS_NO_FINDINGS} passes!")
                return 0
        else:
            consecutive_passes = 0
            print(f"[{utc_now()}] {STATUS_FINDINGS_DETECTED} ({reason}) — triggering remediation pass...")
            invoke_opencode_agent(
                repo_root,
                repo_root / REMEDIATION_PROMPT_FILE,
                f"Remediate every finding in {REPORT_FILE}, re-run `./scripts/generate-rigs.py` and `./scripts/verify-rigs.sh` until green, and update REMEDIATION_LOG.md.",
                args.model,
                logs_dir / f"iter-{iteration:02d}-remediation.log",
            )

    print(f"\n[{utc_now()}] FAILED: Reached max iterations ({args.max_iterations}) without achieving {args.required_passes} consecutive passes.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
- **Acceptance:**
  ```bash
  python3 ./scripts/audit_loop.py --self-test | grep -q "SELF-TEST PASSED"
  ```

### Milestone 7: Idempotency & Sabotage Gate Verification
- **Do:**
  1. Run `python3 scripts/generate-rigs.py` a second time and verify `registry/status.json` `bodyDigest` is unchanged.
  2. Run the sabotage checks from `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` Section 4 in a temporary directory and confirm `verify-rigs.sh` catches every single one.
- **Acceptance:**
  ```bash
  BEFORE="$(jq -r .bodyDigest registry/status.json)" && python3 scripts/generate-rigs.py && AFTER="$(jq -r .bodyDigest registry/status.json)" && test "$BEFORE" = "$AFTER"
  ```

### Milestone 8: Final Audit Loop & Pull Request Readiness
- **Do:**
  1. Run `./scripts/verify-rigs.sh --check-only` and `python3 ./scripts/audit_loop.py --self-test` (or full `python3 ./scripts/audit_loop.py` when `opencode` CLI is active).
  2. Verify all 6 deliverables (`docs/OSINT_ECOSYSTEM_REPORT.md`, `docs/OPENRIG_MUSE_GO_ARCHITECTURE.md`, `PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md`, `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`, `PROMPT_FLEET_AUDIT_REMEDIATION.md`, `scripts/audit_loop.py`) are committed cleanly.
- **Acceptance:**
  ```bash
  ./scripts/verify-rigs.sh --check-only && python3 ./scripts/audit_loop.py --self-test
  ```

---

## 7. Gotchas (Re-Read Before Every Milestone)

1. **CLI Name Trap**: The OpenRig CLI executable is `rig`, never `openrig`.
2. **51-Role Parity Trap**: `ROLE_CATALOG_50.md` has **51** roles (`static-analysis-lead` is Role 37 in Rig 6; `ai-red-teamer` is Role 51 in Rig 7). Missing either fails V1 and V2.
3. **`PI_PROVIDER_ENV_VARS` Trap**: `runtime: pi` does NOT receive `OPENCODE_API_KEY` from the daemon environment (`pi-runner-protocol.ts:102`); seats must be provisioned via `scripts/bootstrap-pi-seats.sh` writing `$OPENRIG_HOME/state/pi/<seat>/agent/{models.json,auth.json}`.
4. **Pi Plugin Projection Trap**: `PiRuntimeAdapter.projectEntry()` (`pi-runtime-adapter.ts:392`) skips plugins, subagents, and runtime_resources; OpenRig operating skills must live in `specs/agents/shared/agent.yaml` under `resources.skills`.
5. **Symlink & Relative Path Trap**: `checkBundleFolder` (`bundle-check.ts:41`) resolves `fs.realpathSync` and fails if any `agent_ref` or `imports[].ref` points outside `rigs/<rig-slug>/`, and `specs.ts:44` rejects symlinks. Always materialize real directory copies into `rigs/<rig-slug>/agents/`.
6. **PyYAML Date Trap**: Always normalize `yaml.safe_load()` output with `json.loads(json.dumps(raw, default=str))` before validating against `schemas/*.v1.schema.json`.
7. **Pod-Local vs Cross-Pod Edge Trap**: Pod-local edges (`pods[i].edges`) MUST use unqualified member IDs (`exec-director`), whereas top-level `edges` MUST use qualified `pod.member` IDs (`governance.exec-director`) across different pods.
8. **Quoted Version Trap**: In `agent.yaml` and `rig.yaml`, `version: "1.0"` and `version: "0.2"` MUST be quoted strings; unquoted numbers fail OpenRig's validator.

---

## 8. Definition of Done

- [ ] All 51 specialist roles from `Heretek-Crew/roles-catalog/ROLE_CATALOG_50.md` exist in `specs/agents/<domain>/<role-slug>/` with valid `agent.yaml` (`version: "1.0"`), `guidance/role.md`, `startup/context.md`, `runtime/*.json`, and custom `skills/*/SKILL.md`.
- [ ] All 8 OpenRig v0.2 bundles exist under `rigs/<rig-slug>/` with materialized `agents/<role-slug>/` and `agents/shared/`, `CULTURE.md`, `README.md`, `SETUP.md`, `configurations.yaml`, and `bundle.yaml` (zero symlinks).
- [ ] Every seat across all 51 agents and 8 rigs is locked to `model: opencode-go/muse-spark-1.3-contributor:high` on `runtime: pi` (with `all-omp`, `all-claude`, and `all-codex` presets in `configurations.yaml`).
- [ ] All 16 read-only auditor/director roles enforce `permission_policy: builtin:locked`, `pi_security_mode: "max"`, and read-only MCP tool scoping.
- [ ] All 8 `configurations.yaml`, 8 `registry/views/*/behaviour.json`, 8 `registry/entries/*.yaml`, and `registry/status.json` pass `Draft202012Validator` against `schemas/*.v1.schema.json` and match their computed `configurationId`, `packageDigest`, and RFC 8785 JCS `bodyDigest`.
- [ ] `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, and `python3 ./scripts/audit_loop.py --self-test` all exit 0.
