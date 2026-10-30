# seat-hygiene implementation report (stage: seat-hygiene, 2026-10-30)

## What ran

Audit-only wave for #147 (Refs #147 — never Closes). No launches, no
queue writes, no sends, no edits to live state. All inspection via
`rig ps --nodes -A` (rc=0 ×2), `rig seat status --json` ×51 (rc=0 all),
and read-only filesystem reads under `~/.openrig/state/pi/` + existence
checks of referenced paths.

## Deliverables (worktree only, uncommitted)

- `openspec/changes/2026-10-30-seat-hygiene/proposal.md` (goal: fleet-wide
  audit; non-goals: no repairs / no launches / no live-health change /
  no V-gate / never Closes #147)
- `openspec/changes/2026-10-30-seat-hygiene/specs/seat-hygiene/spec.md`
  (ADDED REQ-H1 completeness, REQ-H2 machine-readable output, REQ-H3
  zero-mutation, each with `#### Scenario:` blocks)
- `openspec/changes/2026-10-30-seat-hygiene/design.md` (state-root map,
  6-field inventory, dangling definition, impact classes, repair-wave
  input contract)
- `openspec/changes/2026-10-30-seat-hygiene/tasks.md` (triad box UNCHECKED)
- `docs/evidence/seat-hygiene-2026-10-30/audit.md` (runbook: every command
  rc=0, 51-row per-seat table, counts, impact), `dangling-seats.json`
  (24 entries: 2 lobotomized + 22 stale), `ps-pre.txt` + `ps-post.txt`
  (111 lines each, byte-identical)
- `AGENTS.md`: +1 docs-map row (1 insertion, 0 deletions)

## Validation

- `openspec validate 2026-10-30-seat-hygiene` → `Change is valid`, rc=0
- `./scripts/verify-rigs.sh --check-only` → 39 passed, 0 failed (no new
  gate), rc=0 — re-run after AGENTS.md row, still 39/0
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED, rc=0
- `python3 scripts/generate-rigs.py --check-idempotent` → byte-identical,
  rc=0; left 35 generated-leaf modifications (PRE-EXISTING staleness, same
  as seat-race QA §A.4 — wave touched zero generator inputs) → reverted
  via `git checkout -- .`; final `git status`: only the 2 new untracked
  dirs + AGENTS.md
- Secret sweep (`sk-|ghp_|xox[bap]-` over new files): 0 matches. Sole
  `Closes #147` occurrence is inside backticks (code span, not parsed by
  GitHub) — same precedent as seat-race R3.
- `make test`: SKIPPED — `git diff --name-only` (tracked) shows only
  AGENTS.md; all other additions are untracked openspec + evidence docs.
  Zero code/test/script diffs, so skip is legitimate per stage rules.

## Self-audit / skips / blockers

- Per-seat counts: 51 live seats scanned — 24 DANGLING shellPath
  (2 lobotomized: `build-java-kotlin-eng`, `build-python-backend-spec`;
  22 stale), 27 clean. `launch_cwd` uniform + existing (51/51).
  `packages[]`, `sessionFile`, secret-store: 0 missing. 21 missing MCP
  binaries ALL under disabled/deferred servers (benign). 16 sessions-only
  dirs + 3 orphaned command-* state dirs recorded with reason.
- Top findings: (1) 47% of the live fleet carries a dangling shellPath —
  any next fresh launch on those 24 lands lobotomized; (2) daemon
  `running/active/ready` does NOT validate shellPath (all 51 report ready);
  (3) no live field references any existing worktree → pruning
  `seat-hygiene` later orphans nothing.
- Skipped: `make test` (reason above, verified). Nothing else skipped.
- Blockers: none. NOT committed (coordinator commits). Triad UNCHECKED —
  coordinator runs QA + drift-guard next.
