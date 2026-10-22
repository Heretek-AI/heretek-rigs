# Proposal: remediate-40-manifest-closure — stage-time manifest-closure lint

## Status
Spec-only proposal (no implementation). Addresses heretek-rigs issue #40
("Scaffold slices reference undeclared binaries; need a manifest-closure
check"). All premises verified read-only before authoring; no code touched.

## Motivation
Wave-1 scaffold slices staged manifests whose scripts referenced binaries no
manifest declares. Each failure surfaced only when the operator ran the gate
— authoring seats cannot execute builds (heretek-rigs #12), so authoring
seats never see the breakage. Four instances of one defect class, all fixed
during Asset-Manager W2-02..W2-04 (operator-runner logs, 2026-10-22):

1. `e2e` tsconfig lists `types: node`, but no `@types/node` in e2e devDeps
   (TS2688). Fixed: `@types/node 22.10.0` declared in `e2e/package.json:14`.
2. `apps/web` uses React 19 JSX with no `@types/react(+dom)` (TS7016/7026);
   an earlier typecheck pass was transient-layout luck — undeclared deps
   resolving by accident. Fixed: `@types/react 19.0.0` (+ `-dom`) declared
   in `apps/web/package.json:21-22`.
3. `apps/web`+`tests`+`e2e` scripts invoke `eslint`/`prettier`, declared
   nowhere; runs leaked via GLOBAL eslint 10.11.0 and failed on the
   `typescript-eslint` import. Fixed: `eslint 9.39.5` +
   `typescript-eslint 8.72.0` + `prettier 3.9.10` declared per package
   (root `package.json:22-25`, mirrored in `apps/web` and `e2e`).
4. `apps/web` `unit` script invokes `vitest`, undeclared (command not
   found). Fixed: `vitest 3.0.0` declared in `apps/web/package.json:29`.

No closure check exists in `heretek-rigs/scripts/` today (verified: zero
matches for `closure`/`undeclared` in `scripts/` and `Makefile`).

## Boundaries
- Touch ONLY (at implementation time): a new `scripts/manifest-closure.*`
  check, one new `Makefile` target, one additive `verify-rigs.sh` gate block.
- No changes to `fleet/`, `specs/`, `rigs/`, `rosters/`, `registry/`
  (no regen required, no digest impact).
- No renumbering/rewording of the existing 22 `verify-rigs.sh` checks
  (audit-baselined per AGENTS.md — the new gate is appended alongside).

## Non-goals
- Full type-resolution checking (instance #2's ambient-JSX class): that
  remains the `tsc` typecheck gate's job. This lint covers script-invoked
  binaries and explicit tsconfig `types` references; §Instance-2 limitation
  is documented in `design.md`, not silently claimed.
- Network installs or lockfile verification (`--frozen-lockfile` behavior
  is the operator-runner's job); the lint is parse-only and offline.
- Operator-runner pre-flight (#40 option (c)) and QA-checklist-only
  (option (b)) fallbacks — this proposal is option (a), stage-time lint.

## Acceptance (see tasks.md)
Re-running the Wave-2 gate sequence on a fresh checkout with the four fixed
pins in place produces zero undeclared-binary failures, and re-introducing
any one of the four original omissions fails the lint at stage time (before
QA handoff), with the offending binary named in the output.
