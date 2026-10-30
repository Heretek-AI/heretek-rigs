# Seat-race

## Purpose

Bounded live-seat exercise closing the four Wave-3 gaps carved into #140:
seat-execution parallelism, claim-latency-under-contention, the
first-degrading metric under real seat load, and failure isolation under a
real failing slice. Four racer seats run probe workloads (timed samples +
claim attempts + self-check, never engine work) against two synthetic rows
in one contention window. Each requirement is a runbook obligation with
binary evidence (rc=0 artifact or honest abort). Refs #16, Refs #17,
Refs #140 — never Closes.

## ADDED Requirements

### Requirement: REQ-SR1 — race mechanics: 4 racers, 2 rows, pinned base, honest join-or-abort

The exercise MUST launch at most 6 seats total (4 racers + up to 2
fresh-relaunch spares, each launch disclosed with reason), create exactly
2 synthetic rows (`SEAT-RACE-1`, `SEAT-RACE-2`, tags
`seat-race,synthetic,probe`, `--no-nudge`, never real tracker rows), pin
the base SHA per slice at fan-out, abort on the first non-scripted RED,
and close with per-racer proofs plus the runbook join. No racer is cited
green until the join.

#### Scenario: join or honest abort

- When the exercise finishes, either every non-scripted-failure racer has
  a proof artifact AND the runbook join records winners/losers with the
  pinned base SHA — or the runbook shows the abort point, the failing
  racer, and the pinned base SHA — with pre/post `rig ps` snapshots and
  zero residue (no synthetic rows left open, no probe dirs left on disk,
  no queue residue).

#### Scenario: fallback composition recorded

- When the kickoff health snapshot mismatches the Wave-3 baseline, the
  runbook records NO-GO and no launch, row, or send happens until the
  coordinator clears it; the composition that actually ran (including any
  spare launches and the scripted-failure racer) is recorded in the
  runbook.

### Requirement: REQ-SR2 — isolation: failed slice pins base, others continue, no rebase

Racer D's proof command MUST fail at the FIXED scripted step (`false`,
post-claim) → D pins the base SHA and stops without closing anything;
the other racers MUST continue on the pinned base with NO rebase, and the
operator MUST close any D-held row as `canceled` at cleanup with the
reason recorded.

#### Scenario: scripted failure contained

- When D's step 3 exits nonzero, D reports STOPPED-SCRIPTED-FAILURE with
  the pinned base SHA, performs no further claims or closes, and the
  runbook shows the remaining racers completing on the same base SHA with
  no rebase event.

#### Scenario: join-or-honest-abort under failure

- When the exercise closes, the evidence distinguishes the scripted D
  stop (expected, non-aborting) from any genuine RED (aborting); a
  genuine RED in any other racer aborts the window per REQ-SR1.

### Requirement: REQ-SR3 — metrics: per-metric observations plus first-degrading named

The exercise MUST record, across the full race window: per-row claim
latency (`claimedAt − tsCreated` primary, `claimedAt − window-open`
secondary), refused-claim receipts (losers), stuck-sweep volume, periodic
snapshot cost, daemon responsiveness, and ACTIVE/queue-depth samples with
idle classified correctly-vs-spuriously. The report MUST name the
first-degrading metric, or record "none degraded in this run" with one
labeled watched-candidate projection and the unobservable-with-reason
note for any metric that could not be observed.

#### Scenario: metrics with a named bottleneck or honest none-degraded

- When the exercise closes, `metrics.log` states per-metric observations
  (claim-latency series, winner/loser outcomes, watchdog/stuck-sweep
  behavior, snapshot cost, daemon responsiveness, ACTIVE/queue-depth
  samples with idle classified) and names exactly one first-degrading
  metric, or records "none degraded in this run" plus one labeled
  watched-candidate projection.
