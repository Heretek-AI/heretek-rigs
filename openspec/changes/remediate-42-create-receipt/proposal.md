# Proposal: remediate-42-create-receipt — mandate create --json --verify + shared upstream issue

## Status
Spec proposal for heretek-rigs issue #42. Specs only — no implementation in this package.

## Verified facts (encoded, not re-litigated)
- #42 CONFIRMED mode-dependent: under `output.compact`, `rig queue create`
  prints a human receipt sentence on stdout
  (`Queue create request ID: <id> (not proof of persistence) ...`) instead of
  the created row JSON, so every programmatic caller needs a follow-up `show`
  to confirm persistence and learn row state. Contrast: `queue update`
  returns the row JSON directly — create is the odd one out.
- Agent-safe form today: `create --json --verify` (or `--full`).
- The upstream ask (stdout carries a single JSON receipt/row) is the SAME
  stdout-purity principle as #44's notices. Coordination rule: NO second
  upstream issue — this change references the ONE issue filed from
  `remediate-44-json-trailer` (its tasks.md T4/T5), which covers the receipt
  alongside both notices.

## Change (local only, plus shared upstream reference)
1. Mandate `rig queue create --json --verify` as the ONLY agent-safe create
   form in charters, `docs/USER_GUIDE.md`, `README.md`, and root `AGENTS.md`.
2. Update `scripts/send-authenticated.sh` (the sole local create wrapper) to
   invoke create with the agent-safe flags and to parse the JSON receipt
   (extract `qitemId` + state) instead of passing through human text, failing
   closed when the receipt does not parse.
3. Record the shared upstream issue URL (filed via the #44 package) in this
   package, noting it covers the create-receipt ask.

## Shared upstream issue (filed once via remediate-44-json-trailer)

- https://github.com/mvschwarz/openrig/issues/1806 (filed 2026-10-23;
  single shared issue covering the create-receipt ask alongside both
  stdout notices; draft at `docs/evidence/upstream-queue-stdout-issue.md`).
  NO second issue filed — this package references the identical URL.

## Non-goals
- No separate upstream issue for #42 (single shared issue by design).
- No local fork/patch of `@openrig/cli`; no change to `--full` semantics.
- No change to `send-authenticated.sh` auth/pre-flight behavior — receipt
  parsing only.

## Acceptance
- `openspec validate remediate-42-create-receipt` passes clean.
- Implementer checklist in `tasks.md` is fully testable (grep + wrapper
  parse proof + single-create yields qitemId/state with no follow-up).
