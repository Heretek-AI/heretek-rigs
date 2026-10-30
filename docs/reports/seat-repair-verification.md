# seat-repair verification (binding drift-guard audit, stage: seat-repair, 2026-10-30)

Change: `openspec/changes/2026-10-30-seat-repair/`. Worktree: `.lane/trees/seat-repair` (branch `feat/seat-repair`, HEAD `db39ba1` at audit time).
Auditor: agency-drift-guard. Read-only live ops only (no launches, no queue writes, no seat sends). No commits. No secrets printed.

## 1. Scope / One Rule / Refs-only — PASS

- `git diff main...HEAD --name-only`: exactly 26 files — `AGENTS.md` (1 docs-map row), `docs/evidence/seat-repair-2026-10-30/` (runbook + 8 ps + 8 queue snapshots), `docs/evidence/seat-repair/qa-red-proofs.log`, `docs/reports/seat-repair-implementation.md`, `openspec/changes/2026-10-30-seat-repair/*` (proposal/design/tasks/spec), `scripts/live-health.py`, `tests/test_live_health.py`.
- Guarded paths empty in committed diff: `git diff main...HEAD --name-only -- fleet/ specs/ rigs/ rosters/ registry/ archive/ openspec/specs/` → empty. One Rule holds (no hand-edits to generated leaves).
- `AGENTS.md` diff is the single surgical 2-line docs-map row for this change. Nothing else outside the allowlist.
- Closing directives in source diff (`AGENTS.md openspec/ scripts/ tests/ docs/reports/`): zero bare `Closes/Fixes/Resolves #147` (one hit is the negated guard ``never `Closes #147` ``). Refs-only holds.

## 2. Spec acceptance REQ-R1..R4 — PASS (with adjudicated deviations, see §3)

- REQ-R1 (batches ≤6, whole-wave abort): 6+6+6+4 executed with kickoff snapshots and fleet-shape checks between batches; all 8 ps snapshots 111 lines (baseline shape holds); stop-point recording rule never needed. Scenario checks satisfied.
- REQ-R2 (re-resolve + relaunch + live probe; idle-only; lobotomized verify-only): 22/22 stale seats show re-seed rc=0 → relaunch rc=0 → config-clean GREEN → probe record; 22 unique fresh sessionIds (`01M67…`) in runbook; per-seat activity re-checks recorded idle (0 skips, credible — fleet quiescent at resume, baseline byte-identical); 2 lobotomized received read-only inspection only (no seed/launch/send). Probe pattern uniform (whoami exit 0 + policy-denied echo + typed `SEAT-REPAIR-OK`), except D1 — adjudicated below.
- REQ-R3 (live-health `seat-shell-paths`, warn-first + strict): diff reviewed — pure `evaluate_shell_paths`, `collect_seat_paths`, `FixtureClient.fetch_seat_paths`, one 4-line allowlist branch for exactly `["seat", "status", <session>, "--json"]`, wired through existing `run_gate → finalize → overall_exit`. Advisory run: exit 0, WARN names ONLY the 2 lobotomized. `--strict` run (true rc, no pipe): rc=2 with `seat-shell-paths` FAIL naming only those 2. Dead-daemon path adds the new check to the all-SKIP set (test-pinned). No new V-gate (correct per Q5 — V-absence verified: `verify-rigs.sh` 39/0, no V-block appended).
- REQ-R4 (zero residue, unchanged others): queue snapshots B1 26→26, B2 26→27 (+1 seat-created handoff, not wave), B3 27→24 (terminal completions, listing-scope effect), B4 263→263 (+0/−0/±0 state changes); zero rows containing `SEAT-REPAIR` across all 8 snapshots; ps post-diffs confined to each batch's own relaunches. `git status --short` empty at audit close (generate side-effects reverted, see §5).

## 3. Adjudications (independent, not deferred to QA)

- F4 / D1 (`design-ux-research-analyst` token-declined probe): CONCUR with QA, and I rule the deviation ACCEPTABLE. The spec scenario's letter (transcript shows `SEAT-REPAIR-OK` + whoami) is unmet for this one seat — recorded honestly as DEVIATION D1, never probe-PASS. The substance is proven by stronger in-turn evidence: seat running/active/ready with `continuity_outcome: fresh` (status read by auditor), clean re-resolved shellPath on disk (auditor-verified exists), whoami exit 0 + queue-list exit 0 + successful file edits through the re-resolved wrapper in the same turn. A re-send would arrive identically unattributed (`--from` deprecated; attributed send requires queue-create, out of bounds), so re-probing could not cure the letter. Treating this as wave-RED would abort a repair wave over a sender-attribution artifact, not a repair failure — the abort rule's purpose (stop on repair failure) was not triggered. No overclaim: runbook §7 and report §self-audit both flag D1 as a triad judgment call. Follow-up: none required beyond this ruling.
- F5 / lobotomized (`build-java-kotlin-eng`, `build-python-backend-spec`): CONCUR with QA. Auditor re-verified read-only: both `settings.json` shellPaths still point at the pruned `.../.lane/trees/fleet-proofs/scripts/seat-sandbox.sh` (target absent) — STILL-DANGLING, untouched, exactly as the wave record states.
- Coordinator-correction adjudication: (a) The wave record is HONEST — no wave file claims the 2 lobotomized seats as repaired by this wave (auditor grep confirms; the only "repaired" counts refer to the 22 stale seats). (b) The outstanding follow-up is PROPERLY NAMED AND BOUNDED — runbook §1 "premise deviation … reported", report §self-audit "Recommending a follow-up scoped to those 2 seats", and `live-health` now names exactly those 2 seats as the standing WARN. The wave does NOT fail for leaving known-broken seats running: design Q6 scoped them verify-only with a never-touch rule (the separate go-ahead has not landed on disk), and relaunching them was explicitly out of bounds. Leaving them running, honestly recorded, guarded by the new check, with a scoped follow-up recommended, is the correct in-bounds outcome.
- "0 aborts, 0 skips" credibility: CREDIBLE, not weak tripwires. Fleet was quiescent (resume state byte-identical to baseline, 51 running/idle, no fresh generations); every seat shows an idle kickoff check plus a per-seat re-check immediately before touching. The tripwires are proven non-vacuous: QA S3/S4 red-proofs plus the auditor's own sabotage (§6) show the gate tests trip on real defects, and D1 shows the operator distinguished repair-failure RED from probe-attribution noise with full evidence.
- F1 (validate content-insensitive): tool weakness, PRE-EXISTING, not wave-introduced — and NOT MATERIAL to this wave's acceptance. Compensated by direct read, re-verified by the auditor: `spec.md` on disk carries 4 `### Requirement:` (REQ-R1..R4) + 7 `#### Scenario:` blocks matching design. `validate` rc=0 is therefore corroborated, not load-bearing.

