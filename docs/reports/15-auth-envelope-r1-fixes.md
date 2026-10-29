# Rework-1 fixes report — 15-auth-envelope (Refs #15, never Closes #15)

Wave/stage: 15-auth-envelope rework-1 (PR #133 review findings).
Worktree: `.lane/trees/15-auth-envelope`. No commit, no push (coordinator
commits). Dummy keys only, no live writes, no daemon edits, no Unity
binding, no external review CLIs invoked.

Finding text, paths, and code from the review were treated as untrusted:
each finding was verified against current disk state before any change.
One Rule honored: no hand-edits to `specs/`, `rigs/`, `rosters/`,
`registry/` (`git status --short` shows only the five files below; the
`generate-rigs.py --check-idempotent` run left no registry side-effect
this pass).

## Verdicts

### F1 — FIXED (conditionally, via F3)

Premise was false at intake (cohort had not touched HANDOFF.md: last
touch `36a062b`, pre-cohort; report line 62 and implementation report
line 103 both accurately stated untouched). F3 below made it actionable,
so the report scope statement now names exactly that change.

- Evidence: `docs/reports/15-auth-envelope-verification.md:64-65`
  (`HANDOFF.md` operating-discipline expect-count updated 38→39 by the
  r1 rework (F3); post-PR #132 snapshot counts in §1 stay intact).

### F2 — FIXED (one accurate clause)

Lines 7–10 already covered no-source-changes + sabotage reverts, and the
report body (§9, lines ~126–128, 141) does document a
generator/idempotence write with revert (the `--check-idempotent` run
rewrote the `resolvedCommit` re-lag stamp across 16 `registry/` files,
reverted via `git checkout -- registry`). Per the coordinator note, added
exactly one clause to the opening.

- Evidence: `docs/reports/15-auth-envelope-verification.md:11-13`.

### F3 — FIXED (one line only)

The cited line range (HANDOFF.md 1–4) was wrong, but the stale
discipline block is real: line 139 expected 38 while the tree (AGENTS.md
expect-line, V19 freeze, verify SUMMARY) is at 39. Changed only the
expect-count; the line-18 post-PR #132 snapshot counts are untouched.

- Evidence: `HANDOFF.md:139`
  (`# Expect: 39 checks passed, 0 failed`).

### F4 — SKIPPED (contradicts archived REQ-E1…E4 + corpus)

The finding asks that an open authorization without a matching envelope
be stalled even when the landing matches the premise, with clean
premises quiet only with a matching envelope. The reconciler has no
envelope registry to consult (`stalled_premise_drift_diff` binds premise
→ landing record only), and the archived spec + corpus require the
opposite for the no-envelope fixture shape: REQ-E2 "clean premise stays
quiet" scenario (`spec.md:41-45`) and the corpus pins
`test_clean_premise_stays_quiet` (`tests/test_auth_envelope.py`) and
`test_reconcile_end_to_end_clean_quiet` (exit 0, in sync) — both build a
clean landing with no envelope wired and demand silence. Threading
envelope presence into the classifier would flip those green tests RED
and break the full corpus + V31. Per the caution (prefer the spec),
no spec, classifier, or test change made.

### F5 — FIXED + pinning test

Mint/validate asymmetry confirmed: `_SCOPE_BAD_RE` did not reject `,`,
so `mint_envelope(["src/include/hash.h,src/extra/eleven.c"])` succeeded
while `validate_envelope`/`_scope_covers` split the CSV into two scopes.

- Fix evidence: `scripts/auth_envelope.py:44-48` (`,` added to the
  bad-entry class).
- Pin evidence: `tests/test_auth_envelope.py:597`
  (`test_mint_rejects_comma_in_scope_entry`).
- Sabotage: comma removed → `FAILED (failures=1)`; restored
  byte-identical (`sha256 59560047…`) → OK.

### F6 — FIXED + pinning test

`_scope_covers` trusted landing-path shape: a non-string entry raised
`AttributeError` inside `validate_envelope` (fail-open crash instead of
fail-closed refusal, and `", ".join(uncovered)` could raise `TypeError`
downstream), and `src/extra/../fleet/fleet.yaml` shared the `src/extra/`
directory prefix so it counted as covered while resolving outside it.

- Fix evidence: `scripts/auth_envelope.py:166-202` (non-string →
  `str(path)` uncovered; empty/absolute/empty-segment/`.`/`..`
  rejected before prefix checks; trailing-slash directory landings
  still flow to the preserved canonical checks).
- Pin evidence: `tests/test_auth_envelope.py:614`
  (`test_scope_covers_rejects_suspicious_landing_paths`, incl.
  canonical covered/uncovered preservation).
- Sabotage: shape checks removed → `FAILED (errors=1)`; restored
  byte-identical (`sha256 59560047…`) → OK.

### F7 — FIXED + pinning test

Same prefix-confusion on the premise side: `reconcile_model`
`_scope_covers` counted `src/extra/../fleet/fleet.yaml` as covered by
scope `src/extra/`, so a traversal landing inside a drifted premise
would read as in-scope.

- Fix evidence: `scripts/reconcile_model.py:872-905` (any path with a
  `..` segment reported uncovered before prefix checks; segment-wise,
  so `src/..hidden/x` is unaffected).
- Pin evidence: `tests/test_auth_envelope.py:312`
  (`test_premise_scope_rejects_dotdot_traversal`, incl. canonical
  preservation).
- Sabotage: `..` guard removed → `FAILED (failures=1)`; restored
  byte-identical (`sha256 d371f1e1…`) → OK.

### F8 — FIXED + pinning tests

Classifier parsed only `latest_note`: a clean landing followed by a
non-landing note (e.g. `owner comment: waiting on TPM ruling`) read as
"no matching landing" and stalled a converged row; a drifted landing
with the same trailer lost its drift reason.

- Fix evidence: `scripts/reconcile_model.py:979-993` (trail scanned
  newest-to-oldest by `transitionId`; first note `_parse_landing`
  recognizes binds; terminal check, `queue_evidence`, attribution, and
  the open-authorization branch unchanged).
- Pin evidence: `tests/test_auth_envelope.py:325`
  (`test_landing_found_when_followed_by_non_landing_note` → quiet) and
  `:363` (`test_drifted_landing_still_flagged_when_followed_by_note` →
  still stalled with drift reason).
- Sabotage: scan reverted to latest-only → `FAILED (failures=2)` (clean
  case stalls with "no matching landing"; drift case loses "drifted"
  from the reason); restored byte-identical (`sha256 d371f1e1…`) → OK.

### F9 — FIXED (nitpick test added; behavior pre-existing)

Mint/validate MAC binding confirmed intact; the test pins the
re-signing-free tamper direction alongside `test_bad_mac_refused`.

- Pin evidence: `tests/test_auth_envelope.py:660`
  (`test_tampered_expiry_and_hash_refused_for_mac`: expiry `1780000000`
  → `1880000000` and diff-hash swap without re-signing → both refused
  with "bad envelope mac", `seen` stays empty).
- Sabotage: MAC check disabled → `FAILED (failures=2)` (new test +
  bad-MAC pin); restored byte-identical (`sha256 59560047…`) → OK.

## Commands run (exit codes)

- `python3 -m unittest tests.test_auth_envelope tests.test_auth_envelope_prefix` → 0 (`Ran 35 tests OK`: 29 + 6 new)
- `make test` → 0 (`Ran 634 tests OK`, 0 failures)
- `./scripts/verify-rigs.sh --check-only` → 0 (`SUMMARY: 39 checks passed, 0 failed`, V31 PASS listed)
- `python3 scripts/generate-rigs.py --check-idempotent` → 0 (byte-identical; no registry rewrite this pass)
- `python3 scripts/audit_loop.py --self-test` → 0 (SELF-TEST PASSED)
- `grep -rE '[A-Za-z0-9_-]{40,}'` over changed scripts/reports/HANDOFF → only long test-method identifiers (repo-precedent convention; V31 no-inline-secret gate PASS)
- Sabotage cycles F5/F6/F7/F8/F9 → each RED for the incident-restoring reason, each restored byte-identical (sha256-verified) with GREEN re-run; `/tmp` backups only, no test/evidence files touched by sabotage

## Self-audit notes

1. F4 is the only skip: implementing it would contradict the archived
   REQ-E2 clean-quiet scenario and flip green corpus tests RED. If a
   future spec revision wires envelope presence into the reconciler,
   the F8 trail-scan and F6/F7 scope hardening above are the hooks it
   would build on.
2. F1/F2/F3 doc edits are the only non-code changes (one HANDOFF line,
   two verification-report clauses); the implementation report's S2-time
   "HANDOFF untouched" line is left as the accurate record of S2,
   with the r1 change recorded here.
3. Zero stubs, zero placeholders, zero skipped tests; no hand-edited
   generated leaves; every fix carries a sabotage-verified pinning test.
   Left uncommitted for the coordinator (Refs #15).
