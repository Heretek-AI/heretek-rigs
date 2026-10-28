# Verification report — remediate-governance (Wave 3: M6–M8, audit #66)

- Stage id: `remediate-governance`, worktree `.lane/trees/remediate-governance`,
  branch `remediate/audit-66-p0-p1-governance`
- Spec: `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md` (M6, M7, M8 + Verified fact F4 + Gotchas)
- Implementation report: `docs/reports/remediate-governance-implementation.md`
- QA report: `docs/reports/remediate-governance-qa.md`
- Red proofs: `docs/evidence/remediate-governance/red-proofs.log` (+ `qa-run.log`)
- Unity binding: none (not a Unity project — no `.meta`/GUID checks applicable)
- Auditor method: read every cited file from disk, re-ran all gates myself,
  spot-checked matchers live, re-ran fixture + envelope rows, inspected diffs.
  No source file modified by this audit.

## M6 (#79, F4) — audit_loop evaluator hardening: VERIFIED

- `HR_HEADER_RE = re.compile(r"^#{1,6}\s*HR-[\w.-]+")` present
  (`scripts/audit_loop.py:49`). F4's pre-fix shape (`^###` + colon) is a strict
  subset; widening is exactly what M6 mandates. Heading scan also uses
  `^#{1,6}\s+(.*)$` for defect-matrix/sabotage context (`:125`).
- Decoration stripping present: `_CELL_DECORATION_RE` (`[*_~`]+`) + `_EMOJI_RE`
  (U+1F300–FAFF, U+2600–2BFF range covering U+274C) + `_LEDGER_TOKEN_RE`
  (`\b(BROKEN|PARTIAL)\b`, IGNORECASE), applied per cell at `:141`
  (`_scan_report_tables`). Pipe-scoped deliberately (prose "broken" stays clean).
- P-grade matrix scan present: `_PGRADE_RE` (`\bP[0-3]\b`, IGNORECASE),
  body-cells-only (header/separator skipped; matrix context = "defect matrix"
  heading or "Priority" header cell), `:148-161`.
- Sabotage last-cell check present: sabotage context (heading or "Caught?"
  column), last cell decorated-stripped + lowered `!= "yes"` counts open, `:162-165`.
- 8 new vectors present (`m6_vectors` V1–V8, `:336-365`), each asserting
  `FINDINGS_DETECTED`; 7 pre-existing vectors kept verbatim above them
  (diff shows pure addition, no deletion/modification of old vectors).
- Re-ran `python3 scripts/audit_loop.py --self-test` myself: exit 0,
  `15 adversarial test vectors`, `SELF-TEST PASSED`.
- Spot-checked 5 shapes live via direct `evaluate_audit_status` calls
  (depth-2 header with colon, no-colon header, `**BROKEN**`, P1 matrix row,
  sabotage non-yes row): all 5 returned `FINDINGS_DETECTED` with specific
  reasons (header count / ledger / matrix / sabotage legs each exercised).
- Sentinel short-circuit (`STATUS: FINDINGS_DETECTED` wins) preserved at `:177`.

## M7 (#83, #84) — governance gates: VERIFIED

- `is_auth` scoping (`scripts/sweep-typed-blocks.py:419`,
  `blocked_on.startswith("auth:")`): exact-equality + actor + evidence gates
  apply on the auth path only. SATISFIED path `:476` uses
  `blocker == blocked_on or (not is_auth and (overlap…))`; legacy path `:526`
  uses exact substring for auth vs `note_names_blocker` overlap for non-auth.
  Non-auth behavior pinned by scope-guard test (green in suite).
- TPM-seat allowlist is fleet-derived, not hardcoded: `load_tpm_seat_ids()`
  (`:272-314`) walks `fleet/fleet.yaml` for role ids containing tpm/scrum plus
  member `session:`/`address:` ids and `@`-local-parts; unreadable catalog →
  empty set (operator-only, stay-blocked bias). Live load returns exactly the 3
  TPM forms (`tpm-scrum-lead`, `delivery-tpm-scrum-lead`,
  `delivery-tpm-scrum-lead@executive-and-architecture`). No hardcoded name in
  the gate itself.
- Exact-equality on auth path confirmed both branches (`==` for SATISFIED,
  full-string `in` for legacy notes); token-overlap OR-branch retained for
  non-auth only.
- State-only terminality: `grep TERMINAL_NOTE_RE scripts/ tests/` → zero hits;
  `queue_terminal` (`scripts/reconcile_model.py:255-264`) is state-only
  (entry + latest-transition state vs `TERMINAL_QUEUE_STATES`). No other
  importers of the removed regex exist.
- `^QA PASS` anchor + negator/fail-token in both paths:
  `QA_PASS_ANCHORED_RE = ^QA PASS\b` ( IGNORECASE), `_NEGATOR_RE`
  (`not|no|never|n't`), `_FAIL_TOKEN_RE` (fail variants) at `:43-45`;
  `is_qa_affirmation` (`:49-57`) enforces anchor + no-negator + no-fail for
  queue notes, and `normalize_tracker` (`:231-241`) voids placed/closed under
  negation for tracker cells. `generate_trackers.py` imports `queue_terminal`
  from the shared model (`:61-72`), so both reconcile paths share one gate.
- Re-ran #84 fixture tests myself:
  `test_84_fixture_reconcile_flags_stale_state`,
  `test_84_fixture_generate_trackers_is_review_not_paste_ready`, plus full
  `TestNegationAwareTerminal` (7) + `TestAuthBlockerHardening` (11): 13/13 OK,
  exit-1 `stale-state` / `NEEDS-HUMAN-REVIEW` semantics intact.

