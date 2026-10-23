# DRAFT — Tasks: issue-12-build-capability (spike, for principal approval — NOT implementation)

> **Status: DRAFT.** Disk-side tasks are executable now; every live task is
> marked **TBD (STAGED)** and belongs to the gated implementation wave after
> principal approval + fleet relaunch. Task IDs: `BC-T*` (static/design),
> `BC-L*` (live, STAGED).

## Static / design tasks (runnable now, no fleet)

- [ ] BC-T1 — REQ-BC1/BC3 static pin: record the corrected 15-role
      build/test matrix from `fleet/fleet.yaml` with the exact grep + parse
      commands (`grep -n "git add"`, `grep -n "git commit"`, per-role
      `bash_allow` dump). Acceptance: matrix reproduces byte-identical from
      the cited commands on the merge commit.
- [ ] BC-T2 — Mock-harness verb probes: render the 4 recon roles with
      `--model-provider mock` and probe the #12 denial set via
      `scripts/gate-run.sh` (`cmake --preset`, `./build.sh --help`,
      `clang++ -fsyntax-only`, `git add`, plus positive controls `ctest`,
      `cmake --build`, `git status`). Acceptance: every probe classified
      ALLOW/DENY with the denial text quoted; surprises (e.g. path-rule
      denials on `./build.sh` for the designated runner) written up as
      findings, not smoothed over.
- [ ] BC-T3 — REQ-BC4 wrapper check: `send-authenticated.sh --dry-run`
      prints the exact 0.6.13 invocation (`--source` + `--summary` always
      passed); fail-closed validation rejections (`--help` cases) exit 2.
      Acceptance: dry-run output + rejection cases recorded.
- [ ] BC-T4 — REQ-BC7 static check: `rig seat launch --help`,
      `rig policy permissions --help`, `rig seat handover --help` show the
      flags cited in `design.md` §4 on CLI 0.6.13. Acceptance: help excerpts
      on file (already captured in this spike).
- [ ] BC-T5 — 12c design alignment: confirm the C1 committer design against
      the A2 envelope owner (no pre-emption) and prefix-matcher reality
      (exact-argv allowlisting sketch). Acceptance: decision record signed
      by principal; BUILD-CLOSEOUT Part-2 refusal stays standing until then.

## Live tasks — TBD (STAGED, gated wave only)

- [x] BC-L1 — **MEASURED 2026-10-23:** 5/5 canary denials live, verbatim
      (0 ALLOWED / 5 DENIED, table in findings report §3; matches the
      2026-10-20 issue record exactly).
- [ ] BC-L2 — **TBD (STAGED):** D1–D4 live build proof from the designated
      runner (build log exit 0, CTest N/N, tree SHA, ELAPSED) attached to #12.
- [ ] BC-L3 — **PARTIAL (dry-run + --help MEASURED 2026-10-23; live
      round-trip STAGED):** wrapper `--dry-run`/`--help` verified; raw
      `rig send` advisories re-observed live on all four probe seats. Live
      authenticated-relay round-trip with seat transcript ACK deferred to
      the gated wave (avoid extra mission-seat traffic).
- [ ] BC-L4 — **PARTIAL (previews MEASURED 2026-10-23; mutation STAGED):**
      `seat launch --fresh --plan` (blocked: requires `--stop`,
      siblings-unchanged preview clean) + `seat handover --dry-run`
      (two-phase plan, no changes) recorded; snapshot `01M5N162P3C5J21KFPCKGHD8XX`
      taken. `--stop` execution awaits TPM sign-off in the gated wave;
      if it refuses, record the block as a headline finding and STOP
      (REQ-BC7).
- [ ] BC-L5 — **TBD (STAGED):** D5–D7 committer path + human merge +
      post-merge re-proof (REQ-BC6, needs the C1 design approved first).

## Canary rollback (applies to every BC-L task)

Before any BC-L step: `rig snapshot heretek-omni-fleet` (record ID);
re-seed from post-merge charters via member-fragment `seed-rig.py`;
restore with `rig restore <snapshotId> --rig <rig-id>` on misbehavior.
Full recipe in `design.md` §6 and the findings report.
