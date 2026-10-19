# Heretek-Rigs — 51-Agent OpenRig + Pi + OpenCode Go Fleet

## Rigs (8)
- executive-and-architecture
- fullstack-and-web-studio
- systems-and-mobile-foundry
- game-dev-and-sim-rig
- cloud-sre-and-data-platform
- qa-and-verification-gauntlet
- defensive-sec-and-red-team
- heretek-omni-fleet (3-seat command + 15 pods + 51 members + rig.all-51.yaml)

## Model
- `opencode-go/muse-spark-1.3-contributor:high` via `https://opencode.ai/inference/go/v1`.

## Secret provisioning
- `$HERETEK_SECRETS/opencode-go.key` with mode `600`.
- `auth.json` uses `!cat` (never inline secrets).

## Makefile targets
| Target | Purpose |
|---|---|
| generate | Deterministically generate AgentSpecs, RigBundles, Roster, Registry |
| verify | Self-testing verification gate |
| test | Unit tests for seat rendering and permissions |
| bootstrap-seats | Provision Pi seats across all rigs |
| seed | Seed one rig before launch |
| gate | Gate-test one role against mock OpenAI |
| guard-profiles | Fail-closed sidecar profile guard |
| sidecars-up | Start sidecar containers |
| sidecars-down | Stop sidecars, preserve volumes |
| bundle-check | `rig bundle check` across all 8 rigs |
| audit-loop | Adversarial audit and remediation loop |

## Sidecars
- Sidecar profiles note: enable only needed profiles via `SIDECAR_PROFILES`.
- `guard-profiles`: mobile/devsec isolation — never co-schedule `--profile mobile` with `devsec` or `web-research`.

## Seat seeding
- Seed before `rig up` / `expand` / `add`.
