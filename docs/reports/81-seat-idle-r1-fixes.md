# 81-seat-idle rework-1 fixes (PR #132 review findings) — Refs #81

Worktree: `.lane/trees/81-seat-idle`, branch `feat/81-seat-idle`.
All five findings verified against current code before editing. All FIXED.
No regeneration needed (generator inputs untouched — One Rule intact).
Nothing committed; coordinator commits. No pushes.

## Verdicts

### F1 — FIXED
**Finding:** pre-fix evidence around the DAEMON_SOURCE / recorded-source
checks must include a dummy daemon-origin handoff invocation and its
resulting source label; the frozen-evidence test must verify that captured
result, not marker absence alone.

**Evidence:** valid as stated — Transcript 3 of
`docs/evidence/81-seat-idle-prefix.md` (lines 70–87) asserted only marker
absence (`daemon:stuck-sweep marker present: False`,
`validate_handoff_source present: False`, `DAEMON_SOURCE present: False`)
plus `recorded source: operator`, with no invocation-to-result capture.
Added a dummy-invocation result block (validator absent on the unpatched
tree, so the operator label passes through with no relabel) and a new
frozen test pinning it. All V30 evidence markers kept byte-identical
(`reconcile exit: 0`, `idle-park signal: ABSENT`,
`park-to-wake attribution: ABSENT`, `daemon source rule: ABSENT`,
`recorded source: operator` — V30 green, see gates below).

**Diff:** `docs/evidence/81-seat-idle-prefix.md` — appended to Transcript 3:
```
validate_handoff_source present: False
handoff invocation result: recorded source operator (rule ABSENT, no relabel)
```
(with 2-line prose header); `tests/test_seat_idle_prefix.py` — new
`test_evidence_records_daemon_handoff_invocation_result` asserting both
lines. Full diff in git (`git diff` on those two files, +12/+13).

### F2 — FIXED
**Finding:** the `wake_ts` assignment in the parked-trail condition must
record a timestamp only when the note indicates a wake or release event;
a watchdog heartbeat or other note lacking idle-park prose must not count
as wake evidence. Parked-trail and unset-wake checks preserved.

**Evidence:** valid — `scripts/reconcile_model.py` line 646–647 set
`wake_ts` on ANY post-park non-idle-park note. Added `_WAKE_NOTE_RE`
(`wake|woken|woke|released?|resumed?|unparked?`) and gated the assignment.
Spot-verified: heartbeat-only trail → `wake_ts None`,
`park_to_wake_s None`; `watchdog release: owner woken` trail →
`wake_ts 2026-10-23T21:34:53.000Z`, `park_to_wake_s 53.0`. Existing
`test_attribution_reports_park_to_wake_vs_work` (wake note carries
`release`+`woken`) still green; full corpus green.

**Diff:** `scripts/reconcile_model.py` — new `_WAKE_NOTE_RE` + docstring
updates; the parked-trail branch now nests `if _WAKE_NOTE_RE.search(note)`
before assigning `wake_ts`. (See `git diff` hunk `@@ -644,10 +681,14 @@`.)

### F3 — FIXED (no spec/V30 conflict)
**Finding:** `render_diff` must handle the stalled-idle-park human-review
diff as review-only: show its review-routing proposal without the
`PROPOSED-CELL` paste-ready marker or the `converged` queue-note
suggestion. Other diff types unchanged.

**Evidence / conflict check (per caution):** no conflict. V30 asserts no
`PROPOSED-CELL`/queue-note output for idle-park (it checks markers,
relabel behavior, refusal guard, leaves, evidence lines, corpus floor —
all still green). The archived spec REQ-I2 requires the diff to
*route for human review* with attribution attached and to be
*report-only / never write state* — emitting `PROPOSED-CELL:::Route …
for human review` plus `Tracker row … converged:` contradicted that
(review + "converged" cannot both be true). `generate_trackers.py`
already renders idle-park as review-only (`WITHHELD`, `NEEDS-HUMAN-REVIEW`,
`SUGGESTED (not paste-ready)`, class outside `PASTE_READY_CLASSES`);
`render_diff` now matches. No test asserts `PROPOSED-CELL` for idle-park
(grepped `tests/test_seat_idle.py`, `tests/test_seat_idle_prefix.py` —
zero hits); the CLI test asserts `stalled-idle-park` + `park-to-wake` in
stdout, both still present via the header and attribution lines.

