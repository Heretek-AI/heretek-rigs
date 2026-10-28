# Design: grant-bound sender attestation (09-send-identity)

## Architecture

Reuse the #121 issuance path end-to-end; bind a **sender identity** where #121 bound an MCP bearer token.

| Layer | #121 precedent (file:line) | Wave 9 reuse |
|---|---|---|
| Issuance | `issue_seat_grant` (`seed-rig.py:266-272`), `--seat` + `--rig` (`:354-356`), caller passes seat's own rig (`:524-530`) | Sender binding minted per seat with identical `--seat`/`--rig` scope semantics |
| Scope gate | `_grant_scope_matches`: seat+rigs==[rig], roots==[], no workspace/owner (`:231-250`); `seat_needs_grant` + `HERETEK_SEAT_GRANT_OPT_IN` (`:167-183`) | Same match rule for sender bindings; same opt-in env pattern |
| Fail-closed parse | `parse_issued_token` exact `Token for <name>,` + `^[A-Za-z0-9_-]{16,}$` (`:147-161`); revoke + rc=2 on failure (`:371-378`) | Same strictness for sender-binding issuance output |
| 0600 store | lstat rejects non-0600/non-regular (`:337-352`); mkstemp + fchmod 0600 + replace (`:384-391`); store-fail revokes (`:398-404`) | Identical store discipline; scratch/tests use dummy keys in `/tmp` (0600) |
| Render | `seat_grant_token_filename` no-`..`-`/` rule (`render-seat.py:649-655`); `!echo Bearer $(cat …)` reference (`:942-948`); 0600 materialize (`:1438,1325`); symlink/uid/`O_NOFOLLOW` (`:784-815`) | `!cat`-reference render, never inline secrets; filename MUST satisfy the same no-`..`-`/` rule (exact name chosen at implementation, pinned by V28) |
| Redaction | `_redact_for_log`: `[A-Za-z0-9_-]{40,}` → `…redacted…`, truncate >200 (`seed-rig.py:193-201`); choke-point `_fail` (`:287-290`) + store-error path (`:401`) | ALL new log paths go through `_redact_for_log`; evidence carries `or…XX`-style redaction or dummies only |
| Relay verify | `send-authenticated.sh` forgery guard (`:131-190`); `seat-sandbox.sh` `--source==$OPENRIG_SESSION_NAME` (`:103-106`) | Relay compares **attested** sender against the claimed `--source`; mismatch → claim ignored, message held UNVERIFIED (never rejected outright — availability); replayed attestation → rejected |

## Verification flow (normative)

1. Operator/seat sends via the authenticated path; the relay attaches the grant-bound attestation (server-side, never client-supplied).
2. Receiving side checks: binding exists for claimed seat AND scope matches (seat+rig) AND attestation fresh (non-replay).
3. Any client-supplied sender identity (`--source`, env) that disagrees with attestation is **ignored** (spoof-proof by construction, mirroring R3 same-rig refutation: impersonation impossible across rigs because scope binds `--rig`).
4. Missing attestation ⇒ UNVERIFIED (current behavior preserved — no availability regression).

## Fail-closed failure modes

- Issuance parse failure ⇒ revoke + non-zero exit (mirrors `:371-378`).
- Non-0600 / non-regular store ⇒ refuse pre-mint (mirrors `:337-352`).
- Scope mismatch on verify ⇒ treat as unattested (UNVERIFIED), log redacted.
- Replay (attestation seen before) ⇒ reject with redacted log line.
- Render of missing secret ⇒ `!cat` reference to absent path MUST fail closed at seed (strict default; degraded `--allow-missing-secrets` renders disabled, per AGENTS.md seeding rule).

## Threat model → must-fail mapping

| Attack | Pre-fix (S0 proves) | Post-fix (S1+S2 prove) |
|---|---|---|
| Forged `--source` (fleet-id guard bypass) | accepted as sender (verbatim log) | ignored; attested sender (or UNVERIFIED) recorded |
| `OPENRIG_SESSION_NAME` spoof (F9 residual) | `transport:v1` accepted | unattested ⇒ UNVERIFIED unless grant-bound attestation present |
| Replay of a valid attested send | n/a (no attestation exists) | rejected; single-acceptance enforced |
| Cross-rig impersonation (seat A @ rig X as seat B @ rig Y) | n/a | impossible: scope binds `--rig` (R3 analogue) |
| Bare `rig send` in-seat bypass | denied (V22) | still denied (V22 intact, re-asserted) |

## Trade-offs considered (decided in grilling)

- **Extend grants vs new envelope protocol** → extend. Reason: V23/V24 precedent, R3 refutation, and the 0600/`!cat`/redaction corpus are already audited; a new protocol would re-open all of them.
- **Reject vs hold-UNVERIFIED on missing attestation** → hold UNVERIFIED. Reason: no availability regression for paths not yet migrated; rejection applies only to proven forgeries/replays.
- **New V28 vs stretching V23** → new V28 block. Reason: V1–V27 are audit-baselined (append-only); stretching V23 would rewrite a baselined gate.
