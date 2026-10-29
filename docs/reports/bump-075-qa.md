# QA report — Wave 1 `2026-10-29-bump-075` (0.7.5 bump-eval ledger)

- **Stage:** Wave 1 `2026-10-29-bump-075` · **Branch:** `feat/bump-075` @ `d158dc7` · **Worktree:** `.lane/trees/bump-075`
- **Role:** agency-qa · **Date (UTC):** 2026-10-29 · **Unity binding:** none
- **Inputs read from disk (trusted nothing, verified everything):** five-wave remediation plan (Wave 1 section), `openspec/changes/2026-10-29-bump-075/` (proposal.md, design.md, tasks.md, specs/bump/spec.md), `AGENTS.md`, `docs/reports/bump-075-implementation.md`, `docs/sprints/CLI-0.7.5-BUMP.md`
- **Pre-state:** `git status --short` clean, `git log --oneline -2` = `d158dc7 feat(bump-075): implement stage requirements` / `c1da1fb`
- **Secrets:** none printed, logged, or committed (version strings plus tarball sha256 only). Nothing committed by qa.

## Acceptance compound — real outputs

| # | Check (inside worktree) | Real output | rc | Result |
|---|---|---|---|---|
| 1 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 39 checks passed, 0 failed` (V13 green on `ARG OPENRIG_VERSION=0.7.5`, V18 green on installed 0.7.5; no V-gate added or renamed) | 0 | PASS |
| 2 | `make test` | `Ran 634 tests in 106.123s — OK` (634 or more, 0 failures) | 0 | PASS |
| 3 | `python3 scripts/audit_loop.py --self-test` | `SELF-TEST PASSED` | 0 | PASS |
| 4 | `python3 scripts/generate-rigs.py --check-idempotent` | `idempotence check passed (two consecutive runs byte-identical)`; regen side-effect dirtied 35 generated leaves (queue-handoff parking prose plus provenance) — inspected (exactly the deferred 0.7.5 content, confirming the no-regen disposition) and reverted via checkout, status clean | 0 | PASS |
| 5 | `openspec validate 2026-10-29-bump-075` | `Change '2026-10-29-bump-075' is valid` | 0 | PASS |
| 6 | `rig --version` | `0.7.5 (b57c4da3)` (matches ledger plus peeled tag claim) | 0 | PASS |
| 7 | AGENTS.md scope vs merge-base c1da1fb | `1 file changed, 2 insertions(+), 1 deletion(-)` (3 lines, limit 15) | 0 | PASS |
| 8 | Changed-set scope (diff c1da1fb to HEAD) | 14 files: exactly the 8 true-pin files plus ledger plus 4 change-dir files plus implementation report. No generator inputs, no generated leaves, no dated-record rewrites | — | PASS |
| 9 | Ledger claims (REQ-BUMP3) | Full sha `22d67c2c…bb9754` present with two-fetch evidence, version `0.7.5 (b57c4da3)` present, 8 true-pin files listed, tarball-diff disposition plus verify output plus rollback present | — | PASS |
| 10 | Stub scan over change plus ledger | no matches (grep rc=1 means clean) | — | PASS |
| 11 | T0 spec-file gate (4-path ls) | all 4 files list | 0 | PASS |

## Red-proof summary (8 probes; full commands plus rc in `docs/evidence/bump-075/red-proofs.log`)

| Probe | Sabotage | RED evidence | Restore to GREEN |
|---|---|---|---|
| A — V18 version gate | pin expects 0.7.4 | FAIL V18, 38/1, rc=1 | byte-identical, 39/0 rc=0 |
| B — V13 Dockerfile gate | ARG set to 0.7.4 | FAIL V13, 38/1, rc=1 | byte-identical, 39/0 rc=0 |
| C — ledger sha claim | sha replaced with zeros | sha grep rc=1 | byte-identical, grep rc=0 |
| D — openspec validate | spec.md replaced with garbage | delta errors, rc=1 | byte-identical, valid rc=0 |
| E — suite anti-vacuity | findings gate inverted | FAILED (failures=1) | byte-identical, OK rc=0 |
| F — audit self-test | fleet.yaml moved away | rc=1 | moved back, SELF-TEST PASSED rc=0 |
| G — AGENTS.md scope | 20 lines appended | 24 lines vs base, rc=1 | byte-identical, 3 lines rc=0 |
| H — T0 file gate | tasks.md moved away | ls rc=2 | moved back, ls rc=0 |

- **Vacuous checks:** none — every acceptance check turned RED under targeted sabotage and GREEN on byte-identical restore.
- **Noted validator boundary (not a wave defect):** `openspec validate` enforces delta-section and scenario presence only — demoting a Requirement header, removing proposal.md, or removing tasks.md each still validates rc=0. The wave ships all four files (T0 ls gate covers presence), but a future wave should not rely on `openspec validate` alone to catch requirement deletion.
- **Skips and failures:** none. No baseline failure (tree was green before sabotage). No production or test code left modified: final `git status --short` shows only the two evidence files, `git stash list` empty, post-probe verify 39/0 rc=0.

## Per-criterion results

- Proposal acceptance 1 (`rig --version` shows 0.7.5): PASS (check 6 plus Probe A proves the gate behind it).
- Proposal acceptance 2 (ledger with version plus two-fetch SHA plus verify output plus 8 pins plus deferred notes): PASS (check 9 plus Probe C).
- Proposal acceptance 3 (verify 39/0, idempotent rc=0, self-test PASSED, make test at least 634 with 0 failed): PASS (checks 1–4 plus Probes A, B, E, F).
- Proposal acceptance 4 (`openspec validate` rc=0): PASS (check 5 plus Probe D, with noted boundary).
- Proposal acceptance 5 (red-proof pin-0.7.4 goes RED, restore goes GREEN): PASS (Probe A; extended to 8 probes).
- Plan Wave-1 acceptance (compound 39/0 plus 634 or more plus ledger two-agent sha plus `rig --version` 0.7.5 plus validate rc=0 plus pin-string-mismatch RED to GREEN): PASS on all conjuncts. (Probe A proves V18 pin-string `0.7.4`→RED/restore→GREEN; fetched-tarball-digest vs expected-digest comparison is evidenced by the ledger's two independent fetches plus 0.7.4 control re-fetch, not by digest-corruption sabotage — see red-proofs.log Probes A/C.)
- AGENTS.md surgical scope (15 lines or fewer): PASS (3 lines).

## Rework-1 re-verification (2026-10-29, branch fix/bump-075-r1 @ 0381977, role agency-qa)

- **Pre-state:** `git status --short` clean, HEAD `0381977`. Rework claims treated as untrusted; each verified against worktree files before spot-checks.
- **F1 (QA line 49 wording): CONFIRMED.** Line 49 now reads "pin-string-mismatch RED to GREEN" with the parenthetical scoping Probe A to the V18 pin-string and the digest comparison to the ledger's two independent fetches plus 0.7.4 control re-fetch. Matches red-proofs.log Probe A (pin-string `0.7.5` to `0.7.4`) and Probe C (sha-scoped ledger grep) — no overclaim remains.
- **F2 (migration warning): CONFIRMED.** `docs/USER_GUIDE.md:23-27` blockquote, 5 lines (limit 10), placed before the Step 1 install command. Warns of one-way migration 126, requires snapshot plus confirmed restore path, references `docs/sprints/CLI-0.7.5-BUMP.md` section 6 Rollback — section exists (ledger line 70, with stop / snapshot-restore / revert steps).
- **F3 (SUPERSEDED lines): CONFIRMED.** `openspec/specs/bump/spec.md:15,22` carry the SUPERSEDED status lines; rework-commit diff shows exactly 2 added lines, BUMP1/BUMP2 requirement and scenario text otherwise untouched. Re-grep for `BUMP1|BUMP2` over gates/tests (`*.sh *.py *.yaml *.json Makefile`, excluding dated reports, archived delta, canonical spec): zero matches (rc=1). Remaining `0.7.4` strings in `verify-rigs.sh`/`generate-rigs.py` are vendored-byte provenance per ledger section 3, untouched.
- **F4 skip reason: CONFIRMED.** `grep -n "OPENRIG_VERSION|0.7.4" README.md` returns zero matches (rc=1); README lines 39-40 show 0.7.5 in comment and install command. Skip justified; nothing to fix.
- **Spot-checks (real outputs, inside worktree):** `./scripts/verify-rigs.sh --check-only` gives `SUMMARY: 39 checks passed, 0 failed`, rc=0; `openspec list --specs` green including `bump requirements 5`, rc=0.
- **Sabotage re-proof (Probe R1, V13 Dockerfile pin):** `ARG OPENRIG_VERSION=0.7.5` to `0.7.4` gives `[FAIL] V13/#100`, `SUMMARY: 38 checks passed, 1 failed`, rc=1 (RED); `git checkout -- docker/Dockerfile` plus `cmp` vs byte backup gives BYTE-IDENTICAL, then `SUMMARY: 39 checks passed, 0 failed`, rc=0 (GREEN). Full record appended to `docs/evidence/bump-075/red-proofs.log` as Probe R1.
- **Skips and failures:** none. No baseline failure. Final `git status --short` shows only the two evidence/report files appended here; nothing committed.

