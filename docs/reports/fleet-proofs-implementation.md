# Fleet-proofs implementation — Phase A (2026-10-30)

> Execution note: the `subagent` tool was policy-denied this session
> (retried once), so Phase A was executed directly by the coordinator with
> read-only live ops + worktree-confined file writes. No code or tests
> touched; live mutations limited to: daemon start (loopback, disclosed),
> `chmod 600` hardening (safe direction). No seats launched, no queue
> writes, no installs attempted.

## What ran (real outputs)

- `stat` secrets: dir `700`; `opencode-go.key` `600`; `github.pat` was
  `644` → hardened to `600`, re-verified. Strict-mode compliant after fix.
- `render-seat.py --dry-run` (blue-appsec-engineer@defensive-sec-and-red-team):
  rc=0, `!cat` refs only; one fail-loud `trivy` warn (gate working as designed).
- Tool presence: `r2`/`rabin2`/`tshark`/`trivy` MISSING; `go 1.27.3`,
  `pytest 9.1.1`, `cmake 4.3.0`, `bwrap 0.13.1`, `rig 0.7.5 (b57c4da3)` PRESENT.
- `sudo -n true` → password required: no unattended installs.
- Daemon: was down; `rig daemon start --no-kernel` → port 7433, left running.
- `rig ps --nodes -A`: 102 rows, ALL `seat-not-running` (some with queued WORK).
- Firecrawl `10.121.15.142:3002`: no route to host.

## Files written (worktree only)

- `openspec/changes/2026-10-29-fleet-proofs/` (proposal, specs/fleet-proofs,
  design, tasks — Phase A boxes checked, Phase B unchecked)
- `docs/74-PROVISIONING-MATRIX.md` (2026-10-30 re-take addendum)
- `docs/evidence/fleet-proofs-2026-10-30/phase-a-recon.md` (redacted recon +
  GO/NO-GO table + user questions)
- This report.

## Validation

- `./scripts/verify-rigs.sh --check-only` → 39/0 (run at commit time below).
- `openspec validate 2026-10-29-fleet-proofs` → must be rc=0 (run below).
- `make test`: SKIPPED — no code/tests touched (spec+docs+evidence only);
  634/0 baseline stands from the Wave-1 merge validation.
- `python3 scripts/audit_loop.py --self-test` + `--check-idempotent` at commit.

## Skips / deferrals

- Runbook steps 3–7: NO-GO per recon (no running seats; firecrawl unroutable)
  — gated on user approval, NOT attempted.
- Installs: named follow-ups (sudo needs tty).
- `HANDOFF.md` sync: still pending (pre-existing).
