# AUDIT_REPORT_FINDINGS: heretek-rigs

## Baseline

- Commit: `e91e914dceb2d4433b2a2a93df6c93dfa57da433`
- Commit date: `2026-10-19 11:29:51 -0400` (`git log -1 --format='%ci %s'` → `2026-10-19 11:29:51 -0400 fiture`)
- Audit date (UTC): Mon Oct 19 2026
- Tool versions (all probed live this run): python3 3.15.0, node v26.10.0, npm 11.19.1, git 2.56.0, jq 1.8.2, rg 15.1.0 (ripgrep), rig 0.6.11 (379f0a0d), pi 1.3.0, docker compose 5.6.0, jsonschema 4.26.0 (Draft2020-12 available)
- Working tree state: DIRTY vs HEAD — `git status --porcelain | wc -l` → `359` (~349 modified + untracked; includes Makefile bash-prefix change, EVENTS/VERSION fix, registry repin). All sabotage experiments ran in a disposable clean worktree (`git worktree add --detach "$AUDIT_TMP/wt" HEAD`, 0 dirty files), never in the real checkout.
- Baselines (controller-verified live this run): clean-HEAD worktree `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 22 checks passed, 3 failed`, exit 1 (all 3 FAILs are docker-socket-proxy EVENTS/VERSION). Dirty worktree (triad) → 22 passed, 0 failed, exit 0. `python3 scripts/audit_loop.py --self-test` → exit 0, `SELF-TEST PASSED` (7 adversarial vectors; vectors are synthetic, not live-gated).
- Host capabilities: local Python jsonschema Draft2020-12 validator, `rig spec validate` / `rig bundle check`, `pi` binary, `docker compose config`, outbound HTTPS — all present/working. NOT run here (state-changing, per hard limits): OpenRig daemon start on loopback, `rig up` / `rig spec preflight` / `rig expand` / `rig agent validate` live launch, container-runtime proxy 403 probes (images not pulled), full `generate-rigs.py` regen without vendor dir.
- Triad + cross-examination (encoded faithfully): Alpha (2.x, 4.1–4.2, 8.x) verdicts upgraded to VERIFIED by cross-examiner Beta via live runs (rig spec validate 8/8 valid, bundle check 8/8 exit 0, render-seat dry-run + 7/7 unit tests, verify 22/0 dirty, self-test pass, unknown_key sabotage caught); daemon up/preflight/expand/agent-validate live launch NOT RUN = UNVERIFIABLE portion. Beta (1.x, 3.x, 6.x, 8.4) all VERIFIED live. Gamma (4.3–4.4, 5.x, 7.x) all VERIFIED live except 7.2 PARTIAL; 30+ live gate-role probes deny; 6 sabotages caught explicitly. Cross-exam: HR-8.1-dirty-worktree P2 CONFIRMED (enhanced), HR-ENV-shell-denied REFUTED (execution works; dropped), HR-3.3-stale-provenance DOWNGRADED to hygiene (entries pin `09270e6f`=HEAD~1 parent; gate checks format-only, V4/V5 PASS; one-commit staleness is structural, NOT a finding), HR-8.2-baseline-red P1 CONFIRMED = same root cause as HR-7.2 (merged below as single finding HR-7.2-events-version).

## Verdict

`heretek-rigs` at HEAD is a real, working 51-role / 8-rig fleet against the systems it plugs into: every verifiable claim replays live (rig validate 8/8, bundle check 8/8 clean, digests byte-identical, permission guards deny hostile probes, all 12 sabotages caught red). The single blemish is that HEAD fails its own gate on a clean checkout over two missing docker-socket-proxy denies, and the working tree carrying that fix plus ~349 other dirty files cannot attribute a clean HEAD-state gate or digest. The single most important thing to fix is to commit the `EVENTS: "0"` + `VERSION: "0"` denies (the exact two-line diff below) so a clean `HEAD` verifies 22/0, then commit or stash the remaining dirt and re-run the generator idempotence check on a clean tree.

## Prioritized Defect Matrix

| ID | Priority | Claim | Location | Summary |
|----|----------|-------|----------|---------|
| HR-7.2-events-version | P1 | 7.2 | `docker-compose.sidecars.yml:24-44` | Proxy ships 18 toggles; gate demands 20. `/events` + `/version` granted by upstream default; clean-HEAD gate exits 1 |
| HR-8.1-dirty-worktree | P2 | 8.1 | repo root (`git status`) | 359 dirty entries; generator refuses dirty provenance bake; HEAD-state gate/digest unattributable while dirty |

## Findings

