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
