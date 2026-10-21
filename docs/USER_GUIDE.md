# Heretek-Rigs Operator & User Guide

Welcome to the operator manual for **`heretek-rigs`** — the 51-agent, 8-rig software engineering fleet built on **OpenRig v0.6.13** (`rig`), **Pi Coding Agent v1.3.0** (`pi`), **`@gotgenes/pi-permission-system@41.0.0`**, and **OpenCode Go** (`opencode-go/muse-spark-1.3-contributor:high`).

This guide walks you through installing prerequisites, provisioning zero-leak secrets, seeding isolated seat directories, launching and operating domain rigs, dynamically scaling the `heretek-omni-fleet` command center, running Docker sidecars safely, customizing the fleet catalog, and troubleshooting common issues.

## 1. Prerequisites & Toolchain Installation

### System Requirements

| Component | Required Version | Purpose |
| :--- | :--- | :--- |
| **Operating System** | Linux or macOS (WSL2 on Windows) | Host environment for OpenRig daemon, `tmux` sessions, and Docker sidecars. |
| **Node.js & npm** | Node.js `22.x` or `24.x` (`>=22.19.0`) | Required by `@openrig/cli@0.6.13` (`better-sqlite3` ABI) and `@earendil-works/pi-coding-agent@1.3.0`. (Node 20 is unsupported.) |
| **tmux** | `3.2+` | Terminal multiplexer backing all OpenRig agent seats. |
| **Python 3** | `3.10+` with `pyyaml` and `jsonschema` (or `uv`) | Runs `generate-rigs.py`, `render-seat.py`, `seed-rig.py`, `verify-rigs.sh`, and `audit_loop.py`. All scripts automatically fall back to `uv run --with pyyaml --with jsonschema` if `uv` is installed. |
| **Docker & Compose** | Docker Engine + `docker compose` v2 | Optional for core rig launch; required when starting supporting sidecar profiles (`docker-compose.sidecars.yml`) or the `terraform` MCP container. |

### Step 1: Install OpenRig CLI (`rig`) and Pi Coding Agent (`pi`)

Install the exact pinned versions of the OpenRig CLI (`@openrig/cli@0.6.13`) and Pi Coding Agent (`@earendil-works/pi-coding-agent@1.3.0`) globally:

```bash
npm install -g @openrig/cli@0.6.13 @earendil-works/pi-coding-agent@1.3.0
rig --version   # Expect: 0.6.13 (9eeb2e42)
pi --version    # Expect: 1.3.0
```

> **Note**: Always invoke the OpenRig CLI using `rig` (or `openrig-tui` for the standalone dashboard binary), never `openrig`.

### Step 2: Install Pi Permission & AST/LSP Packages into `$HERETEK_TOOLS`

By default, `scripts/render-seat.py` looks for Pi extension packages and local npm MCP binaries under `$HERETEK_TOOLS` (which defaults to `~/.local/share/heretek-rigs/tools`). Install the mandatory permission harness (`@gotgenes/pi-permission-system@41.0.0`) and optional builder AST/LSP extensions (`pi-lsp-extension@1.4.0`, `pi-ast-grep@0.1.0`):

```bash
export HERETEK_TOOLS="${HERETEK_TOOLS:-$HOME/.local/share/heretek-rigs/tools}"
mkdir -p "$HERETEK_TOOLS/pi-packages" "$HERETEK_TOOLS/mcp" "$HERETEK_TOOLS/bin" "$HERETEK_TOOLS/src"

# 1. Install Pi permission and AST/LSP packages
npm --prefix "$HERETEK_TOOLS/pi-packages" install \
  @gotgenes/pi-permission-system@41.0.0 \
  pi-lsp-extension@1.4.0 \
  pi-ast-grep@0.1.0

# 2. Install stdio npm MCP servers used by fleet seats
npm --prefix "$HERETEK_TOOLS/mcp" install \
  codebase-memory-mcp@0.12.1 \
  @upstash/context7-mcp@4.4.2 \
  @modelcontextprotocol/server-memory@1.0.0 \
  @playwright/mcp@0.0.83 \
  chrome-devtools-mcp@1.11.0 \
  @mobilenext/mobile-mcp@1.0.12 \
  mcp-openapi-schema-explorer@1.3.5 \
  kubernetes-mcp-server@0.0.67
```

If you plan to run the binary/firmware reverse engineering seats (`binary-reverse-eng`, `firmware-sec-analyst`), build the pinned read-only `radare2-mcp@1.9.0` binary into `$HERETEK_TOOLS/bin/r2mcp`:

