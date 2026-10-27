# 107-identity cycle 4 — drift-guard binding verification

Stage/wave: 107-identity cycle 4 final audit. Worktree:
`/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/107-identity`
(branch `feat/107-identity` at `4dc7ed3`, tree clean: `git status --short` empty
at audit). Auditor changed no code and made no commits; this report is the only
new file. Read from disk: `AGENTS.md`,
`openspec/changes/107-identity/{proposal.md,design.md,tasks.md,specs/identity/spec.md}`,
`docs/reports/107-identity-cycle4.md`,
`docs/reports/107-identity-{verification,rework1-verification,rework2-verification,rework3-verification}.md`,
`docs/evidence/107-identity/cycle4-red-proofs.log`.

## 1. Cycle-4 diff is V24 + one corpus test class only (no behavior change)

`git diff --stat c9907fc...HEAD` = 4 files, **268 insertions, 0 deletions**:

- `docs/reports/107-identity-cycle4.md` (79+, new) — cycle report.
- `docs/evidence/107-identity/cycle4-red-proofs.log` (122+, new) — QA red-proofs.
- `scripts/verify-rigs.sh` (+33/-0) — V24 block appended after V23, before SUMMARY.
- `tests/test_identity_m1.py` (+34/-0) — `import re` + `RotationRunbookStep3Tests`.

`git diff c9907fc...HEAD` over `scripts/seed-rig.py scripts/render-seat.py
openspec/ fleet/ specs/ rigs/ rosters/ registry/
docs/evidence/107-identity-rotation.md` is EMPTY: no seed/render/rotation/spec
text touched, so no regen was needed or run. `rotation.md` hash
`e922084db951beae6c94ccfb3dce48d308ca0da2ec0e257d77b1f5ef6a2a73c2`
matches the rework-3 pre-sabotage hash byte-identically (history preserved).

V-headers `V1, V2&V3, V4&V5, V6–V24` all present in order, V1–V23 unrenamed;
removed-lines count in the verify diff = 0; single live
`SUMMARY: {passes} checks passed…` print; SUMMARY frozen at 35. V24 is
FAIL-ONLY (no `ok()`), same convention as V20/V21/V22/V23.

## 2. V24 semantics correct (FAIL-ONLY, non-vacuous floor, step-3 scoped)

V24 (`scripts/verify-rigs.sh:2807-2839`, FAIL-ONLY) slices the §1 step-3 region
between the `3. Mint the replacement` and `4. Redistribute` anchors and asserts
(1) at least one backticked `` `rig mcp token add … --seat … --rig …` `` mint
form exists (zero-mint floor trips), and (2) every backticked mint in step 3
carries `--rig` (any rig-less form trips). Auditor reproduced the extraction
read-only: whole-file backticked `token add` forms = 2 (line-7 `--help` with no
`--rig`, step-3 `--seat --rig` form); step-3-region forms = 1 (the `--rig`
form); both conditions hold GREEN on the clean tree. The §2 live-evidence
section's rig-less `token add` invocations (2 shell-transcript lines) are
non-backticked and outside the anchor slice, so they correctly do not trip the
gate — the same scoping the corpus test (`step3_region`) implements. §2
evidence untouched, as required (history, not rewritten).

## 3. Generator rule holds (specs/rigs/rosters deltas provenance-only + prior content)

- `git diff 51d7df1..HEAD --name-only -- specs/ rigs/ rosters/` → EMPTY.
- `git diff 51d7df1..HEAD -- registry/` → 16 files; every changed line is a
  `resolvedCommit` `892e1a7…→47e71aa…` provenance re-stamp (+ matching
  `canonicalUrl` pins); `grep -c DIRTY` → 0. Compliant (accepted re-lag per
  AGENTS.md). No cycle-4 registry/fleet/catalog change at all.

## 4. No stubs/skips, no committed secrets

Added-lines grep over the cycle-4 code diff for
`TODO|FIXME|XXX|HACK|NotImplementedError|skipTest|pytest.skip|assert True||| true`
→ 0 hits; bare-`except:pass` → 0 hits. No skips, no `ok()` in V24, no
`yaml.load`/`safe_dump` (V24 parses no YAML). 40+-char runs in the added lines
are only file paths, the sha256 hash, a spec path, and the test method name —
zero bearer-shaped literals. The only `ghp_/sk-/Bearer …` hits repo-wide are
the pre-existing secret-detector regexes inside `verify-rigs.sh` itself.

## 5. Red-proof audit (`docs/evidence/107-identity/cycle4-red-proofs.log`)

Recorded by agency-qa at `058ef2c`, verified line-by-line by this auditor:

- Baseline GREEN recorded (make verify exit 0, check-only 35/0 with V23+V24
  green, pytest 26, self-test PASSED).
- Sabotage A (step-3 mint reverted to rig-less, 1-line surgical edit): corpus
  test RED exit 1
  (`AssertionError: runbook step 3 must mint with --seat AND --rig`) AND
  verify RED exit 1 with both V24 fail lines (+ expected V23 collateral via the
  corpus run; SUMMARY count frozen at 35). Non-vacuous — two independent
  committed mechanisms trip. Restore via `git checkout --` → hash
  byte-identical `e922084d…0da`, all gates GREEN.
- Sabotage B (scoping): clean-tree GREEN with rig-less forms present elsewhere
  (§2 transcripts, line-7 `--help`) IS the proof V24 examines only the anchor
  slice — verified in code (`_v24_lines[_v24_start:_v24_end]`). No vacuous check.
- `git status --short` clean after restore (this audit confirms clean at
  `4dc7ed3`, which additionally commits the cycle-4 log itself).

## 6. Prior VERDICTs still stand (no regressions)

M0–M3 deliverables, F1–F5/R1–R3 fixes, N1–N4 benign verdicts, and the S1–S8 /
rework red-proofs are untouched by the cycle-4 diff (0 deletions, no file from
those stages modified). Re-run confirms: V23 green with 26 corpus tests
(floor `>= 15` holds), SUMMARY 35/0.

## 7. Re-run — real output (this audit, unmodified tree)

- `bash scripts/verify-rigs.sh --check-only` → exit 0:
  `V23/107-identity M1 green: … 26 corpus tests pass (FAIL-ONLY, SUMMARY frozen)`,
  `V24/107-identity R1 green: rotation step 3 mandates --rig alongside --seat,
  no rig-less mint (FAIL-ONLY, SUMMARY frozen)`,
  `SUMMARY: 35 checks passed, 0 failed.`
- `python3 -m pytest tests/test_identity_m1.py -q` → `26 passed in 1.88s`,
  exit 0 (expect 26: MET).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, exit 0.
- Failed/skipped commands: none failed; no `[SKIP]` lines in check-only output
  on this run.

## Findings

None. Cycle-4 diff is exactly the disclosed V24 block + one corpus test class
plus report/evidence; no behavior change; V24 is FAIL-ONLY, non-vacuous, and
correctly scoped to step 3; generator rule, stub, secret, and SUMMARY-freeze
invariants all hold; red-proofs are non-vacuous with byte-identical restores;
all prior PASS verdicts stand unregressed.

VERDICT: PASS
