# 09-send-identity-r1 — independent adversarial verification (drift-guard, rework cycle 1)

Wave: `09-send-identity-r1` (branch `fix/09-send-identity-r1`, tip `0350a5c` at audit start; cycle base `12ee2ba`).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/09-send-identity-r1`.
Auditor: independent (no production code changed; no commits; no pushes; this report is the only file written).
Files read from disk (nothing trusted summarized): `AGENTS.md`,
`openspec/specs/send-identity/spec.md` (REQ-S1…S4 normative),
`docs/reports/09-send-identity-rework-1.md`, `docs/reports/09-send-identity-r1-qa.md`,
`docs/reports/09-send-identity-verification.md` (prior PASS — revalidated, not inherited),
`docs/evidence/09-send-identity/red-proofs.log`, `docs/evidence/09-send-identity-rotation.md`,
`scripts/send_identity.py`, `scripts/seed-rig.py`, `scripts/render-seat.py` (read-only),
`scripts/verify-rigs.sh` (cycle hunk), `tests/test_send_identity.py` (cycle hunk),
cycle diff `git diff 12ee2ba..HEAD`, `git log 12ee2ba..HEAD`.

## 1. Cycle-diff analysis

- Commits in scope (all `Refs #9`, none `Closes/Fixes/Resolves`): `2aff663` (fix),
  `ac9869e` (provenance), `1915d5b` + `0350a5c` (reports/evidence). PASS.
- `--name-only` (26 files): `AGENTS.md`, `HANDOFF.md`, `docs/evidence/09-send-identity-rotation.md`,
  `docs/evidence/09-send-identity/red-proofs.log`, 2 new reports, 16 `registry/` leaves,
  `scripts/seed-rig.py`, `scripts/send_identity.py`, `scripts/verify-rigs.sh`,
  `tests/test_send_identity.py`. **Zero files under `openspec/`** (empty diff confirmed),
  zero under `specs/`, `rigs/`, `rosters/`, `fleet/`. PASS.
- Registry diff filter (`^[+-]` minus headers): every non-header line is a
  `resolvedCommit`/`canonicalUrl` embed; zero other lines. Provenance re-lag only. PASS.
- `verify-rigs.sh`: exactly one hunk (V28 skip parsing: `skipped=` parse, fail-on-skip,
  floor on `ran - skipped`). V-header sets base-vs-head byte-identical
  (`diff` of `== V[0-9]+` lines: empty; 26 headers both sides). V1–V27 untouched. PASS.
- `render-seat.py`: **zero diff in cycle** (see N1 below; behavior claim still true of base code).
- Scope: no `daemon`/upstream/fleet-host paths in diff; F11 (`coderabbit`) not acted on
  (no such invocation or file). PASS.

## 2. F5 security trace

- Hole confirmed real by construction: pre-cycle `verify_attestation` checked
  `rig != expected_rig` only (base code read: no sender comparison anywhere before line 332).
  Fix adds required keyword-only `expected_sender: str` (no default — omission is a
  `TypeError`, fail-closed) plus the `sender != expected_sender` → `unverified` denial
  (`scripts/send_identity.py:332-336`), reached before MAC computation so a valid-MAC
  cross-seat attestation still denies. PASS.
- Callers: the only in-repo callers of `verify_attestation` are the 12 call sites in
  `tests/test_send_identity.py` — every one passes `expected_sender` (grep: 12/12).
  `scripts/verify-rigs.sh` V28 only `hasattr`-checks the names, never calls verify.
  No production relay duplicates the logic (single `def verify_attestation`, single
  `def mint_attestation`; no second MAC path in the module). No bypass path. PASS.
- Cross-seat test is not a tautology: `test_cross_seat_secret_cannot_authenticate_other_sender`
  mints with `mint_attestation(SECRET, "seat-b@test-rig", RIG)` (valid MAC under the
  seat-A secret for sender B) and verifies with `expected_sender="seat-a@test-rig"` —
  distinct sender identities, same secret. Pre-fix this verifies `attested` (proven by
  auditor sabotage §5); post-fix `unverified` + `None`. PASS.

