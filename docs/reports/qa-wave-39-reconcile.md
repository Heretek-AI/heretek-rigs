# QA report — wave-39-reconcile (issue #39, change remediate-39-reconcile)

- Stage/wave: `wave-39-reconcile` · Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile`
- Implementation under test: `38262a0` (`feat(39-reconcile): read-only tracker-vs-queue reconcile diff command`)
- Date (UTC): 2026-10-23 · Verifier: QA seat (sabotage-only; no commit/merge/push)
- Evidence: `docs/evidence/wave-39-reconcile/red-proofs.log` (+ `/tmp/opencode/hr39qa/` scratch fixtures, live-run output)
- Spec read: `AGENTS.md`, `proposal.md`, `specs/tracker-reconcile/spec.md` (REQ-R1..R4), `design.md`, `tasks.md` (T1–T6);
  implementation report `docs/reports/wave-39-reconcile-implementation.md`; `gh issue view 39` (OPEN, options (a)/(b)).

## Verdict: QA-CLEAN (no blocking findings)

All acceptance checks pass on the unmodified tree, and every load-bearing check was proven to fail
under minimal targeted sabotage (restored byte-identical afterwards). Two non-blocking findings (F1, F2) below.

## Per-check results

| # | Check | Result | Exact command / output |
|---|---|---|---|
| 1 | `make verify` — SUMMARY 26/0 | PASS | `make verify` → `SUMMARY: 26 checks passed, 0 failed.`, exit 0. V10: `[PASS] Tracker-vs-queue reconcile (issue #39) green`. Advisories only: live-health heartbeat WARN + seat-idleness SKIP (warn-first, unchanged). |
| 2 | V1–V9 behavior-identical | PASS | `git diff HEAD~1 --numstat -- scripts/verify-rigs.sh` → `68 additions / 0 deletions`; zero removed lines. |
| 3 | V10 single `ok()` | PASS | Exactly one code-level `ok(...)` in the appended block; 4 `fail(...)` gates, no pass inflation. |
| 4 | Full suite green | PASS | `make test` → `Ran 85 tests ... OK`, exit 0 (incl. 15 new `test_reconcile.py`). |
| 5 | `openspec validate` | PASS (+F2) | → `Change 'remediate-39-reconcile' is valid`, exit 0. Load-bearing proven: removing `specs/`+`proposal.md` → exit 1 `must have at least one delta` (restored, re-valid). |
| 6 | REQ-R1 / T1: diffs name file+row+both values | PASS | `test_pre_convergence_reports_at_least_seven_diffs` green; QA replicated per-class with synthetic fixtures, each firing exit 1. |
| 7 | Drift class (a): stale-state fires | PASS (RED-proof) | Scratch `STAGED awaiting QA` vs closed queue → exit 1, `stale-state` + slice. |
| 8 | Drift class (a): parked-satisfied-but-tracker-silent fires | PASS (RED-proof) | Scratch `PARKED blocked on QA gate` vs closed queue → exit 1. Code sabotage (`if False and norm["parked"]`) → test FAILED exit 1 (rule load-bearing); restored byte-identical, 15/15 OK. |
| 9 | Drift class (a): missing-convergence-annotation fires | PASS (RED-proof) | Note 3 vs latest 5 → exit 1, named class. |
| 10 | Drift class (a): tracker-row-without-qitem fires | PASS (RED-proof) | Both shapes (em-dash like live W2-01; qitem with no queue entry) → exit 1, named diff, never dropped (REQ-R4 scenario). |
| 11 | REQ-R3 / T4: converged pair in sync; replay-to-zero | PASS | Scratch converged row → exit 0 `in sync`. `test_applying_proposals_converges_to_zero_diffs` green. |
| 12 | REQ-R2 / T2: read-only + paste-ready proposals | PASS | Tracker bytes identical before/after; 7x `PROPOSED Status cell:`. V10 offline leg re-proves read-only by byte comparison. |
| 13 | REQ-R4 / T3: unparseable row fail-closed w/ file:line | PASS (RED-proof) | Broken pipe structure → exit 2 `UNPARSEABLE ROW '<file>:6' (expected 5 cells, got 2)`; never skipped. |
| 14 | REQ-R4 / T3: missing tracker fail-closed | PASS (RED-proof) | Nonexistent path → exit 2 naming it; no false `in sync`. |
| 15 | REQ-R4 / T3: unreachable queue fail-closed | PASS | `test_unreachable_queue_fails_closed` and `test_live_mode_unreachable_rig_fails_closed`; suite green. |
| 16 | Exit-code contract non-vacuous | PASS (RED-proof) | Sabotage `return 1`→`return 0` in diffs branch → drifted fixture exited 0, tripping V10's `returncode != 1` gate. Restored byte-identical. |
| 17 | `--out` no-overwrite guard (f) | PASS (RED-proof) | `--out` == scratch tracker-shaped path → exit 2 `refusing to write proposal to input tracker path`; bytes untouched. Scratch path only. |
| 18 | Live read-only run (g) vs mission trackers+queue | PASS | Daemon up (port 7433). 3 trackers vs 21 queue rows → exit 1, `14 diff(s) across 23 row(s); TPM approval required — no files modified.` Recorded only, NOT acted on. Mission md5s identical after: all 3 `OK`. |
| 19 | T5 `make reconcile` wiring, non-masking | PASS | `make reconcile TRACKER=<mission wave1>` printed live diffs; make exit 2 (tool exit 1 propagated). Makefile delta additive only. |
| 20 | Deferrals spec-sanctioned (not silent drops) | PASS (+F1) | Generation deferral explicitly sanctioned (proposal Non-goals + design "Why diff-first"; follow-up named). Report filename follows stage binding. T6 filing half-open by record → F1. |

No vacuous checks: every gate above that can go RED was driven RED (or driven RED around, for green-path checks).

## Findings (non-blocking)

- **F1 (advisory): T6 half-open — `remediate-39-generate` follow-up issue not filed.** Tasks.md T6 asks to file the
  deferred-generate design sketch as an issue. The implementation report explicitly records the non-filing with
  rationale (issue filing is a network/state-changing act outside implementation scope; left for the TPM) and the
  sketch itself is preserved in-repo (`design.md`: row-model sketch + "follow-up generate change MUST consume this
  diff spec's row model"). Nothing lost or silent; one `gh issue create` by the TPM closes it. Recommend: TPM files
  the issue (or explicitly accepts the deferral) before closing #39.
- **F2 (observation): `openspec validate` leniencies.** Proven by sabotage: broken `### Requirement:` heading →
  silently INFO-ignored, exit 0; `tasks.md` absent → exit 0; one `#### Scenario:` header broken → exit 0. The check is
  load-bearing at the delta level (no `specs/` → exit 1) but does not enforce tasks presence, heading strictness, or
  per-requirement scenario coverage. No action required for this stage; noted for validator hardening elsewhere.

## Paths

- Implementation: `scripts/reconcile.py` (new), `tests/test_reconcile.py` (new, 15 tests), `Makefile` (+reconcile
  target), `scripts/verify-rigs.sh` (V10 only), `docs/reports/wave-39-reconcile-implementation.md`.
- QA deliverables (only tree modifications): `docs/evidence/wave-39-reconcile/red-proofs.log`,
  `docs/reports/qa-wave-39-reconcile.md`.
- Final `git status --short`: clean except the two QA files above. No commit/merge/push. Mission repo untouched.