```bash
git clone --depth 1 --branch 1.9.0 https://github.com/radareorg/radare2-mcp "$HERETEK_TOOLS/src/radare2-mcp"
make -C "$HERETEK_TOOLS/src/radare2-mcp"
install -m 755 "$HERETEK_TOOLS/src/radare2-mcp/src/r2mcp" "$HERETEK_TOOLS/bin/r2mcp"
```

## 2. Environment Variables & Zero-Leak Secret Provisioning

### Key Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `OPENRIG_HOME` | `~/.openrig` | Root directory for OpenRig daemon state, SQLite database, and per-seat Pi directories (`$OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent/`). |
| `HERETEK_TOOLS` | `~/.local/share/heretek-rigs/tools` | Base directory containing `pi-packages/node_modules`, `mcp/node_modules`, and `bin/r2mcp`. |
| `HERETEK_SECRETS` | `~/.config/heretek-rigs/secrets` | Mode `0700` directory holding mode `0600` secret files referenced via `!cat` in `auth.json` and `mcp.json`. |
| `HERETEK_WORKSPACE` | Current working directory (`.`) | Target project repository path passed to `rig up rig.yaml --cwd "$HERETEK_WORKSPACE"`. |
| `SIDECAR_PROFILES` | Empty (`""`) | Space- or comma-separated list of Docker Compose profiles for `make sidecars-up` (e.g., `"web-research"`, `"qa-testing"`). |

### Provisioning `$HERETEK_SECRETS` (`0700` Directory, `0600` Files)

OpenRig strips `OPENCODE_API_KEY` from `runtime: pi` child processes by design. Instead, `heretek-rigs` uses Pi's command-backed credential syntax (`"!cat /abs/path/to/secret"`), where Pi executes the command only when connecting to the inference endpoint or MCP server.

`scripts/render-seat.py` enforces strict security invariants on `$HERETEK_SECRETS`:
- Every secret file **must be a regular file** (symlinks are rejected before `stat()` and via `O_NOFOLLOW`).
- Every secret file **must be owned by your current effective UID** (`st_uid == os.geteuid()`).
- Every secret file **must have mode `0600`** (any group or world permission bit causes `render-seat.py` to abort with exit code `2`).

Create your secrets directory and provision your OpenCode Go API key (`opencode-go.key`):

```bash
export HERETEK_SECRETS="${HERETEK_SECRETS:-$HOME/.config/heretek-rigs/secrets}"
mkdir -p -m 700 "$HERETEK_SECRETS"

# Required for all 51 seats (OpenCode Go API key for Muse Spark 1.3 Contributor)
printf '%s' "your-opencode-go-api-key" > "$HERETEK_SECRETS/opencode-go.key"
chmod 600 "$HERETEK_SECRETS/opencode-go.key"
```

### Optional Role-Specific MCP Secret Files

Depending on which rigs and MCP servers you use, create the corresponding `0600` files in `$HERETEK_SECRETS`:

| Secret File (`$HERETEK_SECRETS/<file>`) | Bound MCP Server | Roles Requiring This Secret | Format / Example Content |
| :--- | :--- | :--- | :--- |
| `opencode-go.key` | Primary LLM (`auth.json`) | **All 51 roles** | Bare OpenCode Go API key string |
| `github.pat` | `github` | `exec-director`, `product-director`, `tpm-scrum-lead`, `ux-research-analyst`, `release-qa-officer`, `threat-modeler`, `compliance-auditor` | Bare GitHub Personal Access Token (expanded via `!echo Bearer $(cat @SECRETS@/github.pat)`) |
| `context7.key` | `context7` (optional) | `system-architect`, `ts-node-fullstack`, `python-backend-spec`, `go-backend-eng`, `rust-systems-spec`, `ai-red-teamer` | Bare Context7 API key (if omitted, `CONTEXT7_API_KEY` env is cleanly stripped) |
| `aws.profile`, `aws.region`, `aws.config`, `aws.credentials` | `aws` | `cloud-platform-eng`, `cloud-sec-auditor` | AWS profile name, region (e.g., `us-east-1`), config file, and credentials file |
| `kubeconfig` | `kubernetes` | `k8s-orchestrator` | Standard Kubernetes client config file (read-only cluster access) |
| `prometheus.url` | `prometheus` | `sre-incident-eng`, `observability-eng` | Prometheus base URL (e.g., `http://127.0.0.1:9090`) |
| `postgres-readonly.uri` | `postgres` | `dba-specialist` | Read-only PostgreSQL URI (`postgresql://ro_user:pass@host:5432/dbname`) |
| `redis-readonly.url` | `redis` | `cache-streaming-eng` | Read-only Redis URI (`redis://ro_user:pass@host:6379/0`) |
| `clickhouse.host`, `clickhouse.user`, `clickhouse.password` | `clickhouse` | `analytics-metrics-eng` | ClickHouse hostname, read-only username, and password |

