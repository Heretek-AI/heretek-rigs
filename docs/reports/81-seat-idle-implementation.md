# Implementation report — 81-seat-idle (Refs #81)

Branch `feat/81-seat-idle`, base `main @ 8dec2ed`. Three issue checkboxes
only (charter claim rule, idle-park classification with latency
attribution, daemon source label + non-dismissible recovery). Detection,
classification, loud refusal only — nothing written here closes a row,
dismisses anything, writes tracker/queue state, or wakes a seat (design D3,
fixtures-only + propose-only; no daemon edits, no upstream filing, no
live-fleet proofs). Refs #81 on everything; never Closes #81.

## S0 — #81-pattern fixtures + pre-fix silence proof

- New `tests/test_seat_idle_prefix.py` (9 tests): Mission-A fixture
  builders (claim-then-park parent
  `qitem-20261023213329-7ad896bfc962330d`: claim t11 + `Handoff received —
  pulling the queue item` t12 + parked-owner-consumer watchdog line
  holding 1 open obligation t13, no work action anywhere) plus the
  claim/park/wake latency spread (claim 21:33:29, park +31s, wake +53s,
  work null) and the daemon-origin handoff labeled `From: operator`
  (`qitem-recovery-3b06228ed0da95e8`); permanent pins on the frozen
  transcript (silence markers, attribution-ABSENT, operator-persists,
  zero 40+ runs) and on fixture genuineness (claim+park+obligation
  present, no work token, spread ordered, daemon origin with operator
  label). Stays green before and after (like the wave-4 prefix file).
- New `docs/evidence/81-seat-idle-prefix.md`: verbatim transcripts —
  `reconcile exit: 0` / `idle-park signal: ABSENT`,
  `park-to-wake attribution: ABSENT` (`grep -c` 0 over
  `reconcile_model.py`), `daemon source rule: ABSENT` /
  `recorded source: operator` (no `daemon:stuck-sweep` /
  `validate_handoff_source` / `DAEMON_SOURCE` in pre-fix
  `send_identity.py`).
- Acceptance: `unittest tests.test_seat_idle_prefix` 9 OK;
  evidence grep exit 1 (clean); verify tree behavior unmodified at S0
  time (37 passed, 0 failed on the untouched tree).

## S1 — charter rule + idle-park classification + daemon source

- `fleet/skill-patches/queue-handoff.yaml` (new): one exact
  `replacements:` append to the hot-potato terminal-turn-rule stating
  REQ-I1 (claiming a qitem and the first work action are one turn; a seat
  holding an open obligation MUST NOT end its turn right after the claim;
  81-seat-idle claim rule). Regen on dev dirt; 9 leaves (specs + 8 rigs)
  gain the rule, `fleet/skills-lock.json` queue-handoff tree-hash
  refreshes, plus self-consistent digest/provenance re-lag.
- `scripts/reconcile_model.py`: `is_idle_park_prose` predicate
  (idle-at-prompt marker + nonzero open-obligation count; zero-obligation
  and obligation-free prose do not match), `trail_has_claim` /
  `trail_has_work_action` (only the known non-work classes excluded, so an
  unfamiliar note counts as work and keeps the row quiet — fail-closed
  against over-flagging), `attribute_idle_latency` (claim/park/wake/work
  timestamps → claim-to-park, park-to-wake vs work shares; report-only),
  and shared `stalled_idle_park_diff` classifier (claim + no work + cell
  shows parked-at-prompt holding an open obligation → `stalled-idle-park`
  with attribution; obligation-free idle and live-gate waiting return
  None); `diff_row` tail tries the gate classifier then the idle-park
  classifier; `render_diff` appends the attribution line when present.
- `scripts/generate_trackers.py`: OTHER-arm carve-out consulting the
  shared idle-park helper (REQ-G5, no parallel mapping), rendered
  review-only (class stays outside `PASTE_READY_CLASSES`). Without this
  the TPM path renders idle-park rows as generic silent-OTHER.
- `scripts/send_identity.py`: `DAEMON_SOURCE = "daemon:stuck-sweep"` and
  `validate_handoff_source` (daemon origin + operator label → relabeled
  to the daemon source with a seed-rig-`_redact_for_log` line, never
  recorded as an operator relay; honest daemon labels persist; genuine
  operator origin keeps `operator` with wave-9 mint/verify semantics
  intact; unknown origin raises fail-closed).
- New `tests/test_seat_idle.py` (24 tests): REQ-I1 leaf markers (patch
  input + all 9 leaves), REQ-I2 flagged + CLI exit 1 with attribution +
  three quiet guards + report-only source inspection + S1a/S1b/S1c
  red-proofs, REQ-I3 relabel/persist/untouched/redaction/S1d, S2.1
  refusal/permission/redaction/never-done.
- `docs/evidence/81-seat-idle/red-proofs.log`: FAIL-ONLY pre-fix run
  (`PREFIX -> None`, classifier absent) plus S1a–S1d RED/GREEN entries
  from live /tmp sabotage runs.
- Acceptance: corpus 24 OK; full suite `Ran 595 tests OK`; idempotent
  byte-identical (two consecutive regens under `ALLOW_DIRTY`).

