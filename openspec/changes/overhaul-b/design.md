# Design: overhaul-b

## Architecture

Single worktree `.lane/trees/overhaul-b`, branch `feat/overhaul-b` from clean `main` (`264135e`). M4 (contracts + regen) first, then M5 (test wiring) on the regenerated tree. Single triad, one PR.

## Verified inputs (live, 2026-10-28)

- Published tarball `/tmp/bump-verify/openrig-cli-0.7.4.tgz` (sha256 `d11dd8a6…`, kept as evidence reference; re-pull from npm if stale): `package/daemon/docs/reference/schemas/run-record.v1.schema.json` hashes `b3c7ac64…` byte-identical to the brief; `package/daemon/assets/plugins/openrig-core/skills/{messaging-the-human,queue-handoff}/SKILL.md` present — use the TARBALL as the verified vendor source (no separate `0c44b23a` clone needed; record the tarball SHA in the ledger update if touched).
- Current tree: `codex_permissions` zero hits; `run-record.v1.schema.json` absent; `make test` line 38 hardcodes 15 files vs 21 on disk (`test_identity_m1` + 5 older orphans unwired); V19 `:2502` `passes + 1`; canary base `a33f3bb` present in-history but expected list predates the 102-closeout all-51 triple (44 extra roles → RED on clean main).
- Symlink `.scratch/vendor` from `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.scratch/vendor` (python `os.symlink`, gitignored) if the worktree lacks it — skill sync needs vendor dirs.

## Milestone order

1. **M4 contracts:** pinned-keys + verify-gate `codex_permissions`; vendor run-record + pin + contract-test coverage; skill sync via generator path; clean-tree regen (commit sources first → regen → chore leaves commit per the established pattern).
2. **M5 wiring:** discover-based `make test`; canary expected-set update to post-#121 reality + fixture fallback (`tests/fixtures/can-base-permissions.json` or equivalent) for missing-`a33f3bb`; V19 canonical total; V12 note-mode.

## Fail-closed modes

- M4 skill sync MUST go through the generator/vendor path (vendor/patch + regen), never hand-edit `specs/`.
- If the tarball skill bodies differ from the brief's `+37/-3`, `+9/-1` deltas, record actuals in the ledger/evidence — do not force the brief's numbers.
- M5 must not weaken the canary: the updated expected set is exactly [canary + M4 5 + wave-F 1 + 102-closeout 51-triple roles...] — enumerate from the live base diff, never invent; any role outside the enumeration still fails.
- Gotchas carry forward: safe_dump ban, TERMINAL_BASH_DENIES mirror rule, `*..*` deny tail, no Closes on open issues, commit-before-regen.
