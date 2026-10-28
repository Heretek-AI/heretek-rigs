# 09-send-identity — drift-guard verification (binding)

Stage/wave: `2026-10-28-09-send-identity` (branch `feat/09-send-identity`).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/09-send-identity`.
Scope: issue #9 ONLY, repo-side only (`fleet/` untouched,
`scripts/` + `tests/` + verify gate + docs). No daemon edits, no upstream
filing, no fleet-host live proofs. All wave commits carry `Refs #9`.

## 1. Spec & architecture alignment (read from disk)

- `AGENTS.md` (One Rule, git conventions, secrets rules),
  `openspec/changes/2026-10-28-09-send-identity/` (`proposal.md`,
  `design.md`, `specs/send-identity/spec.md` REQ-S1…S4, `tasks.md` S0…S3),
  `docs/reports/09-send-identity-implementation.md`,
  `docs/evidence/09-send-identity-spoof.md`,
  `docs/evidence/09-send-identity/red-proofs.log`,
  `docs/evidence/09-send-identity-rotation.md` — all read.
- REQ-S1 deliverables present: seed-time binding issuance reusing the
  `issue_seat_grant` discipline (`scripts/send_identity.py:
  issue_sender_binding`, wired in `scripts/seed-rig.py` under the existing
  grant gate), `!cat` render (`send-identity.json` in
  `scripts/render-seat.py`), server-side relay verify ignoring client claims
  (`verify_attestation` → `attested`/`unverified`/`rejected`).
- REQ-S2 deliverables present: all four forgery classes red-proven
  (`red-proofs.log` S1a–S1d, each sabotage RED for the right reason then
  reverted) and covered by `tests/test_send_identity.py` (25 tests, dummy
  keys only).
- REQ-S3 deliverables present: V28 appended (new block only) with corpus
  rc=0 + non-vacuous floor, FAIL-ONLY demonstrated dynamically (exit 1,
  35/4) and statically (`git show 4b453a2:` — zero markers), PASS post-fix
  (36/0, V28 PASS listed).
- REQ-S4 deliverables present: rotation runbook executed live in scratch
  (revoke + mint replacement, every mint `--seat` + `--rig`, zero rig-less
  forms: `--seat` ×7, `--rig` ×8, rig-less lines 0), re-key proven both
  directions; secrets discipline intact (0600 stores, `!cat` renders,
  `_redact_for_log` on every new log path — reused by import, never
  duplicated — zero `[A-Za-z0-9_-]{40,}` runs in either evidence file).

## 2. Scope discipline — no creep beyond issue #9

- Wave diff `4b453a2..HEAD --stat`: `scripts/` (4 files), `tests/` (2 files),
  3 live-count doc lines, 4 new evidence/report files, `registry/` provenance
  stamps only. `fleet/`, `specs/`, `rigs/`, `rosters/` untouched (one
  temporary `fleet.yaml` sabotage line reverted via `git checkout` during
  red-proof S1d; tree verified clean after).
- `openspec/` wave dir unarchived (only the base spec package + wave work).
  No `Closes #9` anywhere (`grep` confirms `Refs #9` on all six wave commits).
- V1–V27 gate lines unchanged except V19's mandated bump (`_v19_canonical`
  35→36, post-freeze-ok addend +1→+2 with comment, per the freeze's own
  bump rule and tasks S2.1). All 35 pre-existing checks still pass
  individually in the 36/0 run.

## 3. Security & stub audit

- New-code log paths: issuance `_fail` (via seed choke point), store-error
  path (via `_redact`), attestation `_deny` + claim-conflict note (via
  `_redact`). Corpus asserts no bearer-shaped runs in every error string it
  captures. Evidence greps clean (both files).
- Crypto: HMAC-SHA256 via stdlib, `hmac.compare_digest`, strict shape parse
  (5 dot-fields, `v1` tag, nonce `^[A-Za-z0-9_-]{16,}$`, 64-hex MAC),
  empty-secret and `seen=None` fail closed, `ValueError` on `/`/`..`
  sessions at the filename choke point (test-proven hostile triple).
- Stub scan over new/edited code: no `TODO`, `NotImplemented`, pass-through
  mocks, `|| true`, skipped tests, or empty catches. Fake-`rig` harnesses
  are stateful (list/add/revoke with scope metadata), not pass-throughs.
- Cross-test pollution found and fixed during S1 (fake-rig env flags now
  snapshot-restored per test, mirroring `test_identity_m1`): full
  `make test` (530/22) green in one process.

## 4. Acceptance rerun (from disk, this audit)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 36 checks passed,
  0 failed` with `[PASS] V28 send-identity attestation (09-send-identity S1)
  green: binding rules + !cat render + 25 corpus tests pass + S0 evidence present`.
- `make test` → `Ran 530 tests … OK` (22 suites).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`.
- `python3 scripts/generate-rigs.py --check-idempotent` → byte-identical PASS.
- `python3 -m unittest tests.test_send_identity -v` → 25/25 OK, exit 0.
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md
  docs/evidence/09-send-identity-rotation.md` → no output (exit 1).
- Rotation mandate greps: `--seat` ×7, `--rig` ×8, rig-less mint lines 0.

## 5. Known non-blockers (disclosed, not fixed here)

- `HANDOFF.md` + `docs/IMPLEMENTATION_PROMPT.md` still state the 35-count
  baseline (V19-unscanned, coordinator-owned session state).
- Daemon-side `seen`-set persistence = #127 upstream gap (out of scope).
- Committed `resolvedCommit` provenance re-lags HEAD by design (generator
  behavior, merge-time regen rule applies); final tree carries the accepted
  post-`--check-idempotent` stamp dirt, committed in the S3 closeout commit.

VERDICT: PASS
