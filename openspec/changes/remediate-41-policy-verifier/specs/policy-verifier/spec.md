# Delta spec: policy-text verifier (lint tables + workflow run: lines)

## ADDED Requirements

### Requirement: REQ-P1 — Lint-table names MUST exist on the toolchain
The verifier MUST parse every staged TOML file's `[workspace.lints.*]` and
`[lints.*]` tables (including `[workspace.lints.clippy]`). Each lint name
MUST exist in the toolchain's known-lint list, resolved in this order: (a)
the locally installed toolchain's lint enumeration (`rustc -W help` /
clippy lint list) when a toolchain is present; else (b) a checked-in
known-lint snapshot pinned to the repo's toolchain version. Any name
absent from the list MUST fail the check naming the file, line, and name.

#### Scenario: Stale `cast_lossy` reference fails at stage time
- Given `src/w3-06-staging/root-lints-reference.toml:28`
  (`cast_lossy = "deny"`) in the scanned set,
- When the verifier runs (before any clippy invocation),
- Then it exits non-zero with `unknown lint: clippy::cast_lossy` naming
  file and line.

#### Scenario: Corrected live table passes
- Given the live `Cargo.toml:38`
  (`cast_possible_truncation = "deny"`),
- When the verifier runs,
- Then that entry passes (no unknown-lint diagnostic for it).

### Requirement: REQ-P2 — Workflow `run:` lines MUST resolve to declared scripts
Every staged workflow/pipeline YAML `run:` step that invokes a package
script (`pnpm|npm|yarn <name>`) MUST resolve `<name>` to a `scripts` entry
in a staged `package.json` (same package or workspace root); every `cargo
<args>` step MUST start with a known cargo subcommand or a configured
alias. Unresolvable references MUST fail naming the file, line, and
command.

#### Scenario: Reconciled W2-07 steps resolve clean
- Given the staged manifests plus
  `pipelines/w2-07-ci-reconciled.yml:134-138` (`pnpm lint`,
  `pnpm format:check`, `pnpm typecheck`) and `:174` (`pnpm unit`),
- When the verifier runs,
- Then all four steps resolve with no diagnostic.

#### Scenario: Renamed script reference fails named
- Given a `run: pnpm <name>` step where `<name>` matches no staged
  `scripts` entry,
- When the verifier runs,
- Then it exits non-zero naming the file, line, and command.

### Requirement: REQ-P3 — One minimal command, stage-time, fail-closed
Both classes (REQ-P1 + REQ-P2) MUST be covered by a single verifier
invocation runnable as one `make` target at stage time (before QA
handoff). The verifier MUST be parse-only plus local-toolchain queries —
no network. Unreadable TOML/YAML, absent toolchain AND absent snapshot,
or any unknown name/reference MUST fail closed with a non-zero exit and
file:line diagnostics. The verifier MUST NOT auto-fix policy text.

#### Scenario: Unreadable policy file fails closed
- Given a staged but unparseable lint TOML or workflow YAML,
- When the verifier runs,
- Then it exits non-zero naming the file (never skip-silent, never
  auto-fix).

### Requirement: REQ-P4 — Additive gating only
The verifier MUST be wired as an additive gate alongside the existing
`verify-rigs.sh` checks — existing check numbering and wording MUST NOT
change, and no `fleet/`/`specs/`/`rigs/`/`rosters/`/`registry/` file may
be touched by the implementation.

#### Scenario: Additive gate, existing checks untouched
- Given the wired gate,
- When `make verify` runs on the current tree,
- Then all pre-existing checks pass with unchanged names/numbers plus one
  new named policy-verifier check.
