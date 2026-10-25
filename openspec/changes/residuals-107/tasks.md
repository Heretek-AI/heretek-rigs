# Tasks: residuals-107

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/residuals-107/{proposal.md,design.md,tasks.md,specs/residuals/spec.md}` exit 0.
- [ ] T1 — Implement (agency-programmer, isolated branch/worktree `.lane/trees/residuals-107` from clean `main`).
      Do: REQ-R1 V13 pattern extend; REQ-R2 three count refreshes; REQ-R3 pin refresh. Nothing else (REQ-G1/G2 enforced).
      Testable: `verify-rigs.sh --check-only` green; greps in proposal Acceptance 2–3 hold.
      Acceptance command: `make verify`
- [ ] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: sabotage V13 arm off → fixture with `toomanyrequests` REDs (fail-closed); arm on → SKIP. Corpus + evidence `docs/evidence/wave-b2-residuals.md`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only` AND `pytest tests/test_policy_verifier.py tests/test_render_seat.py`
- [ ] T3 — Drift-guard (VERDICT from disk) → PR with B1 evidence + B2 changes. Note: B1 spec+evidence (`ops-sweep-111/`, `wave-b1-seatjail-sweep.md`) ride this PR's branch (host sweep already done).
