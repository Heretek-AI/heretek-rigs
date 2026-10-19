# AUDIT_REPORT_FINDINGS: heretek-rigs

## Baseline
- Repo root: `/home/john/Projects/heretek-rig-workspace/heretek-rigs` (`Read` directory listing: `.git/`, `docs/`, `fleet/`, `schemas/`, `scripts/`, `tests/`, `docker-compose.sidecars.yml`, `identity-vectors.json`, `Makefile`, prompts, `README.md`; no `specs/`, `rigs/`, `rosters/`, `registry/`).
- `git rev-parse HEAD`, `git log -1 --format='%ci %s'`, UTC date, `git status --porcelain`: UNOBTAINABLE — every `default.shell` attempt returns `permission.rejected` (`This non-interactive run cannot ask the user for permission, so the request was rejected`). `.git/HEAD` not re-read this run; `.gitignore:1-8` re-read verbatim (`.scratch/`, `node_modules/`, `.env*` with `!.env.example`, `__pycache__/`, `*.pyc`, `.venv/`) — does NOT ignore `specs/`, `rigs/`, `registry/`, `rosters/`, or `fleet/skills-lock.json`, so their absences are real HEAD-state defects, not ignore artifacts. Audit date (system): 2026-10-19 UTC.
- Tool versions (`python3/node/npm/git/jq/rg/docker compose/rig@0.6.11/pi@1.3.0 --version`): all UNOBTAINABLE (shell blocked). No version asserted by inference.
- Host capabilities: `Read`/`Grep`/`Glob`/`Write`/`Subagent` WORKED; `Shell` BLOCKED. Therefore `rig spec validate`, `rig bundle check`, `rig agent validate`, `rig spec preflight`, `rig expand`/`add`/`up`/`down`, `rig daemon start --no-kernel --port 7699` on loopback, `pi` presence/version/behavior, `Draft202012Validator` runs, `render-seat.py` 0644-vs-0600 probe, `make guard-profiles` execution, `bootstrap-pi-seats.sh` isolated-`OPENRIG_HOME` test, `gate-role.sh` hostile corpus, `docker compose config/down -v`, and all outbound-HTTPS checks (github.com, registry.npmjs.org, pypi.org, api.osv.dev) are UNVERIFIABLE here, each with reason "shell permission.rejected — no command execution". No claim is VERIFIED by code-reading or test-passing alone (Cardinal Rule), except pure existence/placeholder-freedom Claim 8.4 where the filesystem itself (Glob/Read) is the real subject.
- Previous run: `AUDIT_REPORT_FINDINGS.md` existed (486 lines, sentinel `STATUS: FINDINGS_DETECTED`). Read in full before any other work. Every finding re-verified from scratch via fresh triad (Alpha [A], Beta [B], Gamma [G]) + cross-examination (challenger→Alpha: 10 CONFIRMED, 0 drops; challenger→Beta: 10/10 CONFIRMED; challenger→Gamma: 12/12 CONFIRMED) + controller spot-reads (`fleet.yaml:1-30`, `.gitignore:1-8`, `identity-vectors.json:1-31`, `verify-rigs.sh:100-159`).
- State deltas vs previous run: `specs/`, `rigs/`, `rosters/`, `registry/`, `fleet/skills-lock.json` all still absent per fresh `Glob`; `schemas/` 6/6 present; `fleet/fleet.yaml` + `fleet/mcp-servers.yaml` + docs + prompts + `scripts/` present. No code fixes landed since last run that change verdicts; all prior OPEN findings re-confirmed, 8.4 stays VERIFIED.

## Verdict
`heretek-rigs` at this checkout remains a pre-generation source+toolchain commit, not the working 51-role fleet it claims: canonical inputs (`fleet/fleet.yaml`, `fleet/mcp-servers.yaml`, docs, prompts, `scripts/`, `schemas/`, `identity-vectors.json`, sidecar baseline) and generator/verifier/evaluator/harness code are present and statically consistent, but every generated tree the claims assert (`specs/`, `rigs/`, `rosters/`, `registry/`, `skills-lock.json`) is still absent, so `verify-rigs.sh --check-only` cannot exit 0 and no live OpenRig/Pi contract was proven here. Cross-examination confirmed all absence-based BROKENs and all code-proven PARTIALs with zero substantive refutations. The single most important thing to fix is to run the pinned generation pipeline (`python3 scripts/generate-rigs.py` with vendored inputs) and then prove the execution-gated halves (rig validate/bundle/preflight, seat 0600 probe, hostile `gate-role.sh` corpus, guard-profiles matrix, 12-sabotage matrix) before any `STATUS: NO_FINDINGS` can be honestly claimed.