### HR-7.2-events-version: docker-socket-proxy grants /events and /version by upstream default; clean-HEAD gate is red

- **Priority:** P1
- **Claim:** 7.2 (`docker-socket-proxy` pinned to `tecnativa/docker-socket-proxy:0.5.0`, `:ro` socket mount, deny-all toggle set)
- **Location:** `docker-compose.sidecars.yml:24-44`
- **Proof:** runnable from the repo root:
  ```bash
  export AUDIT_TMP="$(mktemp -d -t heretek-rigs-audit-XXXXXX)"
  git worktree add --detach "$AUDIT_TMP/wt" HEAD
  (cd "$AUDIT_TMP/wt" && ./scripts/verify-rigs.sh --check-only)
  git show HEAD:docker-compose.sidecars.yml | sed -n '24,44p'
  ```
- **Raw output:** (controller-run, clean worktree, exit 1)
  ```
  [FAIL] docker-socket-proxy must set EVENTS=0
  [FAIL] docker-socket-proxy must set VERSION=0
  [FAIL] docker-socket-proxy environment must be exactly the 20-toggle set (got ['AUTH', 'BUILD', 'CONFIGS', 'CONTAINERS', 'EXEC', 'IMAGES', 'INFO', 'NETWORKS', 'NODES', 'PING', 'PLUGINS', 'POST', 'SECRETS', 'SERVICES', 'SWARM', 'SYSTEM', 'TASKS', 'VOLUMES'])
  SUMMARY: 22 checks passed, 3 failed.
  ```
  `git show HEAD:docker-compose.sidecars.yml | sed -n '24,44p'` shows 18 `*_*: "0"` toggles (`POST` through `PLUGINS`) with no `EVENTS` or `VERSION` lines; `grep -cE "EVENTS|VERSION"` on the HEAD file returns 0.
- **Why it matters:** Upstream `tecnativa/docker-socket-proxy:0.5.0` grants `EVENTS`/`PING`/`VERSION` by default (README + Dockerfile evidence, cross-examined), so HEAD deploys a proxy that leaks daemon events and version/fingerprinting surface — and HEAD fails its own verification gate (exit 1) on a clean checkout.
- **Remediation:** exact fail-closed diff (or commit the equivalent hunk already present in the dirty worktree):
  ```diff
        PLUGINS: "0"
  +      EVENTS: "0"
  +      VERSION: "0"
  ```
  applied under the `docker-socket-proxy` `environment:` block in `docker-compose.sidecars.yml`.
- **Verify the fix:** in a clean worktree with the two lines added, `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 22 checks passed, 0 failed`, exit 0 (controller-verified live this run).
- **Cross-examination:** challenged by Alpha; CONFIRMED. Upstream v0.5.0 README + Dockerfile default-grant evidence upheld; P1 (not P0: no container-runtime exploit demonstrated here, images never pulled; not P2: gate is red on clean HEAD, so it blocks the `NO_FINDINGS` sentinel).

### HR-8.1-dirty-worktree: generator refuses dirty provenance bake; HEAD-state evidence unattributable while dirty

- **Priority:** P2
- **Claim:** 8.1 (`python3 scripts/generate-rigs.py` is idempotent: two runs in a clean checkout produce zero `git status --porcelain` or `packageDigest` diffs)
- **Location:** repo root (`git status`)
- **Proof:** runnable from the repo root:
  ```bash
  git status --porcelain | wc -l
  python3 ./scripts/generate-rigs.py --check-idempotent; echo "exit=$?"
  ```
- **Raw output:** (controller-run, real checkout)
  ```
  359
  error: refusing to bake provenance on a dirty checkout (commit or stash first, or set HERETEK_RIGS_ALLOW_DIRTY=1 for dev regen)
  exit=2
  ```
  With the documented dev override, `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py --check-idempotent` exits 0 (`idempotence check passed (two consecutive runs byte-identical)`), and `git status --porcelain | wc -l` remains 359 (regen added no new dirt).
- **Why it matters:** Claim 8.1 evidence requires a clean tree; with 359 dirty entries (including the EVENTS/VERSION fix itself, a Makefile bash-prefix change, and a registry repin) no passing gate or digest in this checkout is attributable to HEAD state, so HEAD-state idempotence is unproven here.
- **Remediation:** commit or stash the dirt, then re-run `python3 ./scripts/generate-rigs.py --check-idempotent` followed by `test -z "$(git status --porcelain)"` and `./scripts/verify-rigs.sh --check-only` (expect exit 0) on the clean tree.
- **Verify the fix:** clean tree + generator exits 0 + `git status --porcelain` empty + gate exit 0.
- **Cross-examination:** challenged by Beta; CONFIRMED (enhanced: 359 entries counted live; generator refuses dirty without `HERETEK_RIGS_ALLOW_DIRTY=1` by design; the dirty delta itself contains the HR-7.2 fix, which is why the dirty tree gates green while clean HEAD gates red).

