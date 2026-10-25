# Tasks: checker-batch-d

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/checker-batch-d/{proposal.md,design.md,tasks.md,specs/checkers/spec.md}` exit 0.
- [ ] T1 — Implement (agency-programmer, isolated branch/worktree `.lane/trees/checker-batch-d` from clean `main`).
      Do: REQ-D94/D95/D98/D101 code + corpus; REQ-D102 guard + drift corrections; respect REQ-G1 (append-only, generator rule).
      Testable: `make verify` green.
      Acceptance command: `make verify`
- [ ] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: every new form fails loudly + restores green; evidence `docs/evidence/wave-d-checker-batch.md`. Note canary 12/11 pre-existing if unchanged.
      Acceptance command: `./scripts/verify-rigs.sh --check-only` AND `pytest tests/test_manifest_closure.py tests/test_policy_verifier.py`
- [ ] T3 — Drift-guard (VERDICT from disk) → PR (Refs; Closes only issues fully fixed: #94 #95 #98 #101 + #102-guard portion; #96 untouched).
