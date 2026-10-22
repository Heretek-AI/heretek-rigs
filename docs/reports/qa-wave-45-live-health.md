# QA verdict: wave-45-live-health — QA-CLEAN

- Stage/wave id: `wave-45-live-health` | Change id: `remediate-45-live-health`
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-45-live-health`
- Implementation commit under test: `761b1ac`
- Verifier date (UTC): 2026-10-22
- Evidence: `docs/evidence/wave-45-live-health/red-proofs.log` (this worktree)
- Raw outputs (scratch, not committed): `/tmp/opencode/{final-verify,strict-out,sab-*-out,rig-argv.log,post-restore-out}.txt`

## Per-check verdicts (each mapped to spec REQ + tasks.md testable)

| # | Check | Result | Exact command + output |
|---|---|---|---|
| 1 | `make verify`: 22/0 + WARN advisory, exit 0; no renumbered checks (REQ-LH1, T7) | PASS | `make verify` -> `SUMMARY: 22 checks passed, 0 failed.` (exit 0) then `LIVE-HEALTH WARN (advisory, exit 0)` naming 7 heartbeat-stale sessions + 2 idle holders; pickup/overdue/undelivered PASS; `sources: 5 ok, 0 skipped` |
| 2 | `make live-health` advisory exit 0 on live fleet (T7) | PASS | `make live-health` -> exit 0, same advisory content as above (WARN heartbeat/seat-idleness only) |
| 3 | Full suite 28 tests OK (test_render_seat 7 + test_live_health 21) | PASS | `python3 -m unittest tests/test_render_seat.py tests/test_live_health.py` -> `Ran 28 tests ... OK`, exit 0 |
| 4 | `openspec validate remediate-45-live-health` | PASS | -> `Change 'remediate-45-live-health' is valid`, exit 0 |
| 5 | Fixture replay determinism: names all 3 incident rows (REQ-LH7/T6a) | PASS | `--fixture-dir .../incident-2026-10-22 --now 2026-10-22T12:05:00Z` -> WARN naming all three qitem IDs (each 51m), exit 0 |
| 6 | `--strict` promotion (REQ-LH7) | PASS | Same + `--strict` -> `LIVE-HEALTH FAIL`, exit 2 (note: do not pipe through `tail` when reading `$?`) |
| 7a | T2 heartbeat P0: zero `heartbeat_sec: 0` (REQ-LH3) | PASS | `grep -c "heartbeat_sec: 0" fleet/fleet.yaml` -> `0` (no matches) |
| 7b | No generated-leaf edits; verify-rigs.sh untouched (AGENTS.md one-rule) | PASS | `git diff HEAD --stat -- specs/ rigs/ rosters/ registry/` -> empty; `scripts/verify-rigs.sh` absent from commit `761b1ac` file list |
| 8 | SAB-1 stuck-row flips WARN->FAIL + names ID (REQ-LH5) | PASS (RED proven) | Sabotaged overdue fixture (45m row `qitem-stuck-001`) -> WARN naming it, exit 0; `--strict` -> FAIL, exit 2 |
| 9 | SAB-2 empty queues PASS, no false positive (REQ-LH4/5/6) | PASS | Emptied queue fixtures -> pickup/stuck/undelivered PASS; overall SKIP banner (no healthy banner with a SKIP source) |
| 10 | SAB-3 malformed transitions -> SKIP-with-reason (REQ-LH2) | PASS (RED proven) | Corrupt transitions JSON -> `[SKIP] pickup: transitions unreadable for: <3 IDs>`, `sources: 4 ok, 1 skipped`, no healthy banner |
| 11 | SAB-5 UNCONFIGURED role caps heartbeat at WARN + named (REQ-LH3) | PASS (RED proven) | `fleet_heartbeat.json` with one `0` role -> `[WARN] heartbeat: UNCONFIGURED heartbeat roles (1): a11y-specialist; ...`, exit 0 |
| 12 | SAB-6 dead daemon -> all-SKIP, never healthy (REQ-LH2/T6b) | PASS (RED proven) | `RIG_PATH=/nonexistent/rig-binary` -> 5x SKIP by name, `sources: 0 ok, 5 skipped`, `LIVE-HEALTH SKIP` banner, exit 0 |
| 13 | SAB-7 live pass performs zero mutations (REQ-LH8/T6c) | PASS | PATH-shim argv log shows only `queue list/transitions/overdue/undelivered` + `ps --nodes --json --no-cleanup -A`; no claim/update/block/resolve/handoff/send |
| 14 | SAB-8 unit suite goes RED when breach masked (vacuity guard) | PASS (RED proven) | `t_pickup_min * 1000000` mutation -> `FAILED (failures=2)`, exit 1; `git checkout --` restore -> clean status, 21 tests OK |
| 15 | Env/flag tuning path (REQ-LH7) | PASS | `LH_T_PICKUP_MIN=1` replay prints effective values and names all 3 rows. Note: `make live-health` forwards no extra args; tuning is via direct script flags/env as documented |
| 16 | Read-only discipline (no stage-attributable mutations) | PASS | Verifier ran reads + fixture replays only; SAB-7 log is the proof; `git status --short` clean except this QA evidence |

## Findings

1. Regen gap (stated in implementation report, confirmed benign): `generate-rigs.py`
   refuses in this worktree (missing gitignored `.scratch/vendor/*` pins, fails
   identically on pristine tree); provenance-only `resolvedCommit` hunks were reverted.
   Verified: no `specs/ rigs/ rosters/ registry/` diff, `make verify` 22/0. NOT blocking.
2. Live fleet shows heartbeat WARN (daemon `lastHeartbeat: null`) + 2 idle-at-prompt
   holders — genuine fleet signal surfaced by design (warn-first), not a gate bug.
   No stuck/overdue/undelivered rows live. NOT blocking.
3. No vacuous checks. No FAILs on the unmodified tree. No skipped acceptance items.

## Verdict

**QA-CLEAN.** Stage `wave-45-live-health` (commit `761b1ac`) passes all acceptance
checks; every gate was red-proven to discriminate. Evidence log at
`docs/evidence/wave-45-live-health/red-proofs.log`. Nothing committed (coordinator
commits evidence next); worktree contains no implementation modifications beyond
the stage commit — only `docs/evidence/` + `docs/reports/` additions from this QA pass.

---

# Re-verification appendix: review-driven fixes (d1db5e4 + 5724316) — QA-CLEAN

- Verifier date (UTC): 2026-10-22. Commits under test: `d1db5e4` (six review
  fixes) + `5724316` (stale-note touch-up), on top of `761b1ac`. No commits by
  this verifier; all sabotage reverted (`git status --short` clean except
  `docs/evidence/` + `docs/reports/`).
- Evidence: `docs/evidence/wave-45-live-health/red-proofs.log` (new dated section
  appended at end; original log untouched). Scratch outputs: `/tmp/opencode/rp45/`.

## Per-item verdicts

| # | Check | Result | Exact command + output |
|---|---|---|---|
| R1 | Full suite 28 tests OK | PASS | `python3 -m unittest tests/test_render_seat.py tests/test_live_health.py` -> `Ran 28 tests ... OK`, exit 0 |
| R2 | `make verify` 22/0 + advisory | PASS | -> `SUMMARY: 22 checks passed, 0 failed.`, exit 0; advisory WARN heartbeat (7 stale) + SKIP seat-idleness, `sources: 4 ok, 1 skipped` |
| R3 | `openspec validate remediate-45-live-health` | PASS | -> `Change 'remediate-45-live-health' is valid`, exit 0 |
| R4a | Truncation guard: at-cap -> DataSourceError/SKIP, under-limit passes | PASS (RED proven) | Stub 100 rows/limit 100 -> `DATASOURCEERROR: ... hit the fetch cap (100) ... refusing to report healthy`; 99 rows -> `RETURNED 99`; full entrypoint at-cap -> `LIVE-HEALTH SKIP, sources: 0 ok, 5 skipped`. Guard-disabled sabotage -> `RETURNED 100`; restored clean |
| R4b | Pickup semantics: replay WARNs all 3; within-T passes; no-transition breaches on age | PASS (RED proven) | Replay -> WARN naming all three IDs; 5m-latency row -> PASS; 65m untouched row -> WARN; 26m-late row -> WARN (25.6m latency). Pre-fix-semantics sabotage -> `FAILED (failures=1)`; restored clean |
| R4c | ps pinning: bare/reduced `ps` refused, pinned combo passes | PASS (RED proven) | `check_allowed(["ps"])` + `["ps","--nodes","-A","--json"]` -> RuntimeError; full pinned combo -> allowed. Bare-return sabotage -> both ALLOWED; restored clean |
| R4d | Stub-log test non-vacuity | PASS (RED proven) | Silent-stub sabotage -> `AssertionError: '' is not true : stub log must record at least one command`, exit 1; restored clean, `TestReadOnly` OK |
| R5 | §4 audit-note + test rename consistency | PASS | `grep test_post_claim_transition_clears_breach` -> 0 hits outside logs; tree has `test_late_first_transition_warns` and verification §4 describes it (WARN on late first transition). Behavior matches: 26m-late row breaches with latency, not cleared |
| R6 | Read-only discipline spot-check (live gate argv audit) | PASS | PATH-shim log shows only `queue list/transitions/overdue/undelivered` + `ps --nodes --json --no-cleanup -A`; mutating-verb grep -> 0 hits; log at `/tmp/opencode/rp45/audit/argv.log` |

## Findings

1. One sabotage attempt (SAB-R2 naive `and False` variant) did not go red because
   the age fallback still breached — discarded and replaced with the faithful
   pre-fix-semantics revert, which went red as required. Record of the method,
   not a finding against the stage.
2. No vacuous checks. No FAILs on the unmodified tree. No skipped acceptance items.

## Verdict

**QA-CLEAN (re-verification).** Review-driven changes on `d1db5e4` + `5724316`
pass all acceptance checks; every new behavior was red-proven to discriminate.
Nothing committed (coordinator commits evidence next).
