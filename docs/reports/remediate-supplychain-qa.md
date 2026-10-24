# QA report — remediate-supplychain (Wave 4, M9–M10, audit #66) — FINAL wave

- Stage: `remediate-supplychain` | Branch: `remediate/audit-66-p0-p1-supplychain`
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-supplychain`
- QA date (UTC): 2026-10-24 | Verdict: **PASS** (with 3 honest follow-ups, none merge-blocking)
- Implementation report: `docs/reports/remediate-supplychain-implementation.md`
- Evidence: `docs/evidence/remediate-supplychain/red-proofs.log`

## Baseline (unmodified tree, before any sabotage)

| Check | Command | Result |
|---|---|---|
| Verify | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 29 checks passed, 0 failed`, exit 0 |
| Unit tests | `make test` | `Ran 257 tests ... OK` (11 suites), exit 0 |
| Evaluator | `python3 scripts/audit_loop.py --self-test` | `SELF-TEST PASSED` (15 vectors), exit 0 |
| Render fail-closed (#67) | `HERETEK_TOOLS=/nonexistent ... render-seat.py ... --allow-missing-secrets` | exit 2, "mandatory" |
| Locked-seat gate (#68) | `bash scripts/gate-role.sh sabotage-qa-tester` | exit 0 |
| Diff-deny gate (#69) | `bash scripts/gate-role.sh go-backend-eng` | 43 ok incl. new `-u/--cc` + env-prefixed probes |

## M9 acceptance

1. **Verify 29/0** — PASS (N=29; 28 carried + new V13 block).
2. **make test, 11 suites** — PASS. The 11th suite is `tests/test_generate_supplychain.py` (NEW, 8 tests: archive byte-fidelity, dirty/unknown-sha/missing-path dies, attestation 4-ways). Wired, non-vacuous: each test asserts a fail-closed `SystemExit(2)` or byte-equality ground truth on synthetic `/tmp` repos — never the live tree.
3. **Digest pins** — PASS. All 10 sidecar images `tag@digest` (2 tagless `repo@sha256:` allowed, strictly stronger), all 64-hex. NOTES M9 lists all 10 resolutions with `skopeo inspect` commands: 4 phantom refs corrected (socket-proxy `:0.5.0`, browserless org+tag, firecrawl org+tag, ghidra org), 3 phantom tags fixed (searxng, radare org, sonarqube build number), 3 kept+digest-added. 4 phantom tags confirmed unresolvable upstream, not copied from memory.
4. **Dockerfile** — PASS. `ARG OPENRIG_VERSION=0.6.13`. Install-list rationale recorded: V13/#100 asserts Dockerfile literal pins == catalog (8 npm MCP) + fleet (3 pi-packages) exact-set both directions; drift either way fails.
5. **MCP flags** — PASS. `radare2.args==["-R"]`, k8s `--read-only`, postgres `--access-mode=restricted`, ClickHouse `false`, AWS `READ_OPERATIONS_ONLY=true`, pin==args-pin, `r2mcp`/`aws-mcp` banned active-line + tree-wide. Exact-flag assert red-proved (SAB2/SAB3).
6. **Vendoring** — PASS. `git archive <sha> <path>` in `vendor_skill_from_clone` + dirty-clone refusal confirmed in source. Plain `generate-rigs.py` on clean tree: exit 0. NOTE (accepted behavior): committed provenance (2bc45e5) lags HEAD (53573f8, the post-report fix commit), so regen rewrites 16 registry files with the new SHA (exit 0 once), and a second consecutive run exits 2 via the blocking-dirt refusal. Restored via `git checkout`; tree clean, verify 29/0. The "twice clean" acceptance holds when provenance is current (programmer's commit-time state); the re-lag is the known AGENTS.md-accepted provenance behavior, and the dirt refusal firing is itself fail-closed proof.
7. **Roster/pod + stub scan** — PASS. V13 asserts roster == 51 fleet sessions, omni pod == {exec-director, system-architect, tpm-scrum-lead} led by exec-director, stub regex over role dirs (skills/ excluded, placeholders stripped). Both red-proved (SAB4b/SAB5).
8. **DIRTY stamp** — PASS. `DIRTY-<sha>` stamping + rejection confirmed in code; live-tested (SAB7): dirty tree + ALLOW_DIRTY regen yields `resolvedCommit: DIRTY-53573f8...`, verify fails 16 V13/#99 + 16 V4, checkout restore returns 29/0.
9. **S2a closure** — PASS. `TERMINAL_BASH_DENIES` hoisted to module level in render-seat.py (single source; emitter iterates it); verify-rigs :588 mirror tuple; V13 sync assert ordered-identical. Mirror weakening red-proved (SAB6: named V13/S2a fail + expected cascade).

## M10 acceptance

10. **audit_loop self-test** — PASS, exit 0, 15 vectors. NOTES M10 tick table covers #67–#102: every P0/P1 has a verify command + result; unscoped issues (#75/#91 commandEffects, #76 ctest policy, #77 mission ownership, #80/#81/#88–#90/#94/#95/#98/#101 no-body-on-disk, #96 live re-seed) honestly marked follow-up with Wave-3 precedent — the same standard Wave 3 QA accepted.
11. **V1–V11 untouched; no hand-edits; no safe_dump; Makefile legitimate** — PASS. `git diff 27876bd HEAD -- scripts/verify-rigs.sh`: only deletions are the 2-line stale V6 proxy assert (phantom `:0.5.0` tag; spec-mandated, same precedent as M8's PUSH inversion); only block-header addition is `== V13 ==`. `write_yaml` (safe_dump) never targets fleet/fleet.yaml (read-only at :648). No specs/rigs/rosters/registry hand-edits beyond regen (regen diffs originate from generate-rigs.py; provenance re-lag accepted). 11th Makefile suite is genuine (see item 2).

## Red-proofs (all RED then GREEN; full log in red-proofs.log)

| # | Sabotage | RED | GREEN |
|---|---|---|---|
| SAB1 | strip `@sha256:` from qdrant pin | `V13/#70` exit 1 | 29/0 |
| SAB2 | `radare2.args` `["-R"]` to `[]` | `V13/#71` exit 1 | 29/0 |
| SAB3 | re-add `r2mcp==0.2.5` line | `V13/#71` exit 1 | 29/0 |
| SAB4b | `TODO` in tracked `guidance/role.md` | `V13/#87` (+digest cascade) exit 1 | 29/0 |
| SAB5 | roster 51 to 50 | `V13/#86` exit 1 | file restored 51/51, 29/0 |
| SAB6 | mirror tuple entry removed | `V13/S2a` (+cascade) exit 1 | 29/0 |
| SAB7 | dirty + ALLOW_DIRTY regen | `DIRTY-` stamp; 16 V13/#99 + 16 V4 exit 1 | checkout restore 29/0 |

No vacuous checks. Every acceptance gate was broken with a minimal targeted defect and observed to fail. (SAB4 planted a new file instead of editing a tracked one — still tripped V13/#87, proving the scan covers untracked files; SAB4b is the authoritative tracked-file proof.)

## Residuals assessment (merge-blockers or honest follow-ups?)

1. **Phantom-ref corrections** — follow-up, not blocker: all resolved on-host via skopeo, sibling pins adopted where live, discrepancies logged in NOTES. Correct direction.
2. **Unscoped-issue follow-ups** — honest follow-ups: none regressed, all recorded with derivation (Wave-3 precedent). Not blockers.
3. **Firecrawl standalone boot** — honest follow-up: minimal profile pulls cleanly, full-stack boot unverified; recorded M9 caveat. Not a blocker (compose correctness is asserted by pins, not boot).
4. **Stale "64 skills" prose** — cosmetic, pre-existing, correctly untouched (M10 candidate). Not a blocker.
5. **Footer session-URL discrepancy** (implementation report PR-body footer vs brief session URL) — cosmetic provenance noise in an unopened-PR body. Not a blocker.
6. **NEW (QA-found): V13 existence check FAILs instead of skipping on registry rate-limit** — `toomanyrequests` misses the offline-skip regex, so ~11 verify runs in one window flipped 7 existence probes to FAIL (recovered to 29/0 when quota eased). Follow-up, not blocker: digests are content-addressed (security property never depended on the probe); recommend adding `toomanyrequests|rate limit` to the skip pattern. Evidence in red-proofs.log (ENV-NOTE).
7. **Provenance re-lag on regen** (item 6) — accepted behavior per AGENTS.md; fail-closed dirt refusal verified working. Not a blocker; note for coordinator: commit quickly after regen so the tree stays idempotent-clean.

## Final state

`git status --short` shows only `?? docs/evidence/remediate-supplychain/` and `?? docs/reports/remediate-supplychain-qa.md` (this QA's deliverables). No tracked file modified by QA; all sabotages reverted and verified by clean status; final verify 29/0 green. Implementation commits left intact; nothing committed by QA.
