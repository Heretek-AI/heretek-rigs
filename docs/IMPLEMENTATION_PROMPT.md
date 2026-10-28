# IMPLEMENTATION_PROMPT — heretek-rigs live operator brief

Canonical live prompt for implementation waves and `audit_loop.py` Phase 0
(`--run-implementation-first`). Reconciled 2026-10-28 from the overhaul plan
and the current gate set. It supersedes the archived pre-#122 spoonfeeder
upload (`archive/2026-10-28-overhaul/PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md`
— reference only, never execute the archived copy).

## 1. Stack (pinned)

| Layer | Pin |
|---|---|
| Orchestration | `@openrig/cli@0.7.4` (binary `rig`) |
| Agent runtime | `@earendil-works/pi-coding-agent@1.4.0` (binary `pi`) |
| Permission enforcement | `@gotgenes/pi-permission-system@41.0.0` (fail-closed, `*..*` terminal deny) |
| Model | `opencode-go/muse-spark-1.3-contributor:high` via `https://opencode.ai/inference/go/v1` |

Fleet shape: 51 specialist seats across 8 OpenRig v0.2 bundles, generated
deterministically from `fleet/fleet.yaml` + `fleet/mcp-servers.yaml`.

## 2. The one rule

Never hand-edit `specs/`, `rigs/`, `rosters/`, or `registry/`. Edit
`fleet/fleet.yaml`, `fleet/mcp-servers.yaml`, or `scripts/`, then regenerate:

```bash
python3 ./scripts/generate-rigs.py
HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py   # dev iterations only
./scripts/verify-rigs.sh --check-only     # expect: 35 checks passed, 0 failed
python3 ./scripts/audit_loop.py --self-test
```

Surgical text edits only on `fleet/fleet.yaml` (bulk dump strips comments).

## 3. Gates (all green before any commit or PR)

- `make verify` — full gate: 35 checks passed, 0 failed. V19 freezes the
  SUMMARY at 35; every later gate (V20+) is FAIL-ONLY appended alongside —
  never renumber or reword an existing check.
- `python3 ./scripts/generate-rigs.py --check-idempotent` — clean-tree regen
  is a no-op beyond provenance.
- `make test` — full unit suite, 0 failures.
- `make topology OUT=/tmp/topo` — wiring graph + referential gates, exit 0.
- `python3 scripts/audit_loop.py --self-test` — prompt presence + evaluator
  invariants + verify gate, PASSED.

### V22–V27 (appended gates, FAIL-ONLY, SUMMARY frozen)

- V22: bare queue/send deny in seat maps — all 51 seats deny the bare triple,
  allow the disciplined `--json` / `--json --verify` forms.
- V23: per-seat MCP bearer grants (107-identity M1) — `rig-mcp-http` shape
  (http transport, loopback endpoint, `seat_grant: true`, no static secrets)
  plus filename helper and the M1 corpus (15+ tests).
- V24: rotation runbook step-3 `--rig` mandate (107-identity R1) — mint with
  `--seat` AND `--rig`; runbook lives at `docs/evidence/107-identity-rotation.md`.
- V25: hardened rig relay in `seat-sandbox.sh` (overhaul-a M1) — relay markers
  present, `rig` exec'd from the word list, 7 enforcement tests.
- V26: hermetic regen + tar filter guard (overhaul-a M2).
- V27: docker pipeline bubblewrap + workflow keys (overhaul-a M3).

## 4. Wave triad discipline

One worktree, one branch (`feat/<id>` from clean `main`), one PR.
Milestone order: moves → prompt → regen + gates → red-proofs → drift-guard → PR.

- Agency-programmer implements (red → green → refactor per unit of behavior),
  never delegates, pushes, or merges.
- Coordinator owns regen commits and the final PR (Refs only, never Closes on
  a live issue).
- Agency-QA owns red-proofs (each sabotage must RED, restore must GREEN) and
  the drift-guard `VERDICT: PASS` from disk (never from memory).

Fail closed on validation, auth, transactions, and network errors. No stubs,
no swallowed errors, no skipped tests in delivered code.

## 5. Secrets (hard rules)

- Real keys live ONLY at `~/.config/heretek-rigs/secrets/` (0700 dir, 0600
  files). Never print, copy, or commit them.
- Seats reference secrets via `!cat` only; strict seeding refuses anything
  else. Degraded mode (`--allow-missing-secrets`) renders missing servers
  `"enabled": false` — unseeded seats have NO permission config, always seed
  before `up` / `expand` / `add`.
- Dummy keys for harness and matrix tests (`/tmp` scratch, 0600).

## 6. CLI and queue discipline

- Copy queue item IDs verbatim from `--json` output only; never retype them.
- Bare queue output mixes JSON with a human trailer and MUST NOT be parsed;
  always pass `--json` (`--json --verify` for create). Bare `rig queue list`,
  bare `rig queue create`, and bare `rig send` deny in-seat.
- Past session strays (`docs/evidence/`, `docs/reports/`, `.agents/`,
  `.claude/`, root `skills-lock.json`, `PROMPT_REVIEW.md`) are not yours to
  delete; stale content is archived under `archive/<date>-overhaul/`, never
  removed.

## 7. Live companions

- Audit protocol (live): root `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`.
- Remediation protocol (archived 2026-10-28, reference only):
  `archive/2026-10-28-overhaul/PROMPT_FLEET_AUDIT_REMEDIATION.md`.
- Audit trail (live): `AUDIT_REPORT_FINDINGS.md` (append, don't rewrite
  history). Prior remediation log (archived 2026-10-28, append-only):
  `archive/2026-10-28-overhaul/REMEDIATION_LOG.md`.
- Operator map: root `AGENTS.md`; entry point `README.md`; operator manual
  `docs/USER_GUIDE.md`; architecture reference `docs/TECHNICAL_DOCUMENTATION.md`
  (authoritative over older briefs).
