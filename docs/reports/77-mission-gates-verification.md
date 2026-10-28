# Drift-guard verification — 77-mission-gates (Refs #77)

Wave-end re-verification of the 77-mission-gates change set against the
repo's audit-baselined gates. Read from disk outputs, not summaries.

## Gate outputs (final, wave end)

| # | Command | Output |
|---|---|---|
| 1 | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 37 checks passed, 0 failed`, V29 PASS line present, exit 0 |
| 2 | `make test` | `Ran 558 tests`, `OK` (0 failures, 0 errors), exit 0 |
| 3 | `python3 scripts/audit_loop.py --self-test` | `SELF-TEST PASSED`, exit 0 |
| 4 | `python3 scripts/generate-rigs.py --check-idempotent` | `idempotence check passed (two consecutive runs byte-identical)`, exit 0 |
| 5 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md docs/evidence/77-mission-gates-runbook.md` | no output (exit 1) |
| 6 | `grep -c -- '--gate' docs/evidence/77-mission-gates-runbook.md` | `2` (>= 1) |
| 7 | `python3 -m unittest tests.test_mission_gates tests.test_mission_gates_prefix` | `Ran 22 tests`, `OK` |

## V1–V28 integrity (append-only)

- `git diff 6fe665f -- scripts/verify-rigs.sh` shows exactly two hunks:
  (a) the V19 freeze bump (`_v19_canonical` 36 → 37, `passes + 2` →
  `passes + 3`, comment names V29 as the second post-freeze ok()-gate —
  the freeze's own prescribed edit, also applied by wave 9 for V28);
  (b) the appended `== V29. Mission-Gate Ownership ==` block (one `ok()`).
  No V1–V28 header renumbered or reworded (121 insertions, 4 deletions,
  all inside the two hunks).
- V28 corpus still runs its own floor (`tests.test_send_identity`, >= 20,
  28 tests passing per the V28 PASS line); V19 stale-count guard green
  (live docs state 37, no stale 64/0.6.11/31 strings).
- Existing suites intact: `tests.test_reconcile`,
  `tests.test_generate_trackers`, `tests.test_sweep_typed_blocks` all pass
  unmodified (81 tests combined with the new corpus at S1 time; 558 total
  at wave end).

## Scope and safety pins re-checked

- D2 (no auto-done): nothing written in this wave transitions any row to
  done/complete/closed or dismisses anything. `diff_row` /
  `stalled_awaiting_gate_diff` are pure classification; `render_proposal`
  review renders carry no `PROPOSED-CELL:::` marker for the new class
  (proven by `test_generator_names_missing_gate_in_review`);
  `check_recovery_dismissal` returns data or raises (proven by
  `test_guard_issues_no_writes_and_never_done`); sweep unpark route still
  pins `in-progress` and refuses `done`.
- Propose-only intact: `reconcile.py` / `generate_trackers.py` control
  flow unchanged (one OTHER-arm carve-out that reuses the shared helper
  and renders review-only); `--out` fresh-path guard untouched.
- One Rule intact: no hand edits under `specs/`, `rigs/`, `rosters/`,
  `registry/` (regen diff was patch-caused leaves + lock tree-hash +
  accepted digest/provenance re-lag; verified by drift scan at S1).
- Secrets: real keys never touched (verified permissions only at session
  start per AGENTS.md); every new log path interpolates
  `_redact_for_log` output; evidence files carry dummy ids only (gate 5).
- `openspec/changes/2026-10-28-77-mission-gates/` left unarchived for the
  coordinator's merge wave.

## Red-proofs on file

`docs/evidence/77-mission-gates/red-proofs.log`: S1 classifier-removal RED
(`SABOTAGED -> None`) / GREEN (`PATCHED -> stalled-awaiting-gate`),
executable as `test_sabotage_classifier_removed_returns_to_silent`; S2
FAIL-ONLY pre-fix reference (S0 transcript: silence exit 0, dismissal
ALLOWED), executable as `test_bypassed_guard_restores_b2_dismissal`.

VERDICT: PASS
