# Tasks: 2026-10-29-bump-075

- [x] T0 — Spec gate (this change). Testable: `ls openspec/changes/2026-10-29-bump-075/{proposal.md,design.md,tasks.md,specs/bump/spec.md}` exit 0.
      Acceptance command: `ls openspec/changes/2026-10-29-bump-075/proposal.md openspec/changes/2026-10-29-bump-075/design.md openspec/changes/2026-10-29-bump-075/tasks.md openspec/changes/2026-10-29-bump-075/specs/bump/spec.md`

- [x] M1 — Bump + ledger (agency-programmer, worktree `.lane/trees/bump-075`).
      Do: `npm install -g @openrig/cli@0.7.5`; ledger `docs/sprints/CLI-0.7.5-BUMP.md` (version, two-fetch tarball SHA, 8 true-pin files, tarball-diff disposition, verify output); update true 0.7.4 version pins only (AGENTS.md surgical, diff-stat ≤15 lines); regen only if generator inputs changed (they did not — no regen).
      Testable: `rig --version` → `0.7.5`; ledger contains version + tarball SHA + green verify output.
      Acceptance command: `rig --version && ./scripts/verify-rigs.sh --check-only`

- [x] T2 — Red-proofs (agency-qa, same worktree, evidence in the implementation report).
      Do: prove ledger claims (version string, SHA presence); sabotage the V18 expected-version pin back to `0.7.4` and prove the gate trips RED (38/1); restore `0.7.5` and prove GREEN (39/0).
      Evidence: `docs/reports/bump-075-implementation.md` (red-proof § with commands + outputs).
      Acceptance command: `./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test`

- [x] T3 — Drift-guard (VERDICT from disk) → PR (Refs only; no Closes).