## Prioritized Defect Matrix
| ID | Priority | Claim | Location | Summary |
|----|----------|-------|----------|---------|
| HR-1.1-missing-specs-trees | P0 | 1.1 | `specs/` (absent) | 51 roles declared, zero role dirs on disk |
| HR-1.2-pregen-partition | P0 | 1.2 | `rigs/` (absent) | 6+11+4+6+11+6+7 declared only, no rig.yaml |
| HR-1.4-pregen-files | P0 | 1.4 | `specs/agents/<domain>/<role>/` (absent) | 357-file promise unmet on disk |
| HR-2.1-missing-rigs | P0 | 2.1 | `rigs/*/rig.yaml` (absent) | No subjects for `rig spec validate` |
| HR-2.2-missing-edges | P0 | 2.2 | `rigs/*/rig.yaml` (absent) | Edge/DAG claims without subjects |
| HR-2.5-missing-bundles | P0 | 2.5 | `specs/`, `rigs/` (absent) | No subjects for symlink/containment/`bundle check []` |
| HR-2.3-schema-mismatch | P0 | 2.3 | `specs/agents/*/*/agent.yaml` (absent) | No AgentSpec subjects |
| HR-3.1-empty-registry | P0 | 3.1 | `registry/`, `rigs/` (absent); `schemas/` present | Schemas 6/6 present, ~25 subjects absent |
| HR-4.1-pins-unmaterialized | P0 | 4.1 | `rigs/*/rig.yaml` (absent); `fleet/fleet.yaml:8-17` | Pins correct in source, zero materialized seats |
| HR-6.1-unbuilt-catalog | P0 | 6.1 | `fleet/skills-lock.json`, `specs/` (absent) | 62-skill vendoring unexecuted |
| HR-8.2-gate-red | P0 | 8.2 | `scripts/verify-rigs.sh:130` | Gate red on clean checkout (missing skills-lock.json) |
| HR-1.3-omni-fragments | P1 | 1.3 | `rigs/heretek-omni-fleet/` + `rosters/` (absent) | source 15+51 explicit; nothing materialized |
| HR-2.4-recipe-correct-unproven | P1 | 2.4 | `specs/agents/executive/exec-director/agent.yaml` (absent) | Recipe correct; catch unproven |
| HR-3.3-vectors-proof-absent | P1 | 3.3 | `identity-vectors.json` (present) vs `rigs/`+`registry/` (absent) | Vectors vendored; digest proof unproven |
| HR-5.2-guards-unproven | P1 | 5.2 | `scripts/render-seat.py:268-285` | Full guards in code; live proof missing |
| HR-5.4-extension-unproven | P1 | 5.4 | `scripts/render-seat.py:306-310` | Triple-deny unconditional; live Pi bypass untested |
| HR-7.1-compose-unproven | P1 | 7.1 | `docker-compose.sidecars.yml:52-140` | Loopback+pinned in file; `compose config` unexecuted |
| HR-8.1-not-generated | P1 | 8.1 | `specs/`, `rigs/`, `registry/`, `rosters/` (absent) | Generation never ran; `--check-idempotent` exists but unrun |
| HR-8.3-evaluator-execution | P1 | 8.3 | `scripts/audit_loop.py:62-109,149-170` | Evaluator logic in code; self-test gate-blocked red |
| HR-4.2-bootstrap-residual | P2 | 4.2 | `scripts/verify-rigs.sh` (no default seat-dir gate) | Strict default in code; seat-materialization gate opt-in only; unexecuted |
| HR-4.3-secret-probe-gap | P2 | 4.3 | `fleet/mcp-servers.yaml:7-11`; `scripts/render-seat.py:111-120` | Forms allowed; 0644-refusal/sabotage probes unexecuted |
| HR-5.1-locked-unmaterialized | P2 | 5.1 | `rigs/*/rig.yaml` (absent); `fleet/fleet.yaml` 20x locked | Source correct (20=2 rig+18 role, 16 readonly); disk half vacuous |
| HR-5.5-bash-matcher | P2 | 5.5 | `scripts/render-seat.py:287-303` | Deny-first + metachar + `--output` die in code; matcher semantics unproven |
| HR-6.2-pins-liveness | P2 | 6.2 | `fleet/mcp-servers.yaml:19-266` | Pins textually right; liveness unverified; 2 servers not-run |
| HR-3.2-jcs-proof-gated | P3 | 3.2 | `scripts/generate-rigs.py:120-152`; `registry/status.json` (absent) | Explicit JCS canonicalizer in code; disk proof gated, ASCII-only limit |
| HR-4.4-literal-floor-note | P3 | 4.4 | `scripts/verify-rigs.sh:290-298,681-714` | Name+literal scans in code; unexecuted |
| HR-5.3-url-user-present | P3 | 5.3 | `scripts/render-seat.py:323-350` | Denies present in code; live proof missing |
| HR-5.5-render-output-allow | P3 | 5.5 | `scripts/render-seat.py:299-302`; `scripts/generate-rigs.py:371-376` | Renderer+generator `--output` die present in code; live die-probe unexecuted — kept OPEN |
| HR-5.4-gate-coverage | P3 | 5.4 | `scripts/gate-role.sh:75-80` | All three mutating tools probed in code; live run unexecuted — kept OPEN |
| HR-7.2-proxy-residual | P3 | 7.2 | `docker-compose.sidecars.yml:18-43` | 18 toggles pinned in code; exhaustiveness + live proof missing |
| HR-7.3-network-note | P3 | 7.3 | `docker-compose.sidecars.yml:92-153`; `Makefile:45-53` | Literal claim satisfied; guard-only-in-make + co-residence note |

## Findings
### HR-1.1-missing-specs-trees: 51-role catalog declared but zero role directories exist
- **Priority:** P0
- **Claim:** 1.1 — `fleet/fleet.yaml` defines all 51 canonical roles and all 51 `specs/agents/<domain>/<role-slug>/` dirs exist.
- **Location:** `specs/` (absent); `fleet/fleet.yaml:25-28` (roles:51), `fleet.yaml` 51 role keys incl. `static-analysis-lead`, `ai-red-teamer`
- **Proof:** `Glob specs/**/*` from repo root
- **Raw output:** `No files found`
- **Why it matters:** Without role dirs there is nothing to seed, validate, or launch; every downstream domain fails.
- **Remediation:** Vendor `Heretek-Crew@5ffb1fc`, run `python3 scripts/generate-rigs.py`, then `find specs/agents -mindepth 2 -maxdepth 2 -type d | wc -l` must equal 51.
- **Verify the fix:** `test $(find specs/agents -mindepth 2 -maxdepth 2 -type d | wc -l) -eq 51 && ./scripts/verify-rigs.sh --check-only`
- **Cross-examination:** Beta-challenger CONFIRMED BROKEN (gitignore-hides-specs bid fails — `.gitignore:1-8` has no `specs/` rule).

### HR-1.2-pregen-partition: Rigs 1-7 partition exists only as declaration
- **Priority:** P0
- **Claim:** 1.2 — Rigs 1–7 partition 51 roles 6+11+4+6+11+6+7, each role in exactly one static rig.
- **Location:** `rigs/` (absent); declaration `fleet/fleet.yaml:30-381`
- **Proof:** `Glob rigs/**/*` → No files found
- **Raw output:** `No files found` (rigs)
- **Why it matters:** No rig.yaml means no RigSpec to validate or `rig up`; single-homing unprovable.
- **Remediation:** Generate, then assert 7 rig dirs each with `rig.yaml` and disjoint membership.
- **Verify the fix:** `for d in rigs/*/; do test -f "$d/rig.yaml"; done && ./scripts/verify-rigs.sh --check-only`
- **Cross-examination:** Beta-challenger CONFIRMED BROKEN (partition counts re-verified exact in source: 6+11+4+6+11+6+7=51).

### HR-1.3-omni-fragments: source explicit, disk absence remains
- **Priority:** P1
- **Claim:** 1.3 — Rig 8 hybrid omni-fleet with 3-seat command pod + 15 pod fragments + 51 member fragments + `rig.all-51.yaml` + roster.
- **Location:** `fleet/fleet.yaml:382-399` (3-seat command), `:400-430` (15 pod fragments), `:431-534` (51 member_fragments); `rigs/heretek-omni-fleet/` + `rosters/` absent
- **Proof:** `Read fleet.yaml:382-534` explicit lists; `Glob rigs/**/*`, `Glob rosters/**/*` → none
- **Raw output:** `No files found` (rigs, rosters)
- **Why it matters:** The flagship 51-seat profile doesn't exist on disk.
- **Remediation:** Generate omni artifacts (`pods/*.yaml` ×15, `members/*.yaml` ×51, `rig.all-51.yaml`, roster JSON).
- **Verify the fix:** `test $(ls rigs/heretek-omni-fleet/pods/*.yaml | wc -l) -eq 15 && test $(ls rigs/heretek-omni-fleet/members/*.yaml | wc -l) -eq 51 && ./scripts/verify-rigs.sh --check-only`
- **Cross-examination:** Beta-challenger CONFIRMED BROKEN (15 pods + 51 members re-counted exact in source); P1 retained.

### HR-1.4-pregen-files: Per-role file set absent
- **Priority:** P0
- **Claim:** 1.4 — every role dir has 7 files, zero TODO, matches `rigs/` copy.
- **Location:** `specs/` (absent); generator `scripts/generate-rigs.py:523-647`
- **Proof:** `Glob specs/**/*` → none
- **Raw output:** `No files found`
- **Why it matters:** 357-file promise (51×7) unmet on disk.
- **Remediation:** Generate; assert 51×7 files and `diff -r` specs vs rigs copies clean.
- **Verify the fix:** `find specs/agents -type f | wc -l` equals 357 and `./scripts/verify-rigs.sh --check-only`
- **Cross-examination:** Beta-challenger CONFIRMED BROKEN.

