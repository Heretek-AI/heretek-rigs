# Design: issue-57-generate-trackers

The reconcile diff (option (b)) left three questions open by design — this
change settles them. Row ownership (Q7), note-append semantics (Q8), and
parent-rollup scope (Q9) are decided below; the locked enum (Q10) and the
fail-closed matrix incl. the empty-queue rule (Q11) follow. All 12 plan
decisions are binding on implementation.

## Row-ownership table (Q7)

The generator owns NO prose. Every field has exactly one owner:

| Field | Owner | Generator behavior |
|---|---|---|
| Slice id | tracker (human) | Copied verbatim; NEVER invented. |
| Owner seat | tracker (human) | Copied verbatim. |
| Output | tracker (human) | Copied verbatim. |
| Slice qitem | queue↔tracker link | Copied verbatim. Row with no qitem (em-dash/empty) or a qitem with no queue entry → `tracker-row-without-qitem` proposal carrying a `NEEDS-HUMAN-REVIEW` marker with both-side evidence; the status is NEVER guessed, exit stays non-zero. |
| Status | queue (authority) | Full-replacement cell from the enum mapping table below. Tracker prose that matches no enum arm → `OTHER(<raw>)` + `NEEDS-HUMAN-REVIEW` marker with both-side evidence; NEVER coerced to a guessed enum. |
| Parent row | its own qitem | Emitted ONLY when the parent row's own qitem diffs (per-tracker scope, Q9). The generator MUST NOT synthesize parent status from child rows. |

`NEEDS-HUMAN-REVIEW` markers MUST quote both sides (tracker cell text and
queue `state=` + `latest_transition=<id> (<note>)`) so the TPM can decide
without re-running anything.

## Note-append rule + exact cell shape (Q8)

Status proposals are FULL-REPLACEMENT cells (the TPM pastes one cell, never
splices prose). Exact shapes, inherited from the converged `reconcile.py`
`propose_cell` / `normalize_proposal_note` behavior
(`scripts/reconcile.py:321-343`):

- Terminal queue, stale tracker:
  `QA PASS + PLACED canonical (queue note <id>: <note>; operator note appended)`
- Terminal queue, tracker PARKED without the blocker annotation:
  `QA PASS + PLACED canonical (queue note <id>: <note>; operator note appended — parked-on-QA blocker satisfied)`
- Terminal queue, terminal enum, stale note id (`missing-convergence-annotation`):
  `<existing cell> (queue note <id>: <note>; operator note appended)`
- Non-terminal queue, terminal tracker claim (stale-terminal):
  `Re-verify <slice> with QA, or correct the tracker cell; queue-side evidence: <note-or-state>`
  + `NEEDS-HUMAN-REVIEW` marker.

Append rule: a `(queue note <id>…)` reference is appended ONLY when the
queue's latest transition id is newer than every note id recorded in the
cell (`recorded_note_ids`: `note NNN` / `(NNN)` / `+MMM`); otherwise the
cell is emitted unchanged — no churn. Interpolated notes MUST be
paste-normalized (single line, `|` → `/`, whitespace runs collapsed);
diagnostic fields keep the raw note byte-identical.

## Per-tracker scope (Q9)

One tracker in, one proposal out. The generator diffs each input tracker
against queue state independently; it MUST NOT roll rows up across waves or
across tracker files. A parent row is treated like any other row: emitted
only on its own qitem diff. No cross-wave rollup engine exists in this
change.

## Enum mapping table (Q10 — locked)

Tracker Status cells normalize (case-insensitive substring rules, from
`reconcile.py:251-260`) to exactly this enum; queue terminal signal from
`reconcile.py:270-282`:

| Tracker cell signal | Enum arm |
|---|---|
| `qa pass` in cell (never bare `awaiting QA`) | QA PASS |
| `placed` in cell | PLACED |
| `closed` in cell, or word `done` | CLOSED / DONE |
| `staged` in cell | STAGED |
| `dispatched` in cell | DISPATCHED |
| `parked` in cell UNLESS `blocker satisfied` also present | PARKED |
| none of the above | `OTHER(<raw>)` — raw cell quoted verbatim, always a `NEEDS-HUMAN-REVIEW` diff, never silent |

| Queue signal | Meaning |
|---|---|
| `state` in `closed, done, handed_off, handed-off, complete, completed`, OR latest-transition `state` in that set, OR latest note matching `qa pass\|placed\|closed\|handed-off\|done` | terminal → generator proposes `QA PASS + PLACED canonical …` |
| otherwise | non-terminal → generator proposes nothing terminal; a terminal tracker claim becomes a re-verify proposal |

The enum set is LOCKED: `STAGED, DISPATCHED, PARKED, QA PASS, PLACED,
DONE, CLOSED + OTHER(<raw>)`. Adding an arm requires a spec amendment, not
an implementation judgment call.

## Fail-closed matrix (Q11)

| Condition | Exit | Behavior |
|---|---|---|
| Tracker missing / unreadable / no Slices table / bad header / unparseable row / empty Slices table | 2 | Named diagnostic (`UNREADABLE TRACKER`, `NO SLICE TABLE`, `UNPARSEABLE ROW '<file>:<line>'`, …); never "in sync". |
| Queue listing unreachable, unparseable JSON, or wrong shape | 2 | `UNREACHABLE QUEUE …` / `UNPARSEABLE QUEUE LIST …`; no partial-diff output that could be mistaken for convergence. |
| Queue listing parses to an EMPTY list `[]` (the live state) | 2 | Named `EMPTY QUEUE LIST` failure — an empty queue MUST NEVER report "in sync". |
| `--out` is an input tracker, tracker-shaped (`*dispatch-tracker.md`), inside a `sprints/` directory, or any existing file (re-checked `O_EXCL` at write time) | 2 | `refusing …`; destination bytes untouched (prove with md5 pre/post). |
| Row without qitem / qitem with no queue entry | 1 (diff) | `tracker-row-without-qitem` + `NEEDS-HUMAN-REVIEW`; suggests removal/closure review; row MUST NOT vanish from output. |
| `OTHER(<raw>)` prose or stale-terminal claim | 1 (diff) | `NEEDS-HUMAN-REVIEW` with both-side evidence; still non-zero. |
| Every parsed row agrees (enum terminal + latest note recorded) | 0 | Explicit "in sync" summary covering every parsed row. |

Machine-readable queue input ONLY: `--queue-list` / `--transitions` files
holding `rig queue list --json` / `rig queue transitions --json` output, or
`--live` fetching over the rig CLI with the pinned `--json` read-only verbs
(`list`/`transitions` only; anything else refused). Bare queue output (JSON
+ human trailer) MUST NOT be parsed.

## Risks

- Empty-queue false-green: `rig queue list --json` returns `[]` live TODAY,
  so without the Q11 hard-failure rule the generator would certify any
  tracker "in sync". The exit-2 rule exists because the failure mode is the
  current steady state, not a corner.
- Prose variance: status cells carry free-text annotations (e.g. W1-03's
  `QA PASS 4+merge (row note 3)`); `OTHER(<raw>)` over-reports rather than
  silently agreeing, so new prose styles degrade to review load, not
  missed drift.
- Two-parser drift: the generator MUST import the reconcile row model
  (`parse_tracker`, `normalize_tracker`, `recorded_note_ids`,
  `queue_terminal`, `diff_row` semantics) after the specified G-T1
  importable-module refactor — it MUST NOT own parallel parser/normalizer
  semantics. Any reconcile mapping fix flows to generation for free; any
  fork is a spec violation (REQ-G5).
