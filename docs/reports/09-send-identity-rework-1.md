# Rework 1 report — wave 9 (09-send-identity, Refs #9)

Date: 2026-10-28. Worktree: `.lane/trees/09-send-identity-r1`
(branch `fix/09-send-identity-r1`, base `main @ 12ee2ba`). Rework 1 of max 3.
All review findings below were verified against current code from disk before
any edit; file paths and code quoted in review text were treated as untrusted.

## Per-finding verdicts (F1…F10)

| ID | Verdict | Evidence |
|---|---|---|
| F1 | VERIFIED-FIXED | `openspec/changes/` holds only `archive/` (change archived in `7c4953b`); AGENTS.md docs-map line pointed at the unarchived path. Fixed to `openspec/changes/archive/2026-10-28-09-send-identity/`. |
| F2 | VERIFIED-FIXED | `rig mcp token revoke --help` on the pinned binary (`@openrig/cli@0.7.4`) shows `Usage: rig mcp token revoke [options] <name>` — name-only, no `--seat`/`--rig`. Both revoke invocations in the rotation runbook (§1 steps 2, 6) reduced to the name-only form; parenthetical now states the tool offers no such flags. Mint (`token add`) keeps `--seat` + `--rig` (verified in its `--help`). |
| F3 | VERIFIED-FIXED | `scripts/render-seat.py:662-664` (`die` → `sys.exit(2)`); send-identity block lines 1037-1045: strict render dies on missing binding, degraded render writes `{"sender","enabled":false}`. Runbook failure-modes paragraph rewritten to state exactly that (exit status 2 vs disabled entry + UNVERIFIED). |
| F4 | VERIFIED-FIXED | Reproduced live in scratch (`/tmp/09-r1-bearer-revoke`, since deleted): scratch daemon `127.0.0.1:18442` + `rig mcp serve --http` on `127.0.0.1:18441`. Baseline good bearer `405` / bad bearer `401`; after `revoke` (rc=0) with the serve process still running, old bearer `401 {"error":"unauthenticated",...}`; replacement bearer `405`, old bearer still `401`. Recorded verbatim (redacted, no 40+ runs) as new §2b, kept distinct from the step-7 attestation re-key evidence. The no-restart claim is now supported by the new request behavior. |
| F5 | VERIFIED-FIXED | `verify_attestation` checked `rig != expected_rig` but never the sender: a seat-A secret minting a seat-B attestation verified `attested` with sender B (proven by sabotage run below). Added required keyword-only `expected_sender` + sender-mismatch `unverified` denial; all in-repo callers (tests) updated to pass it. New corpus test `test_cross_seat_secret_cannot_authenticate_other_sender` proves the hole closed. |
| F6 | VERIFIED-FIXED | V28 parsed only `Ran N tests` + rc: a run with skips (`OK (skipped=k)`, rc=0) would count skips toward the ≥20 floor. V28 now parses `skipped=k`, fails on any skip, and floors on executed tests (`ran - skipped`). Only the cited parsing lines touched; V1–V27 byte-identical. |
| F7 | VERIFIED-FIXED | `tests/test_send_identity.py:178` was `assertIsNone(BEARER_RUN_RE.search(body) and None or None)` — always None, vacuous. Replaced with: binding file matches `^fakesendidentitytoken\d{6}$` (the issued token), token absent from captured stdout/stderr, no bearer-shaped run in either stream. |
| F8 | VERIFIED-FIXED | HANDOFF.md §5 quoted `35 checks passed`; ground truth is 36 (AGENTS.md:15, README.md:47, USER_GUIDE.md:127, live SUMMARY). Fixed to 36, 0 failed preserved. |
| F9 | VERIFIED-FIXED (nit) | `seed-rig.py main()` executed `send_identity.py` at startup unconditionally. Module load moved behind `_load_si09_mod()` (cached), called only in the branch that issues a sender binding; unbound/dry-run/policy-only paths never load it. |
| F10 | VERIFIED-FIXED (nit) | `_seed_rig_mod()` re-executed `seed-rig.py` on every call (including per `verify_attestation` for `_redact` alone). Now cached in module-global `_SEED_RIG_MOD`. |
| F11 | SKIPPED | Embedded review-tool promotion (`coderabbit review --agent`); explicitly out of scope per task brief. |

No finding was skipped as invalid — all ten held against current code.

## F5 red-proof (mandatory sabotage cycle)

1. Removed the `if sender != expected_sender` block from `verify_attestation`.
2. `python3 -m unittest tests.test_send_identity.AttestationVerifyTests.test_cross_seat_secret_cannot_authenticate_other_sender` → **FAILED** (`attested` vs expected `unverified`): seat-A secret authenticated a seat-B attestation — hole proven real.
3. Restored the block → full corpus `Ran 26 tests ... OK`.

## Acceptance outputs

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 36 checks passed, 0 failed`, V28 line: `V28 send-identity attestation (09-send-identity S1) green: binding rules + !cat render + 26 corpus tests pass + S0 evidence present`. Exit 0.
- `make test` → `Ran 531 tests ... OK` (was 530; +1 cross-seat test). Exit 0.
- `python3 -m unittest tests.test_send_identity -v` → `Ran 26 tests ... OK`. Exit 0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`. Exit 0.
- `python3 scripts/generate-rigs.py --check-idempotent` → `idempotence check passed (two consecutive runs byte-identical)`, exit 0 (run post-commit; the expected `resolvedCommit` re-lag dirt was committed as `ac9869e`, working re-lag from the check run itself reverted — known/accepted policy).
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md` → no output (exit 1). Clean.
- `git status`: 8 files in fix commit + 16 registry leaves in provenance commit; zero under `openspec/` (archived spec/tasks byte-identical).

## Commits

- `2aff663` `fix(09-send-identity): address PR #128 review findings R1 (Refs #9)` — F1…F10 + this report.
- `ac9869e` `chore(09-send-identity): regenerate leaves for provenance (Refs #9)` — registry-only `resolvedCommit`/`canonicalUrl` re-lag, packageDigests untouched (wave precedent `e04a7f8`).
- (this commit) report finalization with post-commit acceptance state.

## Self-audit notes

- Nothing unfinished: all acceptance gates green; F4 evidence actually reproduced (scratch daemon + serve since torn down, scratch dir deleted); no secrets in evidence (grep-clean, dummy seat, redacted lengths only).
- V28 edit confined to the skip-parsing lines; confirmed V1–V27 untouched via `git diff` (only V28 hunk in `verify-rigs.sh`).
- Did not open a PR (coordinator owns that); did not run `coderabbit` (F11 out of scope); never pushed; no `--force`.
