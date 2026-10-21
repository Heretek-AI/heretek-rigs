# Tooling Batch B7 — Rig 4 (game-dev-and-sim-rig)

**Slice:** Workstream B, batch B7 · **Branch:** `feat/self-rig4-tooling` (worktree `heretek-rigs-self-b7`)
**Date:** 2026-10-20 · **Source:** Issue #14 rows 22–27 vs `fleet/mcp-servers.yaml` (20 servers) + `fleet/skills-lock.json` (64 skills) + Rig-4 seat records in `fleet/fleet.yaml`
**Status:** Zero-change batch, regen + `verify-rigs.sh --check-only` **22/0**. UNCOMMITTED, no push. Live-seat proof deferred (fleet down).
**Rig 4 membership confirmed:** exactly 6 seats carry `rig: game-dev-and-sim-rig` — `engine-systems-eng` (engine pod lead), `physics-sim-eng`, `graphics-shader-eng`, `game-systems-dev` (gameplay pod lead), `game-ai-dev`, `tech-artist-pipeline`. No other seat belongs to this rig.

Every row 22–27 is accounted below. Net catalog/fleet change: **none** — all items resolve to ALREADY PRESENT, REFUSED/EXCLUDED on execution-widening or auth-model grounds, DEFERRED with a named blocker, or INFORMATIONAL (no fleet mechanism). B2/B3/B5/B6 honest zero-change precedent applies; per the task envelope, no changes are forced. All bars were re-verified live 2026-10-20, not assumed.

## Row-by-row diff (#14 rows 22–27 vs in-tree state)

