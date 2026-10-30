# fleet-proofs Specification

## Purpose
Live-host proof batch for repo-side remediations. Each requirement is a
runbook step with binary evidence (rc=0 artifact or named follow-up).

## Requirements

### Requirement: REQ-P1 — secrets safe-check

The runbook MUST start by proving secret hygiene WITHOUT reading values:
`stat` on `~/.config/heretek-rigs/secrets/github.pat` and `opencode-go.key`
MUST show `600` owner-only (dir `700`), and one `render-seat.py --dry-run`
MUST render `!cat` references only (rc=0). Any violation MUST stop the run.

#### Scenario: safe-check green

- When the safe-check runs, both files stat `600`, the dir stats `700`,
  the dry-run exits 0, and no secret value appears in any output or file.

### Requirement: REQ-P2 — provisioning re-take

Step 2 MUST re-take the #74 host snapshot on the fleet host: presence of
`r2`, `rabin2`, `tshark` (B1–B3) plus `go`, `pytest`, `cmake`, `bwrap`,
`rig --version`. Missing tools MUST either be installed (unattended-safe
only, never interactive-auth installs) or recorded as named follow-ups in
`docs/74-PROVISIONING-MATRIX.md` with observed evidence.

#### Scenario: matrix reflects the host

- When Step 2 completes, the matrix addendum states per-tool
  PRESENT-with-version or MISSING-with-reason, dated 2026-10-30.

### Requirement: REQ-P3 — ordered live proofs with stop-on-RED

Steps 3–7 MUST run in plan order (#91/#12 in-seat builds → #96 refresh →
live loops #77/#81/#9/#15 → #107 MCP half) and MUST stop on the first RED.
Each step MUST leave an evidence file under `docs/evidence/fleet-proofs-<date>/`
(command, rc, redacted output) or a named follow-up. Steps requiring running
seats MUST NOT be attempted when recon shows `seat-not-running` everywhere;
that MUST be recorded as NO-GO, not forced.

#### Scenario: proofs or honest deferrals

- When the runbook finishes, every step is either evidenced rc=0 or
  NO-GO-with-reason, and no step was executed against a non-running seat.
