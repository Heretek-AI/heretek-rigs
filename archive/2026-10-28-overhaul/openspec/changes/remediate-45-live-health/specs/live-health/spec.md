# Delta spec: live-fleet health gate (warn-first)

## ADDED Requirements

### Requirement: REQ-LH1 — New gate alongside the static 22, never inside them
A live-health gate script (new file under `scripts/`, implementer picks
`live-health.sh` vs `.py` consistent with repo tooling) MUST exist separately
from `scripts/verify-rigs.sh`. It MUST NOT renumber, reword, or alter the
PASS/FAIL outcome of any of the existing 22 checks. A `make live-health`
target MUST run it independently of `make verify`.

#### Scenario: Static gate untouched
- WHEN `make verify` runs after this change lands THEN all 22 pre-existing
  checks report identical outcomes to before AND `make live-health` executes
  as an independent target.

### Requirement: REQ-LH2 — SKIP is never PASS (the anti-#45 core)
Each sub-check MUST report exactly one of PASS / WARN / FAIL / SKIP. Any
sub-check whose data source is unreachable (daemon down, `rig` error,
unparseable output) or unconfigured MUST report SKIP, MUST be listed by name
in the gate summary, and MUST NOT be counted toward healthy totals. The gate
summary MUST print `sources: N ok, M skipped` (or equivalent) on every run,
and a run with any SKIP MUST NOT print an unqualified healthy banner.

#### Scenario: Dead daemon cannot look healthy
- WHEN the daemon is unreachable THEN every live sub-check reports SKIP by
  name, the summary shows zero healthy sources, and no healthy banner
  appears.

### Requirement: REQ-LH3 — Heartbeat freshness with UNCONFIGURED explicitness
For each running seat whose role configures `heartbeat_sec > 0`, the gate
MUST compare heartbeat age against threshold `T_hb` and WARN/FAIL on breach.
Roles with `heartbeat_sec: 0` MUST be reported as UNCONFIGURED (counted and
named, not silently skipped): while any role is UNCONFIGURED the heartbeat
sub-check MUST report at most WARN (never PASS). Prerequisite P0
(`fleet/fleet.yaml` sets sane nonzero `heartbeat_sec`, regen, `make verify`
22/0) MUST land before the heartbeat sub-check can report PASS.

#### Scenario: Unconfigured heartbeats block a clean PASS
- WHEN any role retains `heartbeat_sec: 0` THEN the heartbeat sub-check
  names the UNCONFIGURED roles and reports at most WARN, even if every
  configured seat is fresh.

### Requirement: REQ-LH4 — Claim-to-first-transition pickup latency
For every claimed row (pending → in-progress via `claim`), the gate MUST
compute pickup latency (claim timestamp → first subsequent transition, via
`rig queue list` + `rig queue transitions`) and MUST name each row exceeding
`T_pickup` with its age. Breach disposition follows REQ-LH7 (warn-first).

#### Scenario: Claimed-but-untouched row is named
- WHEN a row was claimed longer than `T_pickup` ago with no subsequent
  transition THEN the gate output contains that row's ID with its age.

### Requirement: REQ-LH5 — Stuck-row age via `overdue`
The gate MUST query `rig queue overdue` (in-progress past
`closure_required_at`) across rigs and MUST emit a stuck-row age histogram
(buckets defined by the implementer, documented in `--help`/docs). Any
non-empty overdue set older than grace `T_stuck` MUST trigger WARN (FAIL
post-promotion) with every row ID named.

#### Scenario: Overdue backlog surfaces with IDs
- WHEN `rig queue overdue` returns rows older than `T_stuck` THEN the gate
  warns (or fails post-promotion) and every such row ID appears in the
  output alongside the age histogram.

### Requirement: REQ-LH6 — Undelivered-nudge backlog via `undelivered`
The gate MUST query `rig queue undelivered` (PENDING rows whose create-path
nudge FAILED) and MUST list each row ID with its age. A non-empty set older
than grace `T_undelivered` MUST trigger WARN (FAIL post-promotion).

#### Scenario: Failed nudges are listed
- WHEN `rig queue undelivered` returns rows older than `T_undelivered`
  THEN the gate warns (or fails post-promotion) naming each row ID with
  its age.

### Requirement: REQ-LH7 — Warn-first rollout with a promotion policy
On first landing, threshold breaches MUST produce WARN + exit 0 (the gate
MUST NOT fail `make verify`, MUST NOT block merges). Thresholds (`T_hb`,
`T_pickup`, `T_stuck`, `T_undelivered`) MUST be operator-tunable via flags/env
with documented defaults, and the promotion policy (what calibration evidence
flips WARN → FAIL, who approves) MUST be documented in the gate's docs. The
returnable MUST hold: replaying the 2026-10-22 50-minute idle stretch (three
claimed-but-untouched rows) yields WARN or FAIL naming all three row IDs.

#### Scenario: Incident replay cannot pass clean
- WHEN the gate runs against a fleet shaped like the 2026-10-22 incident
  (three claimed rows, ~50 minutes, zero transitions) THEN the result is
  WARN or FAIL and all three row IDs are named.

### Requirement: REQ-LH8 — Read-only against the fleet
The gate MUST NOT mutate queue or session state: no `claim`, `update`,
`block`, `resolve`, `handoff`, `send`, or watchdog-arming calls. Observation
MUST pass `--no-cleanup` (or equivalent non-destructive flags) wherever the
CLI offers a destructive default.

#### Scenario: Gate run leaves zero mutations
- WHEN the gate runs a full pass against the live daemon THEN a diff of
  `rig queue list --all` (plus daemon transition logs) before and after
  shows zero new transitions attributable to the gate.

### Requirement: REQ-LH9 — Seat-idleness signal via `rig ps`
The gate MUST include a seat-activity sub-check sourcing `rig ps --nodes`
(`agentActivity.state`, `contextUsage`) that names seats idle-at-prompt while
holding claimed rows. Exact idle definition (state value + holding-row join)
MUST be documented; unknown/unparseable activity states MUST resolve to SKIP
per REQ-LH2, never to healthy.

#### Scenario: Idle holder named, unknown state skipped
- WHEN a seat is idle-at-prompt per the documented definition while holding
  claimed rows THEN the seat is named; WHEN its activity state is
  unparseable THEN the sub-check reports SKIP instead of healthy.