> **Tip — Degraded Seeding (`--allow-missing-secrets`)**: If you only have `opencode-go.key` (or want to test seat rendering before provisioning every cloud/database credential), pass `--allow-missing-secrets` to `seed-rig.py` or `bootstrap-pi-seats.sh`. Any MCP server (or `auth.json`) whose required secret file is missing will be written with `"enabled": false` and logged as a warning to `stderr` rather than aborting.

## 3. Quickstart: Verify, Seed, Validate, and Launch a Rig

Follow these five steps from the root of the `heretek-rigs` repository to verify your checkout, seed your seats, and launch a rig.

### Step 1: Run the Self-Testing Verification Gate

Verify that all 51 AgentSpecs, 8 RigBundles, JSON schemas, cryptographic digests, and unit tests are intact:

```bash
make verify
```

You should see `SUMMARY: 22 checks passed, 0 failed.`

### Step 2: Seed the Pi Seats for Your Target Rig

**Crucial Rule**: Always seed a rig's seats **before** running `rig up`, `rig expand`, or `rig add`. Seeding populates `$OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent/` with `auth.json`, `models.json`, `settings.json`, `mcp.json`, `extensions/pi-permission-system/config.json`, and `AGENTS.md` (all mode `0600`).

To seed a single rig (for example, `executive-and-architecture`):

```bash
# Strict mode (requires opencode-go.key + github.pat in $HERETEK_SECRETS):
python3 ./scripts/seed-rig.py rigs/executive-and-architecture/rig.yaml

# Or degraded mode (disables MCP servers whose secret files are not yet provisioned):
make seed RIG=executive-and-architecture
```

Or provision all 54 default boot seats across all 8 rigs at once:

```bash
# Strict mode (all required secrets must exist):
make bootstrap-seats

# Degraded mode (allows missing secrets with "enabled": false):
bash ./scripts/bootstrap-pi-seats.sh --all --allow-missing-secrets
```

### Step 3: Validate the Bundle and Start the OpenRig Daemon

Run offline bundle and spec checks first, then start the OpenRig daemon and run preflight checks:

```bash
# 1. Offline bundle integrity check (returns [] when 0 findings exist)
rig bundle check rigs/executive-and-architecture --json

# 2. Offline RigSpec v0.2 structural validation
(cd rigs/executive-and-architecture && rig spec validate rig.yaml --json)

# 3. Start the local OpenRig daemon (if not already running)
rig daemon start --no-kernel

# 4. Run live daemon preflight and AgentSpec validation
(cd rigs/executive-and-architecture && rig spec preflight rig.yaml --json)
(cd rigs/executive-and-architecture && rig agent validate agents/exec-director --json)
```

### Step 4: Launch the Rig Against Your Target Workspace

Set `HERETEK_WORKSPACE` to the git repository you want the rig to work on, and launch the rig from inside `rigs/<rig-id>/` so local `agents/<role>` references resolve cleanly:

```bash
export HERETEK_WORKSPACE="/path/to/your/project-repo"
(cd rigs/executive-and-architecture && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)
```

### Step 5: Inspect Running Seats and Open the Dashboard

```bash
# Check seat status and readiness
rig ps --nodes --rig executive-and-architecture

# Open the OpenRig Terminal UI dashboard
rig tui
```

## 4. Day-to-Day Fleet Operations

### Addressing Seats

Every running seat in OpenRig has a canonical address of the form:
`<pod>-<member>@<rig>`

For example:
- `exec-exec-director@executive-and-architecture` (Director / CEO-Delegate in the `exec` pod)
- `delivery-tpm-scrum-lead@executive-and-architecture` (TPM / Scrum Lead in the `delivery` pod)
- `build-ts-node-fullstack@fullstack-and-web-studio` (TypeScript / Node Fullstack Lead in the `build` pod)
- `qa-release-qa-officer@qa-and-verification-gauntlet` (Release QA Officer in the `qa` pod)
- `blue-threat-modeler@defensive-sec-and-red-team` (Threat Modeler in the `blue` pod)

### Assigning Missions & Managing Work Queues

In `heretek-rigs`, work moves in small, verifiable slices through OpenRig queues (`mission-slice-sop` and `queue-handoff`). Send your high-level objective to a pod lead or director seat, and track progress through `rig queue`:

