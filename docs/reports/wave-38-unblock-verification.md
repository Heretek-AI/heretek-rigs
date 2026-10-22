# Verification report: wave-38-unblock (remediate-38-unblock)

Auditor: Independent Drift Guard (subagent). Commits under audit: `40bc8b5`
(implementation) + `79440dc` (evidence/QA record). Base: `69f2514`.
Worktree branch: `remediate/38-unblock`. `git status --short` is clean
(`scripts/__pycache__/` is gitignored per `.gitignore:6`).

## 1. Diff audit — every file justified, no forbidden edits

`git diff 69f2514..HEAD --stat` = 8 files, +1726/−1:
- `scripts/sweep-typed-blocks.py` (new, T2/T3/BU2/BU3/BU5/BU7)
- `scripts/park-typed-block.py` (new, T2/BU1/BU4)
- `tests/test_sweep_typed_blocks.py` (new, 35 tests, T6)
- `docs/ops/typed-external-block-runbook.md` (new, T4 — editable `docs/` only)
- `docs/reports/remediate-38-unblock-implementation.md` (new, T7)
- `docs/reports/qa-wave-38-unblock.md` + `docs/evidence/wave-38-unblock/red-proofs.log` (evidence commit)
- `Makefile` (1-line `test` target extension)

Zero files under `specs/ rigs/ rosters/ registry/`. `scripts/verify-rigs.sh`
untouched (no diff). Makefile change independently confirmed minimal and
non-masking: it only appends `tests/test_sweep_typed_blocks.py` to the
existing `test` target; the `verify` target is unchanged.

## 2. Sweep logic (read in full, 568 lines) — real predicates, fail-closed

- Read-only discovery allowlisted to `queue list|show|transitions --json`
  via `check_allowed()`; the ONLY live write is `update --state in-progress
  --reopen --note` (spec route). Single `apply_update` call site (line 487),
  guarded by `if dry_run` branch (lines 477–483).
- Fail-closed enumeration (all ambiguous paths resolve to stay-blocked):
  ambiguous/partial evidence → stay-blocked naming what is missing;
  malformed `SATISFIED:` → ignored + recorded evaluation; dangling
  verdict-qitem ref → stay-blocked + WARN naming the ref; daemon
  unreachable → `DataSourceError`, exit 2, no evaluations claimed;
  transitions-unreadable row → SKIP + stay-blocked; malformed/missing
  cursor file → `{}` (full re-evaluation; unparked rows are in-progress and
  skip, so no duplicate unpark); malformed transition entries (non-dict,
  null note) tolerated; park-time predicate alone never self-satisfies
  (post-park window starts after the park transition).
- Unpark path cannot fire accidentally: it requires an explicit operator
  invocation of the script in non-dry-run mode plus a satisfied predicate;
  `--dry-run` is proven write-free (S7 RED-proof + independent probe:
  cursor file never created, `main()` saves cursor only when `not
  dry_run`). The `--reopen` pilot risk is explicitly recorded with the exact
  fallback (drop `--reopen`, record daemon error, no other state verb).
- Structural incapacity for `state=done` is REAL, two layers, independently
  probed: `build_unpark_argv()` pins `in-progress` (line 142) and
  self-checks; `check_unpark_argv()` refuses any argv containing `done`
  (line 129) or any state ≠ `in-progress`. Probe confirmed the guard
  raises `RuntimeError` on a `state=done` argv.
- No network calls (only `subprocess` to `rig`), no secrets access, no
  `|| true`, no bare excepts (`except (OSError, json.JSONDecodeError)` is
  specific), no TODOs. Secrets scan over the full diff: CLEAN.

## 3. Park guard — predicate-less/timer-only rejection is real

`plan()` returns exit 2 with operator-visible stderr and `argv=None` (no
rig invocation possible) for predicate-less and malformed-predicate typed
parks, and for timer-only (`--wake-after` alone) typed parks. Accepted
paths require predicate + live wake (`--wake-watchdog` / `--sweep-covered`
/ live qitem in `--on`). Direct-`rig` bypass exists but is out-of-contract:
REQ-BU1 scopes rejection to "the runbook path" (observation O1, not a
finding — no repo-side mechanism can constrain the daemon binary).

## 4. Tests — 35 cases, spot-read 10+, bidirectional

