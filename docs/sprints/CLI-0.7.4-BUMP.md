# Slice CLI-3 — OpenRig CLI 0.7.2 → 0.7.4

- **Date:** 2026-10-27
- **Branch:** `feat/overhaul-bump` (from clean `main` `88cd930`)
- **Scope:** host toolchain pin + operator-doc pins + this ledger. No generator-input change, no contract sync, no regen. Pi stays at 1.4.0 and pi-permission-system at 41.0.0.
- **Authority:** overhaul-bump proposal/design (pin 0.7.4 with ledger; contract sync explicitly Wave B).
- **Precedent:** `docs/sprints/CLI-0.7.2-BUMP.md` (same recipe, split into two waves this time).

## 1. Version facts (checked 2026-10-27)

| Item | Value |
|---|---|
| npm `latest` | `0.7.4`, published 2026-10-27 (0.7.3 in between, 2026-10-26) |
| Installed binary stamp | `rig --version` → `0.7.4 (6d9e8e27)` (global install, `/home/john/.npm-global/bin/rig`) |
| Tarball | `npm pack @openrig/cli@0.7.4` sha256 `d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1` (independent re-pack; matches the design-doc value) |
| Engines | `node >=22`, unchanged for this fleet |
| Daemon DB | Scratch daemon (`--port 18433 --host 127.0.0.1 --no-kernel`, isolated `OPENRIG_HOME`) started clean on a fresh DB. No migration range recorded here — the real-state daemon was never touched. |

## 2. What changes for this fleet

0.7.2 → 0.7.4 tarball diff (read-only, `/tmp` scratch extracts):

