# Runbook — mission-row gate ownership (77-mission-gates, Refs #77)

Who closes a parent row once its evidence is in, and what happens when a
row waits on a gate nobody owns. Three flows, each exercised against
synthetic fixtures in `/tmp` scratch (dummy ids, no live fleet). Nothing
here writes tracker or queue state: detection, classification, and loud
refusal only — no bot may ever close a row to done (design D2).

## Flow A — owner closes with evidence on the row (REQ-M1, normal path)

When your acceptance evidence is recorded on your row and no live gate
qitem exists, the charter (mission-slice-sop checklist, gate-ownership
rule) directs the destination seat to close its own row `done` with a
closure reason — never "standing by" prose.

Exercised: tracker Status `CLOSED done per t41 verdict + closure recorded
(queue note 44)`, queue `closed` at t44:

```
reconcile: in sync — 1 rows across 1 tracker(s) agree with queue state.
reconcile exit: 0
```

Owner closed, evidence cited, queue agrees: converged, no diff.

## Flow B — creating a gate so someone else owns next action (REQ-M1/M2)

When the row genuinely cannot close yet and needs a named owner, the seat
creates a gate qitem addressed at that owner and records it on the row:

```
rig queue create --json --verify --gate qa-seat --destination qa-seat@rig --body-file /tmp/gate-note.md
```

The seat copies the new gate qitem ID from the `--json` result (never
retyped — bare `rig queue create` output is advisory only and bare create
is denied in-seat) into the row Status cell. Then the row Status names the gate, e.g. `verdict recorded; Standing by
for gate --gate qa-seat, gate qitem qitem-20261024024002-abcdef0123456789
(owner qa-seat@rig)`. A gate qitem with a live owner (non-terminal state +
destination session) exempts the row from the stalled signal: the gate
owner owns next action.

Exercised (gate `in-progress`, owner `qa-seat@rig`):

```
reconcile: in sync — 1 rows across 1 tracker(s) agree with queue state.
reconcile exit: 0
```

Without the gate row, the same prose is `stalled-awaiting-gate` (exit 1,
missing gate named) — see the S0 prefix evidence and REQ-M2 corpus. A gate
whose state went terminal, or a gate reference with no queue entry, does
NOT exempt: the row still waits gateless.

(The `rig queue create --json --verify` form above is the permitted
in-seat seat-run shape against the live fleet — bare `rig queue create`
is denied in-seat per V22; it was not executed here — fixtures only, no
live daemon.)

## Flow C — stuck-recovery dismissal needs a row state change (REQ-M3)

When the sweep flags a stuck row, closing the recovery item while the
flagged row is byte-identical to flag time is refused fail-closed:

```
dismissal-without-change: RecoveryDismissalRefused
log: recovery-dismissal-refused: recovery-B2-01 for flagged row qitem-20261024023941-8685741b5ce805de (row state byte-identical to flag time; owner action required, never auto-close)
```

The flagged row keeps its state and the recovery item stays open. Once the
owner acts (gate created, row advanced, verdict plus closure recorded) the
snapshots differ and the close is permitted:

```
dismissal-with-change: {'dismissal': 'permitted', ...}
```

Guard: `check_recovery_dismissal` in `scripts/sweep-typed-blocks.py`;
every interpolated log value passes through seed-rig `_redact_for_log`.
The guard returns data or raises — it performs no write and never emits a
terminal state. Production wiring: `run_sweep` retains each flagged
(stay-blocked) row's flag-time snapshot in `report["recovery_guards"]`,
and `request_recovery_dismissal` is the close-time gate — it re-reads the
flagged row via `fetch_show`, invokes the guard, and fails closed on an
unreadable row. (No queue-close hook exists in-repo by design: the sweep
allowlist refuses close writes and no bot may close to done — D2.)

## Quick reference

| Row shape | Reconcile | Emitter | Dismissal |
|---|---|---|---|
| evidence in, row closed `done` + reason | in sync (0) | unchanged | n/a |
| gateless "standing by for gate" | `stalled-awaiting-gate` (1) | `stalled-awaiting-gate` review | refused while row frozen |
| gated wait, live gate owner | quiet (0) | quiet | allowed once row moves |
| recovery close, row unchanged | n/a | n/a | `RecoveryDismissalRefused` |

## Secrets discipline

Dummy fixture ids only; no bearer material handled. The wave-end grep
(`grep -rE '[A-Za-z0-9_-]{40,}'` over this file and the S0 prefix file)
prints nothing.
