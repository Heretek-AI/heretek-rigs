# Implementation report — 15-auth-envelope (Refs #15)

Branch `feat/15-auth-envelope`, base `main @ 471f628`. The issue's ask (a):
standing pre-authorization envelopes for defined slice classes, plus the
staleness measurement that justifies them (options (b) freeze discipline
and (c) accept-the-lag recorded as considered-and-deferred in
`design.md`). Detection, classification, loud refusal only — nothing
written here lands a diff, commits, advances a row, or dismisses anything
(design D8, fixtures-only + propose-only; no daemon edits, no upstream
filing, no live-fleet proofs, no auto-commit and no self-executing
envelopes ever). Refs #15 on everything; never Closes #15.

New module vs extending `send_identity.py` (design D-point): new module
`scripts/auth_envelope.py` — wave-9 HMAC/nonce discipline is reused by
import-pattern (cached `seed-rig.py` module load for `_redact_for_log`,
same `seen`-set single-acceptance semantics), while the extra premise
fields (diff-hash, scope, mandatory expiry) carry their own validation.
V31 pins behavior, not location.

## S0 — #15-pattern fixtures + pre-fix silence proof

- New `tests/test_auth_envelope_prefix.py` (8 tests): #15 fixture builders
  (authorized one-liner premise `aaaaaaaaaaaaaaaa` scope
  `src/include/hash.h` with premise/verify timestamps vs multi-file
  drifted landing `bbbbbbbbbbbbbbbb` paths `src/include/hash.h,
  src/extra/eleven.c` at +720s; the premise/verify/landing spread) plus
  permanent pins on the frozen transcript (silence markers,
  attribution-ABSENT, envelope-ABSENT, zero 40+ runs) and on fixture
  genuineness (verified premise present, landing genuinely drifted,
  spread ordered, hashes distinct). Stays green before and after (wave-81
  frozen-transcript pattern).
- New `docs/evidence/15-auth-envelope-prefix.md`: verbatim transcripts —
  `reconcile exit: 0` / `stalled-premise-drift signal: ABSENT`,
  `premise-age attribution: ABSENT` (`grep -c` 0 over
  `reconcile_model.py`), `envelope validation: ABSENT` / `landing
  authorization: NONE` (no `scripts/auth_envelope.py`, no
  mint/validate on `send_identity.py`).
- Acceptance: `unittest tests.test_auth_envelope_prefix` 8 OK; evidence
  grep exit 1 (clean); verify tree behavior unmodified at S0 time
  (38 passed, 0 failed on the untouched tree).

## S1 — premise-drift classification + premise-age attribution

- `scripts/reconcile_model.py`: `_parse_premise` (authorized premise hash
  + scope + premise/verify timestamps from the tracker Status cell; rows
  declaring no premise never match) / `_parse_landing` (landing diff hash
  + paths + landing timestamp from the latest queue-trail landing record;
  open authorizations with no landing record stall explicitly) /
  `_scope_covers` (exact-path or directory-prefix coverage; anything else
  is a breach) / `attribute_premise_age` (premise age + verify-to-landing
  spread + one-line note; report-only, never raises, never writes) / shared
  `stalled_premise_drift_diff` classifier (hash mismatch or scope breach or
  open-without-landing → `stalled-premise-drift` with attribution; clean
  premises quiet); `diff_row` tail tries gate, then idle-park, then
  premise-drift (no parallel mapping anywhere); `render_diff` renders the
  class review-only (NEEDS-HUMAN-REVIEW + SUGGESTED, no PROPOSED-CELL —
  same withhold shape as idle-park, attribution line generic).
- `scripts/generate_trackers.py`: OTHER-arm carve-out consulting the shared
  premise-drift helper (REQ-G5), rendered review-only (class stays outside
  `PASTE_READY_CLASSES`). Without this the TPM path renders drifted rows
  as generic silent-OTHER.
- New `tests/test_auth_envelope.py` (21 tests): REQ-E2 flagged + premise
  age 720s/420s + quiet guards (clean, no-premise) + open-authorization
  stall + scope-breach + report-only byte-identity + end-to-end exit 1/0 +
  classifier-removal pinning; REQ-E1 clean-validates + drift/scope/
  expiry/replay/bad-MAC/no-seen-set refusals + row-untouched +
  redaction + no-self-execution + recovery state-change.
- `docs/evidence/15-auth-envelope/red-proofs.log`: FAIL-ONLY pre-fix run
  (reverted tree: exit 0 silent, zero markers, no envelope module) plus
  S1a (tail → None restores silence; restore → stalled) / S1b (clean quiet
  both ways) / S1c (bypass → drifted authorized RED; restore → refused) /
  S1d (replay + expiry attacks refused; restore → still refused) entries
  from live /tmp sabotage runs with byte-identical restores.
- Acceptance: corpus 21 OK; full suite `Ran 628 tests OK`; idempotent
  byte-identical.

## S2 — envelope mint/validate + non-dismissible recovery + V31

