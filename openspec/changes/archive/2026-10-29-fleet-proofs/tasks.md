# Tasks: 2026-10-29-fleet-proofs

## Phase A (this landing)

- [x] Author change package (proposal/spec/design/tasks)
- [x] Step 1 safe-check (stat 600/700 + dry-run `!cat`-only, rc=0)
- [x] Step 2 provisioning re-take (B1–B3 + build tools + matrix addendum)
- [x] Read-only live recon (daemon, seats, firecrawl, versions) + GO/NO-GO
- [x] Compound green (39/0, validate, self-test, idempotent; make test skipped, no code/tests)

## Phase B (needs user approval — NOT in this landing)

- [x] Step 3: #91 in-seat builds (pytest RC=0, cmake RC=0, go policy-pass + exec-BLOCKED GOCACHE follow-up)
- [x] Step 4: #12 D1–D4 engine compile + ELAPSED (FOLLOW-UP: needs tasked engine seat + capable runner; step-3 attempts are adjacent evidence only)
- [x] Step 5: #96 full loop green (hashes, refresh x2, live denial, revert, restoration proven)
- [x] Step 6: loops (#9 8/8 incl. 124-test host run; #15 same; #77 detect-scan + fixtures, recovery follow-up; #81 GREEN both rounds)
- [x] Step 7: #107 mechanism green (live issue/revoke/cleanup; V23/V24 in 39/0; queue half -> Wave 4; firecrawl NO-GO)
- [x] Triad (self-triad + independent agency-qa re-review PASS [8f27252] + independent agency-drift-guard audit VERDICT: PASS [5af4712]) → `VERDICT: PASS` (see docs/reports/fleet-proofs-verification.md) → PR (Refs-only)
