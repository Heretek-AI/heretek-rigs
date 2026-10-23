# Delta spec: generate dispatch-tracker proposals from queue state

## ADDED Requirements

### Requirement: REQ-G1 — Proposal completeness (every diffed row, paste-ready cell)

The generator MUST, for each input tracker, emit a proposal covering every
row the shared diff model flags (stale-state,
parked-satisfied-but-tracker-silent, missing-convergence-annotation,
tracker-row-without-qitem, stale-terminal, `OTHER(<raw>)`), each carrying
the exact full-replacement Status cell text from the design.md Q8 shapes.
Rows that already agree MUST be listed as unchanged (no partial-row
silence). `OTHER(<raw>)` and orphan-qitem rows MUST carry
`NEEDS-HUMAN-REVIEW` markers quoting both-side evidence and MUST keep the
run non-zero — the status MUST NEVER be guessed.

#### Scenario: Drifted Wave-1 fixture yields seven paste-ready cells

- Given the synthetic pre-convergence Wave-1 tracker (4× STAGED/awaiting
  QA, 1× PARKED blocked on QA, 1× DISPATCHED, 1× QA PASS with stale note)
  with canned queue state showing all 7 slices QA-passed and placed,
- When the generator runs,
- Then it emits 7 proposals, each naming slice + qitem + tracker-side +
  queue-side values with a full-replacement Status cell, and exits non-zero.

#### Scenario: Unknown prose is flagged, never coerced

- Given a tracker row whose Status cell matches no enum arm,
- When the generator runs,
- Then the row is emitted as `OTHER(<raw>)` with a `NEEDS-HUMAN-REVIEW`
  marker quoting the raw cell and the queue-side evidence, and the run
  exits non-zero.

### Requirement: REQ-G2 — Read-only + fresh-out guard (propose, never auto-edit)

The generator MUST be read-only: it MUST NOT modify any tracker file or any
queue state, and it MUST write its proposal ONLY to a fresh non-tracker
path. An `--out` that resolves to an input tracker, to any tracker-shaped
path (`*dispatch-tracker.md` or anything inside a `sprints/` directory), or
to any existing file MUST be refused fail-closed (exit 2, destination bytes
untouched; the existing-file check MUST be re-verified `O_EXCL` at write
time so a file appearing after the up-front check is still refused, never
clobbered).

#### Scenario: Run leaves the tree untouched

- Given a drifted tracker and canned queue state,
- When the generator runs (with or without `--out`),
- Then tracker bytes and queue inputs are byte-identical afterwards (prove
  with md5 pre/post), and `git status --short` shows no modifications.

#### Scenario: Tracker-shaped and existing `--out` refused

- Given any `--out` pointing at an input tracker, a fresh
  `*dispatch-tracker.md` path, a `sprints/` path, or an existing file,
- When the generator runs,
- Then it exits 2 with a `refusing …` diagnostic and the destination is
  byte-identical (or never created).

### Requirement: REQ-G3 — Convergence (generated output re-runs to zero diffs)

Applying every non-`NEEDS-HUMAN-REVIEW` proposed cell to a scratch copy of
the tracker MUST converge: re-running the reconcile diff
(`scripts/reconcile.py --tracker <patched-copy> --queue-list
<canned.json> --transitions <canned.json>`) MUST report zero diffs with
exit 0 and an explicit "in sync" summary. `NEEDS-HUMAN-REVIEW` rows are
excluded from the replay (they require TPM judgment, not pasting).

#### Scenario: Approval simulation converges

- Given a generator proposal for the drifted Wave-1 fixture,
- When every non-`NEEDS-HUMAN-REVIEW` proposed cell is applied to a scratch
  tracker copy and the reconcile diff re-runs against the same canned queue
  state,
- Then the re-run exits 0 with an "in sync" summary covering every parsed row.

### Requirement: REQ-G4 — Fail-closed (named diagnostics, never silent)

A missing/unreadable/unparseable tracker, an unreachable or unparseable
queue listing, an EMPTY queue list (`[]`), or malformed input MUST fail
with a named diagnostic and exit 2 — never "in sync", never a partial-diff
output, never a traceback exit. Orphan-qitem rows
(`tracker-row-without-qitem`) MUST surface as diffs (exit 1), never vanish.

#### Scenario: Empty queue is a hard failure

- Given a well-formed tracker and a queue listing that parses to `[]` (the
  verified live state of `rig queue list --json`),
- When the generator runs,
- Then it exits 2 with a named `EMPTY QUEUE LIST` diagnostic — it MUST NOT
  report "in sync".

#### Scenario: Sabotage matrix stays fail-closed

- Given each sabotage in turn (missing tracker file, short-column row,
  missing queue JSON, invalid queue JSON, unreachable rig binary,
  non-dict transition items),
- When the generator runs,
- Then each exits 2 with a named diagnostic, destination bytes untouched,
  and "in sync" never appears.

### Requirement: REQ-G5 — Shared row model (no parallel semantics)

The generator MUST consume the reconcile row model: after the G-T1
importable-module refactor it MUST import `parse_tracker`,
`normalize_tracker`, `recorded_note_ids`, `queue_terminal`, and the diff
semantics from the reconcile module rather than re-implementing them. It
MUST NOT own a parallel parser, normalizer, or enum-mapping. The locked
enum (`STAGED, DISPATCHED, PARKED, QA PASS, PLACED, DONE, CLOSED +
OTHER(<raw>)`) and the Q8 cell shapes are the single shared contract; any
mapping change lands in the shared module and flows to both commands.

#### Scenario: No forked parser

- Given the generator implementation,
- When its imports are inspected,
- Then tracker parsing, status normalization, note-id extraction, and
  terminal detection resolve to the shared reconcile module — no
  second implementation of any of them exists — and the full
  `tests/test_reconcile.py` suite (28/28) still passes unmodified.
