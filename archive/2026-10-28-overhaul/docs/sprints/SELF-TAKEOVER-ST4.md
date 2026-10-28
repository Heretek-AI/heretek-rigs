# SELF-TAKEOVER-ST4 — Generator vendor surgery + skill bindings (APPLIED by operator)

- Slice qitem: ST-4P (proposal qitem-20261021180558-1f2fb3fd280b160b).
- Source slice: qitem-20261021155313-fe1742ceb (self-takeover brief).
- Operator rule: qitem-20261021161052-94285df7040f2817 (proposal packages).
- Fleet input: system-architect proposal
  docs/architecture/ST-4-PROPOSAL-2026-10-21.md (CANNOT-STATE all four hunks,
  honored) — mechanism premise (B1/B4 ledgers), missing-input list (SHAs,
  licenses, freshness), mandatory rollback statement (stated BEFORE action),
  blast-radius note.
- Human authorization: operator session 2026-10-21 ("you can apply them").
- **Implementation: OPERATOR-EXECUTED, not seat-executed.** No seat holds
  fleet/* or scripts/* write.

## Missing inputs resolved by operator (live, 2026-10-21)

- supabase/agent-skills: exists, MIT, active. Pinned c9be0e9 (short-7 of
  c9be0e931b79, confirmed via local clone rev-parse).
- prisma/skills (NOT prisma/agent-skills, which 404s): exists, MIT, active.
  Pinned ba3f9d7 (short-7 of ba3f9d73200b, confirmed via local clone).
- Skill files verified on disk post-clone (all SKILL.md present).
- SKILL descriptions read for binding fit (quoted in commit message).
- mattpocock/skills: EXISTS, MIT — but NO binding has charter fit
  (design-system-eng candidates are process-generic, not design-systems
  specific). Source NOT added, NOT cloned. Deferred with candidate list
  (prototype, tdd) for a future slice with explicit charter need.
- vector-rag-spec prisma binding: NO FIT (no vector/pgvector skill exists;
  prisma-client-api is generic CRUD). NOT bound, documented (same bar as
  B5/B7 ill-fit refusals).

## Applied changes

1. scripts/generate-rigs.py: pins entries `supabase` (subdir skills) +
   `prisma` (subdir "." — root-layout skills); find_skill gains optional
   `subdir` key, default "skills" (backward-compatible; tob/heretek-crew
   paths untouched).
2. Cloned supabase_agent-skills + prisma_skills at pinned SHAs into
   .scratch/vendor/ (gitignored; SHAs enforced by regen fail-closed check).
3. fleet/fleet.yaml bindings (additive only):
   - ts-node-fullstack += prisma-client-api (prisma), supabase (supabase)
   - dba-specialist += supabase-postgres-best-practices, prisma-postgres-setup
   - data-pipeline-eng += supabase-postgres-best-practices
   Rollback: revert generator + fleet hunks, remove the two vendor clones,
   regen, verify 22/0 (per proposal rollback order).

## Verification (operator-run)

- Regen + ./scripts/verify-rigs.sh --check-only, target 22/0.
- Rendered proof: 4 new skills vendored under specs/agents/_shared/skills/;
  lock entries with new sources; the 3 seats render the bindings; no other
  seat touched.
- Results recorded below after execution.

## Results (operator-executed 2026-10-21)

- Live upstream re-check (2026-10-21): supabase/agent-skills + prisma/skills
  exist, MIT, active; SHAs pinned from local clones (c9be0e9, ba3f9d7).
  prisma/agent-skills 404s — correct source is prisma/skills (B1 ledger said
  prisma/skills; verified). prisma-postgres is a DEPRECATED compat name —
  bound prisma-postgres-setup instead. mattpocock source NOT added (no
  charter fit; deferred with candidate list). vector-rag-spec NOT bound
  (no vector/pgvector skill exists).
- Regen: generate-rigs.py → 51 AgentSpecs, 68 shared skills, 8 RigBundles.
  One gate needed a derived-constant update: shared-skill count 64→68
  (verify-rigs.sh:6,251,252,254) — the gate encodes the old total; the new
  total is exactly 64+4 new vendored skills. No gate logic changed.
- Verify: ./scripts/verify-rigs.sh --check-only → 22 checks passed, 0 failed.
- Rendered proof: 4 skills vendored (68 total in lock with new
  supabase/agent-skills@c9be0e9 + prisma/skills@ba3f9d7 sources);
  ts-node-fullstack + dba-specialist + data-pipeline-eng render all 5
  bindings; pg-best-practices in 2/2 expected seats; no other seat touched.

## Deviation note

No agency subagents available in the operator session (guard rejects
subagent calls for role build). Operator applied the hunks directly under
explicit human authorization with exact-match fail-closed editing, and
verifies via the automated gate + rendered greps. Human merge review
remains the gate.
