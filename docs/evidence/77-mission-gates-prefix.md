# S0 pre-fix silence evidence — 77-mission-gates (Refs #77)

Unpatched tree @ 6fe665f. Fixtures are synthetic B2-pattern replicas in
`/tmp` scratch only (dummy ids, no live fleet, no live queue). Transcripts
below are verbatim command outputs captured at S0 time.

## Fixture: gateless awaiting-gate parent (B2 pattern)

Tracker (`mission-dispatch-tracker.md`, Slices table, one row):

| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| B2-parent mission-row | owner-seat | verdict recorded | qitem-20261024023941-8685741b5ce805de | verdict recorded; Standing by for gate |

Queue side: the parent qitem is `in-progress` (destination `owner-seat`);
its trail is `claimed` (t40) then `verdict recorded, findings filed per
t41` (t41). No gate qitem exists anywhere: the tracker names exactly one
qitem (the parent), and the Status cell carries no second qitem reference.

## Transcript 1: reconciler stays silent (FAIL-ONLY, REQ-M2 pre-fix)

Command:

```
python3 scripts/reconcile.py --tracker /tmp/mg77/mission-dispatch-tracker.md --queue-list /tmp/mg77/queue_list.json --transitions /tmp/mg77/transitions.json
```

Verbatim stdout:

```
reconcile: in sync — 1 rows across 1 tracker(s) agree with queue state.
```

```
reconcile exit: 0
stalled-awaiting-gate signal: ABSENT
```

The gateless parent ("Standing by for gate", no gate row, no named gate
owner) reconciles silent on the unpatched tree: no diff class names it,
exit stays 0. This is the gap REQ-M2 closes.

## Transcript 2: dismissal without row state change succeeds (FAIL-ONLY, REQ-M3 pre-fix)

Flag-time vs close-time snapshots of the flagged parent row state
(canonical key-sorted JSON):

```
flagged : {"blockedOn": null, "destinationSession": "owner-seat", "qitemId": "qitem-20261024023941-8685741b5ce805de", "state": "in-progress", "statusCell": "verdict recorded; Standing by for gate"}
current : {"blockedOn": null, "destinationSession": "owner-seat", "qitemId": "qitem-20261024023941-8685741b5ce805de", "state": "in-progress", "statusCell": "verdict recorded; Standing by for gate"}
```

```
snapshots byte-identical: True
dismissal-without-change: ALLOWED
```

`sweep-typed-blocks.py` on the unpatched tree exposes no recovery
refusal guard (`check_recovery_dismissal` absent): closing the recovery
item while the flagged row is byte-identical to flag time is not refused.
This is the B2 outcome REQ-M3 closes (refuse, never auto-close).

## Secrets discipline

All ids above are dummy fixture ids; no bearer material was handled.
Acceptance grep (`grep -rE '[A-Za-z0-9_-]{40,}'` over this file) prints
nothing (exit 1): longest runs are the 37-char fixture qitem and short
timestamps/paths.