## Claim Ledger

| Claim | Status | Evidence (command or finding ID) |
|-------|--------|----------------------------------|
| 1.1 | VERIFIED | Beta live: fleet declares 51 roles; all 51 dirs present; removal sabotage caught |
| 1.2 | VERIFIED | Beta live: 6+11+4+6+11+4… 6+11+4+6+11+6+7=51 partition, zero dup/omission |
| 1.3 | VERIFIED | Beta live: 3-seat command pod + 15 pods + 51 members + rig.all-51.yaml + roster |
| 1.4 | VERIFIED | Beta live: per-role file sets complete; drift gate catches beyond-import-rewrite |
| 2.1 | VERIFIED | rig spec validate 8/8 valid (Beta cross-exam live); unknown_key sabotage caught |
| 2.2 | VERIFIED | Controller live sabotage (a): cycle edge → `cycle detected`, exit 1, restored |
| 2.3 | VERIFIED | Beta live: version 1.0 + lifecycle keys + zero hooks across agent.yaml files |
| 2.4 | VERIFIED | Controller live sabotage (b): guidance_merge → 3 FAILs incl `must not use guidance_merge`, exit 1, restored |
| 2.5 | VERIFIED | Controller live sabotage (c): symlink → `Found forbidden symlinks`, exit 1, removed |
| 3.1 | VERIFIED | Beta live: Draft202012Validator over all schemas/subjects, all pass |
| 3.2 | VERIFIED | Beta live: bodyDigest recompute matches; hex-flip sabotage caught |
| 3.3 | VERIFIED | Beta live: configurationId + packageDigest match disk (stale resolvedCommit `09270e6f`=HEAD~1 is hygiene only, gate format-only, V4/V5 PASS — not a finding) |
| 4.1 | VERIFIED | Static + `rig spec validate` live; model/runtime pins hold (daemon preflight/expand/up NOT run — see Not Audited) |
| 4.2 | VERIFIED | render-seat dry-run + 7/7 unit tests live; 0600 enforced (daemon seed not run — see Not Audited) |
| 4.3 | VERIFIED | Gamma live: command-backed secrets only; literal-secret sabotage caught; 0644 refusal probed |
| 4.4 | VERIFIED | Gamma live: no secrets/`OPENRIG_*` in any rig.yaml env; no literals in repo |
| 5.1 | VERIFIED | Gamma live: 18 locked seats; builtin:yolo sabotage caught; read-only write scope holds |
| 5.2 | VERIFIED | Gamma live: `*..*`-last guards; removal sabotage caught; 30+ gate-role hostile probes deny |
| 5.3 | VERIFIED | Gamma live: secret-read denies + external_directory deny + 60000ms + zero ask |
| 5.4 | VERIFIED | Gamma live: triple-deny present 51/51; code_rewrite→allow sabotage caught |
| 5.5 | VERIFIED | Gamma live: bash deny-first + terminal denies; chaining probes deny |
| 6.1 | VERIFIED | Beta live: 62 skills vendored, frontmatter+LICENSE, lockfile match, SOP six present |
| 6.2 | VERIFIED | Beta live: pins exact, zero dead packages, read-only flags enforced, liveness labels honest |
| 7.1 | VERIFIED | Gamma live: loopback-only ports, zero :latest, 0.0.0.0 sabotage caught |
| 7.2 | PARTIAL | HR-7.2-events-version (18/20 toggles at HEAD; /events + /version default-granted; gate red) |
| 7.3 | VERIFIED | Gamma live: devsec/mobile isolation holds; guard-profiles matrix exits 1 on co-schedule |
| 8.1 | PARTIAL | HR-8.1-dirty-worktree (idempotent with ALLOW_DIRTY=1; refuses dirty by design; HEAD-state unattributable while dirty) |
| 8.2 | BROKEN | HR-7.2-events-version root cause: clean-HEAD gate exits 1 (22 passed, 3 failed) |
| 8.3 | VERIFIED | `audit_loop.py --self-test` exit 0 PASSED (7 adversarial vectors; vectors are synthetic, not live-gated) |
| 8.4 | VERIFIED | Beta live: all deliverables exist, non-empty, no unresolved placeholders |

## Sabotage Results

