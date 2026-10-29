# Runbook — pre-authorization envelopes (15-auth-envelope, Refs #15)

Who authorizes a landing, how a landing is validated against that
authorization, and what happens when the landing drifted from its premise.
Three flows, each exercised against synthetic fixtures in `/tmp` scratch
(dummy ids and dummy 16-hex diff hashes, no live fleet). Nothing here
writes tracker or queue state and nothing commits: authorization artifacts
authorize — only actors act (design D8). Recovery dismissal requires a row
state change (the wave-4/81 refusal-guard precedent, reused — never `done`,
never committed).

## Flow A — envelope issuance + landing validation (REQ-E1/E3, normal path)

The TPM (or standing operator order) mints an envelope binding the exact
TPM-verified diff-hash plus scope paths plus a mandatory expiry window
plus a single-use nonce, HMAC-bound under the seat binding secret (0600
store, `!cat`-style render — never inline):

```
envelope = mint_envelope(secret, "aaaaaaaaaaaaaaaa",
                         ["src/include/hash.h"],
                         expires_at=1780000000,
                         nonce="runbook-issuance-00001")
```

The landing is validated at landing time — a pure check plus a redacted
log. A clean landing (hash matches, paths inside scope, live, fresh nonce)
authorizes; the actor still performs the landing (no self-execution, no
auto-commit — the module owns no executor and none is added):

```
auth-envelope: authorized (a1b2c3d4e5f60718 scope src/include/hash.h; actor still performs the landing)
Flow A clean landing -> authorized
```

A drifted landing (hash differs, or paths outside scope), an expired
envelope, or a replayed nonce is refused fail-closed with a redacted log;
the row keeps its state and the nonce store is never rewound (a refused
landing never consumes its nonce):

```
auth-envelope: refused (landing diff f1f2f3f4f5f60718 drifted from authorized premise a1b2c3d4e5f60718)
Flow A drifted landing -> refused
```

Exercised: `scripts/auth_envelope.py` mint + validate against /tmp/si15/rb
fixtures (dummy secret, dummy hashes). The envelope file lands via
`write_envelope_exclusive` (fresh 0600 path, never overwrite).

## Flow B — drift triage when the landing drifted (REQ-E2, review path)

When the live landing diff no longer matches its authorized premise, the
reconciler emits `stalled-premise-drift` with the premise-age attribution
attached and routes the row for human review (NEEDS-HUMAN-REVIEW, review
only — no paste-ready cell, no state write). Exercised (tracker premise
`authorized premise a1b2c3d4e5f60718 scope src/include/hash.h; premise at
2026-10-20T10:00:00.000Z; verified at 2026-10-20T10:05:00.000Z`, queue
landing `landing diff f1f2f3f4f5f60718 paths
src/include/hash.h,src/extra/eleven.c at 2026-10-20T10:12:00.000Z`):

```
reconcile: 1 tracker(s) vs queue state (1 queue rows)
DIFF [stalled-premise-drift] /tmp/si15/rb/runbook-tracker.md:6 slice S02 landing slice qitem qitem-20261020100001-a1b2c3d4e5f60718
  reason:  landing diff f1f2f3f4f5f60718 drifted from authorized premise a1b2c3d4e5f60718 and reaches outside scope: src/extra/eleven.c
  tracker: authorized premise a1b2c3d4e5f60718 scope src/include/hash.h; premise at 2026-10-20T10:00:00.000Z; verified at 2026-10-20T10:05:00.000Z; TPM verified
  queue:   state=in-progress latest_transition=62 (landing diff f1f2f3f4f5f60718 paths src/include/hash.h,src/extra/eleven.c at 2026-10-20T10:12:00.000Z)
  attribution: premise age 720.0s at landing (premise 2026-10-20T10:00:00.000Z -> landing 2026-10-20T10:12:00.000Z)
  NEEDS-HUMAN-REVIEW: TPM decide; owner owns next action.
  SUGGESTED (not paste-ready): Route S02 landing slice for human review: landing diff f1f2f3f4f5f60718 drifted from authorized premise a1b2c3d4e5f60718 and reaches outside scope: src/extra/eleven.c (premise age 720.0s at landing (premise 2026-10-20T10:00:00.000Z -> landing 2026-10-20T10:12:00.000Z)); the owner owns next action (fresh premise, narrowed scope, or explicit hold)
reconcile: 1 diff(s) across 1 row(s); TPM approval required — no files modified.
Flow B drifted reconcile exit: 1
```

A landing identical to its premise within scope reconciles silent (exit 0,
in sync); a row declaring no premise never matches the drift class. An
open authorization with no matching landing record stalls with the
attribution naming the missing record.

## Flow C — landing recovery requires a row state change (REQ-E3)

A refused landing leaves the flagged row untouched, and closing the
recovery item while the row state is byte-identical to flag time is refused
fail-closed with a redacted log line (`check_recovery_dismissal` in
scripts/sweep-typed-blocks.py — the wave-4/81 precedent, reused). The
close succeeds only after the row state changed (fresh premise, narrowed
scope, or explicit hold recorded by the owner). The guard never writes
`done` and never commits — the never-`done` / never-auto-commit rules
stand. Exercised by
tests.test_auth_envelope.TestEnvelopeMintValidate.test_recovery_needs_row_state_change
(refusal on identical snapshots; permitted on changed snapshots).

## Premise-age samples (#17 inputs, report-only)

Premise age at landing is computed from fixture timestamps and reported on
the drift diff — never written to tracker or queue state:

| sample | premise | verified | landing | premise age | verify-to-landing |
|---|---|---|---|---|---|
| S02 drifted (#15 replica) | 2026-10-20T10:00:00.000Z | 2026-10-20T10:05:00.000Z | 2026-10-20T10:12:00.000Z | premise age 720.0s | 420.0s |
| S02 clean | 2026-10-20T10:00:00.000Z | 2026-10-20T10:05:00.000Z | 2026-10-20T10:12:00.000Z | (no diff — quiet) | — |

Unparseable timestamps yield unknown ages (still flagged; the age is
unknown, not zero). These samples are inputs for #17 staleness
measurement; attribution never advances rows and never touches the queue.

## Secrets discipline

All ids, hashes, and secrets above are dummy fixture values (16-hex runs,
`dummy-` prefixed secrets); no bearer material was handled. Acceptance
greps (`grep -rE '[A-Za-z0-9_-]{40,}'` over this file) print nothing (exit
1). Every new log path routes through seed-rig `_redact_for_log`.
