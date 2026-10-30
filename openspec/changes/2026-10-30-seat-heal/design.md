# Design: 2026-10-30-seat-heal

## 1. Why re-seed (root cause: relaunch-only reuses stale live config)

`shellPath` is baked into daemon state at seed time:
`render-seat.py:1089` resolves the wrapper absolute to the seeding cwd
(`Path(__file__).resolve().parent / "seat-sandbox.sh"`). Wave 2 seeded
from the `fleet-proofs` worktree; that worktree is pruned, so the 2
lobotomized seats carry a `shellPath` whose target does not exist.
`rig seat launch --fresh --stop` "composes a new command from current
settings" — i.e. from the same daemon-state `settings.json` — so a
fresh launch on a lobotomized seat silently reproduces the dangling
path (no bash on arrival). Seat-race §3 F1 proved it live on these very
seats. The heal MUST therefore re-resolve first: a supported re-seed
from the durable checkout, then fresh-launch. No hand-surgery on daemon
state.

Seed path chosen (with `--help` evidence): full member-fragment re-seed

```bash
python3 scripts/seed-rig.py rigs/heretek-omni-fleet/members/<m>.yaml \
  --rig heretek-omni-fleet --pod build        # run from the MAIN checkout
```

`seed-rig.py --help` offers exactly one non-seed flag,
`--refresh-policy-only`, which forwards `--policy-only` to
`render-seat.py`; `render-seat.py:1458-1471` shows `--policy-only`
rewrites ONLY `extensions/pi-permission-system/config.json` (the #96
pps hot-reload path) and returns before writing `settings.json`.
`shellPath` lives in `settings.json` — so `--refresh-policy-only` is
structurally incapable of fixing the dangling path and is rejected for
this wave. The full member-fragment seed re-renders the whole file set
(`settings.json` with the re-resolved `shellPath`, `mcp.json`,
`sandbox.env`, permission config; `sessions/` preserved `mkdir
exist_ok`; daemon-managed files untouched — seat-repair §2 blast-radius
finding, unchanged since). Grant issuance is idempotent reuse. Seeds
run from the MAIN checkout's `scripts/` — running the worktree's copy
would bake the worktree path and re-create the bug.

## 2. Per-seat protocol (all rcs + replies recorded in runbook.md)

0. Re-check `agentActivity.state` for THIS seat immediately before
   touching it; if ACTIVE-family → SKIP to report-only, record reason,
   move on (cap math: a skip keeps the wave inside bounds).
1. Record pre-seed `shellPath` (must be the stale value — surprises stop
   the seat, not the wave, unless fleet-wide).
2. Re-seed (cwd = main checkout, member fragment per §1) → rc=0;
   record the grant line.
3. Settings pre-check: `settings.json shellPath` == durable wrapper AND
   target exists → else RED → abort wave (§4).
4. Fresh relaunch:
   `rig seat launch <seat> --fresh --stop --reason "seat-heal #147:
   re-resolve dangling shellPath (Refs #147)" --json` → rc=0.
5. Config-clean check: `seat status` running/active/ready AND
   `settings.json shellPath` still clean AND `launch_cwd` exists →
   else RED → abort wave.
6. Exec probe: `rig send <seat> "<task>" --verify --json` → rc=0; wait;
   `rig transcript <seat> --tail/--grep SEAT-HEAL-OK --json` (+
   `capture` on ambiguity). PASS = reply contains `SEAT-HEAL-OK`
   AND genuine shell output. FAIL (no reply in budget, denial without
   output, error) → RED → abort wave.

Probe task text (bare `rig` commands only — seat-race §3 F2: seat
sandboxes deny echo/date/pipes, so a literal `echo` probe would RED on
policy, not on repair state):

> Seat-heal probe #147: in your shell run
> `rig queue whoami` and then `echo SEAT-HEAL-OK`. Reply here with
> both outputs verbatim: the whoami output first, then the exact line
> SEAT-HEAL-OK. If your shell policy denies echo, reply with the
> whoami output plus the line SEAT-HEAL-OK typed in your reply.

PASS criteria (operator-judged from the transcript): the reply carries
`SEAT-HEAL-OK` together with a plausible `rig queue whoami` output
identifying the seat — evidence a live occupant executed shell. A
bash-broken occupant cannot produce genuine command output; absence of
it is FAIL. (Seat-repair D1 precedent: if a seat declines the token on
policy while producing stronger in-turn shell evidence, record the
D1-equivalent case honestly and flag for triad — do not force it.)

## 3. Kickoff re-verification (governs, not the expectation)

Before any seed: (i) `rig ps --nodes --json --no-cleanup -A` → fleet
shape + per-target `agentActivity.state`; (ii) `settings.json
shellPath` read for the 2 audit-listed seats; (iii) fleet-wide
`make live-health` glance (`seat-shell-paths` names every dangling
seat). Proceed IFF dangling set == the expected 2 (or fewer — a
missing dangle is a scope shrink, recorded, wave continues on the
remainder) AND every target is idle AND total dangling ≤ 4. Otherwise
STOP: record NO-GO with the observed state, touch nothing, report back.

## 4. Stop conditions

Abort the WHOLE WAVE (no further launches/sends/seeds) on: failed
re-seed, failed relaunch (rc≠0), failed config-clean check, failed
probe, or unexpected fleet state (ps shape break vs kickoff baseline,
a non-target seat disturbed, any queue mutation in the pre/post diff).
Remaining seats roll to a follow-up run — the runbook records the exact
stop point (seat, step, evidence). No retry-looping past a RED. A seat
that closes GREEN needs no revisit. Zero queue writes, ever: no
create/claim/update/block/resolve/handoff/send; probes are `rig send`
task messages only.