### HR-2.1-missing-rigs: No RigSpec subjects for `rig spec validate`
- **Priority:** P0
- **Claim:** 2.1 — every `rig.yaml` declares `version: 0.2`, valid keys, passes `rig spec validate --json`.
- **Location:** `rigs/*/rig.yaml` (absent); generator `scripts/generate-rigs.py:797-811` (version 0.2); verifier `scripts/verify-rigs.sh:300-304`
- **Proof:** `Glob rigs/**/*` from repo root
- **Raw output:** `No files found`
- **Why it matters:** Core OpenRig contract unproven against real `@openrig/cli@0.6.11`.
- **Remediation:** Generate, install `@openrig/cli@0.6.11`, run §4 recipe 2 verbatim.
- **Verify the fix:** `for d in rigs/*/; do rig spec validate "$d/rig.yaml" --json | jq -e '.valid == true'; done`
- **Cross-examination:** Alpha-challenger CONFIRMED BROKEN (gitignore bid fails — ignores only `.scratch/`/deps, not `rigs/`).

### HR-2.2-missing-edges: Edge topology without subjects
- **Priority:** P0
- **Claim:** 2.2 — pod-local unqualified edges, cross-pod `pod.member`, 5 kinds, DAG acyclic.
- **Location:** `rigs/*/rig.yaml` (absent); source `fleet/fleet.yaml:40-70`; verifier `scripts/verify-rigs.sh:372-399`
- **Proof:** Same absence; sabotage UNVERIFIABLE (shell blocked)
- **Raw output:** `No files found`
- **Why it matters:** Delegation topology is the multi-agent safety invariant.
- **Remediation:** Generate; run verifier DAG check + `rig spec preflight` ×8.
- **Verify the fix:** `./scripts/verify-rigs.sh --check-only && for r in rigs/*/rig.yaml; do rig spec preflight "$r"; done`
- **Cross-examination:** Alpha-challenger CONFIRMED.

### HR-2.3-schema-mismatch: No agent.yaml subjects
- **Priority:** P0
- **Claim:** 2.3 — every `agent.yaml` declares nested lifecycle + zero `hooks`.
- **Location:** `specs/agents/*/*/agent.yaml` (absent); generator `scripts/generate-rigs.py:596-654`; verifier `scripts/verify-rigs.sh:158-188`
- **Proof:** `Glob specs/**/*` → none; `rig agent validate` UNVERIFIABLE
- **Raw output:** `No files found`
- **Why it matters:** 51 AgentSpecs unvalidated against the real OpenRig CLI.
- **Remediation:** Generate; live `rig agent validate` ×51.
- **Verify the fix:** `rig agent validate` ×51 green + `./scripts/verify-rigs.sh --check-only`
- **Cross-examination:** Alpha-challenger CONFIRMED BROKEN.

### HR-2.4-recipe-correct-unproven: `guidance_merge` guard code-complete, catch unproven
- **Priority:** P1
- **Claim:** 2.4 — zero `guidance_merge`; charters in per-seat `<agentDir>/AGENTS.md`.
- **Location:** Generator `scripts/generate-rigs.py:642-649` (`delivery_hint: send_text`); verifier `scripts/verify-rigs.sh:184-188` (specs) + `:349-356` (vendored); renderer `scripts/render-seat.py:360-381`
- **Proof:** No `agent.yaml` exists to sabotage; `Grep guidance_merge scripts/` hits only `generate-rigs.py:981` (legitimate `toldFiles` culture delivery, not `startup.files`) + comments
- **Raw output:** `No files found`; `generate-rigs.py:981` is `toldFiles`, not `startup.files`
- **Why it matters:** The shared-AGENTS.md collision guard is code-only, never executed.
- **Remediation:** Generate then dual sabotage (`send_text→guidance_merge` in both `specs/` and one vendored copy → gate must exit 1 each).
- **Verify the fix:** Above sabotage pair (UNVERIFIABLE here).
- **Cross-examination:** Alpha-challenger CONFIRMED BROKEN; downgrade-to-PARTIAL-P2 bid REJECTED (disk half entirely absent).

### HR-2.5-missing-bundles: Bundle containment without bundles
- **Priority:** P0
- **Claim:** 2.5 — zero symlinks, containment, `rig bundle check --json == []` ×8.
- **Location:** `specs/`, `rigs/` (absent); verifier `scripts/verify-rigs.sh:277-281`
- **Proof:** Globs empty; `find`/`rig bundle check` UNVERIFIABLE
- **Raw output:** `No files found`
- **Why it matters:** Bundle escape is the OpenRig containment boundary.
- **Remediation:** Generate; run §4 recipe 2.
- **Verify the fix:** `find specs rigs -type l | wc -l` equals 0 and 8× `bundle check` clean.
- **Cross-examination:** Alpha-challenger CONFIRMED.

### HR-3.1-empty-registry: Schemas present, subjects absent
- **Priority:** P0
- **Claim:** 3.1 — 8 configurations + 8 behaviour + 8 entries + status.json validate vs schemas.
- **Location:** `schemas/` PRESENT (6 files); `registry/`, `rigs/` absent; verifier `scripts/verify-rigs.sh:498-513`
- **Proof:** `Glob schemas/*` → 6 files; `Glob registry/**/*` → none; validator UNVERIFIABLE
- **Raw output:** 6 schema paths; `No files found` (subjects)
- **Why it matters:** v1 bundle formats are the launch contract; nothing to validate against.
- **Remediation:** Generate registry/configurations; add mutated-doc negative test.
- **Verify the fix:** `Draft202012Validator` green over all ~25 subject files; mutated doc red.
- **Cross-examination:** Beta-challenger CONFIRMED BROKEN (PARTIAL-downgrade bid rejected — zero subjects means validation contract unmet).

### HR-3.2-jcs-proof-gated: explicit JCS canonicalizer in code, disk proof gated
- **Priority:** P3
- **Claim:** 3.2 — `registry/status.json` bodyDigest == hex sha256 over RFC 8785 JCS canonical JSON.
- **Location:** `scripts/generate-rigs.py:120-152` (`jcs_canonicalize`, UTF-16 sort, float-reject); `scripts/verify-rigs.sh:569-619` (mirror + ASCII-only gate + known-answer); `registry/status.json` absent
- **Proof:** `Read` both canonicalizers; `Glob registry/**/*` → none
- **Raw output:** `def jcs_canonicalize(o):` … `sorted(o.keys(), key=utf16_key)` (both files)
- **Why it matters:** Digest interop is code-agreed but never proven against bytes on disk; non-ASCII bodies fail-closed by gate.
- **Remediation:** Generate registry and recompute independently; vendor full Unicode JCS fixtures or a real RFC 8785 canonicalizer.
- **Verify the fix:** Independent `sha256(jcs(body))` equals file value + known-answer test green.
- **Cross-examination:** Beta-challenger CONFIRMED PARTIAL P3.

