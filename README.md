# Heretek-Rigs — 51-Agent OpenRig + Pi + OpenCode Go Fleet

Deterministic, zero-trust multi-agent software engineering monorepo: **51 specialist
AI roles** across **8 OpenRig v0.2 bundles**, generated from a single declarative
catalog and enforced at runtime by Pi's permission system.

| Stack | Pin |
|---|---|
| Orchestration | `@openrig/cli@0.6.13` (binary `rig`) |
| Agent runtime | `@earendil-works/pi-coding-agent@1.3.0` (binary `pi`) |
| Permission enforcement | `@gotgenes/pi-permission-system@41.0.0` (fail-closed, `*..*` terminal deny) |
| Model | `opencode-go/muse-spark-1.3-contributor:high` via `https://opencode.ai/inference/go/v1` |

**Verified live** (2026-10-20, loopback daemon + real seats): 8/8 `rig spec validate`,
8/8 `bundle check` clean, 162/162 `agent validate`, 8/8 `preflight ready`, 25/25 JSON
schemas, digest recomputes match, 64/64 vendored skills match lock + upstream,
12/12 sabotage targets caught, seeded seats refuse out-of-scope writes/reads/secret
access. See `AUDIT_REPORT_FINDINGS.md` and `REMEDIATION_LOG.md`.

## Docs

- **`docs/USER_GUIDE.md`** — operator & setup guide: prerequisites, secret provisioning,
  quickstart (verify → seed → validate → launch), day-to-day ops, omni-fleet scaling,
  sidecars, customization, full command reference, troubleshooting.
- **`docs/TECHNICAL_DOCUMENTATION.md`** — architecture: source-verified upstream
  invariants, data-flow pipeline, 8-rig topology, full 51-role catalog, permission &
  security architecture, MCP catalog + skill provenance, sidecars, digests, gate stages.
- **`docs/OPENRIG_MUSE_GO_ARCHITECTURE.md`**, **`docs/OSINT_ECOSYSTEM_REPORT.md`** —
  design briefs (planning snapshots; `TECHNICAL_DOCUMENTATION.md` is authoritative
  where they differ).

Prefer Docker? Public images (`:latest` slim, `:full` with browser + radare2) run
with `--user 1000:1000` and secrets mounted at `/run/heretek-secrets:ro` — see
`docs/USER_GUIDE.md` §11 and `docker-compose.yml`.

## Quickstart

```bash
# 0. Prerequisites: rig 0.6.13, pi 1.3.0, Python 3.10+ (pyyaml, jsonschema), tmux 3.2+
npm install -g @openrig/cli@0.6.13 @earendil-works/pi-coding-agent@1.3.0

# 1. Secrets (0700 dir, 0600 files; strict mode refuses anything else)
mkdir -p -m 700 ~/.config/heretek-rigs/secrets
printf '%s' "<opencode-go-key>" > ~/.config/heretek-rigs/secrets/opencode-go.key
chmod 600 ~/.config/heretek-rigs/secrets/opencode-go.key

# 2. Verify the checkout (expect: 31 checks passed, 0 failed)
make verify

# 3. Seed seats BEFORE launch (strict; or make seed RIG=<id> for degraded mode)
python3 ./scripts/seed-rig.py rigs/executive-and-architecture/rig.yaml

# 4. Validate + launch against your workspace repo
(cd rigs/executive-and-architecture && rig bundle check . --json)
rig daemon start --no-kernel
(cd rigs/executive-and-architecture && rig up rig.yaml --cwd /path/to/project --yes)

# 5. Operate
rig ps --nodes --rig executive-and-architecture
rig send exec-exec-director@executive-and-architecture "Draft the sprint breakdown for <goal>."
rig queue list --destination exec-exec-director@executive-and-architecture --json
# Copy qitem IDs verbatim from --json output -- never retype them.
# Bare queue output (no flags) mixes JSON with a human trailer and MUST NOT be parsed — always pass --json.
# Bare create output is a human advisory, not proof of persistence — the agent-safe form is create --json --verify.
```

## Rigs (8)

| Rig (`rigs/<id>/`) | Seats | Policy |
|---|---|---|
| `executive-and-architecture` | 6 | `builtin:locked` |
| `fullstack-and-web-studio` | 11 | `builtin:standard` |
| `systems-and-mobile-foundry` | 4 | `builtin:standard` |
| `game-dev-and-sim-rig` | 6 | `builtin:standard` |
| `cloud-sre-and-data-platform` | 11 | `builtin:standard` |
| `qa-and-verification-gauntlet` | 6 | `builtin:standard` |
| `defensive-sec-and-red-team` | 7 | `builtin:locked` |
| `heretek-omni-fleet` | 3 → 51 (15 pods, `expand`/`add`, `rig.all-51.yaml`) | `standard` (command seats `locked`) |

## Guardrails (non-negotiable)

- **Never hand-edit** `specs/`, `rigs/`, `rosters/`, `registry/` — edit `fleet/fleet.yaml` /
  `fleet/mcp-servers.yaml` (or `scripts/`) and run `python3 ./scripts/generate-rigs.py`.
- **Never commit secrets** — seats reference `$HERETEK_SECRETS` via `!cat` only.
- **Seed before `up`/`expand`/`add`** — unseeded seats have no permission config.
- **Sidecars via `make sidecars-up`** — never raw `docker compose` (mobile/devsec guard).
- Full rule set: `PROMPT_FLEET_AUDIT_REMEDIATION.md` §2.
