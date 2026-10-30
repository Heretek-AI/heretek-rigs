# Tasks: 2026-10-30-seat-repair

## Authoring (this landing)

- [x] Author change package (proposal/spec/design/tasks per approved design)
- [x] Verify-only the 2 lobotomized seats (read-only; §6 of design.md)

## Implementation (repo change — TDD)

- [ ] live-health `seat-shell-paths` check: red tests (trip/clear,
  strict promotion, allowlist, dead-daemon) → implement → green
  (12 new tests green; 27 pre-existing green; live smoke: 24 dangling
  named, 51/51 assessed, exit 0, 16s)
- [x] Full validation: `openspec validate 2026-10-30-seat-repair` rc=0;
  `./scripts/verify-rigs.sh --check-only` 39/0 (NO new V-block);
  `make test` FULL (657 run, 0 failures); `audit_loop.py --self-test`
  PASSED; `generate-rigs.py --check-idempotent` byte-identical;
  negative grep (commit/landing-write/exec-on-behalf-of-seats → empty
  beyond the send-probe path)

## Live execution (bounded repair, §2–§5 of design.md)

- [x] B1 (6): kickoff snapshot → per-seat protocol × 6 → close-out
  (ps + queue-diff + live-health) — GREEN 6/6, 0 skips; close-out in
  runbook §4 (watchdog-wake attribution, zero wave writes)
- [x] B2 (6): same — GREEN 6/6, 0 skips; close-out in runbook §6
  (new-row + structural diffs attributed to watchdog/seat-self,
  zero wave writes; ps diff confined to B2 seats)
- [x] B3 (6): same — GREEN 6/6, 0 skips, incl. DEVIATION D1
  (ux-research-analyst probe declined by seat policy; REPAIRED on
  equivalent in-turn shell evidence); close-out in runbook §8
  (terminal-row listing semantics + `-a` methodology fix)
- [x] B4 (4): same — GREEN 4/4, 0 skips; close-out in runbook §10
  (263→263 rows, zero added/removed/state-changes; final
  live-health names ONLY the 2 verify-only lobotomized)
- [x] Evidence: `docs/evidence/seat-repair-2026-10-30/runbook.md`
  (per-batch kickoffs, launches with rcs, probe replies, health
  snapshots, skips with reasons, D1 deviation, watchdog-wake
  attributions) + ps snapshots per batch + queue snapshots per
  batch + `docs/reports/seat-repair-implementation.md`
- [x] AGENTS.md: ONE surgical docs-map row

## Gate

- [x] Triad (agency-qa red-proof + agency-drift-guard audit) → VERDICT
  before any PR (Refs #147 — never Closes); outcome: agency-qa PASS (qa-red-proofs.log) + agency-drift-guard VERDICT: PASS (seat-repair-verification.md), both committed pre-merge
