# overhaul-b M4-M5 drift-guard verification (independent adversarial audit)

- Stage/wave: overhaul-b M4-M5. Worktree: `.lane/trees/overhaul-b`, branch `feat/overhaul-b`.
- Base: `264135e`. Commits: `6781e0e` feat + `58f4202` chore regen + `92e42d8` test evidence. `git status --short` clean (verified this session).
- Auditor: independent subagent audit, read directly from disk. No source files modified, nothing committed by auditor.
- Spec sources: `AGENTS.md`, `openspec/changes/overhaul-b/{proposal.md,design.md,tasks.md,specs/contracts/spec.md}` (REQ-B4/B5/G1), `docs/reports/overhaul-b-implementation.md`, `docs/evidence/overhaul-b/{red-proofs.log,qa-run.log}`.

## REQ-B4 — 0.7.4 contract sync: PASS

- `codex_permissions` placement: `schemas/rigspec-keys.pinned.json:62-63`, `schemas/rigspec-schema.pinned.ts:53-54`, `scripts/verify-rigs.sh:144` — in every copy immediately after `claude_permissions`. Verified live.
- Exact upstream set match: parsed `MEMBER_KEYS` Set literal from installed `@openrig/cli` (`/home/john/.npm-global/lib/node_modules/@openrig/cli/daemon/dist/domain/rigspec-schema.js:45-49`) and diffed against pinned `keys.MEMBER_KEYS` in Python — `MATCH: True`, set symmetric difference empty, `codex_permissions` index 12 directly after `claude_permissions` index 11 in both. No extra/missing key.
- Run-record byte-identity: `sha256sum schemas/run-record.v1.schema.json` = `b3c7ac64fd9dd51152888c99fdbcadd85cddebebb2d38253864bff054da3fde7` (matches REQ-B4); `cmp` tarball extract (`/tmp/opencode/overhaul-b-tarball/.../run-record.v1.schema.json`) vs vendored copy → IDENTICAL. Tarball SHA re-verified: `d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1`.
- Pin + coverage: `schemas/contract-schemas.sha256` carries the run-record line; `sha256sum -c` run inside `schemas/` → 7/7 OK. `tests/test_schema_contracts.py` `SCHEMA_FILES` = 7 entries; suite runs 10 tests (8→10, +upstream-shape +non-vacuous run-record tests).
- Skill sync via generator path: `cmp` tarball skill bodies vs `specs/agents/_shared/skills/{messaging-the-human,queue-handoff}/SKILL.md` → both IDENTICAL. `git diff 264135e HEAD --numstat -- specs` = `37/3` and `4/0` (matches implementation report's recorded actuals, not the brief's `+9/-1` — correctly recorded, not forced). No skill-patch files added; `write_yaml`/`safe_dump` call sites in `generate-rigs.py` target only generated leaves (`agent.yaml`, `rig.yaml`, pods, configurations, bundle) — `fleet/fleet.yaml` is read-only (`yaml.safe_load`, line 967), never dumped.

## REQ-B5 — test wiring, canary, V19, V12: PASS

- Discover runs all suites: `Makefile:37-38` is now `python3 -m unittest discover -s tests -p 'test_*.py' -v`; `git diff 264135e HEAD -- Makefile` touches ONLY that target (2 lines). 21 files match `tests/test_*.py`; `make test` re-ran by auditor → `Ran 504 tests … OK`, exit 0.
- Canary expected-set enumerated from live diff, not invented: `test_canary_scope_only` asserts the 102-closeout `bash_deny` triple byte-exact on all 51 roles, normalizes it away via fail-closed `_without_triple`, then asserts changed set == canary + M4 5 (`ai-red-teamer`, `compliance-auditor`, `dependency-patcher`, `sabotage-qa-tester`, `static-analysis-lead`) + wave-F 1 (`cpp-lowlevel-eng`). Fixture fallback real: `tests/fixtures/can-base-permissions.json` = `{base_commit: a33f3bb, permissions: 51 roles}`; `_load_base_permissions` prefers live `git show a33f3bb`, falls back to fixture, with freshness cross-check (fixture == git whenever git resolves); dedicated `test_canary_scope_only_fixture_fallback` pins the fallback path.
- V19 canonical total with cascade gone: `scripts/verify-rigs.sh:2517` `_v19_canonical = 35`, `:2523` `_v19_live = _v19_canonical` (no `passes + 1`); green-run guard (`passes + 1 != canonical` → loud fail) retained so a future ok()-bearing gate cannot rot silently. Auditor re-ran full `verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed`, exit 0; red-proofs R6 triplication evidence (old code → 3× V19 doc-drift FAILs) is on record and the restored tree shows single-fail-only behavior.
- V12 note-mode mandatory-by-default: `scripts/verify-rigs.sh:1703-1706` branches on `HERETEK_ALLOW_NO_BWRAP=1` → `[NOTE]`, else hard `fail`. Red-proofs R7 probes both paths (exit 1 without var, exit 0 with var, `[NOTE]` text present). No dedicated unit test — live gate probe is the coverage, correctly disclosed in the log.

