# Typed-external block runbook (remediate-38-unblock)

A row parked on a typed non-qitem blocker (`external:<what>`, `fold:<what>`,
`auth:<what>`) has **no self-wake**: a live blocker qitem supplied with
`--on` wakes the row when resolved, but a typed gate never resolves, so only
timer wakes revisit it. On 2026-10-22, W1-03/W1-04 stayed `blocked` for hours
after QA PASS verdicts + placements landed and unblock notes were appended,
because `rig queue update` without `--state` never changes row state.

The re-evaluation sweep (`scripts/sweep-typed-blocks.py`) closes that gap.
This runbook is the park-time discipline that makes the sweep a check, not a
judgment call.

## 1. Park-time checklist (mandatory for every typed-external park)

Use the guard wrapper — it rejects bad parks with an operator-visible error
and creates no HELD row:

```
python3 scripts/park-typed-block.py <qitemId> --on external:<what> \
  --predicate "SATISFY-WHEN: <what evidence> VIA <where it lands>" \
  --note "<continuation>" (--wake-watchdog <id> | --sweep-covered) \
  [--wake-after 2h] [--dry-run]
```

1. **Predicate (REQ-BU1).** `--predicate` is required and must match
   `SATISFY-WHEN: <what evidence> VIA <where it lands>`. It travels in the
   park transition note — the sweep's carrier. Examples:
   - `SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report`
   - `SATISFY-WHEN: operator placement log VIA apps/web/src-tauri on disk`
   A predicate-less typed park is rejected: no HELD row is created.
2. **Live wake (REQ-BU4).** At least one of `--wake-watchdog <id>` (attached
   live watchdog) or `--sweep-covered` (this sweep's transitions-cursor
   coverage). `--wake-after` alone is **rejected** — a timer is a backstop,
   never the only wake for typed blocks. A live blocker qitem in `--on`
   also counts (it self-wakes on resolve).
3. `--dry-run` prints the exact `rig queue block` argv and executes nothing.
   Use it to rehearse.

Human-seat and live-qitem parks pass through unwrapped (`resolve` covers
leg-1 human parks; live qitem blockers already self-wake).

## 2. Recording satisfaction (REQ-BU3)

When the blocker is satisfied, append the explicit record with existing verbs
only — note-only, **no `--state` surgery by the operator**:

```
rig queue update <qitemId> --note "SATISFIED: <blocker> <evidence-ref>"
```

(Paste `<qitemId>` as the full ID copied from `rig queue list --json` output — never retype it.)

- `<blocker>` must be the row's `blockedOn` value (or its `<what>` suffix).
- `<evidence-ref>` is mandatory: a report path, placement location,
  transition ref (`t928`), or verdict qitem id. A bare `SATISFIED:` or
  `SATISFIED: <blocker>` with nothing after it is **malformed**: ignored,
  with a recorded evaluation (never acted on).

Legacy operator/seat verdict notes also count when they (a) name the
blocker's key, (b) carry an un-negated satisfaction token (`satisfied`,
`pass`, `resolved`, `verified`, `unblock`, `green`), and (c) cite evidence
(`per <artifact>`, `t<ref>`, `report`, `log`) — or come from the operator,
which is the verdict authority. Seat progress notes without a citation
("QA PASS, all good") do **not** unpark; add the citation or use the
`SATISFIED:` record.

## 3. Sweep operation (REQ-BU2/BU5)

```
python3 scripts/sweep-typed-blocks.py [--dry-run] [--cursor-file PATH] [--log-file PATH]
```

- **Discovery is read-only**: `queue list` / `transitions` (`--json`).
  The only live write is the spec'd unpark route
  (`update --state in-progress --reopen` + evidence-citing audit note).
- **Triggers**: a new transition on the parked row (leg (a)), or on a
  blocking verdict qitem named by the predicate — any `qitem-…` id cited in
  the row's transition notes (leg (b)). Both sides are keyed on the
  append-only transitions log with a per-row cursor entry
  (`{row: <parked-row max>, blockers: {<qitem>: <max>}}`) persisted in
  `--cursor-file` (default
  `/tmp/heretek-sweep-typed-blocks/cursor.json`; point it at a durable path
  when wiring the watchdog job). Either side advancing triggers
  re-evaluation; blocker-side satisfying notes count as evidence, cited
  with their source qitem. A blocker ref that is unresolvable/unreadable
  fails closed: stay blocked + named SKIP, retry next cycle, never unpark.
- **Cadence**: watchdog-cycle scale (≤15 min recommended — the incident's
  lesson was ~50 min of idle seats, so nightly scale defeats the purpose).
  Suggested watchdog-job wiring: run the sweep as an attached job on the
  fleet's watchdog cycle, or a 10–15 min cron on the shell host with
  `--log-file` appended to the ops log. (Wiring is operator-executed; this
  change ships the script + discipline, no live jobs.)
- **Unpark targets `in-progress` only.** `done` requires the
  verdict/acceptance path; the sweep structurally cannot emit `state=done`
  (the argv builder refuses it; tests scan every emitted argv).
- **Fail-closed table**:

  | Condition | Sweep behavior |
  |---|---|
  | Predicate satisfied, unambiguous | Unpark + audit note citing evidence |
  | Evidence ambiguous / partial | Stay blocked + recorded evaluation naming what is missing |
  | Malformed `SATISFIED:` | Ignored + recorded evaluation |
  | Blocker ref unresolvable (deleted qitem) | Stay blocked + WARN naming the ref, retry next cycle |
  | Later note cites new failure/rework | Block re-armed, stay blocked |
  | Evidence-free restatement ("blocker stands", "park continues") | Does NOT override a prior satisfaction |
  | Daemon unreachable | Log-only error, exit 2, no evaluations claimed |

- **Idempotency**: reruns with no new transitions emit nothing (per-row
  cursor); double-wake with `--wake-after` timers is harmless (the second
  evaluation sees an in-progress row and no-ops). `--dry-run` reports
  would-unpark rows with zero live writes and zero cursor writes.

## 4. Deferred live pilot (manual, operator-executed)

No live queue state was mutated by this change (fixtures only). First live
pilot, in order:

```
python3 scripts/sweep-typed-blocks.py --dry-run   # read-only: confirm WOULD-UNPARK set
# review each WOULD-UNPARK citation, then:
python3 scripts/sweep-typed-blocks.py --cursor-file <durable-path> --log-file <ops-log>
rig queue show --json <unparked-id>               # confirm in-progress + audit note
```

Note: the unpark route is `update --state in-progress --reopen`. If the
daemon rejects `--reopen` on a non-terminal state, drop `--reopen` for that
run and record the daemon's exact error in the implementation report
follow-up — do not work around it with any other state verb.
