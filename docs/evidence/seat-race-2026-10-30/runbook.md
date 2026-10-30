# Seat-race runbook — bounded live seat-claim race (#140 remainder)

Change: `openspec/changes/2026-10-30-seat-race/`. Stage: seat-race.
Bounds: principal-approved seat-race grilling Q1 — LIVE SEATS claim
synthetic rows; token spend + fleet mutation authorized within: max 6
seat launches, synthetic rows only, abort on first RED, pre/post `rig ps`
snapshots, zero-residue cleanup. Refs #16, Refs #17, Refs #140 — never
Closes.

Composition: 4-probe racers (ALL-PROBE, no engine work).
Racer A: `build-java-kotlin-eng@heretek-omni-fleet`.
Racer B: `build-python-backend-spec@heretek-omni-fleet`.
Racer C: `data-dba-specialist@heretek-omni-fleet`.
Racer D (FIXED scripted failure): `data-analytics-metrics-eng@heretek-omni-fleet`.

Base SHA (pinned per slice, no mid-exercise rebase): `2b3999b`
(full `2b3999bb3b47b4485a7ba7791c387eedde34d94c`, worktree HEAD at kickoff).

All outputs redacted. Zero secret values recorded. Bearer-shaped strings:
(to be grep-verified at close-out; none expected).

## 1. Kickoff — `rig ps --nodes -A` re-snapshot vs Wave-3 baseline

- Command: `rig ps --nodes -A` → rc=0, 111 output lines (filed as
  `ps-kickoff.txt`).
- Observed: 51 `heretek-omni-fleet` seats ALL `run`/`idle` (zero non-run,
  zero non-idle) + kernel rows; 111 lines total (1 header + 51 fleet +
  51 model + 8 kernel) — identical shape to Wave-3 baseline (51 + 4, 111).
- WORK pattern consistent with baseline: build-ts-node-fullstack 7,
  data-pipeline 2, design rows 2–3 (+yes rows), delivery-tpm 2, systems
  rows 2–3 (+yes rows). Other sessions ACTIVE, nothing touched.
- Racer seats at kickoff: all four `run`/`idle`, WORK `no`, model-record
  UNKNOWN (long-idle, minimal disruption risk).
- Verdict: **GO** (no unexpected state; NO-GO not triggered).

## 2. Fan-out (prior session 14:59Z; adopted after verification)

ADOPTION NOTE (honest discontinuity): the builder session created both
rows at 14:59:26/28Z then died abruptly before writing spec.md. The
resumed session re-verified live state at 15:12:38Z — both rows pending,
unclaimed, `claimedAt` null, single `created` transition each
(actor `seat-race`), queue shape at baseline — and ADOPTED the rows (no
recreate; no mutation found, so no NO-GO). Everything below 14:59–15:05Z
is reconstructed from on-disk artifacts (`/tmp/opencode/seat-race/`
create-*.json, launch-*.json, send-log.txt, transcripts) + live
re-verification, not from memory.

- Queue baseline (`rig queue list --json -a`, 14:59Z, rc=0): 100 rows —
  done 76, blocked 13, in-progress 7, handed-off 4. Zero SEAT-RACE rows.
- Row creates (both `--json --verify --no-nudge --source seat-race`,
  tags `seat-race,synthetic,probe`, rc=0 each):
  - SEAT-RACE-1: `qitem-20261030145926-b82354bc9dce4899`,
    tsCreated 2026-10-30T14:59:26.596Z → `seat-race-r1@heretek-omni-fleet`.
  - SEAT-RACE-2: `qitem-20261030145928-4779d07d4c7fdf1c`,
    tsCreated 2026-10-30T14:59:28.922Z → `seat-race-r2@heretek-omni-fleet`.
  - Cold rows by design (synthetic destinations match no live seat).
