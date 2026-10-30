# Verification report — Wave 5 F4 amendment (`f4-amendment`, change `2026-10-29-f4-amendment`)

Independent drift-guard audit. Worktree `.lane/trees/f4-amendment`, branch
`feat/f4-amendment`, HEAD `c4ed784`. Stage `f4-amendment` (BEHAVIOR CODE:
reconciler classifier). Refs #15, Refs #134. Auditor modified no worktree
source file: both sabotages ran in `/tmp/f4dg-tree` scratch; generator
side-effects reverted; final `git status --short` empty.

## 1. Scope — One Rule holds, no regen needed

- `git diff main...HEAD --stat`: 11 files — `AGENTS.md` (+1 docs-map row),
  `scripts/reconcile.py` (+17/−2), `scripts/reconcile_model.py` (+93/−12),
  `tests/test_auth_envelope.py` (+281/−0), `docs/evidence/f4-amendment/`
  (2 logs), `docs/reports/f4-amendment-implementation.md`,
  `openspec/changes/2026-10-29-f4-amendment/` (proposal/design/tasks +
  `specs/auth-envelope/spec.md` delta). Exactly the allowlisted set.
- Guarded paths empty in diff: `git diff main...HEAD --name-only --
  fleet/ specs/ rigs/ rosters/ registry/ archive/ openspec/specs/` → empty.
  Canonical `openspec/specs/auth-envelope/spec.md` (REQ-E2) byte-intact.
- Test file is pure append (+281/−0; zero `-` lines): both green E2 pins
  untouched. `generate_trackers.py` unchanged (default `None` ⇒ quiet).
- `python3 scripts/generate-rigs.py --check-idempotent` → `idempotence
  check passed (two consecutive runs byte-identical)`, re-run by this
  auditor; environmental side-effects (`registry/` re-lag + hermetic drift
  in `registry/ rigs/ specs/ fleet/`) reverted via `git checkout --`,
  final status empty. No `ALLOW_DIRTY` used, no wave drift.

## 2. Amendment legitimacy — all three F4 skip-reasons resolved, E2 intact

Per `docs/reports/15-auth-envelope-verification.md` §3 (lines 80–113):

1. **No registry → passed-in index.** Old signature
   `stalled_premise_drift_diff(row, queue_by_id, transitions_by_id)` had no
   envelope parameter; new signature threads `envelope_by_id=None` through
   `diff_row` → classifier, fed by `reconcile.py --envelopes FILE`
   (JSON object, read-only load, absent flag ⇒ `None`). No store exists in
   the reconciler — the caller supplies the registry, which is exactly the
   "envelope-lookup design" the skip demanded.
2. **Scenario contradiction → scoped by addition.** REQ-E2 text, the
   clean-quiet scenario, and both corpus pins byte-intact (0 diff lines
   under `openspec/specs/`; E2 pins re-run green). REQ-E5 fires only where
   a populated lookup is consulted; `if not envelope_by_id: return None`
   covers absent (`None`) and empty (`{}`) at the single gate, so
   clean-quiet is preserved by construction. The normative parenthetical is
   unchanged; the new REQ carries the clean-landing-without-envelope case.
3. **Scenario governs → still governs.** The E2 quiet scenario and its two
   pins exercise the classifier without a lookup and stay green pre- and
   post-fix (auditor re-ran both: OK; QA Q-R3: E2 pins green on pre-fix
   tree while all 11 new pins fail/error).

F6/F7/F8 hook claim is REAL (auditor read `reconcile_model.py:1027–1095`):
the E5 helper receives the already-parsed `premise`, the F8
newest-to-oldest-bound `landing`, and `queue_evidence`; it is reachable
only after no-premise/no-qitem/no-entry/terminal early-`None` returns and
after the E2 landing-absent/drifted/scope-breach stalls — i.e. downstream
of the F8 scan, the F7 hardened `_scope_covers`, and F6 shape parsing. No
duplicate parsing; no parallel mapping.

## 3. Classifier correctness — re-verified by this auditor on HEAD

- No flag ⇒ `envelope_by_id=None` ⇒ quiet (code path read; e2e no-flag
  half green in corpus).
- Empty file `{}` ⇒ exit 0 `in sync` (auditor ran pristine CLI: `empty-file: 0`).
- Non-dict file ⇒ exit 2 `UNPARSEABLE ENVELOPES (expected a JSON object)`
  fail-closed (auditor ran pristine CLI: `non-dict: 2`).
- Matching envelope ⇒ quiet; mismatched `premise_hash`/`diff_hash` ⇒
  `stalled-envelope-absence` (corpus pins green; case-insensitive compare
  via `str(...).lower()` vs stored `premise["diff_hash"]`).
