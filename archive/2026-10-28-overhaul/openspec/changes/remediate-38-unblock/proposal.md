# Proposal: remediate-38-unblock — event-driven re-evaluation of typed-external blocks

## Status
Spec-only change package for issue #38. No implementation in this package;
`tasks.md` is the testable checklist the implementation stage follows.

## Motivation
A row parked with `block --on <blocker>` (or parked-on-verdict discipline)
stays blocked after the blocker is satisfied. On 2026-10-22, W1-03
(`qitem-20261022052407-3d618a4431583b97`) and W1-04
(`qitem-20261022052409-291190744e33d1fe`) parked on the QA verdict; QA PASS
verdicts + placements landed and the operator appended unblock notes to both
rows, yet both remained `blocked` (verified via `rig queue show` post-note).
Only the 2h timer wake will revisit them; the owner seats sit idle meanwhile.
Related: #15 (authorization-loop lag) is the same structural shape — premises
go stale between rounds.

## Fact sources (verified read-only before authoring)
- `rig queue update --help`: "A note without --state never changes row
  state." This is the exact mechanism of the incident: unblock notes appended,
  state untouched by design.
- `rig queue resolve --help`: "Resolve a leg-1 parked qitem (state=blocked
  on a human seat)". `resolve` covers ONLY leg-1 human parks — no verb exists
  for satisfying a typed-external blocker.
- `rig queue block --help`: `--on` accepts a live blocker qitem, a typed
  gate, or a human-seat session; "A live blocker qitem supplied with --on
  also wakes the row when resolved." So live-qitem blockers already
  self-wake — the gap is precisely typed non-qitem gates.
- `rig queue update --blocked-on`: blocker may be "a qitem id (must exist and
  be live), a human seat (FR-6 park…), or a typed non-qitem gate
  'fold:<what>' / 'auth:<what>' / 'external:<what>'". `external:<what>` is
  the parked-on-verdict shape with no wake path.
- Repo-wide grep: no `satisfy`, `unblock`, note-landed, or re-evaluation
  helper exists in `scripts/` or seat-facing docs.

## Boundaries
- Repo-side ONLY: a re-evaluation sweep (new script + scheduling/watchdog-job
  wiring + seat runbook in editable `docs/`, never in generated leaves)
  built EXCLUSIVELY on existing `rig queue` verbs
  (`list`/`show`/`transitions`/`update --state … --reopen`). No daemon patch,
  no assumed new CLI verb.
- An upstream `@openrig/cli` feature request for a `satisfy` transition
  (typed-blocker analogue of `resolve`) is filed as a tracked artifact, but
  the repo-side sweep MUST NOT assume it exists.
- Park-time discipline: every typed-external park MUST record a
  machine-checkable satisfaction predicate (what evidence, where), so
  re-evaluation is a check, not a judgment call.

## Non-goals
- No change to `resolve` (leg-1 human parks untouched) or to timer wakes
  (`--wake-after` stays as backstop, never the only wake for typed blocks).
- No auto-closing rows as `done` (unpark targets in-progress; `done`
  requires the verdict/acceptance path).
- #15 auth-loop proper (same shape, separate change if the principal scopes
  it).

## Acceptance (see tasks.md)
1. Returnable: a parked-on-verdict row transitions to in-progress (or done
   via the normal acceptance path) within one sweep cycle of the verdict
   note landing, with zero operator state surgery.
2. Replayed W1-03/W1-04 shape (blocked row + satisfied blocker + unblock
   note) unparks without `--state` surgery by the operator.
3. Ambiguous/insufficient evidence resolves to stay-blocked + recorded
   evaluation (fail-closed), never to silent unpark or silent drop.
