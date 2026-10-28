# 09-send-identity-r2 QA acceptance report (Refs #9, never Closes #9)

Wave: 09-send-identity-r2 | Branch: fix/09-send-identity-r2 | Tip verified: a570bf1 (cycle base 5bbb846)
Scope: rework cycle 2 — 5 CodeQL findings on PR #128 (C1...C5) in
`scripts/send_identity.py` + `tests/test_send_identity.py`.
Verifier: acceptance subagent, 2026-10-28. No commits, no pushes.
Spec under test: `openspec/specs/send-identity/spec.md` (REQ-S1...S4 normative).

## Verdict: PASS — all 7 battery checks green, all 3 QA-R3 red-proofs RED-then-GREEN, no vacuous checks, no findings.

## 1. Battery results (current tip a570bf1, unmodified tree, real outputs)

| # | Check | Result |
|---|-------|--------|
| 1 | `./scripts/verify-rigs.sh --check-only` | exit 0 — `SUMMARY: 36 checks passed, 0 failed.` V28: `[PASS] V28 send-identity attestation (09-send-identity S1) green: binding rules + !cat render + 27 corpus tests pass + S0 evidence present`. V1–V27 `== V...` headers confirmed present and unrenamed (28 header lines, V1 through V28 in order). |
| 2 | `make test` | exit 0 — `Ran 532 tests in 120.095s` / `OK` (zero failures). |
| 3 | `python3 -m unittest tests.test_send_identity -v` | exit 0 — `Ran 27 tests ... OK`, including `test_reuse_path_emits_no_token_material` (new, rework-2) and `test_cross_seat_secret_cannot_authenticate_other_sender` (r1). Targeted 6-test subset (spoof / replay / cross-rig / bare-deny-triple / cross-seat / reuse-no-token) also `Ran 6 tests ... OK`. |
| 4 | `python3 scripts/audit_loop.py --self-test` | exit 0 — `SELF-TEST PASSED: audit_loop.py is ready for autonomous OpenCode execution.` |
| 5 | `python3 scripts/generate-rigs.py --check-idempotent` | exit 0 — `idempotence check passed (two consecutive runs byte-identical)`. The run restamped 16 registry files with provenance-only diffs (`resolvedCommit` cb3ba9a->a570bf1 + `canonicalUrl` embeds, zero other diff lines — verified via `git diff`); reverted with `git checkout -- registry/ rosters/`; `git status --short` clean. |
| 6 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md` | exit 1, no output (clean — zero unredacted bearer-shaped strings in evidence). |
| 7 | C-fixes on disk | (a) Fixture is `os.chmod(target, 0o640)` (`tests/test_send_identity.py:237`) with refusal semantics intact (`assertNotEqual(rc, 0)`, `assertIn("0600", err)`). (b) All 7 session/filename log interpolations in `issue_sender_binding` use `_session_log`/`_binding_log` (precomputed via `_redact_for_log`); every subprocess/exception detail flows through redacting `_fail`, every verify-side reason through redacting `_deny`; L350 raw `{e}` flows into `_deny` -> redacted; caller-facing ValueErrors (L75/L262/L268) carry identifiers/static text only. (c) Byte-identical stdout/stderr for real identifiers proven live: `_redact_for_log(x) == x` for `blue-x@rig-y`, `send-id-blue-x@rig-y.key`, `blue-x@rig-y/send-identity` (exit 0). |

## 2. Requirement regression check (REQ-S1...S4)

- REQ-S1 (attestation + seed issuance): V28 PASS covers binding rules + `!cat` render + 27 corpus tests; `test_issue_mints_with_seat_and_rig_scope` asserts `--seat`/`--rig` on mint and 0600 store; unattested-hold path intact (`test_missing_attestation_holds_unverified` OK). No regression.
- REQ-S2 (four forgery refusals): all four corpus tests green on tip (see check 3 subset); each class was additionally red-proven in prior series (S1a–d, QA-R3a–d, QA-R2a) and the r2 fixes touch no verify-path logic (diff is log-interpolation + fixture mask + one new test only). No regression.
- REQ-S3 (V28 gate + corpus): 36/0, V28 PASS, V1–V27 intact, 27/27 corpus, 532 `make test`. No regression.
- REQ-S4 (rotation runbook + secrets discipline): rotation evidence files unchanged and grep-clean (check 6); every new/changed log line routes through `_redact_for_log`; stores remain 0600 (`os.fchmod(tmp_fd, 0o600)`; refusal test enforces); `!cat` render untouched. No regression.

## 3. Red-proofs (QA-R3 series, appended to `docs/evidence/09-send-identity/red-proofs.log`; prior entries untouched)

| ID | Sabotage | RED (verbatim, non-zero exit) | Restore -> GREEN |
|----|----------|-------------------------------|-----------------|
| QA-R3a | Fixture `0o640` -> `0o644` (`tests/test_send_identity.py:237`) | Probe asserting `mode & 0o007 == 0`: `AssertionError: RED: fixture is world-readable (py/overly-permissive-file class, mode 0644)`, exit 1. Companion: refusal test still `OK` under 0644 — proving H1 semantics (any non-0600 refuses; mask change is meaning-preserving). | `git checkout -- tests/test_send_identity.py`; probe GREEN (mode 640, world-bits 0, still != 0600); refusal test OK; status clean. |
| QA-R3b | Reuse-ok sink back to raw `f"ok {session}: ... (reuse {binding_path.name})"` (`scripts/send_identity.py:168`); drove issue->reuse with `"A"*45` session | Guard asserting no 40+ run on reuse stdout/stderr: `AssertionError: RED: bearer-shaped run leaked on reuse stdout: 'ok AAAA...(45)...: sender binding already issued (reuse send-id-AAAA...(45)....key)'`, exit 1 — sink is live, the helper is what stops it (H2). | `git checkout -- scripts/send_identity.py`; guard GREEN (`no bearer-shaped runs`, exit 0); `test_reuse_path_emits_no_token_material` OK; status clean. |
| QA-R3c | `mv scripts/send_identity.py` away (pre-fix shape) | `verify-rigs.sh --check-only`: 3 V28 FAILs (`cannot load...`, `unreadable...`, `tests.test_send_identity failed:`), `SUMMARY: 35 checks passed, 4 failed.`, exit 1. | Moved back byte-identical; V28 PASS + `SUMMARY: 36 checks passed, 0 failed.`, exit 0; `git status --short` clean, `git diff --stat` empty. |

No vacuous checks found: every sabotaged check turned RED and every restore turned GREEN.

## 4. Findings

None. Numbered findings F1...: (empty — nothing failed, nothing skipped, no stubs introduced, no requirement regressed).

## 5. Tree state on handover

`git status --short` shows only the two intended files:
- `M docs/evidence/09-send-identity/red-proofs.log` (QA-R3 series appended)
- `?? docs/reports/09-send-identity-r2-qa.md` (this report)

All sabotage fully reverted (`git diff --stat` on code/test paths empty; byte-identical restores verified). Nothing else modified. No commits, no pushes.
