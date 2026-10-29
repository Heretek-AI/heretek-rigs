# S0 pre-fix silence evidence — 15-auth-envelope (Refs #15)

Unpatched tree @ 471f628. Fixtures are synthetic #15-pattern replicas in
`/tmp` scratch only (dummy ids, no live fleet, no live queue). Transcripts
below are verbatim command outputs captured at S0 time.

## Fixture: authorized one-liner premise vs multi-file drifted landing (#15 pattern)

Tracker (`mission-dispatch-tracker.md`, Slices table, one row):

| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| S02 landing slice | owner-seat | hash.h one-liner | qitem-20261020100001-a1b2c3d4e5f60718 | authorized premise a1b2c3d4e5f60718 scope src/include/hash.h; premise at 2026-10-20T10:00:00.000Z; verified at 2026-10-20T10:05:00.000Z; TPM verified |

Queue side: the parent qitem is `in-progress` (destination `owner-seat`);
its trail is `claimed` (t61, 2026-10-20T10:00:00.000Z), then the landing
record `landing diff f1f2f3f4f5f60718 paths
src/include/hash.h,src/extra/eleven.c at 2026-10-20T10:12:00.000Z` (t62).
The landing diff hash differs from the authorized premise hash and the
landing file-set reaches outside the authorized one-liner scope — the
11-file vs one-liner shape of the 2026-10-20 incident (issue #15).

Premise-age spread fixture: premise 2026-10-20T10:00:00.000Z, verified
2026-10-20T10:05:00.000Z (+300s), landing 2026-10-20T10:12:00.000Z (+720s
premise age at landing, +420s verify-to-landing).

No-envelope baseline: no `scripts/auth_envelope.py` exists and
`scripts/send_identity.py` exposes no premise-envelope mint/validate, so no
envelope authorizes (or refuses) this landing.

## Transcript 1: reconciler stays silent (FAIL-ONLY, REQ-E2 pre-fix)

Command:

```
python3 scripts/reconcile.py --tracker /tmp/si15/mission-dispatch-tracker.md --queue-list /tmp/si15/queue_list.json --transitions /tmp/si15/transitions.json
```

Verbatim stdout:

```
reconcile: in sync — 1 rows across 1 tracker(s) agree with queue state.
```

```
reconcile exit: 0
stalled-premise-drift signal: ABSENT
```

The drifted premise-vs-landing row (landing hash differs by the full
multi-file drift, landing paths outside the one-liner scope, premise aged
720s at landing) reconciles silent on the unpatched tree: no diff class
names it, exit stays 0. This is the gap REQ-E2 closes.

## Transcript 2: premise-age attribution absent (FAIL-ONLY, REQ-E2 pre-fix)

```
grep -c "stalled-premise-drift\|premise-drift\|premise age" scripts/reconcile_model.py
0
```

```
premise-age attribution: ABSENT
```

No premise-drift classifier and no premise-age report field exist anywhere
in the reconciler: the premise/verify/landing timestamps above (premise
2026-10-20T10:00:00.000Z, landing 2026-10-20T10:12:00.000Z) have no
attribution consumer. REQ-E2 adds the report-only field (inputs for #17,
never state writes).

## Transcript 3: no envelope validates the landing (FAIL-ONLY, REQ-E1 pre-fix)

```
grep -c "mint_envelope\|validate_envelope\|auth_envelope" scripts/send_identity.py
0
ls: cannot access 'scripts/auth_envelope.py': No such file or directory
```

```
envelope validation: ABSENT
landing authorization: NONE (no envelope to present, none to refuse)
```

No envelope module exists on the unpatched tree, so the drifted landing
above is neither authorized nor refused — authorization is invisible until
a human re-checks. This is the hole REQ-E1 closes (diff-hash + scope +
expiry + single-use nonce; drift/scope-breach/expiry/replay refused
fail-closed at landing).

## Secrets discipline

All ids and hashes above are dummy fixture values (16-hex runs); no bearer
material was handled. Acceptance grep
(`grep -rE '[A-Za-z0-9_-]{40,}'` over this file) prints nothing (exit 1):
longest runs are the 37-char fixture qitem and short timestamps/paths.