### HR-3.3-vectors-proof-absent: vectors vendored; digest proof open
- **Priority:** P1
- **Claim:** 3.3 — digests match official `identity-vectors.json` vectors.
- **Location:** `identity-vectors.json:1-31` PRESENT (utf16 `A=pi,a=pi,b=pi`, JCS `{"a":1,"b":2}`, coverage `openrig.package-digest/v1`, algorithm `sha256`); replay `scripts/verify-rigs.sh:626-649`
- **Proof:** `Read identity-vectors.json:1-31` verbatim; `Glob rigs/**/*`, `Glob registry/**/*` → none; replay UNVERIFIABLE
- **Raw output:** `identity-vectors.json:12` `"expected": "A=pi,a=pi,b=pi"`; `No files found` (subjects)
- **Why it matters:** Digest correctness rests solely on the generator agreeing with itself until replayed against generated trees.
- **Remediation:** Generate, run gate replay, then independently recompute `configurationId`/`packageDigest`/`bodyDigest` from disk.
- **Verify the fix:** Verifier replays vendored vectors, fails on mismatch + independent recompute matches.
- **Cross-examination:** Beta-challenger CONFIRMED PARTIAL.

### HR-4.1-pins-unmaterialized: Model/runtime pins declared but unmaterialized
- **Priority:** P0
- **Claim:** 4.1 — all agents+members pin `opencode-go/muse-spark-1.3-contributor:high` + `runtime: pi`; `configurations.yaml` has an `all-omp` preset (`runtime: omp`).
- **Location:** `rigs/*/rig.yaml` absent; source `fleet/fleet.yaml:8-17`; generator + verifier pin gates
- **Proof:** Model pins present in fleet; zero materialized seats; `preflight` UNVERIFIABLE
- **Raw output:** `fleet.yaml:8-17`; `No files found` (rigs)
- **Why it matters:** Wrong model/runtime = seats boot wrong harness (cf. `PI_PROVIDER_ENV_VARS` trap).
- **Remediation:** Generate; enforce recipe §4.2 + `rig spec preflight` ×8.
- **Verify the fix:** `grep -rh 'muse-spark' rigs/*/rig.yaml | sort -u` single pin + preflight green.
- **Cross-examination:** Alpha-challenger CONFIRMED BROKEN.

### HR-4.2-bootstrap-residual: strict default in code; seat-materialization gate missing
- **Priority:** P2
- **Claim:** 4.2 — render/seed/bootstrap provision 6 seat files 0600 with correct endpoint.
- **Location:** `scripts/bootstrap-pi-seats.sh:17` (`ALLOW_MISSING=""`), `:46-58`; `scripts/render-seat.py` (`os.chmod 0o600`); verifier seat-dir sampling opt-in only (`HERETEK_REQUIRE_SEATS=1`)
- **Proof:** Read-verified; 0644-refusal + isolated-`OPENRIG_HOME` probes UNVERIFIABLE (shell blocked)
- **Raw output:** `bootstrap-pi-seats.sh:17` strict default; verifier has no default seat-dir assert
- **Why it matters:** Nothing in default CI proves seats were actually materialized with 0600 perms and matching `models.json`.
- **Remediation:** Add gate asserting sampled `$OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent/` dir exists with 0600 files and matching `models.json`.
- **Verify the fix:** `OPENRIG_HOME=$AUDIT_TMP/oh ./scripts/bootstrap-pi-seats.sh --rig executive-and-architecture` without secrets must fail; with 0600 key must produce 0600 files.
- **Cross-examination:** Alpha-challenger CONFIRMED PARTIAL (P1-upgrade bid rejected — seats are host-local by design, correctly opt-in).

### HR-4.3-secret-probe-gap: Secret forms allowed, live refusal/sabotage probes unexecuted
- **Priority:** P2
- **Claim:** 4.3 — command-backed secrets only; renderer refuses missing/group-readable keys.
- **Location:** `fleet/mcp-servers.yaml:7-11` (three allowed forms); `scripts/render-seat.py:111-120,136-137,204-207`; verifier `scripts/verify-rigs.sh:653-677`
- **Proof:** Forms documented and allowed; no literals in reads; refusal probe + `sk-live` sabotage UNVERIFIABLE (shell blocked)
- **Raw output:** `mcp-servers.yaml` allowed Authorization form `"!echo Bearer $(cat @SECRETS@/github.pat)"`
- **Why it matters:** Secret-handling posture is code-reviewed only, which the Cardinal Rule forbids counting as proof.
- **Remediation:** Run §4 recipe 4 (0644 must fail, 0600 must pass) + `mcp.json` literal sabotage must flip gate.
- **Verify the fix:** `verify-rigs.sh` V6 green + 0644-refusal probe green.
- **Cross-examination:** Gamma-challenger CONFIRMED PARTIAL (P3-downgrade bid rejected — missing verification coverage for a secret boundary is P2 per rubric).

### HR-4.4-literal-floor-note: verifier fixed in code; note only
- **Priority:** P3
- **Claim:** 4.4 — no `rig.yaml` `env:` secrets/reserved names; no literal secrets in repo.
- **Location:** `scripts/verify-rigs.sh:290-298` (rig.yaml env ban + name list + literal-material regex), `:681-717` (fleet/mcp/registry scans)
- **Proof:** Controller-read confirms rig.yaml value scan; `Grep` literal-secret regex under `fleet/` → zero hits
- **Raw output:** `verify-rigs.sh:293-298` verbatim scans
- **Why it matters:** Residual is defense-depth note only, no bypass demonstrated.
- **Remediation:** Keep scans; optionally add short-literal entropy check.
- **Verify the fix:** Planted-secret sabotage trio each makes gate exit 1 (UNVERIFIABLE here).
- **Cross-examination:** Gamma-challenger CONFIRMED P3.

### HR-5.1-locked-unmaterialized: Locked-seat source correct, rig.yaml absent
- **Priority:** P2
- **Claim:** 5.1 — 18 seats `builtin:locked`; 16 readonly confined to `docs/*`/`sbom/*`; no yolo/open.
- **Location:** `fleet/fleet.yaml` 20x `builtin:locked` (= 2 rig + 18 role-level); 16x `readonly_charter: true`; `rigs/*/rig.yaml` absent
- **Proof:** `Grep builtin:locked` → 20 hits; `Grep readonly_charter: true` → 16 hits; `Grep builtin:yolo|builtin:open` in fleet → zero hits
- **Raw output:** Grep tallies as above
- **Why it matters:** Disk half vacuous without generated `rig.yaml`; propagation UNVERIFIABLE.
- **Remediation:** Generate; assert 18-set in `rigs/*/rig.yaml`.
- **Verify the fix:** `verify-rigs.sh` green + `rig spec preflight` ×8.
- **Cross-examination:** Gamma-challenger CONFIRMED P2.

