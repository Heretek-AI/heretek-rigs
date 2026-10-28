# Tasks: 77-mission-gates (S0 → S3, each gated)

Standard baseline for EVERY milestone (must be green before moving on):

```bash
./scripts/verify-rigs.sh --check-only            # S0/S1: 36 passed, 0 failed | S2/S3: 37 passed, 0 failed (V29 appended)
python3 scripts/generate-rigs.py --check-idempotent
python3 scripts/audit_loop.py --self-test
```

Secrets rules (all milestones): real keys ONLY in `~/.config/heretek-rigs/secrets/` (0700/0600), dummy keys in
scratch/tests (`/tmp`, 0600), every new log path through `_redact_for_log`, `gh` bodies via heredoc files.
Refs #77 on every commit/PR (never `Closes #77` — the issue stays open until a live mission proves the loop).
No daemon edits, no upstream filing, no live-fleet proofs. Nothing under `openspec/` changes after this spec
except the end-of-wave archive. Generated leaves (`specs/`, `rigs/`, `rosters/`, `registry/`) never hand-edited.

## S0 — B2-pattern fixtures + pre-fix silence proof

- [x] S0.1 Scratch fixtures (repo `tests/` fixtures + `/tmp` scratch only): gateless awaiting-gate parent (B2 pattern);
  recovery dismissal with byte-identical row state.
- [x] S0.2 Preserve verbatim transcripts at `docs/evidence/77-mission-gates-prefix.md` (redacted/dummies only).
- [x] S0.3 Prove non-vacuous: reconciler exits without the stalled signal AND dismissal succeeds on the unpatched tree;
  `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md` MUST print nothing.

Acceptance (S0):

```bash
python3 -m unittest tests.test_mission_gates_prefix -v   # exits 0, documents pre-fix silence (fixture asserts current behavior)
grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md; test $? -eq 1
./scripts/verify-rigs.sh --check-only                    # 36 passed, 0 failed (tree behavior unmodified)
```

## S1 — charter rule + stalled classification

- [x] S1.1 Closure-ownership rule via `fleet/skill-patches/` (+ `generate-rigs.py` regen; zero hand-edited leaves).
- [x] S1.2 `reconcile_model.py` new diff class for gateless awaiting-gate parents (stalled signal, propose-only;
  live gate qitem exempts). Corpus fixtures in the reconcile test style, dummy data only.
- [x] S1.3 `tests/test_mission_gates.py` covering REQ-M1/M2 scenarios (exempt + flagged paths).

Acceptance (S1):

```bash
python3 -m unittest tests.test_mission_gates -v   # exits 0; each scenario listed and passing
./scripts/verify-rigs.sh --check-only             # 36 passed, 0 failed
python3 scripts/generate-rigs.py --check-idempotent
```

Red-proof (S1, logged in `docs/evidence/77-mission-gates/red-proofs.log`): remove the classification → fixture
returns to silent-OTHER (RED); restore → flagged (GREEN). One entry per check.

## S2 — non-dismissible recovery + V29

- [x] S2.1 Sweep recovery requires row state change for dismissal (fail-closed refusal, redacted log; never `done`).
- [x] S2.2 Append V29 block `== V29. Mission-Gate Ownership (77-mission-gates) ==` (new block only; SUMMARY 36 → 37).
- [x] S2.3 V29 asserts: diff class present, charter marker present in rendered leaves, corpus rc=0, S0 evidence present
  with silence transcript and zero secret-shaped strings. FAIL-ONLY run against pre-fix tree recorded in red-proofs.log.

Acceptance (S2):

```bash
./scripts/verify-rigs.sh --check-only             # SUMMARY: 37 checks passed, 0 failed, V29 PASS listed
make test                                         # 0 failures (record count in report)
python3 scripts/audit_loop.py --self-test         # SELF-TEST PASSED
```

## S3 — runbook, docs, wave closeout

- [x] S3.1 `docs/evidence/77-mission-gates-runbook.md`: owner-closes-with-evidence flow + gate-creation flow
  (`rig queue create --gate …` with destination), exercised against fixtures in scratch.
- [x] S3.2 AGENTS.md docs-map line for this change (docs-map-only; no rule-text changes).
- [x] S3.3 Implementation report `docs/reports/77-mission-gates-implementation.md`; QA red-proofs committed;
  drift-guard `docs/reports/77-mission-gates-verification.md` ending `VERDICT: PASS`.
- [x] S3.4 Leave `openspec/changes/2026-10-28-77-mission-gates/` unarchived until merge; archive only after triad passes.

Acceptance (S3):

```bash
grep -c -- '--gate' docs/evidence/77-mission-gates-runbook.md              # >=1
./scripts/verify-rigs.sh --check-only && python3 scripts/generate-rigs.py --check-idempotent
```

## Wave closeout (coordinator)

- [x] Triad complete with `VERDICT: PASS` read from disk (never trusted from summary).
- [x] `git merge --ff-only` into `main`, `make check` green, worktree pruned, change archived.
- [ ] PR with `Refs #77` (issue stays open for the live-mission proof).
