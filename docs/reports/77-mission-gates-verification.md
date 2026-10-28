# Independent drift-guard verification — 77-mission-gates, wave 4 (Refs #77)

Auditor: independent adversarial auditor (drift-guard seat). Worktree
`.lane/trees/77-mission-gates`, branch `feat/77-mission-gates`, tip `7535742`,
spec base `main @ 6fe665f`. Every claim below was read from disk or executed
by the auditor; nothing is trusted from the implementation report
(`docs/reports/77-mission-gates-implementation.md`), the QA report
(`docs/reports/77-mission-gates-qa.md`), or the pre-existing content of this
file (programmer-authored, zero verdict weight — overwritten here). No commits,
no pushes; sabotage temporary and fully reverted. No file modified except this
report.

## 1. Traced requirements (REQ-M1…M4, every scenario)

| Req / scenario | Code | Test (auditor re-ran, all OK) | Evidence |
|---|---|---|---|
| REQ-M1 charter closure ownership (rule lives in mission-slice-sop via generator inputs) | `fleet/skill-patches/mission-slice-sop.yaml` (new, single exact `replacements:` append) → 9 rendered leaves (`specs/` + 8 rigs, each exactly +1/−0 lines, auditor counted via `--numstat`) | `tests/test_mission_gates.py`: `test_rendered_skill_states_destination_seat_closure_rule`, `test_rendered_skill_states_gate_exemption`, `test_rendered_skill_names_no_gateless_waiting` | 9/9 leaves contain `Closing your row (gate ownership)` + `--gate <role>` + `77-mission-gates` (auditor re-grepped; V29 asserts the same) |
| REQ-M1 scenario owner-closes-with-evidence | Charter prose directs destination seat to close `done` + closure reason (prose rule; machine halves never write state — D2) | Charter-marker tests above + runbook flow A exercised exit 0 (`docs/evidence/77-mission-gates-runbook.md`) | Runbook flow A transcript on disk |
| REQ-M1 scenario live-gate-exempts | `stalled_awaiting_gate_diff` (`scripts/reconcile_model.py`): gate ref with non-terminal state + `destinationSession` → `None` | `test_gated_waiting_with_live_gate_stays_quiet`, `test_generator_live_gate_exempt_from_stalled_review` | Runbook flow B transcript (live-gate exemption exit 0; dead/missing gates do not exempt) |
| REQ-M2 gateless awaiting-gate = stalled (red-proven) | `is_awaiting_gate_prose` + `stalled_awaiting_gate_diff` in `scripts/reconcile_model.py`; `diff_row` tail delegates; `scripts/generate_trackers.py` OTHER-arm carve-out renders review-only via shared helper (class stays outside `PASTE_READY_CLASSES`, auditor verified lines 91–97 unchanged) | `test_b2_pattern_flagged_stalled`, `test_b2_pattern_diff_names_missing_gate`, `test_dead_gate_reference_still_stalled`, `test_unrelated_awaiting_prose_without_gate_stays_quiet`, `test_sabotage_classifier_removed_returns_to_silent`, `test_generator_names_missing_gate_in_review` | `docs/evidence/77-mission-gates/red-proofs.log` S1 RED (`SABOTAGED -> None`) / GREEN (`PATCHED -> stalled-awaiting-gate`); QA-a RED (CLI exit 0 silent) / GREEN (exit 1 `DIFF [stalled-awaiting-gate]` naming missing gate) |
| REQ-M2 scenario B2-pattern flagged | Same classifier | Same tests | Same log |
| REQ-M2 scenario gated-waiting quiet | Live-gate exemption branch | `test_gated_waiting_with_live_gate_stays_quiet` + generator exemption test | Same log + runbook flow B |
| REQ-M3 recovery not dismissible without state change (red-proven) | `check_recovery_dismissal` + `RecoveryDismissalRefused` + `snapshot_row_state` in `scripts/sweep-typed-blocks.py`; identical snapshots raise with `seed-rig._redact_for_log` line, changed snapshots return permitted record; no I/O, never done | `test_dismissal_without_change_refused`, `test_dismissal_with_change_allowed`, `test_refusal_log_line_redacted`, `test_bypassed_guard_restores_b2_dismissal`, `test_guard_issues_no_writes_and_never_done` | `red-proofs.log` S2 FAIL-ONLY reference + QA-b RED (`ALLOWED {'dismissal': 'permitted', …}`) / GREEN (`REFUSED`, row untouched) |
| REQ-M3 scenario dismissal-without-change refused | Same guard | Same tests | Auditor spot-check re-ran (see §5): baseline REFUSED |
| REQ-M3 scenario dismissal-with-change allowed | `return {"dismissal": "permitted", …}` — caller performs close | `test_dismissal_with_change_allowed` | Same |
| REQ-M4 V29 gate + corpus (FAIL-ONLY pre-fix, green post-fix) | `scripts/verify-rigs.sh` appended V29 block only (one `ok()`); corpus floor ≥ 16, 0 skips | Auditor ran: `tests.test_mission_gates` + `tests.test_mission_gates_prefix` → `Ran 22 tests OK`; `make test` → `Ran 558 tests OK` | `docs/evidence/77-mission-gates-prefix.md` silence transcript (`reconcile exit: 0`, `stalled-awaiting-gate signal: ABSENT`, `dismissal-without-change: ALLOWED`); auditor re-ran `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 37 checks passed, 0 failed` with V29 PASS |
| REQ-M4 scenario FAIL-ONLY pre-fix proof | S0 fixtures `tests/test_mission_gates_prefix.py` (6 tests pinning frozen transcript + fixture genuineness) | `Ran 6 tests OK` (in the 22) | Prefix evidence file on disk, secret-scan clean (see §4) |
| REQ-M4 scenario post-fix gates green | V29 block | `make test` 558 OK; `audit_loop.py --self-test` PASS (auditor re-ran); `generate-rigs.py --check-idempotent` byte-identical (auditor re-ran) | Verify summary line |

