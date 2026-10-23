# Wave-39 rework-1 — implementation report (drift-guard F1 + F2)

Stage: `wave-39-rework-1` (change `remediate-39-reconcile`, issue #39, rework cycle 1 of max 3).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile`
Branch: `remediate/39-reconcile` (commit on top; no merge, no push).

Binding inputs read from disk first: `docs/reports/wave-39-reconcile-verification.md`
§Findings (F1 + F2), `AGENTS.md`, `openspec/changes/remediate-39-reconcile/specs/tracker-reconcile/spec.md`
REQ-R2, `tasks.md` T6, `design.md`.

## F1 — FIXED + VERIFIED (REQ-R2 --out overwrite gap closed)

- Cause: `scripts/reconcile.py:379-391` refused `--out` only when its resolved
  path equalled one of the input `--tracker` paths; both write sites
  (`:450`, `:461` `Path(args.out).write_text`) were otherwise unguarded.
- Fix (no other behavior changes; read path byte-identical):
  - New `refuse_out_path()` up-front guard refuses fail-closed (exit 2,
    destination bytes untouched): (a) `--out` resolving to any input
    `--tracker`; (b) ANY tracker-shaped destination — `*dispatch-tracker.md`
    filename or anything inside a `sprints/` directory — regardless of the
    input set; (c) ANY existing file at the destination.
  - Both write sites now go through `write_out_exclusive()` (`O_CREAT|O_EXCL`),
    so a file appearing after the up-front check is still refused, never
    clobbered. Fresh non-tracker `--out` paths still write.
  - Module docstring updated to state the broadened refusal.
- Tests (TDD red→green): added 4 tests to `TestProposeNeverEdit` —
  (i) `--out` to a scratch byte-copy of a tracker (different path from input)
  → exit 2, victim bytes identical; (ii) `--out` to a tracker-named path in a
  fresh dir → exit 2, nothing created (plus a `sprints/`-location sub-case);
  (iii) `--out` to an existing non-tracker file → exit 2, bytes untouched;
  (iv) `--out` to a fresh non-tracker path → writes, exit 1. RED gate held:
  the 3 refusal tests failed pre-fix (exit 1 + clobber); post-fix 19/19 green.
  The original exact-match test is untouched and green.
- Auditor's exact repro replayed (scratch only):
  `--tracker /tmp/opencode/hr39rework1/input-tracker.md --out
  /tmp/opencode/hr39rework1/phase0-dispatch-tracker.md` (victim byte-copy of
  live phase-0, md5 `d7678fce…` pre-run, matching the audit) →
  `reconcile: FAILED: refusing to write proposal to tracker-shaped path …`,
  exit 2, victim md5 `d7678fce…` post-run (untouched), live mission file
  md5-identical.
- Replay/proposal output to a FRESH non-tracker path proven working
  (exit 1, proposal written, input tracker untouched).

## F2 — FIXED + VERIFIED (T6 follow-up issue filed)

- Filed via `gh issue create` (exit 0):
  https://github.com/Heretek-AI/heretek-rigs/issues/57 —
  "Follow-up (deferred from #39): generate dispatch trackers from queue
  state (remediate-39-generate sketch)". Body = the design sketch from
  `openspec/changes/remediate-39-reconcile/design.md`
  (generate-tracker-from-queue deferred scope, reconcile-diff as
  prerequisite, TPM-approval requirement) plus suggested acceptance
  (consume the reconcile row model; propose-never-auto-edit; REQ-R3
  convergence check). No pre-existing generate follow-up issue existed
  (`gh issue list` confirmed).
- URL recorded in-package: `openspec/changes/remediate-39-reconcile/tasks.md`
  T6 checked off with the URL + filing note; and in
  `docs/reports/wave-39-reconcile-implementation.md` (§Skipped / deferred
  rewritten: filed, not "left for the TPM"; F1 guard + 19-test count updated).

## Files changed

- `scripts/reconcile.py` (+guard `refuse_out_path` + `write_out_exclusive`,
  `import os`, docstring; write sites exclusive-create).
- `tests/test_reconcile.py` (+4 F1 tests; 15 original untouched).
- `openspec/changes/remediate-39-reconcile/tasks.md` (T6 `[x]` + issue URL).
- `docs/reports/wave-39-reconcile-implementation.md` (F1 guard note, 19-test
  count, F2 filed).
- This report (new).

No forbidden-dir edits (`specs/`, `rigs/`, `rosters/`, `registry/` untouched);
`Makefile` + `scripts/verify-rigs.sh` untouched → V1–V9 byte-identical by
construction (`git status` shows only the 4 files above + this report).
Mission repo NEVER written: pre/post md5 of all 3 mission trackers OK,
`git -C /home/john/Projects/heretek-asset-manager diff --stat` empty.

## Acceptance (exact commands, exit codes)

- `python3 -m unittest tests.test_reconcile -v` → Ran 19 tests, OK (exit 0).
- `make test` → Ran 89 tests, OK (exit 0).
- `make verify` → `SUMMARY: 26 checks passed, 0 failed` (exit 0) + standing
  live-health advisory (WARN heartbeat / SKIP seat-idleness, unchanged);
  V10 line reports 19 tests pass.
- `openspec validate remediate-39-reconcile` → `Change
  'remediate-39-reconcile' is valid` (exit 0).
- Live read-only reconcile (3 mission trackers, `--live`) → exit 1,
  `14 diff(s) across 23 row(s); TPM approval required — no files modified.`
  (identical to the audit baseline — no read-path behavior change).

## Self-audit notes

- Nothing unfinished: F1 closed with guard + 4 tests + auditor-repro proof;
  F2 closed with issue #57 URL recorded in both required places (no
  filing-failure fallback needed — `gh issue create` succeeded).
- No QA dispatch, no merge, no push (per instructions).
- Auditor scratch dirs used: `/tmp/opencode/hr39rework1/` (repro + issue body
  draft); all fixtures synthetic except read-only live verification.
