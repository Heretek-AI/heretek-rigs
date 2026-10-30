# Proposal: F4 amendment — opt-in envelope-presence gating (new REQ-E5)

- **Change ID**: `2026-10-29-f4-amendment`
- **Issues**: Refs #15, Refs #134 (both stay open; never `Closes #15`, never `Closes #134` — no live fleet has proven envelope pace).
- **Amends**: `openspec/specs/auth-envelope/spec.md` REQ-E2 parenthetical (unimplementable half), via ADDITION only.
- **Order**: amendment-first, then classifier, then corpus. No classifier or corpus change lands before this amendment is approved in the worktree.

## Motivation

PR #133 review finding F4 asks that an open authorization without a matching envelope stall **even when the landing matches the premise** (clean quiet only with a matching envelope). The rework-1 drift-guard audit (`docs/reports/15-auth-envelope-verification.md` §3) independently confirmed a three-reason skip: (1) no envelope registry exists in the reconciler — the classifier signature `stalled_premise_drift_diff(row, queue_by_id, transitions_by_id)` binds premise→landing and has no envelope parameter or store to consult; (2) the concrete REQ-E2 scenario "clean premise stays quiet" plus its two green corpus pins (`test_clean_premise_stays_quiet`, `test_reconcile_end_to_end_clean_quiet`) contradict envelope-presence gating — threading presence into the classifier flips both green tests RED; (3) per the review caution (prefer the spec), the scenario governs, so the normative parenthetical ("or which carries an open authorization with no matching envelope") is unimplementable as written for the clean-landing case.

The implementable half of that parenthetical (open authorization with no landing *record*) is already covered by the existing `landing is None` → stalled branch, pinned by `test_open_authorization_without_landing_is_stalled`. What remains is the clean-landing-without-envelope case — and it needs a design the reconciler can actually consult.

## Proposed change

1. **Amendment (this package)** — author new REQ-E5 (envelope-presence gating) as an ADDITION alongside REQ-E2. REQ-E2 text, the clean-quiet scenario, and both green E2 tests stay byte-intact. REQ-E5 is opt-in: it fires only where an envelope lookup exists; a default empty/absent lookup keeps it quiet, so clean-quiet is preserved by construction.
2. **Classifier** — build the minimal envelope lookup the F4 skip proved missing: an envelope index passed alongside `queue_by_id` (same passing pattern through `reconcile.py` into the classifier). The classifier consults the store where present; no store rewrites, no executor, no commit surface (REQ-E3 never-`done`/never-auto-commit stands).
3. **Corpus + pins** — fixtures plus anti-vacuity pins only; corpus grows past 634. V33 appended ONLY if the new classifier proves a gap the corpus cannot pin — default NO new gate (decision recorded with reason either way).

## Non-goals

- No REQ-E2 rewrite (text, scenario, and both green tests stay byte-intact).
- No live execution (fixtures only; no live seats, no live queue/rows).
- No auto-commit surface (REQ-E3 stands; negative check: no `commit()`/landing-write calls in new/changed code).
- No `Closes #15` / `Closes #134` tokens anywhere wave-owned.
- No V33 unless a proven gap demands it (default: none).
- Touching V1–V31 (append-only if V33 is ever appended; post-wave total stays 39 by default).

## Acceptance summary (binding; see `tasks.md`)

- A1: `openspec validate 2026-10-29-f4-amendment` exits 0.
- A2: REQ-E2 text, clean-quiet scenario, and both green E2 tests byte-intact and still green.
- A3: REQ-E5 red-proven: populated lookup without a matching envelope → stalled; lookup absent/empty → quiet; clean premise with matching envelope → quiet; sabotage (lookup emptied / check removed) → silent (RED), restore → stalled (GREEN).
- A4: compound green: `verify-rigs.sh --check-only` → 39 passed, 0 failed (40/0 only iff V33 appended with freeze note); `make test` ≥634, 0 failures; `audit_loop.py --self-test` PASS; `generate-rigs.py --check-idempotent` byte-identical.
- A5: negative checks: no `commit()`/landing-write calls in new/changed code; zero unredacted secret-shaped strings in evidence; fixtures use dummy ids/hashes only.
