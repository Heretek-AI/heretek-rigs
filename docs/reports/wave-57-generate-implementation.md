# Implementation report — wave-57-generate (issue #57, change issue-57-generate-trackers)

- Stage/wave: `wave-57-generate` · Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-57-generate` · Branch: `feat/57-generate-trackers @ b8ec671`
- Spec read from disk first: `AGENTS.md` (one rule, git conventions, Tracker-proposals discipline row), `openspec/changes/issue-57-generate-trackers/proposal.md`, `design.md` (Q7–Q11 binding), `specs/generate-trackers/spec.md` (REQ-G1..G5), `tasks.md` (G-T1..G-T5). Ground truth `scripts/reconcile.py` + `tests/test_reconcile.py` (28 tests) + `Makefile` line 24 (`generate` = fleet generator) read before any edit.
- Test-first: `tests/test_generate_trackers.py` written first (red: 22 failures + 1 error, script absent), then G-T1 refactor + emitter built to green. No stubs/TODOs/empty-catch/`|| true` in new code; real markdown-table parsing via the shared model (no regex shortcuts).

## Deliverables (G-T1..G-T5)

- G-T1 (REQ-G1+G5): `scripts/reconcile_model.py` (new) — verbatim home of the reconcile row model (`parse_tracker`, `normalize_tracker`, `recorded_note_ids`, `queue_terminal`, `diff_row`, `propose_cell`, `normalize_proposal_note`, `refuse_out_path`, `write_out_exclusive`, plus `load_json_file`, `split_row`, `is_separator`, `check_allowed`, `run_rig`, `render_diff`, constants, `ReconcileError`). `scripts/reconcile.py` is now a thin wrapper importing the model and defining `main` verbatim (module-global `parse_tracker` reference preserved, so the existing monkeypatch test still works). `scripts/generate_trackers.py` (new, executable) — propose-only emitter on the shared model: per-tracker proposals, exact Q8 cell shapes, unchanged-row listing, note-append only on newer transitions, hostile-note normalization in proposals with raw notes in diagnostics. Fresh non-tracker `--out` only (shared `refuse_out_path` + O_EXCL `write_out_exclusive`, exit 2).
- G-T2 (REQ-G1): locked enum display (`STAGED/DISPATCHED/PARKED/QA PASS/PLACED/DONE/CLOSED` via the shared normalizer) + `QUEUE_TO_TRACKER_MAP` table; `OTHER(<raw>)` checked BEFORE `diff_row` so unknown prose is never coerced to a canonical cell — always `other-prose` + `NEEDS-HUMAN-REVIEW` with both-side evidence, no `PROPOSED-CELL` marker, exit 1. Orphan rows (`tracker-row-without-qitem`) and stale-terminal re-verify rows carry `NEEDS-HUMAN-REVIEW` with both-side evidence and no paste marker; the row never vanishes.
- G-T3 (REQ-G2+G4): fail-closed set — missing/unreadable tracker (`UNREADABLE TRACKER`), short-column row (`UNPARSEABLE ROW`), missing/invalid/wrong-shape queue JSON (`UNREADABLE/UNPARSEABLE QUEUE LIST`), EMPTY queue `[]` (`EMPTY QUEUE LIST`, exit 2, never in sync), unreachable rig binary (`UNREACHABLE QUEUE`), non-dict transition items (`malformed input`, exit 2, no traceback), `--out` at input tracker / `*dispatch-tracker.md` / `sprints/` / existing file (`refusing …`, exit 2, bytes untouched). New suite `tests/test_generate_trackers.py` (25 tests). Verify gate V11 appended to `scripts/verify-rigs.sh` (exactly one `ok()`, no existing check renumbered/reworded).
- G-T4 (REQ-G3): convergence replay — all 7 non-review `PROPOSED-CELL` markers applied to a scratch copy re-run through `scripts/reconcile.py` to exit 0 "in sync". `--out` targeting the scratch copy is refused (exit 2), proving the refuse rule covers the replay path.
- G-T5 (wiring+docs): `make generate-tracker TRACKER=… [OUT=…]` (distinct from fleet `make generate`; `.PHONY` + `test` target extended surgically). AGENTS.md Tracker-proposals row already documents `make generate-tracker` + the fresh-out guard — no AGENTS.md edit needed. USER_GUIDE never documented `make reconcile`, so no USER_GUIDE edit (report is the doc).

## Verification outputs (real, inside the worktree unless noted)

- `python3 -m unittest tests/test_generate_trackers.py tests/test_reconcile.py` → `Ran 53 tests … OK` (25 new + 28 reconcile, unmodified, exit 0).
- `make test` → `Ran 123 tests … OK` (exit 0).
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 27 checks passed, 0 failed` (26 baselined + new V11; exit 0).
- Differential proof of no-behavior-change refactor: `git show HEAD:scripts/reconcile.py` vs new wrapper on drifted + converged fixtures → byte-identical stdout, same exit codes (`IDENTICAL_DRIFT`, `IDENTICAL_SYNC`).
- G-T1 gate by hand (`/tmp/opencode/g57`, synthetic live-shape qitems): 7 `PROPOSED-CELL` markers, exit 1, `md5sum -c` tracker+queue inputs OK.
- G-T3 sabotages by hand: empty queue → exit 2 `EMPTY QUEUE LIST`; missing tracker → exit 2 `UNREADABLE TRACKER`; existing `--out` → exit 2 `refusing …` with identical md5 pre/post.
- G-T4 replay by hand: scratch copy converges → `reconcile: in sync — 7 rows …`, exit 0; original tracker still drifts (7 diffs, untouched).
- G-T5 wiring: `make generate-tracker TRACKER=/tmp/opencode/g57/live-tracker.md OUT=…` (real live qitem) → exit 0 in-sync proposal written, tracker untouched. Synthetic-qitem live run correctly fails closed (exit 2 `UNREACHABLE QUEUE`, no file created). `make generate` still the fleet target (its dirty-checkout refusal on this wave's intended dirt is by design, verified message).
- Hygiene: stub scan clean (sole `|| true` is pre-existing Makefile line 13); secret-pattern scan over the wave diff clean; dummy/synthetic qitems in `/tmp` only; `~/.config/heretek-rigs/secrets` never read; no credentials in code/tests/report.
- `git status --short` shows only intended files: `M Makefile`, `M scripts/reconcile.py`, `M scripts/verify-rigs.sh`, `?? scripts/generate_trackers.py`, `?? scripts/reconcile_model.py`, `?? tests/test_generate_trackers.py`, plus this report (`?? docs/reports/wave-57-generate-implementation.md`).

## Decisions / deviations

- Deviation (verified live, contrary to the brief's premise): `rig queue list --json` does NOT return `[]` right now — it returns a populated list (20+ items sampled). The `EMPTY QUEUE LIST` exit-2 rule is still implemented and tested (synthetic `[]` + V11 gate); the risk it guards is real but not the current steady state.
- Fix found via live probing: UNCHANGED lines initially claimed `(queue note <id> recorded)` even when the cell recorded nothing (non-terminal queue rows). Now renders `(queue latest <id>; queue non-terminal, no convergence note required)` unless the id is actually recorded — encoded in `test_unchanged_annotation_distinguishes_recorded_vs_non_terminal`.
- `reconcile.py` keeps unused-import names (`check_allowed`, `normalize_tracker`, etc.) re-exported deliberately: they document the shared-model surface and keep `rec.<name>` patch points stable for the existing suite.

## Unfinished: none. NOT committed — dirty-with-intent for the coordinator, as instructed.
