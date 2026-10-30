# seat-race implementation report (stage: seat-race, 2026-10-30)

## What ran

Bounded live seat-claim race for #140 (Refs #16, Refs #17, Refs #140 —
never Closes). Prior builder session created 2 synthetic rows at
14:59:26/28Z then died; resumed session verified live state
15:12:38Z (both rows pending/unclaimed/single-created-transition, queue
at baseline, fleet 51 run/idle) and ADOPTED the rows (runbook §2).
Round 1 (4 sends 15:05:22Z) falsified the contention premise live:
7/7 cross-seat claims → `claim_destination_mismatch` (destination
enforced on claim). 2 of 4 original racers landed on seats with
dangling shellPath (bash broken); 2 spare launches replaced them
(6/6 budget). Round 2: `fallback` rerouted R1→B, R2→C (rc=0);
B claimed R1 15:14:13.987Z, C claimed R2 15:14:31.658Z; A completed
as loser (2 mismatch); D diagnostic-only (seat policy denies bash).
C's reassigned scripted `false` denied by policy — gate unexecuted.
Rows closed done/no-follow-on under `seat-race` identity (bare close
fail-closed rc=1 first, retries rc=0). Zero residue verified.

## Validation (all run in worktree, real output read)

- `openspec validate 2026-10-30-seat-race` → rc=0 (`Change is valid`).
- `./scripts/verify-rigs.sh --check-only` → 39 passed / 0 failed.
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `python3 scripts/generate-rigs.py --check-idempotent` → rc=0,
  byte-identical; `git status` shows no registry modification.
- `make test`: SKIPPED — `git diff --name-only` (tracked) shows only
  `AGENTS.md` (1 docs-map row); untracked additions are openspec +
  docs/evidence + docs/reports only. Zero code/test/script diffs.
- Bearer-shaped strings: none in evidence, report, or package
  (grep-verified: `sk-|ghp_|Bearer [A-Za-z0-9]|xox[bap]-` → 0 matches).

## Per-step verdicts

- Kickoff vs baseline: GO (51 run/idle, 111 lines, WORK pattern match).
- Adopt-vs-recreate: ADOPT (rows pristine); honest discontinuity noted.
- Fan-out rows: GREEN (rc=0, tags/source correct).
- Launches 6/6: GREEN rc=0; 2 originals environmentally lobotomized
  (F1), 2 spares healthy.
- Round-1 race: design FALSIFIED (destination enforcement); racers
  behaved correctly (fail-closed, adapted to bare commands).
- Round-2 race: GREEN — 2 addressed wins with claimedAt, winner+loser
  outcomes, no rebase, base pinned throughout.
- REQ-SR1: MET (adapted, recorded). REQ-SR2: NOT EXECUTED (gate
  policy-blocked on D and C; emergent isolation only; triad judges).
  REQ-SR3: MET (metrics.log; none-degraded + watched-candidate).
- Cleanup: GREEN (rows closed, queue baseline restored, /tmp clean).
- V-gate: NOT APPENDED (39/0 stands; 3 findings → #140 follow-ups,
  runbook §7 with reasons).

## Metrics summary

Claim-once-claimable: R1 14.060 s, R2 25.751 s (LLM action variance).
7 cross-seat refusals synchronous. Snapshots 0.24–0.65 s. Overdue [].
Watchdog active (1 redundant wake post-claim). Daemon responsive.
First-degrading: none degraded; watched-candidate: claim latency.

## Live state left behind

- Rows: `qitem-20261030145926-b82354bc9dce4899` done/no-follow-on
  (winner B, claimed 15:14:13.987Z); `qitem-20261030145928-4779d07d4c7fdf1c`
  done/no-follow-on (winner C, claimed 15:14:31.658Z). Zero open
  SEAT-RACE rows.
- Seats: all 51 run; A-prime/B-prime/C active (probes complete);
  D active; original A/B idle (dangling shellPath, flagged for
  follow-up repair — out of bounds here).
- Worktree: openspec package + evidence + report + 1 AGENTS.md row,
  uncommitted (coordinator commits).

## Blockers / follow-ups for #140 (propose-only, no tracker writes)

1. Dangling shellPath (~27 seats) + seed absolute-path mechanism
   (render-seat.py:1090) — needs live repair pass (out of bounds).
2. Destination-enforced claims → #16 fan-out MUST use addressed rows
   or fallback reroute (proven pattern this run).
3. Scripted in-seat failure steps must be allow-listed `rig` commands.
