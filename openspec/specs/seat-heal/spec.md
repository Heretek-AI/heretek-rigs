# seat-heal Specification

## Purpose
Heal wave for #147: the 2 `lobotomized`-class seats from the
seat-hygiene audit (`build-java-kotlin-eng`,
`build-python-backend-spec` @ `heretek-omni-fleet`) get their dangling
`shellPath` re-resolved (supported full member-fragment re-seed from
the durable checkout — `--refresh-policy-only` is structurally
insufficient) plus a fresh launch and a live exec probe; the wave
closes with a class-level proof (`make live-health`
`seat-shell-paths` names zero dangling seats). Refs #147 — never
Closes.

## Requirements

### Requirement: REQ-SH1 — kickoff re-verification with scope cap

The wave MUST re-verify the dangling set LIVE before touching any seat
(read-only: per-target `settings.json shellPath` + `agentActivity`
from `rig ps --nodes --json --no-cleanup -A` + fleet-wide
`make live-health` glance). Repair proceeds ONLY when the observed set
matches the expected 2 (or is a strict subset), every target is idle,
and total dangling is ≤ 4. Any drift beyond the cap, or any target
ACTIVE/mid-work, STOPS the wave with a recorded NO-GO — nothing is
improvised and the cap is never exceeded.

#### Scenario: set matches expectation, wave proceeds

- When kickoff shows exactly `build-java-kotlin-eng` and
  `build-python-backend-spec` dangling, both running/idle, and
  `seat-shell-paths` names no other seat, the 2-seat heal proceeds.

#### Scenario: scope drift stops the wave

- When kickoff shows more than 4 dangling seats, or any target with
  ACTIVE-family `agentActivity`, no seed/launch/send is issued; the
  runbook records NO-GO with the observed state (ps excerpt + health
  output) and the wave reports back.

### Requirement: REQ-SH2 — per-seat re-seed, relaunch, and live probe

Each in-scope seat MUST be re-seeded from the durable checkout via the
full member-fragment path (so the baked worktree path is replaced by
the durable in-repo wrapper), then fresh-relaunched (`--fresh --stop`
with an audited reason), then pass a config-clean check
(running/active/ready, clean `shellPath`, resolvable `launch_cwd`),
then answer an exec probe whose reply contains `SEAT-HEAL-OK` plus
genuine shell output. Idle-only: a seat found ACTIVE at kickoff
(re-checked per seat) is SKIPPED to report-only, named, and never
touched without per-seat approval.

#### Scenario: lobotomized seat healed and proven

- When a seat completes re-seed (rc=0), fresh launch (rc=0),
  config-clean check, and its transcript shows `SEAT-HEAL-OK` with
  genuine `rig queue whoami` output, the seat is recorded HEALED
  with every rc, the superseding sessionId, before/after shellPath,
  and the reply excerpt in the runbook.

#### Scenario: first RED aborts the wave

- When any seat's re-seed, relaunch, config-clean check, or probe
  fails (rc≠0, unclean config, or no genuine probe reply), no further
  seat is touched; the runbook records seat, step, and evidence as the
  stop point for a follow-up run.

### Requirement: REQ-SH3 — class-level proof with zero residue

The wave MUST close with `make live-health` showing `seat-shell-paths`
naming zero dangling seats, MUST leave zero residue (no queue rows
written/mutated — proven by a pre/post queue-list diff; no non-target
seat disturbed — proven by pre/post ps snapshots; no installs, no
upstream posts), and the repo diff MUST be limited to the change
package, evidence, one AGENTS.md docs-map row, and the implementation
report. No new V-gate is appended (live state isn't repo state —
unchanged rule).

#### Scenario: class proven clean, others untouched

- When the wave closes, the post-run health advisory shows the class
  PASS (or WARN naming only honestly-recorded out-of-scope seats),
  the queue-list diff is empty, and ps snapshots reconcile (only the
  healed seats differ by occupant generation).
