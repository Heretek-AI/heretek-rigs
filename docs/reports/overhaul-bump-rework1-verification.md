# overhaul-bump rework cycle 1 — drift-guard re-verification (binding re-audit)

- **Stage/wave id:** overhaul-bump rework cycle 1 re-audit (prior VERDICT: PASS at `831e811`; rework `e624e1a` + evidence `d672592` since)
- **Worktree:** `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-bump` (branch `feat/overhaul-bump`)
- **Date (UTC):** 2026-10-27
- **Inputs read from disk:** `AGENTS.md`, `openspec/changes/overhaul-bump/{proposal.md,design.md,tasks.md,specs/bump/spec.md}`, `docs/reports/overhaul-bump-implementation.md`, `docs/reports/overhaul-bump-rework1.md`, `docs/evidence/overhaul-bump/red-proofs.log`, `docs/evidence/overhaul-bump/rework1-red-proofs.log`
- **Rule:** no code fixed, nothing committed. `git status --short` clean at start and end (all wave work already committed in `e624e1a`/`d672592`).

## 1. Scope of rework since prior PASS (`831e811...HEAD`)

Exactly 5 files (plus nothing else):

| File | Change |
|---|---|
| `openspec/changes/overhaul-bump/specs/bump/spec.md` | REQ-BUMP2 narrowed with idempotence-with-0.7.4-vendor deferral parenthetical; scenario matched |
| `openspec/changes/overhaul-bump/tasks.md` | T2 acceptance `AND` → `&&` (one line) |
| `scripts/verify-rigs.sh` | V18 host-version fail-closed gate + ok-split (only hunk) |
| `docs/reports/overhaul-bump-rework1.md` | New rework report (untracked input, audit-neutral) |
| `docs/evidence/overhaul-bump/rework1-red-proofs.log` | New QA evidence (untracked input, audit-neutral) |

## 2. F1 — deferral is honest (no false idempotence HOLD)

- **PASS.** `spec.md:12` requires `--check-idempotent` to pass **with the deferral parenthetical inline** (`idempotence-with-0.7.4-vendor deferred to Wave B: the default resolver now sources installed 0.7.4 skills per generate-rigs.py:623-643, so a run here would vendor Wave B content; this wave holds by empty leaf diff`); scenario `:15` matches. No claim of a live run is made.
- Generator inputs untouched: `scripts/generate-rigs.py:60-61` still `OPENRIG_VERSION = "0.7.2"` / `OPENRIG_COMMIT = "8b180689"`; `fleet/mcp-servers.yaml:273` still `builtin:rig-mcp-serve-http@0.7.2`; `fleet/fleet.yaml` header still `@openrig/cli@0.7.2`.
- `git diff 88cd930...HEAD -- specs rigs rosters registry` → empty; `--stat` likewise empty. Hold-by-empty-leaf-diff is truthful. The live `--check-idempotent` run was correctly NOT executed (it would vendor Wave B bytes into generated leaves; rework report §F1 cites the resolver path `generate-rigs.py:623-643/1999/2004/2044-2051/1129-1231`).

## 3. F2 — `&&` fix is the only tasks.md change

- **PASS.** `git diff 831e811...HEAD -- openspec/changes/overhaul-bump/tasks.md` is exactly one line: T2 acceptance `AND` → `&&`. No other tasks.md hunk.
- Fixed command re-run end-to-end by this auditor: `./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test` → exit 0 (`SUMMARY: 35 checks passed, 0 failed` + `SELF-TEST PASSED`).

## 4. F3 — V18 edit is minimal and fail-closed

