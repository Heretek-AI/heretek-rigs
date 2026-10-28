# Tasks: remediate-41-policy-verifier

Execution waves: implement (T1–T3) → regression (T4) → acceptance (T5) →
evidence (QA) → audit (drift-guard). Map 1:1 to
`specs/policy-verifier/spec.md`. Specs ONLY — do NOT implement in this
change.

- [ ] T1 — REQ-P1: implement lint-table name resolution (staged TOML
      `[workspace.lints.*]`/`[lints.*]` vs toolchain list with checked-in
      snapshot fallback + stale-snapshot-pin failure). Testable: scanning
      `src/w3-06-staging/root-lints-reference.toml` fails naming
      `clippy::cast_lossy` at `:28`; scanning live `Cargo.toml` passes.
- [ ] T2 — REQ-P2: implement workflow `run:` resolution (package-script
      names vs staged manifests; `cargo` subcommands). Testable: the
      reconciled steps `:134-138` (`pnpm lint`, `format:check`,
      `typecheck`) and `:174` (`pnpm unit`) resolve clean; a renamed
      script reference fails naming file:line.
- [ ] T3 — REQ-P3/P4: single-command wiring (`make` target + additive
      `verify-rigs.sh` block; no renumbering of the 22 checks;
      offline; no auto-fix). Testable: `make verify` keeps existing
      checks unchanged plus one new named check, all passing.
- [ ] T4 — Red-proof regression: re-author the W1-03 table with
      `cast_lossy` and confirm failure at stage time (before any clippy
      run); rename to `cast_possible_truncation` and confirm pass with
      clippy still exit 0. Record both outcomes for QA sabotage review.
- [ ] T5 — Acceptance: full verifier run over the staged Wave-3 policy
      set → exit 0 with the corrected pins; record outputs.
- [ ] T6 — Report: write
      `docs/reports/remediate-41-policy-verifier-implementation.md`
      (files changed, verification outputs).
