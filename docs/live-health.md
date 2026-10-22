# Live-fleet health gate (warn-first)

`make live-health` runs `scripts/live-health.py`, a **read-only** probe of the
running fleet alongside (never inside) the static 22-check `verify-rigs.sh`
gate. It answers the question verify cannot: *are seats alive and is claimed
work moving?* (issue #45; change `remediate-45-live-health`.)

## Read-only contract (REQ-LH8)

The gate ONLY invokes:

- `rig queue list | overdue | undelivered | show | transitions` — always with
  `--json` (the pinned parseable combo; bare `--json` was probed clean on
  2026-10-22, so the #44 trailer dependency did not trigger)
- `rig ps --nodes --json --no-cleanup` (`--no-cleanup` preserves stale daemon
  state files during observation)
- `rig daemon status` (plain-text reachability probe)

Anything else raises `RuntimeError` inside `check_allowed()` and fails closed.
A subprocess-level red-proof (`tests/test_live_health.py::TestReadOnly`)
runs the gate against a recording stub `rig` and asserts zero mutating verbs
(`claim/update/block/resolve/handoff/send/create/unclaim/...`).

## Sub-checks

| Name | Sources | Breach |
|---|---|---|
| `pickup` (REQ-LH4) | `queue list` + per-row `queue transitions` | claimed (in-progress) row with no transition after `claimedAt` for longer than `T_pickup`; row ID + age named |
| `stuck-overdue` (REQ-LH5) | `queue overdue` | any row past `closure_required_at` (fallback `tsUpdated`) older than grace `T_stuck`; every row ID named plus age histogram |
| `undelivered` (REQ-LH6) | `queue undelivered` | PENDING row with failed create-path nudge older than `T_undelivered` (age since `lastNudgeAttempt`, fallback `tsCreated`); row ID + age named |
| `heartbeat` (REQ-LH3) | `queue list` (`lastHeartbeat`) + `fleet/fleet.yaml` (`heartbeat_sec`) | session holding claimed rows whose heartbeat is older than `T_hb = hb_mult x role heartbeat_sec`, or missing; roles with `heartbeat_sec: 0` reported as UNCONFIGURED (counted + named, never silently skipped); while any role is UNCONFIGURED the sub-check reports at most WARN |
| `seat-idleness` (REQ-LH9) | `ps --nodes` (`agentActivity.state`) joined with claimed-row holders | seat idle-at-prompt (see definition) while holding claimed rows is named; unknown/unparseable activity states resolve to SKIP for that seat, never to healthy |

Idle definition: `agentActivity.state`, case/separator-insensitive, in
`{idle, idle-at-prompt, waiting, waiting-for-input}` AND holding >= 1 claimed
row. `{running, active, busy, working}` counts as active. Everything else
(including `unknown` and missing rows) is SKIP-per-seat.

Overdue histogram buckets: `<=T_stuck` (grace), `T_stuck-2xT_stuck`,
`>2xT_stuck`, measured as age past `closure_required_at`.

## Thresholds

Defaults (starting point; operator-tunable, printed on every run):

- `T_pickup = 15m` (`--t-pickup-min` / `LH_T_PICKUP_MIN`) — the 2026-10-22
  incident idled ~50m; 15m catches it with margin for slow-seat starts.
- `T_stuck = 30m` (`--t-stuck-min` / `LH_T_STUCK_MIN`)
- `T_undelivered = 15m` (`--t-undelivered-min` / `LH_T_UNDELIVERED_MIN`)
- `T_hb = 3x role heartbeat_sec` (`--hb-mult` / `LH_HB_MULT`) — adapts to
  per-role intervals once the P0 catalog fix lands (all 51 roles now nonzero;
  per-role tuning is later work).

Unparseable threshold config exits 2 with a usage error (fail-closed on
config, distinct from fleet state). Per-row fetch cap: `--limit` (default 100).

## SKIP is never PASS (REQ-LH2)

Every sub-check reports PASS / WARN / FAIL / SKIP. Unreachable daemon,
errored verbs, unparseable output, and unconfigured sources report SKIP **by
name**; the summary always prints `sources: N ok, M skipped`; any SKIP
suppresses the passing banner. Advisory exit code is 0 even with WARN/SKIP.

## Warn-first rollout and promotion policy (REQ-LH7)

On landing, breaches WARN + exit 0: the gate never fails `make verify` and
never blocks merges. Promotion to failing happens only when ALL of these hold:

1. Calibration evidence: baseline distributions of pickup latency and
   stuck-row age collected from >= 14 days of warn-first runs, with proposed
   threshold values justified against that baseline.
2. Heartbeat data source live: `lastHeartbeat` populated by the daemon for
   the assessed sessions (until then heartbeat stays WARN-noisy by design).
3. Human approval recorded (issue or review thread) naming the approver.

Then CI passes `--strict` (WARN -> FAIL, exit 2). Anti-rot rule: if promotion
has not happened within 30 days of landing, the owning team either promotes
or records a dated deferral with rationale. The returnable holds at every
stage: replaying the 2026-10-22 50-minute idle shape (three claimed-but-
untouched rows) yields WARN (or FAIL post-promotion) naming all three IDs:

```bash
python3 scripts/live-health.py \
  --fixture-dir tests/fixtures/live-health/incident-2026-10-22 \
  --now 2026-10-22T12:05:00Z
```

`--fixture-dir` replays saved JSON (`queue_list.json`, `queue_overdue.json`,
`queue_undelivered.json`, `ps_nodes.json`, `transitions.json`,
`fleet_heartbeat.json`) for deterministic QA without touching the daemon.
