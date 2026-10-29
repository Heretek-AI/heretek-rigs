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
