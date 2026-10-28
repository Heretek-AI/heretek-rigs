# Design: remediate-39-reconcile

## Why diff-first, generate-deferred (option (b) now, (a) later)
Generation (trackers-as-a-view) requires settling row-ownership (who may
edit what), queue-note append semantics (the 7 appended notes were prose,
not status), and parent-rollup rules — a design tree of its own. The diff
command needs none of that: it reads two sources, prints mismatches, and
leaves every judgment call (is this PARKED row legitimately parked?) with
the TPM. It converts toil (discovery) into review (approval) on day one
and produces the drift corpus that will justify generation later. The
follow-up generate change MUST consume this diff spec's row model rather
than reinventing it.

## Row model (non-binding sketch)
Parse tracker tables with a real markdown-table parser (not regex):
columns Slice / Owner / Output / Slice qitem / Status. Normalize status
cells to a small enum (STAGED, DISPATCHED, PARKED, QA PASS, PLACED, DONE,
CLOSED + free-text note). Queue side: qitem id → (status, latest notes,
transition ids). Diff = enum mismatch OR queue-side transition newer
than the tracker's recorded note. Proposal = full replacement Status cell
(`QA PASS + PLACED <n>/<m> canonical (queue note <id>)`) so the TPM sees
exact text to paste.

## Fail-closed modes
- Tracker file missing/unparseable → named failure, not "0 diffs" (an
  empty diff MUST mean verified-in-sync, never failed-to-read).
- Queue entry missing for a tracker row → diff of class
  `tracker-row-without-qitem` (suggest removal/closure review), never
  dropped.
- Queue listing unreachable → hard failure; no partial-diff output that
  could be mistaken for convergence.

## Risks
- Status-cell prose varies per row (e.g. W1-03's "PARKED … blocker
  satisfied" annotations): normalizer keeps unknown prose as
  `OTHER(<raw>)` and still diffs it against queue state — over-reporting
  beats silent agreement.
- Depends on machine-readable queue output: consumes the explicit `--json`
  form (per #44's documented workaround), so #44's default-output fix is
  complementary, not a prerequisite.
