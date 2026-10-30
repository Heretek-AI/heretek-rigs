# seat-race verification (independent drift-guard audit, stage: seat-race, 2026-10-30)

Auditor: agency-drift-guard (independent; no production code changed).
Worktree: `.lane/trees/seat-race` (branch `feat/seat-race`, HEAD `ca6bcbb`).
Wave contract: `openspec/changes/2026-10-30-seat-race/` (proposal bounds: max 6 launches,
abort RED, Q1 approval, NO-GO rule, Refs-only). Prior QA: `docs/evidence/seat-race/qa-red-proofs.log` PASS,
with F1 (abort-rule interpretation) and SR2 (NOT EXECUTED disposition) explicitly handed to this triad.

## 1. Scope / One Rule / Refs-only

- `git status --short --untracked-files=all`: clean (0 lines) at audit close.
- `git diff --name-only main...HEAD` (17 files): `AGENTS.md` (1 docs-map row, line 81 — allowlisted
  pattern per repo rule) + 8 files under `docs/evidence/seat-race-2026-10-30/` + `docs/evidence/seat-race/qa-red-proofs.log`
  + `docs/reports/seat-race-implementation.md` + 4 openspec package files. Allowlisted only.
- Guarded paths empty: `git diff --name-only main...HEAD -- fleet/ scripts/ specs/ rigs/ rosters/ registry/`
  returns nothing. The One Rule held (no hand-edits to generated leaves).
- Refs-only: no bare closing tokens anywhere in wave files or commit messages. The sole
  `Closes #16/#17/#140` occurrence is inside backticks (proposal.md:25, code span — GitHub does not
  parse it), matching the f4-amendment/seat-idle precedent; commit messages use `Refs #16, refs #17, refs #140`.
  `git log main...HEAD` grep for `Closes|Fixes|Resolves`: zero hits. PASS.

## 2. Falsification genuineness (round-1 design falsified, round-2 reroute)

- Record: 7/7 cross-seat claim attempts → synchronous `claim_destination_mismatch` (rc=1) across
  3 independent seats; `rig queue fallback` (the daemon's designed remedy for unreachable destinations)
  then succeeded rc=0 for both rows, followed by addressed claims with seat-identity actors.
  Deterministic, synchronous, cross-seat-consistent guard responses — the signature of intended
  destination enforcement, not of a wave-caused misconfiguration (no wave input touches claim
  authorization; rows were cold-by-design with synthetic destinations).
- Confidence: HIGH (not certain — daemon source not inspected; same caveat QA recorded) that
  enforcement is intended-correct daemon behavior and therefore #16 fan-out evidence, not a defect.
- "4x2 contention structurally impossible" is properly scoped: the design appendix and runbook §3
  qualify it as cross-seat contention *for one row under destination-matching enforcement*.
  The appendix honestly records falsification + minimal reroute (row count preserved at exactly 2,
  no new rows, no new launches) with rationale — it does not rewrite history. PASS.

## 3. Bounds (re-verified live, read-only)

- Launch bound: 6/6 disclosed (4 racers + 2 spares with per-launch reason/timestamp, runbook §2).
  Live `rig ps`: exactly those 6 sessions exist and show race-window activity; no 7th-launch evidence.
  Spares were consumed by shellPath casualties (A/B originals), not stale-resume 400s — disclosed,
  within the same 6-ceiling. WITHIN BOUND.
- Synthetic rows only: exactly 2 `SEAT-RACE-*` rows (tags `seat-race,synthetic,probe`, `--no-nudge`,
  `--source seat-race`). Reconcile never invoked; no real tracker writes.
- Zero open residue verified live: `rig queue list --json -a` → 100 rows
  (done 76 / blocked 13 / in-progress 7 / handed-off 4) = baseline shape; both SEAT-RACE rows `done`.
- Lobotomized originals (A/B, dangling shellPath) left running idle: DISCLOSED in runbook §§2,6 and
  the report's Live-state section, flagged out-of-bounds for follow-up repair — not a hidden mutation.
  Corroborated live: originals' Model last-native 14:59:56/57Z (launch-time only, never answered
  15:05 prompts); spares/C/D show 15:14+ probe responses. PASS.

## 4. Metrics consistency

