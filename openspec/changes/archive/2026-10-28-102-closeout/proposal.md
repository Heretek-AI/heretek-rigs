# Proposal: 102-closeout — close #102 P3 remainder (HR-F18, HR-2.5, writing-skills, DAG)

Status: scope approved (principal decisions 2026-10-26 via native ask, Rounds 1–3 all Recommended).
Issues: #102 (P3 bundle remainder). Refs #66 umbrella. Closes #102 only if all four items fully fixed, else Refs.

## Root cause (verified read-only, explore ses_e84bb6c9bffeRd2T657mw5qqlw)

- HR-F18: `fleet/fleet.yaml:648` + ~20 seats carry `rig queue *` wildcard allow (+ paired `rig send *`). `fleet.yaml:49-57` `command_effects` scopes only `queue --note` / `--body-file` argv; no bare `queue list|create` / bare `send` deny. `fleet/command-effects/` does not exist (HANDOFF path stale).
- HR-2.5: `rigs/heretek-omni-fleet/rig.all-51.yaml` EXISTS. `scripts/verify-rigs.sh:2442-2454` (V18) runs `rig spec validate` on 8×`rig.yaml` PLUS `rig.all-51.yaml` → COVERED. `:2419-2428` `rig bundle check` loops `EXPECTED_8_RIGS` only → all-51 NOT bundle-checked.
- writing-skills: 1 hit `specs/agents/_shared/skills/test-driven-development/writing-good-tests.md:51` (`superpowers:writing-skills`).
- DAG: local check `verify-rigs.sh:896` (`cycle detected in delegates_to/spawned_by`) only; no upstream report filed.
- Closest existing specs do NOT cover this: `checker-batch-d` REQ-D102 = stale-count guard only; `remediate-37/44` = doc `--json` examples only.

## Change (single change, 4 gated milestones in order M1→M4)

- M1 HR-F18 (only code change, first): deny bare `rig queue list`, bare `rig queue create` without `--json --verify`, bare `rig send` in seat maps via `fleet/fleet.yaml` + `generate-rigs.py` regen. New appended verify block (never renumber). `AGENTS.md:30` one-line gate append.
- M2 HR-2.5 (docs only): declare `rig spec validate` canonical for `rig.all-51.yaml`, `rig bundle check` 8-rig-only intentional. No code change.
- M3 writing-skills (vendor/patch + regen): fix via `fleet/skill-patches/` + regen, never hand-edit `specs/`.
- M4 DAG (local note only): `docs/evidence/102-closeout-dag.md` + docs reference; no upstream filing.

## Acceptance (binary, per-milestone + gate)

1. M1: bare forms deny in-seat, `--json --verify` forms allow; red-proofs both directions on disk.
2. M2: docs state canonical + intentional; V18 still passes all-51.
3. M3: zero dangling refs, 68/68 loads, no DIAG.
4. M4: local evidence note exists, cites `:896` check.
5. `make verify` green (35/35 + new appended blocks, no renumber); `python3 scripts/audit_loop.py --self-test` passes.
6. Drift-guard `VERDICT: PASS` on disk → PR (`Refs #102`; `Closes #102` only if all four fully fixed).
