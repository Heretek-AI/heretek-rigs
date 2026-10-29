# Design: authorize the premise, refuse the drift (15-auth-envelope)

## Architecture

Three enforcement points, all short of writing row state or committing:

| # | Point | Change |
|---|---|---|
| 1 | Envelope mint/validate (new module or `send_identity.py` extension reusing wave-9 HMAC/nonce discipline; decided at implementation) | Standing pre-authorization envelopes for defined slice classes: `diff-hash` + scope paths + expiry + single-use nonce (HMAC-bound, 0600 stores, `!cat`-style render where seats consume it). Mint is a standing operator/TPM order; validate is pure check + redacted log |
| 2 | `scripts/reconcile_model.py` (diff classes; wave-4 `stalled-awaiting-gate` / wave-81 `stalled-idle-park` precedent) | New diff class (name pinned by V31, e.g. `stalled-premise-drift`): landing diff ≠ authorized premise (or open authorization with no matching envelope) ⇒ stalled diff with premise-age attribution attached. Pure classification + report — propose-only untouched, clean premises quiet |
| 3 | Landing/refusal guard (recovery path; wave-4/81 refusal-guard precedent) | Landing validation requires a valid envelope: drift/scope-breach/expiry/replay ⇒ fail-closed refusal with redacted log. Recovery dismissal requires row state change. Never writes `done`, never commits — the never-`done` / never-auto-commit rules stand |

Premise-age attribution (checkbox: staleness measurement) is a report field on the drift diff (premise→verify→landing timestamps), consumable as inputs for #17. It never advances rows and never touches the queue.

## Fail-closed modes

- Landing diff ≠ envelope diff-hash ⇒ refused (previously invisible until human re-check).
- Landing outside scope paths ⇒ refused.
- Expired envelope or consumed nonce ⇒ refused; nonce store never rewinds.
- Refused landing ⇒ row untouched, redacted log; recovery close with unchanged row state ⇒ refused.
- Worst case is a loud refusal or a review-routed diff, never a silent commit or a manufactured landing.

## Decisions log (user decided in grilling rounds Q1–Q8)

- **D1 — target = #15.** Reason: structural gap (third S02 round-trip); wave-81 attribution feeds it directly.
- **D2 — mechanism = (a) pre-auth envelopes.** Reason: restores pace without stopping seats ((b) costs throughput) and without accepting the lag ((c) is status quo).
- **D3 — binding = diff-hash + scope + expiry.** Reason: the incident was exactly premise-vs-landing drift; anything looser re-opens the hole.
- **D4 — single-use nonce + mandatory expiry.** Reason: wave-9 nonce discipline, red-proven; expiry bounds the staleness window.
- **D5 — S0→S3 mirror of waves 4/81.** Reason: each stage gets a binary acceptance command.
- **D6 — new V31 gate, append-only.** Reason: V1–V30 audit-baselined; V19 freeze 38→39.
- **D7 — corpus ≥16 + S1a–S1d red-proofs.** Reason: sabotage must be non-vacuous (pins required where probes outrun the suite — wave-81 lesson).
- **D8 — envelopes never self-execute / never auto-commit.** Reason: SAFETY — authorization artifacts authorize; only actors act. Recorded as a constraint (nothing to build: no executor exists and none is added).
- **D9 — fixtures-only + propose-only; AGENTS.md docs-map line only.** Reason: safety posture of waves 4/9/81.
- **D10 — spec ID `2026-10-29-15-auth-envelope`.** Reason: archive convention + real UTC date.

## Trade-offs considered

- **(b) freeze discipline vs (a) envelopes**: freeze is simpler to specify (charter + signal) but stops seats during every round-trip — throughput cost on every landing. Chosen: envelopes keep seats authoring; drift is caught at landing, loudly.
- **(c) accept the lag vs (a)**: the hold path is safe and already works, but it scales with human attention and leaves the structural gap open. Chosen: measure the lag (attribution) AND close the gap (envelopes); the hold path remains as the fallback for un-enveloped landings.
- **New module vs extending `send_identity.py`**: wave-9 machinery (HMAC mint/verify, nonce seen-set, redacted logs) is directly reusable, but envelopes carry extra fields (diff-hash, scope, expiry) with their own validation. Left to implementation; either way the V31 block pins behavior, not location.
- **Amending propose-only vs leaving intact**: no requirement needs the amendment — classification, attribution, refusal all fit inside propose-only. Left intact (least privilege).
