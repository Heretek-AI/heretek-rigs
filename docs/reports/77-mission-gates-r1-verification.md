# Independent drift-guard verification — 77-mission-gates rework cycle 1 (Refs #77)

Auditor: independent adversarial auditor (drift-guard seat). Worktree
`.lane/trees/77-mission-gates-r1`, branch `fix/77-mission-gates-r1`, tip
`4104a0d`, cycle base `00f78bc` (2 commits). Every claim below was read
from disk or executed by the auditor; nothing is inherited from the prior
PASS (`docs/reports/77-mission-gates-verification.md`), the rework report
(`docs/reports/77-mission-gates-rework-1.md`), the QA report
(`docs/reports/77-mission-gates-r1-qa.md`), or the pre-existing content of
this file (zero verdict weight). No commits, no pushes; sabotage temporary
and fully reverted (byte-identity proven by `cmp`). No file modified except
this report.

## 1. Production wiring analysis (core question)

Rework claim: `check_recovery_dismissal` was dead code in production (call
sites only in `tests/test_mission_gates.py` and the V29 block) and is now
wired: `run_sweep` retains the flag-time snapshot in the sweep report and
`request_recovery_dismissal` is the close-time gate. Auditor verified each
sub-claim.

### 1a. Wiring diff is additive-only

`git diff 00f78bc..HEAD -- scripts/sweep-typed-blocks.py` is exactly two
hunks (auditor read the full diff):

1. New function `request_recovery_dismissal(client, recovery_id,
   flagged_qitem, flagged_snapshot, log_lines=None)` after
   `check_recovery_dismissal` (+52 lines). It calls only
   `client.fetch_show` (read), `snapshot_row_state` (pure),
   `check_recovery_dismissal` (pure-or-raise), `_redact_for_log`
   (redaction). No `run_rig`, no `apply_update`, no `subprocess`, no file
   write, no new write verb, no `check_allowed`/`check_unpark_argv` change.
2. `run_sweep`: report gains `"recovery_guards": {}` key (+1 line) and the
   stay-blocked branch gains the 5-line retention block
   (`report["recovery_guards"][qid] = {"flagged_qitem", "flagged_snapshot"}`)
   (+9 lines with comments).

No existing line modified: unpark path (`build_unpark_argv` →
`client.apply_update`), stay-blocked logging, dry-run, cursor/idempotency
logic all byte-identical. Neighbor suite `tests.test_sweep_typed_blocks`
54/54 GREEN confirms no semantic change to existing paths (auditor re-ran).

### 1b. Close-path enumeration (every path that can close a stuck-recovery item)

Exhaustive search of `scripts/sweep-typed-blocks.py` (auditor grepped):

| # | Close-capable path | Guarded? |
|---|---|---|
| 1 | `RigClient.apply_update(argv)` — the ONLY live write in the module, gated by `check_allowed` → `check_unpark_argv`, which refuses any `--state` ≠ `in-progress` and any argv containing `done`. It can only unpark to `in-progress --reopen`; it **cannot** close to done/complete/closed by construction. | N/A (incapable of closing; D2 structural) |
| 2 | `run_rig` / `fetch_list` / `fetch_show` / `fetch_transitions` — read-only (`list\|show\|transitions` + `--json` enforced). | N/A (reads, no state change) |
| 3 | `request_recovery_dismissal` (new) — performs no write; returns data or raises `RecoveryDismissalRefused`. The CALLER performs the close. | IS the guard |
| 4 | Human / future-tooling closer — necessarily out-of-repo: no in-repo close-to-done hook exists (by design: allowlist refuses close writes, D2 forbids bot close-to-done). The runbook Flow C documents the call order (retained snapshot → `request_recovery_dismissal` → close only on permit). | Guarded by convention + retained snapshot |

Verdict: **no unguarded in-repo close path exists.** The one live write
cannot close; the new gate cannot write. There is no second close path to
have left unguarded. (Observation O1, not a finding: enforcement of the
human call order is conventional — no code can force a human to call the
gate before closing. This is the maximum the flow supports without
inventing a close hook that would itself violate D2; the alternative would
be worse. The snapshot the gate consumes IS production-retained, so a
compliant closer cannot bypass it accidentally.)

### 1c. Fail-closed direction on unreadable rows

