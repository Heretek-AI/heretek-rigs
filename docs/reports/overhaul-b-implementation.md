# overhaul-b M4→M5 implementation report (agency-programmer)

- Stage/wave: overhaul-b M4 (contract sync + regen) → M5 (test wiring + canary + V19)
- Worktree: `.lane/trees/overhaul-b`, branch `feat/overhaul-b` (from main `264135e`)
- Author: agency-programmer subagent (Muse Spark 1.3 Contributor)
- Date (UTC): 2026-10-28
- Commit: **none** — tree left dirty for coordinator commit (sources-only + tests + spec; NO regenerated leaves, per brief)

## TL;DR

- M4: `codex_permissions` in pinned keys + verify gate (right after `claude_permissions`); `run-record.v1.schema.json` vendored byte-identical from the published 0.7.4 tarball + pin entry + contract-test coverage (10 tests green); `messaging-the-human` + `queue-handoff` SKILL.md synced from installed 0.7.4 (= tarball bytes) via the generator path; DEV regen + idempotence green; leaves reverted so the tree holds sources-only.
- M5: `make test` → `unittest discover` (504 tests, OK); canary reworked to post-#121 reality (triple-aware bound + committed fixture fallback, green via git AND fixture AND git-less simulation); V19 compares against frozen canonical total 35 (no cascade); V12 `HERETEK_ALLOW_NO_BWRAP=1` note-mode (proven both ways).
- Acceptance `make verify`: exit 0 — `SUMMARY: 35 checks passed, 0 failed` + `audit_loop --self-test` PASSED.

## M4 — contract sync + regen

### Tarball SHA re-verification (done live, this session)

- `sha256sum /tmp/bump-verify/openrig-cli-0.7.4.tgz` → `d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1` (matches design doc; tarball NOT re-pulled — present and hash-verified).
- Extracted to `/tmp/opencode/overhaul-b-tarball/` (scratch, uncommitted) and compared:
  - `run-record.v1.schema.json`: tarball == installed 0.7.4 == vendored copy, sha256 `b3c7ac64fd9dd51152888c99fdbcadd85cddebebb2d38253864bff054da3fde7` (matches spec REQ-B4).
  - All five existing schemas (`bundle-behaviour/common/configurations/status`, `registry-entry`): tarball == installed 0.7.4 == repo copies (0.7.2 bytes identical, no digest change).
  - `messaging-the-human/SKILL.md`, `queue-handoff/SKILL.md`: tarball == installed 0.7.4 (so the generator, which vendors openrig-core from the installed package, emits tarball-identical bytes).
- Upstream 0.7.4 `MEMBER_KEYS` extracted from installed `daemon/dist/domain/rigspec-schema.js` (`MEMBER_KEYS = new Set([...])`): pinned list + exactly `codex_permissions` after `claude_permissions`, nothing else.

### Actual skill deltas (recorded, not forced to brief numbers)

- `git diff --numstat` on regenerated tree (before revert): `messaging-the-human/SKILL.md` **+37/−3** (matches brief), `queue-handoff/SKILL.md` **+4/−0** (brief said +9/−1 — actual is +4/−0, recorded here).
- No other shared skill changed (`git diff --numstat | grep skill` shows only these two across all 8 rig mirrors). No skill-patches needed (frontmatter parses; generator path sufficed).

### Files changed (M4)