### HR-5.2-guards-unproven: Full guards in code, live proof missing
- **Priority:** P1
- **Claim:** 5.2 — `path_write` starts `*:deny`, 10 guards, ends `*..*:deny` as last key; same last-rule for `path`.
- **Location:** `scripts/render-seat.py:268-285`; verifier `scripts/verify-rigs.sh:225-240`; `scripts/gate-role.sh:53-56,74` (extended corpus)
- **Proof:** Guard tuple+ordering read-verified (`render-seat.py:271-285` tuple verbatim); zero rendered `config.json`; hostile corpus UNVERIFIABLE
- **Raw output:** `render-seat.py:271-285` tuple verbatim; `gate-role.sh:55,74` dot-dot probes
- **Why it matters:** `..` traversal protection is code-reviewed only, never proven against real `@gotgenes/pi-permission-system@41.0.0`.
- **Remediation:** Regenerate + run §4 recipe 3 assertion ×51 + `gate-role.sh` hostile corpus.
- **Verify the fix:** Recipe 3 green ×51 + `gate-role.sh` denies `docs/../../src/evil.ts`, `AGENTS.md`, `.env.production`.
- **Cross-examination:** Gamma-challenger CONFIRMED P1 (P2-downgrade bid rejected — untested security invariant is P1 by rubric).

### HR-5.3-url-user-present: denies in code; live proof missing
- **Priority:** P3
- **Claim:** 5.3 — denies secrets, `external_directory: deny`, `promptTimeoutMs: 60000`, zero `ask`.
- **Location:** `scripts/render-seat.py:323-350` (18 denies incl `*.url`, `*.user`); verifier `scripts/verify-rigs.sh:216-224`; `scripts/gate-role.sh:57-73`
- **Proof:** Controller-read of maps; hostile corpus UNVERIFIABLE
- **Raw output:** `render-seat.py:347-348` deny map verbatim
- **Why it matters:** A seat with `read: allow` could otherwise read `*.url`/`*.user` credential files — now denied in code.
- **Remediation:** Keep denies; run `bash scripts/gate-role.sh <role>` `.env` read probe.
- **Verify the fix:** `gate-role.sh` denies `.env` read and per-suffix probes.
- **Cross-examination:** Gamma-challenger CONFIRMED P3.

### HR-5.4-extension-unproven: Triple-deny in code, live bypass untested
- **Priority:** P1
- **Claim:** 5.4 — `code_rewrite/lsp_rename/lsp_code_actions: deny` everywhere; 21 builder seats allow read-only AST/LSP only.
- **Location:** `scripts/render-seat.py:306-310`; verifier `scripts/verify-rigs.sh:241-243`; `fleet/fleet.yaml` (21 roles bind `pi-lsp-extension@1.4.0`; zero `pi-lsp@`/`pi-subagents`)
- **Proof:** Read+Grep confirm; no `pi` execution
- **Raw output:** `render-seat.py:309-310` triple-deny verbatim (unconditional)
- **Why it matters:** Upstream classifies these as `ToolKind=extension` (name-checked only) — one missing deny = silent mutation on locked seats.
- **Remediation:** Keep unconditional deny; keep CI assertion per extension-loading seat; run live `code_rewrite` attempt.
- **Verify the fix:** Sabotage `deny→allow` makes gate exit 1; live attempt denied.
- **Cross-examination:** Gamma-challenger CONFIRMED P1.

### HR-5.5-bash-matcher: deny-first + metachar fixed in code; matcher semantics unproven
- **Priority:** P2
- **Claim:** 5.5 — `bash *:deny` + scoped allows; `mcp *:deny` + per-server allow.
- **Location:** `scripts/render-seat.py:287-303` (`die` on metachar + `$(` + `--output`); `scripts/generate-rigs.py:363-376` (mirror); verifier `scripts/verify-rigs.sh:244-271`; `scripts/gate-role.sh:46-52`
- **Proof:** Static — metachar now dies at generation; matcher whether prefix-glob unvendored; exploit UNVERIFIABLE
- **Raw output:** `render-seat.py:293` verbatim; verifier `:270` verbatim
- **Why it matters:** If the matcher is prefix-glob, redirection escapes would collapse the `builtin:locked` story — now blocked at generation, but live proof missing.
- **Remediation:** Keep generation-time die + verifier assertion; add live chaining/redirection probes.
- **Verify the fix:** New assertion + chaining probes red→green (needs shell+`pi`).
- **Cross-examination:** Gamma-challenger CONFIRMED P2 (P2→P3 bid REJECTED — live chaining/redirection probes still unexecuted).

### HR-5.5-render-output-allow: renderer+generator now fail-closed on `--output`; live die-probe unexecuted
- **Priority:** P3
- **Claim:** 5.5 ("zero `git diff/log/show --output=*` write escapes")
- **Location:** `scripts/render-seat.py:299-302` (`if "--output" in p: die(…)`); `scripts/generate-rigs.py:371-376` (mirror); sole prior control `scripts/verify-rigs.sh:265-266`; probe `scripts/gate-role.sh:49`
- **Proof:** `Grep --output scripts/render-seat.py scripts/generate-rigs.py` → die-guard in both (controller-verified); `Grep --output fleet/fleet.yaml` → zero fleet patterns; live die-probe NOT RUN (shell blocked)
- **Raw output:** `render-seat.py:299: if "--output" in p:` / `:300-302: die(…forbidden --output write-escape…)`; `generate-rigs.py:374: if "--output" in _pat:`
- **Why it matters:** Direct `render-seat.py` use no longer silently materializes a file-write escape bypassing `path_write` — but the die path itself never fired here.
- **Remediation:** DONE in code. Keep. Fleet edit adding `git show --output=/tmp/x*` must make generation `die`.
- **Verify the fix:** Above fleet edit makes generation `die` (requires shell; UNVERIFIABLE here). Kept OPEN P3 until then.
- **Cross-examination:** Gamma-challenger ruled NOT-FIXED until execution — stays OPEN P3.

### HR-5.4-gate-coverage: live corpus now probes all three mutating tools in code; live run unexecuted
- **Priority:** P3
- **Claim:** 5.4 (methodology: hostile corpus + `gate-role.sh`)
- **Location:** `scripts/gate-role.sh:75-80` (`code_rewrite :75`, `lsp_rename :79`, `lsp_code_actions :80`)
- **Proof:** `Read gate-role.sh:75-80`; `Grep lsp_rename|lsp_code_actions scripts/gate-role.sh` → hits at `:79,:80`
- **Raw output:** `:75 expect deny code_rewrite …` / `:79 expect deny lsp_rename …` / `:80 expect deny lsp_code_actions …`
- **Why it matters:** A regression dropping any one of the three deny lines now trips the live corpus in code, not just the static verifier — but the corpus never fired here.
- **Remediation:** DONE in code. Keep.
- **Verify the fix:** `bash scripts/gate-role.sh appsec-engineer` shows `ok` for all three (requires `pi`; UNVERIFIABLE here). Kept OPEN P3 until then.
- **Cross-examination:** Gamma-challenger ruled NOT-FIXED until execution — stays OPEN P3.

