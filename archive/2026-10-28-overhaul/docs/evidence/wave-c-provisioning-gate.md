# T2 QA evidence — Wave C provisioning-gate-74 (issue #74, gate-only)

- Stage: `provisioning-gate-74` (T2 red-proofs only; drift-guard follows in T3)
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/provisioning-gate-74`
  (branch `feat/provisioning-gate-74`, T1 commit `493cb98`)
- Date (UTC): 2026-10-25
- Matrix ref: `docs/74-PROVISIONING-MATRIX.md` (20 command-bearing servers +
  B1–B3 `r2`/`rabin2`/`tshark`, `github` remote-http exclusion recorded)
- Spec: `openspec/changes/provisioning-gate-74/` (proposal, design, tasks,
  `specs/provisioning-gate/spec.md` REQ-P1..P4/G1). Unity binding: N/A.

## 1. Baseline acceptance (unmodified tree @ 493cb98)

| Check | Result |
|---|---|
| `make verify` | `SUMMARY: 32 checks passed, 0 failed`, exit 0 (31 baseline + appended V16) |
| `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 32 checks passed, 0 failed`, exit 0, incl. `[PASS] Provisioning existence gate (#74) green` |
| `pytest tests/test_policy_verifier.py tests/test_render_seat.py` (acceptance command) | 52 passed, exit 0 |
| `pytest tests/test_seed_rig.py tests/test_live_health.py` (T1 gate corpus) | 29 passed, exit 0 |
| Full gate set `test_policy_verifier + test_render_seat + test_seed_rig + test_live_health` (post-restore) | 81 passed, exit 0 |

## 2. Canary pre-existing note

`pytest tests/test_build_canary.py` on the T1 tree: **12 failed, 11 passed**
(exit 1). Independently confirmed pre-existing: same file run on a clean
main-checkout temp worktree (`git worktree add /tmp/opencode/main-clean
f2f97f6`, merge-base before this branch) gives the identical
**12 failed, 11 passed**. Failure shape is environment/dependency-related,
unrelated to this change: `CanaryMockProbes::test_deny_cases_rejected`
expects `Denied by policy` but the installed pi-permission-system mock
returns `requires approval, but no interactive UI is available`
(e.g. `chaining with semicolon`, `chaining with pipe`, build/compiler/
staging-entry labels — 12 SUBFAILED lines in both runs). Temp worktree
removed afterwards (`git worktree remove --force`); `git stash` was a
no-op because T1 is committed, so the merge-base worktree served as the
clean-main comparison. T1 implementation report states the same 12.

## 3. Red-proof sabotage, direction (a): missing tool → loud degradation

- Defect: `fleet/mcp-servers.yaml`, semgrep block,
  `command: uvx` → `command: /nonexistent-qa74-sabotage` (1 line, then
  `git checkout -- fleet/mcp-servers.yaml` to restore).
- Render layer (REQ-P1), real host env
  (`HERETEK_SECRETS=~/.config/heretek-rigs/secrets … --role
  appsec-engineer --rig defensive-sec-and-red-team --pod blue --dry-run
  --allow-missing-secrets`):
  - Baseline before: semgrep entry has NO `enabled` key, zero semgrep
    stderr lines (uvx resolves on this host).
  - Under sabotage: exit 0 degraded, semgrep entry carries
    `"enabled": false`, stderr carries exactly
    `warn: blue-appsec-engineer@defensive-sec-and-red-team: semgrep disabled, missing tool artifact: /nonexistent-qa74-sabotage`.
- Seed layer (REQ-P2): `stage_time_provisioning_warns(...)` against the
  sabotaged catalog returns
  `warn: blue-appsec-engineer@defensive-sec-and-red-team: semgrep missing tool artifact at stage time: /nonexistent-qa74-sabotage`
  (asserted non-empty, names server + artifact + `at stage time`).
- Restore: `git checkout -- fleet/mcp-servers.yaml`; `git status --short`
  clean; re-render back at baseline (no `enabled` key, 0 semgrep warns).

## 4. Red-proof sabotage, direction (b): silenced warn → verify must RED

- Defect: `scripts/render-seat.py`, replaced the REQ-P1 warn block
  (`entry["enabled"] = False` + `print(f"warn: … disabled, missing tool
  artifact: …")`) with `pass  # QA74-SABOTAGE: warn silenced`
  (then `git checkout -- scripts/render-seat.py` to restore).
- `./scripts/verify-rigs.sh --check-only` under sabotage: **exit 1**,
  `SUMMARY: 30 checks passed, 4 failed`, with
  `[FAIL] V16/#74: scripts/render-seat.py must contain 'disabled, missing tool artifact' (REQ-P1)`,
  `[FAIL] V16/#74 red-proof (missing): stderr must name semgrep + missing tool artifact uvx`,
  `[FAIL] V16/#74 red-proof (missing): stderr must name r2mcp as the missing tool artifact`,
  `[FAIL] tests/test_render_seat.py failed: … TestProvisioningGate74.test_missing_mcp_binary_disables_loudly`.
  (Bash-grant B1–B3 checks stayed green — separate warn path, sabotage was precise.)
- `pytest tests/test_render_seat.py` under sabotage: **exit 1**,
  `1 failed, 17 passed`
  (`TestProvisioningGate74::test_missing_mcp_binary_disables_loudly` fails).
- Restore: `git checkout -- scripts/render-seat.py`; verify back to
  `SUMMARY: 32 checks passed, 0 failed` exit 0; `git status --short` clean.

## 5. Vacuous-check verdict

No vacuous checks. Every acceptance check turned RED under targeted
sabotage: V16 string gate + both missing-direction behavioral red-proofs +
the pytest corpus missing-binary test all fail when the warn is silenced,
and both render and seed layers observably degrade (enabled:false + named
warn) when a bound command points at a nonexistent path.

## 6. Restore proofs

- After (a): `git checkout -- fleet/mcp-servers.yaml` → `git status
  --short` empty; baseline re-render confirmed.
- After (b): `git checkout -- scripts/render-seat.py` → `git status
  --short` empty; `verify-rigs.sh --check-only` 32/0 exit 0.
- Pre-evidence-commit `git status --short` showed nothing modified except
  this untracked evidence file. No production or test files changed by QA.

Refs #74 (never Closes #74; issue stays OPEN per spec REQ-G1).

## 7. Rework-cycle-1 QA re-verification (fix commit 941ff77, CodeQL py/clear-text-logging-sensitive-data)

- Fix under test: `941ff77 fix(provisioning-gate-74): warn raw catalog command
  token, not substituted path` (on top of T3 `ac44602`). One file changed:
  `scripts/render-seat.py` (+6/-1). The REQ-P1 MCP warn now logs the raw
  catalog command leading token (`_raw74`, e.g. `@TOOLS@/bin/r2mcp`) instead
  of the substituted absolute artifact (`_art74`) derived from secrets/tools
  dirs. No prod/test logic change beyond the logged token.
- Date (UTC): 2026-10-25. Worktree:
  `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/provisioning-gate-74`
  (branch `feat/provisioning-gate-74` @ `941ff77`). Unity binding: N/A.

### 7a. Baseline acceptance (unmodified tree @ 941ff77)

| Check | Result |
|---|---|
| `make verify` | `SUMMARY: 32 checks passed, 0 failed`, exit 0 |
| `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 32 checks passed, 0 failed`, exit 0, incl. `[PASS] Provisioning existence gate (#74) green` |
| `pytest tests/test_render_seat.py tests/test_seed_rig.py tests/test_live_health.py tests/test_policy_verifier.py` (acceptance command) | 81 passed, exit 0 (10.29s; 10.14s post-restore rerun) |

### 7b. Fix-property verification (no host-path / no secret content in warn)

- Render with empty tools dir (dummy 0600 secrets + bare tools fixture under
  `/tmp/opencode/qa74-*`, `PATH=/tmp/opencode/qa74-emptybin`):
  `render-seat.py --role binary-reverse-eng --rig defensive-sec-and-red-team
  --pod red --dry-run --allow-missing-secrets` → exit 0, radare2 entry
  `"enabled": false`, stderr carries exactly
  `warn: red-binary-reverse-eng@defensive-sec-and-red-team: radare2 disabled, missing tool artifact: @TOOLS@/bin/r2mcp`.
- Warn names server (`radare2`) + seat
  (`red-binary-reverse-eng@defensive-sec-and-red-team`) + artifact in catalog
  form (`@TOOLS@/bin/r2mcp`) per REQ-P1 — still loud, never silent.
- Leak scan of full stderr: zero matches for the tmpdir path
  (`/tmp/opencode/qa74`), zero for the secrets dirname, zero for the dummy
  secret content, zero host-absolute paths (`/tmp/|/home/|*.config|secrets`
  pattern). The only slash-bearing stderr line is the `@TOOLS@` catalog-form
  token itself. Bash-grant warns carry bare binary names only
  (`r2`, `rabin2`, `tshark`, `rig`). No secret CONTENTS in any warn
  (paths/names only, matching the repo `!cat`-reference convention).

### 7c. Red-proof sabotage, direction (a): missing command → loud degradation

- Defect: `fleet/mcp-servers.yaml`, semgrep block,
  `command: uvx` → `command: /nonexistent-qa74-rework1-sabotage` (1 line,
  then `git checkout -- fleet/mcp-servers.yaml` to restore).
- Under sabotage, appsec-engineer/blue render: exit 0 degraded, semgrep
  entry `"enabled": false`, stderr carries
  `warn: blue-appsec-engineer@defensive-sec-and-red-team: semgrep disabled, missing tool artifact: /nonexistent-qa74-rework1-sabotage`
  (raw catalog token, names server + seat + artifact).
- Restore: `git checkout -- fleet/mcp-servers.yaml`; `git status --short`
  empty.

### 7d. Red-proof sabotage, direction (b): silenced warn → verify must RED

- Defect: `scripts/render-seat.py`, replaced the REQ-P1 warn `print(...)`
  block with `pass  # QA74-REWORK1-SABOTAGE: warn silenced`
  (then `git checkout -- scripts/render-seat.py` to restore).
- `./scripts/verify-rigs.sh --check-only` under sabotage: **exit 1**,
  `SUMMARY: 30 checks passed, 4 failed`, with
  `[FAIL] V16/#74: scripts/render-seat.py must contain 'disabled, missing tool artifact' (REQ-P1)`,
  `[FAIL] V16/#74 red-proof (missing): stderr must name semgrep + missing tool artifact uvx`,
  `[FAIL] V16/#74 red-proof (missing): stderr must name r2mcp as the missing tool artifact`,
  `[FAIL] tests/test_render_seat.py failed: … TestProvisioningGate74.test_missing_mcp_binary_disables_loudly`.
- Restore: `git checkout -- scripts/render-seat.py`; verify back to
  `SUMMARY: 32 checks passed, 0 failed` exit 0; full pytest corpus back to
  81 passed exit 0; `git status --short` clean.

### 7e. Vacuous-check verdict (rework-cycle-1)

No vacuous checks. The V16 string gate, both behavioral red-proofs, and the
pytest missing-binary test all turn RED when the warn is silenced, and both
the `@TOOLS@`-form (radare2) and bare-name (semgrep/uvx) layers observably
degrade (`enabled:false` + named warn) when the bound command is
unresolvable — with the warn now provably free of host-absolute
secrets/tools paths.

### 7f. Restore proofs

- After (a): `git checkout -- fleet/mcp-servers.yaml` → `git status
  --short` empty.
- After (b): `git checkout -- scripts/render-seat.py` → `git status
  --short` empty; `verify-rigs.sh --check-only` 32/0 exit 0; pytest 81
  passed exit 0.
- Pre-evidence-commit `git status --short` showed nothing modified except
  this evidence file. No production or test files changed by QA.

Refs #74 (never Closes #74; issue stays OPEN per spec REQ-G1).

## 8. Rework-cycle-2 QA re-verification (fix commit 3615011, six review findings)

- Fix under test: `3615011 fix(provisioning-gate-74): rework-cycle-2 review
  findings (executable resolution, fixture fallback, table-column V16)`
  (on top of rework-cycle-1 `2ececce`). Five files changed:
  `openspec/changes/provisioning-gate-74/proposal.md` (+1/-1, matrix path
  `7164` → `74`), `scripts/live-health.py` (fixture default + which-for-all),
  `scripts/render-seat.py` (which-for-all + no-whitespace-split),
  `scripts/seed-rig.py` (same), `scripts/verify-rigs.sh` (V16 entrypoint
  call assert + table-column parse). Plus the coordinator's uncommitted
  one-line `design.md` path-exists → which-for-all wording edit, verified
  below and committed with this evidence.
- Date (UTC): 2026-10-25. Worktree:
  `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/provisioning-gate-74`
  (branch `feat/provisioning-gate-74` @ `3615011` + the design.md one-liner).
  Unity binding: N/A.

### 8a. Baseline acceptance (unmodified tree @ 3615011 + design.md one-liner)

| Check | Result |
|---|---|
| `make verify` | `SUMMARY: 32 checks passed, 0 failed`, exit 0 |
| `./scripts/verify-rigs.sh --check-only` | `SUMMARY: 32 checks passed, 0 failed`, exit 0, incl. `[PASS] Provisioning existence gate (#74) green` |
| `pytest tests/test_render_seat.py tests/test_seed_rig.py tests/test_live_health.py tests/test_policy_verifier.py` (acceptance command) | 81 passed, exit 0 (10.04s; 10.08s post-restore rerun) |

### 8b. Per-finding behavioral verification

1. **Executable resolution, render-seat** (`resolve_tool_artifact` now
   `shutil.which` for absolute + slash paths, whole trimmed command, no
   whitespace split): non-executable scratch file (`0644`,
   `/tmp/qa74-exec-*/nonexec-qa74-tool`) → `(False, <path>)`; after
   `chmod 755` → `(True, <path>)`. Non-executable explicit paths no longer
   resolve.
2. **Executable resolution, seed-rig** (`_resolve_artifact74`, same shape):
   same scratch file → `(False, <path>)` at `0644`, `(True, <path>)` at
   `0755`. Matches render-seat.
3. **Executable resolution, live-health** (`live_tool_status` slash-branch
   now `_shutil.which(first)`): `shutil.which(<0644 path>)` → `None`
   (resolves False). All three resolvers agree: only executable artifacts
   resolve.
4. **Fixture fallback, absent file** (`FixtureClient.fetch_tool_status`
   default `{"missing": [], "total": 0}`): empty scratch fixture dir →
   returns `{"missing": [], "total": 0}`, no `DataSourceError`;
   `evaluate_tool_provisioning` → `SKIP` (`no tool artifacts assessed
   (never healthy)`). Missing fixture degrades to SKIP, never healthy.
5. **Fixture fallback, JSON null** (`status is None` guard): fixture file
   containing `null` → `json.loads` yields `None` → same
   `{"missing": [], "total": 0}` dict, no `DataSourceError`, same SKIP
   evaluation. Both fallback directions behave identically.
6. **V16 table-column parse (REQ-P4)** + **proposal path** + **design
   wording**: catalog carries 20 command-bearing servers; full matrix table
   server column covers all 20. Scratch-copy proof: deleted every `|`
   table row naming `codebase-memory`, appended a prose-only mention —
   old substring logic (`name in text`) still PASSES (vacuous), new
   column-set logic (`name in _v16_table_servers`) FAILS correctly
   (`V16/#74: matrix doc table server column must name ...`). Proposal
   acceptance line now reads `docs/74-PROVISIONING-MATRIX.md` (verified on
   disk; `docs/7164-PROVISIONING-MATRIX.md` absent — the old path is gone).
   Design wording now reads `shutil.which for bare names and explicit paths
   alike — only executable artifacts resolve` (matches the shipped code).

### 8c. V16 entrypoint sabotage (staging-loop call removed → RED)

- Defect: `scripts/seed-rig.py`, replaced the staging-loop call block
  (`for _w74 in stage_time_provisioning_warns(...)`) with
  `for _w74 in []:  # QA74-SABOTAGE` (definition kept; count
  `stage_time_provisioning_warns(` 2 → 1). Then
  `git checkout -- scripts/seed-rig.py` to restore.
- `./scripts/verify-rigs.sh --check-only` under sabotage:
  `SUMMARY: 31 checks passed, 1 failed` with
  `[FAIL] V16/#74: scripts/seed-rig.py must CALL
  stage_time_provisioning_warns in the staging loop, not just define it
  (REQ-P2)`. A defined-but-never-called gate is now caught.
- Restore: `git checkout -- scripts/seed-rig.py`; count back to 2; verify
  back to `SUMMARY: 32 checks passed, 0 failed`.

### 8d. Red-proof sabotage, direction (a): missing command → loud degradation

- Defect: `fleet/mcp-servers.yaml`, semgrep block,
  `command: uvx` → `command: /nonexistent-qa74-rework2-sabotage` (1 line,
  then `git checkout -- fleet/mcp-servers.yaml` to restore).
- Under sabotage, tool-poor render harness (dummy 0600 `opencode-go.key`,
  pi-permission-system `41.0.0` stub, `HERETEK_TOOLS=<tmp>/tools`,
  absolute-path `python3` with `PATH=<tmp>/emptybin`):
  `render-seat.py --role appsec-engineer --rig defensive-sec-and-red-team
  --pod blue --dry-run --allow-missing-secrets` → exit 0 degraded, semgrep
  entry `"enabled": false`, stderr carries
  `warn: blue-appsec-engineer@defensive-sec-and-red-team: semgrep disabled, missing tool artifact: /nonexistent-qa74-rework2-sabotage`
  (names server + seat + artifact; bash-grant line also fires).
- Restore: `git checkout -- fleet/mcp-servers.yaml`; `git status --short`
  shows only the design.md one-liner again.

### 8e. Red-proof sabotage, direction (b): silenced warn → verify must RED

- Defect: `scripts/render-seat.py`, replaced the REQ-P1 warn `print(...)`
  block with `pass  # QA74-REWORK2-SABOTAGE: warn silenced`
  (then `git checkout -- scripts/render-seat.py` to restore).
- `./scripts/verify-rigs.sh --check-only` under sabotage: **exit 1**,
  `SUMMARY: 30 checks passed, 4 failed`, with
  `[FAIL] tests/test_render_seat.py failed: … test_missing_mcp_binary_disables_loudly`,
  `[FAIL] V16/#74: scripts/render-seat.py must contain 'disabled, missing tool artifact' (REQ-P1)`,
  `[FAIL] V16/#74 red-proof (missing): stderr must name semgrep + missing tool artifact uvx`,
  `[FAIL] V16/#74 red-proof (missing): stderr must name r2mcp as the missing tool artifact`.
- Restore: `git checkout -- scripts/render-seat.py`; verify back to
  `SUMMARY: 32 checks passed, 0 failed` exit 0; pytest corpus back to
  81 passed exit 0; `git status --short` shows only `design.md` + this
  evidence file.

### 8f. Vacuous-check verdict (rework-cycle-2)

No vacuous checks. The V16 entrypoint assert REDs when the staging-loop
call is removed; the V16 column parse FAILS when a server leaves the table
even if its name survives in prose (the old substring check stayed green —
precisely the vacuity the fix closes); the V16 string gate + both
missing-direction behavioral red-proofs + the pytest missing-binary test
all RED when the warn is silenced; and all three resolvers observably
reject non-executable explicit paths while both fixture fallbacks yield the
same SKIP dict without `DataSourceError`.

### 8g. Restore proofs

- After table test: scratch-copy only — repo matrix file never touched.
- After entrypoint sabotage: `git checkout -- scripts/seed-rig.py`.
- After (a): `git checkout -- fleet/mcp-servers.yaml`.
- After (b): `git checkout -- scripts/render-seat.py` + full green rerun
  (verify 32/0, pytest 81 passed).
- Pre-evidence-commit `git status --short` showed exactly
  `M openspec/changes/provisioning-gate-74/design.md` (coordinator one-liner)
  + `M docs/evidence/wave-c-provisioning-gate.md` (this file). No production
  or test files changed by QA.

Refs #74 (never Closes #74; issue stays OPEN per spec REQ-G1).
