# Tasks: overhaul-bump

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/overhaul-bump/{proposal.md,design.md,tasks.md,specs/bump/spec.md}` exit 0.
      Acceptance command: `ls openspec/changes/overhaul-bump/proposal.md openspec/changes/overhaul-bump/design.md openspec/changes/overhaul-bump/tasks.md openspec/changes/overhaul-bump/specs/bump/spec.md`

- [ ] M1 — Bump + ledger (agency-programmer, worktree `.lane/trees/overhaul-bump`).
      Do: `npm install -g @openrig/cli@0.7.4`; ledger `docs/sprints/CLI-0.7.4-BUMP.md`; update true 0.7.2 version pins only; regen only if generator inputs changed.
      Testable: `rig --version` → `0.7.4`; ledger contains version + tarball SHA + green verify output.
      Acceptance command: `rig --version && ./scripts/verify-rigs.sh --check-only`

- [ ] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: prove ledger claims (version string, SHA presence); sabotage one updated pin back to 0.7.2 and prove a gate/ledger check trips; restore.
      Evidence: `docs/evidence/overhaul-bump/red-proofs.log`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test`

- [ ] T3 — Drift-guard (VERDICT from disk) → PR (Refs only; no Closes).
