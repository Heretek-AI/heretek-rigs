# Proposal: remediate-45-live-health — warn-first live-fleet health gate

## Status
Spec-only change package for issue #45. No implementation in this package;
`tasks.md` is the testable checklist the implementation stage follows.

## Motivation
`scripts/verify-rigs.sh` (22 checks, ~1343 lines) validates generated leaves,
schemas, digests, and unit tests — all static. Nothing checks the *running*
fleet: seat liveness, queue pickup latency, stuck-row backlogs, undelivered
nudges. On 2026-10-22/23 three W4 seats claimed rows at 11:14 and produced
zero transitions for ~50 minutes (idle-at-prompt, no blockers) while verify
read 22/0 throughout; discovery required manual transcript inspection. The
watchdog's nightly done-row sweeps file the same stuck rows as toil, not
signal. Two `rig send` calls returned producer-link/instrumentation advisories
yet delivered — telemetry degrades silently.

Related: #17 (utilization/throughput) — this change is its concrete,
checkable subset.

## Fact sources (verified read-only before authoring)
- `fleet/fleet.yaml`: 51 `heartbeat_sec` entries, **49 set to `0`**
  (only 2 nonzero: 1800, 3600). Heartbeat-based liveness has no data source
  until the catalog configures it — prerequisite P0 below.
- `scripts/verify-rigs.sh`: zero matches for heartbeat/pickup/stuck/overdue/
  undelivered checks (only incidental "live" strings about schemas/secrets).
- `rig queue` CLI (on PATH, read-only `--help` probes): `overdue` (in-progress
  past `closure_required_at`), `undelivered` (PENDING rows whose create-path
  nudge FAILED), `list --state`, `show`, `transitions`, `ps --nodes`
  (`agentActivity.state`, `contextUsage`) all exist — no new daemon verbs
  required.

## Boundaries
- Touch ONLY: a NEW gate script alongside `scripts/verify-rigs.py`/
  `scripts/verify-rigs.sh` (implementer picks language consistent with repo
  tooling), a NEW `make live-health` target, `fleet/fleet.yaml` heartbeat
  values (P0 prerequisite, via surgical edit + regen), and docs.
- MUST NOT renumber or reword the existing 22 `verify-rigs.sh` checks
  (AGENTS.md:45 audit-baseline rule).
- Read-only against the daemon: the gate MUST NOT mutate queue or session
  state (no claim/update/block/resolve/send).
- Warn-first rollout: the gate warns loudly on breach; it does not fail
  `make verify` or block merges until thresholds are calibrated (promotion
  policy in spec).

## Non-goals
- No dashboard UI, no auto-remediation (no auto-unclaim/reassign/nudge).
- No change to watchdog sweep behavior (covered by #38 package if at all).
- No fleet-wide heartbeat interval tuning beyond enabling the data source
  (P0 sets sane nonzero values; per-role tuning is later work).
- Upstream `rig` CLI changes (none needed — all primitives exist).

## Acceptance (see tasks.md)
1. `make live-health` exits 0 with a WARN banner (not FAIL) on a fleet
   exhibiting the 2026-10-22 shape, naming each breaching row ID.
2. Returnable: replaying the 50-minute idle stretch (three claimed-but-
   untouched rows) against the new gate produces WARN (or FAIL post-
   promotion) with the three row IDs named — never a clean PASS.
3. Gate reports SKIP (never PASS) for any sub-check whose data source is
   unreachable or unconfigured; `make verify` still reads 22/0.
