# Verification report: remediate-foundation (Wave 1, audit #66 M0–M3)

- Stage/wave: remediate-foundation
- Worktree: /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-foundation
- Verify date (UTC): 2026-10-24
- Spec: docs/REMEDIATION_IMPLEMENTATION_PROMPT.md (M0, M1, M2, M3 + F1–F6, Gotchas 1–8)
- Implementation report: docs/reports/remediate-foundation-implementation.md
- QA report: docs/reports/remediate-foundation-qa.md
- Red-proofs: docs/evidence/remediate-foundation/red-proofs.log
- Head verified: 848e790
- Unity binding: none

## Method

Read AGENTS.md, the full remediation spec, both reports, and the red-proofs log from disk.
Re-ran every acceptance command myself in the worktree; inspected all diffs
`8ec5373..HEAD`. No source files modified by this audit.

## 1. M2 fail-closed pps guard (spec M2, #67) — HOLD

- `scripts/render-seat.py:137-144`: `die()` on missing `package.json`
  (`"... is mandatory"`) and on version drift (`need 41.0.0`).
- No `--allow-missing` escape: the guard keys on `check_secret_fs`, which is
  hardcoded `True` at the sole call site (`:610`); no CLI flag flips it.
  `--allow-missing-secrets` only affects the secrets path (`:198-303`).
- Re-ran: `HERETEK_TOOLS=/nonexistent ... --allow-missing-secrets` →
  `error: ... is mandatory`, exit 2. Real-tools render → exit 0
  (`rendered exec-exec-director@executive-and-architecture`).
- `fleet/fleet.yaml` is only `safe_load`ed by `generate-rigs.py:529`;
  `write_yaml`/`safe_dump` targets generated leaves only. No `safe_dump` on
  `fleet.yaml` introduced (Gotcha 4 holds; `generate-rigs.py` untouched).

## 2. V12 tool-existence gate (spec M3, #67/#74/#82) — HOLD

- `== V12 ==` appended at `scripts/verify-rigs.sh:1621`, after V11.
  Diff `8ec5373..HEAD` shows zero `-` lines in `verify-rigs.sh`:
  V1–V11 not renumbered or reworded.
- V12 fail-closes on: M2-guard source strings absent, per-seat
  `runtime/pi-settings.json` `packages[0]` not the mandatory pps, tools-dir
  pps missing/drifted. Host-missing optional MCP binaries are per-seat
  `[NOTE]` lines (naming server+seat+path, incl. `radare2`/`r2mcp`) with no
  failure — no false red on hosts lacking optional binaries.
- Re-ran `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 28 checks passed,
  0 failed.` (exit 0; 27 baseline + V12), with the missing-MCP `[NOTE]` set
  present. Matches the spec M3 acceptance criterion.

## 3. Makefile 10-suite wiring (spec M3, #82) — HOLD

- `Makefile:38` lists all 10 suites (+`test_build_canary`,
  `test_check_envelope`, `test_live_health`).
- Re-ran `make test` → `Ran 208 tests`, `OK`; all 10 suite files present in
  output. `test_manifest_closure.py`/`test_policy_verifier.py` remain
  Makefile-unwired (verify-rigs V8/V9 only) — explicitly out of brief scope
  and disclosed in NOTES/implementation report, not hidden.

## 4. docs/NOTES.md #66 section — HOLD

- M0 baseline counts recorded (`:155-160`): verify 27/0, `make test` 125 OK /
  7 suites, orphans named, `bwrap 0.13.1`, `unshare` exit 0, pps 41.0.0 /
  pi 1.3.0 pins.
- M1 marker evidence (`:162-166`): allowed shows
  `MARKER-SHELLPATH-HIT` + `exit_code 0`; denied shows policy denial +
  `isError true` with no marker (enforcer-first); explicit
  not-hot-reloaded rollout note (RPC reload/relaunch for M4).
- M2/M3 sections (`:168-179`) record acceptance outputs, the severity
  decision, the fixture adaptation rationale, and the cosmetic V6-message
  discrepancy (left untouched per the never-reword rule).

## 5. Stub / weakening / hand-edit scan — CLEAN

- No `TODO/FIXME/TBD/PLACEHOLDER/{{...}}` in changed code; no new
  `except: pass` / swallowed errors; the 2 new `test_render_seat.py` tests
  assert `returncode == 2` + stderr regex (fail-closed, non-vacuous).
- `git diff 8ec5373..HEAD -- specs/ rigs/ rosters/ registry/` is empty —
  no generated-leaf hand-edits. `git diff -- fleet/` is empty.
- Fixture change (`/opt/hr-tools` → scratch tools dir with pinned pps
  41.0.0) is an invariant adaptation required by the new fail-closed guard,
  paired with 2 new tests covering the previously-impossible arms — not a
  weakening. V6 `7/7` message text untouched per spec rule 9.

## 6. Commit discipline — HOLD

- One commit per milestone, explicit file lists, both attribution trailers
  (`Co-Authored-By`, `Claude-Session`) on all four:
  `2b6c03e` M0 (NOTES), `8ef57a9` M1 (NOTES), `376a7f4` M2
  (NOTES+render-seat.py), `589b966` M3
  (Makefile+NOTES+verify-rigs.sh+test_render_seat.py).
- Plus `3d9851a` (stage implementation report) and `848e790` (QA
  red-proofs + QA report). Implementation commits intact; nothing rewritten.

## 7. Red-proof audit — CREDIBLE

- Log records 4 sabotages with break → RED (named failure signatures +
  non-zero exits / count deltas) → `git checkout --` revert →
  diff-identical → green. Signatures are non-vacuous (dual-front RED on
  sabotage 1 and 4C; suite-count criterion correctly identified as the
  non-vacuous check for sabotage 3 since unittest exits 0 regardless).
- `git status --short` is clean (empty) at verification time — all
  sabotages reverted, no stray modifications. QA added only evidence/report
  files, as intended.

## Findings

None. Every M0–M3 deliverable, seam, and acceptance command in the brief
holds against the code on disk, verified by independent re-execution.

VERDICT: PASS
