# Design: remediate-38-unblock

## Why a repo-side sweep, not a daemon verb or `resolve` extension
`rig` is upstream (`@openrig/cli`, HANDOFF routes CLI changes upstream with
local workarounds first). Extending `resolve` beyond leg-1 human parks would
change upstream semantics for all consumers; a new `satisfy` verb is the
right long-term shape but ships on someone else's clock. The sweep needs only
verbs that exist today (`list`/`show`/`transitions`/`update`), so the fleet
unblocks on this repo's timeline. REQ-BU6 keeps the upstream path tracked
instead of silently forked.

## Why poll the transitions log, not subscribe to note events
No note-landed event or subscription primitive was found on the `rig queue`
surface. Polling `transitions` with a per-row cursor is idempotent,
crash-safe (cursor persists; reruns resume), and bounded (only HELD rows
with typed-external blockers are scanned, not the full queue). Cost:
unpark latency is bounded by sweep cadence — the returnable requires
within-one-cycle, so cadence MUST be set accordingly (watchdog-cycle scale,
not nightly scale; exact value calibrated by the implementer against the
50-minute idle lesson).

## Why the predicate lives on the row, not in sweep config
Blocker satisfaction is per-row knowledge (which verdict, which artifact).
Central sweep config would need editing per park — a toil burden that
recreates the manual-reconcile problem of #39. A park-time predicate makes
each park self-describing; the sweep stays generic. The trade-off is seat
discipline at park time (REQ-BU1 rejection rule), enforced by runbook, not
by code — acceptable because parks are already deliberate, low-volume acts.

## Fail-closed modes
| Condition | Sweep behavior |
|---|---|
| Predicate satisfied, unambiguous | Unpark to `in-progress` via `update --state … --reopen` + audit note |
| Evidence ambiguous/partial/contradictory | Stay blocked + recorded evaluation (never unpark, never drop) |
| Malformed `SATISFIED:` record | Ignore + recorded evaluation |
| Blocker reference unresolvable (deleted qitem, missing artifact) | Stay blocked + WARN naming the dangling reference |
| Sweep cannot reach daemon | No evaluations claimed; log-only error (no news is not good news — cf. #45 REQ-LH2 philosophy) |

## Risks
- The sweep unparks via `update --state … --reopen`, an operator-grade
  repair path: every invocation MUST carry the satisfying-evidence citation
  in its note, or QA treats it as state surgery (the exact failure the
  returnable forbids).
- Seat-facing instructions MUST live in editable `docs/` runbooks, never in
  generated leaves (`specs/`, `rigs/`, `rosters/`, `registry/` are regen
  outputs — HANDOFF/AGENTS.md one-rule). If charter text is needed, it goes
  through the generator (`fleet/` + regen), not hand-edits.
- Sweep cadence vs. `--wake-after` timers: both may fire on the same row.
  Idempotency (REQ-BU5 cursor) makes double-wake harmless — the second
  evaluation sees an in-progress row and no-ops.