## 4. Bounds / honesty — PASS

- Launch count: 22 re-seeds rc=0 + 22 relaunches rc=0 + 22 sends rc=0, 0 retries (zero 400s-rot observed), 0 skips, 2 verify-only untouched. Matches the 22-seat batch plan exactly; no spares, no extras.
- Idle-only: every kickoff + per-seat re-check recorded idle; holder seats' stuck rows recorded with IDs, untouched.
- No queue writes: per-batch diffs attributed to `watchdog@system` / seat-self agency; B4 `-a -A` methodology fix (263 rows, zero deltas) is sound and honestly documented.
- No overclaim found in runbook or implementation report: "22/22 stale repaired" is accurate (D1's equivalent-evidence basis disclosed inline); "zero" claims (queue writes, non-target disturbance) verified against snapshots; probe-equivalence (D1) explicitly labeled DEVIATION, never probe-PASS.

## 5. Re-run gates (auditor-executed) — all GREEN

- `make test` FULL: `Ran 657 tests … OK` (auditor run; 12 new `TestSeatShellPaths` included).
- `./scripts/verify-rigs.sh --check-only`: `39 checks passed, 0 failed`, NO new V-block.
- `openspec validate 2026-10-30-seat-repair`: valid, rc=0 (true rc; F1 weakness noted in §3, compensated).
- `python3 scripts/audit_loop.py --self-test`: SELF-TEST PASSED.
- `python3 scripts/generate-rigs.py --check-idempotent`: `idempotence check passed`, rc=0 — with F2 environment note: the run rewrote 35 files (queue-handoff SKILL.md parked-row text + digests) because the host toolchain is rig 0.7.5 while committed output pins 0.7.4-era assets. Pre-existing toolchain drift, NOT wave drift; all 35 reverted via `git checkout --`, tree verified clean after. Side-effects idempotent.
- `make live-health` (advisory): exit 0 as above; `--strict`: rc=2 as above.

## 6. Auditor's independent red-proof — RED then GREEN, byte-identical restore

- Sabotage (distinct from QA's): flipped the dangling-branch `"status": "WARN"` → `"PASS"` in `evaluate_shell_paths` (exact `dangling seat paths` branch, 1 line). Result: `TestSeatShellPaths` → `Ran 12 tests … FAILED (failures=4)`, TRUE rc=1 (measured without pipe). RED confirmed, non-vacuous.
- Restore: `cp` from pre-sabotage copy, `cmp` byte-identical; re-run → `Ran 12 tests … OK`, rc=0. GREEN. `git status --short` empty afterwards. (An earlier mis-aimed sabotage that flipped a non-seat WARN and stayed green was discarded as vacuous and redone correctly — recorded here for honesty.)

## 7. Secrets / anti-stub — PASS

- Secret shapes (`Bearer␣|ghp_|github_pat|sk-|AKIA`) in the source diff: EMPTY. Probe string `SEAT-REPAIR-OK` is a dummy marker, acceptable. No secret values in final files.
- Stub scan over `scripts/` + `tests/` diff: no `TODO/FIXME/XXX/not implemented`/stub-pass. All 12 new tests assert behavior (29 `self.assert*` total, 1–4 per test: trip, clear, relative-resolution, missing-cwd, empty-SKIP, unassessed-SKIP, fixture trip/clear, strict promotion, allowlist accept+refuse, dead-daemon SKIP, collector happy/unreadable paths).
- Spot-check for unreferenced additions: new check is wired into `run_gate` (7th gate slot), rendered output, and live collection — no dead code.

## 8. QA verdict concurrence

QA PASS with F1–F5 is concurred in full: F1 compensated (re-verified §3), F2 pre-existing drift (re-verified §5, reverted), F3 evidence packaging (8+8 snapshots + runbook + report all present and consistent), F4 D1 equivalent-evidence accepted (adjudicated §3), F5 lobotomized still-dangling correctly untouched with bounded follow-up (adjudicated §3).

VERDICT: PASS
