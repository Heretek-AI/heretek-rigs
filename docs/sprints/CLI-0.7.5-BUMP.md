# Slice CLI-4 — OpenRig CLI 0.7.4 → 0.7.5

- **Date:** 2026-10-29
- **Branch:** `feat/bump-075` (from clean `main` `c1da1fb`)
- **Scope:** host toolchain pin + operator-doc pins + this ledger. No generator-input change, no contract sync, no regen, no new V-gate. Pi stays at 1.4.0 and pi-permission-system at 41.0.0.
- **Authority:** Wave 1 (`2026-10-29-bump-075`) of the five-wave remediation plan; Q9 default (no new V-gate).
- **Precedent:** `docs/sprints/CLI-0.7.4-BUMP.md` (same recipe).

## 1. Version facts (checked 2026-10-29, live)

| Item | Value |
|---|---|
| npm `latest` | `0.7.5`, published 2026-10-29T07:36:19Z (`time['0.7.5'] = '2026-10-29T07:36:19.571Z'`, registry `modified` `2026-10-29T07:36:19.834Z`) |
| Upstream tag | `v0.7.5`: tag object `e9b05fda…`, peeled commit `b57c4da3c3ac3fb420a09e5a169d3e85f9529e93` (via `git ls-remote`; npm metadata carries no `gitHead` — `dist.shasum 00ef5b67…` is the tarball sha1, not a commit) |
| Installed binary stamp | `rig --version` → `0.7.5 (b57c4da3)` (global install, `~/.npm-global/bin/rig`) |
| Tarball | `npm pack @openrig/cli@0.7.5` sha256 `22d67c2c7e0d0ab4a5ec9faac0a725d54f9ead2c0f71564985cf4ae240bb9754` (TWO independent fetches into separate scratch dirs, byte-identical; control re-fetch of 0.7.4 reproduces the 0.7.4-ledger value `d11dd8a6…`) |
| Engines | `node >=22`, unchanged for this fleet |
| Daemon DB | Scratch-only wave. The real-state daemon was never touched. Upstream ships a NEW one-way migration 126 (`escalation_target_refs`) — never run 0.7.5 against the pre-upgrade snapshot without a restore path (see §5). |

## 2. What changes for this fleet

0.7.4 → 0.7.5 tarball diff (read-only, `/tmp` scratch extracts):

