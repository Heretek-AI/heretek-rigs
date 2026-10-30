# Proposal: 2026-10-30-seat-heal — bounded heal of the 2 lobotomized seats (Refs #147)

## Goal

Heal wave for #147: re-resolve the dangling `shellPath` on the 2
`lobotomized`-class seats enumerated in
`docs/evidence/seat-hygiene-2026-10-30/dangling-seats.json`
(`build-java-kotlin-eng`, `build-python-backend-spec` @
`heretek-omni-fleet`), verify each with a live exec probe, and close
with a class-level proof: post-run `make live-health` advisory names
zero dangling seats. Refs #147 — never Closes (#147 stays open until a
triad records `VERDICT: PASS`, on principal say-so only).

## Principal-approved design (grilling Q1–Q2, implemented literally)

- **Q1 — mechanism per seat:** (1) re-seed to re-render config from the
  clean committed template via the repo's seed path
  (`python3 scripts/seed-rig.py
  rigs/heretek-omni-fleet/members/<member>.yaml --rig heretek-omni-fleet
  --pod build`, run from the MAIN checkout so the baked path is the
  durable one — `--refresh-policy-only` is INSUFFICIENT, see
  `design.md` §1); (2) `rig seat launch <seat> --fresh --stop
  --reason ... --json` (flags verified against installed 0.7.5);
  (3) exec probe via coordinator `rig send` echo task with reply check.
  Per-seat evidence: pre shellPath (dangling) → post shellPath
  (resolved) + probe reply.
- **Q2 — scope-drift rule:** at kickoff, the dangling set is re-verified
  LIVE (read-only inspection of the audit's 2 + a fleet-wide glance via
  `make live-health`). Repair idle dangling seats up to a CAP OF 4. If
  the set differs (more than 4 dangling, or any target ACTIVE/mid-work):
  STOP, record NO-GO with the observed state, report back — do NOT
  improvise, do NOT exceed the cap.
- **Standing bounds:** abort whole wave on first RED (failed
  re-seed/relaunch/probe, unexpected fleet state); pre/post `rig ps`
  snapshots; zero queue writes; no other seats touched; no installs; no
  upstream posts; no V-gate (unchanged rule — live state isn't repo
  state).

## Kickoff re-verification (2026-10-30, this wave, read-only)

- `rig ps --nodes --json --no-cleanup -A`: 55 rows = 51 fleet seats
  running/idle + 4 detached `@kernel` system rows (not fleet seats).
  Both targets running/idle — zero ACTIVE → within cap, GO.
- `settings.json shellPath` (daemon-state read) on both targets: the
  pruned-worktree absolute path (dangling, as audited).
- `make live-health`: `seat-shell-paths` WARN names EXACTLY the same 2
  seats; all other 49 clear. No drift → proceed with the 2-seat plan
  (cap 4 untriggered).

## Non-goals (explicit boundary)

- No other seats (the 22 stale seats are already healed under
  seat-repair; this wave touches ONLY the 2 lobotomized).
- No queue writes of any kind (probes go via `rig send` task messages,
  NOT queue rows).
- No relaunches beyond the cap of 4; no ACTIVE-seat touches.
- No installs, no upstream posts, no daemon-state hand-surgery (re-seed
  goes through `seed-rig.py`/`render-seat.py`, the supported tooling).
- No V-gate; never `Closes #147` (not in this package, not in any
  close-out text).

## Acceptance

- Compound green in the worktree (39/0, no new V-block; `openspec
  validate 2026-10-30-seat-heal` rc=0; `make test` SKIPPED with reason
  — zero code/test/script diffs, re-seed usage is an operation not a
  code change, and the `seat-shell-paths` class check from the prior
  wave already covers the class; `audit_loop.py --self-test` PASSED;
  `generate-rigs.py --check-idempotent` byte-identical).
- Evidence under `docs/evidence/seat-heal-2026-10-30/`: `runbook.md`
  (kickoff re-verification table, per-seat re-seed/relaunch/probe with
  rcs + sessionIds + before/after shellPath, health snapshots,
  skips/stops), ps snapshots pre/post; zero queue mutation proven by
  queue-list diff pre/post.
- Post-run `make live-health` advisory: `seat-shell-paths` names zero
  dangling seats (PASS on the class).
- Triad box in `tasks.md` stays UNCHECKED (coordinator runs the triad;
  this stage does not commit).
