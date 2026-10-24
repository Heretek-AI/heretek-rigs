# remediate-sandbox QA report (Wave 2, audit #66 M4–M5)

- Stage: remediate-sandbox | Worktree: `.lane/trees/remediate-sandbox`
- Spec: `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md` (M4, M5, F1–F3, F7–F9, Gotchas 1–5, 8)
- Implementation report: `docs/reports/remediate-sandbox-implementation.md`
- Verdict: **PASS** (all acceptance checks green; 6 sabotages red-proofed, 1 gap found — see S2a)
- Evidence: `docs/evidence/remediate-sandbox/red-proofs.log` + `/tmp/opencode/qa-*.log`, `/tmp/opencode/s{1,2,4,6}-*.log`, `/tmp/opencode/s3.log`

## Baseline (unmodified tree — all green before sabotage)

| # | Check | Result |
|---|---|---|
| M4.1 | `bash scripts/gate-role.sh sabotage-qa-tester` | PASS — exit 0, 43 ok / 0 FAIL, bash_allow has 11 verbs, zero runner-ish (`test\|stryker\|mutant\|mutmut\|pytest\|cargo\|garak\|pyrit\|promptfoo\|npx\|clippy`) |
| M4.2a | F2 corpus under `scripts/seat-sandbox.sh` (bwrap 0.13.1) | PASS — `tests/chaos/t.txt` rc=0; `root.txt` rc=1 Read-only; store key `No such file` rc=1; net unreachable rc=1; `git log/status` rc=0; bad usage rc=126 |
| M4.2b | `seat-sandbox.sh` vs spec verified block | PASS — bwrap core byte-identical (programmatic diff); file executable; only addition is the documented M4 `sandbox.env` bootstrap preamble |
| M4.3 | `generate-rigs.py` twice | PASS — run2 identical run3 byte-identical (idempotent); only delta vs commit is the known-accepted `resolvedCommit` re-lag (16 registry files x 1 line); tree restored via `git checkout -- registry/` |
| M4.4 | shellPath + NOTES + rollout split | PASS — committed `pi-settings.json` shellPath = absolute path of `seat-sandbox.sh` (exists +x); `HERETEK_SANDBOX_WRITE` mechanism in NOTES:184-189; rollout split in NOTES:219-220,246 + report Rollout section (sandbox needs relaunch/RPC reload, NOT no-bounce; config.json changes canary-then-fleet) |
| M5.5 | `bash scripts/gate-role.sh go-backend-eng` | PASS — exit 0, 43 ok / 0 FAIL incl. `-u`, `--cc`, `env`-prefixed `OPENRIG_SESSION_NAME` probes + anti-overblock allow |
| M5.5-F9 | Bare-leading vs env-prefixed form, live | PASS — bare `OPENRIG_SESSION_NAME=x rig whoami` EXECUTES (rig resolves `Session: x`); `env ...` DENIES `isError:true` (`*OPENRIG_SESSION_NAME=*`); deviation recorded in NOTES:236-239 exactly as claimed |
| M5.6 | `send-authenticated.sh` | PASS — env-set gives rc=2 refusal; `{"state":"failed","persisted":false}` gives rc=4; persisted-false gives rc=6; failed-state gives rc=5; createWarning gives rc=7; pending/in-progress + persisted gives rc=0; fleet member-id sources give rc=2; `operator --dry-run` gives rc=0 |
| M5.7 | `./scripts/verify-rigs.sh --check-only` / `make test` | PASS — `SUMMARY: 28 checks passed, 0 failed.` (N=28); `make test`: `Ran 210 tests ... OK` |
| M5.8 | Deny-tuple sync | PASS — renderer emitter tuple identical `:588` mirror, 31/31 ordered identical; all 14 M5 git-diff denies in both; `:1158` asserts cover all 16 new denies |
| F7/F8 | Fleet-wide strips | PASS — zero `builtin:locked` seats hold runner verbs (all 18 dumped); `dependency-patcher` (`builtin:standard`, legitimately keeps test verbs) has zero `commit`/`checkout` grants |
| G1/G3/G4/G5/G8 | Gotchas | PASS — scratch under `/var/tmp` (not `/tmp`); tuples in sync (see gap S2a); `safe_dump` only in `write_yaml` for generated leaves, never `fleet.yaml`; V12 asserts wrapper exists +x and `bwrap` resolves; gate-role canary seed intact (:32-40) |
| G2 | No in-tree-secret masking claim | PASS (observation) — implementation never claims the jail masks committed secrets; NOTES:189 documents coarse-bind limitation + pps as fine gate, F2/store-mask scoped to out-of-tree store |

## Red-proofs (sabotage → RED → revert → GREEN)

| ID | Sabotage | RED proof | GREEN restore |
|---|---|---|---|
| S1 | `+pytest*` on sabotage-qa-tester (fleet.yaml) | `pytest --version` probe ALLOWS, `pytest 9.1.1` executes (isError:false) | `git checkout` then re-render then probe DENIES (isError:true). NON-VACUOUS |
| S2a | Remove `*--unified*` from `:588` mirror only | **STAYS GREEN** (28/0, exit 0) — **GAP, see below** | `git checkout` (clean) |
| S2b | Remove `*--unified*` from renderer emitter only | verify-rigs exit 1: `27 passed, 2 failed` (`must emit terminal "*--unified*"`, unit KeyError) | `git checkout` then final verify 28/0. NON-VACUOUS |
| S3 | shellPath pointing at `/path/that/does/not/exist` (scratch render) | fail-closed check gives `Custom shell path not found`, isError:true. NON-VACUOUS | scratch-only, nothing to revert |
| S4 | Neutralize receipt state gate (`sys.exit(5)` to `pass`) | `failed` receipt gives rc=0 `created q-3 state=failed` (delivery falsely claimed) | `git checkout` then same fake gives rc=5. NON-VACUOUS |
| S5 | Disable tmpfs store mask (scratch script copy) | store file readable, rc=0 | unmodified script gives `No such file`, rc=1. NON-VACUOUS |
| S6 | Remove `* -u*` from renderer; probe `git log -u` on write-root file | full diff incl. canary exfiltrated (RED) | `git checkout` then re-render gives `Denied by policy: 'bash' (rule '* -u*')`, 0 exfil. NON-VACUOUS |

Harness insight (S6): pps bash file-arg policing denies *existing* files outside write roots (path rule `*`) while nonexistent paths allow at policy layer — so decisive exfil probes must use existing files inside write roots; gate-role's canary-seeded `fleet/` probes remain decisive via the path-deny interaction.

## GAP (not a failure of the implementation — a verifier-hardening follow-up)

- **S2a: no tuple-sync assert.** Nothing in-repo compares the `render-seat.py` emitter tuple with the `verify-rigs.sh:588` mirror tuple. Weakening the *verifier* (mirror removal) stays green; only weakening the *renderer* goes red (S2b, via `:1158` asserts + unit tests). Real protection (committed leaves) was intact during S2a — only verifier coverage narrowed. Suggested M10/PR follow-up: assert the two tuples are identical (or derive one from the other). QA did not patch code (rules).
- Pre-existing cosmetic (already in NOTES, unchanged): V6 ok() message reads `7/7` while `test_render_seat.py` runs 9 tests; gate keys on returncode.

## Final state

- `git status --short`: clean except untracked `docs/evidence/remediate-sandbox/` (this QA's log).
- Post-revert `verify-rigs --check-only`: `SUMMARY: 28 checks passed, 0 failed.` (exit 0).
- No commits made; no production/test code modified (all sabotage reverted via `git checkout -- <file>`; S3/S5 used scratch copies).