## REQ-G1 — append-only, generator rule: PASS

- V1–V27 unrenamed: all 27 `== VN.` headers present exactly once (`grep` V1/V6–V27 verified; V2&V3 / V4&V5 combined headers are pre-existing convention, untouched). Verify diff adds only new blocks (V18 run-record cmp, V19 freeze wording) — no renumber/reword of existing gates.
- SUMMARY frozen: `AGENTS.md:15`, `README.md:47`, `docs/USER_GUIDE.md:127` all state 35; V19 checks the live SUMMARY against the canonical total.
- `specs/`+`rigs/`+`rosters/` vs `264135e`: 34 files = 8 rigs × (SETUP.md + bundle.yaml + 2 skill SKILL.md) + 2 specs skills; zero `rosters/` changes. SETUP diff = one-liner 0.7.2→0.7.4; bundle diff = min versions + assembler version/commit + integrity digests only. No hand-edits beyond the two generator-emitted skill bodies.
- Registry delta provenance-only, zero DIRTY: only `openrigVersion` 0.7.2→0.7.4, `commit 8b180689`→`6d9e8e27`, `minCli/minDaemonVersion`, `resolvedCommit` (→`6781e0e`), `packageDigest` refreshes; `grep -c DIRTY` on the registry diff = 0; no DIRTY stamps in tree.
- No Makefile changes beyond the test target; no V19-canary edits beyond scope (full `git diff --name-only` = sources + regen leaves + spec/evidence/fixture only; `fleet/fleet.yaml`, `fleet/mcp-servers.yaml`, `rosters/` untouched).

## Stubs / skips / secrets / anti-stub scan: PASS

- Changed scripts/tests (`scripts/generate-rigs.py`, `scripts/verify-rigs.sh`, `tests/test_build_canary.py`, `tests/test_schema_contracts.py`) scanned: no `TODO`/`FIXME`/`NotImplemented`/stub comments added; `except: pass` (generate-rigs helper, verify-rigs) and Makefile `|| true` (line 13 `RIG_BIN`) are pre-existing.
- Skips are pre-existing patterns, not new gaps: `skipUnless(HAS_JSONSCHEMA)` ×5 in contract suite exists on base `264135e` (same lines); `SkipTest` in canary mock-harness probe exists on base (`:233`); no new skip added by the diff (`git diff … | grep Skip` empty).
- Secrets: changed files contain only SHAs (`b3c7ac64…`, `d11dd8a6…`) and dummy fixtures; `grep` hits for `ghp_|AKIA|sk-` are the verifier's own secret-pattern regexes (detection code), not literals. No credentials in evidence/reports.

## Red-proof evidence audit: PASS

- `docs/evidence/overhaul-b/red-proofs.log` R1–R7 each records inject → RED (exit 1, non-vacuous signature) → `git checkout --` restore → GREEN (exit 0): R1 verify-gate RED on dropped `codex_permissions` (`32 passed, 1 failed`, contract suite staying OK correctly explained as scoping); R2 contract RED on 1-byte run-record corruption (`FAILED (failures=1)`); R3 read-only tarball IDENTICAL diffs; R4 discover 504==504; R5 canary RED on both paths (`failures=2`); R6 old-code cascade triplication (`33 passed, 4 failed`) vs fixed single-fail; R7 V12 both paths. Baselines all GREEN exit 0. `git status --short` verified clean by auditor (evidence committed in `92e42d8`); auditor performed no mutations.

## Re-run results (auditor, real output)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed`, exit 0.
- `python3 -m unittest tests.test_schema_contracts` → `Ran 10 tests … OK`, exit 0.
- `make test` → `Ran 504 tests in 102.946s … OK`, exit 0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, exit 0.

VERDICT: PASS
