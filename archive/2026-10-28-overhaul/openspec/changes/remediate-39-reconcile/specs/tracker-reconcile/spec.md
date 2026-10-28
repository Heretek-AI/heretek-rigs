# Delta spec: tracker-vs-queue reconcile diff

## ADDED Requirements

### Requirement: REQ-R1 — Diff queue state against every wave tracker
The command MUST, for each `docs/sprints/wave*-dispatch-tracker.md`
(including `phase0-dispatch-tracker.md`), parse the slice table rows
(slice id, slice qitem, status cell) and compare each row against the
machine-readable queue listing for that row's qitem (status, notes,
transitions). Every mismatch MUST be reported as a row-level diff naming
the tracker file, the row (slice + qitem), the tracker-side value, and
the queue-side value.

#### Scenario: All seven Wave-1 drift classes surface
- Given the pre-convergence Wave-1 state (rows reading STAGED/awaiting
  QA for W1-01/02/06/07, PARKED for W1-04, DISPATCHED for W1-05, while
  queue shows QA PASS + placed for all 7),
- When the command runs,
- Then it reports ≥7 row-level diffs, each naming tracker file, slice,
  qitem, tracker-side value, and queue-side value.

### Requirement: REQ-R2 — Propose, never auto-edit — TPM approval required
The command MUST be read-only: it MUST NOT modify any tracker file or any
queue state. For each diff it MUST emit a proposed row update (exact
replacement status cell text + suggested queue-note append) that the TPM
approves and applies. Applying all approved proposals MUST be checkable
by re-running the command.

#### Scenario: Run leaves the tree untouched
- Given a drifted tracker and live queue state,
- When the command runs,
- Then `git status` shows no modifications afterwards, and every reported
  diff carries paste-ready replacement Status cell text.

### Requirement: REQ-R3 — Empty-diff convergence is the acceptance signal
After a QA+placement turn with all approved proposals applied, tracker
and queue MUST agree: re-running the command MUST report zero diffs
(exit 0 with an explicit "in sync" summary). Any remaining diff MUST exit
non-zero so the command is usable as a gate (e.g. pre-handoff check).

#### Scenario: Convergence is verifiable by re-run
- Given all approved proposals applied after a QA+placement turn,
- When the command re-runs,
- Then it exits 0 with an explicit "in sync" summary covering every
  parsed row (no partial-row silence).

### Requirement: REQ-R4 — Fail-closed parsing
An unreadable tracker, an unparseable slice-table row, a qitem with no
corresponding queue entry, or an unreachable queue listing MUST fail the
command with a named diagnostic — never silently drop the row. The
command MUST consume explicitly machine-readable queue output (flags,
not heuristic scraping of human trailers).

#### Scenario: Missing qitem is a diff, not a drop
- Given a tracker row whose qitem has no queue entry,
- When the command runs,
- Then it reports a `tracker-row-without-qitem` diff (suggesting
  removal/closure review) and exits non-zero — the row MUST NOT vanish
  from the output.
