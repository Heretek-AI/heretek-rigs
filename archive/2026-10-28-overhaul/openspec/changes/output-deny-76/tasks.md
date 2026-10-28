# Tasks: output-deny-76

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/output-deny-76/{proposal.md,design.md,tasks.md,specs/deny-narrowing/spec.md}` exit 0.
- [ ] T1 — Implement (agency-programmer, isolated branch/worktree `.lane/trees/output-deny-76` from clean `main`).
      Do: REQ-O1/O2 tuple edit (position 1, 38→42) + REQ-O4 lockstep (mirror, asserts, V15 exception scope, both corpora, gate-role probes, full regen, docs refresh).
      Testable: `make verify` green, no renumber.
      Acceptance command: `make verify`
- [ ] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: REQ-O3 allows + all deny forms both directions; evidence `docs/evidence/wave-e-output-deny.md`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only` AND `pytest tests/test_render_seat.py tests/test_command_effects.py`
- [ ] T3 — Drift-guard (VERDICT from disk) → PR with `Closes #76`.
