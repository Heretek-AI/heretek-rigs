# Verification: spec-57-generate (issue-57 generate-trackers, spec-only stage)

Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/spec-57-generate`
Branch: `docs/issue-57-generate-trackers` @ `8383729` (log: `8383729 / 6fd6611 / 88af294`).
Stage under audit: spec authoring only — no `scripts/`/`tests/`/`Makefile` implementation expected.
Inputs read from disk: `AGENTS.md`, `git diff main`, plan (`/home/john/.opencode/plan/issue-57-generate-trackers-plan.md`),
`proposal.md`, `design.md`, `specs/generate-trackers/spec.md`, `tasks.md`,
`docs/reports/spec-57-generate-implementation.md`, `docs/evidence/spec-57-generate/red-proofs.log`,
`openspec/changes/remediate-39-reconcile/` (authority), `scripts/reconcile.py` + `tests/test_reconcile.py` (read-only),
`Makefile:24`, `gh issue view 57`.

## 1. Re-runs (auditor-executed, not trusted)

- `openspec validate issue-57-generate-trackers` → `Change 'issue-57-generate-trackers' is valid`, exit 0. Matches red-proofs claim §1.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 26 checks passed, 0 failed` (incl. V10 reconcile 28/28), exit 0. Matches red-proofs claim §2.
- `git status --short` → empty (clean). The red-proofs log's "only this untracked log file" note is stale in the good direction:
  both the log and the implementation report are now committed in `8383729`; nothing uncommitted remains.
- `git diff main --stat` → `AGENTS.md +1`, 4 spec-package files + 2 docs files. No other dirt. Matches red-proofs claim §4.

## 2. AGENTS.md sprawl check — PASS

`git diff main -- AGENTS.md` shows exactly one added table row (`Tracker proposals` with `--json` discipline,
propose-only invariant, fresh-out refusal rule, `make generate-tracker`). No other AGENTS.md change. Plan Q12 allows
"~5 lines"; delivered 1 row. No sprawl.

## 3. Twelve binding decisions — each traced (no drift)

- Q1 #57 next / Q2 #12 separate spike / Q3 upstream watch-wait: process context, correctly recorded only in the
  implementation report's decisions log. No artifact required; no drift.
- Q4 propose-only (extends REQ-R2): REQ-G2 + design refusal matrix + AGENTS.md row (`NEVER auto-edit trackers or
  write queue state`). Row-model authority `REQ-R2` confirmed in `remediate-39-reconcile/specs/tracker-reconcile/spec.md:22`.
  No weakening.
- Q5 shared row model: REQ-G5 mandates import of `parse_tracker`, `normalize_tracker`, `recorded_note_ids`,
  `queue_terminal`, diff semantics after a G-T1 importable-module refactor specified as implementation work, not
  performed now. All five names verified present in `scripts/reconcile.py` (`def` lines 184/251/263/270/346).
  No forked parser specified anywhere. No drift.
- Q6 fresh-out `O_EXCL` guard: REQ-G2 scenarios + design matrix row + G-T3 sabotage list. Mirrors the hardened
  reconcile guard verified at `scripts/reconcile.py:95-157` (`refuse_out_path` + `write_out_exclusive` with
  `os.O_CREAT|O_EXCL`). No weakening.
- Q7 ownership + `NEEDS-HUMAN-REVIEW`: design ownership table (every field has exactly one owner; no-qitem and
  no-queue-entry rows → `tracker-row-without-qitem` + marker, exit 1) + REQ-G1 scenarios requiring both-side
  evidence and never-guessed status. Matches issue #57's fail-closed sketch. No drift.
- Q8 cell shapes + append-only-on-newer-transition: design Q8 transcribes the four shapes from
  `reconcile.py` `normalize_proposal_note` (verified line 321) / `propose_cell` (verified line 333) behavior,
  including `recorded_note_ids` append rule and paste-normalization (`|` → `/`). Line citations are approximate
  (code evolved) but every cited function exists with the described semantics. No drift.
