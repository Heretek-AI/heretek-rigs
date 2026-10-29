# Tasks: 81-seat-idle (S0 → S3, each gated)

Standard baseline for EVERY milestone (must be green before moving on):

```bash
./scripts/verify-rigs.sh --check-only            # S0/S1: 37 passed, 0 failed | S2/S3: 38 passed, 0 failed (V30 appended)
python3 scripts/generate-rigs.py --check-idempotent
python3 scripts/audit_loop.py --self-test
```

Secrets rules (all milestones): real keys ONLY in `~/.config/heretek-rigs/secrets/` (0700/0600), dummy keys in
scratch/tests (`/tmp`, 0600), every new log path through `_redact_for_log`, `gh` bodies via heredoc files.
Refs #81 on every commit/PR (never `Closes #81` — the issue stays open until a live fleet proves the loop).
No daemon edits, no upstream filing, no live-fleet proofs. Nothing under `openspec/` changes after this spec
except the end-of-wave archive. Generated leaves (`specs/`, `rigs/`, `rosters/`, `registry/`) never hand-edited.

## S0 — #81-pattern fixtures + pre-fix silence proof

- [x] S0.1 Scratch fixtures (repo `tests/` fixtures + `/tmp` scratch only): claim-then-park with open obligation
  (Mission-A pattern: claim + "Handoff received" + parked-at-prompt watchdog line, no work action);
  park-to-wake latency spread fixture (claim/work/wake timestamps); daemon handoff labeled `From: operator`.
- [x] S0.2 Preserve verbatim transcripts at `docs/evidence/81-seat-idle-prefix.md` (redacted/dummies only).
- [x] S0.3 Prove non-vacuous: reconciler exits without the idle-park signal AND the operator-labeled daemon handoff
  passes unlabeled on the unpatched tree;
  `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/81-seat-idle-prefix.md` MUST print nothing.

Acceptance (S0):

```bash
python3 -m unittest tests.test_seat_idle_prefix -v   # exits 0, documents pre-fix silence (fixture asserts current behavior)
grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/81-seat-idle-prefix.md; test $? -eq 1
./scripts/verify-rigs.sh --check-only                    # 37 passed, 0 failed (tree behavior unmodified)
```

## S1 — charter rule + idle-park classification + daemon source label

- [x] S1.1 Claim+first-action-is-one-turn rule via `fleet/skill-patches/` (+ `generate-rigs.py` regen; zero hand-edited leaves).
- [x] S1.2 `reconcile_model.py` new idle-park diff class (stalled signal, propose-only; obligation-free idle and
  live-gate waiting stay quiet) with park-to-wake vs work attribution (report-only field, inputs for #15/#17).
  Daemon source validation: daemon origin MUST NOT persist as `operator` (refuse or relabel to `daemon:stuck-sweep`,
  redacted log; wave-9 attestation handling for genuine operator relays unchanged). Corpus fixtures in the
  reconcile test style, dummy data only.
- [x] S1.3 `tests/test_seat_idle.py` covering REQ-I1/I2/I3 scenarios (flagged + quiet + attribution + relabel paths).

Acceptance (S1):

```bash
python3 -m unittest tests.test_seat_idle -v   # exits 0; each scenario listed and passing
./scripts/verify-rigs.sh --check-only             # 37 passed, 0 failed
python3 scripts/generate-rigs.py --check-idempotent
```

Red-proof (S1, logged in `docs/evidence/81-seat-idle/red-proofs.log`): S1a remove the idle-park classification →
fixture returns to silent (RED); restore → flagged (GREEN). S1b obligation-free idle fixture stays quiet both ways.
S1c live-gate waiting stays quiet both ways. S1d allow the operator label for daemon origin → collision restored (RED);
restore validation → distinct daemon source (GREEN). One entry per check.

## S2 — non-dismissible recovery + non-spoofable source + V30

- [x] S2.1 Idle-park recovery requires row state change for dismissal (fail-closed refusal, redacted log; never `done`).
  Daemon-source guard: operator label of daemon origin never persists (refuse or relabel, redacted log).
- [x] S2.2 Append V30 block `== V30. Seat Idle-Park (81-seat-idle) ==` (new block only; SUMMARY 37 → 38).
- [x] S2.3 V30 asserts: idle-park diff class present, charter marker present in rendered leaves, daemon-source rule
  present with wave-9 attestation intact, corpus rc=0 with floor ≥16, S0 evidence present with silence transcript
  and zero secret-shaped strings. FAIL-ONLY run against pre-fix tree recorded in red-proofs.log.

Acceptance (S2):

```bash
./scripts/verify-rigs.sh --check-only             # SUMMARY: 38 checks passed, 0 failed, V30 PASS listed
make test                                         # 0 failures (record count in report)
python3 scripts/audit_loop.py --self-test         # SELF-TEST PASSED
```

## S3 — runbook, docs, wave closeout

- [x] S3.1 `docs/evidence/81-seat-idle-runbook.md`: claim+first-action flow + idle-park triage flow + daemon-source
  verification flow, exercised against fixtures in scratch (record park-to-wake vs work attribution samples as #15/#17 inputs).
- [x] S3.2 AGENTS.md docs-map line for this change (docs-map-only; no rule-text changes).
- [x] S3.3 Implementation report `docs/reports/81-seat-idle-implementation.md`; QA red-proofs committed;
  drift-guard `docs/reports/81-seat-idle-verification.md` ending `VERDICT: PASS`.
- [x] S3.4 Leave `openspec/changes/2026-10-28-81-seat-idle/` unarchived until merge; archive only after triad passes.

Acceptance (S3):

```bash
grep -c -- 'daemon:stuck-sweep' docs/evidence/81-seat-idle-runbook.md              # >=1
grep -c -- 'park-to-wake' docs/evidence/81-seat-idle-runbook.md                    # >=1
./scripts/verify-rigs.sh --check-only && python3 scripts/generate-rigs.py --check-idempotent
```

## Wave closeout (coordinator)

- [x] Triad complete with `VERDICT: PASS` read from disk (never trusted from summary).
- [x] `git merge --ff-only` into `main`, `make check` green, worktree pruned, change archived.
- [x] PR with `Refs #81` (issue stays open for the live-fleet proof).
