# Design: 2026-10-30-seat-repair

## 1. Why plain relaunch cannot fix the stale seats (mechanism, proven)

`shellPath` is baked into daemon state at seed time:
`render-seat.py:1090` resolves the wrapper absolute to the seeding cwd
(`Path(__file__).resolve().parent / "seat-sandbox.sh"`). Wave 2 seeded
from the `fleet-proofs` worktree; that worktree is pruned, so 24 live
seats carry a `shellPath` whose target does not exist. `rig seat launch
--fresh --stop` "composes a new command from current settings" — i.e.
from the same daemon-state `settings.json` — so a fresh launch on a
stale seat silently reproduces the dangling path (no bash on arrival).
Seat-race §3 F1 proved it live: the race's originals A/B were
fresh-launched post-prune into the dangling path and STILL carry it in
`settings.json` today. The repair MUST therefore re-resolve first: a
supported re-seed from the durable checkout (`seed-rig.py` member
fragment → `render-seat.py`), which rewrites `shellPath` to the
in-repo wrapper the 27 clean seats already point at
(`scripts/seat-sandbox.sh`, repo-root-relative),
then fresh-launch. This is the "re-resolve" half of the hygiene input
contract ("re-resolve vs relaunch"); no hand-surgery on daemon state.

Re-seed blast radius (checked pre-wave): `render-seat.py` rewrites only
its rendered file set (`settings.json`, `mcp.json`, `sandbox.env`,
permission config, `AGENTS.md`, `auth.json` as a `!cat` reference —
never a literal secret); `sessions/` is preserved (`mkdir exist_ok`),
daemon-managed files (`models-store.json`, `bin/`, `skills/`, logs)
are untouched. Grant issuance is idempotent reuse (`issue_seat_grant`:
already-issued → `ok ... reuse`, rc=0). Seeds run from the MAIN
checkout's `scripts/` — running the worktree's copy would bake the
worktree path and re-create the bug. The main checkout is verified
clean at `53cdda5` before the first seed.

## 2. Batch plan (22 targets, 6+6+6+4)

Source: `docs/evidence/seat-hygiene-2026-10-30/dangling-seats.json`,
`impact == stale` only (the 2 `lobotomized` are verify-only, §6).
Pod/member for re-seed derives from the session name (`<pod>-<member>`),
verified against `rigs/heretek-omni-fleet/members/<member>.yaml`:

- B1: blue-appsec-engineer (blue/appsec-engineer),
  build-go-backend-eng (build/go-backend-eng),
  build-ts-node-fullstack (build/ts-node-fullstack),
  delivery-git-drift-coord (delivery/git-drift-coord),
  delivery-tech-docs-lead (delivery/tech-docs-lead),
  delivery-tpm-scrum-lead (delivery/tpm-scrum-lead).
- B2: design-a11y-specialist, design-brand-copy-spec,
  design-design-system-eng, design-fe-perf-eng, design-mobile-web-eng,
  design-ui-ux-designer (all pod `design`).
- B3: design-ux-research-analyst (design), engine-engine-systems-eng
  (engine/engine-systems-eng), engine-physics-sim-eng,
  exec-exec-director (exec/exec-director),
  exec-product-director, exec-system-architect.
- B4: mobile-android-mobile-spec, mobile-ios-mobile-spec (pod `mobile`),
  systems-cpp-lowlevel-eng, systems-rust-systems-spec (pod `systems`).

Per batch, in order: (i) kickoff snapshot — `rig ps --nodes -A` →
`ps-batchN-pre.txt`, `rig queue list --json -A`, per-target
`agentActivity.state` + held-row check; (ii) per seat (§3); (iii)
close-out — `rig ps --nodes -A` → `ps-batchN-post.txt`, queue-list
diff (must show ZERO queue mutation), `make live-health` advisory.
Between batches the fleet shape is compared to the 111-line baseline;
any unexpected fleet state (missing seat, non-running target outside
the plan, ps shape break) STOPS the wave (NO-GO + report, §5).

## 3. Per-seat protocol (all rcs + replies recorded in runbook.md)

0. Re-check `agentActivity.state` for THIS seat immediately before
   touching it; if ACTIVE-family → SKIP to report-only (per-seat
   approval required to re-enter), record reason, move on.
1. Record pre-seed `shellPath` (must be the stale value — surprises stop
   the seat, not the wave, unless fleet-wide).
2. Re-seed (cwd = main checkout):
   `python3 scripts/seed-rig.py rigs/heretek-omni-fleet/members/<m>.yaml
   --rig heretek-omni-fleet --pod <p>` → rc=0; record the grant line.
