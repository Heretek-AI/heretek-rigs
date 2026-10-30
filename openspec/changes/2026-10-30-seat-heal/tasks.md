# Tasks: 2026-10-30-seat-heal

## Authoring (this landing)

- [x] Author change package (proposal/spec/design/tasks per approved design)
- [x] Kickoff re-verification (read-only): dangling set == expected 2,
  both idle, live-health names only the 2 → GO within cap 4

## Live execution (bounded heal, design.md §2–§4)

- [x] SH1 `build-java-kotlin-eng@heretek-omni-fleet` (pod build / member
  java-kotlin-eng): activity re-check idle → re-seed rc=0 → settings
  pre-check clean+exists → fresh relaunch rc=0 (native occupant
  `01a18e92-f120-76af-915a-886d1e544f1c`) → config-clean →
  probe PASS (`SEAT-HEAL-OK` + genuine whoami, echo-fallback) → HEALED
- [x] SH2 `build-python-backend-spec@heretek-omni-fleet` (pod build /
  member python-backend-spec): same protocol → HEALED (tmux sessionId
  `01M679DC8YV74MEC39AYQBDSY2`, native occupant `01a18e96-...`)
- [x] Class proof + close-out: post-run `make live-health`
  (`seat-shell-paths` PASS — all 51 resolve, zero dangling) + ps
  pre/post reconciled (ambient ticks only + healed-seat occupant
  refresh) + queue-list diff empty of wave writes (263→263, ambient
  pickup-evidence ticks only) + runbook
  (`docs/evidence/seat-heal-2026-10-30/runbook.md` with kickoff table,
  per-seat rcs + sessionIds + before/after shellPath, health
  snapshots, skips/stops) + `docs/reports/seat-heal-implementation.md`
- [ ] AGENTS.md: ONE surgical docs-map row

## Gate

- [ ] Triad (agency-qa red-proof + agency-drift-guard audit) → VERDICT
  before any PR (Refs #147 — never Closes)
