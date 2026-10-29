# Verification report — Wave 1 `2026-10-29-bump-075` (agency-drift-guard)

- **Stage:** Wave 1 `2026-10-29-bump-075` · **Branch:** `feat/bump-075` · **Worktree:** `.lane/trees/bump-075`
- **Revs seen:** `c1da1fb` (merge-base) → `d158dc7` (programmer) → `3d42b7e` (QA evidence) = HEAD
- **Role:** agency-drift-guard (independent adversarial auditor; fixed no code; committed nothing)
- **Unity binding:** none
- **Start state:** `git status --short` clean (empty output before any audit command)

## Inputs read from disk (trusted no summary)

1. `/home/john/.opencode/plan/2026-10-29-five-wave-remediation-plan.md` (Wave 1 § + AGENTS.md-surgical § + triad barrier)
2. Worktree `openspec/changes/2026-10-29-bump-075/` — `proposal.md`, `design.md`, `tasks.md`, `specs/bump/spec.md`
3. Worktree canonical `openspec/specs/bump/spec.md` (regression check)
4. Worktree `AGENTS.md` + `git diff c1da1fb HEAD` (full name list + per-file hunks)
5. Worktree `docs/reports/bump-075-implementation.md`, `docs/reports/bump-075-qa.md`, `docs/evidence/bump-075/red-proofs.log`
6. Worktree `docs/sprints/CLI-0.7.5-BUMP.md` (ledger)

## Re-ran myself (exit codes observed, not quoted)

| # | Command | Observed result | rc |
|---|---|---|---|
| 1 | `rig --version` | `0.7.5 (b57c4da3)` | 0 |
| 2 | `ls` T0 four spec paths (proposal/design/tasks/specs-bump-spec) | all 4 list | 0 |
| 3 | `git diff c1da1fb HEAD --stat -- AGENTS.md` | `1 file changed, 2 insertions(+), 1 deletion(-)` (3 ≤ 15) | 0 |
| 4 | `openspec validate 2026-10-29-bump-075` | `Change '2026-10-29-bump-075' is valid` | 0 |
| 5 | `python3 scripts/audit_loop.py --self-test` | `SELF-TEST PASSED` | 0 |
| 6 | `python3 scripts/generate-rigs.py --check-idempotent` | `idempotence check passed (two consecutive runs byte-identical)`; side-effect dirtied 35 generated leaves, reverted via `git checkout -- fleet/skills-lock.json registry specs rigs rosters`, status clean | 0 |
| 7 | `./scripts/verify-rigs.sh --check-only` (serial re-run) | `SUMMARY: 39 checks passed, 0 failed` | 0 |
| 8 | `make test` | `Ran 634 tests in 105.919s — OK` | 0 |
| 9 | Independent `npm pack @openrig/cli@0.7.5` + `sha256sum` (third fetch, `/tmp` scratch, cleaned after) | `22d67c2c7e0d0ab4a5ec9faac0a725d54f9ead2c0f71564985cf4ae240bb9754` — byte-exact match to ledger + REQ-BUMP3 | 0 |
| 10 | Stub scan over change dir + ledger + both prior reports | no stub tokens (sole `TODO`-family hit is the word "Stub scan" in a table row describing the scan itself) | — |
| 11 | Secret-shape scan (`ghp_`/`sk-ant-`/`Bearer`/AKIA) over wave files | no matches | — |
| 12 | Local-path scan (`/home/`, `/Users/`) over wave files | no matches | — |
| 13 | `Closes #`/`Fixes #`/`Resolves #` scan over wave files | absent (Refs-only discipline holds) | — |

Process note (transparency, not a wave defect): my first `verify-rigs.sh` run (rc=1, `FileNotFoundError specs/agents/web-design/...`) raced with my own concurrent `--check-idempotent` regen pass. I reverted all regen side-effects and re-ran verify serially → 39/0 rc=0 (row 7). The wave's no-regen disposition is thereby independently confirmed: idempotence exits 0 and regen only vendors the deferred 0.7.5 `queue-handoff` prose, which was correctly not kept.

## Own sabotage probes (≥2, RED then GREEN, restore proof)

- **DG-1 — V18 version gate:** `_verm18.group(0) != "0.7.5"` → `"0.7.4"` → verify RED `[FAIL] V18/#98`, `SUMMARY: 38 checks passed, 1 failed`, rc=1 → `git checkout -- scripts/verify-rigs.sh`, `cmp` vs byte backup → **BYTE-IDENTICAL** → verify GREEN `SUMMARY: 39 checks passed, 0 failed`, rc=0.
- **DG-2 — V13 Dockerfile gate:** `ARG OPENRIG_VERSION=0.7.5` → `0.7.4` → verify RED `[FAIL] V13/#100`, `SUMMARY: 38 checks passed, 1 failed`, rc=1 → `git checkout -- docker/Dockerfile`, `cmp` vs byte backup → **BYTE-IDENTICAL** → verify GREEN 39/0, rc=0.
- Post-probe: `git status --short` clean, `git stash list` empty. QA's 8 logged probes were additionally spot-read for non-vacuity (each shows a distinct RED signature plus byte-identical restore); the `openspec validate` leniency boundary (header-rename / missing proposal.md / missing tasks.md still rc=0) is real but covered: the shipped package contains all four files (T0 `ls` gate, row 2) with proper `### Requirement` headers and scenarios (read directly), so the boundary is a validator limitation, not a wave defect.

## Spec-clause verdicts

- **REQ-BUMP3 (0.7.5 + ledger):** PASS — `rig --version` prints `0.7.5 (b57c4da3)`; ledger holds version string (3×), full sha256 with two-fetch evidence plus my independent third-fetch match, 8 true-pin files, tarball-diff disposition, verify output, rollback.
- **REQ-BUMP4 (green tree, frozen gates):** PASS — 39/0, V18/V13 assert 0.7.5 pin strings only (no logic touched), idempotence rc=0, self-test PASSED, `make test` 634 OK / 0 failed.
- **REQ-G1 (append-only, generator rule):** PASS — `specs/ rigs/ rosters/ registry/ fleet/ schemas/ generate-rigs.py` zero-diff vs `c1da1fb`; verify diff is 3 pin-string hunks only; SUMMARY frozen at 39; canonical `openspec/specs/bump/` untouched (still 0.7.4/35 language — correct pre-archive state, no drift beyond the approved change-dir delta).
- **Plan Wave-1 acceptance (compound + two-agent sha + `rig --version` + validate + hash-mismatch RED→GREEN):** PASS on all conjuncts.
- **AGENTS.md surgical (≤15 lines):** PASS — 3 lines (stack pin + ledger docs-map row; One Rule/secrets/conventions verbatim).
- **Changed set:** PASS — exactly 16 files: 8 true-pin files + ledger + 4 change-dir files + implementation report + QA report + red-proofs log. No generator inputs, no generated leaves, no dated-record rewrites.
- **One Rule / `safe_dump`:** PASS — the sole `yaml.safe_dump` is the pre-existing generic `write_yaml` for generated leaves (untouched by this wave); `fleet/fleet.yaml` unmodified.
- **Secrets hygiene:** PASS — no secret-shaped strings, no credential paths, no local-path leaks in any wave file.