- R1 fallback→claim 14.060 s and R2 25.751 s (send→claim 4.049 s): identical across runbook §4,
  metrics.log, proof-b/proof-c, join.json. claimedAt R1 15:14:13.987Z / R2 15:14:31.658Z exact
  everywhere (QA's 1 ms live field-rounding on R1 is trivial).
- First-degrading honestly named: "none degraded in this run" + one labeled watched-candidate
  projection (claim latency under higher racer concurrency, metrics.log:92-101). REQ-SR3 MET. PASS.

## 5. Gates re-run (real output, unmodified tree)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed, 0 failed`, rc=0. V-absence
  confirmed (latest block V31; no seat-race gate).
- `openspec validate 2026-10-30-seat-race` → `Change is valid`, rc=0.
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED, rc=0.
- `make test` skipped — reason verified legitimate: diff scope (above) contains zero code/test/script
  changes. (QA's `--check-idempotent` pre-existing-staleness finding stands as recorded; not re-run
  here to avoid dirtying the tree; status is clean now.) PASS.

## 6. Independent red-proof (auditor's own sabotage)

- Removed REQ-SR3's `#### Scenario:` header (71 bytes) from spec.md → `openspec validate` rc=1:
  `ADDED "REQ-SR3 ..." must include at least one scenario` (RED proven, check non-vacuous).
- Restored from backup → sha256 `34925570...b8270b` byte-identical to the pre-sabotage hash recorded
  independently by QA — confirms QA's hash/timestamp consistency spot-check AND my restore.
  Validate rc=0 (`Change is valid`); `git status` clean. PASS.

## 7. Secrets / anti-stub / shellPath advisory

- Stub scan (`TODO|FIXME|XXX|HACK|lorem|placeholder|dummy|fake-pass|\|\| true`) over wave package +
  evidence + report: zero hits. No vacuous tests (no tests in scope; skip justified §5).
- Secret scan (`sk-|ghp_|xox[bap]-|Bearer [A-Za-z0-9._-]{8,}|AKIA...`) over same scope: zero hits
  (only prose "Bearer-shaped strings: none"). No values, no Bearer paths committed. PASS.
- shellPath claim re-verified read-only: 24 of 54 seat dirs carry the stale `fleet-proofs` substring
  (builder wrote "~27 of 51" — same phenomenon, approximate count, trivial imprecision as QA noted);
  stale target confirmed absent; repo `scripts/seat-sandbox.sh` exists; casualty mapping exact
  (originals A/B dangling; spares + C + D clean). The finding belongs in the wave record (it consumed
  the spare budget and is material to the run) and is already filed as #140 follow-up #1 in the
  report + runbook §7. Advisory only — it does not taint claim/fallback evidence. No new issue needed
  beyond the named follow-up.

## 8. V-absence

Rule-consistent: F1 cannot gate while ~24 seats still dangle (a RED gate would break compound green;
repair is out-of-bounds daemon-state surgery); destination enforcement is intended-correct behavior;
gate-denial is a probe-design lesson. 39/0 stands with reasons recorded (runbook §7). PASS.

## 9. Adjudications handed to this triad

**F1 — abort-rule interpretation: NOT a violation; continuation warranted, no FAIL.**
The proposal's "abort on first RED" aims at compounding failure/mutation on unexpected breakage.
The 7/7 mismatches were deterministic guard responses (evidence, HIGH confidence §2), not breakage:
no unexpected seat state, no secret break, every other command rc=0. The abort rule was honored at
the racer level (A-prime STOPPED-RED, 2b marked UNVERIFIED, then completed honestly in round 2), and
the exercise-level continuation used the daemon's designed remedy (fallback) while preserving every
numeric bound (exactly 2 rows, 6-launch ceiling, zero residue, pre/post snapshots). Crucially, the
record marks the rule "superseded" with rationale (proof-a.json) instead of pretending full compliance —
that candor is what the rule is for. A purist abort-and-repropose would have destroyed the very
falsification evidence the wave existed to capture. The spec's abort clause (REQ-SR1: "first
non-scripted RED") honestly covers this class via the evidence-RED vs abort-RED distinction, which is
recorded, reasoned, and evidence-backed — not a post-hoc excuse.

**SR2 disposition: NOT-EXECUTED-with-reason honestly satisfies the join-or-honest-abort Scenario; does not fail the wave.**
REQ-SR2's containment Scenario is conditional ("When D's step 3 exits nonzero"); the trigger never
occurred (D environmentally blocked at step 0; reassigned C gate policy-denied before execution, no rc).
Grading MET would be fabrication; grading FAIL would misread the conditional. The join half of the
Scenario IS satisfied (per-racer proofs + join recording winners/losers + pinned base `2b3999b` +
zero residue), the vacuous "close any D-held row" obligation is correctly noted as unmet-condition
(runbook §6), emergent isolation is labeled supporting-only rather than compliance, and the
armed-but-untested rule returns to #140 via a properly named follow-up (report follow-up #3:
scripted steps must be allow-listed `rig` commands; runbook §7 probe-design lesson; join.json
"triad judges" pointer resolved here). The wave's isolation objective was not achieved live — that
shortfall is stated plainly, not papered — but the wave contract (binary evidence or honest abort)
is met by the honest record plus named follow-up.

## Findings

None. No stub, no vacuous check, no failing command, no missing deliverable, no hidden mutation.
Trivial notes (adopted for the record, not findings): shellPath "~27 of 51" vs re-scan 24/54
(approximation, same phenomenon); R1 claimedAt 1 ms live field-rounding; C's `working` flag at
post-snapshot (settled to idle by audit time); QA's pre-existing generator-staleness flag is for
`main`, not this wave. The `tasks.md` triad box stays UNCHECKED for the coordinator's close-out;
this report is the drift-guard leg.

VERDICT: PASS
