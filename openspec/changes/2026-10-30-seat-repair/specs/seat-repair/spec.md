# Seat-repair

## Purpose

Live repair wave for #147: the 22 `stale`-class seats from the
seat-hygiene audit get their dangling `shellPath` re-resolved (supported
re-seed from the durable checkout) plus a fresh launch and a live exec
probe; `make live-health` learns a warn-first `shellPath` +
`launch_cwd` resolvability check so the class cannot silently
re-accumulate. Refs #147 — never Closes.

## ADDED Requirements

### Requirement: REQ-R1 — bounded batches with whole-wave abort

The repair MUST proceed in batches of at most 6 (6+6+6+4 = 22 stale
seats), with a fleet health check (`rig ps` shape vs baseline) between
batches. The FIRST failed relaunch, failed probe, or unexpected fleet
state MUST abort the whole wave; remaining seats roll to a follow-up
run with the stop point recorded honestly.

#### Scenario: batch closes green, next batch proceeds

- When batch B1 closes with all 6 seats relaunched, config-clean, and
  probe-PASS, and the fleet shape matches the baseline, batch B2
  kicks off with a fresh snapshot.

#### Scenario: first RED aborts the wave

- When any seat's re-seed, relaunch, config-clean check, or probe
  fails (rc≠0, unclean config, or no genuine probe reply), no further
  seat is touched; the runbook records batch, seat, step, and evidence
  as the stop point for a follow-up run.

### Requirement: REQ-R2 — per-seat re-resolve, relaunch, and live probe

Each in-scope seat MUST be re-seeded from the durable checkout (so the
baked worktree path is replaced by the existing in-repo wrapper), then
fresh-relaunched (`--fresh --stop` with an audited reason), then pass a
config-clean check (running/active/ready, clean `shellPath`,
resolvable `launch_cwd`), then answer an exec probe whose reply
contains `SEAT-REPAIR-OK` plus genuine shell output. Idle-only: a seat
found ACTIVE at kickoff (re-checked per seat) is SKIPPED to
report-only, named, and never touched without per-seat approval. The 2
lobotomized seats are verify-only — never relaunched.

#### Scenario: stale seat repaired and proven

- When a stale seat completes re-seed (rc=0), fresh launch (rc=0),
  config-clean check, and its transcript shows `SEAT-REPAIR-OK` with
  genuine `rig queue whoami` output, the seat is recorded REPAIRED
  with every rc and the reply excerpt in the runbook.

#### Scenario: ACTIVE seat skipped, lobotomized seat untouched

- When a target shows ACTIVE-family `agentActivity` at kickoff, it is
  recorded SKIP with reason and receives no seed, launch, or send;
  the 2 lobotomized seats receive read-only inspection only (no seed,
  launch, or send under any circumstance in this wave).

### Requirement: REQ-R3 — live-health shellPath + launch_cwd check with strict semantics

`make live-health` MUST check `shellPath` + `launch_cwd`
resolvability for every running seat: advisory WARN naming each
dangling seat (exit 0), promoted to FAIL under `--strict` through the
gate's existing warn-first promotion path. No new V-gate is appended
(live state isn't repo state — recorded decision).

#### Scenario: dangling seat trips the check, clean fleet clears it

- When the gate assesses entries including a seat whose `shellPath`
  target does not exist, the `seat-shell-paths` sub-check is WARN and
  names the seat, field, and target; when all entries resolve, it is
  PASS. Under `--strict`, the WARN promotes per existing gate
  semantics.

#### Scenario: unassessable degrades to SKIP, never healthy

- When a running seat's `settings.json` is missing/unreadable or its
  `seat status` is unparseable, the seat is listed as unassessed and
  the sub-check is SKIP (never PASS on partial data); the read-only
  allowlist still refuses every mutating verb.

### Requirement: REQ-R4 — zero residue and unchanged others

The wave MUST leave zero residue: no queue rows written/mutated
(proven by per-batch queue-list diffs), no non-target seat disturbed
(proven by per-batch ps snapshots vs baseline), no installs, no
upstream posts, and the repo diff limited to the change package, the
live-health script + tests, evidence, and one AGENTS.md docs-map row.

#### Scenario: close-out proves non-interference

- When the wave closes, every batch shows its queue-list diff empty
  and its ps snapshots reconciled (only the batch's own relaunches
  differ by occupant generation); the final `git status` shows only
  intended wave files.
