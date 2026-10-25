# T3 drift-guard verification — output-deny-76 (issue #76, Wave E)

Stage: `output-deny-76` · T3 audit only. No production code changed by this audit.
Worktree: `.lane/trees/output-deny-76` · branch `feat/output-deny-76` @ `e667ca7`
(T1 `6a6dfa9` + regen `4589759` + T1 report `18f6e82` + T2 evidence `e667ca7`).
Unity binding: N/A. All reads/edits confined to the worktree; nothing committed by the auditor.

Spec read from disk: `openspec/changes/output-deny-76/{proposal.md,design.md,tasks.md,specs/deny-narrowing/spec.md}`.
Prior art read from disk: `docs/reports/output-deny-76-implementation.md` (T1), `docs/evidence/wave-e-output-deny.md` (T2).

## 1. Spec & architecture audit (REQ-O1/O2/O3/O4/G1)

- REQ-O1 (narrowed write-forms, position 1): `scripts/render-seat.py:81-86` holds
  `"*--output=*"`, `"*--output *"`, `"*--output\t*"`, `"*--output-junit*"`,
  `"*--output-log*"` in place of `"*--output*"`. Module import confirms
  `len(TERMINAL_BASH_DENIES)==42`, `first5` exactly the five new forms, old
  `"*--output*"` literal absent. PASS.
- REQ-O2 (junit/log denies, 42 total): confirmed by the same import (42 entries,
  junit/log present at positions 4–5). PASS.
- REQ-O3 (legit flags pass): independent matcher spot-check (`*`→`.*`,
  `re.fullmatch`, last-match-wins, documented semantics) on the rendered
  `cpp-lowlevel-eng` leaf (`specs/agents/languages/cpp-lowlevel-eng/runtime/pi-permission-config.json`):
  `ctest --test-dir build --output-on-failure` → `('ctest*','allow')`;
  all six deny forms → their narrowed denies; `--output-format` matches no
  `--output`-family deny; `--output-junit=x` → junit deny. 8/8 ok. A mock-gate
  `expect allow` probe for the ctest form exists in `scripts/gate-role.sh`
  (conditional on fleet `ctest*` grant via `HAS_CTEST`). PASS.
- REQ-O4 (lockstep):
  - Mirror `verify-rigs.sh:588` carries the identical 42-tuple; V13/S2a
    (`:1737-1750`) asserts ordered-identity source↔mirror and greens in the
    re-run (§3). PASS.
  - Emitter asserts `:1153-1162` cover all five new literals. PASS.
  - V15 frozen assert (`:2016-2025`) allowlists exactly the --output-only diff
    (`got[:5]` == five new forms, `got[5:]` byte-frozen 37). Characterized in
    `/tmp` against the live module (sources untouched): actual 42-tuple passes;
    drop/reorder/reword/add of any non-output entry, reorder of the output head,
    drop of one output entry, and restore of old `"*--output*"` all fail the
    predicate (7/7 fail-closed). PASS.
  - `tests/test_command_effects.py`: `EXPECTED_38_DENIES` →
    `EXPECTED_42_DENIES` + renamed frozen-order test. PASS.
  - `tests/test_render_seat.py`: corpus block (`:178-219`) holds exactly 42
    entries whose set equals the 42-tuple (programmatically verified 42/42),
    including the 7 previously-missing tab variants (closes the pre-existing
    tab gap); `:508`-area literal updated to `"*--output=*"`
    (`assertIsNone(bash_leading_binary("*--output=*"))`). PASS.
  - `scripts/gate-role.sh`: `=` deny probe kept; space/tab deny probes added;
    ctest allow probe added conditional on `HAS_CTEST` (role-arg derived, same
    pattern as `FIRST`). PASS.
  - Regen: 51 specs leaves + 102 rigs leaves all carry the 42-tuple as the bash
    tail in order (0 mismatches); zero `"*--output*"` literals anywhere under
    `rigs/`, `specs/`, `registry/` (the single remaining occurrence is the V15
    comment at `verify-rigs.sh:2017` naming the removed entry — intentional
    documentation, not policy); charter taxonomy regenerated
    (`generate-rigs.py` charter text diff carries the five new forms). PASS.
  - Docs refreshed: `TECHNICAL_DOCUMENTATION.md` (15→42 counts+lists),
    `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` claim 5.5 (42 denies listed),
    `USER_GUIDE.md` probe count (32+→40+) + new probe forms, charter taxonomy
    text; `docs/PROMPT_REMEDIATION_REAUDIT.md:26` #76 row already end-state
    (`ALLOWED; --output=/tmp/x still denied`), correctly untouched
    (no diff). PASS.
  - Non-generated diff surface is exactly: 3 docs + 2 evidence/report files +
    `render-seat.py`, `verify-rigs.sh`, `gate-role.sh`, `generate-rigs.py`
    (charter/formatting only), 2 test files — plus regenerated leaves. No other
    source touched. PASS.
