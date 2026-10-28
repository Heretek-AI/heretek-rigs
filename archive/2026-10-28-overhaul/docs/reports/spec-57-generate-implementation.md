# Report: spec-57-generate implementation (2026-10-23)

Stage: `spec-57-generate` (branch `docs/issue-57-generate-trackers`).
Spec-only stage: no `src/`/`scripts/`/`tests/` code touched. Worktree left
dirty-with-intent for the coordinator's commit step (NOT committed).

## Files written

- `openspec/changes/issue-57-generate-trackers/proposal.md` — motivation
  (last-mile paste toil after reconcile), boundaries (new
  `scripts/generate_trackers.py` + `make generate-tracker` + read-only
  parse at IMPLEMENTATION time; this change ships spec only), non-goals
  (auto-apply, queue writes, cross-wave rollup).
- `openspec/changes/issue-57-generate-trackers/design.md` — row-ownership
  table (Q7), note-append rule + exact cell shapes (Q8), per-tracker scope
  (Q9), locked enum mapping table (Q10), fail-closed matrix incl.
  empty-queue `[]` exit-2 rule (Q11), risks.
- `openspec/changes/issue-57-generate-trackers/specs/generate-trackers/spec.md`
  — RFC 2119 delta spec, `## ADDED Requirements`, REQ-G1..G5 each with
  Given/When/Then scenarios.
- `openspec/changes/issue-57-generate-trackers/tasks.md` — G-T1..G-T5,
  each with an explicit runnable binary pass/fail acceptance command,
  1:1 mapped (G-T1→G1+G5, G-T2→G1, G-T3→G2+G4, G-T4→G3, G-T5→wiring+docs).
- `AGENTS.md` — 1-line surgical table-row addition (Tracker proposals:
  `--json` discipline pointer, propose-only invariant, fresh-out refusal
  rule, `make generate-tracker` row). No broad rework; comments/format kept.
- This report: `docs/reports/spec-57-generate-implementation.md`.

## Verification outputs (real, run inside the worktree)

- `openspec validate issue-57-generate-trackers` → `Change
  'issue-57-generate-trackers' is valid`, exit 0 (binary `openspec`
  1.13.1 present; no npx fallback needed).
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 26 checks passed,
  0 failed`, exit 0 (incl. V10 reconcile 28/28 green).
- `git status --short` → ONLY `M AGENTS.md` + `??
  openspec/changes/issue-57-generate-trackers/`. No other dirt.
- `openspec/config.yaml`: NOT present in the worktree (no `openspec/`
  config file; only `openspec/changes/` exists) — noted per instructions,
  nothing invented.
- Stub scan (`grep TODO|stub|NotImplemented` over the new package) → clean.
- Ground truth verified first-hand: `python3 scripts/reconcile.py --help`
  (exit 0; `--tracker/--queue-list/--transitions/--live/--rig-bin/--rig/--out`
  flags as cited), `gh issue view 57 --json title,body` (deferred option
  (a) sketch confirmed), exit codes 0/1/2 + `O_EXCL` guard cited to exact
  `scripts/reconcile.py` lines (30-32, 95-157, 321-343).

## Decisions log (plan Q1..Q12 — all 12 applied)

- Q1 #57 next / Q2 #12 separate spike / Q3 upstream watch-wait: recorded
  as context; no artifact needed beyond this log.
- Q4 propose-only: REQ-G2 + design refusal matrix; extends REQ-R2.
- Q5 shared row model: REQ-G5 + G-T1 (importable-module refactor specified
  as implementation work, NOT performed in this spec-only stage).
- Q6 fresh-out `O_EXCL` guard: REQ-G2 scenarios + design matrix row.
- Q7 ownership/`NEEDS-HUMAN-REVIEW`: design ownership table + REQ-G1
  scenarios (both-side evidence, never guessed, still non-zero).
- Q8 cell shape + append-only-on-newer-transition: design Q8 section with
  the four exact shapes transcribed from `reconcile.py:321-343` behavior.
- Q9 per-tracker only: design scope section + REQ-G3/G-T4 (parent row only
  on its own qitem diff; no rollup engine).
- Q10 locked enum + mapping table: design table + REQ-G5 (amendment, not
  judgment, to add an arm).
- Q11 empty-queue `[]` exit-2: design matrix + REQ-G4 dedicated scenario
  (live `[]` state cited as the reason the rule exists).
- Q12 home + AGENTS.md patch: package at
  `openspec/changes/issue-57-generate-trackers/` + 1-row AGENTS.md patch.

## Deliberate deviation (1, flagged for coordinator)

Plan G-T1/G-T5 acceptance says `make generate TRACKER=… OUT=…`. The
worktree `Makefile:24` already defines `make generate` as the deterministic
fleet generator (`fleet/fleet.yaml` → 51 AgentSpecs / 8 RigBundles / Roster
/ Registry) with idempotency gates depending on it. Overloading that name
would shadow fleet generation and risk an operator running a full regen
when they meant a tracker proposal (or vice versa). The spec therefore
names the wiring `make generate-tracker TRACKER=… OUT=…` (proposal.md
boundaries, design risks, G-T5 text all state the reason). If the
coordinator prefers the literal plan name, G-T5 is the single point to
rename — no other artifact depends on the target name.

## Deferred / not done

- Generator implementation (`scripts/generate_trackers.py`), the G-T1
  importable-module refactor, fixtures, and `Makefile` wiring: specified,
  not built (spec-only stage per instructions).
- `make generate-tracker` does not exist yet — G-T5 acceptance commands
  referencing it are for the implementation wave, not runnable today.
- No commit (coordinator's commit step, per instructions).
