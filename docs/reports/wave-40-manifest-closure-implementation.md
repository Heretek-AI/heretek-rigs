# Implementation report — wave-40-manifest-closure (issue #40)

Stage: `wave-40-manifest-closure` · Branch: `remediate/40-manifest-closure`
Change id: `remediate-40-manifest-closure` · Date: 2026-10-22 (UTC)

## What was built

Stage-time manifest-closure lint: every binary invoked by a staged
`package.json` script or staged pipeline/workflow `run:` step must resolve to
a declared dependency (own or workspace-root manifest, own `bin` entries, or
a grounded binary→package alias), or to the checked-in operator-runner tool
allowlist. Staged `tsconfig*.json` `types` entries must resolve to declared
`@types/<name>` packages or to declared packages shipping their own types.
Anything else fails closed, naming the binary, the invoking script/step, and
the package. `PATH` is never consulted; no network; no `node_modules` probing.

## Deliverables (files changed)

- `scripts/manifest-closure.py` (new, executable, shebang) — the lint.
  REQ-C1 entry-point collection (quote-aware `&&`/`;`/`|` segmentation,
  env-assignment/redirection/fd skipping, `${{ }}` skipping,
  `pnpm|npm|yarn|npx <script>` recursion into every defining package with
  cycle detection + depth cap, `cargo <sub>` → toolchain cargo, `pnpm dlx` /
  `npx <pkg>` one-shots always undeclared); REQ-C2 resolution incl.
  `BIN_ALIASES = {tsc: typescript, playwright: @playwright/test}` grounded
  read-only in the live fixed state; REQ-C5 `types` resolution with
  relative-`extends` following; REQ-C3/REQ-C4 `--staged` (git-index blobs)
  and default tree-walk modes, exit 0/1/2.
- `fleet/allowed-system-tools.txt` (new) — checked-in allowlist:
  `node npm pnpm yarn git cargo echo rig`, each grounded in a header comment
  against the live fixed state. Missing/empty file fails the lint (exit 2).
- `Makefile` — one additive `manifest-closure` target (`python3
  ./scripts/manifest-closure.py --staged`) + one `.PHONY` token. No existing
  target touched.
- `scripts/verify-rigs.sh` — one additive `== V8. Manifest-Closure Lint ==`
  block before `SUMMARY`: runs `tests/test_manifest_closure.py` plus a live
  `--staged` pass, exactly one new `ok()`. No existing check renumbered or
  reworded (byte-identical names/numbers).
- `tests/test_manifest_closure.py` (new) — 17 tests, all synthetic fixtures
  in `/tmp`, never the mission repo or this repo's live files.

## Verification (exact commands, worktree root, exit codes)

- `python3 -m unittest tests/test_manifest_closure.py` → `Ran 17 tests / OK`,
  exit 0. Covers: fixed pins pass; each omission of `@types/node`,
  `eslint`, `prettier`, `vitest`, `typescript` fails naming the binary/package;
  GLOBAL-leak binary on `PATH` still fails; unreadable (dir-as-manifest) and
  corrupt manifests fail naming the file; instance #2 (`@types/react`
  omitted) passes the lint; pnpm indirection recurses and cycles fail;
  `npx serve` / `pnpm dlx cowsay` one-shots fail naming the package;
  allowlisted `git`/`echo` pass, unknown binary fails, missing allowlist
  fails; workflow `run:` collected while `uses:` ignored; `--staged` reads
  index blobs (breaking the worktree while the index is clean stays green);
  quoted-`;`/`2>&1` shapes don't false-positive; checked-in allowlist covers
  `node/npm/git/rig`.
- T4 red-proofs on `/tmp/t4demo` fixtures (built from the fixed pins):
  `fixed` → exit 0; `omit-types-node` → exit 1 naming `@types/node`;
  `omit-eslint` → exit 1 naming `eslint`; `omit-prettier` → exit 1 naming
  `prettier`; `omit-vitest` → exit 1 naming `vitest`; `omit-types-react` →
  exit 0 (documented limitation).
- Instance #2 covering-gate proof (`/tmp/t4-react`, JSX + `react-jsx`,
  no `@types/react`): `tsc --noEmit` → exit 1 with `TS7026` +
  `TS2875` (the issue's TS7016/7026 class). tsc remains the covering gate.
- T5 Wave-2 gate re-run, read-only, 7 live mission files (root + apps/web +
  tests + e2e `package.json`, web + e2e `tsconfig.json`, `ci.yml`):
  `manifest-closure: 42 entry point(s) checked; zero undeclared.`, exit 0.
  During T5 the lint caught a real tokenizer bug (naive split on the quoted
  `;` in the workflow's `echo "lock round-trips; ..."` flagged `harness`);
  fixed with quote-aware segmentation plus a regression test.
- `bash ./scripts/verify-rigs.sh --check-only` →
  `SUMMARY: 24 checks passed, 0 failed.`, exit 0.
- `make verify` → exit 0 (verify-rigs.sh 24/0 + `live-health.py` advisory
  heartbeat WARNs, same advisories as baseline).
- `make test` → `Ran 59 tests / OK`, exit 0.
- `openspec validate remediate-40-manifest-closure` → valid, exit 0.
- `make manifest-closure` (empty stage) → `no staged manifests`, exit 0.
- Stub scan over new/changed files: no TODO/FIXME/stubs/skips (only hit is
  the pre-existing Makefile `|| true` on the `rig` probe line).

## No-live-mutation record

The mission repo (`/home/john/Projects/heretek-asset-manager`, zero commits)
was only read (`package.json` × 4 probed, `tsconfig` × 2, `ci.yml` × 1, all
grounding the four fixed pins). Nothing was written outside this worktree.
All fixtures synthetic under `/tmp` (`/tmp/t4demo`, `/tmp/t4-react`,
per-test `tempfile` trees) or in-worktree test code. Untracked strays from
prior sessions left alone per AGENTS.md.

## Self-audit notes / deviations stated plainly

- Count note: the brief's acceptance line says `SUMMARY 23 passed / 0
  failed`, but tasks.md T3 ("plus one new named check, all passing") and
  REQ-C4 require the additive gate, so the worktree reports **24/0** with
  all 23 pre-existing checks byte-identical (verified by diff: only the V8
  block + 5 Makefile lines added). The "23" is read as the no-regression
  baseline, which holds.
- Report filename: tasks.md T6 names
  `docs/reports/remediate-40-manifest-closure-implementation.md`; this file
  is written at the stage-id path the work order mandates
  (`docs/reports/wave-40-manifest-closure-implementation.md`).
- `npx` bare (no args) and `pnpm exec <bin>` resolve conservatively
  (builtin/script rules above); bare-package `extends` in tsconfig stays with
  the tsc gate per design.md; a segment whose binary is a `$VAR` is skipped
  (unknowable offline) — recorded boundaries, not silent holes.
- `--staged` `extends` follows the worktree file, not the blob (index-only
  renames of a base config are vanishingly rare; the staged leaf's own
  `types` are always read from the blob).
- Not done (out of scope per spec non-goals): lockfile/`--frozen-lockfile`
  verification, network installs, full type-resolution, Go/Rust manifest
  shapes. No QA dispatch, no merge, no push — as ordered.
