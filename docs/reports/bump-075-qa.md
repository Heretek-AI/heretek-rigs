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
