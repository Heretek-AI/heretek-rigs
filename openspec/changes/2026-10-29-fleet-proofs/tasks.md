# Tasks: 2026-10-29-fleet-proofs

## Phase A (this landing)

- [x] Author change package (proposal/spec/design/tasks)
- [x] Step 1 safe-check (stat 600/700 + dry-run `!cat`-only, rc=0)
- [x] Step 2 provisioning re-take (B1–B3 + build tools + matrix addendum)
- [x] Read-only live recon (daemon, seats, firecrawl, versions) + GO/NO-GO
- [x] Compound green (39/0, validate, self-test, idempotent; make test skipped, no code/tests)

## Phase B (needs user approval — NOT in this landing)

- [ ] Step 3: #91 in-seat `pytest tests/rag`, `go build ./...`, `cmake -S . -B build`
- [ ] Step 4: #12 D1–D4 in-seat engine compile + ELAPSED (D5–D7 noted as follow-up if no committer)
- [ ] Step 5: #96 `--refresh-policy-only` on a running seat with tightened rule
- [ ] Step 6: live loops #77 mission-gate, #81 claim→action, #9 attestation, #15 envelope pace
- [ ] Step 7: #107 MCP half (governance boxes; firecrawl boot NO-GO from this host)
- [ ] Triad (QA + drift-guard) → `VERDICT: PASS` → PR (Refs-only)
