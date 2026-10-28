# Independent drift-guard verification — 77-mission-gates rework cycle 2 (Refs #77)

Auditor: independent adversarial auditor (drift-guard seat). Worktree
`.lane/trees/77-mission-gates-r2`, branch `fix/77-mission-gates-r2`, tip
`08f97b7`, cycle base `e7a53be` (2 commits). Prior PASS
(`docs/reports/77-mission-gates-r1-verification.md`) revalidated, zero
weight inherited. No commits, no pushes; auditor sabotage temporary and
fully reverted (`cmp` byte-identical). No file modified except this report.

## 1. The fix (M4, one token)

`git diff e7a53be..HEAD -- scripts/sweep-typed-blocks.py` is exactly one
line (auditor read the full diff):

- `scripts/sweep-typed-blocks.py:315`: `f"time: {exc}; ..."` →
  `f"time: {redact(str(exc))}; ..."` inside the `except DataSourceError`
  branch of `request_recovery_dismissal`. Nothing else in the hunk changed.

Verified byte-for-byte beyond the token:

- Message shape unchanged: prefix `recovery-dismissal-refused:
  {redact(recovery_id)} for flagged row {redact(flagged_qitem)} (flagged
  row unreadable at close time: ...; owner action required, never
  auto-close)` identical on both sides; only the `exc` interpolation
  gained `redact(str(...))`.
- Raise behavior unchanged: `raise RecoveryDismissalRefused(...)` at
  lines 317-321 byte-identical (raised text carries no `{exc}` before or
  after — confirmed by diff and by the new test asserting zero
  `[A-Za-z0-9_-]{40,}` runs in the raised message).
- Control flow unchanged: `try fetch_show / except DataSourceError:
  append + raise / snapshot / try check / except Refused: re-log + raise /
  append permitted + return` — no branch added, removed, or reordered.
- `redact` is the genuine choke point, not a lookalike: line 306
  `redact = _seed_rig_mod()._redact_for_log` (same binding as line 271 in
  `check_recovery_dismissal`); `_seed_rig_mod` loads
  `scripts/seed-rig.py` via importlib (lines 221-239, cached singleton);
  `_redact_for_log` at `scripts/seed-rig.py:211` replaces every
  `[A-Za-z0-9_-]{40,}` run with `…redacted…` and truncates at 200 chars.
  No local `def redact`, no shadow, no duplicate regex in the sweep module.

## 2. Residual-leak question (key audit)

### 2a. Enumeration — every remaining raw interpolation in `scripts/sweep-typed-blocks.py`

Auditor grepped `{exc}`, `log_lines.append`, `sys.stderr.write`, and all
f-string interpolations in the file. Post-fix raw sites (file:line):

| # | Site | Raw interpolation | Kind |
|---|---|---|---|
| R1 | `scripts/sweep-typed-blocks.py:164` | `{RIG_BIN}`, `{exc}` (FileNotFoundError text) in `raise DataSourceError(...)` | exception constructor, not a log line |
| R2 | `scripts/sweep-typed-blocks.py:168-171` | `{proc.stderr.strip()[:300]}` in `raise DataSourceError(...)` | **taint source**: raw daemon stderr (≤300 chars) embedded in the exception |
| R3 | `scripts/sweep-typed-blocks.py:175` | `{exc}` (JSONDecodeError str: line/col, no doc body) in `raise DataSourceError(...)` | exception constructor |
| R4 | `scripts/sweep-typed-blocks.py:810-813` | raw `{qid}` + raw `{exc}` in `SKIP {qid}: transitions unreadable (...)` | log line, stay-blocked site 1 of 4 |
| R5 | `scripts/sweep-typed-blocks.py:825` → logged at `:832-835` | raw `{ref}: {exc}` buffered into `unreadable[]`, joined into `SKIP {qid}: blocker qitem(s) unreadable (...)` (plus raw `{qid}`) | log line, stay-blocked site 2 of 4 |
| R6 | `scripts/sweep-typed-blocks.py:872-876` | raw `{qid}` + raw `{exc}` in `SKIP {qid}: blocker evaluation incomplete (...)` | log line, stay-blocked site 3 of 4 |
| R7 | `scripts/sweep-typed-blocks.py:893-898` | raw `{qid}`, raw `{row.get('blockedOn')}`, raw `{exc}` in `STAY-BLOCKED ... unpark write failed (...)` | log line, stay-blocked site 4 of 4 |
| R8 | `scripts/sweep-typed-blocks.py:883-886` | raw `{qid}`, raw `{blockedOn}`, raw `{verdict['evidence_citation']}` in `WOULD-UNPARK` | log line (dry-run/unpark path) |
| R9 | `scripts/sweep-typed-blocks.py:902-905` | raw `{qid}`, raw `{blockedOn}`, raw `{verdict['evidence_citation']}` in `UNPARKED` | log line (unpark path) |
| R10 | `scripts/sweep-typed-blocks.py:908-910` | raw `{qid}`, raw `{blockedOn}`, raw `{verdict['reason']}` in `STAY-BLOCKED` (retention site) | log line |
| R11 | `scripts/sweep-typed-blocks.py:966-969` | raw `{exc}` in `sys.stderr.write("sweep: data source unreachable: ...")` | stderr, top-level `fetch_list` failure |

