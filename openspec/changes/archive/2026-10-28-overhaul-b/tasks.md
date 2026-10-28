# Tasks: overhaul-b

- [x] T0 — Spec gate (this change). Testable: `ls openspec/changes/overhaul-b/{proposal.md,design.md,tasks.md,specs/contracts/spec.md}` exit 0.
      Acceptance command: `ls openspec/changes/overhaul-b/proposal.md openspec/changes/overhaul-b/design.md openspec/changes/overhaul-b/tasks.md openspec/changes/overhaul-b/specs/contracts/spec.md`

- [x] M4 — Contract sync + regen (agency-programmer, worktree `.lane/trees/overhaul-b`).
      Do: `codex_permissions` in pinned keys + verify gate; vendor run-record + pin + contract coverage; skill sync via generator; clean-tree regen (sources commit → regen → chore leaves commit by coordinator).
      Testable: contract suite + regen + idempotence green, digests self-consistent.
      Acceptance command: `python3 -m unittest tests.test_schema_contracts -v && python3 ./scripts/generate-rigs.py --check-idempotent`

- [x] M5 — Test wiring + canary + V19.
      Do: discover-based `make test`; canary expected-set update + fixture fallback; V19 canonical total; V12 note-mode.
      Testable: all suites run 0 failures; canary green with and without a33f3bb; no V19 cascade on injected early failure.
      Acceptance command: `make test`

- [x] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: sabotage contract pin (drop codex_permissions), canary fixture (corrupt), V19 (restore passes+1) — each must RED, restore GREEN.
      Evidence: `docs/evidence/overhaul-b/red-proofs.log`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test`

- [x] T3 — Drift-guard (VERDICT from disk) → PR (Refs only; no Closes).
