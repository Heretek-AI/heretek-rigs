# Proposal: 2026-10-30-seat-repair — bounded live repair of 22 stale seats (Refs #147)

## Goal

Repair wave for #147: re-resolve the dangling `shellPath` on the 22
`stale`-class seats enumerated in
`docs/evidence/seat-hygiene-2026-10-30/dangling-seats.json`, verify each
repaired seat with a live exec probe, and land a `shellPath` +
`launch_cwd` resolvability check in `make live-health` so this class can
never silently re-accumulate. Refs #147 — never Closes (#147 stays open
until a triad records `VERDICT: PASS`).

## Principal-approved design (grilling Q1–Q6, implemented literally)

- **Q1 — batches of 6:** 6+6+6+4 = 22 stale seats. Fleet health check
  (`rig ps` shape vs 111-line baseline) between batches. Abort the WHOLE
  WAVE on first RED (failed relaunch, failed probe, unexpected fleet
  state); remaining seats roll to a follow-up run — the stop point is
  recorded honestly, never forced through.
- **Q2 — idle-only rule:** at each batch kickoff, any target found
  ACTIVE/mid-work is SKIPPED to report-only (named in the runbook, needs
  per-seat approval to touch — do not touch it). Operationalized in
  `design.md`: SKIP iff `agentActivity.state` normalizes to
  active/running/busy/working at kickoff (re-checked per seat); an
  idle-at-prompt seat holding pre-existing stuck rows is repairable with
  the rows recorded untouched (no queue writes, ever).
- **Q3 — per seat:** re-seed from the durable checkout (re-resolves the
  baked worktree path — plain relaunch provably reproduces the
  lobotomy, seat-race §3 F1) → fresh relaunch (`rig seat launch --fresh
  --stop --reason ...`, Wave-2 F2 pattern, flags verified against
  installed 0.7.5) → ps/config-clean check → exec probe: coordinator
  `rig send` with a task whose reply must contain `SEAT-REPAIR-OK` plus
  genuine shell output (bare `rig` command — the seat-race §3 F2 sandbox
  lesson), reply checked via transcript/capture. Every rc + reply
  recorded. Probe token spend pre-approved.
- **Q4 — live-health:** add `shellPath` + `launch_cwd` resolvability for
  every running seat (advisory WARN per dangling seat, exit 0; strict
  promotes per the gate's existing WARN→FAIL semantics). Fixture
  red-proof: fake dangling + clean entries trip/clear the check. Keep
  the existing warn-first semantics; minimal diff.
- **Q5 — no V-gate:** live state isn't repo state (recorded decision —
  the seat-race §7 precedent: a gate over live dangling paths cannot be
  green while seats dangle, and a RED gate breaks compound green).
- **Q6 — verify-only lobotomized:** the 2 lobotomized seats
  (`build-java-kotlin-eng`, `build-python-backend-spec`) are VERIFY-ONLY
  (repaired under a separate go-ahead) — do NOT relaunch them. If found
  still dangling, record honestly and report; do not touch.

## Non-goals (explicit boundary)

- No ACTIVE-seat relaunches without per-seat approval (Q2 skips are
  report-only; a skipped seat needs its own approval to re-enter).
- No queue writes of any kind (probes go via `rig send` task messages,
  NOT queue rows; stuck rows held by idle targets are recorded, never
  unclaimed/fallen-back — queue mutation is out of bounds).
- No repairs beyond the 22 listed stale seats (+ relaunch retries
  necessitated by 400s-rot, within the abort rule). Never touch other
  seats; never touch the 2 lobotomized.
- No installs, no upstream posts, no daemon-state hand-surgery (re-seed
  goes through `seed-rig.py`/`render-seat.py`, the supported tooling).
- No V-gate; never `Closes #147` (not in this package, not in any
  close-out text).

## Batch plan

- B1 (6): blue-appsec-engineer, build-go-backend-eng,
  build-ts-node-fullstack (holds 4 stuck rows — idle, repairable per Q2),
  delivery-git-drift-coord, delivery-tech-docs-lead,
  delivery-tpm-scrum-lead (holds 2 stuck rows).
- B2 (6): design-a11y-specialist (2 rows), design-brand-copy-spec,
  design-design-system-eng (1 row), design-fe-perf-eng,
  design-mobile-web-eng, design-ui-ux-designer (2 rows).
- B3 (6): design-ux-research-analyst (1 row), engine-engine-systems-eng,
  engine-physics-sim-eng, exec-exec-director,
  exec-product-director (1 row), exec-system-architect.
- B4 (4): mobile-android-mobile-spec, mobile-ios-mobile-spec,
  systems-cpp-lowlevel-eng, systems-rust-systems-spec.

## Acceptance

- Compound green in the worktree (39/0, no new V-block; `openspec
  validate 2026-10-30-seat-repair` rc=0; `make test` FULL run ≥645, 0
  failures; self-test PASSED; generate `--check-idempotent`
  byte-identical) + negative grep over new/changed code (commit/
  landing-write/exec-on-behalf-of-seats → empty beyond the send-probe path).
- Evidence under `docs/evidence/seat-repair-<date>/`: `runbook.md`
  (per-batch kickoff states, launches with rcs, probe replies, health
  snapshots, skips with reasons), ps snapshots per batch; zero queue
  mutation proven by queue-list diff per batch.
- Post-wave `make live-health` shows the repaired seats clean (remaining
  WARNs, if any, name only out-of-scope seats honestly).
- Triad box in `tasks.md` stays UNCHECKED (coordinator runs the triad;
  this stage does not commit).