**Diff:** `scripts/reconcile_model.py` `render_diff` — early return for
`diff["class"] == "stalled-idle-park"` emitting header / reason /
tracker / queue / attribution + `NEEDS-HUMAN-REVIEW: TPM decide; …` +
`SUGGESTED (not paste-ready): {proposal}`. All other classes fall through
to the unchanged `PROPOSED-CELL` + queue-note block.

### F4 — FIXED (corpus holds)
**Finding:** non-work note filtering in `trail_has_work_action` (and the
same logic in `attribute_idle_latency`) must exclude a transition note
only when it contains known non-work events AND no work action, so mixed
notes remain eligible as work evidence.

**Evidence / corpus check (per caution):** valid and corpus-safe. Added
`_WORK_ACTION_RE` (`verdict|filed|files|QA PASS|PLACED|DONE`, grounded in
the S0/S1 corpus vocabulary) and shared `_is_non_work_only(note)` helper
used by both `trail_has_work_action` and the `work_ts` leg of
`attribute_idle_latency`. The standing conservative rule is preserved (a
note with no non-work event is still work). Spot-verified: mixed
`claimed; verdict recorded, findings filed` → work `True`; pure
`claimed`, handoff receipt, watchdog heartbeat → `False`. Full corpus
(596 tests incl. wave-4/77 suites that share `diff_row`) green — no
contradiction.

**Diff:** `scripts/reconcile_model.py` — new `_WORK_ACTION_RE` +
`_is_non_work_only`; `trail_has_work_action` and `attribute_idle_latency`
call it instead of bare `any(rx.search …)`. (See `git diff` hunks
`@@ -114,6 +114,38 @@`, `@@ -597,15 +629,18 @@`, `@@ -628,7 +663,9 @@`.)

### F5 — FIXED (file/line mapping note)
**Finding:** update the pre-fix evidence line to report the wake interval
as +84s from claim and +53s park-to-wake; leave both `WAKE_TS` constants
unchanged.

**Evidence:** the finding cites `tests/test_seat_idle_prefix.py:56`, which
is the `WAKE_TS = "2026-10-23T21:34:53.000Z"` constant line itself — and
that file's documentation carries no interval prose (its latency comment
cites only the #81 audit ranges 8–31s / 22–53s, which are issue-level, not
fixture-level). The only line reporting a fixture wake interval is the
pre-fix evidence line `docs/evidence/81-seat-idle-prefix.md:23`, and its
arithmetic was wrong: claim 21:33:29 → wake 21:34:53 is **84s** (not
53s), park 21:34:00 → wake is **53s** (not 22s). Fixed that line;
verified both `WAKE_TS` constants byte-identical
(`tests/test_seat_idle_prefix.py:56`,
`tests/test_seat_idle.py:58`, still `2026-10-23T21:34:53.000Z`).
Out-of-scope observation (NOT changed, minimal-diff rule):
`docs/reports/81-seat-idle-implementation.md:18` repeats `wake +53s`
without a basis — left for the coordinator to decide.

**Diff:** `docs/evidence/81-seat-idle-prefix.md:22-24` —
`(+53s, +22s park-to-wake)` → `(+84s from claim, +53s park-to-wake)`.

## Gates (all green, uncommitted tree)

- `python3 -m unittest tests.test_seat_idle tests.test_seat_idle_prefix` → 34 tests OK (24 + 10 incl. new F1 test). Exit 0.
- Full corpus `python3 -m unittest discover -s tests` → 596 tests OK. Exit 0.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 38 checks passed, 0 failed`, V30 PASS listed (24 corpus tests). Exit 0.
- `python3 scripts/generate-rigs.py --check-idempotent` → exit 0, no regenerated files (`git status` shows only the 3 intended edits).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`. Exit 0.
- Secret hygiene: new evidence/test lines contain no 40+ `[A-Za-z0-9_-]` runs (prefix frozen test + V30 evidence grep both green).

## Files changed (3, uncommitted)

- `scripts/reconcile_model.py` (F2/F3/F4)
- `docs/evidence/81-seat-idle-prefix.md` (F1/F5)
- `tests/test_seat_idle_prefix.py` (F1: +1 test)
