# remediate-supplychain — implementation report (Wave 4, M9–M10, audit #66)

- Stage id: `remediate-supplychain` (FINAL wave: M9 supply-chain + M10 final pass + PR)
- Branch: `remediate/audit-66-p0-p1-supplychain`
- Base: `27876bd` (Waves 1–3 merged on main: 28 verify checks, 248 unit tests)
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-supplychain`
- Unity binding: none. No stubs/`TODO`s/placeholders added; no test skipped, weakened, or deleted
  (one genuinely-stale test updated in its own commit per brief rule 4, reason in `docs/NOTES.md`).

## Deliverables

M9 (`af3e52e`): all 10 sidecar images tag@digest-pinned with on-host-resolved
digests; Dockerfile on OpenRig 0.6.13 with catalog-aligned installs; `git archive`
vendoring with dirty-clone refusal; DIRTY- provenance stamp + rejection;
"Not tested" attestation default; `== V13 ==` verify block (S2a + #70/#71/#85/#86/#87/#97/#99);
Wave-2 S2a advisory closed (mirror-vs-emitter sync assert).

M10 (`test`-fix `2bc45e5` + this report): full gates green, #67–#102 tick table,
PR body prepared, branch push-ready.

## Files changed (M9 commit af3e52e + test-fix 2bc45e5)

| File | Change |
|---|---|
| `scripts/generate-rigs.py` | `vendor_skill_from_clone()` (`git archive <sha> <path>`); tracked-modification refusal in pins loop + helper (`--untracked-files=no`); `resolve_run_attestation()`; `DIRTY-<sha>` stamp on blocking dirt under ALLOW_DIRTY; listings/harness attestation wiring |
| `scripts/render-seat.py` | terminal denies hoisted to module `TERMINAL_BASH_DENIES` (single source; emitter iterates it) |
| `scripts/verify-rigs.sh` | V6 `:1300` proxy assert updated to verified `v0.5.0@sha256:1f50…3459` (stale-pin update); new `== V13 ==` block, no V1–V12 renumber/reword |
| `docker-compose.sidecars.yml` | all 10 images tag@digest-pinned (4 repo fixes, 3 tag fixes, firecrawl PORT/ ghidra server cmd) |
| `docker/Dockerfile` | `OPENRIG_VERSION` 0.6.11→0.6.13; context7 4.4.2→4.4.4; server-memory 1.0.0→2.0.0 |
| `Makefile` | 11th suite (`test_generate_supplychain`) wired into `test:` |
| `tests/test_generate_supplychain.py` | NEW: 8 tests (archive fidelity, dirty/unknown-sha/missing-path dies, attestation 4-ways) |
| `tests/test_regen_gate.py` | stale DIRTY expectation updated + clean-tree bare-SHA pin (own commit 2bc45e5) |
| `docs/NOTES.md` | M9 resolutions/decisions/red-proofs + M10 tick table appended |
| `specs/`, `rigs/`, `registry/`, `rosters/` | regenerated leaves (provenance + attestation + worktree shellPath; `_shared` byte-identical, `skills-lock.json` unmodified) |

## Digest resolutions (all resolved on-host 2026-10-24 via `skopeo inspect`; never from memory)

- `tecnativa/docker-socket-proxy:v0.5.0` (`:0.5.0` phantom) → `sha256:1f5038b5…3459`
- `searxng/searxng@sha256:79180616…4a768` (`:2026.10.18-2c9b2d4` phantom; upstream-tested tagless, verified live)
- `ghcr.io/browserless/chromium:v2.26.0@sha256:899026f6…24da9` (`browserless/chrome:1.66.0` phantom repo+tag)
- `ghcr.io/firecrawl/firecrawl:2.10.19@sha256:50446cbc…6d7ed` (`ghcr.io/mendable/…:1.6.0` phantom org+tag)
- `redis:8.0.3@sha256:be0a135f…55de0`, `qdrant/qdrant:v1.15.3@sha256:31407c0e…8007`, `budtmo/docker-android:emulator_14.0@sha256:8ee678cf…70b372d2a` (tags kept, digests added)
- `blacktop/ghidra:12.1.4@sha256:b2479177…a193c` (`ghcr.io/ghidra/…:11.4.2` phantom — no such org)
- `radare/radare2@sha256:88b7ff67…2ae37` (`radareorg/radare2:5.9.8` phantom org; upstream-tested tagless)
- `sonarqube:25.10.0.114319-community@sha256:ef0290a2…48ef4e` (`:25.10.0-community` phantom)
- 4 phantom tags confirmed unresolvable upstream; sibling Heretek-Crew pins adopted where they exist and verify live.

## Acceptance outputs (exact commands, exit codes)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 29 checks passed, 0 failed.`, exit 0
- `make test` → `Ran 257 tests ... OK` (11 suites), exit 0
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED` (15 vectors), exit 0
- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py --check-idempotent` → `idempotence check passed`, exit 0
- `python3 ./scripts/generate-rigs.py` (clean tree, no flag) → clean provenance, exit 0
- `bash scripts/gate-role.sh sabotage-qa-tester` → exit 0; `go-backend-eng` → exit 0
- Red proofs (plant → verify exit 1 → restore): tag-only qdrant (V13/#70), bad redis digest (V13/#70 manifest-unknown), clickhouse true (V13/#71), r2mcp re-added (V13/#71), roster −1 (V13/#86), TODO in role.md (V13/#87), fake tested claim (V13/#97), mirror-entry removal (V13/S2a), DIRTY leaves (V13/#99 + V4, 32 fails), dirty vendor clone (generate exit 2). Full logs: `/tmp/opencode/sab_*.log`, `/tmp/opencode/verify_m*.log`.

## #67–#102 tick table (verify commands from docs/PROMPT_REMEDIATION_REAUDIT.md §1; derivation in NOTES)

| Issue | Verify command | Result |
|---|---|---|
| #67 | render with `/nonexistent` tools | PASS (exit 2, "mandatory") |
| #68 | `gate-role.sh sabotage-qa-tester` + F2 corpus | PASS (exit 0, 43 ok) |
| #69 | `gate-role.sh go-backend-eng` | PASS (exit 0) |
| #70 | `docker manifest inspect` + V13 existence | PASS (exit 0) |
| #71 | weaken flag / re-add r2mcp → verify | PASS (exit 1, named gates) |
| #72 | env-prefixed send refusal | PASS (exit 2); live half residual per F9 |
| #73 | commit grants fleet-wide | PASS (0 roles) |
| #74 | V12 names missing r2mcp etc. | PASS (NOTEs, gate green) |
| #75/#91 | commandEffects | NOT IMPLEMENTED → follow-up |
| #76 | `ctest --output-on-failure` | DENIED (pre-existing deny; needs policy decision) → follow-up |
| #77 | mission-row ownership | no wave scope, needs live queue → follow-up |
| #78 | missions writes | no wave scope (M4 sandbox mitigates) → follow-up |
| #79 | `audit_loop --self-test` | PASS (15 vectors) |
| #80/#81 | not on disk | → follow-up |
| #82 | `make test` 11 suites | PASS (257 OK) |
| #83 | sweep tests | PASS |
| #84 | reconcile fixture exit 1 | PASS |
| #85 | dirty clone + archive fidelity | PASS (exit 2; byte-identical) |
| #86 | roster sabotage | PASS (exit 1) |
| #87 | stub sabotage | PASS (exit 1) |
| #88/#89/#90 | not on disk | → follow-up |
| #92 | 69 envelope tests | PASS |
| #93 | `--source` member-id reject | PASS (exit 2) |
| #94/#95 | table-defined, no wave scope | → follow-up |
| #96 | live re-seed | UNVERIFIABLE off-fleet |
| #97 | fake tested claim | PASS (exit 1); tree "Not tested" |
| #98 | not on disk | → follow-up |
| #99 | ALLOW_DIRTY regen → verify | PASS (exit 1, DIRTY rejected) |
| #100 | `grep OPENRIG_VERSION` + render | PASS (0.6.13; pps-only render recorded) |
| #101 | not on disk | → follow-up |
| #102 | P3 spot-checks | recorded (64-prose, firecrawl boot caveat, version deltas) |

## Self-audit notes (unfinished / honest residuals)

1. V13 `#100` exact-set assert is strict by design: any future Dockerfile or catalog pin change must update both sides together.
2. Firecrawl minimal profile (firecrawl-redis only) pulls cleanly but standalone boot is unverified — upstream runs rabbitmq/nuq-postgres/playwright-service. Follow-up: mirror the backing stack or drop the service.
3. `commandEffects` (#75/#91), `ctest --output-on-failure` (#76), mission-row ownership (#77), TOML lint (#95) and undeclared-binary probes (#94) are NOT fixed — no wave scoped them; flagged as follow-up, not regressed.
4. `docs/evidence/run-records.json` does not exist → attestation is honestly "Not tested". Creating it requires recorded live runs (needs the fleet).
5. Stale "64 shared skills" prose (AGENTS.md + generator docstring; actual 68 after Waves 2–3) left untouched — M10 follow-up candidate.
6. Upstream Heretek-Crew still pins phantom `:0.5.0` socket-proxy and older qdrant/docker-android tags — reported here, not edited there (different repo).
7. S2a closure changes the failure mode only: mirror weakening now fails V13/S2a instead of staying green; renderer weakening still fails via `:1158` asserts + unit tests (S2b, Wave-2 QA).
8. Committed provenance re-lags one commit per merge (known, accepted per AGENTS.md).
9. Post-commit semgrep scan flagged `tarfile.extractall` (traversal rule) in `vendor_skill_from_clone`; hardened to validated per-member extraction (reject absolute/`..` members, then `tf.extract` each) — rescan 0 findings; helper unit tests (18/18 incl. byte-fidelity) re-run green. Committed as `fix(remediate-supplychain)` after M10.

## PR

Push blocked by the execution environment (2 attempts, same error — push
guardrail, not a repo problem), so no PR was opened. Branch is ready for a
shell host with push rights:

- Exact error (verbatim, twice): `{"type":"permission.rejected","message":"Permission denied: shell"}`
- Command attempted: `git push -u origin remediate/audit-66-p0-p1-supplychain`
- Remote exists (`origin → https://github.com/Heretek-AI/heretek-rigs`) and `gh auth status` is logged in — the block is the sandbox push guardrail, not credentials.
- To open the PR: `git push -u origin remediate/audit-66-p0-p1-supplychain`, then `gh pr create --base main --title "Remediation: audit #66 P0/P1 (supply-chain wave)" --body-file <body>` with the body below.
- Full PR body text (spec format):

## Remediation: audit #66 P0/P1 (supply-chain wave, M9–M10)

Fixes: #67 #68 #69 #70 #71 #72 #73 #74 #79 #82 #83 #84 #85 #86 #87 #92 #93 #97 #99 #100

| Issue | Fix | Verify command | Result |
|---|---|---|---|
| #67 | render fails closed on missing pps | `HERETEK_TOOLS=/nonexistent ... render-seat.py --role exec-director ... --allow-missing-secrets` | PASS (exit 2, "mandatory") |
| #68 | locked-seat runners stripped; bubblewrap jail | `gate-role.sh sabotage-qa-tester` + F2 corpus | PASS (exit 0, 43 ok) |
| #69 | git-diff read-bypass denies | `gate-role.sh go-backend-eng` | PASS (exit 0) |
| #70 | all 10 sidecars tag@digest-pinned, on-host resolved | `docker manifest inspect <image>` + V13 existence | PASS |
| #71 | exact MCP security args/env, pin==args-pin, r2mcp/aws-mcp deny-lists | sabotage → `verify-rigs.sh --check-only` | PASS (exit 1, named gates) |
| #72 | `send-authenticated.sh` refuses `OPENRIG_SESSION_NAME` | env-prefixed send | PASS (exit 2); live half residual per F9 |
| #73 | dependency-patcher cannot commit | fleet bash_allow query | PASS (0 commit grants) |
| #74 | V12 names missing r2mcp etc. | `verify-rigs.sh --check-only` | PASS (per-seat NOTEs, gate green) |
| #79 | evaluator hardening, 15 vectors | `audit_loop.py --self-test` | PASS |
| #82 | 11 suites wired + run | `make test` | PASS (257 OK) |
| #83 | auth actor/exactness/evidence | `make test` (11 sweep tests) | PASS |
| #84 | negation-aware terminal | fixture → exit 1 NEEDS-HUMAN-REVIEW | PASS |
| #85 | `git archive` vendoring; dirty-clone refusal | dirty clone → generate; archive fidelity | PASS (exit 2; byte-identical) |
| #86 | roster==51 sessions; command pod | member-removed → verify | PASS (exit 1) |
| #87 | stub scan over role dirs | TODO planted → verify | PASS (exit 1) |
| #92 | envelope semantics | `make test` (69 tests) | PASS |
| #93 | receipt + member-id source rejects | `--source` member-id send | PASS (exit 2) |
| #97 | attestation grounded or "Not tested" | fake tested claim → verify | PASS (exit 1) |
| #99 | DIRTY- stamp + reject | ALLOW_DIRTY regen → verify | PASS (exit 1) |
| #100 | Dockerfile 0.6.13 + catalog alignment | `grep OPENRIG_VERSION` + render probe | PASS |

Gates: verify-rigs 29/0, make test OK (11 suites, 257 tests), audit_loop self-test OK (15 vectors), generate-rigs clean ×2 (`--check-idempotent` byte-identical).
Not done / follow-up: #75/#91 commandEffects, #76 ctest---output policy, #77 mission ownership, #78 missions write-scope, #80/#81/#88/#89/#90/#94/#95/#98/#101 (no issue body on disk / no wave scope), #96 live re-seed (UNVERIFIABLE off-fleet); P3 spot-checks in #102. See docs/NOTES.md M10 tick table.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014wevSWHET5eqHNVNTYZ9W

PR URL or blocker: BLOCKED — push refused by sandbox (`permission.rejected` ×2, command above). Branch `remediate/audit-66-p0-p1-supplychain` ready with M9 + test-fix + M10 commits.