- Q9 per-tracker only: design scope section + REQ-G3/G-T4 (parent row only on its own qitem diff; "No cross-wave
  rollup engine exists in this change"). Matches issue #57 sketch scope. No drift.
- Q10 locked enum + mapping table: design table (`STAGED, DISPATCHED, PARKED, QA PASS, PLACED, DONE, CLOSED +
  OTHER(<raw>)`) + REQ-G5 amendment rule. Substring rules verified against `normalize_tracker` (line 251:
  `qa pass`/`placed`/`closed|done`/`staged`/`dispatched`/`parked` minus `blocker satisfied`) and `queue_terminal`
  (line 270: terminal states + terminal-note regex). No drift.
- Q11 empty-queue `[]` exit-2: design matrix + REQ-G4 dedicated scenario citing the verified live `[]` state.
  No "in sync" path for empty queue anywhere. No drift.
- Q12 home + AGENTS.md patch: package at `openspec/changes/issue-57-generate-trackers/` (proposal/design/
  specs/generate-trackers/spec/tasks = four artifacts) + 1-row AGENTS.md patch. No drift.

## 4. Scope-creep hunt — PASS (nothing smuggled)

`grep` for `queue (write|create|update)`, `auto-apply`, `rollup`, `cross-wave` over the package returns hits ONLY in
prohibition/non-goal positions (proposal non-goals, REQ-G2 title, design "MUST NOT synthesize/roll up" rows).
No queue-write verb, no auto-apply path, no cross-wave rollup engine is specified. TPM approval is required, never
bypassed. `gh issue view 57` sketch elements (row-ownership, note semantics, rollup, fail-closed, TPM-approval,
convergence) are each covered and none is exceeded.

## 5. Parallel-parser risk — PASS

The package specifies exactly one table semantics: the shared reconcile module. Design risks section names two-parser
drift explicitly and declares any fork a spec violation (REQ-G5); REQ-G5's scenario gates it by import inspection +
`tests/test_reconcile.py` 28/28 unmodified. No second parser, normalizer, or enum mapping exists in the spec.

## 6. Overwrite risk — PASS

Every `--out` path in the package lands on a fresh non-tracker proposal file: input-tracker, `*dispatch-tracker.md`,
`sprints/`-interior, and existing-file destinations are all refused fail-closed (exit 2, md5 pre/post proof), with
the existing-file check re-verified `O_EXCL` at write time (G-T3, REQ-G2, design matrix). G-T4 explicitly forbids
`--out` targeting the scratch convergence copy. No `--out` example in any task points at a tracker.

## 7. Vacuous-acceptance check — PASS

Every task carries a binary pass/fail gate: G-T1 emitter + `git status` clean + unittest green with 28/28 pinned;
G-T2 marker presence + non-zero exit asserted; G-T3 named exit-2 per sabotage + md5 byte-identity + two-sabotage
hand replay; G-T4 reconcile re-run exit 0 with explicit "in sync" covering every parsed row; G-T5 `make
generate-tracker` exit codes + `verify-rigs.sh` 26/0. No "looks good" check found.

## 8. `make generate` vs `make generate-tracker` — deliberate deviation, SOUND (not a finding)

Plan text (package item 1, G-T5 acceptance) says `make generate TRACKER=…`. `Makefile:24` confirms `make generate`
is the deterministic fleet generator (`fleet/fleet.yaml` → 51 AgentSpecs / 8 RigBundles / Roster / Registry) with
idempotency gates depending on it. The spec wires `make generate-tracker` instead and states the reason in three
places (proposal boundaries, G-T5 text, AGENTS.md row); the implementation report flags it as its one deliberate
deviation with the single rename point. Overloading `make generate` would shadow fleet generation — the rename is
the correct call, fully disclosed, consistently applied. The audit brief anticipates exactly this check.

## 9. Stub / secrets scans — PASS

- Stub scan over package + AGENTS.md + report: sole hit is the report's meta-sentence "Stub scan … → clean".
  No `TODO`/`FIXME`/`XXX`/`placeholder`/`stub`/`NotImplemented`/`lorem`/`TBD` in any artifact.
- Secret-pattern scan (`ghp_`, `github_pat_`, `sk-`, `AKIA`, `xox[bpas]-`, `PRIVATE KEY`) over package + AGENTS.md +
  report + evidence: zero hits.

## 10. Red-proofs audit — PASS (non-vacuous, with disclosed validate limits)

The log's three sabotage REDs (deleted delta spec → validate exit 1; MUST→SHOULD in REQ-G3 → STRUCT3 RED while
validate stays warning-only exit 0; broken G-T4→REQ-G3 link → MAP RED while validate stays exit 0) are internally
consistent and correctly characterize `openspec validate` as blind to tasks.md presence and RFC 2119 enforcement,
with the four-artifact / STRUCT3 / MAP gates as the real guards. Revert proofs (byte-restore, re-green, clean
status) are claimed per sabotage; current clean status + green re-runs corroborate the final state. The branch/COMMIT
labels in the log (`6fd6611`) predate the QA commit (`8383729`) — expected ordering, not a discrepancy.

No findings. The spec package is complete (REQ-G1..G5 with Given/When/Then, G-T1..G-T5 1:1 mapped, four artifacts),
faithful to all 12 binding decisions, free of scope creep, parallel semantics, overwrite paths, vacuous checks,
sprawl, stubs, and secrets, with both acceptance commands re-run green.

VERDICT: PASS