- Non-dict record counts as present (quiet) — matches spec ("bare
  non-dict record counts as present"); dict without hash keys falls
  through `for...else` ⇒ quiet, a conservative non-gating choice.
- No auto-commit surface: `git diff` adds zero lines matching
  `subprocess|commit\(|os.system` (the two `subprocess` hits are the
  pre-existing read-only `run_rig` fetcher, untouched); corpus
  `test_no_commit_surface_in_presence_path` + attribution report-only pin
  (input/output byte-compare) green.
- `render_diff` renders `stalled-envelope-absence` as NEEDS-HUMAN-REVIEW +
  SUGGESTED (not paste-ready), no `PROPOSED-CELL:::` — same withholding as
  E2 (diff read; e2e stdout asserts green).
- Never-done/recovery preserved for the new class: it returns a routing
  diff only; row state untouched (byte-compare pin).

## 4. Gates re-run by this auditor (all binary green)

- `make test` → `Ran 645 tests OK` (110s; baseline 634 + 11 new), 0 failures.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed,
  0 failed`, V31 PASS (notes "38 corpus tests pass" = 27 + 11). V33
  absence JUDGED RIGHT: `grep V33 scripts/verify-rigs.sh` empty; per
  `design.md` §5 no corpus-unpinnable gap was proven (DG-R1/DG-R2 below).
- `openspec validate 2026-10-29-f4-amendment` → valid, rc=0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`.
- Idempotence + revert per §1.

## 5. Red-proofs — auditor's own sabotage (scratch, worktree untouched)

- **DG-R1 (check removed):** scratch copy with the clean-landing tail
  replaced by `return None` → `Ran 11 tests, FAILED (failures=5)` (same
  count/set direction as builder R1 and QA Q-R1); scratch restored from
  backup, sha256 `081987f9…` byte-identical to the logged green pin →
  `Ran 11 tests OK`. R1 signature holds at HEAD.
- **DG-R2 (lookup emptied at call site):** scratch `reconcile.py` patched
  to `envelope_by_id=None` →
  `test_reconcile_end_to_end_envelopes_flag` + match-quiet pair gives
  `Ran 2 tests, FAILED (failures=1)` — the flag test flips, the quiet
  test holds. The corpus pins the CALL SITE (not just the helper),
  confirming the honesty of the V33-relevance claim. R2 signature holds.
- **R3 vacuity:** QA Q-R3 reproduced on record (`failures=2, errors=11`
  pre-fix; E2 quiet pins green) — gap real, no pin vacuous. Auditor's
  DG-R1/DG-R2 RED→GREEN both directions confirm non-vacuity at HEAD.
- Green-pin shas independently corroborated: `sha256sum` of all three
  files matches `red-proofs.log` exactly
  (`081987f9…`, `042824b1…`, `5258c0bf…`).

## 6. Secrets, stubs, Refs-only

- No secret values in diff or evidence. The only 40+ char strings in
  `docs/evidence/f4-amendment/` are the three sha256 restore pins
  (one-way digests of committed public files, re-verified), two evidence
  path strings, and three long test identifiers. Fixtures use dummy ids +
  16-hex hashes. F1 wording nit confirmed substance-only.
- No stubs: `grep TODO|FIXME|XXX|SkipTest` in changed scripts empty; all
  11 new tests assert behavior (`assertIsNone/IsNotNone`, class equality,
  return codes, stdout markers, byte-identical file compares); zero
  deletions in the test file.
- Refs-only: no actionable `Closes`/`Fixes`/`Resolves` directive anywhere
  wave-owned. Remaining `Closes #15/#134` mentions are (a) `never Closes`
  convention statements inside repo markdown (GitHub acts only on PR
  bodies/commit messages; no PR exists — nothing committed), and (b) the
  report quoting its own negative-grep command. Zero bare closing tokens.

## 7. Honesty — no overclaim found

- "+281/−0" exact (`--numstat` 281/0). "38 corpus tests" exact per V31
  output. "39/0, no V33" exact. R1 "5 failures" exact (auditor reproduced
  the count; F2's enumeration imprecision — one of the five is the
  attribution report-only pin, not a second e2e flag test — changes no
  signature, count, or restore behavior). F1/F2 nits confirmed
  informational: neither touches any acceptance predicate.
- "Corpus pins the call site" is TRUE (DG-R2 proves the e2e flag test is
  the call-site pin), not just the helper.

## Findings

None. No FAIL-grade items.

VERDICT: PASS