Auditor read `request_recovery_dismissal:310-321`: `fetch_show` raising
`DataSourceError` appends a redacted refusal line and raises
`RecoveryDismissalRefused` — refuse, never permit. Pinned by
`test_close_time_gate_refuses_when_flagged_row_unreadable` (auditor re-ran,
OK) and behaviorally confirmed in the QA-R5a GREEN transcript (zero
writes).

### 1d. D2 safety rule still holds

`git diff 00f78bc..HEAD -- scripts/` grep for `update --state`,
`queue (update|close)`, `--state (done|complete|closed)` → matches are
prose only (new docstring: "except the unpark route (update --state
in-progress --reopen)" and "forbids any bot close-to-done"). Zero new
write verbs; zero allowlist changes; the `done`-refusal in
`check_unpark_argv:124-134` untouched. Auditor's behavioral drives
(sabotaged and restored) both show `writes: []` / `updates == []`. **D2
holds: no path writes done/complete/closed as a result of this wiring.**

## 2. Drift analysis (cycle base 00f78bc..HEAD)

- `git diff 00f78bc..HEAD --name-only` (7 files): `docs/evidence/
  77-mission-gates-runbook.md`, `docs/evidence/77-mission-gates/
  red-proofs.log`, `docs/reports/77-mission-gates-qa.md`,
  `docs/reports/77-mission-gates-r1-qa.md` (new),
  `docs/reports/77-mission-gates-rework-1.md` (new),
  `scripts/sweep-typed-blocks.py`, `tests/test_mission_gates.py`.
  Functional changes confined to the three H1–H3 findings (runbook queue
  form, QA pipe entities, sweep wiring + 3 tests). Nothing under
  `openspec/` (empty diff), `specs/`, `rigs/`, `rosters/`, `registry/`,
  `fleet/`. `scripts/verify-rigs.sh` untouched → V29 and V1–V28 text
  untouched by this cycle (verify re-run: `SUMMARY: 37 checks passed, 0
  failed`, V29 PASS citing 19 corpus tests).
- Registry: zero diff (no regen needed — no generator inputs changed;
  consistent with the rework claim).
- Commits: 2, both carry `Refs #77` in subject/body; none carries
  `Closes`/`Fixes`/`Resolves` near `#77` (issue stays open by design).
  No `--force`, no push (worktree branch only; auditor ran no
  push/fetch affecting remotes; `git status -sb` shows unpushed branch,
  clean tree).

## 3. Spec trace (REQ-M1…M4)

| Req / scenario | Status this cycle | Evidence (auditor-observed) |
|---|---|---|
| REQ-M1 charter closure ownership + both scenarios | UNREGRESSED (no charter/leaf/generator diff this cycle) | V29 PASS (9 leaves + markers) in auditor's verify re-run |
| REQ-M2 B2-pattern flagged + gated-waiting quiet | UNREGRESSED (no `reconcile_model.py`/`generate_trackers.py` diff) | `test_mission_gates` StalledAwaitingGate tests OK in auditor re-run |
| REQ-M3 dismissal-without-change refused (production flow) | HOLDS — now through the wired path | Auditor spot-check (§5): retained snapshot → REFUSED, zero writes |
| REQ-M3 dismissal-with-change allowed (production flow) | HOLDS | Auditor spot-check: advanced row → permitted, zero writes |
| REQ-M3 unreadable-row fail-closed | HOLDS | Code read (§1c) + corpus test OK |
| REQ-M4 V29 + corpus (19 tests, FAIL-ONLY priors intact) | HOLDS | Verify 37/37; corpus 19/19; prefix 6/6; red-proofs.log priors byte-preserved (R1 + QA-R5 appended only) |

## 4. Anti-stub / secrets (auditor re-ran)

- Anti-stub over `git diff 00f78bc..HEAD`: grep for
  `TODO|FIXME|XXX|HACK|stub|placeholder|NotImplemented|skipTest|
  @unittest.skip|pytest.mark.skip|\|\| true|except.*:\s*pass` → **empty**.
  No skips in the 3 new tests; no swallowed errors (guard raises typed
  `RecoveryDismissalRefused`; unreadable branch raises, never returns
  permit). No vacuous checks: every critical assertion is sabotage-pinned
  (R1-a guard neuter → 1 failure; R1-b retention removed → 3 errors;
  QA-R5a call neutered → PERMITTED (BAD); auditor spot-check §5 repeats
  R5a independently).