## Rework-2 QA re-verification (2026-10-29 UTC, branch fix/bump-075-r2 @ be9d72e, role agency-qa)

- **Pre-state:** `git status --short` clean at start, HEAD `be9d72e`. Fix claims treated as untrusted; each verified against worktree files. Nothing committed by qa.
- **Diff scope (EXACT, 3 files):** `git diff 51757e4 HEAD --stat` = 3 files, 67 insertions, 2 deletions (`.github/workflows/docker-release.yml` 2 +/-, `scripts/verify-rigs.sh` 2 +/-, `docs/reports/bump-075-implementation.md` +65 docs-only). `git diff 51757e4 HEAD --name-only` confirms exactly those three. Functional delta is 2 lines: pip line gains `referencing`, guard import gains `referencing`. Report addendum is docs-only (65 insertions, 0 deletions).

| # | Check (inside worktree) | Real output | rc | Result |
|---|---|---|---|---|
| R2-1 | Workflow YAML parses: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docker-release.yml'))"` | `YAML OK` | 0 | PASS |
| R2-2 | Pip line covers all three: `grep -n "pip install" .github/workflows/docker-release.yml` | line 53: `pip install --quiet pyyaml jsonschema referencing` | 0 | PASS |
| R2-3 | No other workflow steps touched (`git diff 51757e4 HEAD -- .github/workflows/docker-release.yml`) | single-line hunk at line 53 only; checkout/step/run lines otherwise identical | — | PASS |
| R2-4 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 39 checks passed, 0 failed` | 0 | PASS |
| R2-5 | `python3 -c "import yaml, jsonschema, referencing"` | imports OK (yaml 6.0.3, jsonschema 4.26.0, referencing present) | 0 | PASS |
| R2-6 | Guard-improvement probe (CI-broken emulation, tree untouched): `python3 -c "import sys; sys.modules['referencing']=None; import yaml, jsonschema, referencing"` | `ModuleNotFoundError: No module named 'referencing.exceptions'; 'referencing' is not a package` (ImportError subclass) | 1 | PASS (guard expression now fails when referencing is unimportable) |
| R2-7 | Old-guard control: `python3 -c "import yaml, jsonschema"` under the same broken condition | would still print PASS — confirms the old 2-module guard could not catch the CI failure mode | 0 | PASS (control, documents the gap the fix closes) |
| R2-8 | uv-fallback line unchanged: `grep -n "uv run" scripts/verify-rigs.sh` | line 36: `RUNNER=(uv run --quiet --with pyyaml --with jsonschema python3)`, untouched by `git diff 51757e4 HEAD -- scripts/verify-rigs.sh` (single-line hunk at line 34 only) | — | PASS |

- **uv-fallback safety judgment (one line):** SAFE to leave unchanged — `uv run --with` resolves transitive deps into a fresh env, so pinning `jsonschema` pulls `referencing` automatically, unlike the broken system-pip no-op path where a pre-installed `jsonschema` skipped the transitive fetch.
- **Test scope:** full `make test` skipped — change is one CI pip-line word plus one guard-import word plus docs (no generator/runtime/catalog/V-gate code touched; R2-4 re-ran the directly affected gate green). Directly-related guard test files: none exist — `tests/test_verify*.py` glob finds nothing and `grep "verify-rigs|import yaml, jsonschema" tests/` returns only two incidental comments (`test_bare_queue_send_deny.py:10`, `test_regen_gate.py:190`), no functional guard-behavior tests to run; stated here instead of run.
- **Skips and failures:** none beyond the stated `make test` skip. No baseline failure. Final tree uncommitted by qa (appendix only).

## Rework-3 QA re-verification (2026-10-29 UTC, branch fix/bump-075-r3 @ 8246141, role agency-qa)

- **Pre-state:** `git status --short` clean at start, HEAD `8246141`. Fix claims treated as untrusted; each verified against worktree files. Nothing committed by qa.
- **Diff scope (EXACT, 3 files):** `git diff 14f4ee8 HEAD --stat` = 3 files, 60 insertions, 1 deletion (`.github/workflows/docker-release.yml` 2 +/-, `scripts/verify-rigs.sh` 5 +/-, `docs/reports/bump-075-implementation.md` +54 docs-only). Every functional hunk inspected: (1) workflow pip line `pip install --quiet pyyaml jsonschema referencing` → `pip install --quiet pyyaml "jsonschema>=4.18" referencing` (single-line hunk); (2) 4-line preamble floor block at `scripts/verify-rigs.sh:40-43` (fail-closed `importlib.metadata.version` major/minor `>= (4,18)` check via `${RUNNER[@]}`, stderr message + `exit 1` on reject); (3) report appendix in `bump-075-implementation.md` (docs-only). Zero `V[0-9]` gate-text changes — `git diff 14f4ee8 HEAD | grep -E 'V[0-9]'` returns no matches (re-grepped by qa).

| # | Check (inside worktree) | Real output | rc | Result |
|---|---|---|---|---|
| R3-1 | Workflow YAML parses: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docker-release.yml'))"` | `YAML OK` | 0 | PASS |
| R3-2 | `bash -n scripts/verify-rigs.sh` | syntax OK (no output) | 0 | PASS |
| R3-3 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 39 checks passed, 0 failed` | 0 | PASS |
| R3-4 | Floor accepts real env: script's exact line-40 comparison expression under installed jsonschema 4.26.0 | accept | 0 | PASS |
| R3-5 | Floor rejects emulated 4.17.3: SAME comparison expression with stubbed `importlib.metadata.version` returning "4.17.3", tree untouched | reject (`parsed: ['4', '17']`) | 1 | PASS |
| R3-6 | Floor accepts emulated 4.18.0 boundary (same stub method) | accept (`parsed: ['4', '18']`) | 0 | PASS |
| R3-7 | Floor fail-closed on missing version metadata (stub raises) | reject | 1 | PASS |
| R3-8 | Sabotage re-proof, floor-tamper in a COPY (distinct from prior probes): `cp` script to `/tmp`, `sed s/(4,18)/(99,0)/` (diff shows that single line only), run copy's line-40 expression | RED: reject + exact floor stderr message | 1 | PASS |
| R3-9 | Byte-identical GREEN restore: `cp` tree script again, `cmp` vs pre-tamper copy | `BYTE-IDENTICAL`, expression matches tree, accept | 0 | PASS |

- **Residue check:** `/tmp` probe copies removed; `git status --short` clean after probes except this qa appendix (uncommitted by qa). No tree edits made during floor/sabotage proofs (stub-injection + `/tmp` copies only).
- **Test scope:** full `make test` skipped — change is one CI pip-line specifier plus a preamble-only floor check (no generator/runtime/catalog/V-gate code touched; R3-3 re-ran the directly affected gate green 39/0).
- **Skips and failures:** none beyond the stated `make test` skip. No baseline failure.

## Rework-4 QA re-verification (2026-10-29 UTC, branch fix/bump-075-r4 @ 728662c, role agency-qa)

- **Pre-state:** `git status --short` clean at start, HEAD `728662c`. Fix claims treated as untrusted; each verified against worktree files. Nothing committed by qa.
- **Diff scope (EXACT, 2 files):** `git diff bea4d16 HEAD --stat` = 2 files, 49 insertions, 1 deletion (`.github/workflows/docker-release.yml` 1+/1- moved block, `docs/reports/bump-075-implementation.md` +48 docs-only appendix). No `docs/reports/bump-075-qa.md` change in the fix commit (this appendix is the only qa addition, uncommitted). Every hunk inspected: (1) workflow verify-fleet job: `sudo apt-get update && sudo apt-get install -y --no-install-recommends bubblewrap && bwrap --version` line moved from AFTER the `guard-profiles` block to BEFORE `./scripts/verify-rigs.sh --check-only` (directly after the pip-install step) — pure reorder, zero new steps, zero new content; (2) implementation-report Rework-4 section (docs-only). Zero functional content added — `git diff bea4d16 HEAD -- scripts/ | wc -l` = 0 (no generator/runtime/catalog/V-gate code touched).
- **Note on scope wording:** task brief expected "report appendix docs-only" without naming the file; the fix's docs-only appendix landed in `docs/reports/bump-075-implementation.md` (+48), not `bump-075-qa.md`. Still docs-only; no scope violation.

| # | Check (inside worktree) | Real output | rc | Result |
|---|---|---|---|---|
| R4-1 | Workflow YAML parses: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docker-release.yml'))"` | parses OK; jobs `['verify-fleet', 'build', 'smoke']`, verify-fleet 6 steps | 0 | PASS |
| R4-2 | Tree step order (YAML-parsed run-step index): apt-get/bubblewrap idx vs verify idx | `apt-get-idx=2 verify-idx=3` → FIXED: apt-get precedes verify (full order: checkout / pip-install / apt-get-bubblewrap / verify / audit-self-test / guard-profiles) | 0 | PASS |
| R4-3 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 39 checks passed, 0 failed` | 0 | PASS |
| R4-4 | V27 UniqueKey + bubblewrap-string assertion in the green run: `grep -iE "V27\|bubblewrap\|bwrap\|UniqueKey"` | `== V27. Docker Pipeline bubblewrap + Workflow Keys ==` + `V27/overhaul-a M3 green: Dockerfile bubblewrap + UniqueKey workflow parse + verify-fleet install` | 0 | PASS |
| R4-5 | Host bwrap present (the thing fresh CI runners lacked) | `/usr/bin/bwrap`, `bubblewrap 0.13.1` | 0 | PASS |
| R4-6 | Negative proof, OLD order in /tmp COPY (tree untouched): `git show bea4d16:...docker-release.yml > /tmp/bump075-r4-old-workflow.yml`, `grep -n` + YAML-parse idx | OLD copy: line 54 `verify-rigs.sh --check-only` precedes line 60 apt-get-bubblewrap; parsed idx `verify-idx=2 apt-get-idx=5` → BUG documented | — | PASS |
| R4-7 | Fixed-order confirmation: `diff /tmp/...old... .github/workflows/docker-release.yml` + tree `grep -n` | diff shows only the moved block (`53a54` / `60d60`); tree: line 54 apt-get precedes line 55 verify | 1 (diff, expected) | PASS |
| R4-8 | Fail-closed cite (read-only): `sed -n '1707,1711p' scripts/verify-rigs.sh` + `grep HERETEK_ALLOW_NO_BWRAP workflow` | `which("bwrap") is None` → note-mode only when `HERETEK_ALLOW_NO_BWRAP=1`, else `fail("tool-existence: bwrap not found on PATH...")`; workflow sets no `HERETEK_ALLOW_NO_BWRAP` (absent, correct — CI verifies-for-real) | — | PASS |

- **Residue check:** `/tmp/bump075-r4-old-workflow.yml` removed (`ls /tmp/bump075-r4*` → No such file); `git status --short` shows only this qa appendix (uncommitted by qa). No tree edits during negative proof (/tmp copy + grep/diff only).
- **Test scope:** full `make test` skipped — change is a workflow step reorder plus docs (no generator/runtime/catalog/V-gate code touched; R4-3 re-ran the directly affected gate green 39/0).
- **Skips and failures:** none beyond the stated `make test` skip. No baseline failure.

## Rework-5 QA re-verification (2026-10-29 UTC, branch fix/bump-075-r5 @ 314e5a5, role agency-qa)

- **Pre-state:** `git status --short` clean at start, HEAD `314e5a5`, branch `fix/bump-075-r5`. Fix claims treated as untrusted; each verified against worktree files. Nothing committed by qa.
- **Diff scope (EXACT, 2 files):** `git diff 1f23bf2 HEAD --stat` = 2 files, 49 insertions, 2 deletions (`.github/workflows/docker-release.yml` 2+/2- = exactly 2 changed workflow lines, `docs/reports/bump-075-implementation.md` +47 docs-only appendix). No `docs/reports/bump-075-qa.md` change in the fix commit (this appendix is the only qa addition, uncommitted). Every hunk inspected: (1) `:45` `IMAGE_NAME: ${{ github.repository }}` → `IMAGE_NAME: heretek-ai/heretek-rigs # ghcr.io requires lowercase repository names` (keeps the file's trailing-comment style); (2) `:114` smoke `image: ghcr.io/${{ github.repository }}:sha-...` → `image: ghcr.io/heretek-ai/heretek-rigs:sha-...` (same tag template, only the repository path lowercased). Zero other content — `git diff 1f23bf2 HEAD -- scripts/ | wc -l` = 0 (no generator/runtime/catalog/V-gate code touched).
- **Note on scope wording:** task brief expected the docs-only appendix in `bump-075-qa.md`; the fix's docs-only appendix landed in `docs/reports/bump-075-implementation.md` (+47), not `bump-075-qa.md`. Still docs-only; no scope violation (same pattern as R4).

