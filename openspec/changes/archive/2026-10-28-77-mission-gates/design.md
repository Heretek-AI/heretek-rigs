# Design: gate ownership without auto-closure (77-mission-gates)

## Architecture

Three enforcement points, all short of writing row state:

| # | Point (file:line) | Change |
|---|---|---|
| 1 | Charter: `specs/agents/_shared/skills/mission-slice-sop/SKILL.md` (park/orchestrator judgment at `:87`) — edited ONLY via `fleet/skill-patches/` + `generate-rigs.py` regen | Closure-ownership rule: the destination seat closes its own row (`done` + closure reason) once acceptance evidence is on the row, unless a `--gate <role>` qitem exists with a live owner |
| 2 | `scripts/reconcile_model.py` (`:16-17` enum, `:373-453` diff classes, `:270-289` normalizer) | New diff class (name pinned by V29, e.g. `stalled-awaiting-gate`): a parent row whose status is awaiting-gate prose with NO gate qitem reference fails convergence and routes as stalled, not silent-OTHER. Pure classification — REQ-R2 propose-only untouched |
| 3 | `scripts/sweep-typed-blocks.py` (`:108-153` unpark route, `:644-783` run_sweep) | Recovery dismissal requires a row state change: closing a stuck-recovery item while the flagged row's state is byte-identical to flag time is refused (fail-closed). Never writes `done` — the never-`done` rule stands |

`--gate` semantics (from the issue): a seat that wants a gate creates one (`rig queue create --gate …`) with a destination; a gate qitem with a live owner exempts the row from the stalled signal. "Standing by for gate" with no gate row counts as stalled, never as a false positive.

## Fail-closed modes

- Awaiting-gate prose + no gate qitem ⇒ stalled diff (previously silent OTHER).
- Recovery close with unchanged flagged-row state ⇒ refused with redacted log line.
- Charter rule is prose for seats; machine-enforced halves (2, 3) never write tracker or queue state — worst case is a loud refusal, never a silent burial.

## Decisions log (user delegated all open branches; decided here with reasons)

- **D1 — scope = the issue's 3 checkboxes.** Reason: the issue is precise and complete; anything wider is scope creep.
- **D2 — no bot may ever close a row to done/complete.** Reason: SAFETY, not compatibility — auto-closure buries evidence and manufactures false "done"s; the B2 incident is exactly a premature sense of completion. Even with compat waived, this stays forbidden. Recorded as a constraint, not a requirement to implement (nothing to build — the existing never-`done` rule already holds).
- **D3 — fixtures-only acceptance.** Reason: `docs/NOTES.md:364` (live queue UNVERIFIABLE off-fleet); prior reconcile waves proved this pattern works.
- **D4 — charter via skill-patches + regen.** Reason: the SKILL.md leaf is generated; the One Rule forbids hand-editing it.
- **D5 — new V29 gate, append-only.** Reason: wave-9 precedent; V1–V28 audit-baselined.
- **D6 — spec ID `2026-10-28-77-mission-gates`.** Reason: archive convention + real UTC date.

## Trade-offs considered

- **Auto-close vs enforce-action**: auto-close is less toil but destroys the evidence trail the whole audit system exists to protect. Chosen: force the owner to act (loud refusal), never act for them.
- **Amending REQ-R2/G2 vs leaving intact**: waived compat would permit it, but no requirement needs the amendment — classification and refusal both fit inside propose-only. Left intact (least privilege).