- Launches (6 of 6 budget used; each `--fresh --stop` with reason, rc=0):
  1. 14:59:37Z racer A `build-java-kotlin-eng` (reason: racer A probe).
  2. 14:59:40Z racer B `build-python-backend-spec` (reason: racer B probe).
  3. 14:59:45Z racer C `data-dba-specialist` (reason: racer C probe).
  4. ~14:59:4xZ racer D `data-analytics-metrics-eng` (reason: scripted-failure probe).
  5. spare 1/2: `blue-cloud-sec-auditor` (reason: replace racer A —
     original A fresh-launched with DANGLING shellPath
     `.../.lane/trees/fleet-proofs/scripts/seat-sandbox.sh` into the
     deleted fleet-proofs worktree; bash broken on arrival).
  6. spare 2/2: `blue-compliance-auditor` (reason: replace racer B —
     same dangling-shellPath casualty).
  - Original A/B seats left running idle, untouched after launch (no
    operator repair: daemon-state surgery out of bounds; documented as
    finding §7/F1).
- Window 1 opened 15:05:22.836Z: 4 back-to-back `rig send --verify`
  (rc=0 each; delivery rendered-unconfirmed) to A-prime/B-prime/C/D.
- Prompt flaw (recorded, not hidden): round-1 prompts ordered
  `date`/`echo`/pipes/`-a` flags, all denied under seat least-privilege
  sandboxes; racers adapted to bare `rig` commands. Round-2 prompts
  corrected to bare-only.

## 3. Round 1 — design falsified live (15:05–15:13Z)

- A-prime: step 2a R1 claim rc=1 `claim_destination_mismatch`
  (destination seat-race-r1 ≠ claimant); STOPPED-RED per round-1 abort
  rule (2b unattempted, marked UNVERIFIED). Base quoted from prompt.
- B-prime: R1 refused + R2 refused (both mismatch, rc=1); self-check
  `whoami` rc=0; full report. RED notes: step-0 echo-denied, mismatch ×2.
- C: R1 refused + R2 refused (both mismatch, rc=1); self-check ok;
  RED=none.
- D: STOPPED-BLOCKED at step 0 — seat policy denies ALL bash including
  bare `echo` (`[pi-permission-system] Denied by policy: 'bash'
  (rule '*')`). No claims attempted, no writes. Scripted gate unreached.
- FALSIFICATION (core design assumption, proven live): cross-seat
  contention for one row is STRUCTURALLY IMPOSSIBLE — the daemon enforces
  destination-matching on claim (`claim_destination_mismatch`), not just
  on nudge routing. 7/7 cross-seat attempts refused synchronously.
  Design §"Why 4 racers × 2 rows" assumed first-claim-wins across seats;
  the queue is 1:1-addressed single-owner. This is #16 fan-out evidence
  (fan-out MUST use addressed rows), not a daemon defect.
- Live finding F1 (shell integrity): original racers A/B fresh-launched
  into seats whose daemon-side pi `settings.json shellPath` points at
  `.../.lane/trees/fleet-proofs/scripts/seat-sandbox.sh` — a worktree
  that no longer exists (`.lane/trees/` holds only `seat-race`).
  Read-only scan 15:1xZ: ~27 of 51 fleet seats carry this dangling path
  (consistent with seeding from the deleted fleet-proofs stage worktree;
  `render-seat.py:1090` resolves the wrapper absolute to the seeding
  cwd). Fresh launch on such a seat silently lobotomizes it (no bash).
  Mechanism recorded; repair (daemon-state surgery) out of bounds.
- Live finding F2 (sandbox variance): seat sandboxes are least-privilege
  per-seat — A-prime/B-prime/C allow bare `rig` commands but deny
  `echo`/`date`/pipes/flags-beyond-need; D denies even bare `echo` while
  allowing `rig queue whoami`. Scripted steps must be allow-listed `rig`
  commands (lesson for #16 probe design). D's valid shellPath (repo
  `scripts/seat-sandbox.sh` exists) proves F2 is policy, not F1.

## 4. Adaptation — round 2 with addressed rows (15:13–15:17Z)

Rationale (minimal fix, recorded): with cross-seat claims forbidden,
the exercise reroutes rather than recreates — `rig queue fallback`
is the designed path for unreachable destinations, and both synthetic
destinations ARE unreachable. Spec row-count ("exactly 2") preserved;
no new rows; no new launches (budget exhausted 6/6).

- `fallback R1 → blue-compliance-auditor` rc=0 (transition 1532,
  15:13:59.927Z, actor `system:queue-fallback`; reason recorded).
- `fallback R2 → data-dba-specialist` rc=0 (transition 1533,
  15:14:05.907Z).