## Skips (explicit)

- Upstream tag-peel (`git ls-remote v0.7.5 → b57c4da3…`) not re-fetched; accepted via installed-binary stamp `0.7.5 (b57c4da3)` corroboration plus ledger record. Low risk; owned by ledger, not gates.
- `rig preflight` / `rig agent validate` / daemon restart: out of scope per ledger §5 (scratch-only wave; migration 126 never run against real state).
- Two transient shell `permission.rejected` denials during audit (retried clean); one `rm -rf` blocked by policy (single-file `rm` used). No evidence lost.
- Never committed; never printed secrets.

## Rework-1 re-audit (2026-10-29, branch fix/bump-075-r1 @ a32a336, role agency-drift-guard)

- **Role:** independent adversarial auditor; fixed no code; committed nothing. Prior verdict above re-issued, not copied: every claim below re-verified against current worktree files with commands I ran myself.
- **Start state:** `git status --short` clean (empty output before any audit command). Revs seen: `b584cae` (archive/promote) → `0381977` (rework fix) → `a32a336` (QA re-verification) = HEAD.
- **Rework delta (b584cae..HEAD):** exactly 5 files, +81/−1: `docs/USER_GUIDE.md` (+6), `docs/evidence/bump-075/red-proofs.log` (+14 Probe R1), `docs/reports/bump-075-implementation.md` (+47 Rework-1 section), `docs/reports/bump-075-qa.md` (+13/−1: line-49 wording + re-verification appendix), `openspec/specs/bump/spec.md` (+2 SUPERSEDED lines). No other files touched.

### F-clause verdicts (each verified, not trusted)

- **F1 (QA line-49 wording): HONEST.** Line 49 now reads "pin-string-mismatch RED to GREEN" with the parenthetical scoping Probe A to the V18 pin-string and the digest comparison to the ledger's two independent fetches plus 0.7.4 control re-fetch. Matches red-proofs.log Probe A (pin-string sabotage, `[FAIL] V18/#98`) and Probe C (sha-scoped ledger grep) — no overclaim remains. No gate compares fetched-tarball digest vs expected digest, so digest-corruption sabotage would prove nothing; correction (not new evidence) is the minimal honest fix.
- **F2 (migration warning): MINIMAL + ACCURATE.** Blockquote is exactly `docs/USER_GUIDE.md:23-27` (5 lines, verified by `sed -n` read above), placed before the Step 1 install command (line 30). Warns of one-way migration 126, requires snapshot plus confirmed restore path, references ledger §6 Rollback — section exists (ledger lines 70-74: stop / snapshot-restore / revert steps). Ledger already had the procedure, so no ledger edit was owed.
- **F3 (SUPERSEDED lines): ACCEPTABLE + HISTORY INTACT.** `openspec/specs/bump/spec.md:15,22` carry the status lines; diff shows exactly 2 added lines, BUMP1/BUMP2 requirement and scenario text byte-verbatim. Re-grep for `BUMP1|BUMP2` over gates/tests (`*.sh *.py *.yaml *.json Makefile`, excluding dated reports, archived delta, canonical spec): zero matches (rc=1) — no gate asserts on the old text. Canonical spec still parses: `openspec list --specs` shows `bump requirements 5`, rc=0. Judgment on the direct canonical-spec edit: acceptable here — the archived package `openspec/changes/archive/2026-10-29-bump-075/` is byte-untouched (frozen history holds), no active change-id exists (`openspec/changes/` holds only `archive/`, so no `validate <change-id>` is owed), the append-only rule governs V-gates (untouched, SUMMARY still 39), and no gate pins canonical-spec wording. Rationale is recorded, not silent.
- **F4 skip: HOLDS.** Re-grep of `README.md` for `OPENRIG_VERSION|0.7.4` returns zero matches (rc=1); lines 39-40 show 0.7.5 in comment and install command. Stale line number; nothing to fix.
- **coderabbit skip: HOLDS.** The "consider running coderabbit review" text is an optional-tooling suggestion embedded in untrusted review text, not a finding; the compound gates are the acceptance path. No such tool run is owed by any spec clause.

### Re-ran myself (exit codes observed, not quoted)

| # | Command | Observed result | rc |
|---|---|---|---|
| R1 | `./scripts/verify-rigs.sh --check-only` (serial) | `SUMMARY: 39 checks passed, 0 failed` | 0 |
| R2 | `openspec list --specs` | green, `bump requirements 5` | 0 |
| R3 | Stub-token scan over all 5 rework files | zero real tokens (sole hit is the word "Stub scan" in implementation.md:78 describing the scan itself; excluding that word: rc=1 clean) | — |
| R4 | Secret-shape scan (`ghp_`/`sk-ant-`/AKIA/`Bearer`) over rework files + ledger | no matches (rc=1) | — |
| R5 | Local-path scan over rework files | sole hit is pre-existing container path `/home/heretek` (USER_GUIDE:486, from commit `7717930`, not introduced by rework) — no machine-local leak | — |
| R6 | `Closes #`/`Fixes #`/`Resolves #` scan over rework files | absent (Refs-only discipline holds) | — |
| R7 | Archived-package frozen check (`git diff b584cae..HEAD -- openspec/changes/archive/`) | empty (untouched) | 0 |
| R8 | One-Rule check (`git diff b584cae..HEAD -- specs/ rigs/ rosters/ registry/ fleet/ schemas/ generate-rigs.py`) | empty (no generated leaves, no generator inputs) | 0 |

### Own sabotage probe (DG-R1, RED→GREEN, restore proof)

