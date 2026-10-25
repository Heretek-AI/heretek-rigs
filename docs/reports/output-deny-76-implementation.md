# T1 implementation report — output-deny-76 (issue #76)

Stage: output-deny-76 · T1 implement only (QA + drift-guard follow).
Branch: `feat/output-deny-76` · worktree `.lane/trees/output-deny-76`. All edits inside worktree.

## Deliverables (REQ-O1/O2/O3/O4/G1)

- Tuple narrowed at position 1, order preserved, 38→42:
  `"*--output=*", "*--output *", "*--output\t*", "*--output-junit*", "*--output-log*"`
  replacing `"*--output*"` (`scripts/render-seat.py:81`, source of truth).
- Lockstep: identical mirror (`verify-rigs.sh:588`, V13 auto-green); emitter asserts cover
  all five new literals (`:1153-1162`); V15 frozen assert allowlists exactly the
  --output-only diff (positions 0-4 = five new forms, positions 5+ byte-frozen 37 —
  fails on any other add/remove/reorder/reword); `test_command_effects.py`
  `EXPECTED_38→EXPECTED_42_DENIES` + renamed frozen-order test; `test_render_seat.py`
  corpus to full 42 parity (closes pre-existing 7-entry tab gap) + `:508` literal update;
  `gate-role.sh`: `=` deny probe kept, space/tab deny probes added, `ctest
  --output-on-failure` allow probe conditional on fleet `ctest*` grant (role-arg derived
  `HAS_CTEST`, same pattern as `FIRST`).
- Regen: full `generate-rigs.py` from committed sources (51×2 leaves, 484 files, zero
  DIRTY provenance); charter taxonomy (`generate-rigs.py:699`) regenerated into all
  51 charters.
- Docs: TECHNICAL_DOCUMENTATION counts+lists (15→42), PROMPT_ADVERSARIAL claim 5.5,
  USER_GUIDE probe count (32+→40+) + new probe forms, reaudit #76 row already
  end-state (unchanged).
- Untouched: fleet `bash_allow` dies (`render-seat.py:719`, `verify-rigs.sh:641`),
  commandEffects (#96/#91), no V renumber.

## Acceptance

- `make verify`: exit 0 — `SUMMARY: 35 checks passed, 0 failed` (matches audit baseline).
- `pytest tests/test_render_seat.py tests/test_command_effects.py`: 29 passed, 209 subtests.
- `audit_loop.py --self-test`: PASS.
- TDD red proved first: updated corpora failed against the 38-tuple renderer
  (`KeyError: '*--output=*'`, tuple inequality), then greened.
- Matcher emulation (`*`→`.*`, fullmatch, last-match-wins, documented semantics) on the
  rendered cpp-lowlevel-eng config: ctest `--output-on-failure` → `('ctest*','allow')`;
  `=`/space/tab/junit/log write forms → corresponding narrowed denies; `--output-format`
  hyphen forms match no deny.

## Known non-blockers (for T2)

- Live `gate-role.sh` allow probes fail in this environment with
  `requires approval, but no interactive UI is available` — pre-existing (identical
  3 failures on pristine main checkout for `git status`, `git log --oneline`,
  `write inside src/`); the new ctest allow probe fails the same environmental way.
  Policy-level allow is proved by emulation above; T2 red-proofs in a UI-capable env.
- `make verify` tail prints live-daemon `[SKIP]`s (no daemon here) + `Exited with code 1`
  from that post-gate step; the gate itself exits 0 with 35/0.

## Commits

- `6a6dfa9` feat(output-deny-76): sources+tests+docs (9 files)
- `4589759` feat(output-deny-76): regen 51×2 leaves (484 files)
- (this report commits next)
