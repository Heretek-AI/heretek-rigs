# Tasks: 102-closeout

- [x] T0 — Spec gate (this change). Testable: `ls openspec/changes/102-closeout/{proposal.md,design.md,tasks.md,specs/closeout/spec.md}` exit 0.
      Acceptance command: `ls openspec/changes/102-closeout/proposal.md openspec/changes/102-closeout/design.md openspec/changes/102-closeout/tasks.md openspec/changes/102-closeout/specs/closeout/spec.md`

- [x] M1 — HR-F18 deny (agency-programmer, worktree `.lane/trees/102-closeout`).
      Do: `fleet/fleet.yaml` deny bare `queue list|create` (no `--json --verify`) + bare `send`; `AGENTS.md` one-liner; regen; appended verify block.
      Testable: bare denies, `--json --verify` allows; `make verify` green.
      Acceptance command: `make verify`

- [x] M2 — HR-2.5 docs. Do: canonical statement (spec-validate for all-51, bundle-8-intentional).
      Testable: `rig spec validate` covers `rig.all-51.yaml` per V18; docs grep hits.
      Acceptance command: `./scripts/verify-rigs.sh --check-only`

- [x] M3 — writing-skills patch + regen. Do: `fleet/skill-patches/` entry + regen.
      Testable: `grep -rn 'superpowers:writing-skills' specs/ fleet/` returns 0; loader 68/68 no DIAG.
      Acceptance command: `make verify`

- [x] M4 — DAG local note. Do: `docs/evidence/102-closeout-dag.md`.
      Testable: evidence file exists, cites `verify-rigs.sh:896`.
      Acceptance command: `ls docs/evidence/102-closeout-dag.md`

- [x] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: every new deny/fix fails loudly + restores green; evidence `docs/evidence/102-closeout-m1.md` + `red-proofs.log`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only AND grep -rn 'superpowers:writing-skills' specs/ fleet/ (expect 0)`

- [x] T3 — Drift-guard (VERDICT from disk) → PR (Refs #102; Closes #102 only if M1–M4 fully fixed).
