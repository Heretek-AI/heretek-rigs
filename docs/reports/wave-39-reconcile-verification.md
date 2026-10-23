# Verification report — wave-39-reconcile (issue #39, change remediate-39-reconcile)

- Stage/wave: `wave-39-reconcile` · Worktree: `/home/john/Projects/heretik-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile`
- Commits under audit: `38262a0` (implementation) + `2a1c6a2` (evidence/QA report on top). `git status --short` clean at audit time.
- Spec read: `AGENTS.md`, `openspec/changes/remediate-39-reconcile/proposal.md`, `specs/tracker-reconcile/spec.md` (REQ-R1..R4), `design.md`, `tasks.md` (T1–T6); implementer's `docs/reports/wave-39-reconcile-implementation.md`; QA `docs/reports/qa-wave-39-reconcile.md` + `docs/evidence/wave-39-reconcile/red-proofs.log`; `gh issue view 39` (OPEN) and `gh issue list` (no generate follow-up exists).
- Auditor touched no worktree sources and no mission files: all sabotage/write probes ran against `/tmp/opencode/hr39audit/` copies. Mission md5s verified identical before/after every live read.

## What was independently re-run (all green unless noted)

- `make verify` → `SUMMARY: 26 checks passed, 0 failed`, exit 0, plus the standing live-health advisory block (heartbeat WARN / seat-idleness SKIP, unchanged behavior). V10 `[PASS] Tracker-vs-queue reconcile (issue #39) green` present.
- `make test` → `Ran 85 tests ... OK` (incl. 15 new `test_reconcile.py`).
- `openspec validate remediate-39-reconcile` → `Change 'remediate-39-reconcile' is valid`, exit 0.
- Live read-only run (daemon port 7433 up): 3 mission trackers vs live queue → exit 1, `14 diff(s) across 23 row(s); TPM approval required — no files modified.` Mission md5s OK before/after. Replicates QA §11 exactly.
- Diff audit `git diff 184f1a5..HEAD --stat`: 7 files (`Makefile`, `scripts/reconcile.py` new, `tests/test_reconcile.py` new, `scripts/verify-rigs.sh`, 3 report/evidence files). No hand-edit under `specs/ rigs/ rosters/ registry/`. `scripts/verify-rigs.sh` numstat 68+/0− (pure append, zero removed lines; exactly one code-level `ok()` in the V10 block, 4 `fail()` gates). `Makefile` delta is 2 modified lines (`.PHONY` + `test` list gains, additive) plus a new `reconcile` target with no `-`/`|| true` masking. `Makefile`/`verify-rigs.sh` surface: PASS.
- Secrets scan over the full diff (`ghp_`/private-key/`AKIA`/ Crab patterns): 0 matches.
- Sabotage replication on a `/tmp` copy (worktree untouched): neutering the parked branch (`if norm["parked"]:` → `if False and ...`) makes exactly `test_parked_satisfied_but_tracker_silent_flagged` fail (W1-04 falls through to `stale-state`); restoring pristine returns 15/15 OK. The parked-rule test is load-bearing in both directions, as QA logged.
- Live tracker-shape grounding: mission `wave1-dispatch-tracker.md` has the 5-column Slices table (`Slice | Owner seat | Output | Slice qitem | Status`), `qitem-YYYYMMDDHHMMSS-hex` ids matching `QITEM_RE`, and QA PASS/PLACED/DONE prose with note ids — the shapes the parser/normalizer implement. Fixtures are faithful.

## Findings (binding)

