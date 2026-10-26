# Slice CLI-2 — OpenRig CLI 0.6.13 → 0.7.2

- **Date:** 2026-10-26
- **Branch:** `claude/project-thread-502xnv` (stacked on PR #118)
- **Scope:** version pin, RigSpec key pins, provenance refresh, re-vendor of `openrig-core` skills. No charter, permission, seat-scope or MCP-catalog change. Pi stays at 1.3.0 and pi-permission-system at 41.0.0.
- **Authority:** human instruction "update to the most recent version of openrig" (2026-10-26).
- **Precedent:** `docs/sprints/CLI-0.6.13-BUMP.md` (same recipe).

## 1. Version facts (checked 2026-10-26)

| Item | Value |
|---|---|
| npm `latest` | `0.7.2`, published 2026-10-25 (0.6.14, 0.7.0 and 0.7.1 in between) |
| Upstream tag | `mvschwarz/openrig` `v0.7.2` = `8b180689` (208 commits after `v0.6.13` `9eeb2e42`) |
| Tarball | `npm pack @openrig/cli@0.7.2` sha256 `42b4d4980c062f49f99db7e843a2ba96c0066a420cbaace381f435e22699d4c5` |
| Engines | `node >=22`, unchanged in practice for this fleet |
| Daemon DB | migrations `118`–`139` (22, one-way) run on first daemon start |

## 2. What changes for this fleet

| Upstream change | Fleet impact |
|---|---|
| RigSpec `MEMBER_KEYS` gains `advisor`, `claude_permissions`, `agent_file`, `append_system_prompt_file`, `plugin_dirs` (the last four are Claude-only). RIG/POD/EDGE keys and edge kinds unchanged. | Pins updated in all three local copies. Our specs use none of them. |
| `queue update`: a done close with `closure_reason: blocked_on` is now rejected. Waiting on another qitem is `rig queue block <id> --on <child>` (state `blocked`). | No charter or script uses the old form (grep clean). The re-vendored `queue-handoff` skill teaches the new one. `sweep-typed-blocks.py` reads `state == blocked` + `blockedOn` and unparks with `update --state in-progress --reopen`; both still exist with the same typed `auth:`/`fold:`/`external:` blockers. |
| `queue create` receipt: same `qitemId`, `persisted: true`, `createWarning` shape (source-compared). `--source` still required outside a managed seat (both CLIs print the same refusal). | `send-authenticated.sh` unchanged in behaviour. |
| `rig send` from a shell that isn't a seat now arrives as `From: <unknown sender>`, and the help points to `rig queue create --source …` or `rig attach --self`. | Relevant to #9 and #81 (`From: operator`). Needs a live look. |
| `rig snapshot list`, `rig expand` take a rig **name or ID**; `rig up --name`. | Likely fixes #80; confirm live. |
| `rig down` asks for confirmation when the caller's own seat is in that rig (`--yes` to skip). | Operator runbooks run from outside seats; no change expected. |
| Typed gate blockers can be resolved with recorded evidence (`#1809`). | Overlaps the `auth:` unblock discipline in `sweep-typed-blocks.py` (#83). Worth adopting later; not done here. |
| `rig mcp serve --http` with per-seat bearer-token grants (`#1860`). | The per-seat identity primitive #107's F9 box waits for, for the MCP path only. |

## 3. Re-vendored `openrig-core` skills (12 bound; content changed in 6)

| Skill | Lines (+/−) |
|---|---|
| `openrig-user` | +287 / −67 |
| `messaging-the-human` | +43 / −4 |
| `refocusing` (incl. `scripts/trace-to-root.py`) | +12 / −32 |
| `forming-an-openrig-mental-model` | +16 / −10 |
| `queue-handoff` | +10 / −4 (the `blocked_on` change above) |
| `delegating-work` | +1 / −1 |

The 0.7.2 plugin still ships the seven unbound skills listed in the 0.6.13 ledger. Binding any of them is a catalog change, outside this slice.

## 4. Repo changes

| File | Change |
|---|---|
| `scripts/generate-rigs.py` | `OPENRIG_VERSION` 0.7.2, `OPENRIG_COMMIT` 8b180689; the vendored-tarball path now follows `OPENRIG_VERSION`. |
| `schemas/rigspec-schema.pinned.ts`, `schemas/rigspec-keys.pinned.json`, `scripts/verify-rigs.sh` | The five new member keys; provenance package/commit/tarball sha. |
| `docker/Dockerfile` + V13/#100 | `ARG OPENRIG_VERSION=0.7.2`. |
| `schemas/contract-schemas.sha256` | Header corrected: the tarball does ship `*.v1.schema.json` under `daemon/docs/reference/schemas/` (#98 reopened). |
| Current-state docs | `AGENTS.md`, `README.md`, `Makefile`, `docs/USER_GUIDE.md`, `docs/TECHNICAL_DOCUMENTATION.md`, `fleet/fleet.yaml` header, `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`. |
| Generated (regen only) | 6 skill bodies, `fleet/skills-lock.json`, registry `openrigVersion`/`minCliVersion`/`minDaemonVersion`/digests, `resolvedCommit`. |

Not rewritten: dated audit and planning records (`docs/sprints/CLI-0.6.13-BUMP.md`, `SEAT-REFRESH-RUNBOOK.md`'s verified-at-0.6.13 notes, `docs/NOTES.md`, handoffs, openspec changes).

## 5. Verification (cloud container)

- Regen used every catalog pin checked out at its sha and the 0.7.2 tarball's `openrig-core`. Before bumping, the same setup reproduced main byte-for-byte except the accepted `resolvedCommit` re-lag. `--check-idempotent` passes.
- `rig --version` → `0.7.2 (8b180689)` (local install).
- `./scripts/verify-rigs.sh --check-only` with that `rig` on PATH → **35 checks passed, 0 failed**. V18 ran the native verbs instead of noting them unchecked.
- `rig spec validate --json` on all 8 `rig.yaml` + `rig.all-51.yaml` → valid, 0 errors, 0 advisories (no session-name collisions). `rig bundle check --json` on all 8 → 0 fails (only the always-`not_checked` README and secrets rules).
- `make test` → 347 tests OK (2 skipped: no `pi`). `audit_loop.py --self-test` → passed.

## 6. Not verified here (needs the fleet host)

1. Take the Constitution §2.7 pre-relaunch snapshot, then `npm i -g @openrig/cli@0.7.2` and restart the daemon. Migrations 118–139 are one-way.
2. `rig preflight`, `rig agent validate` (needs the daemon), then re-seed and relaunch one canary rig.
3. Live checks: a `send-authenticated.sh` relay receipt; `sweep-typed-blocks.py --dry-run` against real blocked rows; `rig snapshot list <name>` (#80); what a seat sees for an operator `rig send` (#9/#81).
4. `make test` with `pi` installed (the canary mock probes).

## 7. Rollback

1. `rig daemon stop`, `npm i -g @openrig/cli@0.6.13`.
2. Restore the pre-upgrade daemon snapshot (the migrations are one-way; never run 0.6.13 against a migrated database).
3. Revert this slice's commits and re-run `generate-rigs.py`.
4. Re-seed seats, then `rig up`.
