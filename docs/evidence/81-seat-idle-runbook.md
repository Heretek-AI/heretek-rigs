# Runbook — 81-seat-idle (Refs #81)

Seat idle-park after claim + daemon source label. Fixtures-only,
propose-only: nothing here writes tracker or queue state, wakes a seat, or
closes a row to `done`. All transcripts below are verbatim outputs captured
against `/tmp` scratch fixtures (dummy ids, no live fleet).

## Flow A — claim + first action is one turn (REQ-I1)

Charter rule (rendered leaf
`specs/agents/_shared/skills/queue-handoff/SKILL.md`, via
`fleet/skill-patches/queue-handoff.yaml` + regen, in all 9 leaves):

> **Claiming is not finishing — claim+first-action is one turn.** Claiming
> a qitem and the first work action are one turn: a seat holding an open
> obligation MUST NOT end its turn immediately after the claim with no work
> action recorded — no park-at-prompt after claim.

Operator check: after a seat claims a qitem, the next observable queue
transition on that qitem must be a first work action (verdict, file,
finding — anything outside the claim / handoff-receipt / parked-watchdog
classes), not a parked prompt. Negative control (claim `t11`, handoff
receipt `t12`, verdict filed `t13`, no park line), verbatim:

```
reconcile: in sync — 1 rows across 1 tracker(s) agree with queue state.
reconcile exit: 0
```

A worked claim stays quiet: the classifier only fires when the trail holds
a claim, zero work actions, and the Status cell shows parked-at-prompt
while holding a nonzero open-obligation count.

## Flow B — idle-park triage (REQ-I2)

Symptom: a seat claimed (`claimed` t11, `Handoff received — pulling the
queue item` t12) then the parked-owner-consumer watchdog line fired
(`You are parked (arbitrated: idle at prompt) while holding 1 open
obligation`, t13) with no work action anywhere; the tracker Status cell
reads `claimed, 1 open obligation; Handoff received — pulling the queue
item; parked (arbitrated: idle at prompt)`.

Run (read-only):

```
python3 scripts/reconcile.py --tracker <tracker> --queue-list <queue_list> --transitions <transitions>
```

Verbatim (exit 1, human review routed, nothing modified):

```
DIFF [stalled-idle-park] /tmp/si81/rb/si81rbB_kbrl9wuv/mission-dispatch-tracker.md:6 slice A-parent seat-row qitem qitem-20261023213329-7ad896bfc962330d
  reason:  seat claimed then parked idle at prompt while holding an open obligation with no work action recorded (parked: claimed, 1 open obligation; Handoff received — pulling the queue item; parked (arbitrated: idle at prompt))
  tracker: claimed, 1 open obligation; Handoff received — pulling the queue item; parked (arbitrated: idle at prompt)
  queue:   state=in-progress latest_transition=14 ([OpenRig watchdog scheduler · policy: parked-owner-consumer …] You are parked (arbitrated: idle at prompt) while holding 1 open obligation)
  attribution: park-to-wake vs work: seat still parked (wake pending); claim-to-park 31.0s, work share 0s
  PROPOSED Status cell:
    Route A-parent seat-row for human review: the owner claimed and parked without a first work action (park-to-wake vs work: seat still parked (wake pending); claim-to-park 31.0s, work share 0s); the owner owns next action (first work action or handoff), never a parked prompt while holding the obligation
reconcile: 1 diff(s) across 1 row(s); TPM approval required — no files modified.
reconcile exit: 1
```

Triage: page the owner seat to record the first work action or hand the
baton off; do NOT close anything — the diff is a review route, and the
recovery close-time guard (`check_recovery_dismissal`) refuses any
idle-park recovery dismissal while the flagged row is byte-identical to
flag time. Obligation-free idle (`queue exhausted`, no open-obligation
count) and live-gate waiting (live gate owner named) stay quiet — if the
row shows either, it is not an idle park.

Latency inputs for #15/#17 (report-only attribution sample, same fixture
plus a watchdog-release wake note at 2026-10-23T21:34:53.000Z):

```
claim_ts: 2026-10-23T21:33:29.000Z, park_ts: 2026-10-23T21:34:00.000Z
wake_ts: 2026-10-23T21:34:53.000Z, work_ts: null
claim_to_park_s: 31.0, park_to_wake_s: 53.0, work_s: 0
note: park-to-wake vs work: park-to-wake 53.0s vs work 0s (claim-to-park 31.0s)
```

Reading: of the 84s after claim, 31s ran claim-to-park and 53s ran
park-to-wake with zero work seconds — the spread is park-then-wake, not
work. Attribution never advances rows and never touches the queue.

## Flow C — daemon-source verification (REQ-I3)

Daemon-originated stuck-sweep recovery handoffs must carry the distinct
source `daemon:stuck-sweep`, never `From: operator` (operator relays arrive
through `send-authenticated.sh` with a human-ref; wave-9 attestation is
untouched). Verify with the repo-side validator (verbatim, stderr log
line first):

```
daemon-source-relabeled: daemon:stuck-sweep presented as operator relabeled to daemon:stuck-sweep (operator label never persists for daemon origin; redacted)
C1 daemon origin + operator label -> {'source': 'daemon:stuck-sweep', 'action': 'relabeled', 'presented_from': 'operator'}
C2 daemon origin + daemon label  -> {'source': 'daemon:stuck-sweep', 'action': 'persisted', 'presented_from': 'daemon:stuck-sweep'}
C3 operator origin + operator     -> {'source': 'operator', 'action': 'persisted', 'presented_from': 'operator'}
C4 unknown origin -> ValueError: validate_handoff_source needs an established origin
```

Record only the returned `source`: C1 is stored as `daemon:stuck-sweep`
(the operator label never persists, the recovery context is preserved,
the log line is redacted); C2 passes through; C3 keeps the operator source
with wave-9 mint/verify semantics unchanged
(attested → accepted, replay → rejected); C4 fails closed — establish
origin before presenting a source.

## Quick reference

| Signal | Meaning | Action |
|---|---|---|
| `stalled-idle-park` + `park-to-wake` attribution | claim-then-park, open obligation, no work | page owner for first work action or handoff; review only |
| `reconcile exit: 0` on a worked claim | claim followed by work action | quiet — no action |
| `recovery-dismissal-refused` on identical snapshots | close attempted without owner action | owner must act on the flagged row first; never `done` by tooling |
| `action: relabeled` to `daemon:stuck-sweep` | daemon handoff arrived as `operator` | store the daemon source; operator trust model intact |

## Secrets discipline

Dummy ids throughout; every new log path through seed-rig
`_redact_for_log`. Acceptance grep over this file prints nothing (exit 1):
no 40+ bearer-shaped runs.
