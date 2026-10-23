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

VERDICT: FAIL
