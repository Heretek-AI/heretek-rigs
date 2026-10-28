# Proposal: overhaul-bump — pin @openrig/cli 0.7.4 with ledger

Status: scope approved (principal decisions 2026-10-27/28: bump-first, pin+ledger only, full triad bar).
Issues: none tracked (stack maintenance; Refs #66 umbrella only if needed).

## Why

The fleet pins `@openrig/cli@0.7.2` (`8b180689`) while npm `latest` is `0.7.4` (tarball sha256 `d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1`, verified 2026-10-28 from the published tarball). The overhaul (Waves A–C) must build on the bumped tree rather than mid-flight. Per the 0.7.2 precedent (`docs/sprints/CLI-0.7.2-BUMP.md`), a stack bump ships with a ledger and a green tree.

## What Changes

- Pin bump: install `@openrig/cli@0.7.4` (host toolchain) and record the version/commit/tarball in the bump ledger `docs/sprints/CLI-0.7.4-BUMP.md` (0.7.2-ledger pattern: version output, pin locations, verify result).
- No contract sync here (MEMBER_KEYS `codex_permissions`, run-record schema, openrig-core skills ride overhaul Wave B with their own red-proofs).
- Full tree green on the bumped toolchain: `make verify`, `audit_loop --self-test`, idempotent regen.

## Acceptance

1. `rig --version` → `0.7.4` on the build host.
2. Ledger exists with version + tarball SHA + verify output.
3. `make verify` green (35/0 + V22/V23/V24 info lines, SUMMARY frozen), `generate-rigs.py --check-idempotent` passes, `audit_loop --self-test` PASSED.
4. Drift-guard `VERDICT: PASS` → PR (Refs only).
