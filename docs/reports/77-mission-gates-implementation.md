# Implementation report — 77-mission-gates, wave 4 (Refs #77)

Branch `feat/77-mission-gates`, base `main @ 6fe665f`. Three issue
checkboxes only (charter closure rule, stalled classification,
non-dismissible recovery). Detection, classification, loud refusal only —
nothing written here closes a row or dismisses anything (design D2, hard
safety rule; no task text conflicted with it).

## S0 — B2-pattern fixtures + pre-fix silence proof (`bef020f`)

- New `tests/test_mission_gates_prefix.py` (6 tests): B2-pattern fixture
  builders (gateless awaiting-gate parent
  `qitem-20261024023941-8685741b5ce805de`, "Standing by for gate", queue
  `in-progress`) plus byte-identical recovery snapshots; permanent pins on
  the frozen transcript (silence markers, dismissal-ALLOWED line, zero
  40+ runs) and on fixture genuineness (no second qitem, snapshots equal).
- New `docs/evidence/77-mission-gates-prefix.md`: verbatim transcripts —
  `reconcile exit: 0` / `stalled-awaiting-gate signal: ABSENT`, and
  `snapshots byte-identical: True` / `dismissal-without-change: ALLOWED`
  (`check_recovery_dismissal` absent pre-fix).
- Acceptance: `unittest tests.test_mission_gates_prefix` 6 OK;
  evidence grep exit 1 (clean); verify `36 passed, 0 failed`.
- Side note: the S0 `--check-idempotent` run re-baked `registry/`
  provenance (accepted re-lag class); left unstaged and absorbed by S1.

## S1 — charter rule + stalled classification (`2ac7238`)

- `fleet/skill-patches/mission-slice-sop.yaml` (new): one exact
  `replacements:` append to the moment-of-truth checklist stating REQ-M1
  (destination seat closes its own row `done` + closure reason; live
  `--gate <role>` owner exempts). Regen on a clean tree; diff was
  patch-caused only — 9 leaves (specs + 8 rigs) gain the bullet,
  `fleet/skills-lock.json` mission-slice-sop tree-hash refreshes, plus
  self-consistent digest/provenance re-lag (drift-scanned, no content
  drift). Zero hand-edited leaves.
- `scripts/reconcile_model.py`: `is_awaiting_gate_prose` predicate
  (waiting verb + gate within 60 chars; "awaiting QA" and verb-less
  "blocked on QA gate" do not match) and shared
  `stalled_awaiting_gate_diff` classifier (live gate = non-terminal +
  destination session exempts; else `stalled-awaiting-gate` naming the
  missing gate); `diff_row` tail delegates to it.
- `scripts/generate_trackers.py`: OTHER-arm carve-out consulting the
  shared helper (REQ-G5, no parallel mapping), rendered review-only (the
  class stays outside `PASTE_READY_CLASSES`, so the withhold-canonical-cell
  rule holds). This was a mid-milestone design refinement: without it the
  TPM-facing emitter stayed silent-OTHER about the stall, which REQ-M2/A1
  ("not silent OTHER", "gate missing named explicitly") would not accept.
- New `tests/test_mission_gates.py` (11 tests at S1): REQ-M1 leaf markers,
  B2 flagged (CLI exit 1) + diff-shape, live-gate quiet (diff None + CLI
  exit 0), dead-gate still stalled, awaiting-without-gate quiet guard,
  sabotage red-proof, generator review naming + exemption.
- `docs/evidence/77-mission-gates/red-proofs.log`: S1 RED/GREEN entries
  (mechanical sabotage run: `SABOTAGED -> None`,
  `PATCHED -> stalled-awaiting-gate`).
- Acceptance: corpus 11 OK; combined 81 OK with untouched reconcile /
  generate-tracker suites; verify `36 passed, 0 failed`; idempotent
  byte-identical (registry side effect reverted).

## S2 — non-dismissible recovery + V29 (`39c0cb5`)