1. `schemas/rigspec-keys.pinned.json` — `MEMBER_KEYS` += `codex_permissions` (after `claude_permissions`); provenance `package`/`commit` → 0.7.4/`6d9e8e27`, `upstream_tarball.tarball_sha256` → `d11dd8a6…920a1`, `refreshed_at` 2026-10-28, recipe/refresh strings → 0.7.4. `vendored_sha256` auto-refreshed by the generator to `1d4bf9a1…` (verified MATCH against `.ts` bytes post-revert).
2. `schemas/rigspec-schema.pinned.ts` — same key + header/commit/recipe → 0.7.4.
3. `schemas/run-record.v1.schema.json` — **new**, `cp` from tarball extract, `cmp`-verified identical to tarball AND installed copy.
4. `schemas/contract-schemas.sha256` — run-record line appended (`b3c7ac64…`); header reworded to six-of-seven from 0.7.4 tarball. `sha256sum -c` → 7/7 OK.
5. `scripts/verify-rigs.sh` — `MEMBER_KEYS` += `codex_permissions`; HR-2.1 block 0.7.2→0.7.4 (12 replacements, all in-block; tgz filename too); V18 appended run-record byte-cmp block (no existing line reworded).
6. `scripts/generate-rigs.py` — `OPENRIG_VERSION` 0.7.2→0.7.4, `OPENRIG_COMMIT` `8b180689`→`6d9e8e27`.
7. `tests/test_schema_contracts.py` — `SCHEMA_FILES` += run-record (7 total); "six"→"seven"; new `test_run_record_schema_is_upstream_shape` ($id/const/9 required keys) + `test_run_record_schema_is_non_vacuous` (empty doc fails). Suite: 8→10 tests.
8. `.scratch/vendor` — symlink → `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.scratch/vendor` via `python os.symlink` (gitignored; needed for regen only).

### M4 verification (exact commands, all in worktree)

- `python3 -m unittest tests.test_schema_contracts` BEFORE pin/file (RED): `FAILED (failures=1, errors=8)` — file missing + pin gap. AFTER: `Ran 10 tests … OK`.
- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py` → exit 0 (`wrote 51 specialist AgentSpecs, 68 shared skills, …`).
- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py --check-idempotent` → `idempotence check passed (two consecutive runs byte-identical)`.
- `./scripts/verify-rigs.sh --check-only` on DEV-regenerated tree → `SUMMARY: 32 checks passed, 51 failed`; **every** failure is `DIRTY-264135e…` provenance (54 lines) except 3× V19 expecting `'33 checks passed'` — i.e. the old `passes + 1` cascade under dirt, which is exactly the M5 motivation (log: `/tmp/opencode/verify-m4.log`). Non-DIRTY gates (V1 member keys, V4/V5 digests, V18 contracts incl. run-record cmp, 68-skill lock) all PASS; skills-lock sources read `npm:@openrig/cli@0.7.4`.
- Revert (sources-only): `git checkout -- specs/ rigs/ rosters/ registry/ fleet/skills-lock.json` → tree holds only the 8 source files above (+ new schema + openspec dir). Coordinator runs the clean regen.

## M5 — test wiring, canary, V19, V12

### Files changed (M5)

1. `Makefile` — `test:` → `python3 -m unittest discover -s tests -p 'test_*.py' -v` (was 15 hardcoded files; 21 suites / 504 tests now run).
2. `tests/fixtures/can-base-permissions.json` — **new** (17 KB): `{base_commit: a33f3bb, permissions: {51 roles}}` generated from `git show a33f3bb:fleet/fleet.yaml` on this host; fixture-fallback source when the object is unresolvable.
3. `tests/test_build_canary.py` — `test_canary_scope_only` reworked: asserts the 102-closeout `bash_deny` triple byte-exact on all 51 roles, normalizes it away (`_without_triple`, fail-closed — non-triple denies are kept), then asserts the normalized changed set == canary + M4-5 + wave-F-1. Base loads from live git object, else fixture (`_load_base_permissions`); freshness cross-check (fixture == git) whenever git resolves; new `test_canary_scope_only_fixture_fallback` pins the fallback with an unresolvable commit.
4. `scripts/verify-rigs.sh` V19 — `_v19_live = passes + 1` → frozen canonical total `_v19_canonical = 35` (the freeze V19 itself declares and V20+ comments cite); green-run guard `passes + 1 == 35` retained so a new ok()-bearing gate still fails loudly instead of rotting. ok() text, block header, SUMMARY count unchanged.
5. `scripts/verify-rigs.sh` V12 — bwrap-missing + `HERETEK_ALLOW_NO_BWRAP=1` → `[NOTE]` note-mode; otherwise still hard `fail`.

### Post-#121 reality (enumerated from live base diff, not invented)

