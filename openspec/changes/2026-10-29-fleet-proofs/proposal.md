# Proposal: 2026-10-29-fleet-proofs — live-host proof batch

## Goal

Execute the ordered live-host runbook proving the repo-side remediations for
#91, #12, #74, #96/#11-refresh, #77, #81, #9, #15, and the #107 MCP half on
the fleet host, and record redacted evidence per step. Single PR, Refs-only
(never Closes — every issue stays open until its live loop is proven).

## Non-goals

- No behavior-code changes, no new V-gate (per plan Q9/Q12).
- No upstream filing (Wave 4), no F4 classifier work (Wave 5), no #78 (own spec).
- No fleet-wide seat launches in Phase A; any seat launch for Phase B needs
  explicit user approval (sensitive action: token spend + side effects).

## Phase split

- **Phase A (this change, landed first):** change package + Step 1 safe-check +
  Step 2 provisioning re-take + read-only live recon with per-step GO/NO-GO.
- **Phase B (gated on user approval):** runbook steps 3–7 against live seats.

## Acceptance

- Compound green in the worktree (39/0, `openspec validate`, self-test,
  idempotent); `make test` skipped with reason (no code/tests touched).
- Every executed runbook step has an evidence file with rc=0 or a named
  follow-up; every deferred step has a recorded NO-GO reason.
- Triad `VERDICT: PASS` before PR.