- New `scripts/auth_envelope.py` (executable): `mint_envelope` binding
  diff-hash + scope + mandatory expiry epoch + single-use nonce
  (HMAC-SHA256 `v2` wire format, `!cat`-rendered 0600 stores, mint-side
  scope jailbreak tail) / `validate_envelope` pure check + redacted log
  (shape → MAC → expiry → replay → hash → scope; refused landings never
  consume the nonce, the store never rewinds; `seen=None` fails closed) /
  `write_envelope_exclusive` (shared O_EXCL 0600 guard). No subprocess, no
  shell, no commit call anywhere in code (docstrings stripped before the
  pin check) — the module cannot execute or land anything.
- S2.2 rides the existing `check_recovery_dismissal` close-time guard
  (fail-closed refusal on byte-identical snapshots, redacted log, performs
  no write, never done): exercised with premise snapshots
  (`recovery-premise-01` refused while the S02 row is unchanged, permitted
  once the owner re-verifies) in the corpus.
- `scripts/verify-rigs.sh`: appended V31 block only
  (`== V31. Pre-Authorization Envelopes (15-auth-envelope) ==`, one
  `ok()`); model markers + emitter import + mint/validate markers with
  HMAC/nonce/expiry/scope checks + inline live refusal behavior (clean
  authorized; drift/scope/expiry/replay refused) + no-inline-secret +
  no-self-exec code scan + sweep refusal markers + S0 evidence lines +
  red-proof lines + corpus floor ≥ 16 (21, 0 skips). V19 freeze bump
  38 → 39 (`passes + 5`) per the freeze's own rule — the only V1–V30
  touch, same as waves 9/4/81. `AGENTS.md` / `README.md` /
  `docs/USER_GUIDE.md` live counts move 38 → 39 with it (V19-gated).
  `HANDOFF.md` 38-mentions left alone (prior-session file, not V19-gated).
- Acceptance: V31 PASS (21 corpus tests); `make test` `Ran 628 tests OK`;
  `audit_loop.py --self-test` PASS; idempotent byte-identical.

## S3 — runbook, docs, wave closeout

- `docs/evidence/15-auth-envelope-runbook.md` (new): flow A (issuance +
  landing validation: verbatim authorized/refused lines), flow B
  (drift-triage: verbatim exit-1 stalled-premise-drift diff with premise
  age), flow C (recovery needs row state change) — all exercised against
  /tmp scratch fixtures; premise-age 720.0s / verify-to-landing 420.0s
  sample recorded as #17 inputs. `diff-hash` ×1+, `premise age` ×4;
  evidence grep exit 1.
- AGENTS.md docs-map line for this change: already present at base
  (`AGENTS.md:76`), no edit needed; no rule-text changes in S3 (the
  38 → 39 count move rode with S2 as freeze mechanics).
- `docs/reports/15-auth-envelope-verification.md` (new): drift-guard
  re-verification ending `VERDICT: PASS` (read from disk).
- `openspec/changes/2026-10-29-15-auth-envelope/` left unarchived for the
  coordinator merge wave. Refs #15 everywhere; never Closes #15.

## Commands run (exit codes)

- `python3 -m unittest tests.test_auth_envelope_prefix -v` → 0 (8 OK)
- `python3 -m unittest tests.test_auth_envelope` → 0 (21 OK)
- `python3 -m unittest discover -s tests -p 'test_*.py'` → 0
  (`Ran 628 tests OK`)
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/15-auth-envelope-prefix.md
  docs/evidence/15-auth-envelope-runbook.md` → 1 (clean); same over
  `scripts/auth_envelope.py` + `scripts/reconcile_model.py` → 1 (clean;
  test files carry long identifiers per repo precedent, evidence and
  scripts carry none)
- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 scripts/generate-rigs.py
  --check-idempotent` → 0 (byte-identical; generation inputs untouched —
  no regen required for this wave); plain `--check-idempotent` → 2
  (dirty-tree gate refuses the uncommitted worktree by design —
  coordinator runs post-commit; a dev-regen stamp was reverted via
  `git checkout -- specs rigs rosters registry`, verify back to 39/0)
- `./scripts/verify-rigs.sh --check-only` → 0: `SUMMARY: 39 checks
  passed, 0 failed` with V31 PASS and V1–V30 intact
- `python3 scripts/audit_loop.py --self-test` → 0 (SELF-TEST PASSED)

## Self-audit notes (unfinished stated plainly)

1. Nothing unfinished: fixtures, prefix evidence, classifier, envelope
   module, V31, corpus (21 + 8), red-proofs (S1a–S1d + FAIL-ONLY),
   runbook with #17 samples, and both reports are complete and green.
   Left uncommitted in the worktree for the coordinator (per stage
   instructions — no commit, no push).
2. No daemon edits, no upstream filing, no live-fleet proofs, no
   auto-commit and no self-executing envelopes (non-goals honored; REQ-E3
   pinned by a no-executor code scan in both the corpus and V31). Dummy
   keys only; every new log path through `_redact_for_log`; zero
   unredacted secret-shaped strings in evidence and scripts.
3. Zero stubs, zero placeholders, zero skipped tests in delivered code; no hand-edited
   generated leaves (`specs/`/`rigs/`/`rosters/`/`registry/` untouched —
   no regen required since `fleet/` and the generator are unmodified).
   Every fix carries a pinning test proving it non-vacuous (wave-81
   lesson): classifier-removal silence, clean-quiet both ways, drift
   bypass, replay/expiry attacks, redacted refusal, row-untouched,
   no-executor surface.
