# Proposal: 2026-10-29-bump-075 — pin @openrig/cli 0.7.5 with ledger

Status: scope per `2026-10-29-five-wave-remediation-plan.md` Wave 1 (Build-agent handoff, agreed via grilling Q1–Q14).
Issues: none tracked (stack maintenance; bump ledger, no issue — no `Closes`).

## Why

The fleet pins `@openrig/cli@0.7.4` (`6d9e8e27`) while npm `latest` is `0.7.5`
(tag `v0.7.5` peels to commit `b57c4da3c3ac3fb420a09e5a169d3e85f9529e93`,
published 2026-10-29T07:36:19Z). Per the 0.7.4 precedent
(`docs/sprints/CLI-0.7.4-BUMP.md`), a stack bump ships with a ledger and a
green tree. Upstream's own `whats-new` for 0.7.5 lists: DB migration 126
(`escalation_target_refs`), openrig-core 0.1.21→0.1.22 (queue-handoff parking
prose), `rig send` 60s result wait, send-refusal 409-vs-500, #2200 still not
fixed. None of these demand a generator-input change (see design §2).

## What Changes

- Pin bump: install `@openrig/cli@0.7.5` (host toolchain) and record the
  version/commit/tarball in the bump ledger `docs/sprints/CLI-0.7.5-BUMP.md`
  (0.7.4-ledger pattern: version output, pin locations, verify result).
- Update the 8 true-pin files only (AGENTS.md surgical: stack line + tarball
  sha ref + docs-map row, diff-stat ≤15 lines; README.md, Makefile,
  docs/USER_GUIDE.md, docs/TECHNICAL_DOCUMENTATION.md,
  PROMPT_ADVERSARIAL_FLEET_AUDIT.md, docker/Dockerfile, scripts/verify-rigs.sh
  V13/V18 pin strings). No generator-input change, no regen, no new V-gate.
- Full tree green on the bumped toolchain: `make verify` (39/0),
  `audit_loop --self-test`, idempotent regen check, `make test`.

## Acceptance

1. `rig --version` → `0.7.5` on the build host.
2. Ledger exists with version + tarball SHA (two independent fetches) +
   verify output + 8 true-pin files + deferred-item notes.
3. `./scripts/verify-rigs.sh --check-only` green (39/0, SUMMARY frozen, no
   V-gate added/renamed), `generate-rigs.py --check-idempotent` exit 0,
   `audit_loop --self-test` PASSED, `make test` ≥634 passed / 0 failed.
4. `openspec validate 2026-10-29-bump-075` exit 0.
5. Red-proof: pin `0.7.4` tarball-hash expectation back into the V18 gate →
   RED; restore `0.7.5` → GREEN (commands + outputs in the implementation
   report).
6. Drift-guard `VERDICT: PASS` → PR (Refs only; no `Closes`).
