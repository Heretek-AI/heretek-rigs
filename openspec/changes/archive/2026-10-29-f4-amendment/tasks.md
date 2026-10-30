# Tasks: F4 amendment (amendment → classifier → corpus; fixtures only)

Standard baseline for EVERY milestone (must be green before moving on):

```bash
./scripts/verify-rigs.sh --check-only            # 39 passed, 0 failed (40/0 only iff V33 appended with freeze note)
python3 scripts/generate-rigs.py --check-idempotent   # HERETEK_RIGS_ALLOW_DIRTY=1 on the dirty dev tree; revert regen side-effects after
python3 scripts/audit_loop.py --self-test
```

Secrets rules (all milestones): real keys ONLY in `~/.config/heretek-rigs/secrets/` (0700/0600), dummy keys in
scratch/tests (`/tmp`, 0600), no secret-shaped strings in evidence. Refs #15 + Refs #134 on every message
(never `Closes #15`, never `Closes #134`). No live seats, no live queue/rows, no auto-commit surface (ever).
Nothing under `openspec/` changes after this spec except the end-of-wave archive. Generated leaves (`specs/`,
`rigs/`, `rosters/`, `registry/`) never hand-edited. A pure classifier logic change needs NO regen, but
`--check-idempotent` must still prove byte-identical.

## A0 — amendment package (FIRST; nothing else lands before it)

- [x] A0.1 `proposal.md`: goal, non-goals (no REQ-E2 rewrite, no live execution, no auto-commit surface,
  never Closes #15/#134), amendment-first order stated.
- [x] A0.2 `specs/auth-envelope/spec.md`: MODIFIED delta ADDING REQ-E5 with `#### Scenario:` blocks
  (fires on clean-landing-no-envelope where a lookup exists; quiet when lookup absent/empty; quiet on
  matching envelope; mismatch binding fires; report-only attribution; red-proof scenario). REQ-E2 text untouched.
- [x] A0.3 `design.md`: rationale resolving the §3 contradiction (timestamps-vs-presence, why new-REQ over
  revision, lookup threading design, F6/F7/F8 hooks used).
- [x] A0.4 `tasks.md`: this file (boxes: amendment, lookup+classifier, corpus+pins, red-proofs, V33 decision,
  compound, triad → VERDICT before any PR).

Acceptance (A0):

```bash
openspec validate 2026-10-29-f4-amendment   # exits 0
```

## A1 — envelope lookup + classifier (REQ-E5)

- [x] A1.1 `scripts/reconcile_model.py`: `envelope_by_id=None` keyword threaded through `diff_row` →
  `stalled_premise_drift_diff`; new `stalled_envelope_absence_diff` helper consulted only after E2
  establishes a clean landing; populated-lookup-missing/misbound ⇒ `stalled-envelope-absence` diff with
  premise-age attribution; absent/empty lookup ⇒ `None`; matching envelope ⇒ `None`. `render_diff`
  renders the new class as NEEDS-HUMAN-REVIEW + SUGGESTED (not paste-ready), same withholding as E2.
- [x] A1.2 `scripts/reconcile.py`: optional `--envelopes FILE` (JSON object qitemId → envelope record)
  loaded read-only via the shared loader; absent flag ⇒ `None` passed through (existing invocations
  behavior-identical). `generate_trackers.py` unchanged (default `None` ⇒ quiet).
- [x] A1.3 Negative check: `grep` new/changed code for `commit(`/landing-write calls ⇒ empty (REQ-E3 holds
  structurally); `test_clean_premise_stays_quiet` + `test_reconcile_end_to_end_clean_quiet` unmodified and green.

Acceptance (A1):

```bash
python3 -m unittest tests.test_auth_envelope -v   # exits 0 (E2 tests untouched, E5 tests green)
grep -nE '\.commit\(|git (commit|push)|queue-create|tracker-write|os\.system|subprocess' scripts/reconcile_model.py scripts/reconcile.py; test $? -eq 1
```

## A2 — corpus + anti-vacuity pins (past 634)

- [x] A2.1 New `TestEnvelopePresenceGating` cases in `tests/test_auth_envelope.py` (append-only; existing tests
  byte-intact): fires on populated-lookup-no-envelope; quiet on absent lookup; quiet on empty lookup; quiet
  on matching envelope; fires on mismatched binding; attribution report-only (no file bytes change);
  end-to-end `--envelopes` ⇒ exit 1 naming `stalled-envelope-absence`, without flag ⇒ exit 0 in sync;
  anti-vacuity pin (presence check patched out / lookup emptied ⇒ silent AND green-on-restore).
- [x] A2.2 Each pin must fail without the fix: assert the RED signature in the report (sabotage direction recorded).

Acceptance (A2):

```bash
make test   # expect ≥634 + new tests, 0 failures
```

## A3 — red-proofs (sabotage protocol, `docs/evidence/f4-amendment/red-proofs.log`)

- [x] A3.1 Probe R1: remove the presence check from the classifier ⇒ clean-no-envelope fixture reconciles
  silent (RED); byte-identical restore ⇒ stalled (GREEN). sha256 pins both ways.
- [x] A3.2 Probe R2: empty the lookup at the call site ⇒ silent (RED); restore ⇒ stalled (GREEN).
- [x] A3.3 Probe R3 (vacuity guard): confirm the pre-fix tree is silent on the new fixtures AND the new pins
  fail there (the gap was real, the corpus pins it).

Acceptance (A3): log exists with command transcripts, rc values, RED/GREEN signatures, and byte-restore checks.

## A4 — V33 decision (record either way)

- [x] A4.1 Decide per `design.md` §5: append V33 (new block + V19-freeze 39→40 note) ONLY if the classifier
  proves a gap the corpus cannot pin; otherwise record NO-V33 with reason. Default: none.

Acceptance (A4): decision + reason recorded in `docs/reports/f4-amendment-implementation.md` and the red-proofs log.

## A5 — compound + closeout (coordinator)

- [x] A5.1 Compound green (all binary): `openspec validate` rc=0; `verify-rigs.sh` 39/0 (40/0 iff V33);
  `make test` ≥634 0-failures; `audit_loop.py --self-test` PASSED; `generate-rigs.py --check-idempotent`
  byte-identical; E2 tests green unmodified; no `Closes` tokens wave-owned.
- [x] A5.2 `docs/reports/f4-amendment-implementation.md` (what changed, validation, skips); AGENTS.md ONE
  surgical docs-map row (≤5 lines, conventions verbatim).
- [x] A5.3 Triad → `VERDICT` read from disk before any PR. Do NOT archive (`openspec archive` forbidden here);
  do NOT commit (leave the tree for the coordinator); outcome: agency-qa PASS (qa-red-proofs.log) + agency-drift-guard VERDICT: PASS (f4-amendment-verification.md), both committed pre-merge.

Acceptance (A5):

```bash
openspec validate 2026-10-29-f4-amendment
./scripts/verify-rigs.sh --check-only
make test
python3 scripts/audit_loop.py --self-test
python3 scripts/generate-rigs.py --check-idempotent
git status --short   # only intended wave files; no strays committed
```
