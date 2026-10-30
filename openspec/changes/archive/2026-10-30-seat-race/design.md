# Design: 2026-10-30-seat-race

## Why 4 racers × 2 rows forces winner + loser

Queue rows are single-owner: the first `claim` moves pending →
in-progress and later claims on the same row are refused. With 4 racers
attempting the same 2 rows in one contention window, each row yields
exactly one winner; every other attempt on an already-claimed row is a
recorded loss. Two rows (not one) keep two independent winner/loser pairs
observable and leave room for the scripted-failure racer to hold a claim
without collapsing the whole window to a single data point.

## Contention-window mechanics

1. Kickoff: `rig ps --nodes -A` re-snapshot vs the Wave-3 baseline
   (51 fleet `run`/`idle`, 111 lines, WORK pattern); GO or NO-GO.
2. Fan-out: create `SEAT-RACE-1` + `SEAT-RACE-2` with
   `--json --verify --no-nudge --source seat-race`, tags
   `seat-race,synthetic,probe`. Record per-row qitem IDs + `tsCreated`.
   Cold rows by design (synthetic destinations match no live seat; no live
   seat nudged) — they warm only when racer seats claim them by ID.
3. Launches: 4 idle no-WORK fleet seats get fresh occupants
   (`rig seat launch --fresh --stop --reason "seat-race …"`), one reason
   per launch, hard ceiling 6 total including spares. Boot wait until all
   four accept `send`.
4. Window open: the 4 probe prompts go out back-to-back (`rig send
   --verify`). Window-open timestamp = last prompt send. Claim latency per
   row = `claimedAt − tsCreated` (primary) and `claimedAt − window-open`
   (secondary); loser attempts = refused-claim receipts with timestamps.
5. Race: each racer runs timed `rig queue list --json` + `rig ps --nodes`
   samples, attempts both rows by ID in fixed order (R1 then R2), runs its
   self-check (`rig queue show <won-row>` echoing its own claim), and
   reports DONE with rcs. Racer D runs the identical steps except step 3
   is the FIXED scripted failure (`false`): on rc≠0 it stops immediately,
   pins the base SHA, reports STOPPED-SCRIPTED-FAILURE, and closes nothing
   (the operator closes any D-held row as `canceled` at cleanup).
6. Join: per-racer proofs (`proof-a/b/c/d.json`, operator-captured from
   transcripts + queue transition logs) plus this runbook; none cited
   green until the join. No rebase at any point — survivors continue on
   the pinned base `2b3999b`.
7. Cleanup: rows closed under the exercise's own declared `--source`
   `seat-race` identity (Wave-3 pattern: the bare close fails closed
   first, the attributable retry is recorded; both recorded here),
   `/tmp/opencode/seat-race/` removed, residue verified via
   `rig queue list --json`, post `rig ps` snapshot compared to kickoff.

## Scripted-failure step (fixed, deterministic)

Racer D step 3 is `false` — rc=1 by construction, independent of fleet
state. It runs AFTER D's claim attempts so D still contends (and may hold
a claim, which the operator cancels at cleanup with the reason recorded).
D's stop exercises the Wave-3 isolation rule for real: failed slice pins
base, others continue, no rebase. If any OTHER racer hits a RED first,
that is a genuine abort (not the scripted path) and the exercise stops.

## Probe-workdir partitioning

Racers are LLM seats, not shells: their "workdirs" are their own seat
sessions — disjoint by construction. No repo writes are requested or
expected from any racer (read-only `rig` observability commands only,
plus `queue claim` mutations on the two synthetic rows). Operator-side
scratch lives in `/tmp/opencode/seat-race/` (0600, removed post-run).

## Operator-touch audit plan

Every operator touch is numbered in the runbook with rc/evidence and
tagged automatable-under-current-charters vs needs-new-scope (#12
build-runner remains the standing candidate for queue-write authority
and seat-identity judgment calls), same ledger shape as Wave 3 §8. No
charter changes in this exercise.

## Metrics plan (#17 items 1–2 riding along)

Across the window: per-row claim latency (the newly-observable metric),
refused-claim count/timing (losers), stuck-sweep volume (`overdue`,
`transitions`), periodic snapshot cost (timed `ps`), daemon
responsiveness (timed queue reads), ACTIVE/queue-depth samples with idle
classified correctly-vs-spuriously. The report names the first-degrading
metric, or records "none degraded in this run" plus one labeled
watched-candidate projection (Wave-3 pattern).

## Round-2 appendix (executed adaptation, 2026-10-30 ~15:13–15:17Z)

Round 1 falsified the §"Why 4 racers × 2 rows" contention premise live:
the daemon enforces destination-matching on claim (7/7 cross-seat
attempts → `claim_destination_mismatch`), so one row cannot be contended
across seats. Adaptation (minimal, rationale recorded): `rig queue
fallback` rerouted R1→racer B and R2→racer C (designed path for
unreachable destinations; row count preserved at exactly 2; no new rows,
no new launches). Round-2 prompts used bare `rig` commands only (seat
sandboxes deny echo/date/pipes; D denies even bare echo while allowing
`whoami` — per-seat policy variance). The scripted gate moved D→C with
rationale (D environmentally blocked at step 0; C functionally
equivalent); C's `false` was then denied by the same policy, so the
gate never executed — REQ-SR2 scenario unexecuted, isolation observed
only emergently (A's round-1 stop while others continued, no rebase).
Lesson for #16 probe design: scripted failure steps must be allow-listed
`rig` commands; `false`/builtins are not executable in-seat.
