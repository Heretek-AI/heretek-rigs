# Tasks: 2026-10-30-seat-race

## Authoring (this landing — read-only until fan-out)

- [x] Author change package (proposal/spec/design/tasks per approved design)
- [x] Safe-check (`stat` 700/600/600 + dry-run `!cat`-only rc=0, zero
  secret-shaped strings)
- [x] Kickoff `rig ps --nodes -A` re-snapshot vs Wave-3 baseline
  (51 fleet `run`/`idle`, 111 lines, WORK pattern) → GO recorded in
  runbook §1 (NO-GO path: stop until coordinator clears)

## Live race (under the recorded Q1 approval — abort on first RED)

- [x] Fan-out: 2 synthetic rows (`SEAT-RACE-*`, `--json --verify
  --no-nudge --source seat-race`), base SHA `2b3999b` pinned, qitem IDs +
  `tsCreated` recorded; launches used: 0 of 6 so far ; outcome: prior
  session created both rows 14:59:26/28Z then died; resumed session
  verified (pending/unclaimed/single-created-transition) and ADOPTED —
  no recreate (runbook §2)
- [x] Launches: 4 racer seats fresh (`--fresh --stop`, one reason each;
  spares only on stale-resume 400s, ceiling 6); boot wait; window opens
  with 4 back-to-back verified sends (window-open timestamp recorded) ;
  outcome: 6/6 used — 4 racers + 2 spares (NOT for 400s: originals A/B
  fresh-launched with DANGLING shellPath into deleted fleet-proofs
  worktree, bash broken; replaced by blue-cloud-sec-auditor /
  blue-compliance-auditor). Window 1 opened 15:05:22Z (runbook §§2–3)
- [x] Race: A/B/C run timed samples + R1-then-R2 claims + self-check;
  D runs identical steps 0–2, then FIXED scripted failure at step 3
  (`false` → STOPPED-SCRIPTED-FAILURE, base pinned, closes nothing);
  others continue, NO rebase ; outcome: round-1 FALSIFIED cross-seat
  contention live (7/7 `claim_destination_mismatch` — destination
  enforced on claim); D BLOCKED step 0 (seat policy denies all bash);
  round-2 fallback-rerouted addressed rows (R1→B, R2→C, rc=0):
  B WON R1 (claimed 15:14:13Z), C WON R2 (claimed 15:14:31Z), A loser
  (2 mismatch), D diagnostic-only. C's reassigned `false` DENIED by
  policy — scripted gate UNEXECUTED (runbook §4; REQ-SR2 for triad)
- [x] Join: `proof-a/b/c/d.json` (transcripts + transition logs) + runbook
  join; none green until join; D-held row (if any) closed `canceled` ;
  outcome: join.json filed; winners/losers recorded; no D-held row
  existed → both winner-held rows closed done/no-follow-on (bare close
  fail-closed rc=1 first, env-identity retry rc=0; runbook §6)
- [x] Metrics: claim-latency series, winner/loser, watchdog/stuck-sweep,
  snapshot cost, daemon responsiveness, ACTIVE/queue samples →
  first-degrading named or none-degraded + watched-candidate ;
  outcome: metrics.log — none degraded in this run; watched-candidate
  claim latency (LLM action variance); claim-once-claimable 14.1/25.8 s
- [x] Post-exercise `rig ps` snapshot + zero-residue cleanup verified
  (rows closed under `--source seat-race`, `/tmp/opencode/seat-race/`
  removed, `rig queue list --json` residue check, byte-compare ps) ;
  outcome: queue baseline shape restored (76/13/7/4), zero open
  SEAT-RACE rows, non-Model ps lines identical modulo racer C `working`
  flag, /tmp clean (runbook §6)
- [x] V-gate decision: append ONLY if a live behavior gap is proven
  (V19-freeze 39→40 note + live-count docs), else 39/0 stands ;
  outcome: NOT appended — 39/0 stands; 3 findings recorded with
  reasons (dangling shellPath un-gateable-while-red; destination
  enforcement intended-correct; gate-denial probe lesson; runbook §7)
- [x] Triad (agency-qa red-proof + agency-drift-guard audit) → VERDICT
  before any PR (Refs #16, Refs #17, Refs #140 — never Closes); outcome: agency-qa PASS (qa-red-proofs.log) + agency-drift-guard VERDICT: PASS (seat-race-verification.md), both committed pre-merge

## Racer designation (fixed at fan-out; amended round-2 with rationale)

- Racer A: `build-java-kotlin-eng@heretek-omni-fleet` (idle, no WORK)
  → CASUALTY (dangling shellPath, bash broken on fresh launch);
  replaced by spare A-prime `blue-cloud-sec-auditor@heretek-omni-fleet`
  (idle, no WORK, valid shellPath). A-prime ran prompts A.
- Racer B: `build-python-backend-spec@heretek-omni-fleet` (idle, no WORK)
  → CASUALTY (same); replaced by spare B-prime
  `blue-compliance-auditor@heretek-omni-fleet`. B-prime ran prompts B,
  WON R1.
- Racer C: `data-dba-specialist@heretek-omni-fleet` (idle, no WORK);
  ran prompts C, WON R2; scripted gate REASSIGNED to C (D blocked)
  then policy-DENIED (unexecuted, recorded).
- Racer D (scripted failure): `data-analytics-metrics-eng@heretek-omni-fleet`
  (idle, no WORK) → ENVIRONMENTALLY BLOCKED (seat policy denies all
  bash); diagnostic-only in round 2; performed no claims, no closes.
