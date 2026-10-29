# Verification report — 15-auth-envelope rework-1 (Refs #15, never Closes #15)

Independent drift-guard audit of change `2026-10-29-15-auth-envelope`
rework-1 (issue #15, PR #133 review findings F1–F9). Worktree
`.lane/trees/15-auth-envelope`, audited at commits `697543d`
(rework fixes) + `a02d7bf` (QA re-verification + red-proofs).
Prior verdict `docs/reports/15-auth-envelope-verification.md` (PASS @
`0ae5e06`) was re-verified, not trusted: every claim below was checked
against current disk state. No source file was modified by this audit;
the only write is this report. Both sabotage probes were temporary file
edits with `/tmp/opencode/audit-r1/` backups, byte-identical restores
confirmed by `sha256sum`, and GREEN re-runs before proceeding. The
`--check-idempotent` run's registry provenance side-effect was reverted
(`git checkout -- registry`); `git status --short` is clean except this
report.

## 1. Spec traceability (REQ-E1…E4 → code → test → evidence, re-run)

Archived spec `openspec/changes/archive/2026-10-29-15-auth-envelope/specs/auth-envelope/spec.md`
(= promoted `openspec/specs/auth-envelope/spec.md`) re-checked against disk:

| Req / scenario | Code | Test | Re-run |
|---|---|---|---|
| E1 clean validates | `scripts/auth_envelope.py` `validate_envelope` (shape→MAC→expiry→replay→hash→scope) | `test_clean_envelope_validates` | authorized |
| E1 drift refused | hash-compare deny + redacted log | `test_drifted_landing_refused` (+ row-untouched) | refused, nonce NOT consumed |
| E1 scope breach refused | `_scope_covers` uncovered deny | `test_scope_breach_refused` + new F5/F6/F7 pins | refused |
| E1 expiry refused | `if int(now) >= int(expires)` deny | `test_expired_envelope_refused` | refused |
| E1 replay refused | `if nonce in seen` deny, store never rewound | `test_replayed_nonce_refused` + `test_missing_replay_set_fails_closed` | refused |
| E2 drift flagged | `scripts/reconcile_model.py:942 stalled_premise_drift_diff` + newest-to-oldest landing scan (F8) | `test_drifted_premise_flagged_stalled` + `test_reconcile_end_to_end_flags_drift` (exit 1, `stalled-premise-drift`, NEEDS-HUMAN-REVIEW, no PROPOSED-CELL) | exit 1 with drift diff |
| E2 clean quiet | `if not drifted and not uncovered: return None` | `test_clean_premise_stays_quiet` + `test_reconcile_end_to_end_clean_quiet` (exit 0 in sync) | exit 0 silent |
| E2 attribution report-only | `attribute_premise_age` (720s/420s, never raises, never writes) | `test_premise_age_attribution_attached` + `test_attribution_is_report_only` | 720/420 |
| E3 row untouched | `validate_envelope` pure check | `test_refused_landing_leaves_row_untouched` | row JSON byte-identical |
| E3 recovery needs state change | `scripts/sweep-typed-blocks.py check_recovery_dismissal` | `test_recovery_needs_row_state_change` | OK |
| E3 no self-executor | no subprocess/shell/commit in module | `test_no_self_execution_surface` + auditor grep | clean |
| E4 V31 gate / corpus | V31 block (on `main` already; zero rework diff — see §3) | envelope 27 + prefix 8 = 35 OK; `make test` 634 OK | `SUMMARY: 39 checks passed, 0 failed`, V31 PASS listed |
| E4 FAIL-ONLY pre-fix | n/a (unpatched tree) | `tests/test_auth_envelope_prefix.py` pins transcript | `docs/evidence/15-auth-envelope-prefix.md` unchanged |

## 2. Rework fixes F1–F3, F5–F9: confirmed applied and minimal

- **F1 — CONFIRMED.** `docs/reports/15-auth-envelope-verification.md:64-65`
  now names exactly the HANDOFF discipline-line change (38→39 by the r1
  rework via F3; post-PR #132 snapshot counts in §1 stay intact).
- **F2 — CONFIRMED.** Exactly one clause added to the report opening
  (`verification.md:8-13`): the `--check-idempotent` registry
  side-effect + revert. This audit reproduced the same side-effect and
  the same revert (§9).
- **F3 — CONFIRMED, one line only.** `HANDOFF.md:139` reads
  `# Expect: 39 checks passed, 0 failed`; `git diff 0ae5e06...697543d -- HANDOFF.md`
  is that single line. Snapshot counts untouched: `HANDOFF.md:18` still
  records the post-PR #132 baseline (`SUMMARY: 38 checks passed, 0 failed`).
  Matches AGENTS.md expect-line, V19 freeze, and live verify SUMMARY (39/0).
- **F5 — CONFIRMED + pin.** `,` in `_SCOPE_BAD_RE`
  (`scripts/auth_envelope.py:48`); pin
  `test_mint_rejects_comma_in_scope_entry` (`tests/test_auth_envelope.py:597`).
- **F6 — CONFIRMED + pin.** Fail-closed shape block present
  (`auth_envelope.py:182-192`): non-string → `str(path)` uncovered;
  empty/absolute/empty-segment/`.`/`..` rejected before prefix checks.
  Pin `test_scope_covers_rejects_suspicious_landing_paths` (`:614`)
  incl. canonical covered/uncovered preservation.
- **F7 — CONFIRMED + pin.** `..`-segment guard present
  (`reconcile_model.py:885-887`, segment-wise so `src/..hidden/x` is
  unaffected). Pin `test_premise_scope_rejects_dotdot_traversal` (`:312`)
  incl. canonical preservation.
- **F8 — CONFIRMED + pins.** Newest-to-oldest scan present
  (`reconcile_model.py:975-993`): trail sorted by `transitionId`
  descending, first `_parse_landing`-recognized note binds; terminal
  check, `queue_evidence`, attribution, and open-authorization branch
  unchanged. Pins `:325` (clean + trailing non-landing note → quiet) and
  `:363` (drifted + trailing note → still stalled with drift reason).
- **F9 — CONFIRMED + pin.** MAC binding intact (`hmac.compare_digest`);
  pin `test_tampered_expiry_and_hash_refused_for_mac` (`:660`: expiry
  `1780000000`→`1880000000` and diff-hash swap without re-signing → both
  refused with "bad envelope mac", `seen` stays empty), alongside
  `test_bad_mac_refused`.

Pre-probe hashes matched the fix/QA reports exactly
(`auth_envelope.py sha256 59560047…`, `reconcile_model.py sha256 d371f1e1…`),
confirming the committed state is what the reports describe.

## 3. F4 skip adjudication — AGREE (independently confirmed, three reasons)

The finding asks that an open authorization without a matching envelope
stall even when the landing matches the premise (clean quiet only with a
matching envelope). The skip is correct:

1. **No envelope registry exists in the reconciler.** `grep envelope
   scripts/reconcile_model.py scripts/reconcile.py` shows comments only;
   neither file imports nor calls `auth_envelope`. The classifier
   signature `stalled_premise_drift_diff(row, queue_by_id,
   transitions_by_id)` binds premise → landing record only — it has no
   envelope parameter and no envelope store to consult. Implementing F4
   would require a new envelope-lookup design, i.e. a spec amendment, not
   a review fix.
2. **The concrete REQ-E2 scenario contradicts F4.** `spec.md:41-45`
   ("clean premise stays quiet") plus the corpus pins
   `test_clean_premise_stays_quiet` (`:210-233`, no envelope wired,
   asserts `None`) and `test_reconcile_end_to_end_clean_quiet`
   (`:431-442`, exit 0 "in sync", no envelope wired). Threading envelope
   presence into the classifier would flip both green tests RED and break
   the full corpus + V31. ("Within the envelope window" is satisfied in
   fixtures by timestamps, not by envelope presence.)
3. **Per the review caution (prefer the spec), the scenario governs.**
   The REQ-E2 normative parenthetical ("or which carries an open
   authorization with no matching envelope", `spec.md:33`) is
   unimplementable as written (see 1) and contradicted by the scenario +
   corpus (see 2). The code's existing `landing is None` → stalled branch
   covers the implementable half (open authorization with no landing
   *record* — pinned by `test_open_authorization_without_landing_is_stalled`, `:258`).

No spec, classifier, or test change was made for F4 — correct. A future
wave wanting envelope-presence gating needs a spec amendment (new REQ or
REQ-E2 revision) plus a reconciler envelope lookup; the F6/F7 scope
hardening and F8 trail scan are the hooks it would build on.

## 4. Auditor's own sabotage (2/2 RED for the right reason, GREEN on restore)

- **Probe A (F5 comma re-allowed):** removed `,` from `_SCOPE_BAD_RE`.
  `test_mint_rejects_comma_in_scope_entry` → `FAILED (failures=1)`,
  `AssertionError: ValueError not raised` (the mint/validate asymmetry is
  back). Restored from `/tmp` backup: sha256 `59560047…` byte-identical,
  single test OK.
- **Probe B (F8 latest-only reverted):** replaced the newest-to-oldest
  scan with `landing = _parse_landing(latest_note)`. Both F8 pins →
  `FAILED (failures=2)`: clean case stalls with "no matching landing";
  drifted case loses "drifted" from the reason (reads "no matching
  landing record" instead) — the exact incident signatures. Restored:
  sha256 `d371f1e1…` byte-identical, full corpus `Ran 35 tests OK`.

No entry is vacuous: each sabotage flips a named pinning test RED and
GREEN on byte-identical restore. QA's five R1 probes (F5/F6/F7/F8/F9 in
`red-proofs.log`, QA-R1 section) were verified present with matching
failure signatures; my probes independently reproduce two of the five
axes in both directions.

## 5. V31 append-only intact; SUMMARY re-run by the auditor

`git diff main -- scripts/verify-rigs.sh` is empty — the rework touched
no gate code, so V1–V30 are intact by construction (V31 already on
`main` from the S2 wave). V31 uses a dynamic corpus count
(`{_v31_ran}`, non-vacuous floor ≥16, skips fail the gate) — no stale
count. Auditor re-run: `SUMMARY: 39 checks passed, 0 failed`, V31
`[PASS]` listed, exit 0. `make test`: `Ran 634 tests OK`, 0 failures.
Envelope corpus: `Ran 35 tests OK` (27 + 8 prefix).

## 6. Never-self-execute / never-auto-commit (structural)

`scripts/auth_envelope.py` contains no `subprocess`, `os.system`,
`os.exec`, `os.popen`, `check_output`, `.commit(`, `git commit/push`,
queue-create, or tracker-write call (auditor grep clean; corpus + V31
scans agree). Mint/validate are pure functions plus redacted log;
refusals never consume the nonce; `seen=None` fails closed.
`write_envelope_exclusive` reuses the shared O_EXCL guard (refuses
overwrite, 0600). Refusal leaves row state byte-identical (tested);
recovery dismissal requires a row state change (tested). No executor
exists and none was added — holds structurally, not just in prose.

## 7. Propose-only / never-done intact; wave-9 untouched

`stalled-premise-drift` renders `NEEDS-HUMAN-REVIEW` + `SUGGESTED (not
paste-ready)` via the early return in `render_diff`
(`reconcile_model.py:1072-1078`); no `PROPOSED-CELL` marker. It stays
outside `PASTE_READY_CLASSES` (`generate_trackers.py:93-98`: only
`stale-state`, `parked-satisfied-but-tracker-silent`,
`missing-convergence-annotation`); the OTHER-arm carve-out renders
`WITHHELD — TPM judgment required`. Wave-9: `git diff main --
scripts/send_identity.py` is empty (0 lines) — grant-bound mint/verify,
nonce discipline, and redacted logs untouched.

## 8. Hygiene: secrets, stubs, vacuity

- Secrets: no `ghp_/gho_/sk-/AKIA`, no private-key blocks, no password
  assignments. 40+-char runs are only long test-method identifiers
  (repo-precedent convention, same as the S2 audit), the two documented
  source-file sha256 pins in `red-proofs.log`, and expiry-epoch literals.
  Nothing was read from `~/.config/heretek-rigs/secrets/`; fixtures use
  dummy binding secrets and 16-hex hashes.
- Anti-stub: no `TODO/FIXME/STUB/PLACEHOLDER`, no
  `NotImplementedException`, no `|| true`, no `set +e`, no bare
  `except: pass` (all four `except` sites in `auth_envelope.py` raise or
  return an explicit fail-closed `refused`), no `@unittest.skip`, no
  literal/vacuous assertions, no `skip` mentions in either test file.
  All six F-pins assert behavior (rejection raised / uncovered listed /
  quiet-vs-stalled both ways / MAC refusal with empty `seen`) and §4
  proves them non-vacuous in both directions.
- Commit messages use `Refs #15` only (`Closes/Fixes/Resolves #15` count: 0).

## 9. Generator provenance

`python3 scripts/generate-rigs.py --check-idempotent` → exit 0
("idempotence check passed (two consecutive runs byte-identical)").
It rewrote the known `resolvedCommit` re-lag stamp across 16 `registry/`
files (same advisory as S2/QA); reverted via `git checkout --
registry`. `specs/`, `rigs/`, `rosters/` untouched. `audit_loop.py
--self-test` → SELF-TEST PASSED. Final `git status --short` clean except
this report.

## Commands re-run by the auditor (exit codes observed)

- `python3 -m unittest tests.test_auth_envelope tests.test_auth_envelope_prefix` → OK (`Ran 35 tests`)
- `make test` → OK (`Ran 634 tests`, 0 failures)
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed, 0 failed`, V31 PASS (exit 0)
- `python3 scripts/generate-rigs.py --check-idempotent` → exit 0 (registry side-effect reverted)
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED
- Sabotage probes A (F5) + B (F8) → RED as above, GREEN after byte-identical restore

VERDICT: PASS