3. Settings pre-check: `settings.json shellPath` == durable wrapper AND
   target exists → else RED → abort wave (§5).
4. Fresh relaunch:
   `rig seat launch <seat> --fresh --stop --reason "seat-repair #147
   batch BN: re-resolve dangling shellPath (Refs #147)" --json` → rc=0.
5. Config-clean check: `seat status` running/active/ready AND
   `settings.json shellPath` still clean AND `launch_cwd` exists →
   else RED → abort wave.
6. Exec probe: `rig send <seat> "<task>" --verify --json` → rc=0; wait;
   `rig transcript <seat> --tail/--grep SEAT-REPAIR-OK --json` (+
   `capture` on ambiguity). PASS = reply contains `SEAT-REPAIR-OK`
   AND genuine shell output. FAIL (no reply in budget, denial without
   output, error) → RED → abort wave.
7. Record stuck rows held (untouched) for holder seats.

Probe task text (bare `rig` commands only — seat-race §3 F2: seat
sandboxes deny echo/date/pipes, so a literal `echo` probe would RED on
policy, not on repair state):

> Seat-repair probe #147 (batch BN): in your shell run
> `rig queue whoami` and then `echo SEAT-REPAIR-OK`. Reply here with
> both outputs verbatim: the whoami output first, then the exact line
> SEAT-REPAIR-OK. If your shell policy denies echo, reply with the
> whoami output plus the line SEAT-REPAIR-OK typed in your reply.

PASS criteria (operator-judged from the transcript): the reply carries
`SEAT-REPAIR-OK` together with a plausible `rig queue whoami` output
identifying the seat — evidence a live occupant executed shell. A
bash-broken occupant cannot produce genuine command output; absence of
it is FAIL.

## 4. live-health diff design (REQ-R3, minimal)

`scripts/live-health.py` gains one warn-first sub-check,
`seat-shell-paths`, wired through the existing
`run_gate → finalize → overall_exit` path (advisory WARN + exit 0;
`--strict` promotes via the existing `_promote`, exit 2 — the gate's
standard strict semantics, REQ-LH7):

- Pure evaluator `evaluate_shell_paths(entries, repo_root)`: each entry
  `{session, shell_path, launch_cwd}` resolves (absolute → as-is;
  relative → against `repo_root`) and existence-checks both fields.
  PASS = all resolve; WARN = ≥1 dangling (names seat + field + target);
  SKIP = nothing assessable (never healthy, REQ-LH2).
- Collector `collect_seat_paths(ps_nodes, status_fn, state_root,
  repo_root)`: for every running seat — `shellPath` from
  `$OPENRIG_HOME/state/pi/<seat>/agent/settings.json` (filesystem
  read, no rig call), `launch_cwd` from `rig seat status <seat> --json`
  (new allowlisted read-only verb in `check_allowed`: exactly
  `["seat", "status", <session>, "--json"]`). Unreadable/missing →
  unassessed → SKIP naming the seat. REQ-LH8 stays fail-closed: every
  other `seat` verb is still refused (test-pinned).
- `FixtureClient.fetch_seat_paths()` replays `seat_paths.json`
  (absent → SKIP, so old fixtures degrade honestly).
- Tests (TDD): pure trip/clear against tmp dirs with real files
  (dangling shell named; clean entries PASS; relative resolution vs
  repo root; missing launch_cwd named; empty → SKIP); gate-level
  trip/clear via `seat_paths.json` fixture; `check_allowed` accepts
  `seat status --json` and still refuses `seat launch`/`queue send`;
  dead-daemon still all-SKIP exit 0.

## 5. Abort / roll-forward rules

Abort the WHOLE WAVE (no further launches/sends/seeds) on: failed
re-seed, failed relaunch (rc≠0), failed config-clean check, failed
probe, or unexpected fleet state (ps shape break vs baseline, a
non-target seat disturbed, any queue mutation in the per-batch diff).
Remaining seats roll to a follow-up run — the runbook records the exact
stop point (batch, seat, step, evidence). Retries necessitated by
400s-rot count as launches and obey the same abort rule; no
retry-looping past a RED. A batch that closes GREEN needs no revisit.

## 6. Lobotomized verify-only

`build-java-kotlin-eng` / `build-python-backend-spec`: record
`settings.json shellPath` + `seat status` (+ read-only `capture` for
liveness color). No seed, no launch, no send. If either still dangles,
record STILL-DANGLING honestly and report as a premise deviation — the
separate go-ahead has not landed on disk.