Fixed this cycle (not residual): `:315` now `{redact(str(exc))}`; `:328`
re-logs an already-redacted refusal string; `:330-333` permitted line
interpolates only `redact(...)` ids; `:273-277` guard raise fully
redacted. All wave-new log paths are now redacted.

### 2b. Secret-reachability per site

- `{exc}` / DataSourceError content (R4, R5, R6, R7, R11): **plausibly
  secret-bearing.** R2 is the proof: `run_rig` embeds raw daemon stderr
  (`proc.stderr.strip()[:300]`) into the exception, and `rig queue show /
  list / transitions` stderr is daemon-controlled output. A bearer/token
  echoed in stderr (or a URL-with-token, credential-bearing path) flows
  verbatim into every downstream `{exc}` log line. The M4 sabotage
  transcript demonstrates the shape exactly (45-char run verbatim in the
  log). These five log sites are reachable with secret material.
- `{qid}` / `{ref}` (R4–R7, R10): **structurally id-shaped, not
  secret-capable in practice.** Values are `row.get("qitemId")` /
  blocker refs cited by the row (`qitem-*` ids). A hostile daemon could
  in principle return an arbitrary string here, but under the wave's
  threat model (honest daemon, secret material arrives via error
  text/stderr, not via id fields) they cannot carry a 40+ bearer run
  without breaking every downstream consumer; no evidence of such shape
  exists in fixtures or code. Not a redaction vector.
- `{blockedOn}` / `{verdict['reason']}` / `{verdict['evidence_citation']}`
  (R8, R9, R10): **operator/tracker-derived prose, not daemon-secret
  bearing.** `blockedOn` is the typed-blocker cell (`blocked:gate:...`
  family); reason/citation are built by `evaluate_row` from fixed
  templates + blocker keys + tracker note excerpts. A human could paste
  a secret into a tracker note (out of scope for log redaction — that
  secret already lives in the tracker), but these fields do not
  transport daemon stderr/bearer material. Low secret capacity; no
  bearer-shaped runs observed in any fixture or log.
- R1/R3 constructors: path/line-col info only; negligible secret
  capacity, and they are not log lines (they feed R4–R7/R11 via R2's
  stderr embedding).

### 2c. Verdict on scope

**The M4 fix's scope (refusal path only) is sufficient for this cycle;
no new finding. The five secret-reachable residual sites (R4–R7, R11)
are a pre-existing gap outside the wave diff, recorded as Observation O2.**