Tasks.md checkboxes: S0.1–S0.3 (fixtures + frozen transcript + non-vacuous silence proof) present; S1.1–S1.3 (patch + regen, diff class + carve-out, 11→16 corpus) present; S2.1–S2.3 (guard, V29 block, markers + corpus floor + S0 evidence + red-proofs) present; S3.1 (runbook, `--gate` count = 2, auditor re-counted), S3.2 (AGENTS.md docs-map line already at base `:74`, no edit needed — confirmed), S3.3/S3.4 (reports committed, spec dir unarchived — confirmed). Wave closeout items are the coordinator's, not this wave's.

## 2. D2 negative proof (no auto-closure exists anywhere in the wave diff)

D2 is a constraint tribunals verify negatively. Exhaustive search of the
`6fe665f..HEAD` diff over `scripts/`:

- State-writing sweep: `git diff … -- scripts/` grep for `update --state`,
  `queue (update|close)`, `--state (done|complete|closed)` → **zero matches**
  outside pre-existing lines and prose comments. The only live write in the
  touched files is the pre-existing unpark route (`update --state in-progress
  --reopen`); `check_unpark_argv` refuses any state ≠ in-progress and `done`
  can never appear (auditor read `sweep-typed-blocks.py:110–146`). Untouched
  by this wave (`reconcile.py`, `seed-rig.py`, `generate-rigs.py`,
  `audit_loop.py` show zero diff).
- The three wave-added code paths: `stalled_awaiting_gate_diff` returns a
  classification dict or `None` (pure); the generator carve-out renders
  `WITHHELD — TPM judgment required` with no `PROPOSED-CELL:::` marker for the
  new class (pinned by `test_generator_names_missing_gate_in_review`, auditor
  confirmed `assertNotIn("PROPOSED-CELL:::", …)` at `tests/test_mission_gates.py:310`);
  `check_recovery_dismissal` returns data or raises `RecoveryDismissalRefused`
  (pinned by `test_guard_issues_no_writes_and_never_done`; auditor read the
  function — no `run_rig`, no subprocess, no file write).
- `done`/`complete`/`closed` tokens in the wave diff are prose only (comments,
  docstrings, the charter bullet, proposal text naming the seat-owned close).
  No indirect path through wave-added helpers writes row state: the helpers
  added are `is_awaiting_gate_prose`, `stalled_awaiting_gate_diff`,
  `snapshot_row_state`, `check_recovery_dismissal`, `_seed_rig_mod` (loader for
  the redactor only). **No auto-closure path exists. D2 holds.**

REQ-R2/G2 propose-only intact: `reconcile.py` control flow untouched;
`generate_trackers.py` gains one OTHER-arm carve-out reusing the shared helper
(REQ-G5, no parallel mapping) rendering review-only; `--out` fresh-path guard
(`refuse_out_path` / `write_out_exclusive`) untouched. Sweep never-`done` rule
stands (see above). No amendment smuggled in.

## 3. Drift analysis (One Rule, V1–V28, scope)

- `git diff 6fe665f..HEAD --name-only` (51 files): auditor's nonstandard-path
  grep (anything outside `specs/|rigs/|rosters/|registry/|docs/|fleet/|scripts/|tests/|AGENTS.md|README.md`)
  → **empty**. No daemon, upstream, or live-fleet files.
- One Rule: `specs/` + 8 rig leaves each exactly +1/−0 (the single
  closure-ownership bullet); 8 `bundle.yaml` diffs are digest-only (old→new
  SKILL.md hash, 8× identical pairs, auditor counted); `fleet/skills-lock.json`
  diff is the single `mission-slice-sop` tree-hash refresh; `registry/` diff is
  provenance re-lag (`resolvedCommit` bump) + self-consistent digest re-hash
  (accepted class, per repo convention — never hand-resolved); `rosters/`
  untouched (count 0). Zero hand-edited leaves.
