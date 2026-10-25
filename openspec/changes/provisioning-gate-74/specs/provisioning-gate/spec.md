# Delta spec: provisioning existence gate

## ADDED Requirements

### REQ-P1: render-time resolution
`scripts/render-seat.py` MUST resolve each bound MCP `command` and each `bash_allow` leading binary at render time (beside the `secret_ok` / `entry["enabled"]=False` path at `:549`). Unresolvable entries MUST render `enabled:false` (or the seat's equivalent degraded marker) AND emit a stderr warning naming the server, seat, and missing artifact. Silent degradation is forbidden. Rationale: #74 checkbox 2 blesses the degraded-secrets handling as the pattern.

### REQ-P2: seed/stage-time resolution
`scripts/seed-rig.py` MUST perform the same resolution in its per-seat staging loop (fail or degrade-loudly, same warn shape as REQ-P1). Rationale: the literal "stage-time existence gate" from #89.

### REQ-P3: verify block + live-health sub-check
A new appended verify block (never renumber existing checks) MUST assert the REQ-P1/P2 gate strings exist and MUST red-proof both directions (missing → named FAIL/NOTE; present → green). `scripts/live-health.py` MUST gain a WARN-first "0 missing tools" sub-check consistent with its warn-first policy. Rationale: #89's two halves (render-time + live-health).

### REQ-P4: matrix coverage
The gate MUST cover all 20 command-bearing catalog servers (`fleet/mcp-servers.yaml:19-281`) plus bash-grant binaries `r2`, `rabin2`, `tshark` (`fleet/fleet.yaml:1031-1034`). `github` (remote-http, no command) is the documented exclusion accounting 20-vs-21. Rationale: the PR #104 lesson — no single-slice gates.

## MODIFIED Requirements

### REQ-G1: no renumber, no provisioning claims
No existing check renumbered/reworded. No `install:` recipes added, no host tooling installed, no catalog pins changed in this change. The PR body MUST say `Refs #74`, never `Closes #74`.
