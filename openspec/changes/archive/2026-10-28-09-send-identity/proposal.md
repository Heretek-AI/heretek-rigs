# Proposal: per-seat sender attestation for `rig send` (issue #9)

- **Change ID**: `2026-10-28-09-send-identity`
- **Issue**: Refs #9 (stays open until live proof). Daemon-side gap tracked in #127 (blocked, upstream filing needs principal approval).
- **Precedent**: #121 (`2026-10-28-107-identity`, archived) — per-seat MCP bearer grants, V23/V24 gates, R3 same-rig refutation.
- **Scope**: repo-side only (`fleet/`, `scripts/`, tests, verify gate, docs). No daemon edits, no upstream filing, no fleet-host live proofs in this wave.

## Motivation

`rig send` issued from outside a managed seat arrives with **no sender identity**, so seats hold it as UNVERIFIED (`docs/USER_GUIDE.md:224-225`).
The current workaround (`scripts/send-authenticated.sh`) never invokes raw `rig send` (`:4-6`) and records `--source` only as
`claimed:v1` — an explicit claim-not-proof (`:8-11,40,68-71`) with a never-forge rule (`:73-79`).

Root cause (established in #121): `OPENRIG_SESSION_NAME=<seat>` is a spoofable env var that yields
`identityProvenance: transport:v1`, and pps strips leading `VAR=` so `*OPENRIG_SESSION_NAME=*` never fires
(`openspec/changes/archive/2026-10-28-107-identity/proposal.md:8`, `scripts/gate-role.sh:146`).
Residual F9 stands: bare-leading `OPENRIG_SESSION_NAME=x rig whoami` executes rc=0 (`docs/NOTES.md:239`).
The in-jail relay guard (`scripts/seat-sandbox.sh:103-106`, `--source==$OPENRIG_SESSION_NAME`) inherits the same spoofable root.

## Proposed change

Extend the landed #121 bearer-grant model to **sender attestation**:

1. **S0** — isolated-scratch spike proving a forged `--source`/env sender is accepted pre-fix (verbatim evidence, like #123 M0).
2. **S1** — grant-bound sender attestation: seed-time per-seat sender binding reusing the `issue_seat_grant` issuance path
   (`scripts/seed-rig.py:266-272`, `--seat`/`--rig` scope `:354-356`, 0600 store `:337-352,384-391`, fail-closed parse `:147-161`,
   revoke-on-fail `:371-378,398-404`) with `!cat`-reference render (never inline secrets, cf. `render-seat.py:942-948`).
   Relay verifies attestation; client-supplied sender claims are ignored.
3. **S2** — appended **V28** verify gate (new block, never renumber) + `tests/test_send_identity.py` corpus.
4. **S3** — rotation/runbook docs + evidence, secrets-discipline intact.

## Non-goals

- Daemon-side attestation or queue-half changes (REQ-I3 disposition stands; #127 tracks the upstream gap).
- Filing upstream against `mvschwarz/openrig` (principal authorization required — NOT granted in this wave).
- Fleet-host live proofs (#91 live, #12 D1–D4, #74 provisioning — Priority 2, deferred).
- Any change to the 35 audit-baselined gates V1–V27 (append-only; post-wave total becomes 36).

## Acceptance summary (binding; see `tasks.md` for runnable commands)

- A1: all four must-fails red-proven (spoofed `--source` ignored, replay rejected, cross-rig impersonation impossible, V22 bare-send deny preserved).
- A2: `verify-rigs.sh --check-only` → 36 passed, 0 failed (V28 green, V1–V27 intact).
- A3: `make test` green with grown corpus (`tests/test_send_identity.py` rc=0).
- A4: `audit_loop.py --self-test` PASS, `generate-rigs.py --check-idempotent` byte-identical.
- A5: zero unredacted bearer-shaped strings in evidence; `_redact_for_log` choke-point reused.