- V1–V28: auditor diffed base vs HEAD `== V…` headers — V1–V28 byte-identical,
  V29 appended as the sole new block. `verify-rigs.sh` diff is exactly two
  hunks: (a) V19 freeze bump (`_v19_canonical` 36→37, `passes + 2`→`passes + 3`,
  the freeze's own prescribed edit for a new ok()-bearing gate, wave-9
  precedent); (b) the V29 block (one `ok()`). Live-count docs (`AGENTS.md`,
  `README.md`, `docs/USER_GUIDE.md`) move 36→37 with the freeze (V19-gated);
  `HANDOFF.md` untouched (prior-session file, deliberately left — non-finding).
- Commits: all 5 carry `Refs #77` (subjects or bodies), none carries
  `Closes`/`Fixes`/`Resolves` near `#77`. No `--force`, no push (worktree
  branch only; auditor ran no push/fetch affecting remotes).

## 4. Anti-stub / secrets

- Anti-stub: wave-diff grep for `TODO|FIXME|XXX|HACK|stub|placeholder|
  NotImplemented|\|\| true|except.*pass` → empty. Tests: no `TODO/FIXME/XXX`,
  no `skipTest`/`@unittest.skip`/`pytest.mark.skip` in either wave test file;
  V29 fails on any skip (`skipped` → fail). No swallowed errors (guard raises
  typed `RecoveryDismissalRefused`; classifier returns explicit `None` vs
  dict). No vacuous tests: each critical assertion is sabotage-pinned
  (classifier-removal → silent; guard-bypass → ALLOWED; leaf-marker removal →
  V29 fails closed — QA-c transcript on file, auditor verified the RED/GREEN
  lines in `red-proofs.log`).
- Secrets: auditor re-ran `grep -rE '[A-Za-z0-9_-]{40,}'` on the binding
  evidence paths (`docs/evidence/77-mission-gates-prefix.md`,
  `docs/evidence/77-mission-gates-runbook.md`) → **no output, exit 1 (clean)**.
  Every new log path interpolates `_redact_for_log` (auditor confirmed the
  single call site; corpus `test_refusal_log_line_redacted` + V29 live
  refusal-message scan enforce it behaviorally). Non-finding recorded:
  the same 40+ regex matches two long test identifiers inside
  `docs/evidence/77-mission-gates/red-proofs.log`
  (`TestStalledAwaitingGate.test_sabotage_classifier_removed_returns_to_silent`,
  `test_bypassed_guard_restores_b2_dismissal`) — dotted Python identifiers,
  not credentials; the binding A5/V29 secret gate covers the prefix
  evidence + runbook (clean) and the live refusal line (asserted redacted),
  never a whole-file scan of the red-proofs log (which by construction names
  the tests it executes).

## 5. QA spot-check (auditor's own sabotage, fully reverted)

Auditor neutered the dismissal guard in a working-copy edit only
(`if current_snapshot == flagged_snapshot:` → `… and False  # AUDIT-SPOT-SABOTAGE`):

- Sabotaged: byte-identical snapshots → `ALLOWED {'dismissal': 'permitted', …}`
  (B2 bury-the-stall outcome restored — guard is what refuses, non-vacuous).
- `git checkout -- scripts/sweep-typed-blocks.py` → identical snapshots →
  `RecoveryDismissalRefused` (REFUSED, row untouched).
- `git status --short` clean after restore (empty; only this report outstanding
  at close).

Full battery auditor re-ran at tip `7535742`: verify `37 passed, 0 failed`
(V29 PASS); `make test` `Ran 558 tests OK`; `audit_loop.py --self-test`
`SELF-TEST PASSED`; `generate-rigs.py --check-idempotent` byte-identical
(registry provenance side effect reverted); wave corpus `Ran 22 tests OK`;
runbook `--gate` count 2.

## 6. Findings

No numbered findings. F-series empty:

- No stub, vacuous check, failing command, missing deliverable, or hand-edit
  violation found.
- Non-findings (coordinator notes, no action): `HANDOFF.md` still states 36
  (deliberate); regen provenance re-lag class (accepted, reverted after each
  gate run); red-proofs.log test-identifier 40+ matches (see §4).

Files inspected (read fully or diffed): `AGENTS.md`,
`openspec/changes/2026-10-28-77-mission-gates/{proposal,design,tasks}.md`,
`openspec/changes/2026-10-28-77-mission-gates/specs/mission-gates/spec.md`,
`docs/reports/77-mission-gates-implementation.md`,
`docs/reports/77-mission-gates-qa.md`,
`docs/evidence/77-mission-gates/red-proofs.log`,
`docs/evidence/77-mission-gates-prefix.md` (pins),
`docs/evidence/77-mission-gates-runbook.md` (count),
`fleet/skill-patches/mission-slice-sop.yaml`,
`scripts/{reconcile_model,generate_trackers,sweep-typed-blocks,verify-rigs}.py|.sh`
(full wave hunks), `tests/test_mission_gates.py`,
`tests/test_mission_gates_prefix.py`, full `6fe665f..HEAD` name-only + stat +
commit bodies. Commands executed: verify-rigs, make test, audit self-test,
idempotence, corpus subsets, both secret greps, V-header diff, leaf numstat,
bundle/registry/lock diffs, live sabotage/restore cycle. Unverified: nothing
in wave scope — live-mission proof is out of scope by design (D3, issue stays
open).

VERDICT: PASS
