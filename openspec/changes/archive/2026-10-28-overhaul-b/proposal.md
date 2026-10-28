# Proposal: overhaul-b — 0.7.4 contract sync + test/canary/V19 wiring

Status: scope approved (principal decisions 2026-10-27/28; findings re-verified live on main `264135e` 2026-10-28).
Issues: none tracked (hardening; Refs #66 umbrella only if needed).

## Why

The bump wave pinned the 0.7.4 toolchain but deliberately left contracts behind: `codex_permissions` is absent from `schemas/rigspec-keys.pinned.json` and `verify-rigs.sh`, `run-record.v1.schema.json` is not vendored (tarball SHA `b3c7ac64fd9dd51152888c99fdbcadd85cddebebb2d38253864bff054da3fde7` re-verified byte-for-byte from the published tarball), and the two updated `openrig-core` skills are unsynced. Separately, `make test` (line 38) hardcodes 15 of 21 suites, `test_canary_scope_only` compares against `a33f3bb` with a pre-#102 expected-role list (RED on main: 44 extra roles from the 102-closeout triple), and V19 computes its expected count as `passes + 1` (`:2502`), cascading any earlier failure into bogus doc-drift failures.

## What Changes

- M4: add `codex_permissions` to MEMBER_KEYS (pinned keys + verify gate, right after `claude_permissions`); vendor `run-record.v1.schema.json` + sha256 pin entry + contract-test coverage; sync `messaging-the-human` + `queue-handoff` SKILL.md from the published 0.7.4 tarball (verified source — no separate clone needed) via the generator path + full regen.
- M5: `make test` → `unittest discover` over all suites; canary rework (fixture fallback when `a33f3bb` is unresolvable + expected-role update to the post-#121 reality); V19 canonical-count fix; `HERETEK_ALLOW_NO_BWRAP` note behavior in V12.

## Acceptance

1. Contract suite green: `test_schema_contracts` covers all 7 schemas; regen + idempotence green; digests self-consistent.
2. `make test` runs every `tests/test_*.py` suite (discover), 0 failures/errors — canary green on clean tree AND on a tree without `a33f3bb` (fixture path).
3. V19 no longer cascades: inject an early-host failure → only its own FAIL, no doc-drift triplication.
4. `make verify` green (35/0 + V22–V27, SUMMARY frozen), `audit_loop --self-test` PASSED.
5. Drift-guard `VERDICT: PASS` → PR (Refs only).
