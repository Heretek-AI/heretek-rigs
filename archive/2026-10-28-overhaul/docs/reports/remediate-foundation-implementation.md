# remediate-foundation implementation report (Wave 1, audit #66 M0–M3)

- Stage id: remediate-foundation (Wave 1 of audit #66 remediation)
- Branch: remediate/audit-66-p0-p1-foundation
- Worktree: /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-foundation
- Spec: docs/REMEDIATION_IMPLEMENTATION_PROMPT.md (M0, M1, M2, M3 + Verified facts F1–F6, Gotchas 1–8)

## Deliverables

- M0: docs/NOTES.md #66 section appended (baseline: verify 27/0, make test 125 OK / 7 suites, orphans, bwrap 0.13.1, unshare OK, pps 41.0.0 / pi 1.3.0 pins).
- M1: shellPath sandbox-hook spike reproduced in scratch (allowed `date +%s` shows MARKER, denied `date +%s; id` denied by policy with no marker = enforcer-first); outputs + not-hot-reloaded rollout note in NOTES.
- M2: scripts/render-seat.py fail-closed on missing/drifted @gotgenes/pi-permission-system (no --allow-missing escape).
- M3: scripts/verify-rigs.sh new == V12 == tool-existence block; Makefile test: now 10 suites; tests/test_render_seat.py fixture carries pinned pps + 2 new M2 tests (9 total).

## Files changed

| File | Change |
|---|---|
| docs/NOTES.md | M0/M1/M2/M3 log sections appended (nothing overwritten) |
| scripts/render-seat.py | M2 guard after pps_pkg built: die on missing package.json ("is mandatory"), assert version 41.0.0 |
| scripts/verify-rigs.sh | == V12 == appended after V11 (M2-guard source assert, per-seat packages[0] assert, per-seat MCP command resolution with [NOTE] listing) |
| Makefile | test: target + tests/test_build_canary.py, tests/test_check_envelope.py, tests/test_live_health.py |
| tests/test_render_seat.py | fixture tools dir with pinned pps 41.0.0; packages assertion follows self.tools; +2 M2 tests |

Commits (one per milestone, explicit git add, attribution trailers present):
- 2b6c03e remediate(#66): M0 baseline and NOTES section
- 8ef57a9 remediate(#66): M1 shellPath sandbox spike evidence
- 376a7f4 remediate(#66): M2 fail-closed on missing permission extension
- 589b966 remediate(#66): M3 V12 tool-existence gate and orphan suite wiring

## Acceptance outputs (all green, run 2026-10-24 in-worktree)

1. `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 28 checks passed, 0 failed.` (exit 0; N=28, i.e. 27 + V12)
2. `make test` → `Ran 208 tests ... OK` (all 10 suites confirmed in output: test_render_seat, test_sweep_typed_blocks, test_regen_gate, test_queue_id_discipline, test_queue_json_discipline, test_reconcile, test_generate_trackers, test_build_canary, test_check_envelope, test_live_health)
3. `HERETEK_TOOLS=/nonexistent HERETEK_SECRETS=$(mktemp -d) python3 scripts/render-seat.py --role exec-director --rig executive-and-architecture --pod exec --allow-missing-secrets --out $(mktemp -d)` → `error: /nonexistent/... is mandatory`, exit=2; real HERETEK_TOOLS render → exit 0; 40.0.0 drift probe → `version 40.0.0, need 41.0.0`, exit=2
4. M1 marker evidence recorded in docs/NOTES.md (allowed: `MARKER-SHELLPATH-HIT: date +%s` + exit_code 0; denied: `Denied by policy` + isError true, no marker)

## How to reproduce

```bash
cd <worktree>
./scripts/verify-rigs.sh --check-only 2>&1 | tail -2        # expect 28/0
make test 2>&1 | tail -3                                     # expect 208 OK
S=$(mktemp -d); D=$(mktemp -d); HERETEK_TOOLS=/nonexistent HERETEK_SECRETS=$S \
  python3 scripts/render-seat.py --role exec-director \
  --rig executive-and-architecture --pod exec --allow-missing-secrets --out $D; echo $?
  # expect exit 2 + "is mandatory"
```

## Self-audit notes (unfinished / deferred, all stated plainly)

- M3 severity decision (documented in NOTES): V12 hard-fails only on the mandatory pps / M2-guard; host-missing MCP binaries (r2mcp, playwright-mcp, chrome-devtools-mcp, mcp-server-mobile, mcp-openapi-schema-explorer, mcp-server-memory, kubernetes-mcp-server) are listed per seat via [NOTE] without failing. Host tooling completeness is M9 scope; the V12 block names each gap so M9 can promote them to fail-closed.
- V6 ok() message still reads `(7/7 unit tests)` while test_render_seat.py now runs 9 tests; left untouched per the never-reword-V1–V11 rule (gate keys on returncode 0). Cosmetic only.
- M1 scratch dir cleaned (python shutil.rmtree); no experiments ever entered the repo tree.
- No QA dispatch performed (per instructions); tree holds implementation commits only, no evidence files.
- test_manifest_closure.py / test_policy_verifier.py remain Makefile-unwired (verify-rigs V8/V9 only) — untouched per brief (M3 wired only the 3 named orphans).
- Stopping point: M0–M3 complete; M4+ owned by later waves.