- `scripts/sweep-typed-blocks.py`: `RecoveryDismissalRefused`,
  `snapshot_row_state` (canonical key-sorted JSON), and
  `check_recovery_dismissal` (identical snapshots raise with a
  seed-rig-`_redact_for_log` line; changed snapshots return a permitted
  record; no I/O, never done). Corpus grows to 16 (refused + row
  untouched, allowed-on-change, redaction with 45-char dummy tokens,
  bypass-restores-B2 red-proof, no-writes/never-done guard).
- `scripts/verify-rigs.sh`: appended V29 block only (one `ok()`; markers +
  live refusal/permission behavior + 9-leaf charter markers + S0 evidence
  lines + red-proof lines + corpus floor ≥ 16, 0 skips). V19 freeze bump
  36 → 37 (`passes + 3`) per the freeze's own rule — the only V1–V28
  touch, same as wave 9's 35 → 36. `AGENTS.md` / `README.md` /
  `docs/USER_GUIDE.md` live counts move 36 → 37 with it (V19-gated).
  `HANDOFF.md` 36-mentions left alone (prior-session file, not V19-gated;
  wave-9 reports likewise keep their historical 36s — history not rewritten).
- Acceptance: verify `37 passed, 0 failed` with V29 PASS; `make test`
  `Ran 558 tests OK`; audit self-test PASS; idempotent byte-identical.

## S3 — runbook, docs, closeout (this commit)

- `docs/evidence/77-mission-gates-runbook.md` (new): flows A (owner closes,
  exercised exit 0), B (`rig queue create --gate …` shape + live-gate
  exemption, exercised exit 0; dead/missing gates do not exempt), C
  (refusal transcript + permitted-on-change), quick-reference table.
  `--gate` count 2; evidence grep clean.
- `AGENTS.md` docs-map line for this change: already present at base
  (`AGENTS.md:74`), no edit needed; no rule-text changes in S3 (the
  36 → 37 count move rode with S2 as freeze mechanics).
- `docs/reports/77-mission-gates-verification.md` (new): drift-guard
  re-verification ending `VERDICT: PASS` (read from disk).
- `openspec/changes/2026-10-28-77-mission-gates/` left unarchived for the
  coordinator merge wave. Refs #77 on every commit; never Closes #77.

## Surprises (with evidence)

1. Emitter short-circuit (S1): `generate_trackers.py` never calls
   `diff_row` for OTHER-arm cells, so the reconcile-only fix left the
   TPM path silent-OTHER. Resolved with the shared-helper carve-out
   (review-only). Evidence: pre-fix emitter transcript (`DIFF
   [other-prose]` with no gate named) vs post-fix
   `test_generator_names_missing_gate_in_review`.
2. Bearer-regex false positives (S2): `[A-Za-z0-9_-]{40,}` matches `# ---`
   separators and long `test_…` names, so V29 asserts redaction
   behaviorally (live refusal message scan) instead of whole-file source
   scan — unlike V28's file, which is separator-free.
3. Regen provenance side effects (S0/S1/S2): every regen/idempotent run
   re-bakes `registry/` provenance; reverted after each gate run. No
   digest-gate impact either way (verify green before and after revert).
4. `red-proofs.log` S2 section was drafted in the S1 write and committed
   with S1; its referenced test (`TestNonDismissibleRecovery…`) landed in
   S2 as named. No dangling references at wave end.

## Self-audit (unfinished / open)

- Nothing unfinished in wave scope: REQ-M1…M4 scenarios all have passing
  corpus; all wave acceptance gates green (table in the verification
  report).
- Open for coordinator: merge (`--ff-only`), PR body with `Refs #77`,
  worktree prune, OpenSpec archive. `HANDOFF.md` still states 36 checks
  (left deliberately; flagging in case the coordinator wants a handoff
  refresh outside this wave).
- Live-mission proof (issue stays open until a mission closes the loop)
  is out of scope by design (fixtures-only, D3).