- **F1 (FAIL — REQ-R2 violated: the no-overwrite guard is exact-match-only, and a real tracker file was clobbered through the gap).** `scripts/reconcile.py:379-391` refuses `--out` only when its resolved path equals one of the *input* `--tracker` paths; the only write sites (`:450`, `:461` `Path(args.out).write_text`) are otherwise unguarded. Spec clause: spec.md REQ-R2, "The command MUST be read-only: it MUST NOT modify any tracker file or any queue state" (no location qualifier), and the module docstring's own promise that `--out` refusals keep "proposals OUTSIDE the mission repo for TPM review". Demonstrated overwrite (all scratch, worktree/mission untouched): with `--tracker /tmp/opencode/hr39audit/input-tracker.md` and `--out /tmp/opencode/hr39audit/phase0-dispatch-tracker.md` — a byte-identical copy of the live mission phase-0 tracker (md5 `d7678fce…` pre-run, matching the mission file) — the command exited 1 and replaced the victim file with the proposal report (md5 `5f918f99…` post-run). A first probe with a `victim-dispatch-tracker.md` filename confirmed tracker-shaped destinations are not special-cased at all. Realistic trigger: `--tracker <scratch copy> --out <live tracker>` (resolved paths differ, guard passes) or `make reconcile TRACKER=... OUT=<a tracker>`. The shipped test `test_out_refusing_tracker_path` covers only the exact-match case, so the hole is untested. This is the stage's headline invariant (reconcile-diffs-for-approval ONLY, no auto-overwrite) with a demonstrated auto-overwrite path: FAIL.
- **F2 (FAIL — T6 half-delivered: the deferred-generate follow-up issue was not filed).** `tasks.md` T6 (the contract): "…and file the deferred `remediate-39-generate` follow-up design sketch as an issue, not code." Conjunction of two deliverables; only the report was written. `gh issue list` confirms no `remediate-39-generate` issue exists; the implementation report (§Skipped / deferred) and QA F1 both record the non-filing. The stated rationale (issue filing is a "network/state-changing act outside the implementation scope") contradicts the task text, which places the filing *inside* scope ("as an issue, not code"), and none of the cited lane prohibitions (no QA dispatch, no merge, no push) covers `gh issue create` — the `gh` CLI was available and used for reads throughout. The design sketch survives in `design.md`, so recovery is one TPM command, but as a contract item T6 is unsatisfied: FAIL (missing deliverable).

## Observations (non-blocking, not findings)

