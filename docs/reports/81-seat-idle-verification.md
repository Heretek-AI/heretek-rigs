# Drift-guard verification — 81-seat-idle rework-1 (Refs #81)

Independent adversarial audit of rework cycle 1, run 2026-10-29 in worktree
`.lane/trees/81-seat-idle`, branch `feat/81-seat-idle`, HEAD `d9cbdb4`.
Base of prior PASS verdict: `7c211b2`. New commits since base: `7980d7b`
(archive + spec promotion), `367cb45` (F1–F5 fixes), `f23a66d` (QA
re-verification), `84980d9` (F2/F3/F4 pins), `d9cbdb4` (pins confirmation).
Nothing below is trusted from reports — every claim re-verified against
current code, tests re-run, sabotages re-performed by this auditor.
`git status --short` was clean on entry; the only tree mutations during
this audit were the idempotence-check registry re-lag (reverted via
`git checkout -- registry/`), two live sabotages (both fully reverted,
byte-identical restore confirmed via `diff -q` against backup), and this
report (the auditor's sole allowed write). No commits, no pushes.

Prior verdict file (PASS at `37ee746`) was read and then fully
re-verified, not trusted — this report overwrites it entirely.

## 1. Fix record vs diff (all five fixes real)

`git diff 7c211b2..HEAD --name-only -- scripts/ tests/` =
`scripts/reconcile_model.py`, `tests/test_seat_idle.py`,
`tests/test_seat_idle_prefix.py` only. Behavior footprint matches the
fix record exactly.

- **F1 (evidence invocation result) — REAL.** `docs/evidence/81-seat-idle-prefix.md`
  carries the appended dummy-invocation block (`validate_handoff_source
  present: False` + `handoff invocation result: recorded source operator
  (rule ABSENT, no relabel)`) and `tests/test_seat_idle_prefix.py`
  carries `test_evidence_records_daemon_handoff_invocation_result`
  asserting both lines. All five V30 evidence markers byte-intact
  (V30 green, see §3).
- **F2 (wake gate) — REAL and causal.** `_WAKE_NOTE_RE`
  (`wake|woken|woke|released?|resumed?|unparked?`) gates the `wake_ts`
  assignment in the parked-trail branch; docstring updated. Auditor
  sabotage (gate removed): pin test RED —
  `AssertionError: '2026-10-23T21:34:20.000Z' is not None` (heartbeat
  leaks into `wake_ts`, the exact F2 defect). Restored → GREEN.
- **F3 (review-only render) — REAL.** `render_diff` early-returns for
  `class == "stalled-idle-park"` with `NEEDS-HUMAN-REVIEW` +
  `SUGGESTED (not paste-ready)` and no `PROPOSED-CELL` / `converged`
  markers; all other classes fall through unchanged. No committed test
  asserts `PROPOSED-CELL` for idle-park (auditor grep: zero hits outside
  the new pin); CLI presence assertions (`stalled-idle-park`,
  `park-to-wake`) survive via header/attribution lines. No spec/V30
  conflict: REQ-I2 demands route-for-review + report-only, which the old
  `PROPOSED-CELL` + `converged` output contradicted.
- **F4 (mixed-note work evidence) — REAL and causal.** `_WORK_ACTION_RE`
  (`verdict|filed|files|QA PASS|PLACED|DONE`) + shared `_is_non_work_only`
  helper consumed by both `trail_has_work_action` and the `work_ts` leg
  of `attribute_idle_latency`. Auditor sabotage (tail forced to
  `return True`): pin test RED — `AssertionError: False is not true`
  (mixed note excluded, the exact F4 defect). Restored → GREEN.
- **F5 (interval arithmetic) — REAL.** Evidence line now reads `(+84s
  from claim, +53s park-to-wake)`. Hand-verified: claim 21:33:29 →
  wake 21:34:53 = 84s; park 21:34:00 → wake = 53s. Both `WAKE_TS`
  constants byte-identical (`tests/test_seat_idle.py:58`,
  `tests/test_seat_idle_prefix.py:56`, both
  `2026-10-23T21:34:53.000Z`).

## 2. Pins genuinely non-vacuous

- P2 (`test_heartbeat_only_trail_leaves_wake_unset`) and P4
  (`test_mixed_note_counts_as_work_in_both_paths`): auditor's OWN
  sabotages above turn each RED for the right reason and GREEN on
  restore. Non-vacuous, independently proven.
- P3 (`test_idle_park_render_is_review_only`): QA's pins-confirmation
  entry records independent RED-then-GREEN sabotage
  (`if False:` neutering → `'PROPOSED-CELL' unexpectedly found ...;
  1 failure`); code read confirms the pin asserts absence of both
  markers plus presence of `SUGGESTED (not paste-ready)` and a
  stale-state control keeping both markers. Pattern confirmed; not
  re-duplicated to avoid redundant tree churn.
- P1 (F1 frozen test): QA-R1 entry proves RED on line alteration;
  assertion text matches the evidence block verbatim (auditor read both).

## 3. V30 append-only, SUMMARY 38/0 re-run by auditor

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 38 checks passed,
  0 failed`, V30 PASS (auditor-run, exit 0). No V1–V29 renumber/reword:
  `git diff 7c211b2..HEAD` touches no line of `verify-rigs.sh`.
- `python3 -m unittest tests.test_seat_idle tests.test_seat_idle_prefix`
  → 37 tests OK (27 + 10; was 33 at base: +1 F1 pin, +3 F2/F3/F4 pins).
- `make test` → 599 tests OK (105s, 0 failures; was 595 at base:
  +1 F1, +3 pins).
- `python3 scripts/generate-rigs.py --check-idempotent` → pass, exit 0
  (known `resolvedCommit` re-lag dirtied 16 registry files; reverted via
  `git checkout -- registry/`, status clean).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`.

## 4. Propose-only / never-done intact; wave-9 handling unchanged

- `git diff 7c211b2..HEAD -- scripts/send_identity.py
  scripts/generate_trackers.py scripts/verify-rigs.sh fleet/` is EMPTY:
  daemon-source validation, tracker carve-out, V30, and generator inputs
  untouched by rework. `TestDaemonSource` re-run: 5 OK, genuine
  operator relay intact.
- `stalled_idle_park_diff` still returns a review-routed dict only;
  `attribute_idle_latency` still a pure report field; the only new
  `render_diff` path returns early with review-routing text. No new
  write paths in the rework hunks (the `os.open O_EXCL` writer is the
  pre-existing propose-only fresh-file mechanism).
- `TestIdleParkNonDismissibleRecovery` green within the 37-test run;
  no `done` permit, no queue/tracker writes added.

## 5. Scope creep: none (archive + docs-map are sanctioned closeout)

Full `7c211b2..HEAD` file list beyond §1: `AGENTS.md` (1-line docs-map
path update, S3.2-sanctioned), `openspec/changes/archive/…` rename +
`openspec/specs/seat-idle/spec.md` promotion (`7980d7b`), `tasks.md`
checkbox flips (`[ ]`→`[x]`), three audit artifacts (r1-fixes, r1-qa,
red-proofs append). Archive bodies verified identical to the change
spec (only the standard `openspec archive` header + TBD Purpose line
differ); proposal/design/spec are pure renames (0-line content diff).
The archive is explicitly allowed by the tasks' own rule ("Nothing
under `openspec/` changes after this spec except the end-of-wave
archive"). No unrelated behavior change anywhere in the diff.

## 6. Secrets discipline

`grep -rEn '(ghp_|gho_|github_pat|sk-|AKIA|BEGIN [A-Z ]*PRIVATE KEY)'`
over both test files, `reconcile_model.py`, prefix evidence, r1-fixes,
r1-qa, red-proofs.log → exit 1 (clean). The naive 40+ run pattern hits
only long test identifiers (e.g. pin test names) — false positives, not
credentials; V30's own zero-secret grep passes. No `Closes #81` closing
keyword anywhere (only `never Closes #81` prose, which is mandatory).
`git status` showed no stray scratch files; sabotage backup lived in
`/tmp`, never in-tree.

## 7. Anti-stub scan

`grep -rEn 'TODO|FIXME|skipTest|@unittest\.skip|\|\| true|except.*: *pass'`
over `reconcile_model.py`, both test files, prefix evidence, r1 reports,
red-proofs.log → exit 1 (clean). New helpers are real regexes grounded
in corpus vocabulary; new tests assert concrete values (timestamps,
marker absence/presence, boolean work verdicts), not tautologies. No
hand-edited generated leaves (`fleet/fleet.yaml` untouched; registry
has no `DIRTY` stamps — auditor grep clean).

## 8. Generator provenance

No `DIRTY-` stamps in registry. `--check-idempotent` passes
byte-identical across two consecutive runs (registry re-lag reverted).
`audit_loop.py --self-test` green.

## Observation (non-binding, not a finding)

`docs/reports/81-seat-idle-implementation.md:18` still repeats the
pre-fix `wake +53s` figure (pre-existing stale prose, untouched by
rework per the minimal-diff rule, already flagged in the fix record and
QA advisories for the coordinator). Style/prose nit, no spec clause
violated — correctly left for coordinator decision, not this audit.

## Commands run by the auditor (all on the unmodified tree except noted)

- `python3 -m unittest tests.test_seat_idle tests.test_seat_idle_prefix` → 37 OK
- F2 sabotage (gate removed) → pin RED (`...21:34:20.000Z is not None`); restored → OK
- F4 sabotage (`_is_non_work_only` neutered) → pin RED (`False is not true`); restored → OK (`diff -q` confirms byte-identical restore; `git status` clean)
- `make test` → 599 OK; `./scripts/verify-rigs.sh --check-only` → 38/0 V30 PASS
- `generate-rigs.py --check-idempotent` → pass (registry re-lag reverted); `audit_loop.py --self-test` → PASSED
- `TestDaemonSource` → 5 OK; secret/stub/DIRTY/`Closes #81` greps as recorded above

VERDICT: PASS
