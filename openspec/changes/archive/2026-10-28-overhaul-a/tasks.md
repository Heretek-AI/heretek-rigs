# Tasks: overhaul-a

- [x] T0 — Spec gate (this change). Testable: `ls openspec/changes/overhaul-a/{proposal.md,design.md,tasks.md,specs/p0/spec.md}` exit 0.
      Acceptance command: `ls openspec/changes/overhaul-a/proposal.md openspec/changes/overhaul-a/design.md openspec/changes/overhaul-a/tasks.md openspec/changes/overhaul-a/specs/p0/spec.md`

- [x] M0 — Spike (agency-programmer, worktree `.lane/trees/overhaul-a`, scratch probes ONLY).
      Do: fake-rig exfiltration probe vs current relay bounds + `filter=` capability probe; write `docs/evidence/overhaul-a-m0.md` verbatim.
      Testable: evidence log exists with both probe outputs on the unmodified tree.
      Acceptance command: `ls docs/evidence/overhaul-a-m0.md`

- [x] M1 — Relay hardening. Do: re-derived relay + `TestRigRelayEnforcement` (bwrap-independent).
      Testable: 7 relay cases (6 deny + 1 allow); `make verify` green.
      Acceptance command: `python3 -m unittest tests.test_seat_sandbox -v`

- [x] M2 — Hermetic regen. Do: filter guard + charter fallback + snapshot/restore guard.
      Testable: hermetic `--check-idempotent` passes with nonexistent crew/vendor dirs.
      Acceptance command: `python3 ./scripts/generate-rigs.py --check-idempotent --crew-source /nonexistent/crew --vendor-dir /nonexistent/vendor`

- [x] M3 — Docker pipeline. Do: Dockerfile bubblewrap + workflow syntax/dup-key fix + verify-fleet bubblewrap install.
      Testable: UniqueKey YAML parse passes; bubblewrap greppable in both files.
      Acceptance command: `rg -n "bubblewrap" docker/Dockerfile .github/workflows/docker-release.yml`

- [x] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: sabotage relay (allow forged source / secret body-file) + filter guard + workflow (reintroduce dup key) — each must RED, restore GREEN.
      Evidence: `docs/evidence/overhaul-a/red-proofs.log`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test`

- [x] T3 — Drift-guard (VERDICT from disk) → PR (Refs only; no Closes).
