# Proposal: 2026-10-30-seat-race — bounded live seat-claim race (#140 carved remainder)

## Goal

Close the four Wave-3 gaps carved into #140 with ONE bounded live-seat
exercise: 4 racer seats chase 2 synthetic queue rows (`SEAT-RACE-*`) in a
single contention window, proving (1) seat-execution parallelism (in-seat
claims, not local shells), (2) claim-latency-under-contention (observable
`claimedAt` now that live seats claim, unlike Wave 3's cold rows),
(3) the first-degrading metric under real seat load, and (4) failure
isolation under a real failing slice (the armed-but-untested Wave-3 rule:
failed slice pins the base SHA, survivors continue, no rebase).
Refs #16, Refs #17, Refs #140 — never Closes (all three issues stay open
until a triad records `VERDICT: PASS` on live behavior).

## Non-goals

- No real tracker writes: synthetic rows only (`SEAT-RACE-*` tags
  `seat-race,synthetic,probe`); reconcile stays propose-only, never invoked.
- No auto-dispatch: every seat launch and queue write happens under the
  recorded approval below, by explicit runbook step, never self-dispatched.
- No real engine slices: all 4 racers run probe workloads (timed queue/ps
  samples + claim attempts + a self-check), NOT engine work — deterministic,
  no engine-readiness dependency.
- Never `Closes #16/#17/#140` (not in this package, not in any close-out PR).
- No V-gate by default: a V-gate appends ONLY if the race proves a live
  behavior gap the corpus cannot pin (then with V19-freeze note + live-count
  docs); otherwise 39/0 stands. The decision is recorded with reason.

## Sensitive-action approval (recorded verbatim)

APPROVAL GRANTED by the principal (seat-race grilling Q1, 2026-10-30):
"LIVE SEATS claim synthetic rows — explicit sensitive-action approval
GRANTED. Token spend + fleet mutation authorized within the bounds below:
max 6 seat launches (4 racers + up to 2 fresh-relaunch spares), synthetic
rows only, abort on first RED, pre/post `rig ps --nodes -A` snapshots,
zero-residue cleanup (rows closed, probe dirs removed, no queue residue
verified via `rig queue list --json`)."

## Composition and contention

- 4 racer seats (idle, no-WORK fleet seats, disclosed in runbook §2 with per-
  launch reason) × 2 synthetic rows (`SEAT-RACE-1`, `SEAT-RACE-2`).
- Every racer attempts `SEAT-RACE-1` then `SEAT-RACE-2` by qitem ID
  (`--no-nudge` rows; no live seat nudged, no live queue disturbed).
  Single-owner row semantics force winner + loser outcomes per row.
- Racer D carries the FIXED scripted failure: its proof command (`false`,
  step 3, post-claim) fails by design → D pins the base SHA and stops; the
  other racers continue on the pinned base with NO rebase.
- Base SHA pinned per slice at fan-out: `2b3999b` (worktree HEAD at kickoff);
  none cited green until the join.

## Fallback and abort

- Fallback: if the kickoff health snapshot mismatches the Wave-3 baseline
  (51 fleet `run`/`idle` + kernel rows, 111 lines, WORK pattern) → NO-GO
  until the coordinator clears it. The runbook records GO or NO-GO.
- Abort: first RED (non-scripted failure, unexpected seat state, secret
  hygiene break) aborts the exercise; the runbook records the abort point,
  pre/post snapshots are still filed, and cleanup still runs to zero residue.
- Spares: up to 2 fresh-relaunch spares on stale-resume 400s (Wave-2 F2
  lesson: prefer `--fresh --stop`); each launch disclosed with reason;
  6 launches is a hard ceiling.

## Acceptance

- Compound green in the worktree (39/0, or 40/0 iff the V-gate appends with
  freeze note; `openspec validate 2026-10-30-seat-race` rc=0; self-test
  PASSED; generate `--check-idempotent`; `make test` skipped with reason iff
  `git diff --name-only` shows zero code/test/script changes).
- Evidence under `docs/evidence/seat-race-2026-10-30/`: runbook (every
  command, rc, redacted output; composition, which racer failed, base SHAs),
  `proof-a/b/c/d.json`, `metrics.log` (claim-latency series, winner/loser,
  watchdog), `ps-kickoff.txt`, `ps-post.txt`. Redacted; Bearer-shaped
  strings: none (grep-verified).
- Triad box in `tasks.md` stays UNCHECKED (coordinator runs the triad;
  this stage does not commit).