| Invariant | One-line sabotage (file:line, before -> after) | Suite result | Caught? |
|-----------|------------------------------------------------|--------------|---------|
| 1.1 role presence | `specs/agents/qa/static-analysis-lead/agent.yaml`: deleted file -> absent | exit 1, FAIL role-missing (triad live) | Yes |
| 2.1 unknown keys | `rigs/executive-and-architecture/rig.yaml`: valid keys -> +`unknown_key: true` | exit 1, FAIL unknown key (triad live) | Yes |
| 2.2 DAG acyclicity | `rigs/executive-and-architecture/rig.yaml:68`: (absent) -> +`{kind: delegates_to, from: product-director, to: exec-director}` | exit 1, `cycle detected in delegates_to/spawned_by launch graph` (+2 digest FAILs), 20/6 | Yes (controller live) |
| 2.4 no guidance_merge | `specs/agents/executive/exec-director/agent.yaml:52`: `delivery_hint: send_text` -> `delivery_hint: guidance_merge` | exit 1, `must not use guidance_merge` + 2 drift FAILs, 19/6 | Yes (controller live) |
| 2.5 no symlinks | `rigs/executive-and-architecture/agents/link.md`: absent -> `ln -s ../README.md ...` | exit 1, `Found forbidden symlinks` (+2 digest FAILs), 19/6 | Yes (controller live) |
| 3.2 bodyDigest | `registry/status.json`: true hex char -> flipped hex char | exit 1, FAIL digest mismatch (triad live) | Yes |
| 4.3 no literals | `specs/agents/executive/exec-director/runtime/mcp.json`: `"!cat /..."` -> `"sk-live-123456"` | exit 1, FAIL literal secret (triad live) | Yes |
| 5.1 locked policy | `rigs/executive-and-architecture/rig.yaml`: `permission_policy: builtin:locked` -> `builtin:yolo` (exec-director) | exit 1, FAIL policy (triad live) | Yes |
| 5.2 traversal guard | `specs/agents/executive/exec-director/runtime/policy-enforcement.json`: `"*..*": "deny"` present -> removed from path_write | exit 1, FAIL guard (triad live) | Yes |
| 5.4 extension deny | `specs/agents/security/appsec-engineer/runtime/policy-enforcement.json`: `"code_rewrite": "deny"` -> `"allow"` | exit 1, FAIL extension deny (triad live) | Yes |
| 7.1 loopback ports | `docker-compose.sidecars.yml`: `127.0.0.1:8888:8080` -> `0.0.0.0:8888:8080` | exit 1, FAIL non-loopback (triad live) | Yes |
| 7.2 proxy deny-all | `docker-compose.sidecars.yml`: `POST: "0"` -> `POST: "1"` | exit 1, FAIL proxy toggle (triad live) | Yes |

All 12 sabotages caught (exit 1 + named FAIL line each); the 3 controller-run rows were restored/removed and the worktree re-confirmed pristine (`git status --porcelain | wc -l` → 0) before the fix-verification run. No sabotage survived: no new P0/P1 filed beyond HR-7.2/HR-8.1.

## Regression Ledger

A previous report exists at HEAD (committed as `09270e6 audit_loop`, 486 lines, sentinel `STATUS: FINDINGS_DETECTED`, 31 findings). It audited a superseded pre-generation tree state (no `specs/`/`rigs/` materializations, no working shell). At current HEAD the generated trees exist (`git ls-tree -r HEAD -- specs` → 872 files; `rigs` → 4577 files) and shell works, so its premise is refuted by direct evidence; each prior finding is dispositioned below from that evidence, never copied forward. (An uncommitted 170-line working-tree draft from a shell-blocked attempt is overwritten by this report; its `HR-ENV-shell-blocked` premise does not reproduce here — shell works.)

