# Tasks: path-arg-grants-91

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/path-arg-grants-91/{proposal.md,design.md,tasks.md,specs/scoped-args/spec.md}` exit 0.
- [ ] T1 — Implement (agency-programmer, isolated branch/worktree `.lane/trees/path-arg-grants-91` from clean `main`).
      Do: M0 live probe FIRST (outcome in evidence, implementation follows winner; halt-with-replan if neither); then REQ-A1/A2/A3/A4 + regen.
      Testable: `make verify` green.
      Acceptance command: `make verify`
- [ ] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: four verbatim commands allow on scoped roles; all deny forms deny; evidence `docs/evidence/wave-f-path-arg-grants.md`. Live seat proof recorded UNVERIFIED until post-merge (no live fleet here).
      Acceptance command: `./scripts/verify-rigs.sh --check-only` AND `pytest tests/test_command_effects.py`
- [ ] T3 — Drift-guard (VERDICT from disk) → PR (Refs #91; Closes only after post-merge live proof).