Spot-read in both directions (each would fail if its gate were broken, as
QA's 12 RED-proofs demonstrate): `test_replay_w103_shape_unparks_with_spec_route`
(unpark-positive, asserts exact spec argv incl. evidence citation),
`test_rerun_is_idempotent_no_duplicate_unpark` (cursor/robustness),
`test_dry_run_reports_but_mutates_nothing`,
`test_sabotage_note_without_satisfaction_tokens_stays_blocked`,
`test_sabotage_rework_note_rearms_block`,
`test_dangling_verdict_qitem_ref_stays_blocked_and_names_ref`,
`test_pending_pass_assertion_stays_blocked` (live W2-06 false-positive shape),
`test_bare_seat_assertion_without_citation_stays_blocked`,
`test_park_predicate_alone_never_self_satisfies`,
`test_sweep_never_emits_done`. Fixture-only: sweep driven through
`FakeClient`, park wrapper exercised via `--dry-run`/pure `plan()` (one
subprocess test asserts `rig queue block` argv printed, exit 0, no daemon
needed). No daemon/live dependence in the suite.

## 5. Spec fidelity — all ADDED requirements + T1–T7 satisfied

- REQ-BU1/BU4: park guard + runbook §1 checklist. REQ-BU2: transitions-cursor
  sweep with triggers (a)+(b), unpark via spec route with evidence citation.
  REQ-BU3: `SATISFIED:` convention, malformed → ignored + recorded.
  REQ-BU5: audit trail on every evaluation, `--dry-run`, never-`done`,
  cursor idempotency. REQ-BU6: upstream URL recorded; sweep uses only
  today's verbs (grep: zero `satisfy`-verb references in scripts).
  REQ-BU7: W1-03/W1-04-shape replay unparks within one cycle (test + live
  dry-run WOULD-UNPARK t927/t1065).
- Deferred live pilot + watchdog wiring are EXPLICITLY deferred with exact
  manual commands (runbook §3 cadence ≤15 min + wiring suggestion, §4
  ordered pilot commands), not silently dropped. Acceptable per
  design ("operator-executed") and no-live-mutation record.
- Issue #38 (OPEN, confirmed via `gh`) gap — typed-external gates with no
  wake path — is exactly what the sweep closes; live-qitem/human legs
  untouched as spec'd.

## 6. Upstream issue independence

Sweep confirmed independent of the upstream `satisfy` request: no code path
references a `satisfy` verb; unpark uses only `update --state in-progress
--reopen`. (Upstream issue URL recorded in implementation report; remote
existence not re-verified from this worktree — out of scope for repo-side
correctness.)

## 7. Commands run by this auditor (real output, not trusted)

- `make verify` → `SUMMARY: 22 checks passed, 0 failed` (exit 0;
  LIVE-HEALTH advisory WARN only, Wave-1 gate untouched and green).
- `make test` → `Ran 42 tests ... OK` (7 render-seat + 35 sweep, exit 0).
- `openspec validate remediate-38-unblock` → valid (exit 0).
- Live read-only `--dry-run` (own cursor path) → `evaluated=9 unparked=0
  would-unpark=4 stay-blocked=5 skipped=12`, incl. W1-03 t927 + W1-04
  t1065-via-t928; cursor file not created; post-run `rig queue show`
  confirms both W1 rows still `blocked` (zero live writes).
- Anti-stub grep over both scripts + tests: CLEAN (one benign
  "pass-through" status string for non-typed parks, not a stub).

## 8. QA finding F1 — confirmed behavior-neutral, not upgraded

`NEGATIONS` tuple (sweep-typed-blocks.py:71) is defined once and referenced
zero times — `_word_hits` hardcodes its own negation set (`no|zero|without|
none|not`). Dead constant with no behavior impact: it is never read, so it
cannot alter any verdict; both `_word_hits` call sites behave identically
with or without it. Non-blocking observation; suggest removal in a
follow-up. Not a stub (no faked logic, no vacuous pass).

## Observations (non-blocking)

- O1: Park guard is wrapper-level; direct `rig queue block` bypasses it.
  In-contract (REQ-BU1 scopes to the runbook path), noted for awareness.
- O2: Operator-authority rule (`test_operator_verdict_without_citation_unparks`)
  lets operator SAT-notes unpark without citation — documented in runbook §2
  and tested; accepted as verdict-authority design, not fail-closed drift.

No blocking findings. All T1–T7 deliverables present, all gates green,
red-proofs non-vacuous (12 RED RC=1 + 3 documented structurally-green
superseded attempts), tree clean.

## 9. Re-audit of review-driven fixes (2026-10-22, wave-38-review-reaudit)

Auditor: Independent Drift Guard (re-audit subagent). Commits under audit:
`1d8e8a5` (seven review fixes) + `1acc6b1` (evidence record) on top of the
`40bc8b5`+`79440dc`+`acc9f4c` line. Base: `69f2514`. No commits made by this
auditor; `git status --short` shows only gitignored `scripts/__pycache__/`
regenerated by test runs (earlier `git status --short` output in this session
was empty apart from that).

### 9.1 Diff audit — all hunks justified, no forbidden edits

`git diff 69f2514..HEAD --stat` = 9 files (8 from the base implementation +
5 touched by `1d8e8a5`: `scripts/sweep-typed-blocks.py` +219/−?,
`scripts/park-typed-block.py` +27/−?, `tests/test_sweep_typed_blocks.py`
+233/−?, `docs/ops/typed-external-block-runbook.md` §3, and the 2-line
`qa-wave-38-unblock.md` line-37 URL fix). Zero diff under `specs/ rigs/
rosters/ registry/`; `scripts/verify-rigs.sh` untouched (confirmed: `git diff
69f2514..HEAD -- specs/ rigs/ rosters/ registry/ scripts/verify-rigs.sh`
empty). Makefile delta is the pre-existing 1-line `test`-target extension
from the base commit, not the review fix. The seven review items map to
reviewer requests + spec fidelity, no scope creep: (1) blocker-side trigger
leg (b) implements REQ-BU2 trigger (b), which was already in the spec text
("a note/transition lands on the blocker referenced by the predicate") but
missing from the code; (2–3) per-row fault isolation (`apply_update` +
blocker-fetch guards) harden REQ-BU5 fail-closed within T2/T6; (4–6) park
argv safety (`allow_abbrev=False`, empty-watchdog rejection, single
`--continuation` merge) harden REQ-BU1/BU4 within T2; (7) runbook §3 +
line-37 URL fix are docs-only (T4/T7). No new features, no new scope.

### 9.2 Behavior changes — read and independently probed

- Blocker triggers + `{row,blockers}` cursor migration: `blocker_qitem_refs`
  watches every `qitem-…` id cited in the row's notes (superset of the
  predicate-named blocker — conservative toward re-evaluation, never toward
  unpark). `_cursor_seen` normalisation probed with 11 corrupt/legacy shapes
  (None, int-as-entry, str, non-int row, non-dict blockers, non-int blocker
  values, missing key, list): zero crashes, all degrade to `(-1, {})` =
  full re-evaluation; evaluation itself stays fail-closed so re-evaluation
  cannot produce a false unpark (unpark still requires a satisfied
  predicate). `load_cursor` probed with 6 corrupt file contents + missing
  file: all yield `{}` or sanitised entries, never raise. Legacy flat entries
  (`{qid: int}`) normalise to `(int, {})`, biasing toward one extra
  re-evaluation, never a missed unpark. Safe.