## M8 (#92) — envelope semantics: VERIFIED

Every spec-named deny family present in `scripts/check-envelope.py`:

- Leading-dot (`.git/.pi/.agents`/all-dotfiles), interior `.git/.pi/.agents`
  segments, `fleet/` + `scripts/` prefix-or-equal, `AGENTS.md` basename-equal,
  leading `-`, `:` in entry, non-ASCII (`[^\x00-\x7f]`), `%` — all refused
  (`:304-345`).
- PUSH trunk refuse: `branch.upper() in ("HEAD","MAIN","MASTER")` (`:464`),
  old trailing HEAD-only clause removed as subsumed.
- Deadline chain: ALL deadlines parsed, `min()` governs (`:236-239`);
  `issued_at <= now < deadline <= issued_at + 14d`
  (`ENVELOPE_MAX_LIFETIME_DAYS = 14`, `:249-259`); future-issued refused.
- Fleet seat validation via own `fleet_gate_sets()` loader (153-id vocab,
  role/session/address/local-parts); unknown seat refused (`:443`).
- BY WHOM: void-set (`nobody/…`) refused, owning-seat-substring refused BEFORE
  TPM acceptance (self-verification impossible), TPM-seat-or-bare-`TPM`
  accepted, other fleet seats refused, free text accepted as named human (`:530-560`).
- Link-shaped audit: URL | qitem id | digit-bearing hex ≥7 | `commit` |
  slashed path (`_has_link_token`).
- Re-ran myself: `test_dotgit_path_refused`, `test_far_future_expiry_refused`,
  `test_by_whom_nobody_refused`, `test_push_main_refused`,
  `test_push_bare_main_refused`, `test_push_master_refused`-class —
  all OK; full `tests/test_check_envelope` 69/69 OK.
- PUSH-main/master inversion is spec-mandated (#92 names PUSH main explicitly;
  M8 acceptance demands every #92 row REFUSE). NOTES one-liner present
  (`docs/NOTES.md:281`). `git diff main...HEAD -- tests/` shows only additions
  plus the single inversion (`test_push_bare_main_accepted` →
  `test_push_bare_main_refused`); the only `-` lines in tests/ are that rename
  and its docstring. No other test weakened.

## Limitations — merge-blockers or honest M10 follow-ups?

My own verdict on each (agree with QA/implementation: none blocks merge):

1. **Bare-`TPM` shorthand ambiguity.** Today the fleet staffs exactly one
   tpm/scrum seat (verified live: 3 id-forms, one seat), the template names the
   role "TPM", and the retirement condition is recorded in code comments and
   NOTES. Risk is latent, conditional on a future fleet change that the
   verifier itself would surface. M10 follow-up. Not a blocker.
2. **`xyz123`-style token accepts as named human.** No human registry exists in
   M8 scope; every machine-checkable case (void words, owning seats, fleet
   seats) refuses, and the accepted value is audit-recorded, so misuse leaves a
   named trail. Closing it needs a human-registry source that does not exist
   yet. M10 follow-up. Not a blocker.
3. **`"QA PASS, no issues"` now non-terminal.** The spec's negator list is
   literal (`not|no|never|n't`); treating ambiguous prose as non-terminal is
   the fail-closed direction, and the canonical emitted cells never contain
   standalone negators — 248/248 green proves no existing flow regresses.
   Not a blocker; weakening it would re-open #84.

## Hygiene: VERIFIED

- No stubs/swallowed errors: grep over the four touched scripts for
  TODO/FIXME/`|| true`/bare-`except: pass`/`@skip`/`skipTest` → zero hits
  (excluding the words "passing/passed" in prose).
- V1–V11 untouched: `git diff main...HEAD -- scripts/verify-rigs.sh` → 0 lines.
- Untouched files confirmed: `git diff main...HEAD -- verify-rigs.sh Makefile
  render-seat.py seat-sandbox.sh send-authenticated.sh fleet/fleet.yaml` →
  empty.
- Commit discipline: 3 milestone commits (`59786ed`, `6bbd59b`, `330f862`),
  each one-milestone with explicit scope and both attribution trailers;
  stage-report commit `bc4776c` likewise attributed. (Nit, not a finding: QA
  evidence commit `2198a9d` carries a bare message without the trailers — it
  touches only evidence/report files, no code; style nit per severity rule.)
- QA sabotages all reverted: `git status --short` is empty (clean); all
  evidence/report files committed; no source-file drift.
- Red-proofs audit: 4 sabotages, each with a recorded RED (exit 1 + exact
  failure signature: M6 V1 miss; case-B `unpark != stay-blocked`;
  3 reconcile failures exiting 0 in-sync; 3 PUSH tests rc=0 ACCEPT), each with
  a restore proof (self-test exit 0; 11/11; 7/7; 69/69). Signatures are
  non-vacuous — each names the precise assertion that caught the defect.

## Gates re-run by auditor

- `python3 scripts/audit_loop.py --self-test` → exit 0, 15 vectors.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 28 checks passed, 0 failed.`
- `make test` → `Ran 248 tests … OK` (counted myself: 210 baseline + 11 sweep
  + 7 reconcile + 20 envelope net of the inversion = 248).
- `tests/test_check_envelope` → 69/69 OK; sweep hardening 11/11 OK;
  reconcile negation 7/7 OK; #84 fixture pair OK.

VERDICT: PASS
