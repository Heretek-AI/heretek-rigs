# Drift-guard verification — 81-seat-idle (Refs #81)

Independent adversarial audit run 2026-10-29 in worktree `.lane/trees/81-seat-idle`
at HEAD `37ee746` (implementation `2bf02ac` + clean-regen leaves `9461324` +
red-proofs/QA `37ee746`). Every claim below was verified against current code,
not trusted from reports. `git status --short` was clean on entry; the only
tree mutation during this audit was the idempotence-check registry re-lag
(API-known, reverted via `git checkout -- registry/`) plus two live sabotages,
both fully reverted. No commits, no pushes.

## 1. Spec trace (REQ-I1…I4 → code → test → evidence)

| Req | Code | Test (re-run by auditor) | Evidence |
|---|---|---|---|
| REQ-I1 charter one-turn rule, generated not hand-edited | `fleet/skill-patches/queue-handoff.yaml` (`replacements`, fail-closed one-hit) → regen; all 9 leaves (`specs/` + 8 rigs) carry `81-seat-idle` + `one turn` + `first work action` (auditor `grep -c` = 1 in each of the 9 leaves) | `TestCharterRule` 4 tests OK (patch input + rendered + named + all-nine) | runbook Flow A verbatim exit-0 negative control |
| REQ-I2 claim-then-park ⇒ `stalled-idle-park` + attribution, propose-only; obligation-free idle and live-gate waiting quiet | `scripts/reconcile_model.py`: `is_idle_park_prose` + `trail_has_claim` / `trail_has_work_action` (only known non-work classes excluded, unfamiliar note counts as work — fail-closed against over-flagging) + `attribute_idle_latency` (report-only) + shared `stalled_idle_park_diff`; `diff_row` tail tries gate then idle-park; `render_diff` appends attribution line. `scripts/generate_trackers.py` OTHER-arm carve-out consumes the SAME helper (no parallel mapping) and renders review-only (class stays outside `PASTE_READY_CLASSES`) | `TestStalledIdlePark` 7 + `TestIdlePark…` quiet guards OK; CLI exit-1 with attribution OK; report-only inspection OK; auditor re-ran full `tests.test_seat_idle` (24 OK) + `tests.test_seat_idle_prefix` (9 OK) | prefix.md Transcript 1 (`reconcile exit: 0 / idle-park signal: ABSENT`) + Transcript 2 (attribution ABSENT); runbook Flow B verbatim exit-1 diff with `park-to-wake` attribution; #15/#17 sample `park_to_wake_s: 53.0, work_s: 0` |
| REQ-I3 daemon source `daemon:stuck-sweep`, never `operator`; wave-9 genuine-operator handling unchanged | `scripts/send_identity.py`: `DAEMON_SOURCE` + `validate_handoff_source` (daemon origin + non-daemon label → relabeled with `_redact_for_log` line; honest daemon persists; genuine `operator`→`operator` persists; unknown origin raises fail-closed). Wave-9 `mint_attestation` / `verify_attestation`, `attested`/`rejected`/`unverified` untouched in same file | `TestDaemonSource` 5 OK incl. genuine-operator-relay + redaction + S1d sabotage test | prefix.md Transcript 3 (`daemon source rule: ABSENT / recorded source: operator`); runbook Flow C C1–C4 verbatim |
| REQ-I4 V30 gate + corpus | `scripts/verify-rigs.sh` appended `== V30. Seat Idle-Park ==` block only; V19 freeze 37→38 (`passes + 4`) + 3 live-count docs; `HANDOFF.md` untouched (prior-session file) | corpus 24 ≥ 16 floor, 0 skips; auditor: `make test` → `Ran 595 tests OK` | S0 silence transcript + zero-secret grep lines pinned in V30 |

Scenario coverage: flagged (Mission-A fixture → `stalled-idle-park`), legitimate-idle-quiet, live-gate-quiet, worked-claim-quiet, attribution-report-only, relabel/persist/untouched/redaction, non-dismissible recovery (refused while byte-identical, permitted after owner action, never `done`).

## 2. Auditor red-proof sabotages (own, temporary, fully reverted)

