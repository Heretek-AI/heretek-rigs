# Tasks: remediate-45-live-health

Execution waves: prove data sources (T1) → prerequisite (T2) → implement
(T3–T5) → acceptance incl. returnable replay (T6–T7) → report (T8). Map 1:1
to `specs/live-health/spec.md`. Specs ONLY — no implementation in this
package.

- [ ] T1 — Pin parseable read-only sources (REQ-LH2/LH8): from the stage
      worktree against the live daemon, prove the exact flag combos yielding
      parseable output for `rig queue overdue`, `rig queue undelivered`,
      `rig queue list`, `rig queue transitions`, `rig ps --nodes`. Record
      outputs. If bare `--json` mixes the #44 human trailer with no clean
      combo, STOP: record dependency on the #44 fix and do not proceed.
      Testable: pasted command lines + parseable output captured in evidence.
- [ ] T2 — P0 heartbeat prerequisite (REQ-LH3): set sane nonzero
      `heartbeat_sec` in `fleet/fleet.yaml` (surgical text edit only, never
      `yaml.safe_dump`), regen via `generate-rigs.py`, `make verify` 22/0.
      Testable: `grep -c "heartbeat_sec: 0" fleet/fleet.yaml` == 0 (or an
      explicitly documented exception list); verify still 22/0.
- [ ] T3 — Gate skeleton (REQ-LH1/LH2): new `scripts/live-health.*` with
      PASS/WARN/FAIL/SKIP per sub-check, `sources: N ok, M skipped` summary,
      `make live-health` target independent of `make verify`.
      Testable: kill/point-away the daemon → all live sub-checks SKIP by
      name, no healthy banner, exit 0.
- [ ] T4 — Pickup + stuck + undelivered sub-checks (REQ-LH4/LH5/LH6):
      claim→first-transition latency, `overdue` age histogram, `undelivered`
      listing with tunable `T_pickup`/`T_stuck`/`T_undelivered` and effective
      values printed per run.
      Testable: synthetic claimed-untouched row (test rig or staging qitem)
      older than thresholds is named by ID in WARN output.
- [ ] T5 — Heartbeat + seat-idleness sub-checks (REQ-LH3/LH9) + promotion
      policy doc (REQ-LH7): `T_hb` default, UNCONFIGURED reporting,
      `rig ps` idle-at-prompt join, WARN→FAIL promotion criteria documented.
      Testable: with P0 landed, all-configured fleet reports PASS on heartbeat
      when fresh; a stale seat is named.
- [ ] T6 — QA red-proofs (REQ-LH7/LH8): (a) replay the 2026-10-22 50-minute
      idle shape (three claimed-untouched rows, or faithful synthetic
      equivalents with recorded timestamps) → WARN/FAIL naming all three
      IDs; (b) data-source-killed run → SKIP, never PASS; (c) state-mutation
      sabotage: instrument/stub one `rig queue` verb to detect writes, run
      the gate, assert zero mutating calls. Record all three.
- [ ] T7 — Acceptance: `make live-health` (WARN + row IDs on incident-shaped
      fleet), `make verify` 22/0 unchanged, thresholds/flags documented.
- [ ] T8 — Report: write `docs/reports/remediate-45-live-health-
      implementation.md` (files changed, verification outputs).
