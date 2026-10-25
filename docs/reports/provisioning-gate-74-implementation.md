# T1 implementation report — provisioning-gate-74

- Stage id: provisioning-gate-74 (Wave C #74 provisioning gate, T1 implement only)
- Branch: feat/provisioning-gate-74
- Worktree: /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/provisioning-gate-74
- Date: 2026-10-25

## Deliverables (REQ-P1/P2/P3/P4/G1)

- REQ-P1 (`scripts/render-seat.py`): `resolve_tool_artifact()` +
  `bash_leading_binary()` helpers (read-only `shutil.which` + path-exists,
  no installs/pulls/network). Every bound stdio MCP command + every
  `bash_allow` leading binary resolves at render time; unresolvable MCP
  entries render `enabled:false` + `warn: <seat>: <server> disabled, missing
  tool artifact: <artifact>` on stderr; unresolvable bash binaries warn
  `warn: <seat>: bash grant '<pattern>' missing tool artifact: <binary>`.
  Never silent. `mcp_allow` permission map unchanged.
- REQ-P2 (`scripts/seed-rig.py`): `stage_time_provisioning_warns()` run in
  the per-seat staging loop with the same warn shape
  (`... missing tool artifact ... at stage time: ...`), degrade-loudly
  (exit codes unchanged; renderer stays authoritative).
- REQ-P3: appended V16 block in `scripts/verify-rigs.sh` (no renumber/
  reword of V1–V15, exactly one new `ok()`); `scripts/live-health.py`
  WARN-first `tool-provisioning` sub-check (`evaluate_tool_provisioning`,
  `live_tool_status`, `PROVISIONING_BASH_BINARIES`; PASS banner carries
  `0 missing tools`; unassessed/unreadable sources SKIP, never healthy;
  dead-daemon path stays all-SKIP).
- REQ-P4: gate covers all 20 command-bearing catalog servers (`github`
  remote-http documented exclusion) + B1–B3 (`r2`/`rabin2`/`tshark`).
  Matrix on disk: `docs/74-PROVISIONING-MATRIX.md` (20-server table with
  pins, required artifacts, bound roles, 2026-10-25 host snapshot + B1–B3
  table + github exclusion + follow-ups).
- REQ-G1: no `install:` recipes, no catalog pin changes (`fleet/` untouched),
  no check renumbered/reworded; `Refs #74` posture (no `Closes` claim
  anywhere in the change).

## Files changed

- `scripts/render-seat.py` (+71)
- `scripts/seed-rig.py` (+92)
- `scripts/live-health.py` (+131)
- `scripts/verify-rigs.sh` (+169, V16 appended before SUMMARY)
- `tests/test_render_seat.py` (+173, `TestProvisioningGate74`)
- `tests/test_live_health.py` (+87, `TestToolProvisioning`)
- `tests/test_seed_rig.py` (new, `TestSeedStageGate74`)
- `docs/74-PROVISIONING-MATRIX.md` (new)

No regeneration via `generate-rigs.py` required: `fleet/` catalogs untouched,
no generated leaves (`specs/`, `rigs/`, `rosters/`, `registry/`) modified.

## Commands run (exit codes)

- RED: `pytest tests/test_render_seat.py::TestProvisioningGate74 tests/test_seed_rig.py tests/test_live_health.py::TestToolProvisioning` → fail (AttributeError, gate absent). exit 1.
- GREEN: same files → pass; then `pytest tests/test_render_seat.py tests/test_seed_rig.py tests/test_live_health.py` → 47 passed, 129 subtests passed. exit 0.
- Acceptance: `make verify` → `SUMMARY: 32 checks passed, 0 failed` (31 baseline + appended V16), live-health dead-daemon run all-SKIP incl. tool-provisioning. exit 0.
- Full suite: `pytest tests/` → 372 passed; 12 failed in `tests/test_build_canary.py::CanaryMockProbes::test_deny_cases_rejected` — verified PRE-EXISTING by stashing my changes and re-running (same 12 fail on clean tree; environment-dependent canary probes, unrelated to this change).
- Syntax: `bash -n scripts/verify-rigs.sh`, `ast.parse` of the verify heredoc + all touched py files → ok.
- Stub scan: grep for TODO/NotImplemented/skips in touched files → clean.

## Self-audit notes

- Anything unfinished: T2 red-proofs (agency-qa) and T3 drift-guard/PR are
  explicitly out of scope for T1; V16 contains in-gate red-proofs both
  directions as the T1 evidence base. Issue #74 stays OPEN (no `Closes`).
- `uvx`/`docker` PRESENT means launcher-binary resolution only; per-package/
  image deep probes recorded as follow-up in the matrix doc (no network in
  verify, per design).
- The 12 pre-existing `test_build_canary.py` failures are stated plainly
  above; acceptance command `make verify` is 100% green.