- **PASS.** The `scripts/verify-rigs.sh` hunk (`git diff 831e811...HEAD`) adds only: a version probe (`rig --version`, regex `\d+\.\d+\.\d+`, `fail("V18/#98: host rig --version is not 0.7.4 …")` on nonzero rc / unparseable / mismatch, exception → unreadable) at the top of the rig-present branch, and an ok-split (rig-present keeps the original `… clean on installed 0.7.4` string byte-identical; rig-absent prints `… native-verb validation skipped (no rig on PATH)` with no version claim).
- Zero `== V` header lines touched (`git diff … | grep -c '^[-+].*== V'` → 0); all 22 V-header print lines V1–V24 present unrenamed; SUMMARY logic untouched (single `SUMMARY:` print at `:227`; V19/V22/V23/V24 remain FAIL-ONLY, count frozen).
- Behavior re-verified live by this auditor (shims in `/tmp/opencode/reaudit-v18/`, real binary untouched):
  - Wrong-version shim (`rig --version` → `0.7.2 (8b180689)`) → exit **1**, `[FAIL] V18/#98: host rig --version is not 0.7.4 (got 0.7.2 (8b180689))…` + V19 cascade `SUMMARY: 33 checks passed, 4 failed` (non-vacuous).
  - Rig absent (`PATH` without rig) → exit **0**, `SUMMARY: 35 checks passed, 0 failed`, PASS line carries the skipped-claim, `installed 0.7.4` count = 0 (no false claim).
  - Correct host → exit **0**, 35/0, original `… clean on installed 0.7.4` claim intact.
- Pre-existing V18 fail conditions unchanged (only added lines precede them; green-path `failures == _v18_before` logic intact).

## 5. No scope creep beyond the three findings

- **PASS.** Full `git diff --name-only 88cd930...HEAD` = the 8 true-pin files + ledger + spec/design/proposal/tasks + `scripts/verify-rigs.sh` + 3 reports + 2 evidence logs. No file outside the wave's pin table, the three finding fixes, and audit artifacts. `tasks.md`/`spec.md` diffs contain only the F1/F2 lines; `verify-rigs.sh` diff since `831e811` is only the V18 hunk.

## 6. Generator rule

- **PASS.** `git diff 88cd930...HEAD -- specs rigs rosters registry fleet/skills-lock.json schemas fleet/fleet.yaml fleet/mcp-servers.yaml scripts/generate-rigs.py` → empty. No hand-edit of generated leaves; zero DIRTY.

## 7. No stubs / skips / secrets

- **PASS.** Rework diff (`831e811...HEAD`) contains no `TODO`/`FIXME`/`NotImplemented`/`skip(`/`|| true` additions; no test skips added; no committed secret-shaped strings (`ghp_|github_pat|sk-ant|AKIA|PRIVATE KEY|or_[A-Za-z0-9]{20,}` → no hits).

## 8. Re-run results (real output, this audit)

| Command | Exit | Signature |
|---|---|---|
| `rig --version` | 0 | `0.7.4 (6d9e8e27)` |
| `./scripts/verify-rigs.sh --check-only` | 0 | `SUMMARY: 35 checks passed, 0 failed.` (+ V22/V23/V24 info lines) |
| `python3 scripts/audit_loop.py --self-test` | 0 | `SELF-TEST PASSED` |
| `python3 -m pytest tests/test_build_canary.py::CanaryCatalogPins::test_canary_scope_only` (ONLY this test, per orders — not fixed) | 1 (RED, expected) | Identical pre-existing signature: `AssertionError: Lists differ` at `tests/test_build_canary.py:181`, first differing `a11y-specialist` vs `ai-red-teamer`, `First list contains 44 additional elements`, first extra `brand-copy-spec`, `Diff is 1304 characters long` — matches both red-proofs logs byte-for-cause |

`make test` full suite was NOT re-run beyond the single canary test per stage orders (both evidence logs already record 359-run/1-failure twice; this wave touches neither `fleet/fleet.yaml` nor the test, and the signature above is identical).

## 9. Red-proof evidence audit

- `red-proofs.log`: baseline GREEN + V13 sabotage RED (`ARG OPENRIG_VERSION=0.7.2` → exit 1, `33 passed, 4 failed`) + restore GREEN + canary cause proof (102-closeout `892e1a7`, 51× `bash_deny`) — non-vacuous, `git status` clean claim consistent with committed state.
- `rework1-red-proofs.log`: F3a RED (exit 1, new fail line) / F3b GREEN-silent (exit 0, claim count 0) / F3c GREEN-with-claim + S1 (V13) and S2 (V18 expectation `"9.9.9"` → RED) sabotages, each restored GREEN. Non-vacuous. This auditor independently reproduced F3a/F3b/F3c with matching exit codes and signatures (§4).

## 10. Final state

- `git status --short` → empty (clean). No code fixed, no commit made by this audit. Scratch shims/logs live only under `/tmp/opencode/reaudit-v18/` and `/tmp/opencode/canary-reaudit.log`.

VERDICT: PASS
