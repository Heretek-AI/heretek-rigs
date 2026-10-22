# Verification report: wave-45-live-health (independent adversarial audit)

- Stage/wave id: `wave-45-live-health` | Change id: `remediate-45-live-health` | Issue #45
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-45-live-health`
- Commits under audit: `761b1ac` (implementation) + `2ba7dd0` (QA evidence)
- Auditor date (UTC): 2026-10-22. No production code touched; all checks re-run independently.

## 1. Diff audit vs tasks.md + AGENTS.md one-rule

`git diff 5a478b5..HEAD --stat` (14 files): `Makefile`, `fleet/fleet.yaml`,
`scripts/live-health.py` (new), `tests/test_live_health.py` (new),
`tests/fixtures/live-health/incident-2026-10-22/` (6 fixtures), `docs/live-health.md`,
`docs/reports/qa-wave-45-live-health.md`, `docs/reports/wave-45-live-health-implementation.md`,
`docs/evidence/wave-45-live-health/red-proofs.log`. Every file is justified by
tasks.md T1–T8 (gate, tests, fixtures, docs, reports, evidence). No scope creep.

- `git diff 5a478b5..HEAD --stat -- specs/ rigs/ rosters/ registry/` → empty.
  No hand-edits under generated dirs.
- `git diff 5a478b5..761b1ac -- scripts/verify-rigs.sh` → empty (byte-identical;
  audit-baseline rule honored).
- `Makefile` diff: 2 lines — `.PHONY` gains `live-health`, `verify` appends
  `python3 ./scripts/live-health.py`, new `live-health` target. Minimal and correct;
  `verify-rigs.sh` failure still aborts `make verify` before the advisory runs
  (no `|| true`, no `-` prefix), so a static failure cannot be masked by the gate.

## 2. T2 heartbeat edit + regen story — verified honest

- `grep -c "heartbeat_sec: 0" fleet/fleet.yaml` → `0` (49 zeros → `1800`; matches
  existing `exec-director` precedent; per-role tuning explicitly out of scope).
- `grep -rln "heartbeat" scripts/generate-rigs.py scripts/render-seat.py
  scripts/verify-rigs.sh rigs/ specs/ rosters/ registry/` → no hits outside
  `scripts/live-health.py` (consumer) and `fleet/fleet.yaml` (catalog). So
  `heartbeat_sec` flows into zero generated leaves: regen is provably a no-op for
  this edit, the reverted `resolvedCommit` provenance hunks were the only regen
  output, and reverting them keeps the diff surgical without changing any
  generated outcome. `make verify` re-run in this worktree: `SUMMARY: 22 checks
  passed, 0 failed` (exit 0). Regen gap is a documented environmental limitation
  (missing gitignored `.scratch/vendor/*` pins), not a consistency hole.

## 3. scripts/live-health.py — real gate, fail-closed (read in full, 935 lines)

- Thresholds are real and tunable (flags + `LH_*` env + printed effective values);
  defaults match design.md (15/30/15m, hb 3×). No `TODO`, no `|| true`, no bare
  `except:`; every `except Exception` path resolves to SKIP/DataSourceError, never
  to healthy.
- Read-only: allowlist `check_allowed()` refuses `claim/update/block/resolve/
  handoff/send`; live callers use fixed read-only argv (`queue list/overdue/
  undelivered/transitions --json`, `ps --nodes --json --no-cleanup -A`).
  Re-verified via dead-daemon run (all-SKIP) and QA's argv-shim log (SAB-7).
  Note (non-blocking hardening): the `ps` branch of `check_allowed()` permits any
  `ps` argv rather than pinning `--json --no-cleanup`; all real call sites are
  fixed and read-only, so this is defense-in-depth looseness, not a live mutation
  path.
- SKIP-never-PASS: `finalize()` orders FAIL > WARN > SKIP > PASS; any SKIP blocks
  the healthy banner; dead-daemon run prints `LIVE-HEALTH SKIP ... (no passing
  signal)`, `sources: 0 ok, 5 skipped`, exit 0. Confirmed by independent re-run.
- Warn-first semantics: advisory exit 0 on WARN/SKIP; `--strict` promotes WARN→FAIL
  with exit 2 (independently re-run: replay exit 0 WARN → `--strict` exit 2 FAIL).
  Config errors (`_resolve_number`, `--now`) die exit 2, distinct from fleet state.
- REQ-LH3: any `heartbeat_sec: 0` role caps heartbeat at WARN and is named;
  fresh+configured → PASS (unit-tested).
- REQ-LH9: idle definition documented in module docstring (`idle/idle-at-prompt/
  waiting/waiting-for-input` + holds claimed row); unknown states → SKIP, never
  healthy. Live run shows exactly this behavior (all-`unknown` → SKIP with reason).

## 4. Tests — non-vacuous (21 cases, all re-run OK)

Spot-read: `test_claimed_untouched_row_named_with_age` asserts WARN + exact row ID
+ age ≥ 50m; `test_fresh_claim_passes` / `test_post_claim_transition_clears_breach`
assert the negative direction (no false positive); `test_overdue_breach_...`
asserts breach/non-breach split at the grace boundary plus histogram totals.
QA SAB-8 proved the suite goes RED (`FAILED (failures=2)`) when the breach
condition is masked, with clean restore. Independent re-run:
`python3 -m unittest tests/test_render_seat.py tests/test_live_health.py` →
`Ran 28 tests ... OK`.

## 5. Spec fidelity (all 9 ADDED requirements)

REQ-LH1 ✓ (separate script + target, 22 untouched) · LH2 ✓ (SKIP semantics,
`sources:` line, dead-daemon proof) · LH3 ✓ (UNCONFIGURED cap + P0 landed) ·
LH4 ✓ (claim→transition latency, IDs + ages) · LH5 ✓ (overdue + histogram
buckets) · LH6 ✓ (undelivered IDs + ages) · LH7 ✓ (warn-first exit 0, --strict
exit 2, promotion policy + anti-rot rule in `docs/live-health.md`, incident replay
WARN naming all 3 qitem IDs re-run independently) · LH8 ✓ (zero-mutation argv
proof) · LH9 ✓ (idle join + unknown→SKIP). tasks.md T1–T8 all done; no stated
deferrals except the documented regen-environment note.

## 6. Secrets / status

- Secret-pattern grep over the full diff → no hits; fixtures use synthetic qitem
  IDs and recorded timestamps only. `git status --short` → clean (only the
  auditor's untracked scratch under `/tmp/opencode/`).
- `openspec validate remediate-45-live-health` → valid.

## 7. Issue #45 closure note (observation, not a finding)

The spec contract is fully met, including the issue's returnable (replay names
all three 11:14 row IDs). Two asks in the issue body — watchdog sweep-rate
signal and telemetry-advisory spike detection — are outside the spec's ADDED
requirements; the proposal explicitly scopes watchdog changes out (routed to #38
if at all) and telemetry advisories were folded into observable heartbeat/idleness
WARNs. Closing #45 on this stage is legitimate for the specified subset; if the
maintainers want the remaining two signals, that is follow-up work, not a defect
in this stage.

VERDICT: PASS
