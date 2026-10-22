# Implementation report: remediate-38-unblock (stage wave-38-unblock)

## Stage / scope
- Stage: `wave-38-unblock`, worktree branch `remediate/38-unblock` (from
  origin/main @ 69f2514, clean).
- Implemented ONLY `openspec/changes/remediate-38-unblock/tasks.md` (T1–T7).
  No other remediate-* package touched. No merges, no pushes.

## Deliverables
1. **`scripts/sweep-typed-blocks.py`** (new, executable) — repo-side
   re-evaluation sweep (REQ-BU2/BU3/BU5/BU7). Read-only discovery via
   allowlisted `queue list|show|transitions --json`; the ONLY live write is
   the spec'd unpark route `update --state in-progress --reopen` with an
   evidence-citing audit note. Transitions-cursor idempotency, `--dry-run`
   (zero live writes, zero cursor writes), fail-closed evaluation,
   `state=done` structurally impossible (builder refuses it).
2. **`scripts/park-typed-block.py`** (new, executable) — park-time guard
   wrapper over `rig queue block` (REQ-BU1/BU4). Rejects predicate-less
   typed parks and timer-only typed parks with an operator-visible error and
   no HELD row; predicate travels in the park transition note (the sweep's
   carrier). `--dry-run` prints the exact rig argv, executes nothing.
3. **`docs/ops/typed-external-block-runbook.md`** (new) — seat park-time
   checklist, `SATISFIED:` convention, sweep operation/cadence/fail-closed
   table, deferred live-pilot steps. Editable `docs/` only; zero hand-edits
   under `specs/ rigs/ rosters/ registry/` (verified via git status).
4. **`tests/test_sweep_typed_blocks.py`** (new, 35 tests) — fixture-only,
   no daemon, no live-queue mutation. Covers: T1 baseline pins the recorded
   W1-03 stuck shape; W1-03/W1-04-shape replay unparks via the exact spec
   route; rerun emits no duplicate; dry-run mutates nothing; malformed
   `SATISFIED:` stays blocked; ambiguous evidence stays blocked naming what
   is missing; dangling verdict-qitem ref stays blocked naming the ref;
   rework note re-arms; negated "zero rework owed" does not re-arm;
   watchdog "pass still pending" restatement does not satisfy (live-data
   red-proof); seat bare assertion without citation does not satisfy;
   operator verdict unparks; park predicate alone never self-satisfies;
   never-`done` scan over all emitted argv; daemon-unreachable claims
   nothing; park wrapper rejections/acceptances all in `--dry-run`.
5. **`Makefile`** — `test` target extended to run
   `test_render_seat.py` + `test_sweep_typed_blocks.py`. `verify-rigs.sh`
   untouched (22-check baseline preserved).

## Ground facts verified live (read-only, 2026-10-22)
- W1-03 (`qitem-20261022052407-3d618a4431583b97`,
  `blockedOn=external:operator-placement-qa-gate`) and W1-04
  (`qitem-20261022052409-291190744e33d1fe`,
  `blockedOn=external:qa-operator-gate-verdict`) still `blocked` post-note.
- `update` without `--state` never changes state; `resolve` covers leg-1
  human parks only; no satisfy/unblock verb exists; live-qitem `--on`
  blockers self-wake, typed gates do not.
- Live `--dry-run` (reads only): 9 typed rows evaluated → 4 WOULD-UNPARK
  (W1-03 t927, W1-04 t1065-via-t928, W1-08 t1101, W2-06 t1102 — all genuine
  operator/seat verdict evidence), 5 STAY-BLOCKED with named gaps/re-arms.
  A first-pass false positive on a watchdog "runner pass still pending"
  restatement was caught by this dry-run and fixed (pending-state negation +
  evidence-citation rule) with regression tests — the dry-run earned its keep.

## Upstream request (REQ-BU6 / T5)
- Filed: **https://github.com/mvschwarz/openrig/issues/1785** — `queue
  satisfy` feature request with the W1-03/W1-04 evidence. The sweep uses only
  today's CLI verbs and does not depend on it.

## No-live-mutation record
- Zero `queue create/send/update/block/resolve` invocations against the live
  daemon by this stage. Evidence: all tests run against `FakeClient`
  fixtures; `park-typed-block.py` exercised only via `--dry-run` (argv
  printed, nothing spawned); `sweep-typed-blocks.py` against live data only
  via `--dry-run` (read verbs `list`/`transitions` + `--json`; no `update`
  call observed — report shows `unparked=0`); cursor file defaulted to
  `/tmp` and dry-run wrote nothing.
- First live unpark is a DEFERRED MANUAL step (runbook §4): dry-run review,
  then a real run with a durable cursor path. One known pilot risk recorded:
  if the daemon rejects `--reopen` on the non-terminal `blocked` state, drop
  `--reopen` for that run and record the exact daemon error — no other state
  verb.

## Acceptance outputs (exact commands, worktree root)
- `openspec validate remediate-38-unblock` → `Change
  'remediate-38-unblock' is valid` (exit 0).
- `make test` → `Ran 42 tests ... OK` (exit 0: 7 render-seat + 35 sweep).
- `python3 -m unittest tests/test_live_health.py` → `Ran 21 tests ... OK`
  (exit 0; Wave-1 suite unregressed).
- `make verify` → `SUMMARY: 22 checks passed, 0 failed` + `LIVE-HEALTH
  WARN (advisory, exit 0)` (exit 0; Wave-1 gate untouched and green).
- Anti-stub grep over all new files → CLEAN (no TODO/stub/skip/pass-through).

## Skipped / deferred
- Live pilot unpark runs (deferred manual per above; reads only in this stage).
- Watchdog-job/cron wiring for sweep cadence (documented recommendation in
  runbook §3; creating live jobs would mutate live state — operator-executed).
- No `satisfy` verb adoption (upstream #1785 may never land; sweep is
  independent by design).

## Self-audit notes
- `verify-rigs.sh` deliberately untouched: the 22 checks are
  audit-baselined, and the new tests ride the `make test` target + the
  report instead of renumbering the gate.
- Heuristic residual (documented in runbook §2): legacy-note evaluation is
  keyword+authority based. Fail-closed direction is enforced by tests, but
  operators should prefer the exact `SATISFIED:` record for new parks —
  that path is structural, not heuristic.
- File naming: report uses the tasks.md T7 filename
  (`remediate-38-unblock-implementation.md`) rather than the stage-slug
  variant; content covers the stage-report requirements (claims, skips,
  no-live-mutation record).
