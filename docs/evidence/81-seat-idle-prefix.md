# S0 pre-fix silence evidence — 81-seat-idle (Refs #81)

Unpatched tree @ 8dec2ed. Fixtures are synthetic Mission-A-pattern replicas
in `/tmp` scratch only (dummy ids, no live fleet, no live queue). Transcripts
below are verbatim command outputs captured at S0 time.

## Fixture: claim-then-park with open obligation (Mission-A pattern)

Tracker (`mission-dispatch-tracker.md`, Slices table, one row):

| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| A-parent seat-row | owner-seat | claim recorded | qitem-20261023213329-7ad896bfc962330d | claimed, 1 open obligation; Handoff received — pulling the queue item; parked (arbitrated: idle at prompt) |

Queue side: the parent qitem is `in-progress` (destination `owner-seat`);
its trail is `claimed` (t11, 2026-10-23T21:33:29.000Z), then `Handoff
received — pulling the queue item` (t12, +8s), then the parked-owner-consumer
watchdog line `You are parked (arbitrated: idle at prompt) while holding 1
open obligation` (t13, +31s). No work action anywhere in the trail (no
verdict, no file, no QA prose); the seat holds 1 open obligation.

Latency spread fixture: claim 2026-10-23T21:33:29.000Z, handoff +8s, park
2026-10-23T21:34:00.000Z (+31s), wake 2026-10-23T21:34:53.000Z (+53s, +22s
park-to-wake), work_ts null (no work action recorded).

Daemon handoff fixture: stuck-sweep recovery item
`qitem-recovery-3b06228ed0da95e8` of daemon origin (`daemon:stuck-sweep`)
labeled `From: operator`.

## Transcript 1: reconciler stays silent (FAIL-ONLY, REQ-I2 pre-fix)

Command:

```
python3 scripts/reconcile.py --tracker /tmp/si81/mission-dispatch-tracker.md --queue-list /tmp/si81/queue_list.json --transitions /tmp/si81/transitions.json
```

Verbatim stdout:

```
reconcile: in sync — 1 rows across 1 tracker(s) agree with queue state.
```

```
reconcile exit: 0
idle-park signal: ABSENT
```

The claim-then-park parent (claimed, handoff receipt, parked-at-prompt
watchdog while holding 1 open obligation, no work action) reconciles silent
on the unpatched tree: no diff class names it, exit stays 0. This is the gap
REQ-I2 closes.

## Transcript 2: latency attribution absent (FAIL-ONLY, REQ-I2 pre-fix)

```
grep -c "park-to-wake\|idle-park\|stalled-idle-park\|attribution" scripts/reconcile_model.py
0
```

```
park-to-wake attribution: ABSENT
```

No park-to-wake vs work latency field exists anywhere in the reconciler: the
claim/work/wake timestamps above (claim 2026-10-23T21:33:29.000Z, wake
2026-10-23T21:34:53.000Z, work_ts null) have no attribution consumer. REQ-I2
adds the report-only field (inputs for #15/#17, never state writes).

## Transcript 3: operator-labeled daemon handoff passes unlabeled (FAIL-ONLY, REQ-I3 pre-fix)

```
daemon:stuck-sweep marker present: False
validate_handoff_source present: False
DAEMON_SOURCE present: False
```

```
daemon source rule: ABSENT
recorded source: operator
```

`scripts/send_identity.py` carries no daemon-source rule on the unpatched
tree, so the daemon-originated stuck-sweep recovery handoff
(`qitem-recovery-3b06228ed0da95e8`) labeled `From: operator` persists with
the operator label — the #9 trust-model collision REQ-I3 closes (refuse or
relabel to the distinct daemon source, redacted log).

## Secrets discipline

All ids above are dummy fixture ids; no bearer material was handled.
Acceptance grep (`grep -rE '[A-Za-z0-9_-]{40,}'` over this file) prints
nothing (exit 1): longest runs are the 37-char fixture qitem and short
timestamps/paths.