| #14 item | In-tree state | Decision |
|---|---|---|
| Row 22 `engine-systems-eng`: `pi-fff@0.11.0` (Pi ext col) | Exists on npm (`@ff-labs/pi-fff`: `0.11.0` present, `latest` = `0.11.0` — verified 2026-10-20) | DEFERRED — pi-extensions follow-up batch (B1/B4 precedent). Seat carries `@gotgenes/pi-permission-system@41.0.0` + `pi-lsp-extension@1.4.0` + `pi-ast-grep@0.1.0` today |
| Row 22: `Docker catalog` (MCP col) | Catalog `dropped.docker` is explicit: "`docker-mcp==0.2.0` (last release 2024-12) gave daemon-level access; mlops/k8s seats use explicit bash allows instead" (re-confirmed in-tree) | REFUSED — granting Docker execution (MCP or bash allow) to engine seats widens execution capability. Same bar as B3's red-seat Docker refusal, applied to all execution grants per the slice envelope. Seat's scoped allows (`cargo bench/test engine*`, `cmake --build*`, `ctest*`) already cover its build remit |
| Row 22: `VoltAgent list` (skill col) | No bindable distribution: `@voltagent/mcp` → 404, `voltagent-mcp` → 404 on npm (re-verified 2026-10-20). `voltagent/*` packages are a TS agent framework (core/SDK/CLI/memory providers) — no MCP server or skill surface to bind | NOTHING TO ADD — informational/deferred. No MCP/skill ID exists at any pin |
| Row 22: Bevy MIT+Apache (OSS col) | Engine crate set; no fleet mechanism pins seat-executed crate versions (`sidecar_profiles` are labels; `bash_allow` is a capability grant, not a version pin, and this batch grants no new execution) | INFORMATIONAL — no action |
| Row 23 `physics-sim-eng`: `pi-subagents` | Rejected second delegation path | EXCLUDED — verify gate HR-6.2 rejects `pi-subagents` (`scripts/verify-rigs.sh:1074-1091`, re-confirmed in-tree; B1/B2/B3/B4/B5/B6 same verdict) |
| Row 23: `Docker` (MCP col) | As row 22 (`dropped.docker`) | REFUSED — same execution-widening bar. Seat's scoped allows (`cargo test physics*`, `ctest -R physics*`) already cover its remit |
| Row 23: `VoltAgent` | As row 22: no MCP/skill distribution at any pin | NOTHING TO ADD — informational/deferred |
| Row 23: Rapier MIT/Apache (OSS col) | Physics crate; no version-pin mechanism | INFORMATIONAL — no action |
| Row 24 `graphics-shader-eng`: `pi-lens` | Exists on npm (`latest` = `4.4.4` — verified 2026-10-20) | DEFERRED — extensions batch |
| Row 24: `Docker` | As row 22 | REFUSED — same bar. Seat's scoped allows (`glslangValidator*`, `naga*`, `spirv-val*`, `cargo test rendering*`) already cover shader validation |
| Row 24: `superpowers` | Seat binds **no** shared skills; #14 names `superpowers` generically (no skill ID). Vendored `obra/superpowers@bb92a77` exposes only process skills (`brainstorming`, `systematic-debugging`, `test-driven-development`, `executing-plans`, `writing-plans`, review/worktree skills…) — none is graphics/shader-fitting. Unlike B4's `exec-director`/`tpm-scrum-lead` additions, no charter-fitting skill exists to bind | NO ACTION — generic label, no fitting vendored skill (B1/B2 ill-fitting bar) |
| Row 24: wgpu MIT/Apache + glTF-Transform (OSS col) | No version-pin mechanism. Shader-validation tooling already allowed on-seat; adding `gltf-transform*` here would be a new execution grant to a seat whose remit is shaders/rendering (asset-pipeline transformation belongs to `tech-artist-pipeline`, which already carries it) | INFORMATIONAL / NO ACTION — no new execution grant in a minimal batch (B4 Syft / B3 Gitleaks same bar) |
| Row 25 `game-systems-dev`: `@ff-labs/pi-fff@0.11.0` | As row 22 (verified exists) | DEFERRED — extensions batch |
| Row 25: `Docker` | As row 22 | REFUSED — same bar. Seat's scoped allows (`cargo/npm/pytest test game*`) cover its remit |
| Row 25: `superpowers:game` | **No such skill exists**: vendored lock carries 13 superpowers skills (none game-named); upstream pinned checkout (15 skills: the 13 vendored + `diagnosing-superpowers` + `writing-skills`) contains nothing game-related — verified against the checkout, not assumed | NO ACTION — #14 names a skill ID that exists neither vendored nor upstream |
| Row 25: Godot 4.6.3 MIT (OSS col) | #14's own maintenance notes flag Godot 4.6.3 as stale (May 2026 — "re-check quarterly"); engine binary, no fleet version-pin mechanism | INFORMATIONAL — no action |
| Row 26 `game-ai-dev`: `pi-fff` | As row 22 (verified exists) | DEFERRED — extensions batch |
| Row 26: `GCP Vertex` (MCP col) | Console-managed, no MCP/pin in #14 | NOTHING TO ADD (B1 rows-28/29/34/35/37 + B3 row-49 same verdict) |
| Row 26: `anthropics/skills` | Vendored `anthropics/skills@dbd4588` exposes `doc-coauthoring`, `frontend-design`, `webapp-testing` — none fits a game-AI (behavior-tree/steering) charter | NO ACTION — ill-fitting (B4 row-3 same bar) |
| Row 26: Bevy + Ollama v0.40.6 MIT (OSS col) | No version-pin mechanism for crates or model-server binaries | INFORMATIONAL — no action |
| Row 27 `tech-artist-pipeline`: `pi-mcp-adapter@5.4.0` | Exists on npm (`latest` = `5.4.0` — verified 2026-10-20) | DEFERRED — extensions batch |
| Row 27: `Figma` (MCP col) | No `figma` server in catalog; #14 directs to the official remote (OAuth, no pin); `@figma/mcp` → 404 (re-verified 2026-10-20); npm `figma-mcp@0.1.4` exists but is a stale (2025-05) third-party package of unknown provenance, not the official remote | EXCLUDED — remote-OAuth surface + no-pin-no-add (B4 rows-2/12 same verdict, re-verified) |
| Row 27: `Docker` (MCP col) | As row 22 | REFUSED — same bar. Seat's scoped allows (`gltf-transform*`, `node tools/asset-pipeline/*`) already cover the asset pipeline |
| Row 27: `vercel-labs` MIT | Vendored `vercel-labs/agent-skills@063bee9` exposes only `react-best-practices` + `web-design-guidelines`; neither fits an asset-pipeline charter | NO ACTION — ill-fitting (B4 row-2 same bar) |
| Row 27: glTF-Transform MIT (OSS col) | Seat **already** carries `gltf-transform*` in `bash_allow`; no fleet mechanism pins the CLI version | ALREADY PRESENT (tooling) + INFORMATIONAL (pin) — no action |

