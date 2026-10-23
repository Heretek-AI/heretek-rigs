# Verification report — wave-57-generate (issue #57, change issue-57-generate-trackers)

- Stage/wave: `wave-57-generate` · Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-57-generate` · Branch: `feat/57-generate-trackers @ 3495e33`
- Spec read from disk first: `AGENTS.md`, `openspec/changes/issue-57-generate-trackers/specs/generate-trackers/spec.md` (REQ-G1..G5), `tasks.md` (G-T1..G-T5), `docs/reports/wave-57-generate-implementation.md`, `docs/evidence/wave-57-generate/red-proofs.log` (212 lines).
- Diff under audit: `git diff main --stat` = 8 files (`Makefile`, `scripts/generate_trackers.py` new, `scripts/reconcile.py`, `scripts/reconcile_model.py` new, `scripts/verify-rigs.sh`, `tests/test_generate_trackers.py` new, plus the implementation report and red-proofs.log). `git status --short` is clean (empty). `git diff main -- specs/ rigs/ rosters/ registry/` is empty — the one rule holds.

## Requirement verdicts

- REQ-G1 (proposal completeness, paste-ready cells, OTHER/orphan markers): PASS. Re-ran by hand on a 1-row drifted fixture: exit 1 with `PROPOSED-CELL:::QA PASS + PLACED canonical (queue note 7: handed_off_to Next; operator note appended)`; suite test `test_drifted_wave1_emits_seven_paste_ready_cells` covers the 7-cell Wave-1 fixture. OTHER prose fixture yields `OTHER(awaiting tea-leaf reading)` + `NEEDS-HUMAN-REVIEW` quoting both sides, exit 1, no `PROPOSED-CELL` guess. Orphan-qitem fixture yields `tracker-row-without-qitem` + `NEEDS-HUMAN-REVIEW` quoting `STAGED awaiting QA` / `(no queue entry)`, exit 1, row never vanishes.
- REQ-G2 (read-only + fresh-out guard, O_EXCL, exit 2): PASS. Re-ran all four refusal shapes by hand: `--out` at input tracker path, `*dispatch-tracker.md`, `sprints/` dir, and existing file — each exits 2 with a `refusing …` diagnostic, destination bytes untouched or never created (md5 pre/post verified; existing file still `PRE`). Run leaves tracker + queue inputs byte-identical (`md5sum -c` OK). Both scripts share `refuse_out_path` + `write_out_exclusive` imported from `reconcile_model` (identity, not a copy); O_EXCL is in the shared writer. Suite `TestReadOnlyAndFreshOut` (5 tests) asserts each refusal plus owner-only mode.
- REQ-G3 (convergence replay): PASS. Applied the single `PROPOSED-CELL` to a scratch patched copy and re-ran `scripts/reconcile.py` → `reconcile: in sync — 1 rows…`, exit 0, original tracker still drifts. Full 7-row replay is proven in red-proofs.log CHECK 4 (`reconcile: in sync — 7 rows…`, exit 0) and suite `test_applying_non_review_cells_converges_reconcile_to_zero_diffs`. `--out` targeting the scratch copy is refused (suite asserts the `refusing` path).
- REQ-G4 (fail-closed, named diagnostics, never silent): PASS. Re-ran: empty queue `[]` → exit 2 `EMPTY QUEUE LIST`, never "in sync"; missing tracker → exit 2 `UNREADABLE TRACKER`; missing/invalid/wrong-shape queue JSON, unreachable rig binary, and non-dict transition items are all covered by `TestFailClosed` (7 tests) asserting exit 2 + named diagnostic + no traceback. No bare `except:`, no `except…pass/continue`, no `|| true` in new code (sole `|| true` is pre-existing Makefile line 13).
- REQ-G5 (shared row model, no parallel semantics): PASS with proof, not assumption. Compared `main:scripts/reconcile.py` against the new tree: all 15 moved functions (`refuse_out_path`, `write_out_exclusive`, `load_json_file`, `split_row`, `is_separator`, `parse_tracker`, `normalize_tracker`, `recorded_note_ids`, `queue_terminal`, `check_allowed`, `run_rig`, `normalize_proposal_note`, `propose_cell`, `diff_row`, `render_diff`) are byte-IDENTICAL, constants identical, and wrapper `main` is IDENTICAL. `scripts/generate_trackers.py` imports all nine shared names from `reconcile_model`, defines zero `def parse_tracker/normalize_tracker/recorded_note_ids/queue_terminal/diff_row`, compiles zero regexes, and its `tracker_enum_arm`/`queue_side_of` delegate to the shared normalizer/terminal detector. Suite `test_generator_imports_shared_model_no_fork` enforces identity (`assertIs` against `sys.modules["reconcile_model"]`) plus `assertNotIn("def …")` — non-vacuous by construction (renaming one import or adding a local `def parse_tracker` fails it). `tests/test_reconcile.py` still 28/28 unmodified.

## Task gates (G-T1..G-T5)

- G-T1: PASS — refactor + emitter gate green (`Ran 53 tests … OK`: 25 new + 28 reconcile).
- G-T2: PASS — OTHER/orphan markers present, both sides quoted, exit codes asserted.
- G-T3: PASS — sabotage matrix green in suite and replayed by hand (empty queue, missing tracker, existing/tracker-shaped/sprints `--out`).
- G-T4: PASS — replay converges (hand replay exit 0; log CHECK 4 exit 0 over 7 rows).
- G-T5: PASS — `make generate-tracker` added as a distinct target (line 94; fleet `make generate` line 24 untouched, `.PHONY` extended only, `test` target extended only). AGENTS.md Tracker-proposals row already documents the target + guard, so no AGENTS.md edit was needed and none was made. `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 27 checks passed, 0 failed` (26 baselined + new V11). Note: the target is `--live`-only (no `--queue-list` passthrough), matching the existing `reconcile` target convention and allowed by the task's "`--queue-list`/`--transitions` or `--live`" wording; synthetic fixtures therefore fail closed via make (exit 2 `UNREACHABLE QUEUE`), which the red-proofs log records honestly.

## Negative checks

- Overwrite/auto-edit paths: none. Every `--out` path funnels through the shared refuse guard + O_EXCL writer; no flag combo mutates a tracker or queue state (no writes to tracker/queue paths exist in either script).
- Verify-baseline tampering: none. `scripts/verify-rigs.sh` diff is a single appended V11 block with exactly one `ok()`; no existing check renumbered or reworded (V9/V10 lines intact).
- Stubs/TODOs/swallowed errors: none (`TODO|FIXME|XXX|HACK|NotImplemented` clean; empty-except scan `NONE` in the log; re-verified no bare `except:`).
- Secrets: none (`ghp_|github_pat|sk-|AKIA|PRIVATE KEY` clean over diff files; dummy/synthetic qitems in `/tmp` only; `~/.config/heretek-rigs/secrets` never read).
- Makefile shadowing: none (`generate` fleet target byte-untouched).
- Red-proofs honesty: the log records a real stumble (CHECK 6 `DRIFT-DIFFERS`/`SYNC-DIFFERS` from resolving the model against the wrong path) followed by the corrected `IDENTICAL_DRIFT`/`IDENTICAL_SYNC` rerun — failure preserved in the log, not scrubbed. Sabotage matrix (5a–5f, sprints, existing-file, orphan/OTHER redo, make guards) shows fail-closed exits with named diagnostics and md5/byte-identity evidence.

## Commands re-run (real output)

- `python3 -m unittest tests/test_generate_trackers.py tests/test_reconcile.py` → `Ran 53 tests … OK`, exit 0.
- `python3 -m unittest tests/test_reconcile.py` → 28 tests OK; `make test` → `Ran 123 tests … OK`.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 27 checks passed, 0 failed`, exit 0.

VERDICT: PASS