- O1: Worktree `AGENTS.md:15,45` still says "23 checks" while `make verify` reports 26 (25 baselined + V10). The staleness predates this wave (base `verify-rigs.sh` already carried V1–V9 with more than 23 passes); not wave-39's scope, no action here.
- O2: Concur with QA F2 — `openspec validate` is lenient at the margins (heading/task/scenario presence). Load-bearing at the delta level (verified by the spec's own content, which I re-validated green). No action for this stage.

## Ruling notes (reasoned from tasks.md, not from QA)

- (a) Full generation deferred — spec-sanctioned. `proposal.md` §Non-goals explicitly defers option (a) to its own change package and `design.md` records why diff-first; no scope creep occurred (diff touched only the sanctioned files). PASS aspect, no finding.
- (b) T6 follow-up issue — contract text explicitly requires filing it, and the seat demonstrably could (`gh` present, no applicable prohibition). An advisory cannot substitute for a tasked deliverable under the missing-deliverable rule. Hence F2.

## Paths

- Implementation: `scripts/reconcile.py`, `tests/test_reconcile.py`, `Makefile`, `scripts/verify-rigs.sh` (V10 only), `docs/reports/wave-39-reconcile-implementation.md`.
- QA: `docs/evidence/wave-39-reconcile/red-proofs.log`, `docs/reports/qa-wave-39-reconcile.md`.
- Audit scratch (outside both repos): `/tmp/opencode/hr39audit/` (sabotage copies, cross-tracker victim + md5s, live-run output `/tmp/opencode/hr39audit-live.txt`).
- No commit/merge/push performed by this audit. Mission repo saw reads only (md5-verified).

> VERDICT: FAIL (prior audit 38262a0+2a1c6a2 — superseded; preserved as history)

## Re-audit — wave-39-rework-1-reaudit (2026-10-23, rework cd262e6 + evidence 6f916cf) — drift-guard re-audit

- Stage/wave: `wave-39-rework-1-reaudit` · Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile`
- Commits under audit: `cd262e6` (rework) + `6f916cf` (evidence on top). `git log --oneline -5` confirms; `git status --short` clean at audit time.
- Spec read from disk first: this report (prior FAIL F1/F2 above), `openspec/changes/remediate-39-reconcile/tasks.md` (T6 now `[x]` with issue URL), `openspec/changes/remediate-39-reconcile/specs/`, `docs/reports/qa-wave-39-reconcile.md` (§Rework-1 re-verification), `docs/reports/wave-39-rework-1-implementation.md`, `docs/evidence/wave-39-reconcile/red-proofs.log` (§16), `AGENTS.md`.
- Auditor touched no worktree sources and no mission files: all write probes ran against `/tmp/opencode/hr39reaudit/` copies. No commit/merge/push.

### F1 — CLEARED (REQ-R2 overwrite gap closed; guard complete at both write sites)

- Guard read: `scripts/reconcile.py:95-134` `refuse_out_path()` refuses fail-closed (exit 2, bytes untouched): (a) `--out` resolving to any input `--tracker` (`:108-118`); (b) tracker-shaped by NAME (`:119-123` `*dispatch-tracker.md`) AND by LOCATION (`:124-128` any `sprints/` path part), regardless of the input set; (c) ANY existing file (`:129-134` `os.path.lexists` or resolved exists). Up-front call at `:450` before any parsing; BOTH write sites (`:507-508` diffs branch, `:515-516` in-sync branch) go through `write_out_exclusive()` (`:137-157`, `os.O_CREAT|O_EXCL`), so a file appearing after the up-front check is still refused, never clobbered. No `write_text` remains on the `--out` path (grep confirms only `os.open` at `:144`). TOCTOU-meaningful gap for this threat model: none — the O_EXCL create is the write-time re-check.
- Independent repro of the auditor's exact attack (scratch only): `--tracker /tmp/opencode/hr39reaudit/input-tracker.md --out /tmp/opencode/hr39reaudit/phase0-dispatch-tracker.md` (victim byte-copy of live mission phase-0, md5 `d7678fce…` pre-run matching the mission file) → exit 2 `refusing to write proposal to tracker-shaped path`, victim md5 `d7678fce…` post-run — BYTES IDENTICAL. Existing non-tracker `--out` → exit 2, bytes untouched. Fresh non-tracker `--out` → exit 1 with proposal written (positive path not over-blocked). `sprints/`-location sub-case covered by `test_out_refusing_tracker_named_path_in_fresh_dir`, green in-suite.
- Tests: `python3 -m unittest tests.test_reconcile` → 19/19 OK (4 new F1 tests green alongside the untouched original exact-match test). QA red-proofs §16 two-layer sabotage (guard noop + O_EXCL→O_TRUNC) claim spot-checked via code read (both sites exclusive) and the passing refusal/positive test split — load-bearing, no vacuous check.

### F2 — CLEARED (T6 follow-up issue filed, URL recorded in-package)

- `gh issue view 57` → OPEN, `https://github.com/Heretek-AI/heretek-rigs/issues/57`, title carries the `remediate-39-generate` sketch marker; body is the design-sketch transcription (deferred generate scope, reconcile-diff prerequisite + row-model consumption, TPM-approval requirement, REQ-R3 convergence acceptance) — read-only `gh` reads only.
- `tasks.md:26-35` T6 is `[x]` with the issue URL + filing note (grep count 1). In-package recording complete.

### Scope / regression / gates (all independently re-run)

- Rework diff `2a1c6a2..cd262e6`: 6 files only (`scripts/reconcile.py`, `tests/test_reconcile.py`, `tasks.md`, 2 reports + this verification record). No `specs/`/`rigs/`/`rosters/`/`registry/` edits; `Makefile` + `scripts/verify-rigs.sh` untouched by rework (V1–V9 byte-identical); no scope creep beyond F1/F2.
- `make verify` → `SUMMARY: 26 checks passed, 0 failed`, exit 0 (+ standing live-health advisory WARN/SKIP, unchanged); V10 reports 19 tests pass. `openspec validate remediate-39-reconcile` → valid, exit 0. Secrets scan over the rework diff (token-shaped patterns): 0 real hits.
- Live read path unchanged: `--live` over the 3 mission trackers → exit 1, `14 diff(s) across 23 row(s); TPM approval required — no files modified.` Mission md5s identical before/after (`phase0 d7678fce…`, `wave1 a24fca86…`, `wave2 74f93824…`, matching QA §16). QA re-verification claims spot-checked and confirmed (26/0, 19/19, F1 repro md5, #57 OPEN, 14-diffs live).

### Ruling

- F1: CLEARED. F2: CLEARED. No new blocking defects. Both binding findings closed with red-proofed guards.

> VERDICT: PASS (prior re-audit cd2626e+6f916cf — superseded; preserved as history)

## Re-audit — wave-39-review2-reaudit (2026-10-23, review fixes d9b6504 + evidence 6d56b10) — drift-guard re-audit

- Stage/wave: `wave-39-review2-reaudit` · Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile`
- Commits under audit: `d9b6504` (review fixes) + `6d56b10` (evidence/QA on top). `git log --oneline -6` confirms; `git status --short` clean at audit time (before this append; no commit/merge/push by this audit).
- Spec read from disk first: this report (history above), `openspec/changes/remediate-39-reconcile/tasks.md` (T6 still `[x]` with issue #57 URL), `openspec/changes/remediate-39-reconcile/specs/tracker-reconcile/spec.md`, `docs/reports/qa-wave-39-reconcile.md` (§Review-fixes re-verification + F1 advisory), `docs/reports/wave-39-review-fixes-implementation.md`, `docs/evidence/wave-39-reconcile/red-proofs.log` (§17), `AGENTS.md`.
- Auditor touched no worktree sources and no mission files: all probes ran against `/tmp/opencode/hr39reaudit2/` copies or fresh `tempfile` fixtures; mission repo never written.

### 1. Diff audit — scope CLEAN

- `git diff b2f107f...d9b6504 --stat`: exactly 3 files (`docs/reports/wave-39-review-fixes-implementation.md` new, `scripts/reconcile.py` +27/−3, `tests/test_reconcile.py` +152). Evidence commit `6d56b10`: 2 files (`docs/evidence/wave-39-reconcile/red-proofs.log` §17, `docs/reports/qa-wave-39-reconcile.md` §Review-fixes). Total `b2f107f...HEAD`: 5 files.
- No V1–V9 changes: `Makefile` + `scripts/verify-rigs.sh` untouched by review-2 (V10 reports 24 tests pass, matching the new suite size). No `specs/`/`rigs/`/`rosters/`/`registry/` edits (`grep` over diff names: NO_FORBIDDEN). No scope creep beyond the two approved review items.

### 2. Changed-region reads — both items CORRECT

- Normalization helper `scripts/reconcile.py:321-330`: `" ".join(str(note).replace("|", "/").split())` — `|`→`/` then EVERY whitespace run (spaces, tabs, newlines) collapses to one space; `str()` coerces non-string notes. Independently exercised: `"QA PASS a|b\nc   d  placed"` → `"QA PASS a/b c d placed"`; `"a\tb\n\nc"` → `"a b c"`; clean notes normalize to themselves. Correct.
- Application sites: `propose_cell()` both branches (`:333-343` parked True/False via shared `note`) + missing-convergence-annotation site (`:407-411`). `queue:` diagnostic fields keep the RAW note byte-identical (independent probe: `PROPOSED-CELL` normalized `wip x/y z w ongoing` while `queue:` line kept raw `wip x|y` + multi-space) — normalization masks no finding. Correct.
- Except-clause `main` (`:536-542`): `except (AttributeError, TypeError, ValueError, KeyError)` AFTER the `ReconcileError` handler — concise one-line `reconcile: FAILED: malformed input (<Type>: <detail>)` with whitespace-collapsed detail, exit 2, no traceback. `ReconcileError`→2, diffs→1, in-sync→0 paths untouched (suite + live run confirm). Legitimate-flow check by reading the `try` block: `JSONDecodeError` (a `ValueError` subclass) is consumed by local handlers in `run_rig`/`load_json_file` first; `refuse_out_path`/`parse_tracker` raise `ReconcileError` (first handler wins); `parser.error()` raises `SystemExit` (`BaseException`, uncaught); `queue_terminal`/`diff_row` `AttributeError`/`TypeError`/`KeyError` arise only from non-dict trails, unhashable ids, missing row keys — all malformed-input signals. No legitimate control flow broken. Correct.
- Independent spot-checks of QA's two load-bearing claims (fresh `tempfile` fixtures, not reusing test helpers): (SPOT1) hostile note `wip x|y\nz   w ongoing` → exit 1, single `PROPOSED-CELL` pipe-free/newline-free with `wip x/y z w ongoing`, raw note preserved in `queue:` line; (SPOT2) trail `[42, "not-a-dict"]` → exit 2 `malformed input (AttributeError: 'int' object has no attribute 'get')`, no traceback. Both match QA §17.

### 3. QA F1 advisory — ruling: PASS-WITH-NOTE (not a finding)

- Independently reproduced: the `stale-terminal` branch (`reconcile.py:414-424`, tracker-claims-terminal while queue is not) interpolates the RAW note — direct `diff_row` probe returned proposal `'Re-verify W1-01 with QA, or correct the tracker cell; queue-side evidence: wip update x|y\nz   w ongoing'`, where the `|` WOULD split a pasted markdown table row into an extra column and the newline WOULD break the row across lines. The corruption is real, not hypothetical.
- Nevertheless PASS-with-note, for three independent reasons: (a) the branch was explicitly OUTSIDE the approved review brief (scoped to `propose_cell` + missing-annotation site) — the fix commit did exactly what was approved, so this is not a missing deliverable; (b) it is pre-existing behavior, not a review-2 regression (no previously-passing shape now fails); (c) it is fully disclosed in both the implementer's report (Residual) and QA's F1 with exact blast radius, so nothing is silent. The stale-terminal proposal is also a `Re-verify…` instruction rather than a paste-into-Status-cell replacement, which weakens any REQ-R2/T2 paste-ready claim against it. Recommend a follow-up review item to extend normalization to that branch — advisory only, no action for this stage.

### 4. F1/F2 from the original FAIL remain CLEARED (quick re-probe)

- F1 (overwrite gap): auditor's exact attack re-run on scratch (`--tracker …/input-tracker.md --out …/phase0-dispatch-tracker.md`, victim byte-copy md5 `d7678fce…`): refused exit 2 `refusing to write proposal to tracker-shaped path`, victim md5 `d7678fce…` post-run — BYTES IDENTICAL. Existing-file variant likewise refused exit 2, bytes identical. Positive path unblocked (suite green).
- F2 (unfiled follow-up): `gh issue view 57` → OPEN, `https://github.com/Heretek-AI/heretek-rigs/issues/57`, title carries the `remediate-39-generate` sketch marker; `tasks.md` T6 still `[x]` with the URL. Cleared.

### 5. Gates re-run by this auditor

- `make verify` → `SUMMARY: 26 checks passed, 0 failed`, exit 0 (+ standing live-health heartbeat WARN / seat-idleness SKIP advisory, unchanged); V10 reports 24 tests pass.
- `openspec validate remediate-39-reconcile` → `Change 'remediate-39-reconcile' is valid`, exit 0.
- `python3 -m unittest tests.test_reconcile` → 24/24 OK (incl. the 5 review-2 tests, also run standalone: 5/5 OK).
- Secrets scan over the review-2 diff (token-shaped patterns): 0 hits. `docs/evidence/wave-39-reconcile/red-proofs.log` §17 present with the review-2 sabotage record.

### Ruling

- Scope clean, both approved review items correct with load-bearing non-vacuous tests, QA's claims independently confirmed, F1/F2 stay cleared, all gates green. QA's F1 is a real but explicitly out-of-scope, pre-existing, fully disclosed residual → advisory, not a finding. No new blocking defects. (Review2 ruling — preserved as history; restated below by the Option A re-audit.)

## Re-audit — wave-39-optionA-reaudit (2026-10-23, Option A + perms df6e6cb + evidence c71f7f3) — drift-guard re-audit

- Stage/wave: `wave-39-optionA-reaudit` · Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile`
- Commits under audit: `df6e6cb` (Option A + perms) + `c71f7f3` (evidence/QA on top). `git log --oneline -4` confirms (`c71f7f3`, `df6e6cb`, `0e0bcc3`, `6d56b10`); `git status --short` clean at audit time (before this append; no commit/merge/push by this audit).
- Spec read from disk first: this report (history above), `openspec/changes/remediate-39-reconcile/tasks.md` (T6 still `[x]` with issue #57 URL), `openspec/changes/remediate-39-reconcile/specs/tracker-reconcile/`, `docs/reports/qa-wave-39-reconcile.md` (§Re-verification 2026-10-23 wave-39-optionA-reverify), `AGENTS.md`.
- Auditor modified no source files: all probes ran against `/tmp/opencode/hr39optionA/` + fresh `tempfile` fixtures; mission repo never written. Only this verification report is appended (uncommitted, per brief).

### 1. Diff audit — scope CLEAN

- Fix commit `df6e6cb --stat`: exactly 2 files (`scripts/reconcile.py` +5/−2, `tests/test_reconcile.py` +123). Evidence commit `c71f7f3`: exactly 2 files (`docs/evidence/wave-39-reconcile/red-proofs.log` +30, `docs/reports/qa-wave-39-reconcile.md` +26).
- No V1–V9 changes: `git diff df6e6cb --name-only -- Makefile scripts/verify-rigs.sh specs/ rigs/ rosters/ registry/` → empty. No forbidden-dir edits. No scope creep beyond the two approved items (stale-terminal normalization + 0o600).

### 2. Changed-region reads — both items CORRECT

- Stale-terminal fix (`scripts/reconcile.py:415,423`): `evidence_note = normalize_proposal_note(latest_note)` then `queue-side evidence: {evidence_note or entry.get('state')}`. Fallback-to-state preserved when note empty (`normalize("")` → `""` falsy → state; independently probed: empty note → `queue-side evidence: in-progress`). Diagnostics untouched (`:420` `queue:` field keeps RAW `latest_note`, byte-identical by design). Correct.
- 0o600 (`:144`): `os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)` — the ONLY `os.open` site in the script (grep); no `write_text`/`chmod`/`O_TRUNC` anywhere on the `--out` path; both write sites (`:523` diffs, `:531` in-sync) go through `write_out_exclusive`. No other world-readable creates. No test/gate depends on group readability (only assertion on mode is the new owner-only test `:836` `mode & 0o077 == 0`). Correct.

### 3. Prior advisory CLOSED — intentional-raw set verified by own grep

- Classified every `latest_note` use in `scripts/reconcile.py`: paste-safe — `propose_cell` parked True/False (`:389`,`:396` via internal `normalize_proposal_note`), missing-annotation inline (`:409`), stale-terminal `evidence_note` (`:423`, the fix); intentional-raw — exactly the 4 `queue:` diagnostic fields (`:388`,`:395`,`:406`,`:420`), which QA §Review-fixes documents as raw-by-design and which never enter a `PROPOSED-CELL` line; non-interpolated — `queue_terminal :275` (regex match only). No raw-note proposal site remains. The review2 advisory is the exact defect this commit fixes → CLOSED, not merely noted.

### 4. F1/F2 stay CLEARED

- F1 (overwrite gap): auditor's tracker-shaped-victim attack re-run on scratch (`--out …/phase0-dispatch-tracker.md`) → exit 2 refusing tracker-shaped path, victim md5 identical pre/post. Cleared.
- F2 (unfiled follow-up): `gh issue view 57` → OPEN (`remediate-39-generate` sketch); `tasks.md` still `[x]` with the URL (grep count 1). Cleared.

### 5. Gates re-run by this auditor + one QA claim spot-checked independently

- `make verify` → `SUMMARY: 26 checks passed, 0 failed`, exit 0 (+ standing live-health heartbeat WARN / seat-idleness SKIP advisory, unchanged); V10 reports 28 tests pass.
- `openspec validate remediate-39-reconcile` → valid, exit 0. `python3 -m unittest tests.test_reconcile` → 28/28 OK.
- Secrets scan over the `6d56b10...HEAD` script/test diff (token-shaped patterns): 0 hits.
- Independent spot-checks (fresh fixtures, not reusing test helpers): (SPOT1) hostile note `wip ev|idence\nline2   spaced` in stale-terminal row → exit 1, single `PROPOSED-CELL` pipe-free with `wip ev/idence line2 spaced`, matching QA §optionA 4a; (SPOT2) empty note → falls back to state; (SPOT3) real `--out` run → mode `0o600`, `mode & 0o077 == 0`. All match QA's table.

### Ruling

- Scope exact (2 + 2 files), both hunks correct with fallback preserved and diagnostics untouched, prior advisory verified closed with a complete raw-site classification, F1/F2 stay cleared, all gates green, QA's claims independently confirmed with non-vacuous probes. No new blocking defects. PASS stands.

VERDICT: PASS
