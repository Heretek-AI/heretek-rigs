# Design: flag the park, measure the wait, label the daemon (81-seat-idle)

## Architecture

Three enforcement points, all short of writing row state or waking seats:

| # | Point | Change |
|---|---|---|
| 1 | Charter: seat skill (`specs/agents/_shared/skills/` via `fleet/skill-patches/` + `generate-rigs.py` regen) | Claim+first-action-is-one-turn rule: a seat holding an open obligation MUST NOT end its turn right after the claim. Prose rule for seats; machine halves below never write tracker state |
| 2 | `scripts/reconcile_model.py` (diff classes; wave-4 `stalled-awaiting-gate` precedent) | New diff class (name pinned by V30, e.g. `stalled-idle-park`): claim recorded + no work action + parked-at-prompt while holding an open obligation ⇒ stalled diff with park-to-wake vs work attribution attached. Pure classification + report — propose-only untouched, live-gate waiting and obligation-free idle stay quiet |
| 3 | Source validation (recovery handoff path feeding `send_identity.py` attestation) | Daemon-originated handoffs MUST carry the distinct daemon source (e.g. `daemon:stuck-sweep`); an `operator` label of daemon origin is refused or relabeled with a redacted log line. Wave-9 attested/unverified/rejected handling for genuine operator relays is unchanged |

Latency attribution (checkbox 2) is a report field on the idle-park diff (claim→wake vs wake→work split, fixture timestamps), consumable as inputs for #15/#17. It never advances rows and never touches the queue.

## Fail-closed modes

- Claim + park-at-prompt with open obligation and no work action ⇒ idle-park stalled diff (previously silent).
- Obligation-free idle or live-gate waiting ⇒ quiet (no diff).
- Daemon handoff labeled `operator` ⇒ refused or relabeled to the daemon source, redacted log; never recorded as an operator relay.
- Idle-park recovery close with unchanged flagged-row state ⇒ refused (wave-4 guard reused); never writes `done`.
- Worst case is a loud refusal or a review-routed diff, never a silent burial or a manufactured `done`.

## Decisions log (user decided in grilling rounds Q1–Q9)

- **D1 — target = #81.** Reason: clear observable trigger, fits the wave-4 detect/classify/propose-only pattern.
- **D2 — artifact = `openspec/changes/2026-10-28-81-seat-idle/` on `feat/81-seat-idle`.** Reason: waves 9/4 precedent, canonical promotion via `openspec archive`.
- **D3 — fixtures-only + propose-only.** Reason: safety posture of waves 4/9; no daemon edits, no live-host writes.
- **D4 — S0→S3 mirror of wave 4.** Reason: each stage gets a binary acceptance command; the coder never guesses.
- **D5 — new V30 gate, append-only.** Reason: V1–V29 audit-baselined; V19 freeze 37→38.
- **D6 — corpus ≥16 + S1a–S1d red-proofs.** Reason: sabotage must be non-vacuous (2-of-4 minimum re-run by QA, 4-of-4 by drift-guard).
- **D7 — AGENTS.md docs-map line only.** Reason: operator guide points at the spec; no rule-text changes.
- **D8 — non-goals locked: no daemon fix, no auto-wake, no live proof, no upstream filing, dummy keys + redacted logs.** Reason: #81 stays open until a live fleet proves the loop; #127 tracks any upstream gap separately.

## Trade-offs considered

- **Charter nudge vs daemon watchdog fix**: fixing the watchdog would address symptoms fleet-wide but requires daemon edits (out of repo scope, needs live host). Chosen: charter rule (repo-side, testable in fixtures) + stalled signal so the park is loud instead of silent.
- **Auto-wake vs force-owner-action**: auto-wake hides the turn-boundary bug and risks acting for the seat. Chosen: flag + refuse-dismissal-without-change (loud), never act for the owner.
- **Relabel vs refuse for operator-labeled daemon handoffs**: outright refusal could drop recovery context; silent relabel could mask the bug. Chosen: refuse-or-relabel with redacted log (V30 asserts the operator label never persists for daemon origin), preserving the evidence trail either way.
- **Amending propose-only vs leaving intact**: no requirement needs the amendment — classification, attribution, and refusal all fit inside propose-only. Left intact (least privilege).
