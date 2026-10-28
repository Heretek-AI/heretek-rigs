# QA verdict — wave-41-policy-verifier (issue #41)

Stage: `wave-41-policy-verifier` · change-id `remediate-41-policy-verifier`
Implementation commit under test: `d8fdded`
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-41-policy-verifier`
Date (UTC): 2026-10-22 · Verifier: QA seat (sabotage-only; nothing committed, merged, or pushed)

## Verdict: QA-CLEAN (no blocking findings)

## 1. Checks run (all on the unmodified tree unless noted)

- `make verify` → PASS — `SUMMARY: 25 checks passed, 0 failed`, exit 0; then
  `live-health.py` advisory exit 0 (only pre-existing heartbeat/idleness WARN/SKIP on seats).
- V1–V8 identical → PASS — `git diff HEAD~1 -- scripts/verify-rigs.sh` shows zero removed
  lines; the diff is 35 pure insertions (appended `== V9 ==` block with exactly one `ok()`).
- `python3 -m unittest discover -s tests` → PASS — 124 tests, OK.
- `openspec validate remediate-41-policy-verifier` → PASS — valid.
- V9 gate present → PASS — `[PASS] Policy-text verifier (issue #41) green ...
  (tests/test_policy_verifier.py 16 tests pass)`.
- T1–T5 contract → PASS — every numbered requirement exercised (see sabotage battery).
- Forbidden dirs untouched → PASS — `git show --stat HEAD` lists no
  `specs/`/`fleet/`/`rigs/`/`rosters/`/`registry/` files.

Count note: 28 `[PASS]` lines in raw `make verify` output = 25 gated checks in the SUMMARY
+ 3 `live-health.py` advisory lines (outside the SUMMARY count). The 25 = 24 pre-existing
(loop-expanded) + 1 new V9. `grep -c "ok("` undercounts because several checks increment
`passes` inside loops (e.g. per-rig).

## 2. Red-proof sabotage (7-step protocol; evidence: docs/evidence/wave-41-policy-verifier/red-proofs.log)

- S0 production-code sabotage (non-vacuity proof): early `return` at top of
  `Verifier.check_toml` → `python3 -m unittest tests.test_policy_verifier` → FAILED
  (failures=4), exit 1. Restored via `git checkout -- scripts/policy-verifier.py`,
  byte-identical, tracked status clean.
- (a) synthetic stale `cast_lossy` TOML → exit 1, `UNKNOWN LINT 'clippy::cast_lossy'
  at stale.toml:6`; corrected `cast_possible_truncation` → exit 0.
- (b) `run: pnpm eslint .` with `lint` script present → exit 1,
  `DUPLICATE RUN COMMAND ... citing 'lint'`; reconciled `run: pnpm lint` → exit 0.
- (c) `run: pnpm lintt` (no such script) → exit 1,
  `UNRESOLVABLE SCRIPT 'lintt' at pipelines/ci.yml:8` naming file:line+command.
- (d1) snapshot copy with `cast_possible_truncation` removed + fixed file → exit 1
  (legit file now FAILS — snapshot load-bearing, not decorative).
- (d2) `--expect-pin fixture-toolchain-2` vs pin-1 snapshot → exit 1, STALE (fail-closed).
- (d3) missing snapshot file → exit 1, MISSING KNOWN-LINT SNAPSHOT ... refusing (fail-closed).
- (e1) unparseable TOML → exit 1, `UNREADABLE POLICY 'bad.toml' (invalid TOML: ...)`.
- (e2) unparseable workflow YAML → exit 1, `UNREADABLE WORKFLOW ... (invalid YAML: ...)`.
- (f1) `run: cargo frobnicate --locked` → exit 1, `UNKNOWN CARGO SUBCOMMAND 'frobnicate'`.
- (f2) staged `.cargo/config.toml [alias] xit` + `run: cargo xit` → exit 0; alias entry
  removed → exit 1 (`UNKNOWN CARGO SUBCOMMAND 'xit'`) — alias lookup load-bearing.
- (g) snapshot with pin line removed + `--expect-pin` → exit 1,
  `STALE ... (snapshot pin 'None' != ...)` — no default-allow.

No vacuous checks found. Every acceptance check turns RED under minimal targeted sabotage.

## 3. Live-grounding honesty — CONFIRMED (mission repo read-only, never written)

- `src/w3-06-staging/root-lints-reference.toml:28` = `cast_lossy = "deny"` — matches the
  proposal anchor and the fixture stanza shape (`[workspace.lints.clippy]` tail entry).
- Live `Cargo.toml:38` = `cast_possible_truncation = "deny"` — matches the corrected anchor.
- `pipelines/w2-07-ci-reconciled.yml` carries the proven steps (`run: pnpm lint`,
  `format:check`, `typecheck`; `run: pnpm unit` + `cargo fmt`/`clippy`/`test`).
- Mission repo (`/home/john/Projects/heretek-asset-manager`) only read (`sed`/`grep`);
  `git status` there shows zero tracked modifications (only pre-existing untracked strays),
  no commits, no pushes.

## 4. Makefile delta review — PASS (additive, non-masking)

- `.PHONY` line only appends `policy-verifier`; one new target block running
  `python3 ./scripts/policy-verifier.py --staged`. No existing target touched; the name
  shadows no file or existing target.

## 5. Snapshot + toolchain-pin grounding — PASS (spot-checked vs the real toolchain)

Snapshot (`scripts/policy-verifier.known-lints.txt`, `pin: fixture-toolchain-1`, matching
`scripts/policy-verifier.toolchain-pin`) vs installed rustc 1.95.0 + clippy
(`clippy-driver -W help`):
1. `clippy::cast_possible_truncation` — REAL (pedantic group). 
2. `clippy::unwrap_used` — REAL (restriction group).
3. `rust::rust_2018_idioms` — REAL (`rust-2018-idioms` group in `rustc -W help`).
4. `clippy::cast_lossy` — ABSENT (0 hits) — correctly omitted.

## 6. Report-filename deviation — reasoned, NON-BLOCKING

tasks.md T6 names `docs/reports/remediate-41-policy-verifier-implementation.md`; delivered is
`docs/reports/wave-41-policy-verifier-implementation.md`. The acceptance contract is
REQ-P1–REQ-P4 plus the T1–T5 testability clauses — no requirement constrains the report
filename, and T6's parenthetical "(files changed, verification outputs)" is fully satisfied
by the delivered content. The delivered name follows the stage evidence convention
(`docs/reports/<stage>-*.md`), consistent with every sibling report, and nothing references
the tasks.md-suggested path. A filename suggestion is not acceptance. Deviation accepted.

## 7. Final tree state

`git status --short` shows nothing modified except untracked sanctioned paths:
`docs/evidence/wave-41-policy-verifier/red-proofs.log` and this report. No commits, merges,
or pushes. Production and test code untouched since `d8fdded`.

## Findings

Numbered blocking findings: none. QA-CLEAN.
Observations (non-blocking): O1 report-filename deviation (accepted, see section 6);
O2 stale check-count strings in worktree AGENTS.md ("expect: 23") and old V-block comments
("22 -> 23") — pre-existing doc drift outside this stage's touch set.

---

# Re-verification — rework cycle 1 (commit 8dc4d57, 2026-10-22)

Stage/wave id: `wave-41-rework-1-verify` · commit under test: `8dc4d57`
(`fix(41-policy-verifier): complete snapshot from live tables, wire pin freshness by default`)
on top of `dea5b74` + `d8fdded` (`git log --oneline -4` confirmed).
Binding findings: `docs/reports/wave-41-policy-verifier-verification.md` §Findings (F1 major + F2 minor).
Rework claim: `docs/reports/wave-41-rework-1-implementation.md`.
Evidence: `docs/evidence/wave-41-policy-verifier/red-proofs.log` §RE-VERIFY (verbatim outputs).
Sabotage-only; nothing committed, merged, or pushed.

## Verdict: QA-CLEAN (both findings remediated, no vacuous checks, no regressions)

## 1. Full suite (unmodified tree)

- `make verify` → PASS — `SUMMARY: 25 checks passed, 0 failed` (V9: 19 tests pass), exit 0;
  `live-health.py` advisory exit 0 (only pre-existing heartbeat/idleness WARN/SKIP).
- `openspec validate remediate-41-policy-verifier` → PASS — valid, exit 0.
- `python3 -m unittest discover -s tests` → PASS — 127 tests, OK, exit 0.

## 2. F1 red-proofs (complete snapshot) — all PASS

- F1a: live corrected mission `Cargo.toml`, bare scan → exit 0
  (`all 1 staged policy file(s) resolve`). The 2 false positives are gone.
- F1b: live stale `root-lints-reference.toml` → exit 1 with EXACTLY ONE finding
  (`clippy::cast_lossy` at `:28`); `rust::` names quiet. True positive preserved, no masking.
- F1c (sabotage): `rust::missing_docs` removed from checked-in snapshot →
  `PolicyVerifierLiveTableTests` FAILED (failures=2), exit 1. Restored via
  `git checkout`, diff-confirmed byte-identical, 3/3 OK after. Proves the
  vendored tests guard the fix (not vacuous).
- F1d (fidelity, read-only): tomllib parse of live vs vendored fixture —
  `[workspace.lints.rust]` and `[workspace.lints.clippy]` keys AND levels match
  exactly (only trailing comments dropped, parse-irrelevant). Fixture is faithful.

## 3. F2 red-proofs (pin freshness by default) — all PASS

- F2a: stale-pin snapshot (`stale-pin-0`), NO pin flags → exit 1
  `STALE KNOWN-LINT SNAPSHOT ... 'stale-pin-0' != ... 'fixture-toolchain-1'`.
  The pre-fix silent pass is closed; the bare `make policy-verifier` path is enforced
  via `DEFAULT_PIN_FILE`.
- F2b: matching pin, bare invocation → exit 0. Good-file path unaffected.
- F2c (sabotage): precedence guard (`if expect_pin is None`) removed so the
  default pin-file unconditionally overrides explicit `--expect-pin` →
  both pre-existing pin tests FAILED (failures=2), exit 1, in opposite
  directions (stale passes silent; matching goes STALE). Restored via
  `git checkout`, byte-identical, 5/5 OK after. Precedence is load-bearing.
  Note: `--expect-pin`/`--pin-file` are argparse-mutexed, so precedence means
  an explicit `--expect-pin` skips the default pin-file read.

## 4. Regression (original red-proofs, anti-masking) — all PASS

- R1 stale `cast_lossy` TOML → exit 1 naming `clippy::cast_lossy` + file:line.
- R2 `run: pnpm eslint .` with `lint` script → exit 1 `DUPLICATE RUN COMMAND` citing `lint`.
- R3 unparseable TOML → exit 1 `UNREADABLE POLICY` (fail-closed).

## 5. Hygiene — PASS

- Mission repo: `git diff --stat` empty (read-only scans only; pre-existing untracked strays only).
- `scripts/verify-rigs.sh`: zero removed lines vs `0a3db37` (V1–V8 byte-identical);
  V9 block carries exactly one new `ok()`; `Makefile` additive only
  (`.PHONY` token append + one new target block, no existing target touched).
- Forbidden dirs (`specs/ rigs/ rosters/ registry/ fleet/`): zero files in diff.
- `git status --short`: only this report and `red-proofs.log` modified (uncommitted, as instructed).

## Findings

Numbered blocking findings: none. QA-CLEAN.
Vacuous checks: none — every acceptance check turned RED under minimal targeted sabotage
(F1c snapshot-line removal, F2c precedence-guard removal, plus R1/R2/R3 regression battery).
---

# Re-verification — review round 2 (commit 3513e47, 2026-10-22)

Stage/wave id: `wave-41-review2-reverify` · commit under test: `3513e47`
(`fix(41-policy-verifier): address PR review - index authority, expr placeholder,
builtins, quoting, cargo context`) on top of `627b3b4` + `8f9da0e` + `8dc4d57`
(`git log --oneline -5` confirmed).
Must read: worktree `AGENTS.md`, `openspec/changes/remediate-41-policy-verifier/specs/`,
`tasks.md` (F1/F2 regression: live corrected table exit 0, live stale fires only
cast_lossy, stale pin bare exit 1). Sabotage-only edits (all reverted via
`git checkout -- <file>`); nothing committed, merged, or pushed.

## Verdict: QA-CLEAN (all new behaviors verified, no vacuous checks, no regressions)

## 1. Full suite (unmodified tree)

- `make verify` → PASS — `SUMMARY: 25 checks passed, 0 failed` (V9 now: 34 tests pass),
  exit 0; `live-health.py` advisory exit 0 (only pre-existing heartbeat/idleness WARN/SKIP).
- `openspec validate remediate-41-policy-verifier` → PASS — valid, exit 0.
- `python3 -m unittest discover -s tests` → PASS — 142 tests, OK, exit 0.

## 2. RED-PROOFS for each NEW behavior (evidence: red-proofs.log §REVIEW-2) — all PASS

- (a) Index authority: unstaged worktree snapshot breakage (`pin: wrong-pin`, uncommitted)
  → staged run still exit 0 (index wins); staged snapshot edit adding
  `clippy::new_hotness` honored (exit 0). Sabotage (worktree-read forced in staged
  mode) → `MISSING KNOWN-LINT SNAPSHOT ... (no lint entries parsed)`, exit 1 —
  behavior changes, index path load-bearing. Restored, status clean, 7/7 staged tests OK.
- (b) Snapshot honesty: `curated subset` headers present in BOTH files
  (known-lints.txt:3, toolchain-pin:3), both disclaim toolchain capture and document
  the manual refresh process. Pin-mismatch re-proof: stale-pin-9 snapshot, no pin
  flags → exit 1 `STALE KNOWN-LINT SNAPSHOT` (F2 mechanism intact).
- (c) Expressions: `echo ${{ a || b }}` single segment, no finding (exit 0);
  `pnpm ${{ matrix.script }}` skipped, no UNRESOLVABLE (exit 0);
  `pnpm lint ${{ matrix.args }}` still resolves (exit 0). Sabotage (placeholder
  substitution removed) → `pnpm ${{ matrix.script }}` FAILED exit 1
  (`UNRESOLVABLE SCRIPT 'matrix.script'`), and direct probe `pnpm ${{ a || b }}`
  → exit 1 (`UNRESOLVABLE SCRIPT 'a'`, split at `||`). Restored → exit 0, 3/3 OK.
- (d) Builtins: `npm test` with-script exit 0; without-script exit 0 no UNRESOLVABLE;
  `npm t` ≡ test; `yarn workspace foo build` exit 0; `yarn workspace foo bogus`
  exit 1 naming `bogus`. Sabotage (`test` removed from PM_DEFAULT_COMMANDS) →
  scriptless `npm test` FAILED exit 1 (`UNRESOLVABLE SCRIPT 'test'`), while
  with-script/alias paths stay green (precise). Restored, 5/5 OK.
- (e) Quoting: `"pnpm eslint ."` → exit 1 DUPLICATE citing lint (double, single,
  and interior-escape variants). Sabotage (quote-blind parsing restored) → all 3
  quoting tests FAILED with exit-0 silence (DUPLICATE missed). Restored, 3/3 OK.
- (f) Cargo context: staged workflow + committed-not-staged `.cargo/config.toml`
  alias → `cargo xit` resolves exit 0; `cargo frobnicate` → exit 1 UNKNOWN (control).
  Sabotage (config dropped from index context) → `cargo xit` FAILED exit 1
  (`UNKNOWN CARGO SUBCOMMAND 'xit'`). Clean-tree full-suite output contains ZERO
  `.cargo/config` strings (grep exit 1); context config entries route through
  `load_aliases` only (policy-verifier.py:983-987), never `check_toml`. Restored, OK.
- (g) Nitpick: `write_snapshot` default derives from `read_checked_in_pin()`
  (comment-tolerant); 34/34 module tests OK. Sabotage (derivation forced to
  `sabotage-pin`) → FAILED failures=26 (`STALE ... 'sabotage-pin' !=
  'fixture-toolchain-1'`). Default is derived, not hardcoded. Restored, 34/34 OK.

No vacuous checks: every new behavior turns RED under minimal targeted sabotage.

## 3. F1/F2 regression — all PASS

- F1a live corrected `Cargo.toml`, bare → exit 0 (`all 1 staged policy file(s) resolve`).
- F1b live stale `root-lints-reference.toml`, bare → exit 1 with EXACTLY ONE finding
  (`clippy::cast_lossy` at `:28`; `1 finding(s)`).
- F2 stale-pin bare → exit 1 STALE (see section 2(b)).
- Mission repo (`/home/john/Projects/heretek-asset-manager`): read-only scans,
  `git diff --stat` empty (tracked tree untouched).

## 4. Scope — PASS

Fix commit `3513e47` touches exactly the 4 intended files
(`scripts/policy-verifier.known-lints.txt`, `scripts/policy-verifier.py`,
`scripts/policy-verifier.toolchain-pin`, `tests/test_policy_verifier.py`);
zero files under `specs/`/`fleet/`/`rigs/`/`rosters/`/`registry/`.

## 5. Final tree state

`git status --short` shows nothing modified except the sanctioned evidence paths:
`docs/evidence/wave-41-policy-verifier/red-proofs.log` (appended §REVIEW-2) and this
report (appended review-round-2 section). Production and test code untouched since
`3513e47`; all sabotage reverted (per-item `git checkout`, status clean each time).
No commits, merges, or pushes.

## Findings

Numbered blocking findings: none. QA-CLEAN.
Vacuous checks: none.