## Considered and rejected (not #14-traceable — recorded so a follow-up does not re-litigate)

- **Binding a process skill (`systematic-debugging`, `test-driven-development`) to an engine seat on the B4 fitting argument:** B4's additions succeeded because #14 named the exact skill AND the charter (executive discovery, delivery triage) fit. Here #14 names only generic `superpowers` (row 24) or a nonexistent `superpowers:game` (row 25) — no #14-named, charter-fitting skill exists for any Rig-4 seat. Adding process skills without a #14 mandate would be scope expansion, not minimal-batch adoption. NO ACTION.

## What was added

None. Zero catalog, script, or seat-content change. The regen diff is 16 registry files of pure provenance relag (`resolvedCommit` `e8577db` → `88c13d7`, the known per-merge convention) plus this ledger — the B2/B3/B5/B6 zero-change shape.

## Deferred with named blockers (not started here)

- **Pi-extension batch** (all #14 pins in rows 22–27: `@ff-labs/pi-fff@0.11.0`, `pi-lens@4.4.4`, `pi-mcp-adapter@5.4.0` — every pin verified to exist on npm 2026-10-20): NOT adopted here — B2/B3/B4/B5/B6 deferred a dedicated per-seat extension batch, and B7 must coordinate by not duplicating it.
- **VoltAgent / Figma / GCP Vertex / Docker surfaces:** no bindable distribution (VoltAgent), remote-OAuth surface with no pin (Figma), console-managed with no MCP/pin (Vertex), catalog-dropped daemon access (Docker). Revisit only with a stated pin + compatible auth model + live verification.
- **OSS pins** (Bevy, Rapier, wgpu, glTF-Transform, Godot 4.6.3, Ollama v0.40.6): no fleet mechanism pins them (`sidecar_profiles` are labels; `bash_allow` is a capability grant, not a version pin, and this batch grants no new execution). Recorded informational. Freshness note: #14 itself flags Godot 4.6.3 as stale (May 2026); re-check at PR merge time per program plan §4.

## Regen + verify evidence

- Tracked tree was clean at start (`git status` empty on `feat/self-rig4-tooling` @ `88c13d7`); regen ran **without** `ALLOW_DIRTY` (no stated reason needed).
- Generator: `python3 ./scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor --crew-source <heretek-crew-checkout>` → "wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles…". Vendor SHAs matched pins (`bb92a77`, `5c99c03`, `f57ada2`, `dbd4588`, `063bee9`). No new vendor sources introduced. (Placeholders used for machine-local paths.)
- Regen diff: **16 files, +24/−24** — registry entries + views only; every hunk is the `resolvedCommit` relag (`e8577db` → `88c13d7`) plus matching `canonicalUrl` commit pins. Zero hand-edits to generated leaves; `fleet/` and `scripts/` untouched.
- `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 22 checks passed, 0 failed**, incl. "All 20 MCP servers … verified (pinned, command-backed secrets)".
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `git status`: the 16 relag files above + this ledger. No A-slice or B1–B6 files touched; no secrets/values; no machine-local paths in this ledger (placeholders only).

## Deferred live proof (fleet down)

Not run: `seed-rig.py` for `game-dev-and-sim-rig`, any skill/MCP smoke beyond dry verification. Nothing to smoke — zero content change. Required before merge: freshness re-check of the deferred extension pins (pins rot; today's `latest` values are dated in this ledger for that purpose).