### HR-6.1-unbuilt-catalog: 62-skill vendoring unexecuted
- **Priority:** P0
- **Claim:** 6.1 — shared `agent.yaml` vendors 62 skills with `SKILL.md`+LICENSE matching lock.
- **Location:** `fleet/skills-lock.json` (absent), `specs/` (absent); logic `scripts/generate-rigs.py:462-507`; gate `scripts/verify-rigs.sh:130,150-154`
- **Proof:** `Glob **/skills-lock*` → none; `Glob specs/**/*` → none
- **Raw output:** `No files found` ×2
- **Why it matters:** Shared skills are the agent operating system; absence = no seat has SOPs.
- **Remediation:** Vendor pins, run generation, assert 62 dirs + frontmatter + LICENSE + lock match.
- **Verify the fix:** `find specs/agents/_shared/skills -name SKILL.md | wc -l` equals 62 and `./scripts/verify-rigs.sh --check-only`.
- **Cross-examination:** Beta-challenger CONFIRMED BROKEN.

### HR-6.2-pins-liveness: Pins textually right; liveness and per-seat halves gap
- **Priority:** P2
- **Claim:** 6.2 — every MCP server pinned exact+verified, read-only flags enforced.
- **Location:** `fleet/mcp-servers.yaml:19-266` (pins+flags); per-seat `runtime/mcp.json` absent
- **Proof:** `Read` + `Grep :latest|r2mcp|aws-mcp` → active pins clean (hits only `replaces:` comments); `npm view`/`pip index` NOT RUN (shell blocked)
- **Raw output:** `replaces: pypi:r2mcp==0.2.5`, `replaces: npm:aws-mcp@1.0.2` (comments only)
- **Why it matters:** Admitted not-run servers + unverified registry existence = supply-chain risk.
- **Remediation:** Re-run failed/not-run servers, pin-verify each, generate per-seat `mcp.json`.
- **Verify the fix:** All servers `status: run-verified` + V6 gate green.
- **Cross-examination:** Beta-challenger CONFIRMED PARTIAL ("wrong package" sub-claim refuted — file correctly rejects both; liveness gap stands).

### HR-7.1-compose-unproven: Sidecar baseline present, runtime unproven
- **Priority:** P1
- **Claim:** 7.1 — every host port binds `127.0.0.1:`; every image pinned/`@sha256` (zero `:latest`).
- **Location:** `docker-compose.sidecars.yml:52-140` (8× `127.0.0.1:`); 10 images pinned; verifier `scripts/verify-rigs.sh:799-824`
- **Proof:** `Read` + `Grep 0.0.0.0|:latest` → zero active hits; `compose config` unexecuted
- **Raw output:** Compose lines cited
- **Why it matters:** Exposed sidecars on non-loopback = network boundary failure.
- **Remediation:** Run `docker compose -f docker-compose.sidecars.yml config` shows only `127.0.0.1:` publishes, zero `:latest`.
- **Verify the fix:** Same compose config command.
- **Cross-examination:** Gamma-challenger CONFIRMED P1 (P1→P2 bid REJECTED — loopback binding is a P1 network boundary until `compose config` + sabotage pair prove it).

### HR-7.2-proxy-residual: 18 toggles pinned in code; exhaustiveness + live proof missing
- **Priority:** P3
- **Claim:** 7.2 — proxy pinned, `:ro` sock mount, toggles deny.
- **Location:** `docker-compose.sidecars.yml:18-43` (pin + 18×`0` + `:ro`); verifier `scripts/verify-rigs.sh:826-841`
- **Proof:** Controller-read of both; sabotage + live `GET /containers/json` UNVERIFIABLE; upstream README exhaustiveness unvendored (no network)
- **Raw output:** `docker-compose.sidecars.yml:24-41` 18× `"0"` verbatim
- **Why it matters:** Verifier enforces exactly the set compose declares; upstream family unproven.
- **Remediation:** Diff full toggle set against vendored image README version; run `POST:1` fixture (must flip gate) + live least-privilege probe.
- **Verify the fix:** `POST: 1` fixture makes gate exit 1; live `GET /v1.xx/containers/json` via proxy denied.
- **Cross-examination:** Gamma-challenger CONFIRMED P3.

### HR-7.3-network-note: Literal satisfied; shared-tenant hardening note
- **Priority:** P3
- **Claim:** 7.3 — `ghidra`+`radare2` only on `heretek-devsec` + `:ro` samples; `docker-android` only on `heretek-mobile`; guard refuses bad co-scheduling.
- **Location:** Compose `ghidra:92-101` + `:ro`, `radare2:103-112` + `:ro`, `docker-android:134-142`, nets `internal:true:148-153`; guard `Makefile:45-53`
- **Proof:** `Read` as cited; `make guard-profiles` 3-case matrix NOT RUN (shell blocked); verifier only greps keywords, never evaluates logic
- **Raw output:** `Makefile:45-53`; compose cited ranges
- **Why it matters:** `sonarqube` co-resides on `heretek-devsec` (documented intentional per compose `:6-14`); guard bypassable via direct `docker compose --profile` (lives only in `make`); `devsec×web-research` allowed by design. Defense-in-depth note, not breach.
- **Remediation:** Document intended coexistence matrix (done in compose header); add verifier coverage invoking the guard matrix.
- **Verify the fix:** `! make guard-profiles SIDECAR_PROFILES="mobile devsec"`, `! make guard-profiles SIDECAR_PROFILES="mobile web-research"`, `make guard-profiles SIDECAR_PROFILES="web-research"`.
- **Cross-examination:** Gamma-challenger CONFIRMED P3.

### HR-8.1-not-generated: Generation never ran; `--check-idempotent` exists but unrun
- **Priority:** P1
- **Claim:** 8.1 — `generate-rigs.py` idempotent: twice in clean checkout → zero diffs.
- **Location:** `specs/`, `rigs/`, `registry/`, `rosters/` (absent); `scripts/generate-rigs.py:1281-1321` (`--check-idempotent`); `Makefile:27-28`; verifier contains no generator re-run gate
- **Proof:** Outputs absent (`Glob` ×4 → none; first run necessarily diffs); twice-run UNVERIFIABLE
- **Raw output:** `No files found` (outputs)
- **Why it matters:** Non-deterministic generation = phantom digest diffs; claim asserted with opt-in CLI only.
- **Remediation:** Vendor all inputs, run `python3 scripts/generate-rigs.py --check-idempotent --root $AUDIT_TMP/regen`, wire into CI/gate.
- **Verify the fix:** Above command prints `idempotence check passed` with empty diff.
- **Cross-examination:** Alpha-challenger CONFIRMED BROKEN.

### HR-8.2-gate-red: Verification gate red on clean checkout
- **Priority:** P0
- **Claim:** 8.2 — `verify-rigs.sh --check-only` exits 0 clean, non-zero on any `[S]` sabotage.
- **Location:** `scripts/verify-rigs.sh:130` (`json.loads((root/"fleet/skills-lock.json").read_text())` → FileNotFoundError); also role discovery + rig.yaml gates
- **Proof:** Absence facts + code path read-verified; execution UNVERIFIABLE but failure path explicit
- **Raw output:** `File not found: .../fleet/skills-lock.json` (deduced path; shell blocked)
- **Why it matters:** Clean checkout fails for the wrong reason, so sabotage-catch cannot be demonstrated.
- **Remediation:** Run pinned generation pipeline, then re-run full §4 sabotage matrix (12 one-line breaks, each must flip gate 0→1).
- **Verify the fix:** `./scripts/verify-rigs.sh --check-only` exits 0 clean; each sabotage exits 1.
- **Cross-examination:** Alpha-challenger CONFIRMED BROKEN (downgrade-to-UNVERIFIABLE bid REJECTED — missing file + unconditional read is deterministic, and fail-closed sentinel requires the gate red to be recorded as BROKEN until generation proves otherwise).

