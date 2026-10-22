# Tasks: remediate-38-unblock

Execution waves: reproduce (T1) → implement sweep + runbook (T2–T4) →
upstream artifact (T5) → acceptance incl. returnable replay (T6) → report
(T7). Map 1:1 to `specs/block-reevaluation/spec.md`. Specs ONLY — no
implementation in this package.

- [ ] T1 — Reproduce the stuck shape (REQ-BU7): on a test/staging qitem (or
      a faithful dry-run harness — NEVER on live W1 rows), park with a typed
      `external:<what>` blocker, land verdict-style evidence + a note-only
      `update`, and prove the row stays blocked (note-without-state
      semantics). Record the transcript as the pre-fix baseline.
      Testable: baseline transcript shows blocked-after-note.
- [ ] T2 — Predicate-at-park + sweep core (REQ-BU1/BU2/BU5): implement the
      predicate carrier, the transitions-cursor sweep with triggers (a) and
      (b), unpark via `update --state in-progress --reopen` with evidence
      citation, `--dry-run` mode, idempotency cursor.
      Testable: `update` note-only on a parked test row triggers unpark on
      next sweep run; rerun sweep → no duplicate transitions; `--dry-run`
      mutates nothing.
- [ ] T3 — Satisfy convention + no-timer-only rule (REQ-BU3/BU4): implement
      and document the `SATISFIED:` (or implementer-fixed equivalent) note
      convention; malformed records ignored + logged.
      Testable: well-formed satisfy note → unpark within one cycle;
      malformed note → stays blocked + recorded evaluation.
- [ ] T4 — Seat runbook (REQ-BU1/BU4, design constraint): park-time
      checklist (predicate required; live wake required) in editable
      `docs/` — NOT in generated leaves. If charter/generator changes are
      needed, they go via `fleet/` edits + regen + `make verify`.
      Testable: runbook exists under `docs/`; `git status` shows zero
      hand-edits under `specs/ rigs/ rosters/ registry/`.
- [ ] T5 — Upstream request (REQ-BU6): file `@openrig/cli` feature request
      for a `satisfy` transition with the W1-03/W1-04 evidence; record
      URL/number in the implementation report. Sweep MUST NOT depend on it.
      Testable: issue URL present in report; sweep works with today's CLI.
- [ ] T6 — QA red-proofs + returnable (REQ-BU5/BU7): (a) replay the
      W1-03/W1-04 shape → unpark within one sweep cycle, no operator
      `--state` surgery; (b) ambiguous-evidence sabotage → stays blocked +
      recorded evaluation; (c) dangling-blocker sabotage → stays blocked +
      WARN naming the reference; (d) sweep NEVER emits `state=done`.
      Record all four.
- [ ] T7 — Report: write `docs/reports/remediate-38-unblock-
      implementation.md` (files changed, upstream issue URL, verification
      outputs). `make verify` stays 22/0 (or 23/0 if the #43 check lands
      first — record which).
