# Proposal: seat idle-park after claim + daemon source label (issue #81)

- **Change ID**: `2026-10-28-81-seat-idle`
- **Issue**: Refs #81 (stays open until a live fleet proves the loop closed; never `Closes #81`).
- **Scope**: the issue's three asks, nothing else. No daemon edits, no auto-wake — by safety decision, not compatibility (see `design.md`).

## Motivation

Seats claim a qitem and then park idle at the prompt without doing the work; progress depends on the daemon's parked-owner-consumer watchdog wake (issue #81, factory audit 2026-10-23/24: Mission A `qitem-20261023213329-7ad896bfc962330d` claimed in 8s, "Handoff received — pulling the queue item", then parked until `[OpenRig watchdog scheduler · policy: parked-owner-consumer …] You are parked (arbitrated: idle at prompt) while holding 1 open obligation`; same pattern on design-ui-ux-designer (B), red-binary-reverse-eng (C, C2), gameplay-tech-artist-pipeline (D); claim latency 8–31s, close latency 22–53s, part of the spread is park-then-wake, not work). Separately, daemon-generated recovery handoffs reach seats as `From: operator` (B2 recovery `qitem-recovery-3b06228ed0da95e8`), colliding with the #9 trust model where operator relays come through `send-authenticated.sh` with a human-ref. Nothing defines claim+first-action as one turn, nothing measures park-to-wake vs work, and nothing forces daemon handoffs to carry a distinct source.

Today in this repo: seat charters live in generated leaves (One Rule: edit via `fleet/skill-patches/` + regen); `reconcile_model.py` classifies tracker prose propose-only (wave-4 `stalled-awaiting-gate` precedent); `send_identity.py` binds operator sender attestation per wave 9 (attested/unverified/rejected, `!cat` render, 0600 stores); `sweep-typed-blocks.py` never writes `done`.

## Proposed change

1. **S0** — fixtures reproducing the #81 pattern (claim-then-park with open obligation; park-to-wake latency spread; daemon handoff labeled `From: operator`), proving current tooling does NOT flag it (FAIL-ONLY pre-fix evidence).
2. **S1** — charter claim+first-action rule (via `fleet/skill-patches/` + regen, never hand-edited leaves) + idle-park classifier with latency attribution (propose-only, still no state writes) + daemon source label (`daemon:stuck-sweep`, never `operator`).
3. **S2** — non-dismissible idle-park recovery without row state change + non-spoofable daemon source (operator label refused for daemon origin, red-proven) + appended **V30** gate + corpus.
4. **S3** — runbook/evidence with latency inputs for #15/#17, secrets-discipline intact, reports.

## Non-goals

- Fixing the daemon watchdog, auto-waking parked seats, or closing rows to `done` (forbidden — safety, see design).
- Amending wave-4/9 propose-only / never-`done` / attestation discipline.
- Live-fleet proofs (fixtures only — verifiability flag stands).
- Upstream filing (tracked separately; no filing without principal authorization).
- Touching V1–V29 (append-only; post-wave total becomes 38).

## Acceptance summary (binding; see `tasks.md`)

- A1: claim-then-park with open obligation is classified idle-park stalled (red-proven: sabotage reverts it to silent).
- A2: park-to-wake vs work latency attribution is reported propose-only (inputs for #15/#17, never writes state).
- A3: daemon recovery handoff labeled `operator` is refused/relabeled to the distinct daemon source; operator attestation model (#9) intact (red-proven).
- A4: `verify-rigs.sh --check-only` → 38 passed, 0 failed (V30 green, V1–V29 intact).
- A5: `make test` green with grown corpus; `audit_loop.py --self-test` PASS; `generate-rigs.py --check-idempotent` byte-identical; zero unredacted secret-shaped strings in evidence.
