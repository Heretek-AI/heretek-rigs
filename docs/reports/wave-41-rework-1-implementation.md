# Implementation report — wave-41-rework-1 (failed-stage rework, cycle 1 of max 3)

Stage/wave id: `wave-41-rework-1` · change-id `remediate-41-policy-verifier` (unchanged)
Branch: `remediate/41-policy-verifier` (commit on top; no merge, no push)
Binding remediation spec: `docs/reports/wave-41-policy-verifier-verification.md` §Findings
(F1 major + F2 minor). O1/O2/O3 explicitly non-findings — untouched.

## Deliverables (per-finding, fixed + verified)

### F1 — completed known-lint snapshot from the live tables
- `scripts/policy-verifier.known-lints.txt`: added `rust::unsafe_code` and
  `rust::missing_docs` (9 entries total), and rewrote the header to record the
  read-only audit: root `Cargo.toml` `[workspace.lints.rust]` +
  `[workspace.lints.clippy]` sections fully covered; audited crate manifests
  (`apps/web/src-tauri/Cargo.toml`) carry only `[lints] workspace = true`
  (zero lint names); the `w1-08-staging` manifest carries no `[lints]` table.
- `tests/fixtures/policy-verifier/live-corrected-lints.toml` (new): vendored
  read-only copy of the complete live corrected table text (both sections),
  transcribed read-only from mission `Cargo.toml:27-38`. The mission repo is
  never a test dependency.
- `tests/test_policy_verifier.py` (+3 tests, 16 → 19, no renumbering):
  `test_vendored_live_corrected_table_passes_checked_in_snapshot` (exit 0
  against the CHECKED-IN snapshot), ..._with_stale_cast_lossy_fires_only_that_name
  (exit 1, `clippy::cast_lossy` present, `rust::unsafe_code`/`rust::missing_docs`
  absent — true positive, no masking).
- `docs/evidence/wave-41-policy-verifier/red-proofs.log`: appended REWORK-1
  section (F1-RED/F1-GREEN/F1-TRUE-POSITIVE verbatim outputs, S0-REWORK).

### F2 — pin freshness enforced by default
- `scripts/policy-verifier.py`: `--pin-file` now defaults to the checked-in
  `scripts/policy-verifier.toolchain-pin` (`DEFAULT_PIN_FILE`); explicit
  `--expect-pin` still wins when passed (precedence fix verified by the two
  pre-existing pin tests). `Makefile` target intentionally untouched — the
  default covers every invocation including bare `--staged`.
- New test `test_default_pin_file_enforces_freshness_without_pin_flags`
  (mismatched snapshot pin, no pin flags → exit 1 `STALE`).

## Files changed
- `scripts/policy-verifier.known-lints.txt` (2 entries + header)
- `scripts/policy-verifier.py` (`DEFAULT_PIN_FILE`, `--pin-file` default +
  help, docstring, `--expect-pin` precedence fix)
- `tests/test_policy_verifier.py` (+3 tests, docstring)
- `tests/fixtures/policy-verifier/live-corrected-lints.toml` (new)
- `docs/evidence/wave-41-policy-verifier/red-proofs.log` (appended REWORK-1)
- `docs/reports/wave-41-rework-1-implementation.md` (this file; new)

Untouched per constraints: `specs/ rigs/ rosters/ registry/ fleet/`,
`scripts/verify-rigs.sh` (V1–V8 byte-identical, zero removed lines), `Makefile`,
and the O1/O2/O3 observation areas.

## Commands run (exit codes)
- Live F1-RED (pre-fix): corrected `Cargo.toml` scan → exit 1 (2 false positives).
- Live F1-GREEN (post-fix, bare): corrected `Cargo.toml` scan → exit 0.
- Live true positive (post-fix): stale `root-lints-reference.toml` → exit 1,
  single `clippy::cast_lossy` finding at `:28`.
- F2-RED (pre-fix): stale-pin `/tmp` fixture, no pin flags → exit 0 (gap).
- F2-GREEN (post-fix): same command → exit 1 `STALE KNOWN-LINT SNAPSHOT`.
- S0-REWORK sabotage (`return` in `check_toml`): new live-table tests →
  FAILED (failures=1, the stale-fires test); restored from `/tmp` backup,
  suite 19/19 OK after.
- `python3 -m unittest discover -s tests` → Ran 127 tests, OK (exit 0).
- `make verify` → `SUMMARY: 25 checks passed, 0 failed` + live-health advisory
  (only pre-existing heartbeat/idleness WARN/SKIP), exit 0.
- `openspec validate remediate-41-policy-verifier` → valid (exit 0).
- Mission repo `git diff --stat` → empty (read-only; untouched).

## Self-audit notes
- Nothing unfinished: F1 and F2 remediations match the report's Remediation
  lines exactly (full-table snapshot incl. crate-manifest audit + vendored-copy
  test + re-recorded red-proofs; default `--pin-file` freshness).
- Scope held: no changes beyond F1/F2; O-items untouched; no merges, no pushes
  (commit only, on the rework branch).
- One mid-course correction: the first `--pin-file` default unconditionally
  overrode explicit `--expect-pin` (broke 2 pre-existing pin tests); fixed with
  `if expect_pin is None` precedence — both old and new pin tests green.
- `git status` shows only the intended files (list verified before commit).