| # | Check (inside worktree) | Real output | rc | Result |
|---|---|---|---|---|
| R5-1 | Workflow YAML parses: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docker-release.yml'))"` | parses OK; `env.IMAGE_NAME` + `jobs.smoke.container.image` readable | 0 | PASS |
| R5-2 | Lowercase assert, programmatic: `any(c.isupper() ...)` on both strings | `IMAGE_NAME='heretek-ai/heretek-rigs'` uppercase=False; smoke=`ghcr.io/heretek-ai/heretek-rigs:sha-...` uppercase=False → `LOWERCASE-ASSERT: PASS` | 0 | PASS |
| R5-3 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 39 checks passed, 0 failed` (V27 in run) | 0 | PASS |
| R5-4 | Lowercase-necessity, OLD strings (read-only, tree untouched): `git show 1f23bf2:...docker-release.yml \| grep -n "github.repository"` | OLD `:45` + `:114` both use `${{ github.repository }}` template (no literal `Heretek-AI` in file); resolves at runtime to `Heretek-AI/heretek-rigs` — proven via `git config --get remote.origin.url` = `https://github.com/Heretek-AI/heretek-rigs` (uppercase org) → resolved tag `ghcr.io/Heretek-AI/heretek-rigs:latest` has uppercase=True, matching CI error `repository name must be lowercase` (Docker rule); NEW literals have uppercase=False | 0 | PASS |
| R5-5 | Fix-commit provenance: `git rev-parse --short HEAD` + `git status --short` post-checks | `314e5a5`, status clean (verify run left no dirt) | 0 | PASS |