| Upstream change | Fleet impact |
|---|---|
| RigSpec `MEMBER_KEYS` permission sets IDENTICAL (`codex_permissions` ×13 both sides). `rigspec-schema.js` gains only additive `escalates_to` + `isEscalationTargetRef` edge tolerance (deferred same-daemon cross-rig escalation routing). | **No generator-input change.** Pinned key sets, `verify-rigs.sh` key gates, `schemas/rigspec-keys.pinned.json`, and all generated leaves stay 0.7.4-derived and correct. Our specs use none of the new edges. |
| `run-record.v1.schema.json` byte-IDENTICAL (vendored digest `b3c7ac64…` still holds); all five bundle/registry schemas byte-IDENTICAL; installed 0.7.5 copies equal the tarball copies. | **No re-vendor.** V18 byte-comparisons stay green against the installed CLI. |
| 19/19 `openrig-core` skill dirs identical set; only `queue-handoff/SKILL.md` gains parking prose (`rig queue block <id> --on external:<what> --wake-after <duration> --continuation "…"`). openrig-core 0.1.21→0.1.22 (plugin.json version bumps only). | **Deferred (out of scope).** Vendored-via-generator content; same deferral rule as the 0.7.4 wave's 3 skill bodies. A future contract-sync wave owns the re-vendor + regen. |
| Daemon behavior notes (upstream `whats-new`, recorded not acted on): `rig send` waits 60s for its result; runtime send refusals return 409 instead of 500 (stale Claude pane names `rig reconcile-session`); `rig down` records an explicit stop after rolled-back launch; terminal follow mode (Linux Herdr 0.9.5 only); `attach --self` tmux separator handling; scope-audit route accepts slice folders ≥100. | None touch our gates. Bearer-grant framing unchanged ("a recorded principal is attribution, not authentication"). #2200 Codex restart refusal still NOT fixed in 0.7.5 (upstream note). |
| Grant/rotation/sandbox/daemon-label surface, snapshot rendering (#80), queue-auth (#107-M3), restart semantics (#11): no issuance-redesign or flag-surface change in the probed paths. | No follow-up owned by this wave. |

## 3. Repo changes

| File | Change |
|---|---|
| Host toolchain | `npm install -g @openrig/cli@0.7.5`; `rig --version` → `0.7.5 (b57c4da3)`. |
| `AGENTS.md` (surgical: `git diff --stat` ≤15 lines) | Stack line `0.7.4`→`0.7.5` + tarball sha ref + docs-map row for this wave + ledger path. One Rule / secrets / git conventions verbatim. |
| `README.md` (stack table + prereqs/install), `Makefile` (target framework), `docs/USER_GUIDE.md` (§1 toolchain + `rig --version` expect + Docker `:latest` table), `docs/TECHNICAL_DOCUMENTATION.md` (target framework + commit `b57c4da3`), `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` (stack definition, baseline tool, real-thing rule, Alpha focus, §2 validation heading) | Toolchain assertions 0.7.4 (`6d9e8e27`) → 0.7.5 (`b57c4da3`). |
| `docker/Dockerfile` + V13 check in `scripts/verify-rigs.sh` | `ARG OPENRIG_VERSION=0.7.4` → `0.7.5` (paired; V13 stays green). |
| `scripts/verify-rigs.sh` V18 fail-closed gate | Expected version `0.7.4` → `0.7.5` (comment + check + fail message + ok line; no gate logic touched, no new gate). |

Intentionally NOT changed (all deferred to a contract-sync wave or owned by dated records):

- `scripts/generate-rigs.py` (`OPENRIG_VERSION`/`OPENRIG_COMMIT` still 0.7.4/`6d9e8e27`) — a generator input; changing it would force a regen that re-vendors 0.7.5 skills/schema. Hence **no generator input changed → no regen** (leaves stay dirty-free; `--check-idempotent` exit 0).
- `fleet/fleet.yaml` header comment, `fleet/mcp-servers.yaml` (`builtin:rig-mcp-serve-http@0.7.2`) — generator inputs; same reason. (Never `yaml.safe_dump` on fleet.yaml regardless.)
- `schemas/rigspec-schema.pinned.ts`, `schemas/rigspec-keys.pinned.json`, `schemas/contract-schemas.sha256`, `verify-rigs.sh` key-set/provenance strings — provenance of still-0.7.4 bytes; editing provenance without re-vendoring would be a lie (disposition table proves no re-vendor is owed).
- Generated leaves (`registry/*`, `rigs/*/bundle.yaml`, `rigs/*/SETUP.md`, `fleet/skills-lock.json`) — one-rule: generator only.
- Dated records (`docs/sprints/CLI-0.7.4-BUMP.md`, `HANDOFF.md`, `docs/evidence/*`, `docs/reports/*`, `openspec/changes/archive/*`, this change's own proposal/design/tasks) — history is never rewritten.
- `docs/IMPLEMENTATION_PROMPT.md` stack line (still 0.7.4) — not one of the 8 true-pin files (same as the 0.7.4 wave, which did not own it either); V19 scans it for no version string.
- Vendored-byte descriptions: `USER_GUIDE.md` vendor-checkout line, `TECHNICAL_DOCUMENTATION.md` source-verified prose + skills-source table, `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` skills-lock pin list — still true (bytes are 0.7.4 until a contract-sync re-vendors).

## 4. Verification (this host, 2026-10-29)

- `rig --version` → `0.7.5 (b57c4da3)`.
- `./scripts/verify-rigs.sh --check-only` → **39 checks passed, 0 failed** (SUMMARY frozen; V13 green on `ARG OPENRIG_VERSION=0.7.5`; V18 green on installed 0.7.5 with byte-identical schema comparisons + `bundle check`/`spec validate` clean; no V1–V31 renames).
- `make test` → full suite result recorded in the wave implementation report (`docs/reports/bump-075-implementation.md`).
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `python3 scripts/generate-rigs.py --check-idempotent` → exit 0 byte-identical (no generator input changed, so no regen was owed).
- Red-proof: V18 expected-version pin sabotaged back to `0.7.4` → gate RED (38 passed, 1 failed); restored to `0.7.5` → GREEN (39/0). Commands + outputs in the implementation report.
- `openspec validate 2026-10-29-bump-075` → exit 0.
- `git diff --stat AGENTS.md` → ≤15 lines.

## 5. Not verified here (needs the fleet host / a contract-sync wave)

1. Constitution §2.7 pre-relaunch snapshot, then restart the real daemon on 0.7.5 (**migration 126 is new and one-way** — never run 0.7.5 against the pre-upgrade snapshot without a restore path).
2. `rig preflight`, `rig agent validate` (need the real daemon), then re-seed and relaunch one canary rig.
3. Contract-sync wave: generator bump (`OPENRIG_VERSION`/`OPENRIG_COMMIT` + tarball re-vendor), `escalates_to` edge-kind adoption decision, `queue-handoff` parking-prose re-vendor review (1 changed body), then regen + idempotence + full gates.
4. Live checks carried over: `send-authenticated.sh` relay receipt; `sweep-typed-blocks.py --dry-run`; `rig snapshot list <name>` (#80); operator `rig send` semantics (#9/#81); `rig send` 60s-wait behavior note.

## 6. Rollback

1. `rig daemon stop`, `npm i -g @openrig/cli@0.7.4`.
2. Restore the pre-upgrade daemon snapshot if 0.7.5 ran any one-way migration against real state (it did not in this wave — scratch evidence only, real daemon untouched).
3. Revert this wave's doc/pin commits (no regen needed — no generator input changed, no leaf touched).
