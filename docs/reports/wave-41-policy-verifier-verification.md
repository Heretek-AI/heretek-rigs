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

VERDICT: FAIL