- Watchdog evidence: transition 1534 (15:14:08.535Z) parked-owner wake
  reserved for B; delivered 15:16:09.020Z (1537) AFTER B's claim —
  redundant-but-harmless, no disturbance. Watchdog ACTIVE during race.
- Round-2 prompts (bare-commands-only, mismatch/already-claimed both
  declared expected loser outcomes): 4 back-to-back verified sends
  rc=0; window 2 opened 15:14:29.797Z.
  - B: claim addressed R1. C: claim addressed R2, then FIXED scripted
    gate `false` (REASSIGNED from D with rationale: D environmentally
    blocked at step 0; C functionally equivalent; mechanics unchanged).
  - A: resume — attempt both (now B/C-addressed; expected refusals
    completing round-1 UNVERIFIED marks). D: single-command diagnostic
    (`whoami`), stop either way.
- Outcomes (all from live transcripts + transition log):
  - B WON R1: claimed 15:14:13.987Z (transition 1535, actor = seat
    identity) — BEFORE the round-2 prompt, on the fallback/watchdog
    wake under standing round-1 instructions. Fallback→claim 14.060 s.
  - C WON R2: claimed 15:14:31.658Z (transition 1536), 4.049 s after its
    round-2 send. Fallback→claim 25.751 s.
  - C step-4 `false`: DENIED by policy (`[pi-permission-system] Denied
    by policy: 'bash' (rule '*')`) — never executed, no rc. C reported
    STOPPED-SCRIPTED-FAILURE step=4 DENIED-not-executed, closed nothing.
    Scripted-failure condition NEVER OCCURRED (on D: blocked step 0;
    on C: gate denied). REQ-SR2 scenario UNEXECUTED — recorded, not
    papered (triad judges; §7).
  - A: R1 refused:mismatch, R2 refused:mismatch (destination check
    precedes state check — R1 already B-held still reports mismatch),
    self-check ok, RED=none. Loser, completed.
  - D: `whoami` rc=0 (partial allow-list proven), stopped per
    instructions, no attempts, no writes. Environmental non-participant.
- Emergent isolation observation (supporting, not compliance): A's
  round-1 STOP (one slice stopped on unexpected refusal) while B/C/D
  continued on the pinned base with no rebase — the isolation property
  held emergently though the scripted mechanism never fired.

## 5. Metrics — see metrics.log (summary)

Claim-once-claimable: R1 14.060 s, R2 25.751 s (n=2; spread = LLM-seat
action variance). 7/7 cross-seat refusals synchronous. Snapshots
0.24–0.65 s stable. `overdue` mid-window: []. Watchdog active, one
redundant wake, no sweep storm (backstop due 15:59Z never fired —
correct non-firing). Daemon responsive on ~25 operator commands, zero
400s. 51/51 correctly-idle-or-engaged. FIRST-DEGRADING: none degraded
in this run; watched-candidate (labeled projection): claim latency
under higher racer concurrency.

## 6. Post-exercise snapshot + zero-residue cleanup — VERIFIED

- Closes (Wave-3 pattern: bare close fails closed first, attributable
  retry recorded):
  - Bare `queue update R1 --state done` (no identity): rc=1 fail-closed
    (`OPENRIG_SESSION_NAME is not set, so there's no seat to act as`).
  - Retry `OPENRIG_SESSION_NAME=seat-race` (exercise's own declared
    identity; no live seat impersonated): R1 done/no-follow-on rc=0;
    R2 done/no-follow-on rc=0 (resolution notes scripted-gate-denied).
  - Note on REQ-SR2's "close any D-held row as canceled": vacuous —
    no D-held row existed (D never claimed); both winner-held rows
    closed done/no-follow-on with reasons. Conditional obligation with
    unmet condition, not a violation.
- Residue: `rig queue list --json -a` post-close: 100 rows (done 76,
  blocked 13, in-progress 7, handed-off 4) — baseline shape restored;
  ZERO open SEAT-RACE rows (grep-verified).
- Post `rig ps --nodes -A` (filed `ps-post.txt`): 51 fleet run, 50 idle
  + racer C `working` (settling post-report); zero dead/down; WORK
  pattern unchanged. Non-Model lines identical to kickoff except C's
  activity flag (expected — C engaged at snapshot). Model-record lines
  differ only by fresh activity timestamps on the 6 touched seats.