## 3. Spec-consistency verdict (REQ-S4 revoke flags)

- REQ-S4 line 76: runbook is "revoke + re-add with `--seat` + `--rig`, V24-style mandate";
  scenario line 83 binds the flags to "**every mint command**" with "zero rig-less forms".
  The flag mandate is **mint-scoped by its own wording** — no normative sentence requires
  `--seat`/`--rig` on `revoke`. Runbook §1 steps 2/6 now use name-only
  `rig mcp token revoke <session>/send-identity`; every `token add` mint keeps
  `--seat` + `--rig`. Auditor independently ran `rig mcp token revoke --help`
  → `Usage: rig mcp token revoke [options] <name>` (no seat/rig flags) and
  `token add --help` → `--seat`/`--rig` present. F2's binary claim confirmed.
  **No contradiction: mandate reads mint-scoped only.** No finding. PASS.

## 4. Anti-stub + secrets

- Stub scan over the cycle diff (`TODO|FIXME|XXX|NotImplemented|pass #||| true|skipTest|@unittest.skip|assert True`
  in `send_identity.py`/`seed-rig.py`/`test_send_identity.py`): zero matches outside
  V28's own skip-detection strings and `verify-rigs.sh`'s pre-existing placeholder-gate
  regexes (which scan other files, not stubs in this change). The vacuous
  `assertIsNone(BEARER_RUN_RE.search(body) and None or None)` is gone, replaced by
  exact-token + absence assertions. `except` audit: `OSError`/`FileNotFoundError`/
  `(OSError, TimeoutExpired)` fail closed; `BaseException` re-raises; inner `OSError`
  `pass` is tmp-cleanup only; `Exception` → `unverified` deny. No swallowed errors. PASS.
- Secrets grep re-run by auditor over both evidence files:
  `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md
  docs/evidence/09-send-identity-rotation.md` → no output, exit 1. PASS.
- F4 §2b evidence: contains only redacted lengths (`or...XX (len=47, redacted)` — dots
  break any 40+ run; grep-clean per above), status codes (`goodbearer:405`,
  `badbearer:401`, `oldbearer-post-revoke:401`, `newbearer:405`,
  `oldbearer-post-readd:401`), and the `{"error":"unauthenticated",...}` refusal body.
  The no-restart claim is request-supported: revoke `rc=0` issued while the serve
  process kept running, immediately followed by `oldbearer-post-revoke:401` on the
  same process, then replacement `405` with old bearer still `401`. Quoted codes in
  sequence, not bare assertion. PASS.

## 5. QA spot-check (auditor sabotage, reverted, tree clean)

- SPOT-F5: removed the `if sender != expected_sender` block → single cross-seat test
  RED (`FAILED (failures=1)`, `- attested / + unverified` diff — the hole reopens exactly
  as claimed) → byte-restored from backup → full corpus `Ran 26 tests ... OK`.
  `git diff --stat -- scripts/send_identity.py` empty after restore. PASS.
- Baseline re-runs on the clean tree: `./scripts/verify-rigs.sh --check-only` →
  `SUMMARY: 36 checks passed, 0 failed` with V28 PASS line, exit 0. `git status --short`
  clean apart from this report. PASS.
- `red-proofs.log` QA-R2a…R2d entries match the QA report's verbatim claims and the
  auditor's independent SPOT-F5 reproduction (same sabotage shape, same RED signature).
  Failure signatures non-vacuous in both directions. PASS.

## 6. Notes (non-blocking)

- N1: rework-1 §F3 describes a `scripts/render-seat.py:662-664` (`die` → `sys.exit(2)`)
  code change, but the cycle diff contains zero `render-seat.py` lines and `die` already
  calls `sys.exit(2)` at base `12ee2ba`. The behavior the runbook now states (strict
  render exits status 2; `--allow-missing-secrets` writes disabled entry) is true of the
  base code (`render-seat.py:1038-1045` read from disk) — the rework entry misattributes
  a wording fix as a code fix. Report-accuracy nit only; no spec clause violated in code.
  Not a finding.

## Findings

None. F1…: none raised.

VERDICT: PASS
