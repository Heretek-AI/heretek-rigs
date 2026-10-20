# Slice CLI-1 — OpenRig CLI 0.6.11 → 0.6.13

- **Date:** 2026-10-20
- **Branch:** `feat/self-cli-0.6.13`
- **Scope:** version pin + provenance refresh + re-vendor of `openrig-core` skills. No charter, permission, seat-scope, or MCP-catalog change.
- **Authority:** human instruction "CLI version slice (0.6.11→0.6.13)" as action 2 of the four-action sequence.

## 1. What the upgrade changes upstream

0.6.12 (206 changes, 12 DB migrations on first start) and 0.6.13 (46 changes, 1 Codex-only migration).

Operationally relevant to this fleet:

| Upstream behaviour | Fleet impact |
|---|---|
| **Seat permission policy changeable in place** (0.6.12) | Directly relevant to issue #11 (single-node policy refresh). The repo-side fallback runbook (`docs/sprints/SEAT-REFRESH-RUNBOOK.md`) must be re-evaluated against this verb on first live use. |
| **Pi seats honour `effort`** as `--thinking <level>` (0.6.13) | Our specs pin `opencode-go/muse-spark-1.3-contributor:high`; effort now reaches Pi from each seat's next managed launch, restore or handover. A seat running from before the upgrade does not pick it up until relaunch. |
| **Shipped agent specs mark the role file** (0.6.13) | `rig queue whoami --json` reports the role instead of `not-declared` after a fresh launch. |
| **Rig names with `.` refused** | None of our 8 rig ids contain a dot. |
| **Daemon restart required after upgrade** | Fleet is down; the daemon will be started fresh in the re-seed/relaunch phase. Migrations run on that first start. |
| Bundled `openrig-core` plugin 0.1.13 → 0.1.14 | Re-vendored below. |

## 2. Repo changes

| File | Change |
|---|---|
| `scripts/generate-rigs.py` | `OPENRIG_VERSION` 0.6.11→0.6.13, `OPENRIG_COMMIT` 379f0a0d→9eeb2e42; the skills-lock source string is now built from `OPENRIG_VERSION` instead of a second hardcoded literal (removes a future drift source). |
| `schemas/rigspec-schema.pinned.ts` | Header/provenance text only — key allowlists (`RIG_KEYS`, `POD_KEYS`, `MEMBER_KEYS`, `EDGE_KEYS`, `EDGE_KINDS`) diffed against upstream `v0.6.13` `packages/daemon/src/domain/rigspec-schema.ts`: **identical, no key drift**. |
| `schemas/rigspec-keys.pinned.json` | `package`/`commit` updated; `vendored_sha256` refreshed to the vendored bytes; `upstream_tarball.tarball_sha256` recorded from `npm pack @openrig/cli@0.6.13` → `e174be6e97617e03a50728549a2f505c5e8b129ed5b103fc32e9554792dd4f6c`. |
| `scripts/verify-rigs.sh` | Comments only (pin source 0.6.13). Gate logic untouched. |
| Current-state docs | `AGENTS.md`, `README.md`, `Makefile`, `docs/USER_GUIDE.md`, `docs/TECHNICAL_DOCUMENTATION.md`, `fleet/fleet.yaml` header, `docs/sprints/SEAT-REFRESH-RUNBOOK.md`. |
| Generated (regen only) | 8 `openrig-core` skill bodies re-vendored, `fleet/skills-lock.json` (sources + 8 tree hashes), registry views/entries/status (`openrigVersion`, `minCliVersion`, `minDaemonVersion`, digests). |

**Deliberately NOT rewritten:** `AUDIT_REPORT_FINDINGS.md`, `REMEDIATION_LOG.md`, `docs/NOTES.md`, `PROMPT_*.md`, `docs/OSINT_ECOSYSTEM_REPORT.md`, `docs/OPENRIG_MUSE_GO_ARCHITECTURE.md`, `docs/PROMPT_REVIEW_*.md`, `claude/`, `gemini/`. These are dated audit/planning artefacts — append-only history per AGENTS.md.

## 3. Re-vendored `openrig-core` skills (12 bound; content changed in 8)

| Skill | Changed lines | Notable |
|---|---|---|
| `openrig-user` | 184 | largest upstream rewrite |
| `refocusing` | 78 | includes `scripts/trace-to-root.py` update |
| `delegating-work` | 31 | adds "check what kind of agent you're handing it to" (model-aware briefing) |
| `session-compaction-and-restore` | 20 | |
| `mission-slice-sop` | 17 | |
| `orienting-to-an-inherited-seat` | 12 | |
| `queue-handoff` | 9 | adds `--summary` on every queue row; `handoff-and-complete` as the successor-recording path |
| `forming-an-openrig-mental-model` | 7 | |
| 4 others | 0 (LICENSE-only diff) | unchanged upstream content |

`delegating-work` and `queue-handoff` changes are operationally relevant: the fleet already adopted queue-authenticated relay and handoff discipline, and these now match upstream vocabulary.

## 4. Seven new upstream skills — NOT bound (follow-up decision)

0.6.13 ships 19 `openrig-core` skills; the catalog binds 12. New upstream skills:

`agent-operated-software`, `applying-a-permission-policy`, `claude-compaction-restore`, `loading-addressable-markdown`, `openrig-skills`, `retiring-and-inheriting-a-seat`, `software-for-agents`.

`applying-a-permission-policy` and `retiring-and-inheriting-a-seat` are candidates for the next catalog slice (the first is directly relevant to #11/#12). Binding them is a **charter change** (catalog edit → regen → re-seed → relaunch) and is deliberately out of this version-bump envelope.

## 5. Verification

- `./scripts/verify-rigs.sh --check-only` from the worktree: **22 checks passed, 0 failed** (21 MCP servers, JCS digests, 64 skills, 7/7 seat-render tests).
- Schema key-set diff vs upstream `v0.6.13`: identical.
- `rig --version` on the host: `0.6.13 (9eeb2e42)`; `npm pack` tarball sha recorded above.
- Regen ran with `HERETEK_RIGS_ALLOW_DIRTY=1` — stated reason: the slice's own catalog/doc edits must be present before the generator can bake provenance. No hand-edits to generated leaves.

## 6. Rollback

1. `npm i -g @openrig/cli@0.6.11` (host), `rig daemon stop`.
2. Revert this PR's commit on `main`.
3. Re-run `generate-rigs.py` (restores 0.6.11 skill bodies + lock sources + hashes).
4. Re-seed seats, then `rig up`.

The schema pin rollback is covered by the same regen; the tarball record returns to the 0.6.11 digest via the revert.

**Daemon database:** 0.6.12's 12 migrations and 0.6.13's migration `117` are one-way. The daemon has not yet run 0.6.13 on this host (no irreversible state exists today), and the **pre-relaunch snapshot mandated by Constitution §2.7 is the rollback mechanism** for that database. A post-migration downgrade to 0.6.11 is untested and must not be attempted without restoring that snapshot first.

## 7. Known caveats

- The npm postinstall (`check-abi.mjs`, better-sqlite3 ABI check) was **not executed** because the host's npm `allowScripts` policy blocks it. The daemon start in the relaunch phase is the ABI proof; if it fails, reinstall with `--allow-scripts=@openrig/cli`.
- `min_cli_version`/`min_daemon_version` in generated bundles is now `0.6.13`; a host still on 0.6.11 will fail closed at launch — intentional.
- Freshness: this ledger is dated 2026-10-20. Re-check `npm view @openrig/cli version` at merge time.
