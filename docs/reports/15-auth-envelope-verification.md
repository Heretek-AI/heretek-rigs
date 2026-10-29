# Verification report — 15-auth-envelope (Refs #15, never Closes #15)

Independent drift-guard audit of change `2026-10-29-15-auth-envelope`
(wave 15-auth-envelope, issue #15). Worktree
`.lane/trees/15-auth-envelope`, audited at commits
`471f628` (spec) + `01286d2` (implementation) + `35d984f` (red-proofs/QA).
Every claim below was verified against current disk state; nothing was
trusted from reports. No source file was modified by this audit; the only
write is this report. All sabotage probes were temporary file edits with
`/tmp` backups, byte-identical restores confirmed by `diff -q`, and
GREEN re-runs before proceeding. The `--check-idempotent` run's registry
provenance side-effect was likewise reverted (`git checkout -- registry`)
with `git status --short` confirming only this report remained (see §9).

## 1. Spec traceability (REQ-E1…E4 → code → test → evidence)

| Req / scenario | Code | Test | Evidence / re-run |
|---|---|---|---|
| E1 clean validates | `scripts/auth_envelope.py:189 validate_envelope` (shape→MAC→expiry→replay→hash→scope; `seen.add` only on authorize) | `test_clean_envelope_validates` | Re-ran: authorized, nonce consumed. V31 live-check also authorizes clean |
| E1 drift refused | same, hash-compare deny + redacted log | `test_drifted_landing_refused` (+ row-untouched) | Re-ran: refused, nonce NOT consumed |
| E1 scope breach refused | same, `_scope_covers` uncovered deny | `test_scope_breach_refused` | Re-ran: refused |
| E1 expiry refused | `if int(now) >= int(expires)` deny | `test_expired_envelope_refused` | Re-ran: refused |
| E1 replay refused | `if nonce in seen` deny, store never rewound | `test_replayed_nonce_refused` + `test_missing_replay_set_fails_closed` | Re-ran: 2nd presentation refused |
| E2 drift flagged | `scripts/reconcile_model.py:934 stalled_premise_drift_diff` + `diff_row` tail (line 565) | `test_drifted_premise_flagged_stalled` + `test_reconcile_end_to_end_flags_drift` (exit 1, `stalled-premise-drift`, NEEDS-HUMAN-REVIEW, no PROPOSED-CELL) | Re-ran: exit 1 with drift diff |
| E2 clean quiet | `if not drifted and not uncovered: return None` | `test_clean_premise_stays_quiet` + `test_reconcile_end_to_end_clean_quiet` (exit 0 in sync) | Re-ran: exit 0 silent |
| E2 attribution report-only | `attribute_premise_age` (720s/420s, never raises, never writes) | `test_premise_age_attribution_attached` + `test_attribution_is_report_only` (tracker/queue/list/transitions byte-identical) | Re-ran: 720/420; runbook table matches |
| E3 row untouched | `validate_envelope` performs no write (pure check) | `test_refused_landing_leaves_row_untouched` | Re-ran: row JSON byte-identical |
| E3 recovery needs state change | `scripts/sweep-typed-blocks.py:254 check_recovery_dismissal` (reused wave-4/81 guard) | `test_recovery_needs_row_state_change` (identical→`RecoveryDismissalRefused`; changed→permitted) | Re-ran: OK |
| E3 no self-executor | no subprocess/shell/commit anywhere in module | `test_no_self_execution_surface` (docstring/comment-stripped code scan) + V31 code scan | Re-ran + own grep: clean |
| E4 V31 gate / corpus | `scripts/verify-rigs.sh` V31 block only (appended; see §3) | corpus 21 + prefix 8 = 29 OK; `make test` 628 OK | `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed, 0 failed`, V31 PASS listed |
| E4 FAIL-ONLY pre-fix | n/a (unpatched tree) | `tests/test_auth_envelope_prefix.py` pins frozen transcript | `docs/evidence/15-auth-envelope-prefix.md`: exit 0 silent, attribution ABSENT, envelope ABSENT |

## 2. Auditor's own red-proof sabotage (2/2 RED for the right reason, GREEN on restore)

- **Probe A (drift-classifier removal):** replaced `diff_row` tail
  `return stalled_premise_drift_diff(…)` with `return None`. Result:
  `tests.test_auth_envelope` → `FAILED (failures=2)`
  (`test_drifted_premise_flagged_stalled`,
  `test_reconcile_end_to_end_flags_drift`) — pre-fix silence restored.
  Restored via `/tmp` backup, `diff -q` byte-identical, corpus 21 OK.
- **Probe B (envelope-validation bypass):** forced `validate_envelope`
  entry to `authorized`. Result: `TestEnvelopeMintValidate` →
  `FAILED (failures=9)` of 11 (every refusal test fails; clean-validates +
  no-executor scan still pass — right reason); `verify-rigs.sh` →
  `SUMMARY: 38 checks passed, 5 failed` (4 live-behavior FAILs + corpus
  FAIL). Restored byte-identical; corpus 29 OK; verify back to 39/0.
  `git status --short` empty after each restore.

The recorded `red-proofs.log` entries (S1a–S1d + FAIL-ONLY + QA
7-probe re-verification with matching failure signatures) were thus
independently reproduced in both required directions. No entry is
vacuous: each sabotage flips a named acceptance command RED and GREEN
on revert.

## 3. V31 append-only

`git diff main -- scripts/verify-rigs.sh`: additions are the V31 block
(one `ok()`), V19 freeze comments, and the `_v19_canonical 38→39` /
`passes + 4 → passes + 5` bump — the freeze's own rule for a fourth
post-freeze `ok()` gate, same as waves 9/4/81. No V1–V30 line renumbered
or reworded (removed lines are only the two V19-bump lines). 39 `[PASS]`
lines, zero `FAIL`. `AGENTS.md:76` docs-map line present (count 38→39
rode with S2 as freeze mechanics); `README.md` / `docs/USER_GUIDE.md`
counts move with it; `HANDOFF.md` operating-discipline expect-count updated
38→39 by the r1 rework (F3; the post-PR #132 snapshot counts in §1 stay intact).

## 4. Never-self-execute / never-auto-commit

`scripts/auth_envelope.py` contains no `subprocess`, `os.system`,
`os.exec`, `os.popen`, `check_output`, `.commit(`, `git commit/push`,
queue-create, or tracker-write call (auditor grep clean; corpus +
V31 scans agree). Mint/validate are pure functions plus redacted log;
refusals never consume the nonce; `seen=None` fails closed.
`write_envelope_exclusive` reuses the shared O_EXCL guard (refuses
overwrite, 0600). Refusal leaves row state byte-identical (tested);
recovery dismissal requires a row state change (tested). No executor
exists and none was added — design D8 holds structurally, not just in prose.

## 5. Propose-only / never-done discipline

Premise-drift diffs render `NEEDS-HUMAN-REVIEW` + `SUGGESTED (not
paste-ready)` with no `PROPOSED-CELL` (`render_diff` early return for
`stalled-premise-drift`, same withhold shape as idle-park).
`stalled-premise-drift` stays outside `PASTE_READY_CLASSES`
(`stale-state`, `parked-satisfied-but-tracker-silent`,
`missing-convergence-annotation` only). The `generate_trackers.py`
OTHER-arm carve-out consults the shared helper (no parallel mapping)
and renders `WITHHELD — TPM judgment required`. S0/S1/S3 acceptance
greps and `make test` show no tracker or queue writes by the new paths.

## 6. Wave-9 attestation untouched

`git diff main -- scripts/send_identity.py` is empty — no change to
grant-bound mint/verify, nonce discipline, or redacted logs. The new
module reuses wave-9 semantics by import-pattern (cached `seed-rig.py`
module load for `_redact_for_log`) without touching the file.

## 7. Secrets discipline

`grep -rE '[A-Za-z0-9_-]{40,}'` over prefix evidence, runbook,
red-proofs log, both reports, and `scripts/auth_envelope.py` → exit 1
(clean). Fixtures use 16-hex dummy hashes and `dummy-`-prefixed
secrets, deliberately under the 40-run floor; the longest bare run is
the 37-char fixture qitem. Every new log path routes through
`_redact_for_log` (single choke point); the corpus redaction test
(`test_refusal_log_is_redacted`) uses a 60+ char dummy secret and
asserts no 40+ run reaches stderr. No real credentials appear in
commands, files, or this report (nothing was read from
`~/.config/heretek-rigs/secrets/`).

## 8. Anti-stub scan

No `TODO/FIXME/XXX/HACK` in `auth_envelope.py` / `reconcile_model.py`
diff; no `|| true`, no bare `except: pass`, no swallowed errors (every
malformed path in `validate_envelope` returns an explicit fail-closed
`refused`; mint raises `ValueError`; `_parse_*` returns `None` → quiet,
never a fake pass). No `@unittest.skip`, no `assert True`, no `skip`
mentions in either test file. 29/29 corpus tests assert behavior
(hash binds, scope binds, expiry, replay, quiet-both-ways, redaction,
byte-identity); `test_classifier_removal_is_silent` pins non-vacuity
in both directions. Zero stubs, zero placeholders, zero skipped tests.

## 9. Generator provenance

`scripts/generate-rigs.py --check-idempotent` → byte-identical, PASS.
The run rewrote the known `resolvedCommit` re-lag stamp across 16
`registry/` files (same advisory as QA); reverted via
`git checkout -- registry`, final `git status --short` empty except
this report. Committed registry state is the accepted re-lag (per
`AGENTS.md`). `specs/`, `rigs/`, `rosters/` untouched
(`git diff main --stat` shows none). `audit_loop.py --self-test` PASS.
Commit messages use `Refs #15` only (`Closes/Fixes/Resolves #15` count:
0) — the issue correctly stays open.

## Commands re-run by the auditor (exit codes observed)

- `python3 -m unittest tests.test_auth_envelope tests.test_auth_envelope_prefix` → OK (29 tests)
- `make test` → OK (`Ran 628 tests`)
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed, 0 failed`
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED
- `python3 scripts/generate-rigs.py --check-idempotent` → byte-identical (registry side-effect reverted)
- Sabotage probes A + B → RED as above, GREEN after byte-identical restore

VERDICT: PASS
