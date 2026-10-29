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
- Plan Wave-1 acceptance (compound 39/0 plus 634 or more plus ledger two-agent sha plus `rig --version` 0.7.5 plus validate rc=0 plus hash-mismatch RED to GREEN): PASS on all conjuncts.
- AGENTS.md surgical scope (15 lines or fewer): PASS (3 lines).