### HR-8.3-evaluator-execution: evaluator logic in code; self-test gate-blocked red
- **Priority:** P1
- **Claim:** 8.3 — `audit_loop.py --self-test` exits 0 and evaluator rejects `NO_FINDINGS` lies.
- **Location:** `scripts/audit_loop.py:62-109` (combined scan, `### HR-` headers, ledger `BROKEN|PARTIAL` incl fenced rows), `:149-170` (self-test gates on verify first → returns 1 here)
- **Proof:** Controller-read verbatim ranges; self-test execution UNVERIFIABLE (gate red ⇒ self-test red, deduced not executed)
- **Raw output:** `audit_loop.py:62-109`, `:149-170` as cited
- **Why it matters:** The deterministic sentinel is the loop's only defense against false NO_FINDINGS; logic now correct but "exits 0" half false pre-generation by design.
- **Remediation:** Generate until gate green, then `python3 scripts/audit_loop.py --self-test` must exit 0; keep 7-vector assertions.
- **Verify the fix:** Post-generation self-test exits 0.
- **Cross-examination:** Alpha-challenger CONFIRMED BROKEN (BROKEN→PARTIAL bid REJECTED — evaluator-correct-but-gated is still a BROKEN "exits 0" claim until the gate is green).

## Claim Ledger
| Claim | Status | Evidence (command or finding ID) |
|-------|--------|----------------------------------|
| Claim 1.1 [B] | BROKEN | HR-1.1-missing-specs-trees (`Glob specs/**/*` → none) |
| Claim 1.2 [B] | BROKEN | HR-1.2-pregen-partition (`Glob rigs/**/*` → none) |
| Claim 1.3 [B] | BROKEN | HR-1.3-omni-fragments (source explicit; artifacts absent; P1 per controller) |
| Claim 1.4 [B] | BROKEN | HR-1.4-pregen-files (specs absent) |
| Claim 2.1 [A] | BROKEN | HR-2.1-missing-rigs (no rig.yaml; `rig spec validate` UNVERIFIABLE) |
| Claim 2.2 [A] | BROKEN | HR-2.2-missing-edges (no rig.yaml) |
| Claim 2.3 [A] | BROKEN | HR-2.3-schema-mismatch (no agent.yaml; `rig agent validate` UNVERIFIABLE) |
| Claim 2.4 [A] | BROKEN | HR-2.4-recipe-correct-unproven (recipe in code; subjects absent; P1) |
| Claim 2.5 [A] | BROKEN | HR-2.5-missing-bundles (`find`/`bundle check` UNVERIFIABLE) |
| Claim 3.1 [B] | BROKEN | HR-3.1-empty-registry (6 schemas present; ~25 subjects absent) |
| Claim 3.2 [B] | PARTIAL | HR-3.2-jcs-proof-gated (P3; code explicit; disk proof gated, ASCII-only limit) |
| Claim 3.3 [B] | PARTIAL | HR-3.3-vectors-proof-absent (P1; vectors vendored; proof unexecuted) |
| Claim 4.1 [A] | BROKEN | HR-4.1-pins-unmaterialized (source pins OK; disk empty) |
| Claim 4.2 [A] | PARTIAL | HR-4.2-bootstrap-residual (strict default in code; seat-gate opt-in only; unexecuted) |
| Claim 4.3 [G] | PARTIAL | HR-4.3-secret-probe-gap (forms allowed; probes UNVERIFIABLE) |
| Claim 4.4 [G] | PARTIAL | HR-4.4-literal-floor-note (scans in code; P3 note; unexecuted) |
| Claim 5.1 [G] | PARTIAL | HR-5.1-locked-unmaterialized (20 locked in source incl 18 role; rig.yaml absent) |
| Claim 5.2 [G] | PARTIAL | HR-5.2-guards-unproven (guards in code; UNVERIFIABLE live) |
| Claim 5.3 [G] | PARTIAL | HR-5.3-url-user-present (denies in code; live proof missing) |
| Claim 5.4 [G] | PARTIAL | HR-5.4-extension-unproven + HR-5.4-gate-coverage (P3; triple-deny in code; live test missing) |
| Claim 5.5 [G] | PARTIAL | HR-5.5-bash-matcher + HR-5.5-render-output-allow (P3; `--output` die in code; matcher unproven) |
| Claim 6.1 [B] | BROKEN | HR-6.1-unbuilt-catalog (`skills-lock.json` + `specs/` absent) |
| Claim 6.2 [B] | PARTIAL | HR-6.2-pins-liveness (pins OK; liveness + per-seat halves missing) |
| Claim 7.1 [G] | PARTIAL | HR-7.1-compose-unproven (P1; loopback holds in file; `compose config` missing) |
| Claim 7.2 [G] | PARTIAL | HR-7.2-proxy-residual (18 toggles in code; exhaustiveness + live proof missing) |
| Claim 7.3 [G] | PARTIAL | HR-7.3-network-note (literal satisfied per P3 note; matrix missing) |
| Claim 8.1 [A] | BROKEN | HR-8.1-not-generated (outputs absent; `--check-idempotent` unrun) |
| Claim 8.2 [A] | BROKEN | HR-8.2-gate-red (`verify-rigs.sh:130` FileNotFoundError clean) |
| Claim 8.3 [A] | BROKEN | HR-8.3-evaluator-execution (logic in code; self-test gate-blocked) |
| Claim 8.4 [B] | VERIFIED | 8/8 deliverables present non-empty, placeholder-free (`Read`+`Grep`; no finding) |

