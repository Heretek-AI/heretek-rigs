# Tasks: overhaul-c

- [x] T0 — Spec gate (this change). Testable: `ls openspec/changes/overhaul-c/{proposal.md,design.md,tasks.md,specs/archive/spec.md}` exit 0.
      Acceptance command: `ls openspec/changes/overhaul-c/proposal.md openspec/changes/overhaul-c/design.md openspec/changes/overhaul-c/tasks.md openspec/changes/overhaul-c/specs/archive/spec.md`

- [x] M6 — Archive moves (agency-programmer, worktree `.lane/trees/overhaul-c`).
      Do: enumerate live, `git mv` stale → `archive/2026-10-28-overhaul/`; update HR-8.4 list + maps + `.gitignore`; keep-list byte-identical; history follows.
      Testable: `test ! -e` every stale path; keep-list identical; `git log --follow` works.
      Acceptance command: `git status --short && ls archive/2026-10-28-overhaul/ | head`

- [x] M7 — Audit prompt placement.
      Do: fresh `docs/IMPLEMENTATION_PROMPT.md`; repoint audit_loop const/help/exec/message; self-test green.
      Testable: self-test PASSED referencing new path; no live reads of archived paths.
      Acceptance command: `python3 scripts/audit_loop.py --self-test`

- [x] M8 — Regen + full gates.
      Do: (coordinator commits sources) clean regen (leaves commit) + idempotence + verify + make test + topology.
      Testable: all five exit 0; regen no-op beyond provenance.
      Acceptance command: `python3 ./scripts/generate-rigs.py --check-idempotent && bash ./scripts/verify-rigs.sh --check-only && make test`

- [x] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: sabotage move-exclusion (touch a keep-list file into the move set) + prompt path (point const at archived file) + HR-8.4 (re-add a moved filename) — each must RED, restore GREEN.
      Evidence: `docs/evidence/overhaul-c/red-proofs.log`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test`

- [x] T3 — Drift-guard (VERDICT from disk) → PR (Refs only; no Closes).
