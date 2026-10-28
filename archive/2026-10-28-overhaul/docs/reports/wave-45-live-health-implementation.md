# Stage implementation report: wave-45-live-health

- Stage/wave id: `wave-45-live-health` (issue #45)
- Change id: `remediate-45-live-health`
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-45-live-health`
- Branch: `remediate/45-live-health` (from `origin/main @ 5a478b5`)
- Date (UTC): 2026-10-22

## Deliverables

Warn-first live-health gate alongside (never inside) the static 22 checks:

1. **`scripts/live-health.py`** (new, executable) — read-only live-fleet gate
   with PASS/WARN/FAIL/SKIP per sub-check (`pickup`, `stuck-overdue`,
   `undelivered`, `heartbeat`, `seat-idleness`), `sources: N ok, M skipped`
   summary, advisory exit 0, `--strict` promotion to FAIL/exit 2,
   `--fixture-dir` deterministic replay, tunable
   `T_pickup/T_stuck/T_undelivered/T_hb` (flags + `LH_*` env, printed per run).
   Mutating verbs refused by `check_allowed()` (fail-closed, REQ-LH8).
2. **`fleet/fleet.yaml`** — T2 P0 prerequisite: all 49 `heartbeat_sec: 0`
   roles set to `1800` (matches the existing `exec-director` precedent;
   per-role tuning out of scope per spec non-goals). `grep -c` for zeros is 0.
3. **`Makefile`** — new `make live-health` target (independent of verify);
   `make verify` now runs `verify-rigs.sh` unchanged followed by the advisory
   gate (22 outcomes untouched; warn-first exit 0 preserved).
4. **`tests/test_live_health.py`** — 21 unittest cases (TDD red->green)
   covering every tasks.md testable: incident replay (T6a), dead-daemon SKIP
   at gate + subprocess level (T3/T6b), read-only argv audit + allowlist
   refusal (T6c), strict promotion, fail-closed config, idle/unknown activity.
5. **`tests/fixtures/live-health/incident-2026-10-22/`** — 6 saved JSON
   fixtures (faithful synthetic equivalents, recorded timestamps) so the
   50-minute idle returnable replays deterministically without the daemon.
6. **`docs/live-health.md`** — gate doc: read-only contract, sub-checks,
   idle definition (REQ-LH9), histogram buckets, thresholds, SKIP-is-never-
   PASS, promotion policy + anti-rot rule (REQ-LH7), fixture format.

`scripts/verify-rigs.sh` is byte-identical (audit-baseline rule honored).

## Tasks.md checklist

- T1 (pin parseable sources): DONE — `rig queue list/overdue/undelivered`
  `--json -A`, `queue transitions --json <id>`, `ps --nodes -A --json` all
  return clean parseable JSON; no #44 trailer mixing observed, dependency on
  the #44 fix NOT triggered, proceeded. `daemon status` is plain-text
  (reachability only). Evidence: command lines + outputs recorded in this
  report; live run below.
- T2 (P0 heartbeat): DONE — 49 zeros -> 1800 via surgical text edit
  (no `yaml.safe_dump`); regen attempted via sanctioned path (see notes);
  `make verify` 22/0; `grep -c "heartbeat_sec: 0"` == 0.
- T3 (skeleton): DONE — exit-0 SKIP run proven by dead-daemon tests.
- T4 (pickup/stuck/undelivered): DONE — unit + live proven.
- T5 (heartbeat/idleness + promotion doc): DONE — `docs/live-health.md`;
  all-configured+fresh PASS proven by unit test; live fleet reports WARN
  (daemon `lastHeartbeat` null — visible, not silent).
- T6 (red-proofs): DONE — (a) fixture replay WARN names all 3 IDs;
  (b) dead-daemon SKIP never PASS; (c) recording-stub run shows zero
  mutating verbs (asserted in test suite).
- T7 (acceptance): DONE — see command outputs below.
- T8 (report): this file.

## Acceptance commands (exact outputs)

- `python3 -m unittest tests/test_render_seat.py tests/test_live_health.py`
  -> `Ran 28 tests ... OK` (exit 0).
- `make live-health` -> `LIVE-HEALTH WARN (advisory, exit 0)` naming 7
  heartbeat-stale sessions + 2 idle-at-prompt holders; pickup/overdue/
  undelivered PASS on the live fleet (incident rows have since progressed);
  `sources: 5 ok, 0 skipped`; exit 0.
- Fixture replay:
  `python3 scripts/live-health.py --fixture-dir
  tests/fixtures/live-health/incident-2026-10-22 --now 2026-10-22T12:05:00Z`
  -> WARN naming all three row IDs
  (`qitem-20261022111416-78213c07c3272cbc`,
  `qitem-20261022111410-8d4e00317b7b6621`,
  `qitem-20261022111413-ea9f86772c241179`, each 51m); exit 0;
  with `--strict` -> exit 2.
- `make verify` -> `SUMMARY: 22 checks passed, 0 failed.` (exit 0) followed
  by the WARN advisory above (exit 0).
- `openspec validate remediate-45-live-health` -> `Change
  'remediate-45-live-health' is valid`.

## T1 probe evidence (2026-10-22, live daemon, read-only)

- `rig queue overdue --json -A --limit 5` -> `[]` (exit 0)
- `rig queue undelivered --json -A --limit 5` -> `[]` (exit 0)
- `rig queue list --json -A --limit 3` -> 3 rows incl.
  `pickup.state: stalled-after-claim` corroboration, `claimedAt`,
  `lastHeartbeat: null` (exit 0)
- `rig queue transitions --json qitem-20261022111416-...` -> 9-entry log
  (created/claimed/blocked/in-progress..., exit 0)
- `rig ps --nodes -A --json` -> 51+ node rows with
  `agentActivity.state` (`unknown`/`idle-at-prompt` mix), `lastActivity`
  (exit 0). Note: `ps --nodes` requires explicit `-A` outside a managed
  session (AGENTS.md live-notes) — the gate always passes scope flags.
- `rig daemon status` -> `Daemon running on port 7433` (exit 0)

## Self-audit notes (unfinished / deferred, stated plainly)

- Regen nuance (documented deferral, not silent): `generate-rigs.py`
  refuses in this worktree because gitignored `.scratch/vendor/*` pins are
  absent here (fails identically on the pristine tree — pre-existing
  environmental gap, proven via stash). Regen was run via the sanctioned
  path with `--vendor-dir` + `--crew-source` pointed at the main checkout
  (read-only inputs; all writes inside this worktree): output was
  byte-identical except `registry/*` `resolvedCommit` re-lagging to the
  worktree base `5a478b5` (the known per-merge re-lag documented in
  AGENTS.md). Those provenance-only hunks were reverted to keep the diff
  surgical — `heartbeat_sec` flows into no generated leaf (zero matches in
  `specs/`, `rigs/`, `rosters/`, `registry/` before or after), and
  `make verify` stays 22/0 either way. Merge-time regen will re-stamp
  provenance normally.
- Catalog fix rationale (T2): single value `1800` for all 49 roles follows
  the in-repo `exec-director` precedent; per-role interval tuning is an
  explicit non-goal. Heartbeat WARN-noisy on the live fleet until the daemon
  populates `lastHeartbeat` — by design (REQ-LH3/LH7.2), never silent.
- No queue creates/sends/updates and no seat mutations were performed;
  all daemon contact was the read-only verbs above plus gate runs.
- Not done (out of scope): dashboard UI, auto-remediation, watchdog changes,
  upstream `rig` changes, `--strict` in CI (needs T7 calibration + approval).
