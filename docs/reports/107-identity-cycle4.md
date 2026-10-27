# 107-identity cycle 4 — R1 coverage gap closed (V24 + corpus test)

Stage: 107-identity cycle 4 (fresh wave, re-authorized). Worktree:
`.lane/trees/107-identity` (branch `feat/107-identity`, tree was clean at start).
Prior verdict: PASS at `c9907fc` with a disclosed R1 coverage gap.

## What and why

Rework-3 QA (`docs/evidence/107-identity/rework3-red-proofs.log`, §R1) proved the
rotation runbook fix (step 3 mints with `--rig <managed-rig>`) GREEN but
disclosed a gap: reverting step 3 to the rig-less form tripped NO committed
gate (corpus 25/25 and verify 35/0 stayed green). Only the ad-hoc, uncommitted
`/tmp/107-r1-gate.sh` detector tripped RED. This cycle commits that property as
real coverage, per the report's own recommendation ("a V24/future appended gate
asserting `--rig` in runbook step 3, per the append-only rule").

Scope was minimal and single-purpose: ONE appended FAIL-ONLY verify block (V24)
plus ONE corpus test. No rotation.md edits (the gate anchors on existing fixed
text: `3. Mint the replacement` … `4. Redistribute`); no spec/generator-input
changes, so no regen.

## Gate semantics

- **V24** (`scripts/verify-rigs.sh`, appended after V23, before SUMMARY):
  extracts the §1 step-3 region between the two existing anchors and asserts
  (1) at least one backticked `rig mcp token add … --seat … --rig …` mint form
  is present (non-vacuous floor: zero mint commands trips), and (2) every
  backticked mint command in step 3 carries `--rig` (any rig-less form trips).
  FAIL-ONLY: no `ok()` line, SUMMARY frozen at 35, V1–V23 untouched —
  same convention as V20/V21/V22/V23.
- **Corpus test** (`tests/test_identity_m1.py::RotationRunbookStep3Tests`):
  the same property re-derived independently in the corpus (region extraction +
  `--seat`+`--rig` presence + per-command `--rig` requirement). The pattern was
  re-derived from the disclosed checkable property (step-3 text contains a
  `--rig` mint form; rig-less mint forbidden) — the uncommitted `/tmp` ad-hoc
  gate was never copied. V23's `>= 15` floor is untouched and still holds
  (corpus is now 26 tests).

Scoping note: the runbook's §2 live-evidence section legitimately contains
rig-less `token add` invocations (scratch-isolation probes, Step A/D), so both
the test and V24 assert on the step-3 region only — a whole-file grep would be
vacuous/false-positive by design.

## Red-first record

1. Baseline (clean tree): pytest 25 passed; rotation.md
   `e922084d…0da` (matches the rework-3 pre-sabotage hash).
2. Added the corpus test → 26 passed on fixed text.
3. Sabotage (temporary, never committed): step-3 command reverted to rig-less
   `` `rig mcp token add <name> --seat <session>` `` → new test RED
   (`AssertionError: runbook step 3 must mint with --seat AND --rig`), then V24
   appended → `verify-rigs.sh --check-only` RED with both V24 fail lines
   (plus expected V23 collateral via the corpus run; SUMMARY frozen at 35,
   exit 1). Defect is real and mechanically checkable by committed gates.
4. Restore: `git checkout -- docs/evidence/107-identity-rotation.md` →
   byte-identical `e922084d…0da`; pytest 26 passed.

## Acceptance

- `make verify` → exit 0; `SUMMARY: 35 checks passed, 0 failed`; V23 green
  (26 corpus tests); V24 green
  (`V24/107-identity R1 green: rotation step 3 mandates --rig alongside --seat,
  no rig-less mint (FAIL-ONLY, SUMMARY frozen)`).
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `git status --short` → only `M scripts/verify-rigs.sh` and
  `M tests/test_identity_m1.py` (67 insertions, 0 deletions). No
  `specs/`/`rigs/`/`rosters/`/`registry/` leaves touched, no
  `fleet/fleet.yaml` or `fleet/mcp-servers.yaml` changes — no generator inputs
  changed, so no regen run and no DIRTY stamps (verify's digest gates green
  confirms it).
- Secrets: no bearer-shaped literals anywhere (dummy `fakegrantsessiontoken`
  fixtures only, mode discipline unchanged). `yaml.safe_load` untouched
  (V24 parses no YAML).

## Self-audit notes

- Nothing unfinished: the R1 gap is now covered by two independent committed
  mechanisms (V24 gate + corpus test) with red-first proof for each.
- Not committed, per stage orders — left dirty for coordinator commit.