| Upstream change | Fleet impact |
|---|---|
| RigSpec `MEMBER_KEYS` gains exactly one key: `codex_permissions` (9 `codex_permissions` refs in `daemon/dist/domain/rigspec-schema.js`, 0 in 0.7.2). No RIG/POD/EDGE key or edge-kind change. | **Deferred to Wave B (out of scope).** Pinned schema copies, `verify-rigs.sh` key sets, `skills-lock.json`, and all generated leaves stay 0.7.2-derived. Our specs use none of the new keys. |
| 3 of 18 `openrig-core` skill bodies changed (`claude-compaction-restore`: session-file naming prose; `messaging-the-human`: `rig gateway participants` + channel-policy guidance; `queue-handoff`: receiver-actionable writing guidance). Skill directory set identical (18/18). 5 skill bodies reference `codex`. | **Deferred to Wave B (out of scope).** No re-vendor, no regen in this wave. |
| `rig mcp serve --http` bearer-grant behavior unchanged in the probed forms: valid Bearer → 200, bad token → 401 with the exact 0.7.2 message (`This credential isn't valid here: it's unknown or was revoked.`), missing credential → 401. `token add`/`token list`/`token revoke` surface unchanged (`--seat/--rig/--root/--workspace/--owner` flags identical). | 107-identity M0 probe forms re-run green on 0.7.4 in scratch env (see §5). No issuance redesign. |
| `rig_whoami` response shape delta: for an unmanaged seat, 0.7.2 returned the daemon 404 error text (`isError:true`); 0.7.4 returns `ok:true` with `caller:{authenticated:true, principal:<grant>}` and message `This seat has no session here: it's the seat this connection's grant names…`. Identity signal (grant's seat) identical; envelope changed. | Recorded, not acted on. 107-identity follow-ups (not this wave) own any caller-side parsing impact. |

## 3. Repo changes

| File | Change |
|---|---|
| Host toolchain | `npm install -g @openrig/cli@0.7.4`; `rig --version` → `0.7.4 (6d9e8e27)`. |
| `AGENTS.md`, `README.md` (stack table + prereqs/install), `Makefile` (target framework), `docs/USER_GUIDE.md` (§1 toolchain + Docker `:latest` table), `docs/TECHNICAL_DOCUMENTATION.md` (target framework + commit), `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` (stack definition, baseline tool, real-thing rule, Alpha focus, §2 validation heading) | Toolchain assertions 0.7.2 (`8b180689`) → 0.7.4 (`6d9e8e27`). |
| `docker/Dockerfile` + V13 check in `scripts/verify-rigs.sh` | `ARG OPENRIG_VERSION=0.7.2` → `0.7.4` (paired; V13 stays green). |
| `scripts/verify-rigs.sh` V18 info line | Status message `installed 0.7.2` → `installed 0.7.4` (no gate logic touched). |

Intentionally NOT changed (all deferred to Wave B contract sync or owned by dated records):

- `scripts/generate-rigs.py` (`OPENRIG_VERSION`/`OPENRIG_COMMIT` still 0.7.2/`8b180689`) — a generator input; changing it would force a regen that re-vendors 0.7.4 skills/schema (Wave B). Hence **no generator input changed → no regen** (leaves stay dirty-free).
- `fleet/fleet.yaml` header comment, `fleet/mcp-servers.yaml` (`builtin:rig-mcp-serve-http@0.7.2`) — generator inputs; same reason.
- `schemas/rigspec-schema.pinned.ts`, `schemas/rigspec-keys.pinned.json`, `schemas/contract-schemas.sha256`, `verify-rigs.sh` key-set/provenance strings — provenance of still-0.7.2 bytes; editing provenance without re-vendoring would be a lie.
- Generated leaves (`registry/*`, `rigs/*/bundle.yaml`, `rigs/*/SETUP.md`, `fleet/skills-lock.json`) — one-rule: generator only.
- Dated records (`docs/sprints/CLI-0.7.2-BUMP.md`, `PI-1.4.0-BUMP.md`, `HANDOFF.md`, `docs/evidence/*`, `docs/reports/*`, `openspec/changes/107-identity/*`, this change's own proposal/design/tasks) — history is never rewritten.
- Vendored-byte descriptions: `USER_GUIDE.md` vendor-checkout line, `TECHNICAL_DOCUMENTATION.md` source-verified prose + skills-source table, `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` skills-lock pin list — still true (bytes are 0.7.2 until Wave B re-vendors).

## 4. Verification (this host, 2026-10-27)

- `rig --version` → `0.7.4 (6d9e8e27)`.
- `./scripts/verify-rigs.sh --check-only` → **35 checks passed, 0 failed** (SUMMARY frozen; V13 green on `ARG OPENRIG_VERSION=0.7.4`; no V1–V24 renames).
- `make verify` → exit 0 (35/0 + live-health SKIP lines: real daemon stale/not running, untouched by design).
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `make test` → full suite result recorded in the wave implementation report (`docs/reports/overhaul-bump-implementation.md`).
- Idempotent-regen note: `--check-idempotent` was NOT run — it regenerates into `--root` using the default `openrig-core` resolver, which now points at the installed 0.7.4 skills, so running it would vendor Wave B content into the tree. No generator input changed, so no regen was owed. Wave B re-runs it after the generator bump.
- 107-identity M0 probe forms on 0.7.4 (isolated `OPENRIG_HOME=/tmp/opencode/bump-m0-20261027-155536`, mode 700; scratch ports 18433/18437; real `~/.openrig/daemon.json` read before/after, byte-identical): `token add --help` surface identical; `token add probe-seat --seat spike-bump-seat` → once-printed token (redacted first/last-2 only: `or…2A`), sha256-only mode-600 store; grant `serve --http` → valid Bearer 200 (`serverInfo.version 0.7.4 (6d9e8e27)`), bad token 401, missing credential 401; `rig_whoami` envelope delta recorded in §2. Cleanup: serve killed, scratch daemon stopped, listeners gone, no `rig` procs remain, probe token file removed. Scratch DB/log files only under `/tmp` (never committed).

## 5. Not verified here (needs the fleet host / Wave B)

1. Constitution §2.7 pre-relaunch snapshot, then restart the real daemon on 0.7.4 (migrations, if any, are one-way — never run 0.7.4 against the pre-upgrade snapshot without a restore path).
2. `rig preflight`, `rig agent validate` (need the real daemon), then re-seed and relaunch one canary rig.
3. Wave B: generator bump (`OPENRIG_VERSION`/`OPENRIG_COMMIT` + tarball re-vendor), `MEMBER_KEYS` `codex_permissions` adoption decision, skill re-vendor review (3 changed bodies), then regen + idempotence + full gates.
4. Live checks carried over from 0.7.2: `send-authenticated.sh` relay receipt; `sweep-typed-blocks.py --dry-run`; `rig snapshot list <name>` (#80); operator `rig send` semantics (#9/#81).

## 6. Rollback

1. `rig daemon stop`, `npm i -g @openrig/cli@0.7.2`.
2. Restore the pre-upgrade daemon snapshot if 0.7.4 ran any one-way migration against real state (it did not in this wave — scratch DB only).
3. Revert this wave's doc/pin commits (no regen needed — no generator input changed, no leaf touched).
