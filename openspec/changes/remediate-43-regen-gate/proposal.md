# Proposal: remediate-43-regen-gate — sanctioned-untracked allowlist in the regen gate

## Status
Spec-only change package for issue #43. No implementation in this package;
`tasks.md` is the testable checklist the implementation stage follows.

## Motivation
`scripts/generate-rigs.py` (`resolve_heretek_commit`, ~L65–105) dies when
`git status --porcelain` is non-empty — and `--porcelain` includes untracked
files. But the fleet's own operating pattern dirties the tree in steady
state: every session writes evidence files (`docs/evidence/…`), reports
(`docs/reports/…`), loop transcripts (`.opencode/…`), and mutates
`HANDOFF.md`. At `main@96aab30` the tree shows 1 modified tracked file
(`M HANDOFF.md`) + 14 untracked session-evidence paths — every regen today
requires the `HERETEK_RIGS_ALLOW_DIRTY=1` dev-escape hatch, so the clean-tree
requirement never holds in practice. The gate's intent (never bake
provenance on an unknown tree) is correct; the failure is that *routine,
sanctioned* outputs the workflow itself demands count as dirt with no
committed home and no ignore rule.

## Fact sources (verified read-only before authoring)
- `scripts/generate-rigs.py`: `resolve_heretek_commit` — single binary
  escape (`ALLOW_DIRTY`), no filtering; refusal message names no paths.
- `git status --porcelain` semantics: untracked (`??`) paths included —
  confirmed by the issue's evidence listing, consistent with git behavior.
- AGENTS.md:46 blesses exactly these strays: `docs/evidence/`,
  `docs/reports/`, `.agents/`, `.claude/`, root `skills-lock.json`,
  `PROMPT_REVIEW.md` — "prior sessions' artifacts, not yours to delete."
  The gate the workflow refuses and the strays the workflow blesses are the
  same files: that contradiction is this change's scope.

## Boundaries (issue option (a), per HANDOFF recommendation)
- Touch ONLY: the dirt check in `scripts/generate-rigs.py`, one appended
  `verify-rigs.sh` check (next number — no renumbering per AGENTS.md:45),
  and docs (`AGENTS.md` gate paragraph + expected-count references).
- The allowlist covers UNTRACKED paths only. Any modified tracked file
  (including `HANDOFF.md`) still refuses without the existing escapes.
  Rationale: tracked modifications can silently change generator inputs, so
  provenance MUST stay fail-closed on them.
- Existing escapes (`HERETEK_RIGS_ALLOW_DIRTY=1`,
  `--allow-synthetic-provenance`) keep their exact semantics.

## Non-goals
- Issue option (b) (auto-commit evidence to a side branch) and option (c)
  (bless ALLOW_DIRTY as normal) — explicitly rejected; this change makes
  clean-tree achievable, not optional.
- No committed home / retention policy for evidence (separate concern).
- No change to what the gate bakes (still `git rev-parse HEAD`, still
  40-hex, still dies on unresolvable HEAD).

## Acceptance (see tasks.md)
1. Returnable: a fresh session producing its normal evidence
   (`docs/evidence/…`, `docs/reports/…`, loop JSON) runs
   `generate-rigs.py` with NO env override.
2. A modified tracked file still refuses (exit 2, blocking path named);
   a non-allowlisted untracked path still refuses.
3. `make verify` green with the appended allowlist-consistency check
   (count documented wherever the old 22-count is referenced by this
   change's docs edits).
