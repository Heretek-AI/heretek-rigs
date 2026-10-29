# Proposal: pre-authorization envelopes for slice classes (issue #15)

- **Change ID**: `2026-10-29-15-auth-envelope`
- **Issue**: Refs #15 (stays open until a live fleet proves authorization keeps pace with execution; never `Closes #15`).
- **Scope**: the issue's ask (a): standing pre-authorization envelopes for defined slice classes, plus the staleness measurement that justifies them. Options (b) freeze discipline and (c) accept-the-lag are recorded as considered-and-deferred (see `design.md`).

## Motivation

Seat fix cycles outrun the verify-then-authorize loop (issue #15, 2026-10-20, heretek-omni-fleet): the operator was authorized to commit "prior ae55c83 + #include hash.h one-liner, nothing else touched", but the live workdir held 11 files / +167−105. The TPM verification premise ("nothing else touched") was stale at execution time. The operator held the commit and escalated — no silent commit, no scope exceedance — but the gap is structural: each authorize→verify→execute round-trip assumes a frozen tree, and seats keep authoring during the round-trip. Third such round-trip on S02 alone.

Today in this repo: every landing needs a fresh human ruling per file-set; `send_identity.py` proves grant-bound mint/verify with single-use nonces and redacted logs (wave 9); `reconcile_model.py` proves propose-only stalled classification with report-only attribution (waves 4/81, incl. wave-81 park-to-wake attribution built explicitly as inputs for #15/#17). Nothing binds an authorization premise to the exact diff it authorizes, so drift between premise and landing is invisible until a human re-checks.

## Proposed change

1. **S0** — fixtures reproducing the #15 pattern (authorized premise vs live-diff drift; premise age at landing) plus a no-envelope baseline, proving current tooling neither flags the drift nor offers an envelope (FAIL-ONLY pre-fix evidence).
2. **S1** — premise-drift classifier (stalled signal, propose-only; clean premises stay quiet) with premise-age attribution (report-only inputs for #17, never state writes).
3. **S2** — envelope mint/validate (`diff-hash` + scope paths + expiry + single-use nonce; any drift/scope-breach/expiry/replay at landing = fail-closed refuse, redacted log; envelopes never self-execute, never auto-commit) + appended **V31** gate + corpus.
4. **S3** — runbook/evidence with staleness samples as #17 inputs, secrets-discipline intact, reports.

## Non-goals

- Self-executing envelopes or auto-commit (forbidden — safety, same invariant class as never-`done`; see design).
- Freeze discipline (b) or accept-the-lag (c): decided against for this wave (throughput cost / status quo), recorded in `design.md`.
- Amending wave-4/9/81 propose-only / never-`done` / attestation discipline.
- Live-fleet proofs (fixtures only — verifiability flag stands).
- Upstream filing (tracked separately; no filing without principal authorization).
- Touching V1–V30 (append-only; post-wave total becomes 39).

## Acceptance summary (binding; see `tasks.md`)

- A1: premise-vs-landing drift is classified stalled (red-proven: sabotage reverts it to silent).
- A2: premise age is attributed report-only (inputs for #17, never writes state).
- A3: drifted/scope-breached/expired/replayed envelopes are refused at landing (red-proven); clean envelopes validate.
- A4: `verify-rigs.sh --check-only` → 39 passed, 0 failed (V31 green, V1–V30 intact).
- A5: `make test` green with grown corpus; `audit_loop.py --self-test` PASS; `generate-rigs.py --check-idempotent` byte-identical; zero unredacted secret-shaped strings in evidence.
