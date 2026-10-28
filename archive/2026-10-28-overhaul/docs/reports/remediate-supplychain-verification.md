# Verification report — remediate-supplychain (Wave 4, M9–M10, audit #66) — FINAL / MERGE GATE

- Stage: `remediate-supplychain` | Branch: `remediate/audit-66-p0-p1-supplychain` | Base: `27876bd`
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-supplychain`
- Auditor: drift-guard (independent; no source files modified — this report is the only new file)
- Inputs read from disk: `AGENTS.md`; `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md` (M9, M10, Definition of done, PR body format, Gotchas); `docs/reports/remediate-supplychain-implementation.md`; `docs/reports/remediate-supplychain-qa.md`; `docs/evidence/remediate-supplychain/red-proofs.log`; `docs/NOTES.md` (full, through M10 + semgrep hardening)
- Verdict: **PASS** (reasoning below; zero numbered findings)

## 1. Independent re-runs (re-run, do not trust)

| Check | Command (worktree root) | Result |
|---|---|---|
| verify-rigs | `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 29 checks passed, 0 failed.`, exit 0 (28 carried + new V13) |
| unit tests | `make test` | `Ran 257 tests ... OK`, exit 0, 11 suites |
| evaluator | `python3 scripts/audit_loop.py --self-test` | `SELF-TEST PASSED`, 15 vectors, exit 0 |
| #67 fail-closed | `HERETEK_TOOLS=/nonexistent ... render-seat.py ... --allow-missing-secrets` | exit 2, "mandatory" (`@gotgenes/pi-permission-system is mandatory`) |
| #68 locked-seat gate | `bash scripts/gate-role.sh sabotage-qa-tester` | exit 0 (tail: live code_rewrite/lsp mutation denies ok) |
| Dockerfile | `grep OPENRIG_VERSION docker/Dockerfile` | `ARG OPENRIG_VERSION=0.6.13` (1 hit) |

## 2. Independent sabotages (2, both RED→GREEN with named gates)

- **SAB-D1 digest-strip (#70):** replaced `qdrant/qdrant:v1.15.3@sha256:3140…8007` with bare tag → verify exit **1**, `[FAIL] V13/#70: sidecar qdrant must pin its image by digest`; restored → 29/0, exit 0. Logs: `/tmp/opencode/drift_sab1.log`, `/tmp/opencode/drift_sab1_green.log`.
- **SAB-D2 stub-plant (#87, tracked file):** appended `# TODO: drift-guard sabotage (reverted)` to tracked `specs/agents/executive/exec-director/guidance/role.md` → verify exit **1**, `[FAIL] V13/#87: ... contains stub marker 'TODO'` (+ digest cascade, 26+3); restored via backup copy → 29/0, exit 0. Logs: `/tmp/opencode/drift_sab2.log`, `/tmp/opencode/drift_sab2_green.log`.
- Both sabotages were reverted; `git status --short` is clean (empty) after restoration. No test was weakened or skipped to obtain green.

## 3. M9 families in code (all present)

- **Digest pins (#70):** all 10 sidecar images match `sha256:[0-9a-f]{64}` (`grep -c` = 10); 8× `tag@digest`, 2× tagless `repo@sha256:` (strictly stronger, spec-allowed). NOTES M9 records every on-host `skopeo inspect` resolution (4 phantom refs corrected, 3 phantom tags fixed, 3 kept+digest-added; 4 phantom tags confirmed unresolvable upstream, none copied from memory). Spot-checked: `tecnativa/docker-socket-proxy:v0.5.0@sha256:1f5038b5…3459`, `qdrant/qdrant:v1.15.3@sha256:31407c0e…8007`.
- **Dockerfile (#100):** `ARG OPENRIG_VERSION=0.6.13`; V13 asserts Dockerfile literals == catalog (8 npm MCP) + fleet (3 pi-packages) exact-set both directions (drift either way fails).
- **Install-list derivation:** recorded in NOTES M9-§Catalog-vs-Dockerfile drift (context7 4.4.2→4.4.4, server-memory 1.0.0→2.0.0 aligned to catalog; Dockerfile stays manual for builder/runtime-split reasons with the V13 exact-set gate as compensation).
- **MCP flags (#71):** `radare2.args==["-R"]`, k8s `--read-only`, postgres `--access-mode=restricted`, ClickHouse `"false"`, AWS `READ_OPERATIONS_ONLY=="true"`, pin==args-pin asserts present; `r2mcp==`/`aws-mcp@`/`pypi:r2mcp`/`npm:aws-mcp` banned active-line + tree-wide (V13 lines ~1824–1858).
- **Vendoring (#85):** `vendor_skill_from_clone()` uses `git archive <sha> <path>` with per-member validated extraction (post-semgrep hardening, rescan 0 findings); pins-loop + helper refuse tracked modifications (`--untracked-files=no`); openrig-core keeps copytree (ships in npm package, not a clone — recorded).
- **Roster/pod (#86):** V13 asserts roster seats == 51 fleet sessions and omni command pod == {exec-director, system-architect, tpm-scrum-lead} led by exec-director. `rosters/` has zero diff vs base.
- **Stub scan (#87):** V13 scans `specs/agents/*/<role>/` excluding `skills/` first path segment, stripping `@TOOLS@/@SECRETS@/@SEAT@`, regex `\b(TODO|FIXME|TBD|PLACEHOLDER)\b|\{\{[A-Za-z_]+\}\}` — matches spec; SAB-D2 proves it fires on tracked files.
- **DIRTY stamp + rejection (#99):** `DIRTY-<sha>` stamping in `resolve_heretek_commit()` + V13/#99 reject + V4 regex reject confirmed in source; QA SAB7 red-proved (16 V13 + 16 V4 fails).
- **"Not tested" default (#97):** `resolve_run_attestation()` returns `("Not tested", [])` absent `docs/evidence/run-records.json`; committed tree is honestly "Not tested"/[] (registry/status.json diff is `tested`+ids → `Not tested`+empty — the fail-closed direction).
- **S2a tuple hoist + sync assert:** `TERMINAL_BASH_DENIES` is module-level in `render-seat.py` (line 81, emitter iterates it at :514); verify-rigs `:588` mirror tuple; V13/S2a ordered-identical assert. Wave-2 advisory closed.
- **Anti-stub scan of changed code:** `grep TODO|FIXME|TBD|PLACEHOLDER|{{…}}` over `tests/test_generate_supplychain.py`, `scripts/generate-rigs.py`, `scripts/render-seat.py` → zero hits (excluding the scan's own marker strings). Clean.

## 4. V1–V11 untouched

`git diff 27876bd HEAD -- scripts/verify-rigs.sh`: the only deletions are the 2-line stale V6 proxy assert (`:0.5.0` → verified `v0.5.0@digest`); the only block-header addition is `== V13 ==`. The old assert pinned a tag proven phantom on-host (NOTES M9: `tecnativa/docker-socket-proxy:0.5.0` → MANIFEST UNKNOWN, only `v0.5.0` exists). Spec-mandated stale-pin update per brief rule 9 ("never renumber/reword" permits appending; M8 PUSH inversion is the accepted precedent, cited in the code comment and NOTES). No V1–V12 line renumbered or reworded. **Not a weakening: the old gate asserted a nonexistent artifact and could never pass against a corrected compose file.**

## 5. 11th suite legitimate and non-vacuous

`tests/test_generate_supplychain.py` (NEW, 8 tests) is wired into `Makefile:38` `test:` alongside the other 10 — `make test` runs 257 tests across 11 suites. Tests operate on synthetic `/tmp` git repos only (never the live tree): archive byte-fidelity ground truth, dirty-clone/unknown-SHA/missing-path `SystemExit(2)`, attestation 4-ways. Standalone run: 8 tests OK in 0.121s. Each asserts a fail-closed `die` or byte-equality — non-vacuous. Spec DoD says "10 suites"; the count grew to 11 with this suite — a super-set, recorded in the implementation report, not a deviation.

## 6. No hand-edits to generated trees; no safe_dump on fleet.yaml; commit discipline

- `fleet/`: **zero diff** vs base. `write_yaml` (safe_dump) targets only generated leaves (`agent.yaml`, `rig.yaml`, pods); `fleet/fleet.yaml` is read-only (`yaml.safe_load`, :653). Comment-stripping risk absent.
- `specs/`/`rigs/` diffs: only `shellPath` worktree-path lines (`.lane/trees/remediate-sandbox/` → `.lane/trees/remediate-supplychain/` — path artifact of the worktree location, not content) plus regen package-digest refreshes.
- `rosters/`: zero diff. `registry/`: provenance (`DIRTY-`→clean SHA), `tested`→`Not tested` attestation, digest refreshes — all regen-originated via `generate-rigs.py`.
- Commits (`af3e52e`, `2bc45e5`, `97a37ca`, `53573f8`, `b4e29b3`): one concern per commit, explicit `git add` class of files, `remediate(#…):` messages with the mandated `Co-Authored-By` + `Claude-Session` attribution lines. The test-fix (`2bc45e5`) and semgrep hardening (`53573f8`) are each in their own commit with reasons in NOTES per brief rule 4.
- Committed provenance re-lag (2bc45e5 vs HEAD) is the known AGENTS.md-accepted behavior; NOT hand-"fixed".
- PR not opened: push blocked by the sandbox push guardrail (`permission.rejected` ×2, remote exists, `gh auth` logged in — environment block, not a repo problem), honestly reported with exact error and the shell-host push instructions + full spec-format PR body in the implementation report. DoD "PR opened, not merged" is satisfied to the extent executable here; branch is push-ready.

## 7. #67–#102 tick table (P0/P1 coverage)

Every P0/P1 (`#67 #68 #69 #70 #71 #72 #73 #79 #82 #83 #84 #85 #86 #87 #92 #93 #97 #99 #100`) has a verify command + result in NOTES M10 and the implementation report; I independently re-ran #67, #68, #70 (SAB-D1), #87 (SAB-D2), #79, #82 and confirm PASS. Remaining P0/P1 entries are covered by QA's red-proofs (SAB1–SAB7: #71 clickhouse/r2mcp, #86 roster, #99 DIRTY, #97 fake-tested, S2a mirror — each with named-gate RED + 29/0 GREEN in `red-proofs.log`, which I read in full; failure signatures non-vacuous, `VERIFY_EXIT:1` recorded per sabotage). Honestly-marked follow-ups with stated reasons: #75/#91 commandEffects (zero code hits, no wave scope), #76 ctest---output (pre-existing deny, needs policy decision), #77 mission ownership (needs live queue), #78 write-scope (M4 sandbox mitigates), #80/#81/#88/#89/#90/#94/#95/#98/#101 (no issue body on disk, no wave scope), #96 live re-seed (UNVERIFIABLE off-fleet). Nothing in-scope is left unproven; nothing out-of-scope is misclaimed as fixed.

## 8. The 2 QA-found advisories (merge-blockers or follow-ups?)

1. **V13 existence check FAILs instead of skipping on registry rate-limit** (`toomanyrequests` misses the offline-skip regex → ~7 FAILs in a rate-limited window, recovered to 29/0 when quota eased). **Follow-up, not a blocker.** Reasoning: the security property (digest pinning) is enforced by the format assert, which is network-independent and red-proves cleanly (SAB-D1); the skopeo probe is advisory-by-design (an offline skip path already exists for transport errors). Failure mode is fail-closed (false RED, never false GREEN) — it can delay a gate, never pass a bad pin. Recommended fix (extend skip pattern with `toomanyrequests|rate limit`) is a 1-line follow-up. I observed no rate-limit failure in my own runs (29/0, no NOTEs on existence).
2. **Provenance-lag regen exit 2** (regen on a tree whose committed provenance lags HEAD exits 2 via blocking-dirt refusal). **Follow-up (coordinator note), not a blocker.** This is AGENTS.md-accepted behavior (re-lag known per merge); the refusal firing is itself fail-closed proof that dirty provenance cannot bake silently. Mitigation is process (commit quickly after regen), already noted by QA.

Neither advisory weakens a gate or hides a defect. Neither blocks merge.

## 9. Definition of done (spec §Definition of done)

- M1 shellPath honored (CLI spike + F1 live-daemon evidence) with the settings.json no-hot-reload rollout split stated — carried over green from Waves 1–2 base (28 checks), rollout split restated in this wave's reports. PASS.
- #67 fail-closed, no `--allow-missing` escape — re-run PASS (exit 2). #68 locked-seat runners stripped + F2 corpus — re-run PASS. #69 git-diff denies — gate green (QA 43 ok). PASS.
- #70/#100 digests + Dockerfile 0.6.13 — PASS (§3). #71 MCP sabotages red — PASS (QA SAB2/SAB3 + source asserts). #72/#73 env-prefix refusal + zero commit grants — PASS (source + QA matrix). PASS.
- #79 15 vectors — re-run PASS. #82 11 suites in `make test` + verify — PASS (super-set noted). #83/#84/#92 fixtures fail closed — carried green on base, untouched this wave. PASS.
- #85/#86/#87/#97/#99 sabotages red — PASS (QA log + my SAB-D1/SAB-D2). Gates green (29/0, 257 OK, 15 vectors, idempotent regen) — re-run PASS.
- NOTES discrepancies logged (M9 + M10 + semgrep sections, ~100 appended lines). PR body ready in spec format, unopened due to sandbox block — honestly reported. PASS with noted residual.
- Suite count grew 10→11 with the new supply-chain suite; verify 27+N resolved to 29. Both recorded.

No stubs, no vacuous checks, no failing commands, no missing deliverables, no hand-edited leaves. One cosmetic residual (stale "64 skills" prose vs 68 actual) correctly left untouched as a follow-up candidate.

VERDICT: PASS