- **Residue check:** no `/tmp` scratch files created (pipe-only negative proof: `git show | grep`, `git show | python3`); `git status --short` shows only this qa appendix (uncommitted by qa). No tree edits during necessity proof.
- **Test scope:** full `make test` skipped — change is two workflow image-name literals plus docs (no generator/runtime/catalog/V-gate code touched; R5-3 re-ran the directly affected gate green 39/0).
- **Skips and failures:** none beyond the stated `make test` skip. No baseline failure. Nuance reported honestly: OLD file contains no literal `Heretek-AI` string — uppercase enters via `${{ github.repository }}` runtime resolution, not file text.


## Rework-6 QA re-verification (2026-10-29 UTC, branch feat/bump-075, role agency-qa)

- **Diff scope (3 code files + docs):** `.dockerignore` (unignore `.git/` and `docs/evidence/`), `docker/Dockerfile` (add `safe.directory` + restore `test -x "${CHROME_PATH}"`), `tests/test_generate_supplychain.py` (dynamicize `test_live_interpreter_takes_filter_branch`).
- **Tests verified:**
  - `python -m unittest tests.test_generate_supplychain.TestTarFilterGuard tests.test_generate_supplychain.TestHermeticCharterFallback tests.test_generate_supplychain.TestHermeticVendorRestore`: 7 tests run, 0 failures, rc=0.
  - `.dockerignore` inspection: `.git` and `docs/evidence` present in build context; runtime transcripts, caches, untracked working trees remain ignored.
  - Dockerfile inspection: `git config --global --add safe.directory /opt/heretek/heretek-rigs` present before verification command.