- Fault isolation: independently reproduced QA B-b (first row's
  `apply_update` raising `DataSourceError` → row stay-blocked, absent from
  cursor, second row still unparked) and QA B-c (blocker-fetch raising →
  stay-blocked + named SKIP, cursor untouched, subsequent row processed).
  Both PASS with this auditor's own fixtures.
- Argv safety: `allow_abbrev=False` is set on the park parser (line 54);
  live probes: `--dry-ru/--dry-r/--sweep-covere/--wake-watchdo/--pred` all
  exit 2 at parse time; valid full-flag `--dry-run` invocation prints argv,
  exit 0. Runbook examples and all tests use full flags only (sole exception:
  the deliberate `--dry-ru` rejection test). No legitimate caller broken.
  Sweep-side parser (`build_parser`) has no `allow_abbrev=False`, but that is
  the safe direction there: prefix matching on the sweep can only err toward
  parsing `--dry-run`, never away from it. Not a finding.

### 9.3 Item-3 deviation — ACCEPT (own reasoning)

The programmer rejected exit-2 via `allow_abbrev=False` instead of aliasing
abbreviations. ACCEPT: an alias list enumerates a finite set of truncations
while `allow_abbrev=False` closes the whole class — every misspelling of any
long option fails at parse time (exit 2) before `plan()` can return an argv,
so no abbreviated flag can reach the `subprocess.run` live-write path (parse
failure → `SystemExit(2)` → `main` never executes; mocked-subprocess test
asserts `run` never called). Rejecting is strictly safer than aliasing here
because the catastrophic direction is a *dropped* `--dry-run` becoming a
live `rig queue block` — aliases cannot cover every truncation a tired
operator might type.

### 9.4 Commands run by this auditor (real output)

- `make verify` → `SUMMARY: 22 checks passed, 0 failed`, exit 0 (advisory
  live-health WARN only). `openspec validate remediate-38-unblock` → valid.
  `make test` → `Ran 50 tests ... OK` (42 base + 8 new).
- Secrets scan over `git diff 69f2514..HEAD` (secret-shaped patterns):
  CLEAN (only benign "satisfaction token" prose matches; no keys/URLs).

### 9.5 QA finding F1 — still behavior-neutral

`NEGATIONS` (sweep-typed-blocks.py:75) still defined once, referenced zero
times (`grep NEGATIONS` hits only the definition); `_word_hits` still
hardcodes its own smaller negation set. Dead constant, cannot alter any
verdict. Not upgraded; removal remains a follow-up nit.

No blocking findings. Review fixes are spec-faithful, independently
reproduced, and fully gated.

VERDICT: PASS
