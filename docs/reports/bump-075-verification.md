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

VERDICT: PASS
