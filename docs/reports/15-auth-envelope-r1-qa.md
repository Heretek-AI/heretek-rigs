# QA report — 15-auth-envelope rework-1 (Refs #15, never Closes #15)

Wave/stage: 15-auth-envelope rework-1 (PR #133 review findings F1–F9).
Worktree: `.lane/trees/15-auth-envelope`, branch `feat/15-auth-envelope`
at `697543d` (rework commit under test; tree was clean at intake).
No commit, no push — left uncommitted for the coordinator.
No Unity binding (not a Unity repo stage). Dummy keys only; nothing read
from `~/.config/heretek-rigs/secrets/`.

Every claim below was verified against current disk state; nothing was
trusted from `docs/reports/15-auth-envelope-r1-fixes.md`. All sabotage was
temporary file edits with `/tmp/opencode/qa-r1/` backups, byte-identical
restores confirmed by `sha256sum`, and GREEN re-runs before proceeding.

## 1. Baseline acceptance (unmodified tree @ 697543d, sequential runs)

- `python3 -m unittest tests.test_auth_envelope tests.test_auth_envelope_prefix` -> `Ran 35 tests OK`, EXIT 0 (29 + 6 new: F5x1, F6x1, F7x1, F8x2, F9x1)
- `./scripts/verify-rigs.sh --check-only` -> `SUMMARY: 39 checks passed, 0 failed`, V31 PASS listed, EXIT 0
- `make test` -> `Ran 634 tests OK`, 0 failures, EXIT 0
- `python3 scripts/generate-rigs.py --check-idempotent` -> byte-identical, EXIT 0 (rewrote the known `resolvedCommit` re-lag stamp across `registry/`; reverted via `git checkout -- registry`, status clean)
- `python3 scripts/audit_loop.py --self-test` -> SELF-TEST PASSED, EXIT 0

Caveat (not a finding): one `./scripts/verify-rigs.sh` run executed
concurrently with `generate-rigs.py` died with `KeyError: 'exec-director'`
mid-regen; the sequential re-run is green (EXIT 0, 39/0). Do not run verify
concurrently with the generator.

## 2. Fix verification (F1–F3, F5–F9)

- **F1 — CONFIRMED.** The report scope statement now names exactly the
  HANDOFF change (`docs/reports/15-auth-envelope-verification.md:64-65`):
  "operating-discipline expect-count updated 38→39 by the r1 rework (F3;
  the post-PR #132 snapshot counts in §1 stay intact)". Verified on disk.
- **F2 — CONFIRMED.** Exactly one clause added to the report opening
  (`verification.md:11-13`): the `--check-idempotent` registry
  provenance side-effect reverted via `git checkout -- registry`. No other
  opening change. This pass reproduced the same side-effect and the same
  revert (see §1).
- **F3 — CONFIRMED, one line only.** `HANDOFF.md:139` reads
  `# Expect: 39 checks passed, 0 failed`; `git show HEAD` confirms the
  single-line 38→39 diff. Snapshot counts untouched: `HANDOFF.md:18`
  still records the post-PR #132 baseline (`SUMMARY: 38 checks passed,
  0 failed`). Matches the AGENTS.md expect-line, the V19 freeze, and the
  live verify SUMMARY (39/0).
- **F5 — CONFIRMED + red-proofed.** `,` is in the `_SCOPE_BAD_RE` class
  (`scripts/auth_envelope.py:48`); pin
  `test_mint_rejects_comma_in_scope_entry` (`tests/test_auth_envelope.py:597`)
  present. My sabotage (comma removed) → EXIT 1, `ValueError not raised`;
  restore byte-identical (`59560047…`), GREEN.
- **F6 — CONFIRMED + red-proofed.** Shape checks present
  (`auth_envelope.py:182-192`): non-string → `str(path)` uncovered;
  empty/absolute/empty-segment/`.`/`..` rejected before prefix checks.
  Pin `test_scope_covers_rejects_suspicious_landing_paths` (`:614`)
  present, incl. canonical covered/uncovered preservation. My sabotage
  (block removed) → EXIT 1, `AttributeError: 'NoneType' ... startswith`
  (the exact fail-open crash); restore byte-identical, GREEN.
- **F7 — CONFIRMED + red-proofed.** `..`-segment guard present
  (`reconcile_model.py:885-887`, segment-wise so `src/..hidden/x` is
  unaffected). Pin `test_premise_scope_rejects_dotdot_traversal` (`:312`)
  present, incl. canonical preservation. My sabotage (guard removed) →
  EXIT 1, `failures=1`; restore byte-identical (`d371f1e1…`), GREEN.
- **F8 — CONFIRMED + red-proofed.** Newest-to-oldest scan present
  (`reconcile_model.py:979-993`): trail sorted by `transitionId`
  descending, first `_parse_landing`-recognized note binds; terminal
  check, `queue_evidence`, attribution, and the open-authorization branch
  unchanged. Pins `:325` (clean + trailing note → quiet) and `:363`
  (drifted + trailing note → still stalled with drift reason) present.
  My sabotage (latest-only) → EXIT 1, `failures=2` with the exact incident
  signatures (clean case stalls "no matching landing"; drift case loses
  "drifted"); restore byte-identical, GREEN.
- **F9 — CONFIRMED + red-proofed.** MAC binding intact; pin
  `test_tampered_expiry_and_hash_refused_for_mac` (`:660`: expiry
  `1780000000`→`1880000000` and diff-hash swap without re-signing → both
  refused with "bad envelope mac", `seen` stays empty) present alongside
  `test_bad_mac_refused`. My sabotage (MAC check disabled) → EXIT 1,
  `failures=2`; restore byte-identical, GREEN.

Pre-sabotage pins matched the fix report (`59560047…`, `d371f1e1…`),
confirming the committed state is what the report describes. No vacuous
check: all 5 QA-R1 probes went RED for the incident-restoring reason and
GREEN on byte-identical restore (details in
`docs/evidence/15-auth-envelope/red-proofs.log`, QA-R1 section).

## 3. F4 adjudication — AGREE with skip (evidence)

The finding asks that an open authorization without a matching envelope be
stalled even when the landing matches the premise (clean quiet only with a
matching envelope). I agree with the implementer's skip, for three
independent reasons verified on disk:

1. **No envelope registry exists in the reconciler.** `grep envelope
   scripts/reconcile_model.py scripts/reconcile.py` shows only comments —
   neither file imports nor calls `auth_envelope`. The classifier
   signature `stalled_premise_drift_diff(row, queue_by_id,
   transitions_by_id)` binds premise → landing record only; it has no
   envelope parameter and no envelope store to consult. Implementing F4
   would require a new envelope-lookup design, i.e. a spec amendment, not
   a review fix.
2. **The concrete REQ-E2 scenario contradicts F4.** `spec.md:41-45`
   ("clean premise stays quiet"): "GIVEN a landing diff identical to its
   authorized premise within the envelope window WHEN the reconciler runs
   THEN no premise-drift diff is emitted". The corpus implements exactly
   this as `test_clean_premise_stays_quiet` (`:210-233`, no envelope
   wired, asserts `None`) and `test_reconcile_end_to_end_clean_quiet`
   (`:431-442`, exit 0, "in sync", no envelope wired). Threading envelope
   presence into the classifier would flip both green tests RED and break
   the full corpus + V31. ("Within the envelope window" is satisfied in
   fixtures by timestamps, not by envelope presence.)
3. **Per the review caution (prefer the spec), the scenario governs.**
   The REQ-E2 normative sentence's parenthetical ("or which carries an
   open authorization with no matching envelope", `spec.md:33`) is
   aspirational but unimplementable as written (see 1) and contradicted by
   the scenario + corpus (see 2). The code's existing
   `landing is None` → stalled branch covers the implementable half
   (open authorization with no landing *record* — pinned by
   `test_open_authorization_without_landing_is_stalled`, `:258`).

No spec, classifier, or test change made for F4 — correct. If a future
wave wants envelope-presence gating in the classifier, it needs a spec
amendment (new REQ or REQ-E2 revision) plus a reconciler envelope lookup;
the F6/F7 scope hardening and F8 trail scan above are the hooks it would
build on.

## 4. Hygiene

- One Rule honored: no `specs/`, `rigs/`, `rosters/`, or `registry/`
  hand-edits (registry re-lag reverted).
- Zero stubs/placeholders/skipped tests; no `TODO`, no `|| true`, no bare
  `except`, no `@unittest.skip` in either test file (re-grepped).
- Secrets: no 40+ runs outside long test-method identifiers
  (repo-precedent convention); fixtures use 16-hex dummy hashes.
- Commit messages use `Refs #15` only. Final `git status --short` shows
  only the two evidence/report files below (left uncommitted for the
  coordinator).

## 5. Files written by this QA (uncommitted)

- `docs/evidence/15-auth-envelope/red-proofs.log` (appended QA-R1 section)
- `docs/reports/15-auth-envelope-r1-qa.md` (this report)

VERDICT: PASS (rework-1 fixes F1–F3, F5–F9 verified + red-proofed; F4 skip agreed with evidence; full acceptance green; no vacuous checks).