```bash
# 1. Send a mission to the pod lead
rig send exec-exec-director@executive-and-architecture \
  "Draft an ADR and sprint breakdown for migrating our auth service to passkeys. Coordinate with system-architect and tpm-scrum-lead."

# 2. Inspect the seat's queue items
rig queue list --destination exec-exec-director@executive-and-architecture --limit 100

# 3. Capture recent terminal output or full conversation transcript from a seat
rig capture exec-exec-director@executive-and-architecture
rig transcript exec-exec-director@executive-and-architecture
```

> **Operator relays must be authenticated (issue #9).** `rig send` issued from outside
> a managed seat arrives with no sender identity, so seats hold it as UNVERIFIED.
> Never relay a human decision with raw `rig send` — use
> `scripts/send-authenticated.sh`, which files the relay as a signed queue item
> (`rig queue create --destination <session> --body-file <file>`) self-identified as
> operator-relayed with its human-ref grounding, UTC timestamp, and verbatim-relay
> statement. It never claims seat origin. See `--help` for the full contract.

### How Seats Handle Permission Denials & Escalations

Every seat is governed by the **Heretek Fleet Culture** (`CULTURE.md`) and `@gotgenes/pi-permission-system@41.0.0`:
- **Evidence Over Assertion**: Every seat must include the exact verification command and its output before marking a queue slice complete.
- **Permission Denials Are Hand-Offs**: If a seat attempts to write outside its `path_write` globs (for example, `appsec-engineer` attempting to edit `src/auth.ts` directly when its writable path is `docs/security/advisories/*`), `@gotgenes/pi-permission-system` immediately returns:
  `[pi-permission-system] Denied by policy: 'path_write' for tool 'write' for path 'src/auth.ts' (rule '*')`
- Instead of working around the restriction, the seat writes its advisory to `docs/security/advisories/` and escalates or hands off the code fix to its designated escalation target (`rig send <reports_to> "<message>"`) as documented in its `<agentDir>/AGENTS.md` `## Seat` block.

### Snapshotting, Restoring, and Stopping a Rig

```bash
# Stop a rig while capturing a full state snapshot for later resumption
rig down executive-and-architecture --snapshot

# Restore a snapshotted rig
rig up executive-and-architecture

# Stop and tear down a rig cleanly
rig down executive-and-architecture
```

## 5. Choosing the Right Rig for Your Mission

| Scenario / Engineering Goal | Recommended Rig | Lead Seat to Contact First | Key Writable Outputs |
| :--- | :--- | :--- | :--- |
| **Product roadmap, OKRs, architecture decision records (MADRs), sprint planning, or repo documentation** | `executive-and-architecture` (6 seats, all `builtin:locked`) | `exec-exec-director@executive-and-architecture` or `delivery-tpm-scrum-lead@executive-and-architecture` | `docs/executive/*`, `docs/product/*`, `docs/adr/*`, `docs/architecture/*`, `docs/sprints/*`, `docs/ops/*`, `docs/*` |
| **Building web apps, REST/gRPC backends (TS/Node, Python, Go, Java/Kotlin), design systems, a11y, or UX research** | `fullstack-and-web-studio` (11 seats) | `build-ts-node-fullstack@fullstack-and-web-studio` or `design-ui-ux-designer@fullstack-and-web-studio` | `src/*`, `app/*`, `cmd/*`, `internal/*`, `pkg/*`, `packages/ui/*`, `tokens/*`, `tests/a11y/*`, `docs/research/*` |
| **Low-level Rust crates, C++20/23 libraries with ASan/UBSan/libFuzzer, or native Android/iOS mobile apps** | `systems-and-mobile-foundry` (4 seats) | `systems-rust-systems-spec@systems-and-mobile-foundry` or `mobile-android-mobile-spec@systems-and-mobile-foundry` | `crates/*`, `src/*`, `include/*`, `app/src/*`, `ios/*`, `Sources/*`, `Tests/*` |
| **ECS game engines, deterministic physics, HLSL/WGSL/GLSL shaders, gameplay AI, or glTF asset pipelines** | `game-dev-and-sim-rig` (6 seats) | `engine-engine-systems-eng@game-dev-and-sim-rig` or `gameplay-game-systems-dev@game-dev-and-sim-rig` | `src/engine/*`, `src/shaders/*`, `src/rendering/*`, `src/game/*`, `assets/*`, `tools/asset-pipeline/*` |
| **OpenTofu/Terraform IaC, Kubernetes/Helm, CVE patching, SRE postmortems, DB migrations, dbt/ClickHouse, or RAG** | `cloud-sre-and-data-platform` (11 seats) | `platform-cloud-platform-eng@cloud-sre-and-data-platform` or `data-dba-specialist@cloud-sre-and-data-platform` | `terraform/*`, `infra/*`, `deploy/*`, `k8s/*`, `migrations/*`, `dbt/*`, `pipelines/*`, `src/rag/*` |
| **Pre-release verification, Playwright E2E tests, OpenAPI contract checks, k6 load tests, mutation testing, or Semgrep** | `qa-and-verification-gauntlet` (6 seats) | `qa-release-qa-officer@qa-and-verification-gauntlet` | `docs/releases/*`, `tests/e2e/*`, `tests/api/*`, `tests/load/*`, `tests/chaos/*`, `rules/*` |
| **Zero-trust security audit: STRIDE threat modeling, OWASP triage, IAM audit, SBOMs, LLM red-teaming, or binary RE** | `defensive-sec-and-red-team` (7 seats, all `builtin:locked`) | `blue-threat-modeler@defensive-sec-and-red-team` or `red-ai-red-teamer@defensive-sec-and-red-team` | `docs/security/threat-models/*`, `docs/security/advisories/*`, `docs/security/cloud/*`, `sbom/*`, `docs/security/ai-redteam/*`, `docs/protocols/*`, `docs/forensics/*`, `docs/security/firmware/*` |
| **Cross-domain mission starting small (3 seats) and scaling pods/specialists on demand** | `heretek-omni-fleet` (3 default seats, scales to 51) | `command-exec-director@heretek-omni-fleet` | Starts with `docs/executive/*`, `docs/sprints/*`, `docs/adr/*`; scales dynamically as pods/members are attached |

## 6. Dynamic Scaling with `heretek-omni-fleet`

Instead of booting all 51 agents at once, `rigs/heretek-omni-fleet/` provides a **Hybrid Omni-Fleet** workflow:

### Mode A: Boot the 3-Seat Command Pod and Scale on Demand (Recommended)

1. **Seed and launch the 3-seat command center** (`exec-director`, `tpm-scrum-lead`, `system-architect`):
   ```bash
   python3 ./scripts/seed-rig.py rigs/heretek-omni-fleet/rig.yaml --allow-missing-secrets
   (cd rigs/heretek-omni-fleet && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)
   ```
2. **Dynamically attach any of the 15 domain pods (`rig expand`)**:
   Available pod fragments in `rigs/heretek-omni-fleet/pods/` are: `exec`, `delivery`, `build`, `design`, `systems`, `mobile`, `engine`, `gameplay`, `platform`, `sre`, `data`, `ml`, `qa`, `blue`, and `red`.
   Always seed the pod fragment first, then run `rig expand`:
   ```bash
   # Example: Attach the 'blue' security pod to the running heretek-omni-fleet rig
   python3 ./scripts/seed-rig.py rigs/heretek-omni-fleet/pods/blue.yaml \
     --rig heretek-omni-fleet --allow-missing-secrets

   RIG_ID=$(rig ps --json | jq -r '.[] | select(.name=="heretek-omni-fleet") | .rigId')
   (cd rigs/heretek-omni-fleet && rig expand "$RIG_ID" pods/blue.yaml --rig-root "$PWD" --json)
   ```
3. **Dynamically attach a single specialist seat to an existing pod (`rig add`)**:
   All 51 specialist roles have member fragments in `rigs/heretek-omni-fleet/members/<role>.yaml`.
   Always seed the member fragment for the target rig and pod first, then run `rig add`:
   ```bash
   # Example: Add 'rust-systems-spec' into the 'command' pod (or 'systems' pod)
   python3 ./scripts/seed-rig.py rigs/heretek-omni-fleet/members/rust-systems-spec.yaml \
     --rig heretek-omni-fleet --pod command --allow-missing-secrets

   (cd rigs/heretek-omni-fleet && rig add heretek-omni-fleet command members/rust-systems-spec.yaml --rig-root "$PWD" --json)
   ```

### Mode B: Boot the Full 51-Seat Static Omni Profile (`rig.all-51.yaml`)

If you have sufficient host memory and want all 15 pods and 51 seats running inside `heretek-omni-fleet` simultaneously:

```bash
# 1. Seed all 51 seats under @heretek-omni-fleet
bash ./scripts/bootstrap-pi-seats.sh --profile all-51 --allow-missing-secrets

# 2. Launch rig.all-51.yaml
(cd rigs/heretek-omni-fleet && rig up rig.all-51.yaml --cwd "$HERETEK_WORKSPACE" --yes)
```

### Consulting the Fleet Roster (`rosters/heretek-omni-fleet.json`)

Agents and operators can query `rosters/heretek-omni-fleet.json` to find which specialist seat owns a capability:

```bash
jq '.members[] | select(.capabilities[] | contains("semgrep"))' rosters/heretek-omni-fleet.json
```

## 7. Managing Docker Sidecar Services

Supporting services (`docker-compose.sidecars.yml`) are opt-in by profile and bind exclusively to `127.0.0.1`.

### Sidecar Environment Variables (`.env`)

Before starting `web-research` or `ai-gateway` sidecars, set the required secret variables in your shell or `.env` file (the Compose specification uses `${VAR:?...}` fail-closed guards):

| Variable | Required By Profile / Service | Purpose |
| :--- | :--- | :--- |
| `SEARXNG_SECRET` | `web-research` (`searxng`) | Secret key for the local SearXNG metasearch instance (`127.0.0.1:8888`). |
| `BROWSERLESS_TOKEN` | `web-research` (`browserless`) | Authentication token for headless Chrome on `127.0.0.1:3000`. |
| `QDRANT_API_KEY` | `ai-gateway` (`qdrant`) | API key for the Qdrant vector database container on `127.0.0.1:6333`. |

### Starting and Stopping Sidecars Safely

**Never invoke `docker compose -f docker-compose.sidecars.yml` directly**, as raw Compose bypasses the mobile/devsec isolation guard. Always use `make sidecars-up` or `./scripts/compose-sidecars.sh`:

```bash
# Start web-research sidecars (searxng, browserless, firecrawl, firecrawl-redis)
make sidecars-up SIDECAR_PROFILES="web-research"

# Start devsec sidecars (ghidra on :1337, radare2 on :9090, sonarqube on :9000)
# Note: Place binaries to analyze in ./workspaces/binaries (mounted :ro at /samples)
mkdir -p ./workspaces/binaries
make sidecars-up SIDECAR_PROFILES="devsec"

# Start qa-testing sidecar (GET-only docker-socket-proxy) and ai-gateway (qdrant)
make sidecars-up SIDECAR_PROFILES="qa-testing ai-gateway"

# Start isolated Android emulator sidecar (6080) ALONE
make sidecars-up SIDECAR_PROFILES="mobile"

# Stop all running sidecar containers while preserving named volumes
make sidecars-down
```

> **Isolation Rule**: `make guard-profiles` and `./scripts/compose-sidecars.sh` will refuse to start `--profile mobile` alongside `devsec` or `web-research` (`exit 1`) so the Android emulator remains strictly isolated on the internal `heretek-mobile` bridge network.

## 8. Customizing the Fleet, Regenerating Artifacts & Running Security Gates

### Editing `fleet/fleet.yaml` or `fleet/mcp-servers.yaml`

Never hand-edit files under `specs/`, `rigs/`, `rosters/`, or `registry/`. Because `rigs/*/bundle.yaml` and `registry/status.json` embed SHA-256 digests over every generated file, any manual edit to a generated file will immediately break `make verify` (Stage V3/V5).

To modify a role's permissions, skills, thinking level, or MCP bindings:
1. Edit `fleet/fleet.yaml` or `fleet/mcp-servers.yaml`.
2. Ensure your git working tree is clean (or set `HERETEK_RIGS_ALLOW_DIRTY=1` during local development so `resolve_heretek_commit()` allows provenance baking on a dirty worktree).
3. Ensure the pinned upstream checkouts exist in `.scratch/vendor/` (`obra_superpowers@bb92a77`, `trailofbits_skills@5c99c03`, `getsentry_skills@f57ada2`, `anthropics_skills@dbd4588`, `vercel-labs_agent-skills@063bee9`, plus `Heretek-Crew@5ffb1fc` and `@openrig/cli@0.6.13`).
4. Run the deterministic generator and idempotency gate:
   ```bash
   HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py
   HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py --check-idempotent
   make verify
   ```

### Live Role Permission Gate Testing (`make gate`)

To test a role's rendered `@gotgenes/pi-permission-system@41.0.0` configuration against a local mock OpenAI server (`scripts/mock-openai.mjs`) and real `pi --no-approve --mode json` execution across 32+ hostile probes (unauthorized writes, `AGENTS.md` overwrites, `..` traversal, `curl`, `;` / `|` / `&` / `$()` / backtick / newline command chaining, `--output` write escapes, `git log -p` / `--patch` / `--full-diff` / `--textconv` read-deny bypasses, `.env` / `*.pem` / `*.url` / `*.user` / `.pi/` / `.agents/` / `fleet/*` / `scripts/*` reads, and `code_rewrite` / `lsp_rename` / `lsp_code_actions` mutations):

```bash
make gate ROLE=appsec-engineer
make gate ROLE=exec-director
make gate ROLE=go-backend-eng
```

### Fleet Wiring & Topography (`make topology`)

To verify every cross-reference in the catalog and render the whole hierarchy:

```bash
make topology OUT=/tmp/heretek-topology
```

`scripts/topology.py` fail-closed checks that every `reports_to.address` resolves to
a real seat, every `collaborators[]` / skill / MCP / package reference exists on
disk and in the lockfiles, every `rig.yaml` member matches `fleet.yaml` (and vice
versa), all 51 member fragments are present, and every pod edge endpoint exists with no
self-edges. It then renders `graph.json`, an org-chart SVG
(15 pods + command), per-rig agent SVGs, per-rig seat×resource bipartite SVGs, and a
51-row `matrix.md`. Orphan skills/servers and omni-divergent `reports_to` addresses
are reported as advisory warnings only. The `.github/workflows/topology.yml` CI job
runs this on every push/PR and uploads the renderings as artifacts.

### Live Seat Audit (`make audit-sessions`)

To scan running seats for misattributed permission denials (assistant claims a
tool-wide ban while the review log shows a unit-scoped deny and the config allows
the capability) and false delivery claims (`DISPATCHED` with no `qitem-` id):

```bash
make audit-sessions WORKSPACE=/path/to/seat-workspace
```

Findings are leads for operator review (exit 1 when any exist), not verdicts:
assistant-text matching is heuristic, and delivery flags do not cross-check live
queue state. Scans every seat under `OPENRIG_HOME/state/pi`, including archived rigs.

## 9. Complete Command Reference (`Makefile` & Scripts)

### `Makefile` Targets

| Command | Description |
| :--- | :--- |
| `make help` | List all documented `Makefile` targets and descriptions. |
| `make generate` | Run `python3 ./scripts/generate-rigs.py` to regenerate all 51 AgentSpecs, 8 RigBundles, Roster, and Registry views. |
| `make idempotent` | Run `python3 ./scripts/generate-rigs.py --check-idempotent` (regenerates twice and fails if any byte differs). |
| `make verify` | Run `bash ./scripts/verify-rigs.sh` (all 6 verification stages V1–V6 + unit tests). |
| `make test` | Run `python3 -m unittest tests/test_render_seat.py -v` (7 offline unit tests for seat rendering and permissions). |
| `make bootstrap-seats` | Run `bash ./scripts/bootstrap-pi-seats.sh --all` (strict secret checking; provisions all 54 default boot seats). |
| `make seed RIG=<rig-id>` | Seed one rig in degraded-allowed mode: `python3 ./scripts/seed-rig.py rigs/$(RIG)/rig.yaml --allow-missing-secrets`. |
| `make gate ROLE=<role-id>` | Live-test one role's permission config against `mock-openai.mjs` and `pi`: `bash ./scripts/gate-role.sh $(ROLE)`. |
| `make topology OUT=<dir>` | Referential wiring gates + rendered topography (`graph.json`, org/rig/bipartite SVGs, 51-row matrix). |
| `make audit-sessions` | Detect misattributed denials + false delivery claims in live seats (`OPENRIG_HOME/state/pi` + workspace docs). |
| `make guard-profiles` | Fail-closed check refusing `SIDECAR_PROFILES` that combine `mobile` with `devsec` or `web-research`. |
| `make sidecars-up SIDECAR_PROFILES="..."` | Run `guard-profiles` then start the specified profiles in `docker-compose.sidecars.yml` (`up -d`). |
| `make sidecars-down` | Stop sidecar containers while preserving named volumes (`docker compose -f docker-compose.sidecars.yml down`). |
| `make bundle-check` | Run `verify` and then invoke `rig bundle check <rig> --json` across all 8 rigs if `rig` is on `PATH`. |
| `make audit-loop` | Run `python3 ./scripts/audit_loop.py` (automated OpenCode triad adversarial audit & remediation loop). |

### Direct Script CLI Reference

| Script | CLI Syntax & Options | Purpose |
| :--- | :--- | :--- |
| `scripts/render-seat.py` | `python3 ./scripts/render-seat.py --role <role-id> --rig <rig-id> --pod <pod-id> [--member <id>] [--fleet fleet/fleet.yaml] [--mcp fleet/mcp-servers.yaml] [--charter <file>] [--out <dir>] [--model-provider opencode-go] [--model-id muse-spark-1.3-contributor] [--allow-missing-secrets] [--dry-run]` | Renders a single seat's 6 runtime files (`auth.json`, `models.json`, `mcp.json`, `settings.json`, `extensions/pi-permission-system/config.json`, `AGENTS.md`) with mode `0600`. |
| `scripts/seed-rig.py` | `python3 ./scripts/seed-rig.py <rig.yaml \| pod-fragment.yaml \| member-fragment.yaml> [--rig <rig-id>] [--pod <pod-id>] [--dry-run] [--allow-missing-secrets]` | Invokes `render-seat.py` for every seat in a `rig.yaml`, pod fragment (`--rig` required), or member fragment (`--rig` and `--pod` required). |
| `scripts/bootstrap-pi-seats.sh` | `bash ./scripts/bootstrap-pi-seats.sh [--rig <rig-slug> \| --all] [--profile all-51] [--dry-run] [--strict-secrets \| --allow-missing-secrets]` | Batch wrapper around `seed-rig.py` to provision one rig, all 8 default rigs (54 seats), or the 51-seat omni static profile (`--profile all-51`). |
| `scripts/verify-rigs.sh` | `bash ./scripts/verify-rigs.sh [--check-only \| --dry-run \| --help]` | Runs the 22-check offline verification suite (V1–V6) and unit tests. |
| `scripts/compose-sidecars.sh` | `SIDECAR_PROFILES="..." ./scripts/compose-sidecars.sh up -d` or `./scripts/compose-sidecars.sh --profile <p> up -d` | Fail-closed wrapper around `docker compose -f docker-compose.sidecars.yml` enforcing the `mobile` isolation guard. |
| `scripts/audit_loop.py` | `python3 ./scripts/audit_loop.py [--repo-root .] [--required-passes 3] [--max-iterations 15] [--model opencode-go/muse-spark-1.3-contributor] [--run-implementation-first] [--self-test \| --dry-run]` | Runs the automated adversarial triad audit (`Alpha`/`Beta`/`Gamma`) and remediation loop until 3 consecutive `STATUS: NO_FINDINGS` passes. |

## 10. Troubleshooting Guide

| Symptom / Error Message | Root Cause | Resolution |
| :--- | :--- | :--- |
| `error: missing /.../.config/heretek-rigs/secrets/opencode-go.key (chmod 600)` | You ran `render-seat.py`, `seed-rig.py`, or `bootstrap-pi-seats.sh` in default strict mode without provisioning `opencode-go.key` (or a role's required MCP secret). | Provision the secret file in `$HERETEK_SECRETS` with `chmod 600`, or pass `--allow-missing-secrets` to render the missing provider/MCP server with `"enabled": false`. |
| `error: /.../secrets/opencode-go.key is mode 644; run: chmod 600 ...` | The secret file has group or world permission bits (`mode & 0o077 != 0`). | Run `chmod 600 "$HERETEK_SECRETS"/*` and `chmod 700 "$HERETEK_SECRETS"`. |
| `error: /.../secrets/<file> must not be a symlink` or `must be owned by uid <uid>` | A file in `$HERETEK_SECRETS` is a symbolic link or owned by a different user account. | Replace the symlink with a regular file owned by your current user (`chown $(id -u):$(id -g)`) and set `chmod 600`. |
| `error: unknown pod '<pod>' for rig <rig> (valid pods: [...])` | `render-seat.py` or `seed-rig.py` was passed a `--pod` ID that does not belong to `--rig` in `fleet/fleet.yaml`. | Check the valid pod IDs for the target rig (or use `heretek-omni-fleet` when seeding pod/member fragments across all 15 pods). |
| `error: refusing to co-schedule --profile mobile with devsec/web-research` | `SIDECAR_PROFILES` or `--profile` flags included both `mobile` and `devsec` or `web-research`. | Run `mobile` in its own isolated sidecar session; stop `devsec`/`web-research` with `make sidecars-down` before starting `mobile`. |
| `error: refusing to bake provenance on a dirty checkout` | `scripts/generate-rigs.py` detected uncommitted changes via `git status --porcelain`. | Commit or stash your changes before running `make generate`, or set `HERETEK_RIGS_ALLOW_DIRTY=1` during local development iterations. |
| `Declared file is missing, unreadable or outside the bundle folder` during `rig up` or `rig bundle check` | `rig up` was run from outside the `rigs/<rig>/` directory without `--rig-root`, or a symlink was introduced into `rigs/<rig>/`. | Always run `(cd rigs/<rig> && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)` and ensure zero symlinks exist (`make verify` checks this in V3). |
| `rig spec preflight` fails with daemon connection error | The local OpenRig daemon is not running (`rig spec validate` and `rig bundle check` run offline, but `preflight` and `agent validate` require the daemon). | Start the daemon first with `rig daemon start --no-kernel` (or `rig daemon start`). |
