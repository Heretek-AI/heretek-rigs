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
+ age ≥ 50m; `test_fresh_claim_passes` asserts the negative direction (no false
+ positive on a fresh claim) while `test_late_first_transition_warns` asserts
+ WARN when the first post-claim transition lands past T_pickup (late pickup
+ still breaches); `test_overdue_breach_...`
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
signal and telemetry-spike detection — are outside the spec's ADDED
requirements; the proposal explicitly scopes watchdog changes out (routed to #38
if at all). Closing #45 on this stage is legitimate for the specified subset;
telemetry-spike detection and the watchdog sweep-rate signal remain UNFINISHED
follow-up work for the maintainers to schedule separately, not defects in this
stage.

## 8. Re-audit of review-driven fixes (d1db5e4 + 5724316 + 776775e) — 2026-10-22 UTC

- Commits under audit: `d1db5e4` (six review fixes) + `5724316` (note
  touch-up) + `776775e` (QA re-verification evidence). Base for diff:
  `5a478b5`. No production code touched by this auditor; all checks re-run
  independently in the worktree. Nothing committed.
- Prior verdict line confirmed intact before amendment: file ended with exactly
  `VERDICT: PASS`; §7 text matches the review-asked rewrite (telemetry-spike +
  watchdog sweep-rate stated as UNFINISHED follow-up, prior over-claim that
  telemetry was "folded into WARNs" removed); §4 matches actual test behavior
  (names `test_late_first_transition_warns`, describes WARN on late first
  transition — verified against `tests/test_live_health.py:184`).

### 8.1 Diff audit — every hunk justified, no scope creep

- `git diff 5a478b5..HEAD --stat -- specs/ rigs/ rosters/ registry/` → empty.
  No hand-edits under generated dirs (AGENTS.md one-rule honored).
- `git diff 5a478b5..HEAD -- scripts/verify-rigs.sh` → empty (byte-identical;
  audit-baseline honored). `git diff 5a478b5..HEAD -- openspec/` → empty
  (spec contract unchanged — review fixes trace to fidelity, no new features).
- `d1db5e4 --stat`: only `scripts/live-health.py`,
  `tests/test_live_health.py`, `docs/reports/wave-45-live-health-verification.md`
  (§4 + §7 rewrites). `5724316`: test rename (`test_post_claim_transition_clears_breach`
  → `test_late_first_transition_warns`) + §4 touch-up. `776775e`: evidence log +
  QA appendix only. `Makefile` delta (6 lines) belongs to the original `761b1ac`,
  not the review fixes. No new deliverables, no widened surface.

### 8.2 The three behavior changes — read, fail-closed in all paths

- Truncation guard (`scripts/live-health.py:144`): `len(result) >= self.limit`
  → `DataSourceError` → `run_gate` degrades to SKIP (all-SKIP for `fetch_list`,
  single-SKIP for overdue/undelivered; `finalize` orders FAIL > WARN > SKIP >
  PASS so any SKIP blocks the healthy banner). Independently re-run: stub rig
  returning 3 rows with `--limit 3` → `DataSourceError: ... hit the fetch cap
  (3) ... refusing to report healthy`. On the `>=` operator: firing at exactly
  `limit` is conservative — a legitimately full-but-complete page SKIPs instead
  of passing. That is the fail-closed direction (SKIP, exit 0, never PASS), not
  a defect; no finding.
- Pickup first-transition semantics (`evaluate_pickup`, lines 302–314): minimum
  post-claim `ts` computed over dict entries with parseable `ts > claim_ts`;
  latency past `T_pickup` breaches with the latency (not age); no post-claim
  transition falls back to claim-age breach. Unreadable paths stay
  unknown/SKIP: `get_transitions` raising → `unknown` (lines 297–301);
  unparseable `claimedAt` → `unknown` (293–296); non-dict/unparseable transition
  entries skipped, never treated as progress. Breach-empty + unknown-nonempty →
  SKIP with reason; breach-nonempty + unknown → WARN naming both. No healthy
  path on unreadable data.
- ps pinning (`check_allowed`, lines 80–86): bare/reduced `ps` argv refused
  with `RuntimeError`; only the pinned combo (`--nodes --json --no-cleanup`)
  passes. Live caller `fetch_ps_nodes` (line 170) uses exactly the pinned
  combo. `RuntimeError` (not `DataSourceError`) still degrades to SKIP: raised
  inside `run_rig` it is caught by `fetch_list`'s `except Exception` (all-SKIP),
  by the overdue/undelivered/nodes `except Exception` handlers (single-SKIP),
  and inside `evaluate_pickup`'s `except Exception` (unknown → SKIP). No
  mutation path: `queue` branch additionally requires `--json`; `show` remains
  allowed but no live caller uses it and it is read-only.

### 8.3 Test changes — all non-vacuous, independently confirmed

- Renamed test `test_late_first_transition_warns` (line 184): appends an 11:40
  transition (~26m post-claim) and asserts WARN + ID + latency > 15. Old name
  has 0 hits outside the QA report's own audit row. Independent red-proof (no
  tree modification, semantics replicated against fixture data): NEW code →
  `WARN [{'id': 'qitem-...78213c07c3272cbc', 'age_min': 25.605...}]` (matches
  QA's 25.6m); pre-fix `any(ts > claim)` semantics → `progressed=True` → no
  breach (PASS). The test discriminates the semantic change. NOT vacuous.
- FixtureClient swap (line 355): incident replay now replays the on-disk
  fixtures through the real `FixtureClient` instead of a hand-built FakeClient —
  strictly stronger fidelity; replay re-run independently: WARN naming all
  three 11:14 qitem IDs, `sources: 5 ok, 0 skipped`, exit 0. ✓
- Moved assertions + `assertTrue(logged.strip(), "stub log must record at
  least one command")` (line 450): assertions now execute only after the
  subprocess returncode assertion inside the `with` block, and an empty stub
  log fails the test. QA SAB-R4 red-proven (silent stub → AssertionError);
  restored `TestReadOnly` re-run OK per evidence log. NOT vacuous.
- Full suite independently re-run: `Ran 28 tests ... OK`.

### 8.4 Independent re-runs (this auditor)

- `make verify` → `SUMMARY: 22 checks passed, 0 failed` (exit 0) + advisory
  WARN (heartbeat, 7 stale) + SKIP (seat-idleness), `sources: 4 ok, 1 skipped`
  — matches QA R2 exactly.
- `openspec validate remediate-45-live-health` → valid.
- Incident replay `--now 2026-10-22T12:05:00Z` → WARN + all three row IDs
  (51m each), exit 0 — matches QA R4b and verification §5/LH7.
- Red-proofs log: re-verification section present with dated SAB-R1…R4 entries,
  each recording failure signature + `git checkout --` restore + clean status;
  signatures non-vacuous (DATASOURCEERROR text, `FAILED (failures=1)`,
  RuntimeError refusals, AssertionError on empty log). Spot-check of R4b
  (above) and guard behavior (above) confirms the log's claims.
- Secrets: pattern grep over the full `5a478b5..HEAD` diff → 0 hits.
  `git status --short` → clean before this report amendment (only this
  auditor's `/tmp/opencode/` scratch outside the tree).

### Findings

None. No stubs, no vacuous checks, no failing commands, no missing
deliverables, no hand-edits under generated dirs, no spec drift, no secrets.
The `>=` truncation operator and the §7 follow-up-work framing are deliberate
and documented, not defects.

VERDICT: PASS
