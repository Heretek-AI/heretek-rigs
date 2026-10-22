# Tasks: remediate-39-reconcile

Execution waves: implement (T1–T3) → replay (T4) → acceptance (T5) →
evidence (QA) → audit (drift-guard). Map 1:1 to
`specs/tracker-reconcile/spec.md`. Specs ONLY — do NOT implement in this
change.

- [ ] T1 — REQ-R1: implement tracker-table parsing + queue-state
      comparison for `docs/sprints/wave*-dispatch-tracker.md` (and the
      phase-0 tracker). Testable: on the pre-convergence Wave-1 state
      (7 drifted rows per the issue evidence) the command reports ≥7
      diffs naming file + row + both values.
- [ ] T2 — REQ-R2: emit exact proposed row updates (replacement Status
      cell + queue-note append) with strictly no file mutation.
      Testable: run is read-only (`git status` clean afterwards) and each
      proposal contains paste-ready replacement text.
- [ ] T3 — REQ-R4: fail-closed parsing (unreadable tracker, unparseable
      row, missing qitem, unreachable queue → named non-zero failure;
      never silent row-drops). Testable: each sabotage produces a named
      diagnostic, never a false "in sync".
- [ ] T4 — Replay proof: apply the T2 proposals for the 7 Wave-1 rows
      (in a scratch copy, TPM-approval simulation) and re-run →
      zero diffs, exit 0 with "in sync" summary (REQ-R3).
- [ ] T5 — Acceptance: wire a `make` target (e.g. `make reconcile
      TRACKER=...`) usable as a pre-handoff gate; record outputs.
- [ ] T6 — Report: write
      `docs/reports/remediate-39-reconcile-implementation.md`
      (files changed, verification outputs) and file the deferred
      `remediate-39-generate` follow-up design sketch as an issue, not
      code.
