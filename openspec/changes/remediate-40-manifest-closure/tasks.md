# Tasks: remediate-40-manifest-closure

Execution waves: implement (T1–T3) → regression (T4) → acceptance (T5) →
evidence (QA) → audit (drift-guard). Map 1:1 to
`specs/manifest-closure/spec.md`. Specs ONLY — do NOT implement in this
change.

- [ ] T1 — REQ-C1/C2: implement the parse-and-resolve check over staged
      `package.json` scripts, workflow `run:` steps, and `pnpm` script
      indirection. Testable: on the four fixed pins (root `eslint 9.39.5`
      + `typescript-eslint 8.72.0` + `prettier 3.9.10`,
      `apps/web` `vitest 3.0.0` + `@types/react 19.0.0`,
      `e2e` `@types/node 22.10.0`) the check exits 0.
- [ ] T2 — REQ-C3: add the checked-in operator-runner tool allowlist;
      verify offline operation (no network) and fail-closed behavior on an
      unreadable manifest. Testable: `GLOBAL eslint`-style leak (binary on
      PATH, declared nowhere) still exits non-zero naming the binary.
- [ ] T3 — REQ-C4: wire a `make` target + additive `verify-rigs.sh` gate
      block without renumbering/rewording the existing 22 checks.
      Testable: `make verify` shows existing checks unchanged plus one new
      named check, all passing.
- [ ] T4 — Red-proof regression per instance: remove each of the four
      fixed declarations in turn (`@types/node`, `@types/react`,
      `eslint`/`prettier`, `vitest`) and confirm the lint fails naming
      the omitted binary/package; restore and confirm exit 0. Instance #2
      omission is expected to PASS the lint (documented limitation) and
      MUST instead fail the `tsc` typecheck gate — record both outcomes.
- [ ] T5 — Acceptance: re-run the Wave-2 gate sequence on a fresh
      checkout → zero undeclared-binary failures; record outputs.
- [ ] T6 — Report: write
      `docs/reports/remediate-40-manifest-closure-implementation.md`
      (files changed, verification outputs).
