# T3 drift-guard verification — Wave C provisioning-gate-74 (issue #74, gate-only)

- Stage id: `provisioning-gate-74` (T3 audit only; no code fixed, no code changed by auditor)
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/provisioning-gate-74`
- Branch: `feat/provisioning-gate-74` @ `9308017` (T1 `493cb98` + T2 evidence `9308017`)
- Date (UTC): 2026-10-25
- Spec read from disk: `openspec/changes/provisioning-gate-74/proposal.md`,
  `openspec/changes/provisioning-gate-74/specs/provisioning-gate/spec.md` (REQ-P1/P2/P3/P4/G1),
  `openspec/changes/provisioning-gate-74/design.md`,
  `openspec/changes/provisioning-gate-74/tasks.md`
- Unity binding: N/A (no Unity content in this repo)

## 1. Spec deliverable audit (all read from disk, checked against code)

| Req | Verdict | Evidence (file:line) |
|---|---|---|
| REQ-P1 render-time resolution | HOLD | `scripts/render-seat.py:331-376` (`resolve_tool_artifact`, `bash_leading_binary`, read-only `shutil.which` + path-exists); gate applied at `:601-616` (MCP `entry["enabled"] = False` + `warn: <seat>: <server> disabled, missing tool artifact: <artifact>` on stderr) and `:750-762` (bash-grant warns). Silent degradation impossible by construction: every not-ok path prints. |
| REQ-P2 seed/stage-time resolution | HOLD | `scripts/seed-rig.py:48-111` (`_resolve_artifact74`, `_bash_leading74`, `stage_time_provisioning_warns` with `at stage time` warn shape); invoked per seat in the staging loop at `:195-208`. Degrade-loudly, exit codes unchanged. |
| REQ-P3 verify block + live-health | HOLD | `scripts/verify-rigs.sh:2044-2211` appended V16 (exactly one new `ok()`, V1–V15 untouched — no renumber/reword). `scripts/live-health.py:64-67` (`PROVISIONING_BASH_BINARIES`), `:605-698` (`live_tool_status`, `evaluate_tool_provisioning` with `0 missing tools` PASS banner, missing→WARN, unassessed→SKIP never healthy), wired into `run_gate` at `:844-861` incl. dead-daemon all-SKIP path at `:713-719`. |
| REQ-P4 full 20+B3 coverage, github exclusion | HOLD | Catalog check re-run: 20 command-bearing servers (aws … terraform, list verified). `docs/74-PROVISIONING-MATRIX.md:39-67` names all 20 with pins/artifacts/bound roles + github remote-http exclusion; `:69-75` B1–B3 (`r2`, `rabin2`, `tshark`); V16 block asserts all three programmatically (`verify-rigs.sh:2084-2098`, checks `rabin2`/`tshark` by name and all 20 catalog names). |
| REQ-G1 no renumber, no provisioning claims, Refs posture | HOLD | `fleet/` untouched (empty `git diff main...HEAD -- fleet/`); no `install:` recipes, no pin changes; added-lines grep clean for installs/pulls/network; `git log main..HEAD` has no `Closes`; only branch mentions of `Closes #74` are `never Closes #74` disclaimers in evidence/impl-report prose, not claims. No PR exists yet — T3 instructs `Refs #74` at PR time. |

Read-only resolution confirmed: added-lines grep over the three scripts shows no
`pip install`/`apt`/`npm i`/`docker pull|run|image`/`uvx --from`/`urllib`/`requests`/`socket`/`os.system`.
Stub scan clean: no TODO/FIXME/`pass #`/NotImplemented/bare-except-pass in added script lines.

## 2. Generated-leaf / architecture check

- `git diff main...HEAD --name-only` touches only `docs/`, `docs/evidence/`,
  `docs/reports/`, `scripts/`, `tests/` — zero edits under `specs/`, `rigs/`,
  `rosters/`, `registry/`. No regen required (no catalog-adjacent change).
- Diff stat: 10 files, +1071/−3.

## 3. Re-run (auditor-executed, real output)

- `./scripts/verify-rigs.sh --check-only`: `SUMMARY: 32 checks passed, 0 failed`, exit 0,
  incl. `[PASS] Provisioning existence gate (#74) green`. (31 baseline + appended V16.)
- `pytest tests/test_render_seat.py tests/test_seed_rig.py tests/test_live_health.py`:
  **47 passed, 129 subtests passed**, exit 0.
- `pytest tests/test_build_canary.py`: **12 failed, 11 passed** — matches T2's recorded
  counts exactly. T2 evidence proves pre-existing: identical 12/11 on a clean
  main-checkout temp worktree (merge-base `f2f97f6`), environment/dependency shape
  (`Denied by policy` vs mock `requires approval…`), unrelated to this change.
  Out of scope per stage instructions; verdict NOT failed for it.

## 4. Red-proof audit (T2 evidence `docs/evidence/wave-c-provisioning-gate.md`)

- Direction (a), missing tool → loud degradation: sabotage
  (`command: uvx` → `/nonexistent-qa74-sabotage`) produced exit-0 degraded render with
  semgrep `"enabled": false` + exact named stderr warn at both render and seed layers;
  restore via `git checkout`, re-render at baseline. Non-vacuous (behavioral, both layers).
- Direction (b), silenced warn → verify must RED: warn block replaced with `pass`
  produced verify exit 1, `30 passed, 4 failed`, with V16 string-gate FAILs + both
  missing-direction behavioral FAILs + `test_render_seat.py` 1 failure; restore returns
  32/0. Non-vacuous (gate fails when the property is removed).
- `git status --short` at audit time: **clean** (empty). T2 restore proofs logged
  clean after each sabotage. No production/test files changed by QA (evidence-only commit).

## 5. Findings

None. No stubs, no vacuous checks, no failing in-scope commands, no missing
deliverables, no renumber, no install recipes, no pin changes, no `Closes #74` posture.

`git status --short`: clean.

VERDICT: PASS
