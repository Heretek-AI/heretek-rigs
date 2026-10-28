# Tasks: 09-send-identity (S0 → S3, each gated)

Standard baseline for EVERY milestone (must be green before moving on):

```bash
./scripts/verify-rigs.sh --check-only            # S0/S1: 35 passed, 0 failed | S2/S3: 36 passed, 0 failed (V28 appended)
python3 scripts/generate-rigs.py --check-idempotent
python3 scripts/audit_loop.py --self-test
```

Secrets rules (all milestones): real keys ONLY in `~/.config/heretek-rigs/secrets/` (0700/0600), dummy keys in
scratch/tests (`/tmp`, 0600), every new log path through `_redact_for_log`, `gh` bodies via heredoc files.
Refs #9 on every commit/PR (never `Closes #9` — the issue stays open until live proof). No upstream filing.

## S0 — isolated-scratch spoof proof (pre-fix evidence)

- [ ] S0.1 Write scratch-only spike (NEVER in repo paths): forge `--source` + `OPENRIG_SESSION_NAME` env on a loopback
  `rig` scratch env and show the forged sender is accepted as sender.
- [ ] S0.2 Preserve verbatim transcript at `docs/evidence/09-send-identity-spoof.md` (redacted `or…XX` or dummies only).
- [ ] S0.3 Prove the check is non-vacuous: `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md` MUST
  print nothing (exit 1 = no unredacted secrets); the transcript MUST contain the accepted forged sender line.

Acceptance (S0):

```bash
bash /tmp/s0-spoof-proof.sh                       # exits 0, prints SPOOF-OK pre-fix + accepted forged sender
grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md; test $? -eq 1
./scripts/verify-rigs.sh --check-only             # 35 passed, 0 failed (tree unmodified)
```

## S1 — grant-bound attestation + relay verify

- [ ] S1.1 Sender binding issuance reusing `issue_seat_grant` discipline (scope seat+rig, 0600 mkstemp+replace,
  fail-closed parse, revoke-on-fail, `!cat` render, no-`..`-`/` filenames).
- [ ] S1.2 Relay verify: attested sender recorded; conflicting client claim ignored → UNVERIFIED-or-attested (never raw claim);
  replay rejected; cross-rig scope fails; V22 triple intact in fleet + rendered leaves.
- [ ] S1.3 `tests/test_send_identity.py` covering all four REQ-S2 scenarios (spoof, replay, cross-rig, bare-send), dummy keys only.

Acceptance (S1):

```bash
python3 -m unittest tests.test_send_identity -v   # exits 0; each forgery test listed and passing
./scripts/verify-rigs.sh --check-only             # 35 passed, 0 failed (V22 intact)
python3 scripts/generate-rigs.py --check-idempotent
```

Red-proof (S1, logged in `docs/evidence/09-send-identity/red-proofs.log`): for EACH of the four tests, temporarily
re-introduce the forgery (sabotage), observe the test turn RED, then revert — one entry per check.

## S2 — V28 gate + corpus promotion

- [ ] S2.1 Append V28 block `== V28. Send-Identity Attestation (09-send-identity S1) ==` to `scripts/verify-rigs.sh`
  (new block only; no renumber/reword of V1–V27; SUMMARY expectation 35 → 36).
- [ ] S2.2 V28 asserts: binding filename rule, `!cat` render present + no inline secret, corpus rc=0, S0 evidence file present
  with accepted-forgery line and zero bearer-shaped strings.
- [ ] S2.3 FAIL-ONLY demonstration: V28 logic run against the pre-fix tree MUST fail (record output in red-proofs.log).

Acceptance (S2):

```bash
./scripts/verify-rigs.sh --check-only             # SUMMARY: 36 checks passed, 0 failed, V28 PASS listed
make test                                         # 0 failures (suite count grown; record count in report)
python3 scripts/audit_loop.py --self-test         # SELF-TEST PASSED
```

## S3 — rotation runbook, docs, wave closeout

- [ ] S3.1 Write `docs/evidence/09-send-identity-rotation.md` (revoke + re-add, every mint with `--seat` AND `--rig`,
  zero rig-less forms — V24-style mandate) and execute it in isolated scratch.
- [ ] S3.2 AGENTS.md docs-map line for this change (docs-map-only; no rule-text changes).
- [ ] S3.3 Implementation report `docs/reports/09-send-identity-implementation.md`; QA red-proofs committed;
  drift-guard `docs/reports/09-send-identity-verification.md` ending `VERDICT: PASS`.
- [ ] S3.4 Leave `openspec/changes/2026-10-28-09-send-identity/` unarchived until merge; archive (`openspec archive`)
  only after the triad passes on the implementation wave.

Acceptance (S3):

```bash
grep -c -- '--seat' docs/evidence/09-send-identity-rotation.md            # >=1
grep -c -- '--rig' docs/evidence/09-send-identity-rotation.md             # >=1 (every mint scoped)
grep -n 'mcp token add\|sender.*add' docs/evidence/09-send-identity-rotation.md | grep -v -- '--rig' | test "$(cat | wc -l)" -eq 0
./scripts/verify-rigs.sh --check-only && python3 scripts/generate-rigs.py --check-idempotent
```

## Wave closeout (coordinator)

- [ ] Triad complete with `VERDICT: PASS` read from disk (never trusted from summary).
- [ ] `git merge --ff-only` into `main`, `make check` green, worktree pruned, change archived.
- [ ] PR with `Refs #9` (issue stays open for fleet-host live proof batch).