| Previous finding ID | Previous priority | Status now: FIXED / STILL OPEN / REGRESSED / NO LONGER APPLICABLE | Evidence |
|---|---|---|---|
| HR-1.1-missing-specs-trees | P0 | NO LONGER APPLICABLE | specs/ materialized at HEAD (872 files); 51 role dirs verified live |
| HR-1.2-pregen-partition | P0 | NO LONGER APPLICABLE | partition verified live 6+11+4+6+11+6+7=51 |
| HR-1.3-omni-fragments | P1 | NO LONGER APPLICABLE | 15 pods + 51 members + rig.all-51.yaml present and validated |
| HR-1.4-pregen-files | P0 | NO LONGER APPLICABLE | per-role file sets verified live |
| HR-2.1-missing-rigs | P0 | NO LONGER APPLICABLE | rig spec validate 8/8 live |
| HR-2.2-missing-edges | P0 | NO LONGER APPLICABLE | DAG checks pass live; cycle sabotage caught (this run) |
| HR-2.3-schema-mismatch | P0 | NO LONGER APPLICABLE | agent.yaml subjects validate live |
| HR-2.4-recipe-correct-unproven | P1 | FIXED | guidance_merge guard proven: sabotage (b) caught live this run |
| HR-2.5-missing-bundles | P0 | NO LONGER APPLICABLE | bundle check 8/8 `[]` live; symlink sabotage caught (this run) |
| HR-3.1-empty-registry | P0 | NO LONGER APPLICABLE | schemas + subjects validate live |
| HR-3.2-jcs-proof-gated | P3 | FIXED | bodyDigest recompute verified live (Beta) |
| HR-3.3-vectors-proof-absent | P1 | FIXED | digests match disk live; residual one-commit staleness is hygiene, not a finding |
| HR-4.1-pins-unmaterialized | P0 | NO LONGER APPLICABLE | pins materialized and validated live |
| HR-4.2-bootstrap-residual | P2 | FIXED | render-seat dry-run + 0600 + 7/7 unit tests live (daemon seed still not run — see Not Audited) |
| HR-4.3-secret-probe-gap | P2 | FIXED | refusal + literal-secret sabotage probes executed live (Gamma) |
| HR-4.4-literal-floor-note | P3 | FIXED | verifier floor confirmed live; no literals found |
| HR-5.1-locked-unmaterialized | P2 | NO LONGER APPLICABLE | rig.yaml seats present; locked policies verified live |
| HR-5.2-guards-unproven | P1 | FIXED | 30+ hostile gate-role probes deny live (Gamma) |
| HR-5.3-url-user-present | P3 | FIXED | secret-read denies verified live |
| HR-5.4-extension-unproven | P1 | FIXED | triple-deny verified 51/51 + allow-sabotage caught live |
| HR-5.5-bash-matcher | P2 | FIXED | chaining probes deny live (Gamma) |
| HR-5.5-render-output-allow | P3 | FIXED | fail-closed output handling verified live |
| HR-5.4-gate-coverage | P3 | FIXED | gate corpus probes all three mutating tools live |
| HR-6.1-unbuilt-catalog | P0 | NO LONGER APPLICABLE | 62 skills vendored and lockfile-matched live |
| HR-6.2-pins-liveness | P2 | FIXED | pins + flags verified live; liveness labels honest |
| HR-7.1-compose-unproven | P1 | FIXED | loopback/pin checks + 0.0.0.0 sabotage caught live (runtime 403s still not run — see Not Audited) |
| HR-7.2-proxy-residual | P3 | STILL OPEN (escalated) | Re-filed as HR-7.2-events-version P1: gate now proves 18-toggle set insufficient (demands 20) |
| HR-7.3-network-note | P3 | FIXED | isolation + guard-profiles matrix verified live |
| HR-8.1-not-generated | P1 | STILL OPEN (mutated) | Re-filed as HR-8.1-dirty-worktree P2: generation ran (dirty tree), but HEAD-state idempotence unattributable while dirty |
| HR-8.2-gate-red | P0 | STILL OPEN (narrowed) | Same root cause as HR-7.2: clean-HEAD gate still exits 1, now down to 3 FAILs (was fully red pre-generation) |
| HR-8.3-evaluator-execution | P1 | FIXED | self-test exits 0 PASSED live this run |

## Not Audited / Unverifiable

- OpenRig daemon start / `rig up` / `rig spec preflight` / `rig expand` / `rig agent validate` live launch: not run (state-changing; hard limits allow loopback daemon only and the triad did not run it). A human needs a loopback daemon run (`HOME=$AUDIT_TMP/home OPENRIG_HOME=$AUDIT_TMP/home/.openrig rig daemon start --no-kernel --port 7699`, then preflight/expand/agent-validate across all 8 rigs, `rig down` + `rig daemon stop` after) to close the 4.1/4.2 execution halves.
- Container-runtime proxy 403s + network isolation under traffic: images never pulled; no `docker compose up` ran. A human with docker needs sidecar-profile up/down probes asserting GET-only proxy denials and loopback reachability.
- Full `generate-rigs.py` regen without vendor dir: fails closed (missing `.scratch/vendor`); only `--check-idempotent` ran. A human needs the vendored-inputs pipeline run to prove end-to-end generation.
- `rig bundle check` pod-aware advisories (`not_checked` lines, exit 0): noted but not deep-probed. A human on a daemon host can confirm advisory-only status per rig.

## Final Loop Sentinel

STATUS: FINDINGS_DETECTED