- REQ-G1 (freeze exception scoped): `git diff main...feat/output-deny-76 -- fleet/`
  is empty (0 lines — fleet dies unchanged); no diff touches
  `build_command_effects`/`note-effect`/`body-file-effect` (#96/#91 untouched);
  V15 characterization (§above) proves any non-`--output` add/remove/reorder/
  reword fails. Exactly 1 removed + 5 added at position 1. PASS.
- Residuals recorded: bare trailing `--output` (end-of-string, no end-anchor in
  the matcher dialect) recorded as accepted residual in `design.md:4`; the
  `--output<newline>` sibling residual recorded in `design.md:13`. PASS.

## 2. Stub hunt

Changed sources (`render-seat.py`, `verify-rigs.sh`, `gate-role.sh`,
`generate-rigs.py`, both test files) scanned for `TODO|FIXME|XXX|NotImplemented`,
`|| true`, empty catches, skipped tests: only pre-existing hits (the HR-8.4
placeholder-freedom scanner's own patterns; a pre-existing `|| true` in a grep
pipeline at `gate-role.sh:49`, untouched by this change per the diff). No new
stubs, no vacuous checks (every acceptance check is red-proved non-vacuous in
T2 §4, re-verified green here). PASS.

## 3. Re-run, do not trust (auditor-ran)

- `./scripts/verify-rigs.sh --check-only` → exit 0,
  `SUMMARY: 35 checks passed, 0 failed` (audit baseline). PASS.
- `python3 -m pytest tests/test_render_seat.py tests/test_command_effects.py` →
  exit 0, `29 passed, 209 subtests passed`. PASS.
- Independent 8-case matcher spot-check on the rendered leaf → 8/8 ok (§1 REQ-O3). PASS.
- Live allow-probe environmental failures (`no interactive UI`, `isError:true`)
  stay out-of-scope per stage instructions: T2 §3 records them with the
  pre-existing-on-main cause (T1 verified identical failures on pristine main);
  not re-proved exhaustively. Canary 12 pre-existing, out-of-scope. Noted, not findings.

## 4. Red-proof evidence audit (T2 `docs/evidence/wave-e-output-deny.md`)

- Baseline table (§1) matches auditor-observed re-runs (35/0, 29 passed, 14/14 emulation).
- Sabotage log S1–S5 (§4): each defect (old-substring restore; drop junit/log/`=`/space/tab;
  mirror drop; live-probe indistinguishability caveat) records a non-zero-exit RED
  with a non-vacuous signature (verdict flip allow↔deny, `KeyError`, frozen-order
  FAILED, `V13/S2a` + `33 passed, 4 failed`), a `git checkout` revert, and a clean
  `git status --short` — which the auditor confirms is still clean. §5 raw
  excerpts corroborate. S5's sandbox-indistinguishability caveat is honestly
  recorded with the emulation flip as the load-bearing proof. No vacuous checks. PASS.

## 5. Findings

None. Every binding clause (1 removed + 5 added at position 1, 42 total, identical
mirrors, --output-scoped V15, full-parity corpora, gate-role probes, 42-tuple regen
leaves with zero old literals, docs refresh, unchanged fleet dies, untouched
#96/#91, recorded bare-trailing residual) is evidenced in code and green in re-runs.

Report path: `docs/reports/wave-e-output-deny-verification.md`. Not committed.
`git status --short` (auditor-ran): clean.

VERDICT: PASS
