# Verification: wave-d-checker-batch (T3 drift-guard)

- Stage/wave id: checker-batch-d (T3 audit only)
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/checker-batch-d` (branch `feat/checker-batch-d`, HEAD `fb1e7fb`)
- Date (UTC): 2026-10-25
- Auditor: drift-guard (read-only; no code fixed, nothing committed)
- Spec read from disk: `openspec/changes/checker-batch-d/proposal.md`, `openspec/changes/checker-batch-d/specs/checkers/spec.md` (REQ-D94/D95/D98/D101/D102/G1, REQ-D96-DEFER), `openspec/changes/checker-batch-d/design.md`, `openspec/changes/checker-batch-d/tasks.md`, `AGENTS.md`
- T1 report: `docs/reports/checker-batch-d-implementation.md`; T2 evidence: `docs/evidence/wave-d-checker-batch.md`
- Diff basis: `git diff main...feat/checker-batch-d` (191 files; BASED comparison — bare `git diff` omits committed changes on a clean tree)

## 1. Requirements audit (all satisfied)

- REQ-D94 (manifest-closure): `scripts/manifest-closure.py` carries NEEDS-DECLARATION fail-closed for `$`-words (`:672`), `node -e`/`python -c` exec flags (`:135,138,510`), `git -c alias.*=!` shell-out (`:132,543`), `.gitlab-ci.yml` + CircleCI/pipelines discovery (`:142-144,413,731-733,788`). Corpus `tests/test_manifest_closure.py` +260 lines. Auditor re-ran: 44/44 pass (within 91-pass corpus run).
- REQ-D95 (TOML walk + derived pin): `scripts/policy-verifier.py` uses `tomllib` structural walk as authoritative (`:70,312,398-438,630`), line-scan retained for attribution (`_search_lineno :387`). Pin derives from repo-root `rust-toolchain.toml` (`channel = "1.89.0"`, fail-closed), mirror `scripts/policy-verifier.toolchain-pin` = `1.89.0` with agreement enforced by test. Corpus +149/-4. Auditor re-ran: 42/42 pass.
- REQ-D98 (schemas): deviation judged ACCEPTABLE under the spec's own alternative. The 0.6.13 tarball ships no schema files (documented in `schemas/contract-schemas.sha256` header + T1/T2 + V18 block comment), so byte-exact vendoring was impossible without false provenance. Implemented alternative per spec parenthetical ("or validate artifacts against the installed copies"): V18 runs `rig bundle check` x8 + `rig spec validate` x9 on installed 0.6.13 (verify output: "rig bundle check + spec validate clean on installed 0.6.13") + `schemas/contract-schemas.sha256` freezes the 6 locals + `tests/test_schema_contracts.py` (5 tests, mutation red-proof both directions). Auditor re-ran: 5/5 pass; S3 (T2) proves mutation fails loudly.
- REQ-D101 (frontmatter): V17 parses EVERY committed SKILL.md with `yaml.safe_load` + `name == dirname` (verify output: "130 SKILL.md leaves parse with name == dirname"; auditor counted 130 leaves on disk). `nextjs-dev` quote repair + `react-best-practices` name alignment ride `fleet/skill-patches/*.yaml` + `generate-rigs.py` `load_skill_patches`/`apply_skill_patch` (fail-closed, re-parsed, `name == id` enforced) + clean regen — zero `specs/` hand-edits beyond regen output (skill diffs match patch files exactly).
- REQ-D102 (stale-count guard): V19 asserts live docs state the LIVE summary (self-including `passes+1`) and trips on stale `31 checks` / `64 skills` / `0.6.11` strings in live files (history excluded by design). Drift corrected through proper sources (audit prompt 68 skills/0.6.13, tech docs 68=12+56, AGENTS.md/README/USER_GUIDE 35). Verify output: "live docs state the live SUMMARY (35 checks passed)".
- REQ-G1 (append-only, generator rule): `scripts/verify-rigs.sh` numstat = 208 additions / 0 deletions, single hunk `@@ -2222,6 +2222,214` (V17/V18/V19, one `ok()` each) — pure append, no renumber/reword. `specs/` `rigs/` `rosters/` `registry/` leaves in diff are regen effects only (SKILL.md x2 from patches; `mcp.json` `enabled:false` bake-in from pre-existing V16 renderer host tool poverty, noted in T1; `bundle.yaml`/registry views/status from clean regen `e52f2f0` + accepted `bd6ed99` 40-hex provenance re-lag). Generator mechanism on disk; idempotent regen recorded in T1 (`--check-idempotent` rc=0).
- REQ-D96-DEFER: #96 untouched — `git diff` grep for `refresh-policy-only|drift alert` across `scripts/` = 0 hits; broader grep across `scripts/ tests/ openspec/changes/checker-batch-d/` returns only defer/out-of-scope mentions. No `--refresh-policy-only`, no health drift alert. PASS.

## 2. Re-run, do not trust (auditor-ran)

- `./scripts/verify-rigs.sh --check-only` → rc=0, `SUMMARY: 35 checks passed, 0 failed` (V17 130 leaves / V18 native verbs / V19 live-SUMMARY lines all PASS in output).
- `python3 -m pytest tests/test_manifest_closure.py tests/test_policy_verifier.py tests/test_schema_contracts.py` → rc=0, **91 passed** (44 + 42 + 5).
- Stub hunt over changed checkers/generator/corpus: `TODO|FIXME|XXX|NotImplementedError||| true|except.*pass` → zero hits.
- `git status --short` → clean (empty) at audit time.
- Live counts: AGENTS.md / README.md / USER_GUIDE.md all state 35, matching live SUMMARY 35.

## 3. Red-proof audit (T2 evidence, from disk)

`docs/evidence/wave-d-checker-batch.md` records baseline green (35/0 + 91 passed) then 5 sabotages, each RED with non-vacuous signature then GREEN on revert with `git status --short` clean after every revert:
- S1 ($-skip, D94): `pytest -k dollar` rc=1, 4 named tests failed → revert → 44/44 green.
- S2 (inline-table bypass, D95): `pytest -k "inline or dotted"` rc=1, 4 named tests failed, header-spelled still passing (targeted) → revert → 42/42 green.
- S3 (status.json bodyDigest drop, D98): corpus rc=1, 1 named test failed → revert → 5/5 green.
- S4 (nextjs-dev unquoted colon, D101): verify rc=1, 30 passed / 5 failed incl. named `[FAIL] V17/#101 ... frontmatter unparseable` + fail-closed cascade (interlock working) → revert → 35/0 green.
- S5 (stale `31 checks passed` in README, D102): verify rc=1, 34/1 with surgical named `[FAIL] V19/#102` → revert → 35/0 green.
No vacuous checks (`CRITICAL: Vacuous acceptance check — none`). Every critical assertion has a recorded RED before GREEN. PASS.

## 4. Carried items (properly carried, not claimed — do not fail)

- Loader 68/68 host run (REQ-D101 red-proof): UNVERIFIED in T1 self-audit AND T2 §3 with daemon-absent evidence (`rig queue list` → `Error: Daemon not running`); static proxy V17 stands in, proven non-vacuous by S4. Carried honestly, not claimed. PASS.
- D98 vendor deviation: recorded design deviation with impossibility proof + spec-alternative enforcement (see §1). PASS.
- Canary 12 (`test_build_canary` mock-harness deny failures): pre-existing, stays out of scope. `git diff --name-only main...feat/checker-batch-d` shows no `test_build_canary` overlap (only `test_manifest_closure.py`, `test_policy_verifier.py`, `test_schema_contracts.py` under `tests/`); T2 confirms canary file last touched `bd05c65` pre-base. Not re-run per task; not failed. PASS.
- V13 `[:300]` truncation quirk: pre-existing, observed only, untouched per REQ-G1. PASS.

## 5. Findings

None. No stub pattern, no vacuous check, no failing command, no missing deliverable, no renumber/reword, no hand-edit of generated leaves, no #96 scope creep.

## 6. Report

- Verdict file: `docs/reports/wave-d-checker-batch-verification.md` (this file, uncommitted per instructions — NOT committed).
- `git status --short` at audit end: clean except this new untracked verdict file (no source modifications by auditor).

VERDICT: PASS
