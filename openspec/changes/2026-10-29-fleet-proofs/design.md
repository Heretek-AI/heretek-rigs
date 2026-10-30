# Design: 2026-10-29-fleet-proofs

## Topology (observed 2026-10-30, Phase A recon)

- Host: dev machine, `rig 0.7.5 (b57c4da3)`, go 1.27.3, pytest 9.1.1,
  cmake 4.3.0, bwrap 0.13.1. Daemon was DOWN on arrival; started loopback
  (`rig daemon start --no-kernel`, port 7433) for recon. Left running.
- Daemon records 102 node rows (`heretek-omni-fleet` + `kernel`), but EVERY
  seat reports `seat-not-running` (activity UNKNOWN). Some rows carry queued
  WORK (e.g. ts-node-fullstack 7, data-pipeline 2, ux/design 2–3). No agent
  processes to interact with.
- Firecrawl `10.121.15.142:3002`: NO ROUTE from this host (closed).
- `sudo -n`: password required → no unattended apt installs.

## Decisions

- **No seat launches in Phase A.** Launching (1 or 51) seats spends tokens
  and mutates fleet state; it needs explicit user approval (Phase B gate).
- **Provisioning = document, don't force.** `r2`/`rabin2`/`tshark`/`trivy`
  missing; installs need sudo (password) or third-party repos → named
  follow-ups in the matrix, not half-done installs.
- **Firecrawl boot is NO-GO** from this host (no route). #107 MCP proof
  reduces to governance-box tick-off from repo state + the pre-existing
  queue-half note (still → Wave 4).
- **Steps needing running seats are NO-GO until a seat runs** (#96 refresh,
  in-seat builds via seats, live loops). The runbook MUST NOT fake these
  with host-shell equivalents and call them "in-seat".

## Fail-closed modes

- Secret perm != 600/700 → stop, harden, re-verify (as happened: github.pat
  644 → chmod 600, re-statted).
- Any evidence containing a secret-shaped string → redact and re-take.
- Daemon interaction limited to `ps` (read-only) in Phase A.
