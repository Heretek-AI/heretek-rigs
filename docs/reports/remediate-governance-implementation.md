# remediate-governance implementation report (Wave 3: M6–M8, audit #66)

- Stage id: `remediate-governance` (worktree `.lane/trees/remediate-governance`, branch `remediate/audit-66-p0-p1-governance`)
- Scope: M6 (`scripts/audit_loop.py`, #79), M7 (`scripts/sweep-typed-blocks.py` #83 + `scripts/reconcile_model.py` #84), M8 (`scripts/check-envelope.py`, #92). No Unity binding (not a Unity project).
- Prior state: Waves 1–2 merged on main (verify 28 checks, 210 unit tests). `docs/NOTES.md` appended, never rewritten.

## Deliverables

| Milestone | Files changed | What |
|---|---|---|
| M6 (#79) | `scripts/audit_loop.py`, `docs/NOTES.md` | Header/ledger/matrix/sabotage hardening + 8 new self-test vectors (15 total) |
| M7 (#83, #84) | `scripts/sweep-typed-blocks.py`, `scripts/reconcile_model.py`, `scripts/generate_trackers.py` (mapping text only), `tests/test_sweep_typed_blocks.py` (+11), `tests/test_reconcile.py` (+7), `docs/NOTES.md` | auth: actor/exactness/evidence gates; negation-aware terminal detection |
| M8 (#92) | `scripts/check-envelope.py`, `tests/test_check_envelope.py` (+20, 1 spec-mandated inversion), `docs/NOTES.md` | Path/PUSH/expiry/seat/verifier/link gates |

Commits (one per milestone, explicit `git add`, attribution trailer on each):

- `59786ed` `remediate(#79): harden audit_loop evaluator with header/ledger/matrix/sabotage detection`
- `6bbd59b` `remediate(#83,#84): governance gates - auth actor/exactness, negation-aware terminal`
- `330f862` `remediate(#92): envelope semantics - path/PUSH/expiry/seat/verifier/link gates`

Untracked in tree: this report only (to be committed by the spawning session if desired — left uncommitted per "leave tree with implementation commits only"; the three milestone commits are in).

## Acceptance outputs (exact commands, exit codes)

- `python3 scripts/audit_loop.py --self-test` → exit 0, `Fail-closed sentinel evaluator verified against 15 adversarial test vectors` (was 7).
- `make test` → `Ran 248 tests ... OK` (was 210: +11 sweep, +7 reconcile, +20 envelope, +1 inverted PUSH-main still counted).
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 28 checks passed, 0 failed.` (untouched this wave, still green).
- Real-report sanity: current `AUDIT_REPORT_FINDINGS.md` still evaluates `STATUS: FINDINGS_DETECTED` (explicit sentinel; table scan alone gives ledger=24 PARTIAL hits, matrix=0, sabotage=12 UNVERIFIABLE — fail-closed, consistent with pre-fix behavior).

## M6 (#79) — evaluator hardening

- Header: `^#{1,6}\s*HR-[\w.-]+` (any depth, colon optional). Ledger: per-cell scan of every pipe-line after stripping `[*_~``]` + emoji (❌ U+274C covered); token `\b(BROKEN|PARTIAL)\b` case-insensitive. Pipe-scoped deliberately (prose "broken" still clean). Defect-Matrix: body cells only (header/separator skipped) in tables under a "defect matrix" heading or with a "Priority" header cell; P0–P3 case-insensitive. Sabotage: body rows of sabotage-headed/"Caught?"-column tables whose last cell (decorations stripped, lowered) != `yes`.
- RED: all 8 derived vectors returned NO_FINDINGS pre-fix (`/tmp/opencode/red_m6.py`, 8/8 MISS); FINDINGS_DETECTED post-fix (self-test asserts each). 7 pre-existing vectors kept verbatim.

## M7 (#83, #84) — governance gates

- #83: TPM-seat set read-only from `fleet.yaml` (tpm/scrum `roles:` keys + member `session:`/`address:` ids + local-parts; = `tpm-scrum-lead` ×3 forms today; unreadable catalog → operator-only). auth: SATISFIED: requires exact `blockedOn` equality + operator/TPM authorship + ≥1 `qitem-*` evidence ref (dangling → stay-blocked + retry); legacy notes require the full `auth:<what>` string; authority = operator or TPM for auth:, operator-only elsewhere. Rearm stays token-based. Non-auth: paths behavior-identical (pinned by scope-guard test).
- #83 cases A (self-written SATISFIED:) and B (token-overlap blocker + legacy-overlap note) → stay-blocked; non-vacuity proven by in-test overlap assertions and fleet-grounded TPM ids.
- #84: `queue_terminal` state-only (removed `TERMINAL_NOTE_RE` + its uses; no other importers); `^QA PASS\b` + no negator (`not|no|never|n't`) + no fail-token for QA affirmations in notes and tracker cells; `placed`/`closed` void under negation; staged/dispatched/parked unchanged. Fixture ("QA pass NOT granted; NOT placed", in-progress) → reconcile exit 1 `stale-state`, generate_trackers exit 1 NEEDS-HUMAN-REVIEW, zero `PROPOSED-CELL:::` markers (pre-fix both exited 0 "in sync").
- RED: 6/7 reconcile + 9/11 sweep new tests failed pre-fix; full suite green post-fix.

## M8 (#92) — envelope semantics (derived row table)

Issue bodies are not on disk; rows derived from the M8 spec sentence + the reaudit one-liner (`.git/hooks, AGENTS.md, fleet/, PUSH main, 9999 expiry, issued-after-expiry, BY WHOM nobody`). Each row = one new test, each REFUSE (rc=1) post-fix, 19/20 RED pre-fix (colon path already refused via the section parser; now double-layered):

| # | Row | Pre-fix | Post-fix | Test |
|---|---|---|---|---|
| 1 | Path `.git/hooks/x` | ACCEPT | REFUSE | `test_dotgit_path_refused` |
| 2 | Path `.pi/agent/x` | ACCEPT | REFUSE | `test_dotpi_path_refused` |
| 3 | Path `.agents/y` | ACCEPT | REFUSE | `test_dotagents_path_refused` |
| 4 | Path `fleet/fleet.yaml` | ACCEPT | REFUSE | `test_fleet_dir_path_refused` |
| 5 | Path `scripts/run.sh` | ACCEPT | REFUSE | `test_scripts_dir_path_refused` |
| 6 | Path `AGENTS.md`, `docs/AGENTS.md` | ACCEPT | REFUSE | `test_agents_md_path_refused` |
| 7 | Path `-evil` | ACCEPT | REFUSE | `test_leading_dash_path_refused` |
| 8 | Path `src/a:b` | REFUSE (parser) | REFUSE (both layers) | `test_colon_path_refused` |
| 9 | Path `src/café/` | ACCEPT | REFUSE | `test_non_ascii_path_refused` |
| 10 | Path `src/100%x/` | ACCEPT | REFUSE | `test_percent_path_refused` |
| 11 | `PUSH main` | ACCEPT | REFUSE | inverted `test_push_bare_main_refused` |
| 12 | `PUSH master` | ACCEPT | REFUSE | `test_push_master_refused` |
| 13 | 9999 expiry (> issued+14d) | ACCEPT | REFUSE | `test_far_future_expiry_refused` |
| 14 | issued-after-expiry | ACCEPT | REFUSE | `test_issued_after_expiry_refused` |
| 15 | future-issued (issued > now) | ACCEPT | REFUSE | `test_future_issued_refused` |
| 16 | live + expired deadlines (min governs) | ACCEPT | REFUSE | `test_multiple_deadlines_governed_by_min` |
| 17 | unknown owning seat | ACCEPT | REFUSE | `test_unknown_owning_seat_refused` |
| 18 | `BY WHOM: nobody` | ACCEPT | REFUSE | `test_by_whom_nobody_refused` |
| 19 | `BY WHOM: go-backend-eng` (non-TPM seat) | ACCEPT | REFUSE | `test_by_whom_non_tpm_seat_refused` |
| 20 | audit record without link shape | ACCEPT | REFUSE | `test_unlinked_audit_record_refused` |
| — | `PUSH feat/wave-12-canary` (control) | ACCEPT | ACCEPT | `test_explicit_push_with_branch_accepted` |
| — | fully-populated envelope (control) | ACCEPT | ACCEPT | `test_fully_populated_envelope_accepted` (+ wrapped variant) |

- Supporting semantics: vocab = 153 fleet ids (roles + sessions/addresses + local-parts); tpm_ids = exactly the 3 TPM forms. Link-shaped = URL | qitem id | digit-bearing hex ≥7 | `commit` | slashed path (calibrated so both ACCEPT fixtures stay green; recorded in NOTES with the "xyz123 accepts as named human" limitation).
- Spec-mandated inversion only: `test_push_bare_main_accepted` → `test_push_bare_main_refused` (one-line NOTES reason recorded; #92 names PUSH main explicitly). No other test weakened.

## Self-audit notes (unfinished / deferred, stated plainly)

- M6–M8 touch nothing in `verify-rigs.sh`, `Makefile`, `render-seat.py`, `seat-sandbox.sh`, `send-authenticated.sh`, `fleet/fleet.yaml`, `generate-rigs.py` — no regen needed (no generated leaves affected); verified by `git status` (only the listed scripts/tests/NOTES/report touched).
- `check-envelope.py` and `sweep-typed-blocks.py` each carry their own fleet.yaml loader copy (no shared import, per the repo's no-shared-files convention for these tools); the two loaders overlap partially (TPM set vs full vocab) — a future dedup could share one, at the cost of a cross-script import the codebase currently avoids.
- Bare `TPM` as BY WHOM resolves to the fleet's single tpm/scrum seat. If a second TPM-role seat is ever added, the shorthand turns ambiguous and must be retired (NOTES records this).
- "QA PASS, no issues"-style cells are now non-terminal (spec-literal negator list). The canonical emitted cells never contain standalone no/not/never/n't/fail tokens, so no existing flow regresses (248/248 green proves it).
- No QA dispatch performed (per wave instructions). Tree left with the three implementation commits; this report is the only untracked file.
