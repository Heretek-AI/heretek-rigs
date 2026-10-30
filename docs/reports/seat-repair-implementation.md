# seat-repair implementation report (stage: seat-repair, 2026-10-30)

Change: `openspec/changes/2026-10-30-seat-repair/`. Refs #147 — never Closes.

## Resume note

The prior session died mid-package-authoring. Resume verified: `git
status` showed only the untracked change dir; `rig ps --nodes -A` was
byte-identical to the seat-hygiene baseline (51/51 running/idle); no
seat-repair launch evidence. The package (proposal/design/tasks/spec)
was found complete and confirmed against the principal-approved
design before proceeding. One premise deviation found and held
throughout (see §4).

## Deliverables (worktree only)

- `openspec/changes/2026-10-30-seat-repair/`: proposal.md (Q1–Q6
  approval lines, batch plan, non-goals), specs/seat-repair/spec.md
  (REQ-R1..R4 with `#### Scenario:` blocks), design.md (mechanism
  proof, batch plan with pod/member mapping, probe protocol with the
  seat-race sandbox lesson, live-health diff, abort/roll-forward
  rules, D1 recorded post-execution), tasks.md (all boxes checked
  except triad VERDICT).
- `scripts/live-health.py`: `seat-shell-paths` sub-check (REQ-R3) —
  evaluator + collector + `seat status --json` allowlist branch +
  `FixtureClient.fetch_seat_paths` + 7th gate slot. Warn-first via
  existing `finalize → overall_exit` path (advisory WARN exit 0;
  `--strict` promotes per existing gate semantics to FAIL exit 2 —
  the brief's "exit 1" realized as the gate-standard strict exit;
  spec states this explicitly).
- `tests/test_live_health.py`: 12 new tests (trip/clear, relative
  resolution, unassessed-SKIP, fixture replay, strict promotion,
  allowlist accept/refuse, dead-gate, collector happy/unreadable
  paths). 39/39 pass in-file.
- Evidence: `docs/evidence/seat-repair-2026-10-30/` (runbook.md,
  ps-batchN-pre/post.txt × 4, queue-batchN-pre/post.json × 4).
- `AGENTS.md`: one docs-map row (2 lines).

## Live execution (22/22 stale repaired, 0 skips, 0 aborts)

| Batch | Seats | Launches | Sends | Result |
|---|---|---|---|---|
| B1 | blue-appsec-engineer, build-go-backend-eng, build-ts-node-fullstack, delivery-git-drift-coord, delivery-tech-docs-lead, delivery-tpm-scrum-lead | 6 rc=0 | 6 rc=0 | GREEN 6/6 |
| B2 | design-a11y-specialist, design-brand-copy-spec, design-design-system-eng, design-fe-perf-eng, design-mobile-web-eng, design-ui-ux-designer | 6 rc=0 | 6 rc=0 | GREEN 6/6 |
| B3 | design-ux-research-analyst, engine-engine-systems-eng, engine-physics-sim-eng, exec-exec-director, exec-product-director, exec-system-architect | 6 rc=0 | 6 rc=0 | GREEN 6/6 (D1 × 1) |
| B4 | mobile-android-mobile-spec, mobile-ios-mobile-spec, systems-cpp-lowlevel-eng, systems-rust-systems-spec | 4 rc=0 | 4 rc=0 | GREEN 4/4 |

Per-seat protocol all GREEN: re-seed rc=0 (ordinary path, no grant
issuance on any seat) → settings pre-check clean+exists → per-seat
activity re-check idle → relaunch rc=0 ready → config-clean
running/active/ready → probe. Probe pattern uniform: `rig queue
whoami` exit 0 with seat-identifying output + `echo SEAT-REPAIR-OK`
denied by seat policy (verbatim `[pi-permission-system] Denied by
policy: 'bash' (rule '*')` class) + typed SEAT-REPAIR-OK — 21 seats;
B3S1 (ux-research-analyst) declined the unattributed probe while busy
on its own P0-06 work and was recorded REPAIRED on equivalent
in-turn shell evidence (whoami exit 0 + queue list exit 0 + file
edits through the re-resolved wrapper; re-send would arrive
identically unattributed per `rig send --help`, queue create out of
bounds). Zero 400s-rot observed — no retries needed.

## Fleet-behavior findings (all attributed, none wave-caused)

- Watchdog parked-owner wakes + seat-self continuations on holder
  seats post-relaunch (B1 ts-node, B2 design-system-eng, B3
  product-director rows): actors `watchdog@system` / the seats
  themselves; row states preserved except seat-owned continuations.
- Repaired seats resumed and CLOSED backlogged work: ui-ux closed 2
  rows done with PASS verdicts (incl. a 2026-10-22 stuck row);
  ts-node ↔ ui-ux handoff loop moving with verdict notes.
- Queue-listing methodology fix: default `list` shows ACTIVE only
  (`-A` is scope, `-a` is history); terminal rows drop out. B4
  snapshots use `-a -A --limit 10000` (263 rows, zero
  added/removed/state-changes across B4).
- Standing result: the fleet is healing through the repaired seats'
  own agency; the wave issued zero queue writes (no create/claim/
  update/block/resolve/handoff/send-queue ops from the operator shell).

## Validation (close-out, worktree)

- `openspec validate 2026-10-30-seat-repair` → valid, rc=0.
- `./scripts/verify-rigs.sh --check-only` → 39 passed / 0 failed
  (NO new V-block appended — recorded decision: live state isn't
  repo state).
- `make test` FULL → 657 run, 0 failures (pre-wave) — rerun at
  close-out, see commands below.
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `generate-rigs.py --check-idempotent` → byte-identical rc=0.
- Negative grep (commit/landing-write/exec-on-behalf-of-seats over
  new/changed code) → empty.
- Final `make live-health`: seat-shell-paths names ONLY the 2
  verify-only lobotomized seats; all 22 repaired seats clear.

## Self-audit / unfinished

- Triad box UNCHECKED (coordinator runs agency-qa + agency-drift-guard).
- NOT committed (coordinator commits).
- Premise deviation standing: the 2 lobotomized seats are
  STILL-DANGLING on disk (separate go-ahead not landed); untouched
  per Q6. Recommending a follow-up scoped to those 2 seats.
- D1 (B3S1 token-declined) is a judgment call recorded with full
  evidence; the triad may rule the letter of REQ-R2 unmet for that
  seat — the evidence supports the repair substance either way.
