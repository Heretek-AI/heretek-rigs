# Phase-A recon — fresh-slices (2026-10-29, read-only, NO live execution)

All outputs redacted: perms and `!cat` references only, zero secret values,
zero secret-shaped strings. Daemon was UP on arrival; no start was needed
(and none performed). No seat launched, no queue written, no installs.

## Safe-check (REQ-F0) — GO

- `stat -c '%a %U %n'`:
  - `~/.config/heretek-rigs/secrets/` → `700 john`
  - `github.pat` → `600 john`
  - `opencode-go.key` → `600 john`
- `HERETEK_SECRETS=~/.config/heretek-rigs/secrets python3
  scripts/render-seat.py --role appsec-engineer --rig
  defensive-sec-and-red-team --pod blue --dry-run` → rc=0, `!cat` refs
  only, `grep -ciE 'sk-|ghp_|Bearer [A-Za-z0-9]'` → 0 matches.

## Tool versions — GO

- `rig --version` → `0.7.5 (b57c4da3)`
- `go version` → `go1.27.3-X:nodwarf5 linux/amd64`
- `python3 --version` → `Python 3.15.2`
- `pytest --version` → `pytest 9.1.1`
- `cmake --version` → `cmake version 4.3.0`

## Daemon + fleet baseline — GO (with caution)

- `rig ps --nodes -A` → rc=0, 111 output lines: 51 `heretek-omni-fleet`
  seats all `run`/`idle`, 4 `kernel` rows.
- WORK present on live rows (build-ts-node-fullstack 7, data-pipeline 2,
  design rows 2–3, delivery-tpm 2, systems rows 2–3, several `yes`) with
  recent model records (2026-10-30T01:16Z): other sessions are ACTIVE.
- Contrast with fleet-proofs Phase A (`seat-not-running` everywhere): the
  fleet is now live. Stage B MUST re-snapshot at kickoff and treat any
  unexpected state vs this baseline as NO-GO until the TPM clears it.

## GO/NO-GO per Stage-B step

| Stage-B step | Verdict | Reason |
|---|---|---|
| Pre-exercise `rig ps` snapshot | GO (re-take at kickoff) | Baseline filed here; other sessions active, so kickoff MUST re-verify |
| Fan-out 3 synthetic rows, ≤6 launches | GO (pending TPM designation) | Daemon healthy; real slice TBD at kickoff |
| Per-slice proofs + integration join | GO (runbook-ready) | Design § answers #16 1–5; failure-isolation rule set |
| #17 metrics capture | GO | Report-only inputs verified at `reconcile_model.py:665-668`, `:808-810`, `:902` |
| #18 costed (a)/(b) + (c) decision | GO (report-only) | Zero provisioning side effects required; none performed |
| Post-exercise snapshot + zero residue | GO (procedure defined) | Cleanup obligation in REQ-F1 scenario |
| V32 gate | DEFERRED | Append ONLY if Stage B proves a live behavior gap |

Stop-on-RED: no RED encountered in Phase A (read-only). First RED in
Stage B aborts the exercise per design.md.