- `git show a33f3bb:fleet/fleet.yaml` vs live: raw changed = **all 51** (every role gained `bash_deny: ["rig queue list", "rig queue create", "rig send"]` — the 102-closeout triple; verified exact on all 51, absent on all 51 base roles).
- After triple normalization, changed = exactly 7: `engine-systems-eng` (canary: `date +%s`, `cmake -S *`, `gcc/g++ *`, `path_write` +`build/*`), `ai-red-teamer`, `compliance-auditor`, `dependency-patcher` (commit-grant strip), `sabotage-qa-tester`, `static-analysis-lead` (runner-verb strips), `cpp-lowlevel-eng` (wave-F `gcc/g++` overlay).

### M5 verification (exact commands)

- `make test` → exit 0, `Ran 504 tests in 102.875s / OK` (503 pre-existing + 1 new fallback test; mock probes executed, 0 skips). Log: `/tmp/opencode/make-test.log`.
- Canary both modes: `test_canary_scope_only` (git path) ok; `test_canary_scope_only_fixture_fallback` (bogus `000…000` commit → `source == "fixture"`) ok; git-less simulation `GIT_DIR=/tmp/opencode/no-git-db … test_canary_scope_only` → OK.
- V12 note-mode: bwrap hidden via `PATH=/tmp/opencode/no-bwrap-bin` (5026 symlinks, all tools except bwrap):
  - without var → exit 1, `SUMMARY: 34 checks passed, 1 failed`, sole FAIL = V12 bwrap (mandatory preserved). Log: `/tmp/opencode/verify-nobwrap-novar.log`.
  - with `HERETEK_ALLOW_NO_BWRAP=1` → exit 0, `35 checks passed, 0 failed`, `[NOTE] … note-mode`. Log: `/tmp/opencode/verify-nobwrap-var.log`.
- V19 no-cascade: in the no-bwrap run, V19 block → `[PASS] Stale-count guard … (35 checks passed)` despite the V12 failure — only the failing gate fails. (Old-code cascade preserved as evidence in `/tmp/opencode/verify-m4.log`: V19 ×3 expecting `'33 checks passed'`.)
- `make verify` → exit 0 (`SUMMARY: 35 checks passed, 0 failed`; live-health advisory SKIPs only — no daemon on this host, untouched by design). `python3 scripts/audit_loop.py --self-test` → PASSED.
- Stub scan: no TODO/FIXME/NotImplemented/`|| true`(new)/empty-catch added (the two `except: pass` in verify-rigs.sh and Makefile `|| true` are pre-existing).

## Final tree state (for coordinator)

- Modified (8): `Makefile`, `schemas/contract-schemas.sha256`, `schemas/rigspec-keys.pinned.json`, `schemas/rigspec-schema.pinned.ts`, `scripts/generate-rigs.py`, `scripts/verify-rigs.sh`, `tests/test_build_canary.py`, `tests/test_schema_contracts.py`.
- New (3): `schemas/run-record.v1.schema.json`, `tests/fixtures/can-base-permissions.json`, `openspec/changes/overhaul-b/` (spec, pre-existing untracked).
- Reverted (NOT in commit): `specs/ rigs/ rosters/ registry/ fleet/skills-lock.json` — coordinator runs the clean regen + leaves commit per the established pattern.
- Not committed (per instructions). No `--force`, no `Closes` (Refs only at PR time).

## Self-audit / open items

- V19 now hardcodes the canonical 35 with a green-run live-count guard; if a future change adds an ok()-bearing gate, the constant + docs + freeze comments must move together (comment in-block says so).
- The 102-closeout triple is now asserted byte-exact fleet-wide; any future per-role `bash_deny` addition will trip the canary bound until the bound is deliberately updated — intended fail-closed behavior.
- `fleet/fleet.yaml` header (`@openrig/cli@0.7.2`) and `fleet/mcp-servers.yaml` pin (`builtin:rig-mcp-serve-http@0.7.2`) intentionally untouched — generator inputs outside REQ-B4; no verifier checks them.
- Tarball (`schemas/openrig-cli-0.7.4.tgz`, 8.4 MB) intentionally NOT vendored — SHA recorded; generator/verifier attest-if-present semantics unchanged.
