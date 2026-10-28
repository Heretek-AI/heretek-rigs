# Design: overhaul-c

## Architecture

Single worktree `.lane/trees/overhaul-c`, branch `feat/overhaul-c` from clean `main` (`b5b5b2b`). M6 (moves) → M7 (prompt) → M8 (regen + gates) → M9 (PR). Single triad, one PR.

## Verified move mechanics (live, `b5b5b2b`, 2026-10-28)

- Stale dirs/files confirmed present: `claude/`, `gemini/`, `.opencode/` (tracked: loop log + json + skills), `docs/sprints|architecture|ops|perf`, `REMEDIATION_LOG.md`, lockfile, `HANDOFF_CLAUDE_AUDIT.md`, both root `PROMPT_*`, `docs/PROMPT_*`, `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md`. `docs/IMPLEMENTATION_PROMPT.md` absent.
- Code refs into moved content are comments only (`check-envelope.py:5`, `reconcile.py:5` → `docs/sprints/…`) — no executable reads; safe to move.
- HR-8.4 (`verify-rigs.sh:1293`) reads 5 paths incl. the two root `PROMPT_*` files → list MUST be updated to the post-move layout (moved prompt files drop out; the two `docs/*.md` entries stay if those files stay — verify each entry before editing).
- `audit_loop.py`: constants `:39-40`, help `:468`, executed read `:491`, message `:547`.
- `docs/evidence/run-records.json` does NOT exist; V13 reads it only when harness claims exist — nothing to move, keep the semantics (do not create an empty file).
- `.gitignore` today: `.scratch/` present; `.opencode/`, `.lane/`, lockfile name absent → add exactly those three lines.
- Generator inputs (`fleet/`, `schemas/`, vendor) untouched by moves → M8 regen MUST be a no-op (any leaf diff beyond provenance is a finding, not an expectation).

## Milestone order

1. **M6 moves:** enumerate live from disk (do not trust the proposal's counts — recount), `git mv` each stale path into `archive/2026-10-28-overhaul/<same-relative-path>`, update HR-8.4 list + maps + `.gitignore`. Verify keep-list byte-identical (`sha256sum` spot-check + full `git status` review: only intended renames).
2. **M7 prompt:** fresh `docs/IMPLEMENTATION_PROMPT.md` (reconciled plan + current gates: 0.7.4 toolchain, 35-gate SUMMARY, V22–V27, wave discipline), repoint audit_loop (const + help + exec + message), self-test green.
3. **M8 regen + gates:** source commit (coordinator) → clean regen → leaves commit (coordinator) → idempotence + verify + make test + topology.
4. **M9 PR** with Summary/Verification body.

## Fail-closed modes

- Any keep-list file differing after the move → halt (restore + investigate), do not proceed to regen.
- Regen producing non-provenance leaf diffs → halt (a move touched a generator input — find it).
- `git log --follow` spot-check on 3+ moved files must show pre-move history.
