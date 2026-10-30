# Design: F4 amendment — why a new REQ, and how the lookup threads through

Refs #15, Refs #134 (never `Closes`). Fixtures-only; no live seats, no live
queue/rows; no V33 unless a gap is proven (default: none).

## 1. The §3 contradiction (what this amendment resolves)

`openspec/specs/auth-envelope/spec.md` REQ-E2 says the reconciler MUST
classify "a row whose landing diff drifted from its authorized premise (or
which carries an open authorization with no matching envelope)" as stalled.
The parenthetical's clean-landing reading — open authorization + clean
landing + no envelope ⇒ stalled — contradicts the concrete REQ-E2 scenario
"clean premise stays quiet" (`spec.md:46-50`) and its two green corpus
pins:

- `test_clean_premise_stays_quiet` (`tests/test_auth_envelope.py:210-233`,
  no envelope wired, asserts `None`);
- `test_reconcile_end_to_end_clean_quiet` (`:431-442`, exit 0 "in sync",
  no envelope wired).

"Within the envelope window" in the quiet scenario is satisfied in
fixtures by timestamps, not by envelope presence — threading presence into
the existing classifier would flip both tests RED and break the full
corpus + V31. The rework-1 drift-guard audit
(`docs/reports/15-auth-envelope-verification.md` §3, F4 adjudication)
confirmed the skip on three independent grounds: no envelope registry
exists in the reconciler (comments only; neither `reconcile_model.py` nor
`reconcile.py` imports or calls `auth_envelope`); the scenario
contradiction above; and the review caution that the scenario governs.

## 2. Timestamps-vs-presence, resolved

The contradiction dissolves once the two signals are separated:

- **Timestamps** (premise/verify/landing) are the REQ-E2 quiet condition:
  a landing identical to its premise inside scope stays quiet regardless
  of envelope wiring. This is the scenario that governs, and it never
  changes.
- **Presence** (is there an envelope bound to this premise in a consulted
  registry?) is a NEW, strictly opt-in signal. It fires only where a
  caller explicitly provides a populated lookup. Absent/empty lookup ⇒
  the signal does not exist ⇒ quiet. The two green E2 tests call the
  classifier without a lookup, so they exercise the timestamp signal only
  and stay green byte-intact.

## 3. Why a new REQ instead of revising REQ-E2

1. Byte-intact preservation: revising REQ-E2's parenthetical or its quiet
   scenario would require touching normative text the corpus pins
   verbatim, invalidating V31's E2 assertions and the S1 red-proofs.
2. Audit continuity: the rework-1 `VERDICT: PASS` traces REQ-E1…E4 to code
   and tests line-by-line; a revision would reopen that trace. An
   addition (REQ-E5) extends the trace without disturbing it.
3. Falsifiability: REQ-E5's opt-in semantics give it its own RED
   signature (lookup emptied / check removed ⇒ silent), independent of
   the E2 S1a sabotage (classifier removed ⇒ silent). Two distinct
   sabotages, two distinct signatures, one log.

## 4. Lookup threading design

- **Store shape**: a plain index `envelope_by_id` mapping qitemId →
  envelope record (a dict optionally carrying `premise_hash`/`diff_hash`;
  a bare non-dict record counts as present). No store rewrites anywhere:
  the classifier only reads; `reconcile.py` only loads a JSON file into
  the index. No executor, no commit surface — REQ-E3 holds structurally.
- **Passing pattern**: same as `queue_by_id` — `reconcile.py main()`
  builds the index (from optional `--envelopes FILE`; absent flag ⇒
  `None`) and passes it through `diff_row(..., envelope_by_id=None)` into
  `stalled_premise_drift_diff(..., envelope_by_id=None)` and the new
  `stalled_envelope_absence_diff` helper. `generate_trackers.py` keeps
  calling with the default (`None` ⇒ quiet), so its OTHER-arm render is
  behavior-identical until a future wave explicitly threads a registry.
- **Gating position**: the E5 check runs only AFTER the E2 logic has
  established a clean landing (premise parsed, landing found, no drift,
  no scope breach). Drifted / scope-breached / landing-less rows keep
  their existing E2 stalls untouched; terminal rows never reach it.
- **Matching rule**: `None`/empty lookup ⇒ unknown, never gating (quiet).
  qitem present with identical bound hash (or hash-agnostic record) ⇒
  matching envelope (quiet). qitem absent, or bound hash differs from the
  premise hash ⇒ no matching envelope (stalled-envelope-absence).
  Fail-closed direction is deliberate AGAINST over-flagging: an
  unconfigured store must not stall the fleet; only a populated registry
  that lacks (or misbinds) this row gates it.
- **F6/F7/F8 hooks reused**: the E5 path runs downstream of the F8
  newest-to-oldest landing scan (the bound `landing` is the same one E2
  evaluated), the F7 segment-wise `..` scope guard (scope-covered means
  covered under the hardened rule), and the F6 fail-closed shape checks.
  No duplicate premise/landing parsing: the helper receives the already
  parsed `premise`, `landing`, and `queue_evidence`.

## 5. V33 decision rule (recorded either way)

V33 is appended (new block, V19-freeze note updated) ONLY if the new
classifier proves a behavior gap the corpus cannot pin — i.e. a sabotage
that restores silence while every corpus test stays green. The corpus
ships anti-vacuity pins for each E5 scenario precisely so that a gap
cannot hide; if all pins hold in both directions, no V33 is added and
`verify-rigs.sh` stays at 39/0. The decision and its reason are recorded
in `docs/reports/f4-amendment-implementation.md` and the red-proofs log.
