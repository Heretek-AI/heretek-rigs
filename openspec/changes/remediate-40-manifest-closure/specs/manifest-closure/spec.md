# Delta spec: manifest-closure lint

## ADDED Requirements

### Requirement: REQ-C1 — Parse every staged script entry point
The check MUST collect, from every staged `package.json`, all `scripts`
values, and from every staged pipeline/workflow YAML, all `run:` step
bodies. For each, the invoked binary MUST be defined as the first
whitespace-delimited token after stripping package-manager prefixes
(`pnpm|npm|yarn|npx <script>` resolves to the named script, whose own body
is then parsed recursively; `cargo <subcommand>` resolves per REQ-C2c).

#### Scenario: Full Wave-2 script surface is collected
- Given the four fixed manifests (root, `apps/web`, `e2e`) plus the
  reconciled workflow staged,
- When the check enumerates entry points,
- Then `eslint`, `prettier`, `vitest`, `tsc`, and the `pnpm lint /
  format:check / typecheck / unit` indirections are all in the collected
  set (none silently skipped).

### Requirement: REQ-C2 — Every invoked binary MUST resolve to a declared dependency
Each binary extracted under REQ-C1 MUST resolve to at least one of:

- (a) a `devDependencies` (or `dependencies`) entry of the same package
      whose binary name matches (including the package's own `bin`
      entries); or
- (b) a `devDependencies` entry of the workspace root `package.json`; or
- (c) for `cargo` invocations, a toolchain-provided subcommand or an entry
      in the explicit operator-runner-provided tool allowlist (see REQ-C3);
- (d) an entry in a checked-in explicit tool allowlist for binaries the
      operator-runner guarantees (e.g. `git`, `node`, `cargo` itself).

Any binary resolving to none of (a)–(d) MUST be reported as undeclared.

#### Scenario: Four Wave-2 regression fixtures resolve clean
- Given the fixed pins (root `eslint 9.39.5`, `prettier 3.9.10`,
  `typescript-eslint 8.72.0`; `apps/web` `vitest 3.0.0`,
  `@types/react 19.0.0`; `e2e` `@types/node 22.10.0`),
- When the check runs,
- Then it exits 0 with zero undeclared binaries.

#### Scenario: Each original omission fails named
- Given any one of the four declarations removed (undeclared `vitest`,
  undeclared `eslint`/`prettier`, undeclared `@types/node` with a
  `types: node` entry),
- When the check runs,
- Then it exits non-zero naming the undeclared binary/package, the
  invoking script or `run:` step, and the package it was found in.

### Requirement: REQ-C3 — Explicit allowlist, fail-closed, offline
The operator-runner-provided tool allowlist MUST be a checked-in file
(e.g. `fleet/allowed-system-tools.txt` or equivalent named at
implementation time), NOT tribal knowledge. The check MUST run without
network access (parse `package.json` + configs vs declared deps only) and
MUST fail closed: exit non-zero naming each undeclared binary, the script
or `run:` step that invokes it, and the package it was found in. An
unreadable manifest MUST fail the check, never be skipped silently.

#### Scenario: Global-leak binary still fails
- Given a binary resolvable on `PATH` (cf. GLOBAL eslint 10.11.0) but
  matching none of REQ-C2a–d,
- When the check runs,
- Then it exits non-zero naming the binary (PATH resolution MUST NOT
  count as declared).

#### Scenario: Unreadable manifest fails closed
- Given a staged but unreadable `package.json`,
- When the check runs,
- Then it exits non-zero naming the file (never skip-silent).

### Requirement: REQ-C4 — Stage-time wiring
The check MUST be runnable as a single `make` target from the repo root and
MUST run before QA handoff for any staged scaffold slice (wired as an
additive gate alongside the existing `verify-rigs.sh` checks — existing
check numbering and wording MUST NOT change).

#### Scenario: Additive gate, existing checks untouched
- Given the wired gate,
- When `make verify` runs on the current tree,
- Then all pre-existing checks pass with unchanged names/numbers plus one
  new named manifest-closure check.

### Requirement: REQ-C5 — tsconfig `types` references MUST resolve
Every entry in a staged `tsconfig*.json` `types` array MUST resolve to a
declared `@types/<name>` package in that package's or the root manifest
(the `e2e` → `@types/node 22.10.0` instance). Ambient-JSX-style failures
(instance #2: React 19 JSX with no `@types/react`) are outside parse-only
reach and MUST remain covered by the `tsc` typecheck gate — the lint MUST
NOT claim to catch that class (see `design.md`).

#### Scenario: Explicit `types` entry without declared package fails
- Given a staged tsconfig with `types: ["node"]` and no `@types/node`
  declared in that package or root,
- When the check runs,
- Then it exits non-zero naming `@types/node` and the tsconfig file.