- **DG-S1a classifier removal**: injected `return None` at top of `stalled_idle_park_diff` → `test_mission_a_pattern_flagged_stalled` FAILED (`unexpectedly None`, silent — the exact pre-fix gap). Restored → OK. `git status` clean after.
- **DG-S1d operator-label bypass**: injected early `persisted` return in daemon arm of `validate_handoff_source` → `TestDaemonSource` FAILED (failures=3, `operator` collision). Restored → 5 OK. `git status` clean after.

Both RED for the right reason, GREEN on restore. Non-vacuous. (QA's five logged sabotages in red-proofs.log — S1a, S1b/S1c both-ways, S1d, S2 dismissal, V30 marker — were read and are consistent with the code; not re-run in full to avoid duplicating tree churn.)

## 3. V30 append-only

`scripts/verify-rigs.sh` diff vs base `8dec2ed`: the ONLY removed non-comment lines are the three V19-freeze lines (`_v19_canonical = 37`, `passes + 3` + its comment) replaced by the freeze's own bump rule (`38`, `passes + 4` + comment). No V1–V29 block renumbered or reworded. Auditor run: `SUMMARY: 38 checks passed, 0 failed`, V30 PASS listed. `AGENTS.md`/`README.md`/`docs/USER_GUIDE.md` 37→38 count moves are V19-gated.

## 4. Propose-only / never-done intact

`stalled_idle_park_diff` returns a review-routed diff only; `attribute_idle_latency` is a pure report field; the generate_trackers carve-out renders `WITHHELD — TPM judgment required`; `check_recovery_dismissal` refuses identical-snapshot dismissal (never permits `done` — `TestIdleParkNonDismissibleRecovery.test_guard_issues_no_writes_and_never_done` OK). No tracker or queue writes in the diff. No daemon edits, no auto-wake, no upstream filing.

## 5. Wave-9 attestation unchanged for genuine operator relays

`validate_handoff_source(origin="operator", presented="operator")` → persisted `operator` (auditor re-ran `TestDaemonSource` incl. `test_genuine_operator_relay_untouched`, OK); mint/verify semantics, `attested`/`rejected`/`unverified` markers all present per V30 assertions. Unknown origin raises fail-closed.

## 6. Secrets discipline

`grep -rE '[A-Za-z0-9_-]{40,}'` over prefix.md, runbook, red-proofs.log, implementation and QA reports → exit 1 (clean). New log paths go through `_redact_for_log`; refusal-log redaction covered by tests. No bearer-shaped runs in `send_identity.py` (V30 asserts). No real credentials touched.

## 7. Anti-stub scan

No `TODO`/`FIXME`/`skipTest`/`@unittest.skip`/`|| true`/bare-`except-pass` in `reconcile_model.py`, `send_identity.py`, `generate_trackers.py`, both test files, or the skill patch. Tests assert concrete values (class names, attribution numbers, relabel actions, refusal exceptions), not tautologies. Zero hand-edited generated leaves (all `specs/`/`rigs/`/`rosters/`/`registry/` changes via regen; `fleet/fleet.yaml` untouched).

## 8. Generator provenance

No `DIRTY-` stamps anywhere in registry (`grep DIRTY` clean — committed-tree regen, unlike the dev-dirt self-audit baseline). `generate-rigs.py --check-idempotent` → byte-identical, exit 0 (the check's known `resolvedCommit` re-lag dirtied 16 registry files; reverted via `git checkout -- registry/`, status clean; 38/0 was proven on the committed tree before and QA after). `audit_loop.py --self-test` → `SELF-TEST PASSED`, exit 0.

## Commands run by the auditor (exit codes)

- `./scripts/verify-rigs.sh --check-only` → 0, `SUMMARY: 38 checks passed, 0 failed`, V30 PASS
- `python3 -m unittest tests.test_seat_idle tests.test_seat_idle_prefix` → 0, 33 OK
- `make test` → 0, `Ran 595 tests OK`
- `python3 scripts/generate-rigs.py --check-idempotent` → 0 (registry re-lag reverted)
- `python3 scripts/audit_loop.py --self-test` → 0, `SELF-TEST PASSED`
- DG-S1a / DG-S1d sabotages → RED as recorded above, restored GREEN, tree clean
- `git status --short` after all reverts → clean apart from this report

No `Closes #81` anywhere (only `never Closes #81` prose); issue correctly stays open.

VERDICT: PASS
