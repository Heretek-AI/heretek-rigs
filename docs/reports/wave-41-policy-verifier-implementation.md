# Implementation report — wave-41-policy-verifier

Stage: `wave-41-policy-verifier` · change-id `remediate-41-policy-verifier`
(issue #41, policy-as-text defects hide until enforcement).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-41-policy-verifier`
Branch: `remediate/41-policy-verifier`.

## Deliverables

One minimal policy-text verifier covering BOTH halves, per the change spec:

- `scripts/policy-verifier.py` (new, executable, stdlib-only + PyYAML for
  YAML validation — the same dependency `manifest-closure.py` already
  requires; offline/parse-only, no network, no `PATH`/toolchain probing,
  never edits policy files). Exit 0 = all resolve, 1 = finding/unreadable/
  stale, 2 = usage/env error.
  - (a) REQ-P1: scans `[workspace.lints.*]`/`[lints.*]` TOML entries with
    exact file:line diagnostics (line scan cross-checked against a
    `tomllib` parse, so comments/string literals can't false-fire) and
    resolves each name against the checked-in known-lint snapshot —
    deliberately NOT the runner's installed toolchain, per the grounding
    rule (deterministic, reviewable as a diff). Unknown names fail as
    `UNKNOWN LINT '<tool>::<name>' at file:line`.
  - (b) REQ-P2: scans workflow `run:` lines (inline + `run: |` block
    scalars, file:line preserved) and requires `pnpm|npm|yarn <name>` to
    resolve to a staged `package.json` scripts entry (workspace root
    preferred); a `run:` command exactly duplicating a script body
    (`pnpm eslint .` where `lint` = `eslint .`) fails as `DUPLICATE RUN
    COMMAND` citing the script; anything else unresolvable fails naming
    file:line + command. `cargo <args>` must start with a known subcommand
    or a staged `.cargo/config.toml` alias. Builtins (`pnpm install`),
    flag-only cargo invocations, and bare-binary segments (the #40
    manifest-closure domain) pass through without false positives.
  - REQ-P3: fail closed throughout — unparseable TOML/YAML, missing
    snapshot, and snapshot-pin != repo-pin (`STALE KNOWN-LINT SNAPSHOT`)
    are all exit 1. No auto-fix.
- `scripts/policy-verifier.known-lints.txt` (new): checked-in authority
  with `pin: fixture-toolchain-1`; contains `clippy::cast_possible_truncation`
  and omits `clippy::cast_lossy`. Labeled as the minimal fixture subset;
  production refresh captures the full toolchain list as a diff.
- `scripts/policy-verifier.toolchain-pin` (new): one-line repo pin the
  snapshot must match.
- `tests/test_policy_verifier.py` (new, 16 tests): synthetic `/tmp`
  fixtures only.
- `Makefile`: `policy-verifier` target + `.PHONY` entry ( runs
  `policy-verifier.py --staged`).
- `scripts/verify-rigs.sh`: appended `== V9. Policy-Text Verifier ==`
  block (one `ok()`), running the unittest file plus a live `--staged`
  run with `--pin-file`. No existing check renumbered or reworded.

Deliberate deviation from design.md noted in code: the shell-tokenizer
mirrors `manifest-closure.py`'s splitting rules instead of importing it,
so the Wave-41 gate stays separately invokable and a Wave-40 refactor can
never silently change Wave-41 verdicts (shared shape, separate verdicts).

## Claims and proof

- FIRES on the live stale text: the fixture stanza replicates the mission
  `root-lints-reference.toml` `[workspace.lints.clippy]` block read-only;
  `test_stale_cast_lossy_fires_naming_lint_and_line` asserts exit != 0
  with `clippy::cast_lossy` and the exact `:line` (computed, not
  hardcoded). PASSES on the corrected `cast_possible_truncation` stanza.
- FIRES on `run: pnpm eslint .` with a `lint` script present
  (`DUPLICATE ... citing 'lint'`); PASSES on the reconciled shapes
  (`pnpm lint`, `format:check`, `typecheck`, `unit`, `cargo fmt/clippy/test`,
  `pnpm install --frozen-lockfile`).
- Red-proof regression (T4): `--staged` temp-repo test stages the stale
  TOML (fails naming `clippy::cast_lossy`), then the fixed TOML (passes).
- Stale authority fails closed: snapshot pin != `--expect-pin` exits 1
  with `STALE`; unparseable TOML/YAML and missing snapshot exit 1.

## Acceptance outputs

- `make verify`: `SUMMARY: 25 checks passed, 0 failed` (24 pre-existing
  all still green with unchanged names/numbers + 1 new V9 check), then
  `live-health.py` advisory exit 0 (only pre-existing heartbeat/idleness
  warnings on seats).
- `openspec validate remediate-41-policy-verifier`: valid, exit 0.
- Full suite `python3 -m unittest discover -s tests`: 124 tests, OK.
- `make policy-verifier`: exit 0 (`no staged policy files; nothing to
  resolve` on the clean tree).

## Skipped items

- None of tasks T1–T6 skipped. T6 report path: the spawning stage contract
  names `docs/reports/<stage>-implementation.md`, so this file is written
  here rather than at the `remediate-41-policy-verifier-implementation.md`
  path tasks.md suggests; content covers the same evidence.

## No-live-mutation record

- Mission repo (`heretek-asset-manager`) opened read-only (`sed` reads of
  the stale TOML, live Cargo.toml, reconciled workflow, toolchain env);
  `git diff --stat` there is empty — zero tracked modifications, no
  commits, no pushes. All fixtures are synthetic (`/tmp` or worktree).
- `git status` in this worktree shows only the intended artifacts:
  modified `Makefile`, `scripts/verify-rigs.sh`; new
  `scripts/policy-verifier.py`, `scripts/policy-verifier.known-lints.txt`,
  `scripts/policy-verifier.toolchain-pin`, `tests/test_policy_verifier.py`,
  and this report. No `specs/`/`rigs/`/`rosters/`/`registry/`/`fleet/`
  files touched, so no regeneration was required.

## Self-audit

- No stubs, skips, or swallowed errors; all 16 new tests assert on
  diagnostic content (names/lines), not bare exit codes — the one test
  that briefly passed vacuously (missing-snapshot, exit 2 vs expected 1)
  was tightened to `assertEqual(1)` + message match before green.
- Zero-secret handling: fixtures are synthetic; no credentials read,
  printed, or committed.
- Not merged, not pushed, QA not dispatched — handoff left to the
  coordinator. Human merges per repo convention.