- Secrets: auditor re-ran `grep -rE '[A-Za-z0-9_-]{40,}'` on the binding
  evidence paths (`docs/evidence/77-mission-gates-prefix.md`,
  `docs/evidence/77-mission-gates-runbook.md`) → **no output, exit 1
  (clean)**. All new log lines interpolate `_redact_for_log` (auditor
  confirmed: 3 call sites in the new function, all through `redact(...)`).
  Dummy fixture ids only (`qitem-STUCK-01`, `recovery-QA-01` family).

## 5. QA spot-check (auditor's own sabotage, fully reverted)

Auditor neutered the wired guard CALL in a working-copy edit only (the
`check_recovery_dismissal(...)` invocation in
`request_recovery_dismissal` replaced by a direct
`{"dismissal": "permitted", ...}` return; `check_recovery_dismissal`
itself intact — the QA-R5a shape):

- Sabotaged: real `run_sweep` on the `stuck_typed_row` fixture → retained
  keys `['flagged_qitem', 'flagged_snapshot']` → `request_recovery_
  dismissal` on the byte-identical row → `UNCHANGED-DISMISSAL: PERMITTED
  (BAD)`, writes `[]`. B2 bury-the-stall outcome restored through the
  production flow — the gate refuses BECAUSE of the wired call,
  non-vacuous.
- Restored (`cp` pre-sabotage copy back, `cmp` byte-identical) →
  `UNCHANGED-DISMISSAL: REFUSED (GOOD)` + `CHANGED-DISMISSAL: permitted
  (GOOD)` (owner-advanced row), writes `[]` both ways.
- `git status --short` clean after restore (empty; only this report
  outstanding at close). `git diff --stat` empty before writing this
  report.

Full battery auditor re-ran at tip `4104a0d`: verify `37 passed, 0
failed` (V29 PASS); `tests.test_mission_gates` 19/19 OK;
`tests.test_sweep_typed_blocks` 54/54 OK;
`tests.test_mission_gates_prefix` 6/6 OK; `audit_loop.py --self-test`
`SELF-TEST PASSED`. (`make test` 561-family verified by QA at `94ec266`
with identical tree content for code+tests — tip `4104a0d` adds only this
cycle's QA report; auditor ran the three constituent suites directly
rather than repeating the 110 s full battery.)

## 6. Scope

Zero daemon/upstream/live-fleet changes (name-only diff contains none;
`fleet/`, `registry/`, `specs/`, `rigs/`, `rosters/`, `openspec/` all
empty). All commits `Refs #77`; no push/force locally. Live-mission proof
remains out of scope by design (D3, issue stays open).

## 7. Findings

No numbered findings. F-series empty:

- No stub, vacuous check, failing command, missing deliverable, hand-edit
  violation, secret leak, drift, or unguarded close path found.
- Observation O1 (coordinator note, no action): the human call order into
  `request_recovery_dismissal` is conventional, not code-enforced — the
  maximum supportable without violating D2 (see §1b).

Files inspected (read fully or diffed): `AGENTS.md`,
`openspec/specs/mission-gates/spec.md`,
`docs/reports/77-mission-gates-rework-1.md`,
`docs/reports/77-mission-gates-r1-qa.md`,
`docs/reports/77-mission-gates-verification.md` (prior, zero weight),
`docs/evidence/77-mission-gates/red-proofs.log`,
`scripts/sweep-typed-blocks.py` (full file + full cycle diff),
`tests/test_mission_gates.py` (SweepRecoveryClient + new tests),
`docs/evidence/77-mission-gates-runbook.md` + `docs/reports/
77-mission-gates-qa.md` (H1/H2 diffs), full `00f78bc..HEAD` name-only +
stat + commit bodies. Commands executed: verify-rigs, three unit suites,
audit self-test, stub/secrets greps, write-verb/close-path greps, live
sabotage/restore cycle with `cmp` proof. Unverified: nothing in cycle
scope — full 561 `make test` inherited from QA (constituent suites
re-run here); live-mission proof out of scope by design.

VERDICT: PASS