## S2 — non-dismissible recovery + non-spoofable source + V30

- S2.1 rides the existing `check_recovery_dismissal` close-time guard
  (fail-closed refusal on byte-identical snapshots, redacted log, performs
  no write, never done): exercised with idle-park snapshots
  (`recovery-idle-park-01` refused while the Mission-A row is unchanged,
  permitted once the owner records work) via unit and production
  (`request_recovery_dismissal`) paths in the corpus.
- `scripts/verify-rigs.sh`: appended V30 block only
  (`== V30. Seat Idle-Park (81-seat-idle) ==`, one `ok()`); markers +
  live relabel/refusal behavior + 9-leaf charter markers + S0 evidence
  lines + red-proof lines + corpus floor ≥ 16 (24, 0 skips); daemon-source
  rule present with wave-9 `attested`/`rejected`/`unverified` +
  mint/verify intact. V19 freeze bump 37 → 38 (`passes + 4`) per the
  freeze's own rule — the only V1–V29 touch, same as waves 9/4.
  `AGENTS.md` / `README.md` / `docs/USER_GUIDE.md` live counts move
  37 → 38 with it (V19-gated). `HANDOFF.md` 37-mentions left alone
  (prior-session file, not V19-gated).
- Acceptance: V30 PASS (24 corpus tests); `make test` `Ran 595 tests OK`;
  audit self-test prompt-checks pass (verify-gate step red only on the
  DIRTY-provenance stamp — see self-audit); idempotent byte-identical.

## S3 — runbook, docs, wave closeout

- `docs/evidence/81-seat-idle-runbook.md` (new): flow A
  (claim+first-action, negative control exit 0), flow B (idle-park triage:
  verbatim exit-1 diff with attribution), flow C (daemon-source
  verification C1–C4) — all exercised against /tmp scratch fixtures;
  park-to-wake 53.0s vs work 0s sample recorded as #15/#17 inputs.
  `daemon:stuck-sweep` ×6, `park-to-wake` ×5; evidence grep exit 1.
- AGENTS.md docs-map line for this change: already present at base
  (`AGENTS.md:75`), no edit needed; no rule-text changes in S3 (the
  37 → 38 count move rode with S2 as freeze mechanics).
- `docs/reports/81-seat-idle-verification.md` (new): drift-guard
  re-verification ending `VERDICT: PASS` (read from disk).
- `openspec/changes/2026-10-28-81-seat-idle/` left unarchived for the
  coordinator merge wave. Refs #81 everywhere; never Closes #81.

## Commands run (exit codes)

- `python3 -m unittest tests.test_seat_idle_prefix -v` → 0 (9 OK)
- `python3 -m unittest tests.test_seat_idle` → 0 (24 OK)
- `python3 -m unittest discover -s tests -p 'test_*.py'` → 0
  (`Ran 595 tests OK`)
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/81-seat-idle-prefix.md` →
  1 (clean); same over runbook + red-proofs.log → 1 (clean)
- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 scripts/generate-rigs.py
  --check-idempotent` → 0 (byte-identical); plain
  `--check-idempotent` → 2 (dirty-tree gate: refuses uncommitted tree —
  coordinator runs post-commit)
- `./scripts/verify-rigs.sh --check-only` → 1: 36 passed including V30
  PASS and V19@38 docs; 48 failed, ALL 48 carrying the `DIRTY-`
  dev-regen provenance stamp (0 non-DIRTY failures — see self-audit)
- `python3 scripts/audit_loop.py --self-test` → 1: prompt/file checks
  pass; verify-gate step red only on the same DIRTY stamp

## Self-audit notes (unfinished stated plainly)

1. Registry provenance is `DIRTY-8dec2ed…`-stamped (dev regen over my
   uncommitted tree — I am forbidden to commit). This trips the schema /
   V5-40-hex / V13-no-DIRTY gates (all 48 failures; content digests
   themselves are consistent — bundle integrity matches disk). Resolution
   is the coordinator's committed flow (wave-4/9 precedent): commit the
   inputs, re-run `python3 scripts/generate-rigs.py` on the clean tree
   (records the bare SHA), then `./scripts/verify-rigs.sh --check-only`
   → expect `SUMMARY: 38 checks passed, 0 failed` with V30 PASS, plus
   `python3 scripts/generate-rigs.py --check-idempotent` byte-identical
   and `python3 scripts/audit_loop.py --self-test` PASS. Nothing else is
   unfinished: corpus, evidence, runbook, reports, and red-proofs are
   complete and green.
2. No daemon edits, no auto-wake, no `done` writes, no upstream filing, no
   live-fleet proofs (non-goals honored). Dummy keys only; every new log
   path through `_redact_for_log`; zero unredacted secret-shaped strings
   in evidence.
3. Zero stubs/TODOs/skipped tests in delivered code; no hand-edited
   generated leaves (all `specs/`/`rigs/`/`rosters/`/`registry/` changes
   via regen; `fleet/fleet.yaml` untouched — surgical patch-file add
   only). S1b/S1c quiet-both-ways and S1d collision-restore red-proofs
   are non-vacuous (each re-run by QA: 2-of-4 minimum; 4-of-4 by
   drift-guard).
