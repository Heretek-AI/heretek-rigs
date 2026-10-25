# Tasks: provisioning-gate-74

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/provisioning-gate-74/{proposal.md,design.md,tasks.md,specs/provisioning-gate/spec.md}` exit 0.
- [ ] T1 — Implement (agency-programmer, isolated branch/worktree `.lane/trees/provisioning-gate-74` from clean `main`).
      Do: REQ-P1 render resolution + REQ-P2 seed resolution (read-only: `shutil.which`/path-exists, no installs/pulls); REQ-P3 appended verify block + live-health WARN-first sub-check; REQ-P4 full 20+B3 coverage; matrix doc/table on disk.
      Testable: `make verify` green, no renumber.
      Acceptance command: `make verify`
- [ ] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: missing binary → `enabled:false` + named warn (render + seed); present → enabled; verify block both directions; evidence `docs/evidence/wave-c-provisioning-gate.md`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only` AND `pytest tests/test_policy_verifier.py tests/test_render_seat.py`
- [ ] T3 — Drift-guard (VERDICT from disk) → PR with `Refs #74` (never `Closes #74`). #74 stays OPEN.