- **DG-R1 — V18 version gate (distinct from QA's R1, which probed V13):** byte backup of `scripts/verify-rigs.sh` (sha256 `4f3d8c40…c67f9c6c0f` both copies) → sabotage `_verm18.group(0) != "0.7.5"` → `"0.7.4"` (line 2411) → verify RED `[FAIL] V18/#98: host rig --version is not 0.7.5 (got 0.7.5 (b57c4da3))`, `SUMMARY: 38 checks passed, 1 failed`, rc=1 → `git checkout -- scripts/verify-rigs.sh` + `cmp` vs backup → **BYTE-IDENTICAL** (backup removed) → verify GREEN `SUMMARY: 39 checks passed, 0 failed`, rc=0.
- Post-probe: `git status --short` clean (empty), no strays. Rework edits blunt no gate.

### Observation (nit, not a finding)

- Implementation report Rework-1 cites the warning as "`docs/USER_GUIDE.md:21-27`, 6-line blockquote"; the blockquote is actually lines 23-27 (5 lines — lines 21-22 are the install prose). Substance is accurate (migration 126, snapshot, ledger §6 ref all verified above); the QA appendix cites 23-27 correctly. Report line-range imprecision only — style nit, not FAIL per the severity rule.

### Skips (explicit)

- `make test` not re-run by this auditor: rework delta is docs/spec/reports-only (no `.py`/test/generator edits); full suite green at 634/0 per QA baseline and R1 gates green. Skipped with reason, matching the implementation report's stated skip.
- `openspec validate <change-id>`: N/A — no active change-id (`openspec/changes/` holds only `archive/`); canonical-spec health covered by R2 instead.
- One transient shell `permission.rejected` during audit (retried clean, no evidence lost).
- Never committed; never printed secrets.

VERDICT: PASS

## Rework-2 re-audit (2026-10-29, branch fix/bump-075-r2 @ fbca5ed, role agency-drift-guard)

- **Role:** independent adversarial auditor; fixed no code; committed nothing. Prior verdicts above re-issued, not copied: every claim below re-verified against current worktree files with commands I ran myself.
- **Start state:** `git status --short` clean (empty output before any audit command). Revs seen: `51757e4` (rework-1 VERDICT) → `be9d72e` (rework fix) → `fbca5ed` (QA re-verification) = HEAD.
- **Rework delta (`git diff 51757e4 HEAD --stat`):** exactly 4 files, 87 insertions, 2 deletions — `.github/workflows/docker-release.yml` (1 line), `scripts/verify-rigs.sh` (1 line), `docs/reports/bump-075-implementation.md` (+65), `docs/reports/bump-075-qa.md` (+20). Functional delta is exactly 2 lines (one word each); docs diffs are pure append (zero `-` lines outside the two replaced lines; both hunks anchored at file tails `@@ -144,3 +144,68 @@` / `@@ -59,3 +59,23 @@`). No hunk beyond the 2 functional lines + docs appendices exists — minimality HOLDS.

### Hunk-by-hunk audit (full `git diff 51757e4 HEAD` read from disk)

- **H1 — workflow pip line (`docker-release.yml:53`):** `pip install --quiet pyyaml jsonschema` → `pip install --quiet pyyaml jsonschema referencing`. Single-line hunk (`@@ -50,7 +50,7 @@` context is the only hunk in the file); `git diff -U0` confirms no other step touched. Full-file judgment: all other steps byte-identical (checkout SHA pin, all `run:` bodies, matrix, permissions, concurrency, env blocks unchanged — verified by the single-hunk diff, not by summary). YAML-schema risk: NONE — `yaml.safe_load` parses OK, `jobs` keys intact (`verify-fleet/build/smoke`), verify-fleet step count 6, V27 UniqueKey parse green inside the 39/0 run (see R-row below). The added bare name `referencing` matches the line's existing unpinned style; no pin invented — correct minimal form for a CI install line tracking the runner image, not a lockfile.
- **H2 — guard preamble (`scripts/verify-rigs.sh:34`):** `import yaml, jsonschema` → `import yaml, jsonschema, referencing`. Single-line hunk (`@@ -31,7 +31,7 @@`); the `uv` fallback line 36 and every V-gate block below line 40 are byte-untouched. Append-only V-gates HOLDS — zero gate text touched (no `V[0-9]` line in the diff; SUMMARY frozen at 39, confirmed by re-run).
- **H3/H4 — report appendices:** implementation.md +65 and qa.md +20, both tail-appended sections, zero deletions. Content verified accurate against the tree (pip line 53, guard line 34, uv line 36 all re-grepped by me — line numbers and quoted strings match; the `referencing`-has-no-`__version__` deviation note is correct, `importlib.metadata` path verified by me at 0.37.0).

### Discipline verdicts

- **One Rule:** PASS — `git diff 51757e4 HEAD --name-only -- specs/ rigs/ rosters/ registry/` empty; `fleet/ schemas/ generate-rigs.py` empty (sole `scripts/` touch is the guard preamble, not the generator).
- **Frozen-archive integrity:** PASS — `git diff 51757e4 HEAD --name-only -- archive/` empty; `openspec/` empty (no active change-id touched, archived package untouched).
- **Secrets / no-local-paths hygiene on added lines:** PASS — added-line scan for `ghp_|gho_|sk-ant-|AKIA|Bearer|/home/|/Users/|secrets/|.key|.pat|password|token` returns zero hits. Appendix worktree references are repo-relative (`.lane/trees/bump-075-r2`), never machine-absolute.
- **`Refs`-only discipline:** PASS — no `Closes #`/`Fixes #`/`Resolves #` in the delta (bump ledger wave; nothing to close).

### Re-ran myself (exit codes observed, not quoted)

| # | Command | Observed result | rc |
|---|---|---|---|
| R1 | `./scripts/verify-rigs.sh --check-only` (serial) | `SUMMARY: 39 checks passed, 0 failed` (V27 M3 green line present) | 0 |
| R2 | `git diff 51757e4 HEAD --stat` | 4 files, 87 insertions, 2 deletions | 0 |
| R3 | `python3 -c "yaml.safe_load(open('.github/workflows/docker-release.yml'))"` | YAML OK, 3 jobs, 6 verify-fleet steps | 0 |
| R4 | Added-line secret/local-path scan | zero hits | — |

### Own sabotage probe (DG-R2, RED→GREEN, restore proof — distinct from QA's R2-6/R2-7 emulation and all prior V13/V18 pin probes)

- **Why not sabotage the pip line in-tree:** judged VACUOUS and therefore not run in-tree — no local gate asserts on the pip line's word list (V27 checks bubblewrap presence + UniqueKey parse only), so deleting `referencing` from the tree stays GREEN locally and proves nothing about the bare-runner CI failure mode. Demonstrated without tree edit: a `/tmp` COPY with `referencing` removed still parses (`COPY YAML OK`), confirming content-sabotage of that scalar is locally undetectable by design. The meaningful local probe of the touched file is its YAML/parse gate instead.
- **DG-R2 — V27 workflow-keys gate (topical to the touched file):** byte backup of `.github/workflows/docker-release.yml` (sha256 `81154eb6…0eac3690` both copies) → sabotage: duplicate `verify-fleet:` job key → verify RED `[FAIL] V27/overhaul-a: workflow YAML fails UniqueKey parse (duplicate key 'verify-fleet')`, `SUMMARY: 39 checks passed, 1 failed`, rc=1 → `git checkout -- .github/workflows/docker-release.yml` + `cmp` vs backup → **BYTE-IDENTICAL** (backups removed) → verify GREEN `SUMMARY: 39 checks passed, 0 failed`, rc=0.
- Post-probe: `git status --short` clean, `git stash list` empty. The workflow edit blunts no gate.

### Addressed questions

- **(a) uv-fallback line left without `--with referencing`: SAFE — agree, with evidence.** `importlib.metadata.requires('jsonschema')` on the pinned host (jsonschema 4.26.0) lists `referencing>=0.28.4` as an unconditional hard dependency (no `extra ==` marker, unlike the format extras); `pip show jsonschema` Requires line concurs. The CI failure mode was a satisfied-requirement no-op (pre-installed jsonschema → pip fetches nothing transitive), which cannot occur in `uv run`'s fresh ephemeral env. Empirically proven: `uv run --no-project --with pyyaml --with jsonschema python3 -c "import referencing"` → `referencing resolves OK`, rc=0 (`Installed 6 packages`). The new guard (`import yaml, jsonschema, referencing`) correctly routes a referencing-less system python into that uv path, which provably heals it. Extending the uv line would be harmless but is not owed; minimal-diff constraint correctly wins.
- **(b) V8-staged-workflow observation: CONFIRMED pre-existing, out of scope, does NOT affect clean-checkout CI.** I staged the fixed workflow blob and ran `manifest-closure.py --staged` → 20 undeclared (`pip`, `./scripts/verify-rigs.sh`, `python3`, shell words, `make`, `sudo`, `bwrap`, `bash`), rc=1; then staged the pre-fix `51757e4` blob → identical 20 undeclared, rc=1. The failure is byte-for-byte the allowlist's pre-existing scope (only node/npm/pnpm/yarn/git/cargo/echo/rig listed; `pip`/`bash`/`make` never were) and is word-identical with and without the `referencing` fix — the fix contributes zero findings. Clean-checkout CI is unaffected: `git checkout` stages nothing, `--staged` short-circuits to `no staged manifests; zero undeclared`, rc=0, and the committed-tree verify leg is 39/0 (R1). Arguing otherwise would require claiming CI lints staged blobs, which it does not. A staged-workflow allowlist gap is a legitimate future-work note for the manifest-closure owner, not a rework-2 finding. All staging undone; worktree restored byte-identical (`cmp` clean) before this report was written.

### Skips (explicit)

- `make test` not re-run by this auditor: delta is one CI pip-line word + one guard-import word + docs appendices (no generator/runtime/catalog/V-gate/test code touched); full suite green at 634/0 per QA baseline and the directly affected gate re-ran green (R1). Skipped with reason.
- `openspec validate <change-id>`: N/A — no active change-id (`openspec/changes/` holds only `archive/`); canonical-spec health unchanged since rework-1 (R2-equivalent covered by QA's `openspec list --specs` green).
- `gh`-side re-verification of PR #135 / main-failure logs: not re-fetched; the implementation appendix's `gh` citations are corroborated by the locally proven packaging mechanism (transitive-only arrival + pip no-op), and CI-behavior claims are the coordinator's merge-time concern, not this delta's correctness gate.
- Never committed; never printed secrets.

VERDICT: PASS

## Rework-3 re-audit (2026-10-29, branch fix/bump-075-r3 @ 33e012a, role agency-drift-guard)

- **Role:** independent adversarial auditor; fixed no code; committed nothing. Prior verdicts above re-issued, not copied: every claim below re-verified against current worktree files with commands I ran myself.
- **Start state:** `git status --short` clean (empty output before any audit command). Revs seen: `14f4ee8` (rework-2 drift-guard VERDICT) → `8246141` (rework fix) → `33e012a` (QA re-verification) = HEAD.
- **Rework delta (`git diff 14f4ee8 HEAD --stat`):** exactly 4 files, 81 insertions, 1 deletion — `.github/workflows/docker-release.yml` (2 +/-, 1 line), `scripts/verify-rigs.sh` (5 +/-, all insertions), `docs/reports/bump-075-implementation.md` (+54), `docs/reports/bump-075-qa.md` (+21). Functional delta is exactly the pip floor + the preamble block; docs diffs are pure tail appends (hunks anchored `@@ -209,3 +209,57 @@` / `@@ -79,3 +79,24 @@`, zero deletion lines). No hunk beyond pip floor + preamble block + docs appendices exists — minimality HOLDS.

### Hunk-by-hunk audit (full `git diff 14f4ee8 HEAD` read from disk, `-U0` confirmed single-hunk per functional file)

- **H1 — workflow pip line (`docker-release.yml:53`):** `pip install --quiet pyyaml jsonschema referencing` → `pip install --quiet pyyaml "jsonschema>=4.18" referencing`. Single-line hunk; `-U0` shows this is the only hunk in the file. All other steps byte-identical (checkout SHA pin `d23441a48e516b6c34aea4fa41551a30e30af803`, audit_loop leg, guard-profiles triple, bwrap install, and the entire `build`/`smoke` jobs untouched — verified by the single-hunk diff, not by summary). Quoting is correct: double-quoted `"jsonschema>=4.18"` passes YAML `safe_load` as one scalar (proven R2 below) and survives shell intact; the bare-name style of the line is otherwise kept, no exact pin invented. YAML-schema risk: NONE — parses OK, `jobs` keys intact (`verify-fleet`/`build`/`smoke`), verify-fleet step count 6, V27 UniqueKey parse green inside the 39/0 run.
- **H2 — preamble floor block (`scripts/verify-rigs.sh:40-43`):** 4-line fail-closed check inserted after the `RUNNER` selection (lines 33-38) and before the heredoc at line 45 — NOT in any V-gate block. Uses the effective `"${RUNNER[@]}"` interpreter, `importlib.metadata.version` (not deprecated `jsonschema.__version__`), `[0-9]+` regex with no backslash-escape fragility inside bash double quotes, major/minor tuple compared against `(4,18)`; on <4.18 (or missing metadata) prints the actionable `requires jsonschema>=4.18 for Draft202012Validator(registry=...)` stderr message and exits 1. Append-only V-gates HOLDS — zero gate text touched (`git diff 14f4ee8 HEAD | grep -E 'V[0-9]'` returns no matches), SUMMARY frozen at 39 (confirmed by re-run).
- **H3/H4 — report appendices:** implementation.md +54 and qa.md +21, both tail-appended sections, zero deletions. Content verified accurate against the tree (workflow line 53, preamble lines 40-43, `registry=` call sites at verify-rigs.sh:924 and 2380-2381 all re-grepped by me — strings match; the 4.17.3-reproduces-TypeError / 4.18.6-constructs-OK mechanism claim is consistent with the locally proven floor behavior below).

### Discipline verdicts

- **One Rule:** PASS — `git diff 14f4ee8 HEAD --name-only -- specs/ rigs/ rosters/ registry/ fleet/ schemas/ scripts/generate-rigs.py` empty (sole `scripts/` touch is the preamble, not the generator).
- **Frozen-archive integrity:** PASS — `git diff 14f4ee8 HEAD --name-only -- archive/ openspec/` empty (no active change-id touched, archived package untouched).
- **Secrets / no-local-paths hygiene on added lines:** PASS — added-line scan for `ghp_|gho_|sk-ant-|AKIA|Bearer|/home/|/Users/|secrets/|.key|.pat|password|token` returns zero hits. Appendix worktree references are repo-relative (`.lane/trees/bump-075-r3`), never machine-absolute.
- **`Refs`-only discipline:** PASS — no `Closes #`/`Fixes #`/`Resolves #` in the delta (bump ledger wave; nothing to close).

### Re-ran myself (exit codes observed, not quoted)

| # | Command (inside worktree) | Observed result | rc |
|---|---|---|---|
| R1 | `./scripts/verify-rigs.sh --check-only` (serial, post-restore) | `SUMMARY: 39 checks passed, 0 failed` | 0 |
| R2 | `git diff 14f4ee8 HEAD --stat` | 4 files, 81 insertions, 1 deletion | 0 |
| R3 | `python3 -c "yaml.safe_load(open('.github/workflows/docker-release.yml'))"` | `YAML OK`, 3 jobs, 6 verify-fleet steps, pip line carries `"jsonschema>=4.18"` | 0 |
| R4 | `bash -n scripts/verify-rigs.sh` | syntax OK (no output) | 0 |
| R5 | Added-line secret/local-path scan + Refs-only scan | zero hits both | — |
| R6 | Protected-path diff (`specs/ rigs/ rosters/ registry/ fleet/ schemas/ archive/ openspec/`) | empty | 0 |
| R7 | Preamble edge matrix, exact line-40 comparison logic, tree untouched: `4.17.3`→reject, `3.2.0`→reject, `4.9`→reject, single-component `4`→reject, `4.18.0`→accept, `4.26.0`→accept, `4.18.0.post1`→accept, `4.18rc1`→accept | all as listed | 1/1/1/1/0/0/0/0 |
| R8 | Floor fail-closed on missing metadata (`version('no-such-pkg-xyz')` raises; floor expression rejects) | reject | 1 |
| R9 | `uv run --no-project --with pyyaml --with jsonschema python3 -c "import referencing"` | `uv-jsonschema: 4.26.0`, `referencing resolves OK` | 0 |

### Own sabotage probe (DG-R3, RED→GREEN, restore proof — distinct from QA's R3-8 floor-tamper-in-copy probe and from all prior V13/V18 pin probes by fresh backup/sha on this HEAD)

- **DG-R3 — V18 version gate (topical: proves the preamble insert blunts no gate):** byte backup of `scripts/verify-rigs.sh` to `/tmp` (sha256 `2e8adbc4…9258e45` both copies) → sabotage line 2416 `_verm18.group(0) != "0.7.5"` → `"0.7.4"` (single-line `sed`, `git diff --stat` shows that 1 line only) → verify RED `[FAIL] V18/#98: host rig --version is not 0.7.5 (got 0.7.5 (b57c4da3))`, `SUMMARY: 38 checks passed, 1 failed`, rc=1 → `git checkout -- scripts/verify-rigs.sh` + `cmp` vs backup → **BYTE-IDENTICAL** (sha256 `2e8adbc4…9258e45` both, backup removed) → verify GREEN `SUMMARY: 39 checks passed, 0 failed`, rc=0.
- **Why V18 and not a second floor-tamper:** QA already proved the floor rejects when raised to `(99,0)`; repeating the same tamper would prove nothing new. DG-R3 instead proves the property the floor must preserve — every downstream V-gate still fails loudly when its pinned truth is disturbed. Post-probe: `git status --short` clean, `git stash list` empty.

### Addressed question — does the preamble floor check itself introduce any new failure mode for supported envs? REFUTED, with evidence

- **uv-fallback path: SAFE, proven.** The check runs AFTER `RUNNER` selection (lines 33-38 → 40) and execs through `"${RUNNER[@]}"`, i.e. it tests the EFFECTIVE interpreter, not a hardcoded `python3`. Two cases: (a) system python lacks `referencing` → `RUNNER` becomes `uv run … --with jsonschema`, a fresh env that R9 proves resolves jsonschema 4.26.0 + `referencing` — floor always passes there, no false RED; (b) system python has old jsonschema 4.17 + `referencing` (the CI failure mode) → first guard succeeds so `RUNNER` stays system python, and the floor correctly rejects 4.17 early with an actionable message instead of the later cryptic `TypeError: … 'registry'`. Strictly better, no new mode.
- **Missing `importlib.metadata`: NOT a supported-env failure.** stdlib since Python 3.8; supported envs (ubuntu-24.04, local 3.15.1 observed) always have it (R8 pre-check imports OK). If it were ever absent, `from importlib.metadata import version` raises ImportError → non-zero → shell `if !` triggers → stderr message + `exit 1` fail-closed. A missing stdlib module can never yield a silent GREEN.
- **Missing version metadata (package not found): fail-closed, proven.** `version('no-such-pkg-xyz')` raises (rc=1); the floor expression inherits the non-zero exit → reject (R8, rc=1). Uninstallable/broken envs fail loudly at the preamble, never slip through to a misleading gate result.
- **Odd version strings (`4.18rc1`, `.post1`, single-component): NO supported-env impact, evidence in R7.** `[0-9]+` prefix-tuple parsing accepts `4.18rc1` (→ `(4,18)`) and `4.18.0.post1`, rejects single-component `4` fail-closed. `4.18rc1` acceptance is harmless: (i) pip never installs an `rc` under the workflow's `>=4.18` specifier unless explicitly pinned with `==`, which the workflow does not do — CI always resolves a final release; (ii) even in a hypothetical rc1 env, the worst case is the floor passing and the later `Draft202012Validator(registry=...)` raising exactly as before the floor — the pre-existing failure, not a new silent-green. No false RED exists for any real jsonschema release (all PyPI releases are `X.Y.Z` finals; every `>=4.18` final accepts, every `<4.18` final rejects — matrix confirms the boundary `4.17.3`→reject / `4.18.0`→accept).
- **`set -u` / quoting: SAFE.** `RUNNER` is unconditionally assigned at line 33 before the check, so `"${RUNNER[@]}"` cannot trip `set -u`; array expansion preserves the multi-word `uv run …` form without word-splitting. `bash -n` clean (R4), live 39/0 run exercises the exact line green (R1).

### Skips (explicit)

- `make test` not re-run by this auditor: delta is one CI pip-line specifier + a preamble-only floor check + docs appendices (no generator/runtime/catalog/V-gate/test code touched); full suite green at 634/0 per QA baseline and the directly affected gate re-ran green 39/0 (R1). Skipped with reason.
- `openspec validate <change-id>`: N/A — no active change-id (`openspec/changes/` holds only `archive/`); canonical-spec health unchanged since rework-1 (covered by QA's `openspec list --specs` green).
- `gh`-side re-verification of PR #135 CI logs: not re-fetched; the floor's correctness is proven locally (R7-R9) and the CI-behavior claim is the coordinator's merge-time concern, not this delta's correctness gate.
- Never committed; never printed secrets.

VERDICT: PASS

## Rework-4 re-audit (2026-10-29, branch fix/bump-075-r4 @ 205cf01, role agency-drift-guard)

- **Role:** independent adversarial auditor; fixed no code; committed nothing. Prior verdicts above re-issued, not copied: every claim below re-verified against current worktree files with commands I ran myself.
- **Start state:** `git status --short` clean (empty output before any audit command). Revs seen: `bea4d16` (rework-3 drift-guard VERDICT) → `728662c` (rework fix) → `205cf01` (QA re-verification) = HEAD.
- **Mandate note:** plan's 3-cycle rework budget was spent, but the user explicitly authorized continued fixes until PR #135 CI passes — this Rework-4 proceeds under that mandate (same basis recorded in the implementation appendix).
- **Rework delta (`git diff bea4d16 HEAD --stat`):** exactly 3 files, 70 insertions, 1 deletion — `.github/workflows/docker-release.yml` (1+/1-, one line moved), `docs/reports/bump-075-implementation.md` (+48), `docs/reports/bump-075-qa.md` (+21). Fix commit alone (`bea4d16..728662c`): 2 files, 49 insertions, 1 deletion (workflow move + implementation appendix); the third file is the QA re-verification appendix (uncommitted-by-qa equivalent, committed as `205cf01`). No hunk beyond the moved block + docs appendices exists — minimality HOLDS.

### Hunk-by-hunk audit (full `git diff bea4d16 HEAD` read from disk, `-U0` confirmed)

- **H1 — workflow verify-fleet reorder (`docker-release.yml`):** `-U0` shows exactly one `+` line (`+      - run: sudo apt-get update && sudo apt-get install -y --no-install-recommends bubblewrap && bwrap --version` at new line 54) and exactly one `-` line (identical string removed from old line 60). Byte-identical string, pure move, zero new steps, zero new content, zero deleted content. YAML-parsed step lists prove preservation: OLD 6 steps / NEW 6 steps, `sorted(old)==sorted(new)` TRUE; only indices change (OLD `verify-idx=2 apt-get-idx=5` → NEW `apt-get-idx=2 verify-idx=3`; full NEW order: checkout / pip-install / apt-get-bubblewrap / verify / audit-self-test / guard-profiles). All other jobs byte-identical: `build`/`smoke` hunks absent (`grep -E 'build|smoke|matrix|target|container'` over the workflow diff returns no lines), checkout SHA pin `d23441a48e516b6c34aea4fa41551a30e30af803`, pip line `"jsonschema>=4.18"`, guard-profiles triple all untouched.
- **H2/H3 — report appendices:** implementation.md hunk anchored `@@ -263,3 +263,51 @@` (+48), qa.md hunk anchored `@@ -100,3 +100,24 @@` (+21), both tail-appended sections. `git diff bea4d16 HEAD -- docs/ | grep '^-' | grep -v '^---'` returns zero content-deletion lines — pure append. Content verified accurate against the tree (fail-closed cite `scripts/verify-rigs.sh:1707-1711` re-read by me; V27 order-independence claim `scripts/verify-rigs.sh:3032-3034` re-read by me; host bwrap `/usr/bin/bwrap` `0.13.1` confirmed by me).
- **V-gate text note (adversarial clarity):** a naive `git diff bea4d16 HEAD | grep -E 'V[0-9]'` returns 3 hits — all are prose mentions of `V22–V27`/`V27`/`[FAIL] tool-existence` inside the docs appendices, NOT gate-code edits. `git diff bea4d16 HEAD --name-only -- scripts/` is EMPTY (no generator/runtime/catalog/V-gate code touched); SUMMARY frozen at 39, confirmed by re-run. Zero V-gate text touched HOLDS.

### Discipline verdicts

- **One Rule:** PASS — `git diff bea4d16 HEAD --name-only -- specs/ rigs/ rosters/ registry/ fleet/ schemas/ scripts/generate-rigs.py` empty (sole functional touch is the workflow step order, not the generator or generated leaves).
- **Frozen-archive integrity:** PASS — `git diff bea4d16 HEAD --name-only -- archive/ openspec/` empty (no active change-id touched, archived package untouched).
- **Secrets / no-local-paths hygiene on added lines:** PASS — added-line scan for `ghp_|gho_|sk-ant-|AKIA|Bearer|/home/|/Users/|secrets/|.key|.pat|password|token` returns zero hits. Appendix worktree references are repo-relative (`.lane/trees/bump-075-r4`), never machine-absolute.
- **`Refs`-only discipline:** PASS — no `Closes #`/`Fixes #`/`Resolves #` in the delta (bump ledger wave; nothing to close).

### Workflow judgment (all steps preserved, just reordered; YAML + V27 UniqueKey risk)

- **YAML risk: NONE.** `yaml.safe_load` parses OK; jobs keys intact (`verify-fleet`/`build`/`smoke`); verify-fleet step count 6; quoting/indent of the moved line unchanged (it moved as a whole line, so no new parse edge).
- **V27 UniqueKey risk: NONE, proven green.** V27 asserts only that SOME verify-fleet `run:` step contains `"bubblewrap"` (line 3033: `if not any("bubblewrap" in _s27 ...)`) — order-independent by construction — plus the UniqueKey duplicate-key parse (lines 3017-3026) and the Dockerfile bubblewrap assertions. Live 39/0 run shows `V27/overhaul-a M3 green` (R-row below). A reorder cannot trip UniqueKey (no key added/removed/duplicated) and cannot trip the substring assertion (string still present exactly once).

### Re-ran myself (exit codes observed, not quoted)

| # | Command (inside worktree) | Observed result | rc |
|---|---|---|---|
| R1 | `./scripts/verify-rigs.sh --check-only` (serial, post-restore) | `SUMMARY: 39 checks passed, 0 failed` | 0 |
| R2 | `git diff bea4d16 HEAD --stat` | 3 files, 70 insertions, 1 deletion | 0 |
| R3 | `python3 -c "yaml.safe_load(open('.github/workflows/docker-release.yml'))"` | YAML OK, 3 jobs, 6 verify-fleet steps, `apt-get-idx=2 verify-idx=3` | 0 |
| R4 | Old-vs-new step-set comparison (YAML-parsed, `git show bea4d16:` vs tree) | 6 vs 6, sets equal TRUE, OLD `verify-idx=2 apt-get-idx=5` documents the bug | 0 |
| R5 | Added-line secret/local-path scan + Refs-only scan | zero hits both | — |
| R6 | Protected-path diff (`specs/ rigs/ rosters/ registry/ fleet/ schemas/ archive/ openspec/ scripts/`) | empty | 0 |
| R7 | Fail-closed cite `sed -n '1700,1715p' scripts/verify-rigs.sh` + workflow `HERETEK_ALLOW_NO_BWRAP` grep | `which("bwrap") is None` → note-mode only when `HERETEK_ALLOW_NO_BWRAP=1`, else `fail(...)`; workflow sets no such var (absent, correct — CI verifies-for-real) | — |
| R8 | Host bwrap | `/usr/bin/bwrap`, `bubblewrap 0.13.1` | 0 |

### Own sabotage probe (DG-R4, RED→GREEN, restore proof — distinct from QA's R4-6/R4-7 old-order-in-/tmp-copy proof, which touched no tree file)

- **DG-R4 — V27 Dockerfile bubblewrap gate (topical: proves the reorder blunts no bubblewrap gate):** byte backup of `docker/Dockerfile` to `/tmp` (sha256 `9e309ea4…85b8b185` both copies) → sabotage `bubblewrap` → `no-such-pkg-xyz` on line 94 (single-word `sed`, `git diff --stat` shows that 1 line only) → verify RED `[FAIL] V27/overhaul-a: docker/Dockerfile must install bubblewrap`, `SUMMARY: 39 checks passed, 1 failed`, rc=1 → `git checkout -- docker/Dockerfile` + `cmp` vs backup → **BYTE-IDENTICAL** (sha256 `9e309ea4…85b8b185` both, backup removed) → verify GREEN `SUMMARY: 39 checks passed, 0 failed`, rc=0.
- **Why the Dockerfile leg and not a repeat order-tamper:** QA already proved the OLD order is broken (parsed idx) and the NEW order is fixed — repeating that tamper would prove nothing new. DG-R4 instead proves the property the reorder must preserve: every bubblewrap gate still fails loudly when its pinned truth is disturbed. Post-probe: `git status --short` clean, `git stash list` empty.

### Addressed question — could moving apt-get earlier break the `build`/`smoke` jobs or the guard-profiles step in any way? AGREE it cannot, with evidence (no refutation found)

- **`build`/`smoke` jobs: CANNOT be affected — separate runners by construction.** Each job declares its own `runs-on: ubuntu-24.04` (`verify-fleet` needs: none, `build` needs: verify-fleet, `smoke` needs: build); GitHub Actions provisions a fresh VM per job, so `verify-fleet`'s `apt-get install bubblewrap` leaves zero filesystem state for `build`/`smoke`. Corroborated by the diff: zero `build`/`smoke` lines touched. `smoke` additionally runs inside the published container image (`container: image: ghcr.io/...`), where host apt state is definitionally irrelevant. No cross-job contamination vector exists for a step reorder within `verify-fleet`.
- **guard-profiles step (runs after, same job): additive-only, proven independent.** The moved step installs one package (`bubblewrap`) and prints its version — it removes nothing, exports no env vars, writes no repo files. `guard-profiles` (`Makefile:55-65`) is a pure shell `case` over `$(SIDECAR_PROFILES)` refusing `mobile`+`devsec`/`web-research` co-scheduling; its body references no `bwrap`/`bubblewrap`/apt state (grep over `Makefile` guard target: no hits). A package install earlier in the same runner cannot change a string-match guard's outcome — and the step's own pass/fail semantics are unchanged (it still runs exactly once, same command). Worst case (apt mirror flake) fails the workflow at the apt step instead of later — fail-closed, strictly earlier signal, never a silent green.
- **verify/audit legs (also run after): strictly improved, not regressed.** Both require bwrap present (verify fail-closed at `:1707-1711`; audit self-test unaffected by bwrap). Installing before them converts a deterministic RED (`38/1 bwrap not found`) into the proven GREEN (`39/0`), which is the entire purpose of the fix.

### Skips (explicit)

- `make test` not re-run by this auditor: delta is a workflow step reorder + docs appendices (no generator/runtime/catalog/V-gate/test code touched); full suite green at 634/0 per QA baseline and the directly affected gate re-ran green 39/0 (R1). Skipped with reason.
- `openspec validate <change-id>`: N/A — no active change-id (`openspec/changes/` holds only `archive/`); canonical-spec health unchanged since rework-1.
- `gh`-side re-verification of PR #135 CI logs: not re-fetched; the reorder's correctness is proven locally (R3-R4 step-set equality + R1 39/0 + R8 host bwrap + DG-R4 gate still armed) and CI-behavior claims are the coordinator's merge-time concern, not this delta's correctness gate.
- Never committed; never printed secrets.

VERDICT: PASS

## Rework-5 re-audit (2026-10-29, branch fix/bump-075-r5 @ 7497adc, role agency-drift-guard)

- **Role:** independent adversarial auditor; fixed no code; committed nothing. Prior verdicts above re-issued, not copied: every claim below re-verified against current worktree files with commands I ran myself.
- **Start state:** `git status --short` clean (empty output before any audit command, rc=0). Revs seen: `1f23bf2` (rework-4 drift-guard VERDICT) → `314e5a5` (rework fix) → `7497adc` (QA re-verification) = HEAD.
- **Mandate note:** plan's 3-cycle rework budget was spent, but the user explicitly authorized continued fixes until PR #135 CI passes — this Rework-5 proceeds under that standing mandate (same basis recorded in the implementation appendix).
- **Rework delta (`git diff 1f23bf2 HEAD --stat`):** exactly 3 files, 67 insertions, 2 deletions — `.github/workflows/docker-release.yml` (2+/2-, two literal lines), `docs/reports/bump-075-implementation.md` (+47), `docs/reports/bump-075-qa.md` (+18). Fix commit alone (`1f23bf2..314e5a5`): workflow + implementation appendix; the third file is the QA re-verification appendix (committed as `7497adc`). No hunk beyond the 2 literal lines + docs appendices exists — minimality HOLDS.
- **Docs-appendix purity:** `git diff 1f23bf2 HEAD -- docs/ | grep '^-' | grep -v '^---'` returns zero content-deletion lines — pure append. Both hunks are tail-anchored sections. No dated-record rewrite, no history edit.

### Hunk-by-hunk audit (full `git diff 1f23bf2 HEAD` read from disk, `-U0` confirmed exactly 2 changed lines)

- **H1 — env IMAGE_NAME (`docker-release.yml:45`):** `IMAGE_NAME: ${{ github.repository }}` → `IMAGE_NAME: heretek-ai/heretek-rigs # ghcr.io requires lowercase repository names`. Keeps the file's trailing-comment style. This is the load-bearing fix for the build tags (lines 91-92) and the attest `subject-name` (line 100), which both consume `${{ env.IMAGE_NAME }}` — one literal heals all three consumers. Verified: OLD `:45` used the `${{ github.repository }}` template (no literal `Heretek-AI` in file; uppercase enters via runtime resolution — the `Heretek-AI` org casing corroborated via remote URL — matching CI's `repository name must be lowercase` error); NEW literal has `any(c.isupper())` False, proven programmatically.
- **H2 — smoke container image (`docker-release.yml:114`):** `image: ghcr.io/${{ github.repository }}:sha-...` → `image: ghcr.io/heretek-ai/heretek-rigs:sha-...`. Same tag template, only the repository path lowercased. This literal CANNOT be fixed via `env.IMAGE_NAME` or a `GITHUB_ENV` lowercasing step — `container.image` resolves before steps run — so a second hardcoded literal is the correct minimal form, not scope creep. Verified: no other `github.repository` occurrence remains in the file (`grep` over OLD showed `:45` + `:114` only; NEW shows zero).
- **H3/H4 — report appendices:** implementation.md +47 and qa.md +18, tail-appended, zero deletions. Content verified accurate against the tree (OLD `:45`/`:114` template strings, NEW literals, `verify-rigs.sh:3028-3036` V27 cite, YAML re-parse — all re-checked by me; QA's nuance that the OLD file contains no literal `Heretek-AI` string is honest and correct).

### Discipline verdicts

- **One Rule:** PASS — `git diff 1f23bf2 HEAD --name-only -- specs/ rigs/ rosters/ registry/ fleet/ schemas/ scripts/generate-rigs.py` empty; `scripts/` diff is 0 lines (no generator/runtime/catalog/V-gate code touched).
- **Frozen-archive integrity:** PASS — `git diff 1f23bf2 HEAD --name-only -- archive/ openspec/` empty (no active change-id touched, archived package untouched).
- **Zero V-gate text:** HOLDS — `git diff 1f23bf2 HEAD -- .github/ scripts/ | grep -E 'V[0-9]'` returns zero hits. A naive docs-inclusive grep returns 2 prose mentions of `V27` inside the appendices (implementation cite + QA table row) — these are report prose, NOT gate-code edits. `SUMMARY` frozen at 39, confirmed by re-run.
- **Secrets / no-local-paths hygiene on added lines:** PASS — added-line scan for `ghp_|gho_|sk-ant-|AKIA|Bearer|/home/|/Users/|secrets/|.key|.pat|password|token` returns zero hits. Appendix worktree references are repo-relative (`.lane/trees/bump-075-r5`), never machine-absolute.
- **`Refs`-only discipline:** PASS — no `Closes #`/`Fixes #`/`Resolves #` in the delta (bump ledger wave; nothing to close).

### Workflow judgment (all steps/jobs preserved; fork caveat; attest binding)

- **Steps/jobs preserved:** YES, proven by YAML-parsed comparison of OLD (`git show 1f23bf2:`) vs NEW tree — jobs `build/smoke/verify-fleet` identical, step counts 6/6/5 identical, `needs` chain (`build→verify-fleet`, `smoke→build`) identical, all `if: github.event_name != 'pull_request'` conditionals intact (`:75` login, `:87` push flag, `:98` attest, `:107` smoke job). `-U0` diff shows exactly the 2 literal lines; zero step bodies touched. YAML-schema risk: NONE — `safe_load` parses OK.
- **Hardcode safety + fork caveat (explicit):** the hardcode is SAFE for this repo's CI because every registry-mutating or registry-reading consumer is gated on non-PR events — `push: ${{ github.event_name != 'pull_request' }}` (`:87`), attest `if` (`:98`), smoke-job `if` (`:107`), login `if` (`:75`). PR CI (including PR #135 and any fork PR) therefore exercises only `verify-fleet` + a no-push `build`, neither of which resolves the literal against a foreign namespace with write effects. **Fork caveat (real, stated plainly):** a fork that pushes to its own `main` would now build+push to `heretek-ai/heretek-rigs` (upstream namespace → permission denied on push) and its `smoke` job would pull the upstream image, not its own. Upstream `docker-release.yml` files commonly hardcode the canonical repo path for exactly the lowercase reason, but a fork must parameterize or revert these two literals to run its own release pipeline. For THIS repo's mandate (unblock PR #135 CI on `Heretek-AI/heretek-rigs`), the hardcode is the correct minimal fix; the fork cost is documented here, not hidden.
- **Attest subject-name/digest binding:** AGREE it cannot break, with reason. The attest step (`:97-102`) binds `subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}` to `subject-digest: ${{ steps.push.outputs.digest }}`. The digest expression is untouched; only the subject *string* is renamed — and it is renamed to exactly the tag prefix the `build` step pushes (`:91-92` use the same `${{ env.IMAGE_NAME }}`), so subject and pushed artifact remain mutually consistent. Previously the subject-name would have resolved to the uppercase (registry-invalid) name; the rename strictly improves binding validity. No key, identity, or digest-plumbing change exists in the diff.

### Re-ran myself (exit codes observed, not quoted)

| # | Command (inside worktree) | Observed result | rc |
|---|---|---|---|
| R1 | `./scripts/verify-rigs.sh --check-only` (pre-probe) | `SUMMARY: 39 checks passed, 0 failed` | 0 |
| R2 | `./scripts/verify-rigs.sh --check-only` (post-probe-restore) | `SUMMARY: 39 checks passed, 0 failed` | 0 |
| R3 | `git diff 1f23bf2 HEAD --stat` | 3 files, 67 insertions, 2 deletions | 0 |
| R4 | YAML-parsed OLD-vs-NEW structure (`git show 1f23bf2:` vs tree) | jobs equal, steps 6/6/5 both, needs/ifs intact | 0 |
| R5 | Lowercase assert on NEW literals (`any(c.isupper())`) | both False → `LOWERCASE-ASSERT: GREEN` | 0 |
| R6 | Added-line secret/local-path scan + Refs-only scan + functional V-gate scan | zero hits all three | — |
| R7 | Protected-path diff (`specs/ rigs/ rosters/ registry/ fleet/ schemas/ archive/ openspec/ scripts/`) | empty | 0 |

### Own sabotage probe (DG-R5, RED→GREEN, restore proof — distinct from QA's R5-1..R5-5, which never sabotaged the tree; QA's R5-4 was read-only `git show | grep`)

- **DG-R5 — fix-property inversion (topical to the touched literals):** byte backup of `.github/workflows/docker-release.yml` (sha256 `aa78791b…12cf4` both copies) → sabotage both literals `heretek-ai` → `Heretek-AI` (in-tree `sed`, reproducing the CI failure casing) → lowercase-assert RED (`AssertionError: LOWERCASE-ASSERT: RED (uppercase present)`, `IMAGE_NAME upper=True`, `smoke upper=True`), rc=1 → `git checkout -- .github/workflows/docker-release.yml` + `cmp` vs backup → **BYTE-IDENTICAL** (sha256 `aa78791b…12cf4` both, backup removed) → lowercase-assert GREEN (`heretek-ai/heretek-rigs`), rc=0, plus verify GREEN 39/0 (R2).
- **Honesty note:** local `verify-rigs.sh` is case-insensitive by design (no gate validates ghcr naming — V27 asserts bubblewrap-string + UniqueKey parse + smoke-container-is-dict only), so the RED is demonstrated by the property assert, not by verify. This is non-vacuous: it proves the exact fixed property (lowercase literals) fails loudly when inverted and holds when restored, rather than asserting on an unrelated gate. Post-probe: `git status --short` clean, `git stash list` empty, `git diff 1f23bf2 HEAD --stat` unchanged (3 files, 67/2).

### Skips (explicit)

- `make test` not re-run by this auditor: delta is two workflow image-name literals + docs appendices (no generator/runtime/catalog/V-gate/test code touched — `scripts/` diff 0 lines); full suite green at 634/0 per QA baseline and the directly affected gate re-ran green 39/0 twice (R1/R2). Skipped with reason.
- `openspec validate <change-id>`: N/A — no active change-id (`openspec/changes/` holds only `archive/`); canonical-spec health unchanged since rework-1.
- `gh`-side re-verification of PR #135 CI logs: not re-fetched; the lowercase mechanism is proven locally (R5 + DG-R5 RED→GREEN) and CI-behavior claims are the coordinator's merge-time concern, not this delta's correctness gate.
- Never committed; never printed secrets.

VERDICT: PASS
