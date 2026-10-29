# Tasks: 15-auth-envelope (S0 → S3, each gated)

Standard baseline for EVERY milestone (must be green before moving on):

```bash
./scripts/verify-rigs.sh --check-only            # S0/S1: 38 passed, 0 failed | S2/S3: 39 passed, 0 failed (V31 appended)
python3 scripts/generate-rigs.py --check-idempotent
python3 scripts/audit_loop.py --self-test
```

Secrets rules (all milestones): real keys ONLY in `~/.config/heretek-rigs/secrets/` (0700/0600), dummy keys in
scratch/tests (`/tmp`, 0600), every new log path through `_redact_for_log`, `gh` bodies via heredoc files.
Refs #15 on every commit/PR (never `Closes #15` — the issue stays open until a live fleet proves authorization keeps pace).
No daemon edits, no upstream filing, no live-fleet proofs, no auto-commit and no self-executing envelopes (ever).
Nothing under `openspec/` changes after this spec except the end-of-wave archive. Generated leaves (`specs/`, `rigs/`,
`rosters/`, `registry/`) never hand-edited.

## S0 — #15-pattern fixtures + pre-fix silence proof

- [ ] S0.1 Scratch fixtures (repo `tests/` fixtures + `/tmp` scratch only): authorized premise (one-liner scope) vs
  live drifted diff (multi-file); premise-age spread fixture (premise/verify/landing timestamps); no-envelope baseline.
- [ ] S0.2 Preserve verbatim transcripts at `docs/evidence/15-auth-envelope-prefix.md` (redacted/dummies only).
- [ ] S0.3 Prove non-vacuous: reconciler exits without the drift signal AND no envelope validates on the unpatched tree;
  `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/15-auth-envelope-prefix.md` MUST print nothing.

Acceptance (S0):

```bash
python3 -m unittest tests.test_auth_envelope_prefix -v   # exits 0, documents pre-fix silence (fixture asserts current behavior)
grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/15-auth-envelope-prefix.md; test $? -eq 1
./scripts/verify-rigs.sh --check-only                    # 38 passed, 0 failed (tree behavior unmodified)
```

## S1 — premise-drift classification + premise-age attribution

- [ ] S1.1 `reconcile_model.py` new premise-drift diff class (stalled signal, propose-only; clean premises stay quiet)
  with premise-age attribution (report-only field, inputs for #17). Corpus fixtures in the reconcile test style, dummy data only.
- [ ] S1.2 Attribution is report-only: premise age at landing computed from fixture timestamps; no tracker/queue writes.
- [ ] S1.3 `tests/test_auth_envelope.py` covering REQ-E1 (clean-validates path) / REQ-E2 scenarios (flagged + quiet + attribution).

Acceptance (S1):

```bash
python3 -m unittest tests.test_auth_envelope -v   # exits 0; each scenario listed and passing
./scripts/verify-rigs.sh --check-only             # 38 passed, 0 failed
python3 scripts/generate-rigs.py --check-idempotent
```

Red-proof (S1, logged in `docs/evidence/15-auth-envelope/red-proofs.log`): S1a remove the drift classification →
fixture returns to silent (RED); restore → flagged (GREEN). S1b clean-premise fixture stays quiet both ways.
One entry per check; add pinning tests wherever a probe outruns the suite (wave-81 lesson).

## S2 — envelope mint/validate + non-dismissible recovery + V31

- [ ] S2.1 Envelope mint/validate: `diff-hash` + scope paths + mandatory expiry + single-use nonce (HMAC-bound,
  0600 stores, redacted logs; wave-9 nonce discipline reused where it fits). Drift/scope-breach/expiry/replay ⇒
  fail-closed refusal, redacted log; row untouched. Envelopes never self-execute, never auto-commit.
- [ ] S2.2 Landing recovery requires row state change for dismissal (fail-closed refusal, redacted log; never `done`,
  never committed).
- [ ] S2.3 Append V31 block `== V31. Pre-Authorization Envelopes (15-auth-envelope) ==` (new block only; SUMMARY 38 → 39).
- [ ] S2.4 V31 asserts: drift diff class present, envelope validation present with nonce/expiry/scope checks, corpus rc=0
  with floor ≥16, S0 evidence present with silence transcript and zero secret-shaped strings. FAIL-ONLY run against
  pre-fix tree recorded in red-proofs.log.

Acceptance (S2):

```bash
./scripts/verify-rigs.sh --check-only             # SUMMARY: 39 checks passed, 0 failed, V31 PASS listed
make test                                         # 0 failures (record count in report)
python3 scripts/audit_loop.py --self-test         # SELF-TEST PASSED
```

Red-proof (S2, same log): S1c allow drifted landing (bypass validation) → authorized (RED); restore → refused (GREEN).
S1d replay a consumed nonce / present an expired envelope → refused (RED each); restore → refused stays (GREEN = still refused).

## S3 — runbook, docs, wave closeout

- [ ] S3.1 `docs/evidence/15-auth-envelope-runbook.md`: envelope issuance flow + landing validation flow + drift-triage
  flow, exercised against fixtures in scratch (record premise-age samples as #17 inputs).
- [ ] S3.2 AGENTS.md docs-map line for this change (docs-map-only; no rule-text changes).
- [ ] S3.3 Implementation report `docs/reports/15-auth-envelope-implementation.md`; QA red-proofs committed;
  drift-guard `docs/reports/15-auth-envelope-verification.md` ending `VERDICT: PASS`.
- [ ] S3.4 Leave `openspec/changes/2026-10-29-15-auth-envelope/` unarchived until merge; archive only after triad passes.

Acceptance (S3):

```bash
grep -c -- 'diff-hash' docs/evidence/15-auth-envelope-runbook.md              # >=1
grep -c -- 'premise age' docs/evidence/15-auth-envelope-runbook.md            # >=1
./scripts/verify-rigs.sh --check-only && python3 scripts/generate-rigs.py --check-idempotent
```

## Wave closeout (coordinator)

- [ ] Triad complete with `VERDICT: PASS` read from disk (never trusted from summary).
- [ ] `git merge --ff-only` into `main`, `make check` green, worktree pruned, change archived.
- [ ] PR with `Refs #15` (issue stays open for the live-fleet proof).
