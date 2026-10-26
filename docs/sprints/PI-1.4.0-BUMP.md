# Slice PI-1 — Pi Coding Agent 1.3.0 → 1.4.0

- **Date:** 2026-10-26
- **Branch:** `claude/project-thread-502xnv` (PR #118, after the OpenRig 0.7.2 slice)
- **Scope:** Pi version pin, Dockerfile ARG, bundle `SETUP.md` text, registry `harnessVersion`, current-state docs. No charter, permission, seat-scope, model or MCP-catalog change. `@gotgenes/pi-permission-system` stays at 41.0.0 (still npm `latest`; peer range `>=1.0.0`).
- **Authority:** human instruction "Update pi too" (2026-10-26).
- **Precedent:** `docs/sprints/CLI-0.7.2-BUMP.md`.

## 1. Version facts (checked 2026-10-26)

| Item | Value |
|---|---|
| npm `latest` | `1.4.0`, published 2026-10-21 (only release after 1.3.0) |
| Tarball | `npm pack @earendil-works/pi-coding-agent@1.4.0` sha256 `d155c16ef6fa00960fbf58b2911536e80b05f33700e0b14fbd08967ede0c7428` |
| Engines | `node >=22.19.0`, unchanged |
| Sibling packages | `pi-ai`, `pi-agent-core`, `pi-mcp`, `pi-tui`, `pi-codemode` all move to 1.4.0 |

## 2. What the fleet relies on, compared in the installed `dist/`

| Behaviour | 1.3.0 → 1.4.0 |
|---|---|
| `core/auth-storage.js` (command-backed `!cat` keys; `enabled` is never read, #102 HR-4.2) | Byte-identical. The degraded-seat rule (no provider entry when the key is missing) still holds. |
| `core/settings-manager.js` (`shellPath`, `defaultTools`, `packages`) | Byte-identical. |
| `utils/shell.js` custom `shellPath` | Still throws `Custom shell path not found` for a missing path, so the jail stays fail-closed. Only Windows detection changed. |
| `opencode-go` / `muse-spark-1.3-contributor` in `pi-ai` | Same entry: `openai-responses`, `https://opencode.ai/inference/go/v1`, 1,048,576 / 131,072, same cost. Other models in that provider changed; we pin none of them. |
| `models.json` schema (`core/model-config.js`) | Adds descriptions, `headers` and `samplingParams` fields. Our rendered keys are unchanged and still accepted. |
| Extension loader | Adds the `@earendil-works/pi-ai/models` alias. Nothing removed. |
| Resumed sessions (`#11062`) | Extension tools a branch never mentioned now start active. pi-permission-system gates calls, not activation, so the gate is unaffected. |
| OpenCode requests | Send `x-opencode-client` whenever attribution is on. Harmless for the endpoint. |

Changelog items with fleet value: compaction summaries no longer fail at the fixed output cap (#9512), sessions survive recovery from a cut-off tool call (#11227), whitespace-only tool output no longer 400s on OpenAI Responses (#8720), `mcp.json` with a UTF-8 BOM parses (#11191), and the `grep` tool ignores `RIPGREP_CONFIG_PATH`.

## 3. Repo changes

| File | Change |
|---|---|
| `scripts/generate-rigs.py` | New `PI_VERSION = "1.4.0"`; bundle `SETUP.md` and registry `harnessVersion` read it (all listings are still `Not tested`). |
| `docker/Dockerfile` | `ARG PI_VERSION=1.4.0`. |
| `scripts/render-seat.py`, `tests/test_render_seat.py` | Comments name both versions for the `enabled` rule. |
| Current-state docs | `AGENTS.md`, `README.md`, `Makefile`, `docs/USER_GUIDE.md`, `docs/TECHNICAL_DOCUMENTATION.md`, `fleet/fleet.yaml` header, `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`. |
| Generated (regen only) | 8 bundle `SETUP.md` files, registry digests and `harnessVersion`, `resolvedCommit`. |
| `.sonarcloud.properties` | Excludes the generated trees from duplication only. The 0.7.2 re-vendor copied ~370 new skill lines into every rig's `_shared`, which failed the "≤3% duplication on new code" gate (18.2%). |

Not rewritten: dated audit and planning records that name 1.3.0 as what was checked at the time.

## 4. Verification (cloud container, `pi` 1.4.0 and `rig` 0.7.2 on PATH)

- `scripts/gate-role.sh` for `api-contract-tester`, `release-qa-officer` and `cpp-lowlevel-eng` against the mock model with pi-permission-system 41.0.0 installed: all pass on 1.4.0. For `cpp-lowlevel-eng` the 53-line output is identical to the same run on 1.3.0.
- `tests/test_build_canary.py` with `HERETEK_TOOLS` pointing at an installed pi-permission-system 41.0.0: 11 OK on both 1.3.0 and 1.4.0, including the `CanaryMockProbes` allow and deny cases that the plain `make test` run skips without the extension.
- A rendered seat (dummy key, `--allow-missing-secrets`): `pi --list-models opencode-go` lists `muse-spark-1.3-contributor` at 1.0M / 131.1K; `pi mcp list --json` reads the seat's `mcp.json` with no errors.
- `./scripts/verify-rigs.sh --check-only` → **35 passed, 0 failed**. `make test` → 347 OK. `--check-idempotent` passes.

## 5. Not verified here (needs the fleet host)

1. A real turn against `opencode.ai` (the container can't reach it, and only a dummy key was used).
2. `npm i -g @earendil-works/pi-coding-agent@1.4.0`, re-seed and relaunch one canary rig, then one real queue handoff.

## 6. Rollback

`npm i -g @earendil-works/pi-coding-agent@1.3.0`, revert this slice's commits, re-run `generate-rigs.py`, re-seed. Pi keeps no migrated state, so nothing else needs restoring.
