# QA report — remediate-lane-guard (#67 worktree-stale baked-path guard, Wave 5 micro-stage)

Stage: remediate-lane-guard · Branch: `remediate/audit-66-lane-guard` · HEAD: `616b2df` on base `2b103db`
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-lane-guard`
QA date: 2026-10-24 UTC · Verdict: **PASS (with one environmental caveat, section 6 — out-of-stage)**
Implementation report: `docs/reports/remediate-lane-guard-implementation.md` (read in full; all its claims independently re-verified below)
Unity binding: none.

## Checks run (all commands executed literally in the worktree; real output recorded)

| # | Check | Command | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | Full verify, green baseline | `./scripts/verify-rigs.sh --check-only` | 30/0, exit 0 | `SUMMARY: 30 checks passed, 0 failed`, exit 0, `[PASS] Worktree-stale paths (#67) green: 153 committed pi-settings.json leaves carry no /.lane/ baked paths` | PASS |
| 2 | V14 label + placement | `grep -n` / `sed -n '1940,1990p'` on `scripts/verify-rigs.sh` | `== V14 ==` after V13 `ok()`, before `SUMMARY`; V13 label untouched | V14 block at :1954, after V13 `ok()` (:1951-1952), before `SUMMARY` (:1986); V1-V13 headers/blocks unrenamed | PASS |
| 3 | V1-V13 untouched | `git diff main...HEAD -- scripts/verify-rigs.sh` | only additions | 32 insertions, 0 deletions; hunk is a single pure-addition block (verified diff head) | PASS |
| 4 | Red-proof (sabotage) | temp-plant `/.lane/trees/evil/scripts/seat-sandbox.sh` as `cache-streaming-eng` shellPath, verify, `git checkout --` revert | exit 1 with named V14 gate; V12 endswith still passes planted value; clean revert; green after | exit 1; `[FAIL] V14/#67: seat cache-streaming-eng: ... shellPath holds worktree-stale absolute path ...` fired; `endswith("scripts/seat-sandbox.sh")` is True (gap proven real); revert gives clean `git status`, canonical value restored, V14 PASS again | PASS — NON-VACUOUS |
| 5 | `make test` | `make test` | 257 OK, exit 0 | `Ran 257 tests in 52.849s` / `OK`, exit 0, 11 suites | PASS |
| 6 | No regen needed | `git status`, `git log main..HEAD`, `git diff main...HEAD --stat` + scope grep | 1 commit; only guard + NOTES + report; no specs/rigs/rosters/registry/fleet | single commit `616b2df`; 3 files +69/-0; scope grep for specs/rigs/rosters/registry/fleet paths: no matches | PASS |
| 7 | NOTES entry | `grep -n -A30 lane-guard docs/NOTES.md` | catch + fix + V12 gap + guard + commands | `remediate-lane-guard` section (11 lines) covers all five | PASS |

Full sabotage transcript (defect, exit codes, revert proof): `docs/evidence/remediate-lane-guard/red-proofs.log`.

## Red-proof results

- **V14 shellPath gate: RED under sabotage (exit 1, seat/file/key-specific message) → NON-VACUOUS.** No vacuous checks found in this stage.
- Collateral note (not a stage defect): the sabotage run also tripped 2 integrity/digest gates (`28 passed, 3 failed`) because ANY edit to a generated leaf breaks bundle digests — expected, and it further confirms generated-leaf integrity gates work.
- Vacuous checks anywhere in scope: **none**.

## 6. Environmental caveat (out-of-stage; does not touch the verdict on V14)

- After the revert, repeated full-suite runs returned `29 passed, 7 failed`, all 7 being **V13/#70 networked image-existence probes** failing with skopeo `toomanyrequests: You have reached your unauthenticated pull rate limit` (Docker Hub anonymous quota — exhausted in part by this session's own repeated verify runs).
- V13's offline-skip regex does not match `toomanyrequests`/`rate limit`, so quota exhaustion hard-fails instead of skipping. Tree was verified unmodified at the time (`git diff HEAD --stat` empty; sidecar digests verified 64-hex valid in-file via script). V14's own line read PASS in every post-revert run, and the stage's 30/0 was observed in-run before quota exhaustion.
- This belongs to the supply-chain wave's V13 network probe, not to this micro-stage (which adds only the offline V14 block). Recommended follow-up for the owning wave: add `toomanyrequests`/`rate limit` to the V13 skip regex or use authenticated pulls — NOT done here (QA never patches code).

## Verdict

**PASS.** Every acceptance item in the stage brief is met on the unmodified tree: V14 correctly labeled/placed, V1-V13 byte-untouched (32+/0-), sabotage turns V14 RED with the named gate while proving the V12 gap it closes, revert is clean, `make test` is 257 OK, scope is regen-free, NOTES documents the catch/fix/gap/guard/commands, and the single implementation commit is intact. Only `docs/evidence/` (this session's red-proofs.log) and `docs/reports/` (this file) are added by QA — no production or test files touched.
