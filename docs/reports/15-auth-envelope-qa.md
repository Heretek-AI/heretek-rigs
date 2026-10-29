# QA report — 15-auth-envelope (Refs #15, never Closes #15)

Wave/stage: `15-auth-envelope` (change `2026-10-29-15-auth-envelope`).
Worktree: `.lane/trees/15-auth-envelope`, committed implementation
`01286d2` verified clean at QA start (`git status --short` empty).
No Unity binding for this wave (repo fixtures-only; no `unity_*` involved).

## Baseline acceptance (S0 → S3, unmodified tree, all EXIT 0 unless noted)

| # | Command | Result |
|---|---|---|
| S0 | `python3 -m unittest tests.test_auth_envelope_prefix -v` | 8 tests OK |
| S0 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/15-auth-envelope-prefix.md` | EXIT 1 (clean, no match) |
| S0/S1/S2/S3 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 39 checks passed, 0 failed`, V31 PASS, V1–V30 intact (39-tree: S2 already applied; S0-time 38-baseline is recorded in the frozen prefix transcript) |
| S1 | `python3 -m unittest tests.test_auth_envelope -v` | 21 tests OK (every REQ-E1/E2/E3 scenario listed and passing) |
| S1/S3 | `python3 scripts/generate-rigs.py --check-idempotent` | EXIT 0, byte-identical (see advisory below) |
| S2 | `make test` | `Ran 628 tests OK`, 0 failures |
| S2 | `python3 scripts/audit_loop.py --self-test` | SELF-TEST PASSED |
| S3 | `grep -c -- 'diff-hash' docs/evidence/15-auth-envelope-runbook.md` | 1 (>=1) |
| S3 | `grep -c -- 'premise age' docs/evidence/15-auth-envelope-runbook.md` | 4 (>=1) |

## Red-proofs (7/7 RED for the right reason, all restored GREEN)

Full transcripts in `docs/evidence/15-auth-envelope/red-proofs.log`
(QA re-verification section). Each sabotage was a temporary tracked-file
edit reverted with `git checkout -- <file>`; `git status --short` empty
after every restore (final state: only this report + the log appendix
uncommitted, left for the coordinator).

| Probe | Sabotage | RED (right reason) | GREEN after restore |
|---|---|---|---|
| S1a drift classification | `diff_row` tail → `return None` | corpus EXIT 1, 2 failures, reconcile silent "in sync" | 21 OK |
| S1b clean quiet | quiet-branch → `if False` (force over-flag) | 3 quiet tests EXIT 1, 2 failures (both clean-quiet catch the flag; no-premise path unaffected) | 21 OK |
| S1c landing validation | `validate_envelope` entry → forced `authorized` | envelope class EXIT 1, 9/11 failures | 21 OK |
| S1d replay | `if nonce in seen:` → `if False and …` | `test_replayed_nonce_refused` EXIT 1 | OK |
| S1d expiry | `if int(now) >= int(expires):` → `if False` | `test_expired_envelope_refused` EXIT 1 | 21 OK |
| S2 dismissal guard | `check_recovery_dismissal` identical-snapshot → `if False` | EXIT 1, `RecoveryDismissalRefused not raised` | 21 OK |
| V31 gate itself | same validation bypass | verify EXIT 1, `SUMMARY: 38 passed, 5 failed` — 4 live-behavior FAILs (drift/scope/expiry/replay AUTHORIZED) + corpus FAIL | 39/0 V31 PASS |

Vacuous checks: **none** — every acceptance check turned RED under a
minimal targeted defect and GREEN on restore.

## Coverage advisories (no test changes made — reported, not patched)

1. `generate-rigs.py --check-idempotent` exits 0 (two runs byte-identical)
   but is **not side-effect-free**: it rewrote the provenance re-lag stamp
   (`resolvedCommit` 2bf02ac→01286d2) across 16 `registry/` files. Reverted
   via `git checkout -- registry`; committed registry state (the known
   accepted re-lag) preserved. Recommendation: run idempotence immediately
   before a status check, or let the coordinator run it post-commit.
2. S1b's committed corpus already contains the classifier-removal pinning
   test (`test_classifier_removal_is_silent`); the QA over-flag probe outran
   the suite only in direction (over-flag vs removal) — both directions are
   now evidenced in the log. No new tests added (QA does not patch tests).
3. Secret-scan scope: evidence + scripts carry zero 40+ runs (S0 grep EXIT 1
   re-verified; V31 no-inline-secret check PASS). Long dotted identifiers in
   the red-proofs log stay under the 40-run floor per the wave's convention.

## Verdict

All S0→S3 acceptance commands green on the unmodified tree; all 7 sabotage
probes RED for the incident-restoring reason and GREEN after revert; final
`git status --short` shows only `M docs/evidence/15-auth-envelope/red-proofs.log`
and this new report (uncommitted, coordinator commits). No pushes. No code
or test files modified.

`VERDICT: PASS` (Refs #15)