Reasoning, per the binding rule (a finding counts only if (i) reachable
with secret material AND (ii) introduced or left unguarded by THIS
wave's own code):

- (i) holds for R4–R7/R11 (via R2's stderr embedding) but (ii) fails:
  all seven raw-`{exc}` lines exist byte-identical at cycle base
  `e7a53be` (`git show e7a53be:... | grep -n "{exc}"` returns the same
  R1/R3/R4/R5/R6/R7/R11 set; the cycle diff touches none of them).
  They belong to the sweep's original `run_sweep`/`main`/`run_rig`
  landing, not to the mission-gates wave, whose new code is
  `check_recovery_dismissal` + `request_recovery_dismissal` + the
  retention block. The wave's secrets rule ("every NEW log path through
  `_redact_for_log`", rework-1 §4, r1-verification §4) covers exactly
  the new function — now fully redacted post-fix.
- The wave neither introduced the residuals nor widened them: no new
  raw interpolation was added by this wave's code (auditor diffed every
  new line), and the retention block adds no log line at all.
- REQ-M4 as archived (`openspec/specs/mission-gates/spec.md:56-70`)
  mandates the V29 gate + corpus + FAIL-ONLY/prefix proofs; it names no
  pre-existing-log redaction sweep. The "redaction guarantee" the M4
  fix satisfies is the wave's corpus-asserted behavioral property on
  the refusal path (V29 block redaction assertion + new corpus test),
  both green. AGENTS.md secrets hard rules (no real credentials in
  commands/files/reports/audit output) are met: evidence-path secrets
  grep clean (§5), dummy fixture runs only, no real key material
  anywhere in the diff.
- A broader redaction sweep of R4–R7/R11 (routing all `run_sweep`
  `{exc}` lines through `_redact_for_log`) would be a defensible
  hardening follow-up, but it is **not** a cycle finding: it predates
  the wave, is outside the wave diff, and was explicitly noted
  (not filed) by QA (`r2-qa.md:39` awareness note). Filing it here
  would fail-close the wrong change. Recorded as O2 for the
  coordinator, no action required of this cycle.

## 3. Drift analysis (cycle base `e7a53be..HEAD`)

- Name-only (7 files): `docs/evidence/77-mission-gates/red-proofs.log`
  (R2 + QA-R6 append, priors byte-preserved — auditor read all 367
  lines), `docs/reports/77-mission-gates-r1-qa.md` (row-8 scope wording
  only), `docs/reports/77-mission-gates-rework-1.md` (line-35
  idempotence wording only), `docs/reports/77-mission-gates-rework-2.md`
  (new), `docs/reports/77-mission-gates-r2-qa.md` (new),
  `scripts/sweep-typed-blocks.py` (the one-token fix),
  `tests/test_mission_gates.py` (+45-line redaction test, 19→20 tests).
- Functional change confined to the one-token fix + one corpus test.
  Docs edits are precision-only (auditor diffed both: r1-qa row 8 now
  scopes `recovery_guards` to the evaluated non-unpark site; rework-1
  line 35 now records the 16-file provenance churn + revert — both match
  code truth / observed behavior).
- Empty diff (auditor verified): `docs/reports/
  77-mission-gates-r1-verification.md` (M2 skip left it untouched),
  `openspec/`, `specs/`, `rigs/`, `rosters/`, `registry/`, `fleet/`,
  `scripts/verify-rigs.sh` → V29/V1–V28 text untouched (verify re-run:
  `SUMMARY: 37 checks passed, 0 failed`, V29 PASS citing 20 tests).
- Registry: zero diff (no regen needed — no generator inputs changed).
- Commits: 2 (`131ec04` fix + `08f97b7` test/evidence record), both
  carry `Refs #77`; grep for `closes|fixes|resolves` over cycle bodies
  → empty (issue stays open by design). No `--force`, no push
  (worktree branch only; auditor ran no push/fetch).

## 4. Spec trace (REQ-M1…M4)

| Req | Status this cycle | Evidence (auditor-observed) |
|---|---|---|
| REQ-M1 charter closure ownership | UNREGRESSED (no charter/leaf/generator diff) | V29 PASS, 9 leaves + markers, in auditor's verify re-run |
| REQ-M2 B2 flagged / gated-quiet | UNREGRESSED (no reconciler diff) | StalledAwaitingGate corpus OK (20-suite green) |
| REQ-M3 refusal / allowance / unreadable fail-closed | HOLDS, now redacted | New redaction test + auditor sabotage §6; neighbor suite 54/54 |
| REQ-M4 V29 + corpus + FAIL-ONLY priors | HOLDS | Verify 37/37; corpus 20/20; prefix proofs intact; red-proofs.log append-only |

## 5. Anti-stub / secrets (auditor re-ran)

- Anti-stub over `git diff e7a53be..HEAD`: grep for
  `TODO|FIXME|XXX|HACK|stub|placeholder|NotImplemented|skipTest|
  @unittest.skip|pytest.mark.skip|\|\| true` → **empty (exit 1)**. No
  `except: pass` in sweep/tests (exit 1). New test has no skip, no
  vacuous assertion (fails without the fix — §6 RED shows the raw
  45-char run verbatim).
- Secrets: auditor re-ran
  `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md
  docs/evidence/77-mission-gates-runbook.md` → **no output, exit 1
  (clean)**. Only secret-shaped runs in-cycle are the dummy `"A"*45`
  scratch runs inside the test + red-proof transcripts (never a real
  bearer; 0600 scratch, uncommitted).

## 6. QA spot-check (auditor's own sabotage, fully reverted)

Auditor copied the fixed file to `/tmp/opencode/audit-r2-fixed.py`,
replaced the single `{redact(str(exc))}` with `{exc}` (raised message
untouched), and ran the new test:

- RED: `test_close_time_unreadable_log_line_redacted` FAILED —
  `AssertionError: 'redacted' not found in '... flagged row unreadable
  at close time: daemon blew up, bearer leaked: AAAA...(45-char run); ...'`
  (raw run verbatim in the log line; raised message stayed clean —
  leak was log-line-only, non-vacuous).
- GREEN: `cp` back + `cmp` byte-identical → `Ran 20 tests / OK`;
  neighbor `tests.test_sweep_typed_blocks` 54/54 OK; verify
  `37 passed, 0 failed`; `audit_loop.py --self-test` SELF-TEST PASSED.
- `git status --short` clean after restore (empty before writing this
  report).

## 7. Scope

Zero daemon/upstream/live-fleet changes. All cycle commits `Refs #77`;
no push/force locally. Live-mission proof out of scope by design.

## 8. Findings

No numbered findings. F-series empty:

- No stub, vacuous check, failing command, missing deliverable,
  hand-edit violation, secret leak, drift, or unguarded wave-new close
  path found.
- Observation O2 (coordinator note, no action this cycle): five
  pre-existing raw-`{exc}` log sites (R4–R7, R11: `:811`, `:825/:834`,
  `:874`, `:896`, `:968`) can transport daemon-stderr secret material
  via the R2 (`:168-171`) embedding. Predates the wave, outside the
  wave diff, explicitly out of M4 scope. Candidate hardening follow-up
  only — not a cycle defect.

Files inspected: `AGENTS.md`, `openspec/specs/mission-gates/spec.md`,
`docs/reports/77-mission-gates-rework-2.md`,
`docs/reports/77-mission-gates-r2-qa.md`,
`docs/reports/77-mission-gates-r1-verification.md` (prior, zero weight),
`docs/evidence/77-mission-gates/red-proofs.log` (full),
`scripts/sweep-typed-blocks.py` (full file + full cycle diff +
`e7a53be` baseline grep), `scripts/seed-rig.py:200-220` (choke point),
`tests/test_mission_gates.py` (new test diff), full `e7a53be..HEAD`
name-only + stat + commit bodies. Commands executed: verify-rigs,
mission-gates + sweep suites, audit self-test, stub/secrets greps,
`{exc}`/redact greps, baseline comparison, live sabotage/restore with
`cmp` proof. Unverified: full 562 `make test` inherited from QA
(constituent suites re-run here: 20/20 + 54/54); live-mission proof out
of scope by design.

VERDICT: PASS
