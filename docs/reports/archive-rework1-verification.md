# archive-waves rework cycle 1 — drift-guard verification (re-audit)

- Stage/wave: archive-waves rework cycle 1 re-audit (prior state: clean triad start at `87f4f44`; rework `5bc17c4` + evidence `b4a2f16` since).
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/archive-wave` (branch `feat/archive-waves`).
- Date: 2026-10-28. Auditor: Independent Drift Guard (Muse Spark 1.3 Contributor). No production code touched; no commit made.
- Sources read from disk: `AGENTS.md`; `docs/reports/archive-rework1.md`; `docs/evidence/archive-waves/rework1-red-proofs.log`; `openspec/specs/{closeout,identity,bump,p0,contracts,archive}/spec.md`; `openspec/changes/archive/2026-10-28-{102-closeout,107-identity}/tasks.md`; `docs/sprints/CLI-0.7.4-BUMP.md` (restored); `tests/test_schema_contracts.py`.

## 1. Spec & architecture audit — all reported fixes hold

- **F1 (tasks `AND` → `&& !`, 102-closeout T2 + T0 paths): HOLDS.** `openspec/changes/archive/2026-10-28-102-closeout/tasks.md:25` reads `./scripts/verify-rigs.sh --check-only && ! grep -rn 'superpowers:writing-skills' specs/ fleet/ (expect 0)`; line 4 acceptance uses the archived `openspec/changes/archive/2026-10-28-102-closeout/…` paths. The `!` negation is correct shell idiom (bare `grep -rn …` exits 1 on zero hits, so bare `&& grep` could never exit 0) — re-run below confirms exit 0.
- **F2a (`AND` → `&&`, 107-identity T2): HOLDS.** `openspec/changes/archive/2026-10-28-107-identity/tasks.md:25` reads `./scripts/verify-rigs.sh --check-only && grep -c 401 docs/evidence/107-identity/red-proofs.log`. Re-run prints `9`, exit 0.
- **F2b (stale T0 paths): HOLDS.** Both T0 acceptances point at archived locations; both `ls` commands exit 0 (`T0-102=0`, `T0-107=0`); stale `openspec/changes/102-closeout/` and `openspec/changes/107-identity/` confirmed absent (exit 2).
- **F3 (ledger restore): HOLDS.** `openspec/specs/bump/spec.md:15` (REQ-BUMP1) MUSTs the ledger at live path `docs/sprints/CLI-0.7.4-BUMP.md` with a scenario asserting that path's contents — a live requirement, so restore was required, not optional. `docs/sprints/` now holds ONLY `CLI-0.7.4-BUMP.md`; the archive sprints dir holds the stale files and no `CLI-0.7.4-BUMP.md`; `git show --name-status -M HEAD` lineage is an `R100` single-file rename; ledger scenario counts confirmed `0.7.4` ×19, tarball sha ×1, `35 checks passed` ×1. REQ-C6 keep-list excludes the ledger in BOTH copies (`openspec/specs/archive/spec.md:15` and archived overhaul-c delta `:6`, byte-identical sentences); correction note appended to `docs/reports/overhaul-c-implementation.md` (record-preserving, history not rewritten).
- **F4a (grant mapping): HOLDS, accurate to sources.** `fleet/fleet.yaml:648-649` (`- rig queue *`, `- rig send *` in `bash_allow`) with `657-660` the exact bare triple in `bash_deny`; rendered seat map (`rigs/cloud-sre-and-data-platform/agents/analytics-metrics-eng/runtime/pi-permission-config.json`) shows `'rig queue *' → allow`, `'rig send *' → allow`, bare triple → deny. REQ-C18 states the mapping separately in both copies (live `openspec/specs/closeout/spec.md:15` + archived 102-closeout delta `:6`); bare-form denials verbatim.
- **F4b (V18 citations): HOLDS, bracket the true blocks.** Measured: bundle-check loop opens line 2447 (`for _slug18 in EXPECTED_8_RIGS:`), block closes 2469 (trailing `)` of the `fail(` paren); spec-validate loop opens 2470 (`for _spec18 in …`), closes 2482. Cited `:2447-2469` / `:2470-2482` match exactly in both copies.
- **F5 (fixed-digest pin test): HOLDS.** `tests/test_schema_contracts.py:122-134` adds `test_run_record_pins_fixed_074_digest` asserting sha256 == `b3c7ac64fd9dd51152888c99fdbcadd85cddebebb2d38253864bff054da3fde7`; on-disk `sha256sum schemas/run-record.v1.schema.json` matches; pin file line 27 carries the same digest; spec sentence added in both copies (`openspec/specs/contracts/spec.md:15` + archived overhaul-b delta).
- **F6 (at-most-one container): HOLDS.** `.github/workflows/docker-release.yml` contains exactly one `container:` block (line 113, smoke job); verify-fleet (48–60) and build (62–102) define none. REQ-A3 says "at most one … per job (today only the smoke job defines one; verify-fleet and build define none)" in both copies (`openspec/specs/p0/spec.md:33` + archived overhaul-a delta).

## 2. Scope — no creep beyond the findings

`git diff 87f4f44..HEAD --name-only` = exactly 15 paths: the two tasks files, four archived delta specs, four live specs (closeout/contracts/p0/archive — identity and bump specs correctly untouched, no finding touched them), `tests/test_schema_contracts.py`, `docs/reports/overhaul-c-implementation.md` (correction note), the `R100` ledger rename, `docs/reports/archive-rework1.md`, `docs/evidence/archive-waves/rework1-red-proofs.log`. No `scripts/`, `schemas/`, `fleet/`, `docker/`, or workflow changes — the test addition is the only behavior change. F3 left no strays: one path pair changed, nothing else moved.

## 3. Generator rule

`git diff b489310..HEAD -- specs/ rigs/ rosters/ registry/` is empty (zero DIRTY by construction; verify digest gates green). No `generate-rigs.py` run was owed (no generator inputs changed). `yaml.safe_dump` never used — no `fleet/fleet.yaml` edits at all.

## 4. V1–V27 / SUMMARY frozen

No `scripts/` changes in the diff (no renumber/reword possible); `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed`, exit 0 (V22–V27 green, V19 SUMMARY frozen).

## 5. Stub / skip / secret hunt

No `TODO`/`FIXME`/`XXX`/`HACK` or empty-`catch` in changed code; the only `pass`-adjacent hits are docstrings describing vacuous-schema red directions. The six `@unittest.skipUnless(HAS_JSONSCHEMA, …)` decorators are pre-existing (not introduced by rework) and none triggered (11 tests ran, 0 skipped). Secret-pattern grep over all changed specs, the test file, the rework report, and the red-proofs log: no hits (exit 1); only public SHAs (`b3c7ac64…`, `d11dd8a6…`) and dummy/redacted fixtures.

## 6. Red-proof log audit (`docs/evidence/archive-waves/rework1-red-proofs.log`)

Every critical assertion has a recorded RED plus GREEN restore with non-vacuous signatures: F1 compound exit 0 with `VERIFY_EXIT=0` + 35/0; F2a count `9`; F2b stale-path exit 2; F3 move-back sabotage (`test -f` exit 1, `grep -c` exit 2) + sha256 `ba7d3889…` identity + `git log --follow` history; F5 byte-flip → `FAILED (failures=2)` naming exactly the new digest test + pin-consistency test, restore → `OK` with empty `git diff -- schemas/`; F6 duplicate-`container:` → count 2 RED, restore byte-identical. F4a prose sabotage and F4b citation-digit sabotage are honestly recorded as citation/doc-accuracy (no committed gate reads spec prose — V22 reads `fleet/fleet.yaml` + rendered maps, which IS gate-covered); no coverage invented. `git status --short` is clean (empty output, exit 0) — sabotage fully reverted, sole post-rework delta vs HEAD is none.

Nit (not a finding): the log says the archive sprints dir holds "the other 27 stale files"; disk shows 28 entries (none is the ledger). Descriptive count only; isolation facts (ledger sole live file, no ledger copy in archive, R100 rename) all verified.

## 7. Re-runs (real output, this audit)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed.`, `VERIFY_EXIT=0`.
- F1 compound `… && ! grep -rn 'superpowers:writing-skills' specs/ fleet/` → `F1_COMPOUND=0`.
- F2a compound `… && grep -c 401 docs/evidence/107-identity/red-proofs.log` → `9`, `F2A_COMPOUND=0`.
- T0 `ls` acceptances → `T0_102=0`, `T0_107=0`; stale paths → No such file (exit 2).
- `python3 -m unittest tests.test_schema_contracts -v` → `Ran 11 tests … OK` (incl. new digest test), `CONTRACT_EXIT=0`.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, `AUDIT_EXIT=0`.
- Full `make test` (~100s) was NOT re-run by this auditor: no production-code path changed in rework (spec + test + doc edits only; the one test-file change is covered by the contract-suite re-run above), and QA's log records `make test → Ran 505 tests … OK` at `5bc17c4`. Re-running the full suite would add no signal.

## 8. Findings

None. All reported fixes verified against disk; scope confined to the findings; gates green; red-proofs non-vacuous with clean tree.

VERDICT: PASS
