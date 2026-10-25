# Drift-guard verification — Wave C provisioning-gate-74 rework-cycle-2 (stage provisioning-gate-74)

- Stage/wave id: provisioning-gate-74 rework-cycle-2 drift-guard
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/provisioning-gate-74`
  (branch `feat/provisioning-gate-74`, HEAD `71e8bf9` = fix `3615011` + QA evidence `71e8bf9`
  on top of rework-cycle-1 `2ececce`)
--date (UTC): 2026-10-25. Unity binding: N/A.
- Spec read from disk: `openspec/changes/provisioning-gate-74/specs/provisioning-gate/spec.md`
  (REQ-P1/P2/P3/P4/G1). AGENTS.md read from disk (one-rule + git conventions + secrets rules).
- Fix diff audited: `git diff 2ececce..HEAD` (7 files). Full-branch comparison:
  `git diff main...HEAD --name-only` = 14 files, none under `specs/`, `rigs/`,
  `rosters/`, `registry/`.

## 1. Six fixes confined and spec-compliant

Fix commit `3615011` (+ coordinator one-line `design.md` wording, committed under
evidence `71e8bf9`). Cycle-2 diff touches exactly:

1. `scripts/render-seat.py` — `resolve_tool_artifact` now `shutil.which` for
   absolute + slash paths (executability required), whole trimmed command, no
   whitespace split. REQ-P1/P4 compliant; docstring updated to match.
2. `scripts/seed-rig.py` — `_resolve_artifact74`, same shape (whole-path +
   `shutil.which` all branches). REQ-P2 compliant. Staging loop still calls
   `stage_time_provisioning_warns` (def line 84 + call line 205 = count 2);
   still exactly one `print(f"ok …")` (line 229).
3. `scripts/live-health.py` — `live_tool_status` slash-branch now
   `_shutil.which(first)` (was `Path(first).is_file()`); whole trimmed command
   (was `.split()[0]`). All three resolvers agree: only executable artifacts
   resolve. `FixtureClient.fetch_tool_status` keeps the `None` guard
   (default dict + `if status is None` → same SKIP dict, never healthy).
4. `scripts/verify-rigs.sh` V16 — appended entrypoint assert
   (`count("stage_time_provisioning_warns(") < 2` → FAIL, REQ-P2) and
   table-column parse (`_v16_table_servers` set from `|`-row column 2;
   `name in _v16_table_servers`, REQ-P4). Purely additive inside V16.
5. `openspec/changes/provisioning-gate-74/proposal.md` — acceptance path
   `docs/7164-PROVISIONING-MATRIX.md` → `docs/74-PROVISIONING-MATRIX.md`;
   verified on disk (new path exists, old path absent except in QA history text).
6. `openspec/changes/provisioning-gate-74/design.md` — one-line wording to
   `shutil.which for bare names and explicit paths alike — only executable
   artifacts resolve` (matches shipped code).

Fixture fallback `None` guard kept (`live-health.py:224-229`). No-split
whole-path in all three resolvers. V16 still green when gate is intact.

## 2. Negative gates (all hold)

- No renumber: cycle-2 `verify-rigs.sh` diff is additive only (2 hunks inside
  the V16 block); no existing check label/number reworded.
- No install recipes/pins: `grep -rn "install:\|uvx --from\|docker image inspect"
  scripts/` → no matches; `fleet/*.yaml` untouched in cycle-2; V13 pins green.
- Refs posture: `git log main..HEAD` subjects/bodies use `Refs #74` only;
  `grep -rn "Closes #74" scripts/ openspec/changes/provisioning-gate-74/` →
  only historical/never-wording mentions (proposal line 9 declined-PR record,
  line 28 + spec REQ-G1 `never Closes #74`); no live `Closes #74` claim.
- No hand-edits under `specs/ rigs/ rosters/ registry/`: full-branch file list
  contains none of those prefixes (only `docs/`, `openspec/changes/`,
  `scripts/`, `tests/` — the `tests/` entries predate cycle-2).
- Pre-existing warns untouched: `render-seat.py:507-512` (auth-key warn) and
  `:597-602` (missing-secrets warn) present verbatim; cycle-2 diff has no
  hunks there.

## 3. Re-run (auditor-executed, not trusted)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 32 checks passed, 0 failed`
  (incl. `[PASS] Provisioning existence gate (#74) green`), exit 0.
- `python3 -m pytest tests/test_render_seat.py tests/test_seed_rig.py
  tests/test_live_health.py tests/test_policy_verifier.py -q`
  → `81 passed, 129 subtests passed`, exit 0. Matches QA §8a.
- QA red-proofs on disk (`docs/evidence/wave-c-provisioning-gate.md` §8c/8d/8e)
  are non-vacuous by construction: entrypoint-call removal → 31/1 FAIL naming
  REQ-P2; missing-command sabotage → `enabled:false` + stderr naming server +
  seat + artifact; silenced warn → 30/4 FAIL (pytest + V16 string + both
  missing-direction red-proofs). Restore proofs recorded (§8g); tree is green
  after each restore.
- Canary `tests/test_build_canary.py` → `12 failed, 11 passed`, identical to
  the pre-existing main-baseline signature recorded in evidence §2
  (environment/dependency-related, unrelated to this change). Out of scope;
  not failed for.

## 4. Git status

- `git status --short` at audit time: clean (no output). Report file below is
  the only new untracked path at write time and is intentionally left
  uncommitted per instructions (Do NOT commit).
- Report path (new addendum): `docs/reports/wave-c-provisioning-gate-rework2-verification.md`

## 5. Findings

None. No stubs, no vacuous checks, no missing deliverables, no scope drift
beyond the six reviewed findings.

VERDICT: PASS
