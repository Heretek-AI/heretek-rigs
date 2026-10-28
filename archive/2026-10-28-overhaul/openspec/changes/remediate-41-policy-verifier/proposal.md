# Proposal: remediate-41-policy-verifier — minimal policy-text verifier

## Status
Spec-only proposal (no implementation). Addresses heretek-rigs issue #41
("Policy-as-text defects hide until enforcement"). All premises verified
read-only before authoring; no code touched. This is HANDOFF.md option (c):
one minimal verifier covering BOTH lint-table-names-vs-toolchain AND
workflow-`run:`-vs-package-scripts (options (a)+(b) unified, minimal
scope — no general policy engine).

## Motivation
Policy authored as text (lint tables, workflow commands, config) is never
validated at authoring time, so defects hide until the enforcing gate first
runs — possibly waves later. Two live instances:

- **Lint-table name (W1-03 → W3-06).** W1-03 authored
  `cast_lossy = "deny"` in the workspace lints table. No such lint exists
  on the toolchain (correct name: `cast_possible_truncation`). Undetected
  through Waves 1+2 because no crate opted into the table. First
  `cargo clippy --all-targets -- -D warnings` with the W3-06 opt-in failed
  with `unknown lint: clippy::cast_lossy` — a policy-text bug, not a code
  bug. Still live at
  `src/w3-06-staging/root-lints-reference.toml:28` (`cast_lossy = "deny"`)
  vs the corrected live `Cargo.toml:38`
  (`cast_possible_truncation = "deny"`). Fixed by rename; clippy exit 0.
- **Workflow `run:` lines (W2-07).** Same class as #40: text nothing
  executes is text nothing checks. The reconciled workflow
  `pipelines/w2-07-ci-reconciled.yml` carries the proven-shape steps that
  a verifier must resolve: `:134-138` (`pnpm lint`, `pnpm format:check`,
  `pnpm typecheck` via turbo) and `:174` (`pnpm unit`, vitest suite).

## Boundaries
- Touch ONLY (at implementation time): a new policy-text verifier script,
  one `make` target, one additive `verify-rigs.sh` gate block.
- Covers exactly two policy-text classes (lint-table names, workflow
  `run:` resolution). NOT a general config validator, NOT a schema
  language, NOT clippy/rustc reimplementation.
- No changes to `fleet/`, `specs/`, `rigs/`, `rosters/`, `registry/`; no
  renumbering/rewording of the existing 22 `verify-rigs.sh` checks.

## Non-goals
- Validating lint *levels/priorities* (only name existence is checked).
- Checking `run:` shell semantics beyond script/subcommand resolution.
- Rewriting history: the stale `root-lints-reference.toml:28` line is a
  reference fixture, not a live manifest — the verifier MUST flag it as
  unknown-lint when scanned, which is the regression proof.

## Acceptance (see tasks.md)
Re-authoring the W1-03 table with a renamed lint (`cast_lossy`) fails at
QA/stage time with `unknown lint` named, not at first clippy enforcement;
and every reconciled `run:` step (`:134-138`, `:174`) resolves against
staged package scripts / toolchain subcommands.
