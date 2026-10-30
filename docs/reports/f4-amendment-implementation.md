# Implementation report — F4 amendment (`2026-10-29-f4-amendment`)

Stage `f4-amendment`. Worktree `.lane/trees/f4-amendment`, branch
`feat/f4-amendment` (from `main` 7644d9c). Refs #15, Refs #134 (never
`Closes #15`, never `Closes #134`).

## What changed

Amendment-first, then classifier, then corpus — per the principal-approved
design (grilling Q1–Q3):

1. **Amendment package** `openspec/changes/2026-10-29-f4-amendment/`:
   `proposal.md` (goal; non-goals: no REQ-E2 rewrite, no live execution,
   no auto-commit surface), `specs/auth-envelope/spec.md` (MODIFIED delta:
   ADDED REQ-E5 with six `#### Scenario:` blocks),
   `design.md` (timestamps-vs-presence rationale, why-new-REQ,
   lookup threading, F6/F7/F8 hooks, V33 decision rule), `tasks.md`.
   `openspec validate 2026-10-29-f4-amendment` → valid (rc=0).
2. **Classifier** (pure logic change; no regen needed):
   - `scripts/reconcile_model.py`: new `stalled_envelope_absence_diff`
     helper + `envelope_by_id=None` keyword threaded through `diff_row`
     → `stalled_premise_drift_diff`; clean-landing tail consults the
     helper (absent/empty lookup ⇒ `None`; matching envelope ⇒ `None`;
     missing/misbound ⇒ `stalled-envelope-absence` with premise-age
     attribution); `render_diff` renders the new class as
     NEEDS-HUMAN-REVIEW + SUGGESTED (not paste-ready), same withholding
     as E2. Reuses the F8-bound `landing`, the F7-hardened scope check,
     and the F6 shape discipline; no store writes, no executor.
   - `scripts/reconcile.py`: optional `--envelopes FILE` (JSON object
     qitemId → record) loaded read-only; absent flag ⇒ `None`
     (existing invocations behavior-identical).
   - `generate_trackers.py`: unchanged (default `None` ⇒ quiet).
3. **Corpus** (`tests/test_auth_envelope.py`, append-only — `git diff`
   shows +281/−0): new `TestEnvelopePresenceGating` (11 tests) covering
   every REQ-E5 scenario plus report-only attribution, both end-to-end
   directions (`--envelopes` flag/no-flag, match/no-match), an
   anti-vacuity pin (presence check patched out ⇒ silent), and a REQ-E3
   pin scoped to the new helper. REQ-E2 text, clean-quiet scenario, and
   both green E2 tests byte-intact and still green.
4. **Red-proofs** `docs/evidence/f4-amendment/red-proofs.log`: R1
   (check removed ⇒ 5 failures RED; byte-identical restore ⇒ GREEN),
   R2 (lookup emptied at call site ⇒ exit 0 silent RED; restore ⇒
   exit 1 `stalled-envelope-absence` GREEN), R3 (pre-fix tree: new pins
   fail/error, E2 quiet pins hold — gap real, corpus non-vacuous).
5. **AGENTS.md**: one surgical docs-map row for the active change.

## Validation (commands + exit codes, re-run by the implementer)

- `openspec validate 2026-10-29-f4-amendment` → valid, rc=0
- `python3 -m unittest tests.test_auth_envelope` → `Ran 38 tests OK`
  (27 pre-existing + 11 new)
- `make test` → `Ran 645 tests OK`, 0 failures (baseline 634 + 11 new)
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed,
  0 failed`, V31 PASS, exit 0
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`
- `python3 scripts/generate-rigs.py --check-idempotent` → `idempotence
  check passed (two consecutive runs byte-identical)`, rc=0, run with
  `HERETEK_RIGS_ALLOW_DIRTY=1` (dev iteration; plain `--check-idempotent`
  refuses on a dirty checkout by design, rc=2). Side-effects reverted:
  `git checkout -- registry` (resolvedCommit re-lag) AND
  `git checkout -- rigs specs fleet` (hermetic-mode drift — without
  `vendor_dir`/live clones the generator restores snapshots whose hashes
  differ from the network-baked committed leaves; environmental, not
  wave-caused). Final `git status --short` shows ONLY the intended wave
  files: `M AGENTS.md`, `M scripts/reconcile.py`,
  `M scripts/reconcile_model.py`, `M tests/test_auth_envelope.py`,
  `?? docs/evidence/f4-amendment/`,
  `?? docs/reports/f4-amendment-implementation.md`,
  `?? openspec/changes/2026-10-29-f4-amendment/`.
- Negative check: `grep -nE '\.commit\(|git (commit|push)|queue-create|tracker-write|os\.system|subprocess'`
  on the NEW code paths ⇒ empty (the module's pre-existing `run_rig`
  read-only fetcher is untouched; REQ-E3 holds structurally)
- Secret sweep: `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/f4-amendment/`
  ⇒ empty; fixtures use dummy ids + 16-hex hashes only
- `grep -rn 'Closes #1[35]\|Closes #134' openspec/changes/2026-10-29-f4-amendment/ docs/evidence/f4-amendment/ docs/reports/f4-amendment-implementation.md tests/test_auth_envelope.py` ⇒ empty

## V33 decision: NO (with reason)

Per `design.md` §5, V33 appends only if the classifier proves a gap the
corpus cannot pin. R1/R2/R3 each flip named pins RED and restore GREEN
on byte-identical files — no such gap exists. Corpus grows 634 → 645
with all pins bidirectional. `verify-rigs.sh` stays at 39/0; no V-gate
appended, no V19-freeze update needed.

## Skips (stated plainly)

- No live seats, no live queue/rows (fixtures only, per stage scope).
- No `generate-rigs.py` regen of leaves (pure classifier logic change;
  `--check-idempotent` proves byte-identical instead).
- `generate_trackers.py` OTHER-arm not threaded with a registry (default
  `None` ⇒ quiet); a future wave wanting tracker-side gating threads it
  explicitly.
- Do NOT commit; do NOT archive (left for the coordinator/triad).
- No triad verdict claimed here — `VERDICT` belongs to drift-guard.