- Scratch: `/tmp/opencode/seat-race/` (bodies, prompts, launch/send
  logs, transcripts, snapshots) removed post-evidence; seat-side
  truncation droppings `/tmp/pi-bash-*.log` (2 files, 15:05Z, this
  exercise) removed. `ls /tmp/opencode | grep seat-race` clean.
- No tracker writes (reconcile never invoked). No installs, no hosts,
  no upstream posts. Seats left running (A-prime/B-prime/C/D active
  with completed probes; original A/B idle-lobotomized, documented §3
  F1 for follow-up repair — out of bounds here).

## 7. V-gate decision — NOT appended (reason recorded)

No V-gate appended; 39/0 stands. Three live findings, none gated:
- F1 (dangling shellPath, ~27 seats): IS a live behavior gap the corpus
  cannot pin (V12 pins only the committed template suffix, not live
  absolute-path staleness) — but it CANNOT be appended as a green gate
  while 27 live seats still dangle (repair = daemon-state surgery, out
  of bounds; a RED gate breaks compound green). Filed as #140
  follow-up: seed-path hygiene (render-seat.py:1090 absolute resolution
  bakes the seeding worktree) + live repair pass.
- F2 destination-enforcement is intended-correct daemon behavior
  (attribution, Wave-9-adjacent), not a defect: #16 design evidence
  (fan-out MUST use addressed rows / fallback reroute), not a gate.
- Scripted-gate denial (seat policy denies `false`) is a probe-design
  lesson (scripted steps must be allow-listed `rig` commands), not a
  fleet gap.
If a future exercise proves a gap pinnable-green, the gate appends then
with V19-freeze note + live-count docs.

## 8. Operator-touch audit — factual count

| # | Touch | rc / evidence | Tag |
|---|---|---|---|
| 1 | Kickoff `rig ps` snapshot + baseline compare | rc=0, §1 | Automatable (read-only recon) |
| 2–3 | 2× `rig queue create --json --verify --no-nudge` | rc=0 each, §2 | Automatable in principle; queue-write authority needs per-exercise approval (this run) |
| 4–7 | 4× racer `rig seat launch --fresh --stop` | rc=0 each, §2 | Wave-2 pattern; unattended execution needs-scope → #12 build-runner candidate |
| 8–9 | 2× spare `rig seat launch --fresh --stop` (shellPath casualties) | rc=0 each, §2 | Mediation (environmental triage); same scope question as 4–7 |
| 10–13 | 4× round-1 `rig send --verify` | rc=0, §2 | Automatable dispatch in principle; seat-targeting needs-scope |
| 14 | shellPath forensics (read-only daemon-state scan) | 0 matches secret-shaped, §3 F1 | Automatable (read-only recon) |
| 15–16 | 2× `rig queue fallback` reroute (unreachable destinations) | rc=0 each, §4 | Mediation (destination judgment); PARTLY automatable |
| 17–20 | 4× round-2 `rig send --verify` (bare-only, reassigned gate) | rc=0, §4 | As 10–13 + prompt-design judgment |
| 21–23 | Timed operator telemetry (queue/ps/overdue) | rc=0, §5 | Automatable (read-only) |
| 24 | Bare close fail-closed (rc=1) + 2× env-identity closes (rc=0) | §6 | Mediation (Wave-3 pattern); identity choice needs-scope |
| 25 | Post `rig ps` + shape-compare + residue checks | rc=0, §6 | Automatable |
| 26 | /tmp + seat-dropping cleanup | clean, §6 | Automatable (policy-compliant primitive) |
| 27 | Evidence authoring (runbook/metrics/proofs/join) | this file | Operator-side (counted here) |
| 28 | Triad + close-out commit + PR | pending | Coordinator-side (counted at close-out) |

Totals: 27 operator touches (20 automatable-or-trivially-scriptable,
7 needing judgment/scope: queue-write authority, seat identity for
mutation, launch/fallback/destination judgment, prompt design).
Zero charter changes. Bearer-shaped strings: none (grep-verified at
close-out — see implementation report).