## Sabotage Results
| Invariant | One-line sabotage (file:line, before -> after) | Suite result | Caught? |
|-----------|------------------------------------------------|--------------|---------|
| 2.1 | `rigs/executive-and-architecture/rig.yaml`: add `unknown_key: true` | NOT RUN (no rig.yaml; shell blocked; code would catch post-generation) | UNVERIFIABLE |
| 2.2 | `rigs/executive-and-architecture/rig.yaml`: add cycle edge `{kind: delegates_to, from: product-director, to: exec-director}` | NOT RUN; code would catch post-generation | UNVERIFIABLE |
| 2.4 | `specs/agents/executive/exec-director/agent.yaml`: `delivery_hint: send_text` -> `delivery_hint: guidance_merge` | NOT RUN (target absent; code specs + vendored gates would catch) | UNVERIFIABLE |
| 2.5 | `rigs/executive-and-architecture/agents/link.md`: `ln -s ../README.md` symlink | NOT RUN; code would catch post-generation | UNVERIFIABLE |
| 3.2 | `registry/status.json`: flip one `bodyDigest` hex char | NOT RUN (`registry/` absent; suite already red) | UNVERIFIABLE |
| 4.3 | `specs/agents/executive/exec-director/runtime/mcp.json`: `"!cat /..."` -> `"sk-live-123456"` | NOT RUN (target absent; literal path would trip) | UNVERIFIABLE |
| 5.1 | `rigs/executive-and-architecture/rig.yaml`: `exec-director` `builtin:locked` -> `builtin:yolo` | NOT RUN (no rig.yaml; code would catch) | UNVERIFIABLE |
| 5.2 | `specs/agents/executive/exec-director/runtime/policy-enforcement.json`: remove `"*..*": "deny"` | NOT RUN (target absent; code would catch) | UNVERIFIABLE |
| 5.4 | `specs/agents/security/appsec-engineer/runtime/policy-enforcement.json`: `"code_rewrite": "deny"` -> `"allow"` | NOT RUN; code would catch | UNVERIFIABLE |
| 7.1 | `docker-compose.sidecars.yml`: `127.0.0.1:8888:8080` -> `0.0.0.0:8888:8080` | NOT RUN (shell blocked; file present; code would catch) | UNVERIFIABLE |
| 7.2 | `docker-compose.sidecars.yml`: `POST: "0"` -> `POST: "1"` under `docker-socket-proxy` | NOT RUN (shell blocked; file present; code would catch) | UNVERIFIABLE |
| 1.1 | `specs/agents/qa/static-analysis-lead/agent.yaml` (absent): delete file -> missing | NOT RUN (shell permission.rejected; target absent; suite already red) | UNVERIFIABLE |

## Regression Ledger
| Previous finding ID | Previous priority | Status now: FIXED / STILL OPEN / REGRESSED / NO LONGER APPLICABLE | Evidence |
|---|---|---|---|
| HR-1.1-missing-specs-trees | P0 | STILL OPEN | `specs/` still absent |
| HR-1.2-pregen-partition | P0 | STILL OPEN | `rigs/` still absent |
| HR-1.3-omni-fragments | P1 | STILL OPEN | omni artifacts still absent |
| HR-1.4-pregen-files | P0 | STILL OPEN | Disk absent |
| HR-2.1-missing-rigs | P0 | STILL OPEN | No rig.yaml |
| HR-2.2-missing-edges | P0 | STILL OPEN | No edges on disk |
| HR-2.3-schema-mismatch | P0 | STILL OPEN | No agent.yaml |
| HR-2.4-recipe-correct-unproven | P1 | STILL OPEN | Recipe correct; subjects absent |
| HR-2.5-missing-bundles | P0 | STILL OPEN | Bundles absent |
| HR-3.1-empty-registry | P0 | STILL OPEN | Subjects absent |
| HR-3.2-jcs-proof-gated | P3 | STILL OPEN | `generate-rigs.py:120-152`, verifier mirror |
| HR-3.3-vectors-proof-absent | P1 | STILL OPEN | `identity-vectors.json:1-31` present; proof unexecuted |
| HR-4.1-pins-unmaterialized | P0 | STILL OPEN | Disk empty |
| HR-4.2-bootstrap-residual | P2 | STILL OPEN | `bootstrap-pi-seats.sh:17,46-58` strict default; seat-gate opt-in |
| HR-4.3-secret-probe-gap | P2 | STILL OPEN | Probe UNVERIFIABLE |
| HR-4.4-literal-floor-note | P3 | STILL OPEN | Scans in code |
| HR-5.1-locked-unmaterialized | P2 | STILL OPEN | 20 locked / 16 readonly verified in source; rig.yaml absent |
| HR-5.2-guards-unproven | P1 | STILL OPEN | `render-seat.py:268-285` guards in code; execution UNVERIFIABLE |
| HR-5.3-url-user-present | P3 | STILL OPEN (denies present in code) | `render-seat.py:323-350` |
| HR-5.4-extension-unproven | P1 | STILL OPEN | `render-seat.py:306-310` triple-deny; live test missing |
| HR-5.5-bash-matcher | P2 | STILL OPEN | Metachar die in code; matcher unproven |
| HR-5.5-render-output-allow | P3 | STILL OPEN (fix present in code `render-seat.py:299-302` + `generate-rigs.py:371-376`; live die-probe unexecuted) | `Grep --output` guards in both files |
| HR-5.4-gate-coverage | P3 | STILL OPEN (probes present in code `gate-role.sh:75-80`; live run unexecuted) | `gate-role.sh:75-80` |
| HR-6.1-unbuilt-catalog | P0 | STILL OPEN | Lock + specs absent |
| HR-6.2-pins-liveness | P2 | STILL OPEN | Same liveness gap |
| HR-7.1-compose-unproven | P1 | STILL OPEN | Compose holds; `compose config` missing |
| HR-7.2-proxy-residual | P3 | STILL OPEN | Toggles present in code |
| HR-7.3-network-note | P3 | STILL OPEN | Networks+guard present; matrix missing |
| HR-8.1-not-generated | P1 | STILL OPEN | Outputs absent |
| HR-8.2-gate-red | P0 | STILL OPEN | Gate red path unchanged |
| HR-8.3-evaluator-execution | P1 | STILL OPEN | Evaluator correct in code; execution red |
| HR-8.4-deliverables | VERIFIED (no finding) | NO LONGER APPLICABLE as finding (VERIFIED retained) | 8/8 present non-empty placeholder-free |

## Not Audited / Unverifiable
What could not be checked, why, and what a human needs to provide:
- Every execution-gated proof: `verify-rigs.sh --check-only`, `audit_loop.py --self-test`, 12 sabotage re-runs, `rig spec validate/bundle check/agent validate/spec preflight/expand/add/up/down`, `rig daemon start --no-kernel --port 7699` on loopback, `pi` presence/version/behavior, `python3 -c Draft202012Validator`, `render-seat.py` 0644-vs-0600 probe, `make guard-profiles` matrix (3 cases), `bootstrap-pi-seats.sh` isolated-`OPENRIG_HOME` test, `gate-role.sh` hostile corpus, `docker compose config/down -v`, and all network probes (github.com, registry.npmjs.org, pypi.org, api.osv.dev) — all UNVERIFIABLE because `default.shell` returned `permission.rejected` on every attempt. A human must re-run prompt §4 recipes 1–6 verbatim in a shell-capable host with `rig@0.6.11`, `pi@1.3.0`, Python `jsonschema`+`pyyaml`, Docker, and network, saving raw logs under `$AUDIT_TMP/logs/`.
- Upstream liveness/behavior: `@openrig/cli@0.6.11` schema semantics, `@earendil-works/pi-coding-agent@1.3.0` runtime, `@gotgenes/pi-permission-system@41.0.0` matcher/`ToolKind`/`mcp`-map semantics, `pi-lsp-extension@1.4.0` mutability, Tecnativa `docker-socket-proxy:0.5.0` full toggle defaults, npm/PyPI/GitHub tag existence for every pin, `Heretek-Crew@5ffb1fc` 51-role ground truth — none vendored here.
- Exact `HEAD` SHA, commit date/message, and `git status --porcelain` — shell blocked; only absence/presence via `Glob`/`Read` readable. Tool versions likewise unavailable. No `$AUDIT_TMP` created, no worktree created/removed, no daemon/containers started so nothing to clean.

## Final Loop Sentinel
STATUS: FINDINGS_DETECTED
