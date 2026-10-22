# Verification — wave-41-policy-verifier (issue #41)

Stage: `wave-41-policy-verifier` · change-id `remediate-41-policy-verifier`
Commits under audit: `d8fdded` (implementation) + `dea5b74` (evidence: red-proofs + QA report)
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-41-policy-verifier`
Auditor: independent drift-guard (no fixes, no commits). Date (UTC): 2026-10-22.

## 1. Spec & contract inventory

Normative contract: `openspec/changes/remediate-41-policy-verifier/specs/policy-verifier/spec.md`
(REQ-P1…REQ-P4) + `tasks.md` T1–T6. `proposal.md`/`design.md` are context.
`AGENTS.md` binding rules checked: no hand-edits under `specs/ rigs/ rosters/ registry/`;
`verify-rigs.sh` V1–V8 append-only (V9 pattern).

## 2. Diff audit — PASS (hygiene)

`git diff 0a3db37..HEAD --name-only` (9 files, all justified by T1–T6):
`Makefile`, `scripts/policy-verifier.py` (new, 884 lines), `scripts/policy-verifier.known-lints.txt`
(new), `scripts/policy-verifier.toolchain-pin` (new), `scripts/verify-rigs.sh`,
`tests/test_policy_verifier.py` (new, 16 tests), 2 reports + 1 red-proofs log.
No `specs/ rigs/ rosters/ registry/ fleet/` files touched — regeneration correctly not required.
`scripts/verify-rigs.sh`: **0 removed lines** (`grep -c '^-[^-]'` = 0); the V9 block is 35 pure
insertions with exactly one `ok()`. `Makefile`: additive only (one `.PHONY` token + one target
block, no existing target touched). `git status --short` in the worktree is clean.

## 3. Implementation read-through — real parsing, offline, no auto-fix — PASS

`scripts/policy-verifier.py` fully read (884 lines): genuine TOML/YAML parsing (`tomllib`,
`yaml.safe_load`), line-scan cross-checked against the parsed document (comment/string-literal
false-positive guard), shell-aware `run:` segmentation. Imports are stdlib + PyYAML only;
`subprocess` invokes local `git diff/show/ls-files` exclusively — no network, no `PATH`/toolchain
probing, no `node_modules`/`target` descent. No writes to policy files anywhere (only reads).
No `TODO/FIXME`, no `|| true`, no bare `except:`; the five `except Exception` sites all convert to
fail-closed `PolicyError` (exit 1), except one intentional TOML→plaintext fallback inside
`read_toolchain_pin` (`scripts/policy-verifier.py:437-438`) whose failure still surfaces as
`UNREADABLE TOOLCHAIN PIN`. Stale-pin (`STALE KNOWN-LINT SNAPSHOT`), missing snapshot
(`MISSING ... refusing to resolve`), unparseable TOML/YAML (`UNREADABLE ...`) all exit 1.
Fail-closed paths enumerated and confirmed by test + CLI runs.

## 4. Commands re-run — PASS

- `make verify` → `SUMMARY: 25 checks passed, 0 failed` (24 pre-existing + 1 new V9), then
  `live-health.py` advisory exit 0 (only pre-existing heartbeat/idleness WARN/SKIP). V9 line:
  `[PASS] Policy-text verifier (issue #41) green ... (tests/test_policy_verifier.py 16 tests pass)`.
- `openspec validate remediate-41-policy-verifier` → valid.
- `python3 -m unittest discover -s tests` → 124 tests, OK.
- Secrets scan over `git diff 0a3db37..HEAD` (secret/token/key patterns) → only benign
  substrings (`tokenize`, `tokens`); no secret-shaped strings. Implementation/QA agree, and the
  scan was re-run, not trusted.
- Mission repo (`/home/john/Projects/heretek-asset-manager`) opened read-only only
  (`sed`/`grep`/verifier scans); `git diff --stat` there is empty (only pre-existing untracked
  strays) — untouched. Worktree `git status --short` clean.

## 5. QA spot-checks independently reproduced — PASS (synthetic level)

- Stale synthetic TOML (`cast_lossy`) → exit 1, `UNKNOWN LINT 'clippy::cast_lossy'` with exact
  file:line; corrected (`cast_possible_truncation`) → exit 0. Matches QA red-proofs §(a).
- `rustc -W help` confirms `unsafe-code` and `missing-docs` are REAL toolchain lints;
  `clippy-driver -W help` confirms `cast-possible-truncation` real and no `cast-lossy` lint —
  QA §5 grounding spot-check reproduces.
- S0 non-vacuity is credible: QA's early-return sabotage of `check_toml` produced 4 test
  failures (named tests in red-proofs.log), i.e. the lint tests are not vacuous. The 16 tests
  assert on diagnostic content (names/lines), run fixture-only in `/tmp`, and cover both
  directions (RED stale/typo/bogus-cargo + GREEN reconciled/alias/builtin).

## 6. Report-filename deviation — RULING: accept, non-blocking

`tasks.md` T6 suggests `docs/reports/remediate-41-policy-verifier-implementation.md`; delivered is
`docs/reports/wave-41-policy-verifier-implementation.md`. The normative spec (REQ-P1…REQ-P4)
constrains no filename, and T6's parenthetical "(files changed, verification outputs)" is fully
satisfied by the delivered content. The delivered name follows the stage evidence convention
(`docs/reports/<stage>-*.md`) used by every sibling wave, and nothing references the
tasks.md-suggested path. A filename suggestion is not acceptance. Deviation accepted (concurs
with QA §6).

## Findings (blocking)

### F1 — Checked-in known-lint snapshot is incomplete: the CORRECTED live `Cargo.toml` FALSE-FAILS, violating REQ-P1's "Corrected live table passes" scenario and T1
- Spec clause: `openspec/changes/remediate-41-policy-verifier/specs/policy-verifier/spec.md:21-25`
  ("Given the live `Cargo.toml:38` (`cast_possible_truncation = "deny"`), when the verifier runs,
  then that entry passes") and `tasks.md:8-12` (T1 testable: "scanning live `Cargo.toml` passes").
- Defect: `scripts/policy-verifier.known-lints.txt:14-21` ships a 7-entry minimal subset that omits
  `rust::unsafe_code` and `rust::missing_docs`, both present in the real corrected live table
  (mission `Cargo.toml:28-29`, same `[workspace.lints.rust]` block that carries the `:38`
  `cast_possible_truncation` entry the spec names).
- Evidence (read-only, re-runnable):
  `python3 scripts/policy-verifier.py /home/john/Projects/heretek-asset-manager/Cargo.toml --known-lints scripts/policy-verifier.known-lints.txt`
  → exit 1 with `UNKNOWN LINT 'rust::unsafe_code' at ...Cargo.toml:28` and
  `UNKNOWN LINT 'rust::missing_docs' at ...Cargo.toml:29`.
  Both names are REAL toolchain lints (`rustc -W help` lists `unsafe-code` and `missing-docs`),
  so these are false positives, not true findings.
- Why the suite stays green: `tests/test_policy_verifier.py:38-50` synthesizes a clippy-ONLY
  stanza (`STALE_CLIPPY_STANZA`); neither it nor any test reproduces the live file's
  `[workspace.lints.rust]` section, so no test ever scans the real corrected table. The
  implementation report's "PASSED on the corrected stanza" claim (§"Claims and proof") holds only
  for the synthetic fragment, not the spec-named live file.
- Consequence: on the actual artifacts the verifier cannot do its core job cleanly — the stale
  reference file fires on `clippy::cast_lossy` at `:28` (true positive) but confounded by the same
  two false positives (`:18`, `:19` on the real stale file), and the corrected file it MUST pass
  exits 1. The acceptance criterion "scanning live `Cargo.toml` passes" is FALSE as shipped.
- Remediation (for the implementer, not the auditor): add every live-table name
  (`rust::unsafe_code`, `rust::missing_docs`, plus an audit of all live tables incl. crate
  manifests) to the snapshot — or record the FULL pinned-toolchain capture the snapshot header
  already promises — and add a test that scans the complete real live table text (vendored
  read-only copy incl. the `[workspace.lints.rust]` section) asserting exit 0; re-record red-proofs.

### F2 — Stale-snapshot-pin check is opt-in: the REQ-P3 `make policy-verifier` path bypasses the design-mandated freshness failure
- Contract clause: `openspec/changes/remediate-41-policy-verifier/design.md:15-21` ("on
  toolchain-pin bump, a mismatch between snapshot pin and repo toolchain pin MUST fail with
  'snapshot stale, refresh'").
- Defect: `scripts/policy-verifier.py:756-769` performs the comparison ONLY when the caller passes
  `--expect-pin`/`--pin-file` (default `None` → no check), and the `Makefile:87-88`
  `policy-verifier` target runs bare `--staged` without `--pin-file`. An operator relying on `make
  policy-verifier` after a toolchain-pin bump gets a silent pass on a stale snapshot.
- Mitigating fact (why minor, still a finding): the authoritative gate is safe — the V9
  `scripts/verify-rigs.sh` block passes `--pin-file .../policy-verifier.toolchain-pin`, and the
  `--expect-pin` tests prove the mechanism works. The gap is the unwired default path.
- Remediation: default `--pin-file` to the checked-in `scripts/policy-verifier.toolchain-pin`
  (or add `--pin-file` to the Makefile target) so every invocation enforces freshness.

## Observations (non-blocking)

- O1 — Check-count prose drift is pre-existing and outside this stage's touch set: worktree
  `AGENTS.md` says "23 checks", `proposal.md` says "22", actual pre-existing count is 24
  (25 SUMMARY minus V9). No renumbering/rewording occurred in the diff. Not a finding.
- O2 — REQ-P1's authority order ("local toolchain first, snapshot fallback") vs the implemented
  snapshot-only authority is a deliberate, code-docstring- and report-documented deviation that
  matches the stage grounding rule (deterministic, reviewable-as-diff; brief confirms no
  runner-toolchain path may exist — verified: none exists). Recommend amending the spec sentence
  to snapshot-authoritative rather than changing code. Not a finding.
- O3 — Module docstring exit-code note (`scripts/policy-verifier.py:47-50`: "2 = usage or
  environment error (unknown snapshot file, git failure)") is stale: those paths return 1 via
  `PolicyError`; only `--staged`-with-paths and bad-path return 2. Doc trivia. Not a finding.

## Verdict rationale

Diff hygiene, offline fail-closed behavior, test non-vacuity (synthetic level), command outputs,
secrets handling, and mission-repo intactness all reproduce clean. But F1 violates an explicit
spec scenario on the exact live files the change exists to adjudicate, with the suite masking it
via synthetic-only fixtures; F2 leaves a design-MUST freshness failure unwired on the shipped
`make` target. Per the severity rule (missing/simplified deliverable = FAIL), the stage cannot pass.

> Historical verdict (initial audit 2026-10-22, SUPERSEDED by the re-audit below): FAIL

---

# Re-audit — rework cycle 1 (2026-10-22, commits `8dc4d57` + `8f9da0e`)

Stage/wave id: `wave-41-rework-1-reaudit`. Commits under audit: `8dc4d57`
(`fix(41-policy-verifier): complete snapshot from live tables, wire pin freshness by default`)
+ evidence commit `8f9da0e` on top (`git log --oneline -4` confirmed:
`8f9da0e`, `8dc4d57`, `dea5b74`, `d8fdded`). Auditor: independent drift-guard
(no fixes, no commits). Prior FAIL report above is history; O1/O2/O3 already
ruled non-findings and are not re-litigated. Re-verification claims
spot-checked independently (not trusted).

## R1. F1 resolution — CLEARED

- Live corrected mission `Cargo.toml` with the CHECKED-IN snapshot, re-run read-only:
  `python3 scripts/policy-verifier.py /home/john/Projects/heretek-asset-manager/Cargo.toml --known-lints scripts/policy-verifier.known-lints.txt`
  → exit 0 (`all 1 staged policy file(s) resolve`). The two false positives
  (`rust::unsafe_code`, `rust::missing_docs`) are gone.
- Live stale `src/w3-06-staging/root-lints-reference.toml` with the checked-in
  snapshot → exit 1 with EXACTLY ONE finding (`clippy::cast_lossy` at `:28`);
  no `rust::` findings. True positive preserved, no masking.
- Fixture fidelity (read-only byte/parse compare): live vs
  `tests/fixtures/policy-verifier/live-corrected-lints.toml` — `[workspace.lints.rust]`
  and `[workspace.lints.clippy]` key sets match exactly; all levels match
  (only trailing comments dropped, parse-irrelevant).
- Snapshot coverage audited read-only: every name in both live tables is in
  `scripts/policy-verifier.known-lints.txt` (`snapshot-missing-from-live: NONE`).
  The `workspace = true` claim verified: `apps/web/src-tauri/Cargo.toml` carries
  only `[lints] workspace = true` (zero names); `src/w1-08-staging/Cargo.toml`
  carries no `[lints]` table (comment only). No other `[workspace.lints.*]`
  tables exist in the live root (sections: `clippy`, `rust` only).
- Non-vacuity spot-check (independent sabotage, QA §F1c reproduced): removed
  `rust::missing_docs` from the checked-in snapshot →
  `PolicyVerifierLiveTableTests` FAILED (failures=2), exit 1. Restored from
  backup, sha256 (`49e0ce1e…`) matches pre-sabotage; `git status` clean after.
  The vendored tests guard the fix.

## R2. F2 resolution — CLEARED

- `scripts/policy-verifier.py:741-742`: `--pin-file` now defaults to
  `str(DEFAULT_PIN_FILE)` (`scripts/policy-verifier.toolchain-pin`);
  `main` applies it whenever `--expect-pin` is absent
  (`if expect_pin is None and args.pin_file is not None`). Freshness is the
  default, not opt-in.
- End-to-end bare path: stale-pin snapshot (`stale-pin-0`), NO pin flags → exit 1
  `STALE KNOWN-LINT SNAPSHOT ... 'stale-pin-0' != ... 'fixture-toolchain-1'`.
  The pre-fix silent pass is closed.
- Bare default path on good files: `python3 scripts/policy-verifier.py
  tests/fixtures/policy-verifier/live-corrected-lints.toml` (no flags at all) →
  exit 0. Good-file path unaffected.
- `--expect-pin` precedence sane: `--expect-pin`/`--pin-file` are
  argparse-mutexed, so an explicit `--expect-pin` skips the default pin-file
  read (verified: `--expect-pin stale-pin-0` vs stale snapshot passes the pin
  gate and proceeds to lint findings). QA §F2c rationale (guard load-bearing)
  stands; mechanism re-verified by code read + the two runs above.

## R3. Scope — PASS, no creep

Rework diff `dea5b74..8dc4d57` (7 files): `red-proofs.log`, this verification
report (committed copy of the prior audit text), `wave-41-rework-1-implementation.md`,
`scripts/policy-verifier.known-lints.txt`, `scripts/policy-verifier.py`,
`tests/fixtures/policy-verifier/live-corrected-lints.toml` (new),
`tests/test_policy_verifier.py`. Evidence diff `8dc4d57..8f9da0e` (2 files):
`red-proofs.log` §RE-VERIFY + QA re-verification section only. No `specs/ rigs/
rosters/ registry/ fleet/` files; `git diff 0a3db37..HEAD -- scripts/verify-rigs.sh`
has 0 removed lines (V1–V8 byte-identical); V9 block carries exactly one new
`ok()` (line 42 of the diff; the other grep hit is a comment). `Makefile`
untouched by rework. Scope is F1/F2 only.

## R4. Commands re-run — PASS

- `make verify` → `SUMMARY: 25 checks passed, 0 failed`, exit 0; `live-health.py`
  advisory exit 0 (only pre-existing heartbeat/idleness WARN/SKIP).
- `openspec validate remediate-41-policy-verifier` → valid.
- `python3 -m unittest discover -s tests` → 127 tests, OK (124 + 3 new live-table/pin tests).
- Secrets scan over `git diff dea5b74..HEAD` (sk-/ghp_/AKIA/private-key/password
  patterns) → clean. Mission repo `git diff --stat` empty (read-only scans only).
  Worktree `git status --short` clean.
- `red-proofs.log` §RE-VERIFY contains verbatim F1a/F1b/F1c/F2a/F2b/F2c + R1/R2/R3
  outputs; the two QA claims spot-checked above (F1c sabotage, F2b bare path)
  reproduce independently.

## Re-audit findings

F1: CLEARED — corrected live table passes, stale fires only on `cast_lossy`,
fixture faithful, snapshot covers all live tables, guard test non-vacuous.
F2: CLEARED — `--pin-file` defaults to the checked-in pin, stale-pin bare
invocation exits 1, `--expect-pin` precedence sane. No new blocking defects.
No V1–V8 changes, no forbidden dirs, no scope creep.

---

# Re-audit — review round 2 (2026-10-22, commits `3513e47` + `f7b2dc9`)

Stage/wave id: `wave-41-review2-reaudit`. Commits under audit: `3513e47`
(review-2 fixes: index authority, expr placeholder, builtins, quoting, cargo
context) + evidence commit `f7b2dc9` on top (`git log --oneline -6`
confirmed: `f7b2dc9`, `3513e47`, `627b3b4`, `8f9da0e`, `8dc4d57`,
`dea5b74`). Auditor: independent drift-guard (no fixes, no commits).
Prior sections above are history; O1/O2/O3 and R1/R2/R3 already ruled and
not re-litigated. Re-verification claims spot-checked independently
(not trusted).

## D1. Diff audit — PASS, 4 files only, no forbidden dirs

Fix commit `3513e47` touches exactly the 4 intended files
(`scripts/policy-verifier.known-lints.txt`,
`scripts/policy-verifier.py`,
`scripts/policy-verifier.toolchain-pin`,
`tests/test_policy_verifier.py`); evidence commit `f7b2dc9` touches only
`docs/evidence/wave-41-policy-verifier/red-proofs.log` + the QA report.
`git diff 627b3b4..HEAD --name-only -- specs/ fleet/ rigs/ rosters/
registry/` is empty; `git diff 627b3b4..HEAD -- scripts/verify-rigs.sh
Makefile` is empty (V1–V8 byte-identical, no renumbering).

## D2. Changed-region read-through — PASS (adversarial)

1. Index authority: `load_indexed_text_or_worktree`
   (`scripts/policy-verifier.py:507-530`) — tracked+readable path returns
   the index blob (index wins); tracked-but-unreadable raises
   `PolicyError` (fail-closed, no worktree fallback); untracked or
   outside-repo returns `None` and the caller uses the worktree file,
   which is then the only existing source (no staged content is
   overridden). Provenance is distinguishable: index reads carry a
   `(git index)` origin in diagnostics. Empirically proven (D5): worktree
   pin sabotaged to `wrong-pin` → non-staged run STALE exit 1, while
   `load_known_lints_staged` on the same path still returned
   `fixture-toolchain-1`. Restored via `git checkout`, tree clean.
2. Expression placeholder `__GH_EXPR__`: contains no `$`, so
   `tokenize`'s pre-existing `$`-token drop can never manufacture it;
   grep confirms no test/script uses it as a real name (collision
   requires a literal `__GH_EXPR__` script — absurd). The skip fires ONLY
   in command position (`head == GH_EXPR_PLACEHOLDER` in `check_pm_step`
   / `check_cargo_step`); in argument position the placeholder flows
   through normal resolution (`pnpm lint ${{ matrix.args }}` still
   resolves `lint`). Reproduced exit 0 for both dynamic-position steps.
3. `PM_DEFAULT_COMMANDS`: the `head in PM_DEFAULT_COMMANDS → return`
   precedes the `names` lookup, so the "script-present wins" comment
   describes outcome, not code path — but both branches yield no
   finding, so precedence cannot alter any verdict and nothing can
   "hide" (script bodies never produce findings, only DUPLICATE
   comparisons). A typo (`tset`) still fails `UNRESOLVABLE` (fail-closed
   direction kept). Deliberate review-approved leniency with red-proofs;
   not a defect.
4. Quote-strip: single `body[1:-1]` applied ONLY on the inline-`run:`
   branch (`scan_run_steps`, `scripts/policy-verifier.py:412-423`); the
   block-scalar branch assigns `body` before that site — untouched
   (code-read confirmed). `run:` with unbalanced quotes
   (`run: "pnpm lint`) is invalid YAML → `UNREADABLE WORKFLOW` exit 1
   (fail-closed, reproduced in `/tmp`). Trailing-quote-only garbage
   fails `UNRESOLVABLE` (fail-closed direction, never silent pass).
5. Cargo config context: staged mode routes `.cargo/config.toml`
   blobs through `load_aliases` only
   (`scripts/policy-verifier.py:983-987`), never `check_toml` — no
   findings, no `files_checked` increment from context files.
   `index_tracked_manifests` excludes already-staged names, so a staged
   config gets its normal single check, not double handling. Non-staged
   path unchanged.
6. Pin headers: both files now state CURATED SUBSET / audit-revision
   pin and explicitly disclaim any toolchain capture — honest, and the
   prior snapshot-header promise of a "capture" is gone. Mechanism
   preserved: comment-tolerant parsing (TOML-channel-first, else first
   non-`#` line; snapshot skips `#`/`pin:`), stale-pin bare invocation
   still STALE exit 1 (D3). `write_snapshot`/`read_checked_in_pin` are
   test helpers deriving the default from the checked-in pin.

## D3. F1/F2 still cleared — re-run, not trusted

- Live corrected mission `Cargo.toml` + checked-in snapshot → exit 0.
- Live stale `root-lints-reference.toml` → exit 1 with EXACTLY ONE
  finding (`clippy::cast_lossy` at `:28`).
- Stale-pin snapshot (`stale-pin-0`), no flags → exit 1 `STALE
  KNOWN-LINT SNAPSHOT`; bare invocation on good fixture → exit 0.

## D4. Commands re-run — PASS

- `make verify` → `SUMMARY: 25 checks passed, 0 failed`, exit 0;
  `live-health.py` advisory exit 0 (only pre-existing
  heartbeat/idleness WARN/SKIP).
- `openspec validate remediate-41-policy-verifier` → valid.
- `python3 -m unittest discover -s tests` → 142 tests, OK.
- Secrets scan over `git diff 627b3b4..HEAD` (sk-/ghp_/AKIA/private-key
  patterns) → clean. Mission repo read-only (`git diff --stat` empty,
  only pre-existing untracked strays). Worktree `git status --short`
  clean after sabotage restore; scratch in `/tmp` removed.

## D5. QA spot-checks (review-2 §2/§3) independently reproduced

- QA §2(a) index-authority sabotage: reproduced as in D2.1 (worktree
  `wrong-pin` ignored by staged loader, non-staged path fails STALE).
- QA §2(e) quoting: `run: "pnpm eslint ."` with a `lint` script →
  exit 1 `DUPLICATE RUN COMMAND` citing `lint` (reproduced in `/tmp`
  fixture); expression steps exit 0. Both claims hold.

## Re-audit findings

Numbered blocking findings: none. No new blocking defects; F1/F2 remain
cleared; no scope creep; the PASS stands.

VERDICT: PASS
