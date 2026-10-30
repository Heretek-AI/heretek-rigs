# seat-heal implementation report (2026-10-30, Refs #147 — never Closes)

Stage: seat-heal. Change: `openspec/changes/2026-10-30-seat-heal/`.
Branch: `feat/seat-heal` (worktree). No commit (coordinator commits).

## What ran

1. Authored the change package (`proposal.md`, `design.md`, `tasks.md`,
   `specs/seat-heal/spec.md`) per the principal-approved Q1/Q2 design;
   `openspec validate 2026-10-30-seat-heal` → valid, rc=0.
2. Kickoff re-verification (REQ-SH1, read-only): `rig ps --nodes
   --json --no-cleanup -A` (55 rows: 51 fleet running/idle + 4
   `@kernel` system rows), both targets running/idle, `settings.json
   shellPath` dangling on both, `make live-health` naming exactly the
   2 — set == expectation, ≤ cap 4 → GO.
3. SH1 `build-java-kotlin-eng`: activity idle → full member-fragment
   re-seed from main checkout (rc=0) → shellPath re-resolved to the
   durable wrapper (exists) → fresh relaunch rc=0 (native occupant
   `01a18e92-f120-76af-915a-886d1e544f1c`) → config-clean GREEN →
   probe PASS (genuine whoami + typed SEAT-HEAL-OK, echo denied by
   policy) → HEALED.
4. SH2 `build-python-backend-spec`: same protocol → HEALED (tmux
   sessionId `01M679DC8YV74MEC39AYQBDSY2`).
5. Close-out: `make live-health` → `seat-shell-paths` PASS (all 51
   resolve, zero dangling); ps pre/post reconciled (ambient ticks
   only); queue 263→263 with zero wave writes (ambient
   pickup-evidence ticks only). Launches: 2 (cap 4). Sends: 2
   (rc=0). Skips: 0. Deviations: 0.

## Validation

- `openspec validate 2026-10-30-seat-heal` → valid, rc=0.
- `./scripts/verify-rigs.sh --check-only` → 39 passed / 0 failed
  (NO new V-block) — see below.
- `make test` → SKIPPED with reason: zero code/test/script diffs in
  this wave (re-seed usage is an operation through existing tooling,
  not a code change); the `seat-shell-paths` class check landed and
  tested under the prior wave already guards the class.
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED —
  see below.
- `python3 scripts/generate-rigs.py --check-idempotent` →
  byte-identical, rc=0 — see below.

## Skips

- `make test` FULL skipped (reason above). Triad box in `tasks.md`
  left UNCHECKED for the coordinator. No commit made.

## Self-audit notes

- Seed path: full member-fragment re-seed chosen over
  `--refresh-policy-only` on structural grounds (`render-seat.py`
  `--policy-only` rewrites only the pps `config.json` and returns
  before `settings.json`, where `shellPath` lives) — recorded in
  `design.md` §1 with file/line evidence.
- Both probes PASS via the repair-wave echo-fallback branch (echo
  denied by seat policy, genuine whoami output + typed token) — same
  PASS criteria as seat-repair, no D1-equivalent deviation needed.
- Post-run `seat-shell-paths` PASS means the full #147 audit set is
  now resolved (22 stale + 2 lobotomized = 24/24); the issue itself
  stays open for the triad + principal say-so — nothing here closes
  it.
- Anything unfinished: triad + PR + merge are coordinator-owned;
  stated plainly, not claimed.
