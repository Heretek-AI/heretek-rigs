# Design: remediate-45-live-health

## Why a new script, not check 23 in verify-rigs.sh
AGENTS.md:45 audit-baselines the 22 checks: new gates go alongside, existing
ones are not renumbered/reworded. A separate `scripts/live-health.*` keeps the
static provenance gate deterministic and offline-capable (it runs with no
daemon), while the live gate explicitly requires a running daemon. Failure
modes stay decoupled: a dead daemon breaks `make live-health`, never
`make verify`.

## Why warn-first, not fail-now
Three unknowns make immediate FAIL unsafe: (a) thresholds are uncalibrated —
no baseline distribution for pickup latency or stuck-row age exists yet;
(b) 49/51 roles have `heartbeat_sec: 0`, so the heartbeat sub-check cannot
PASS on day one through no fault of the fleet; (c) the 2026-10-22 incident is
a single sample. Warn-first buys calibration data without training operators
to ignore a red gate or, worse, to `ALLOW_DIRTY`-style bypass it. The
promotion policy (REQ-LH7) is the forcing function so warn-first does not rot
into report-only forever.

## Why poll `transitions`/`overdue`/`undelivered`, not daemon events
No event-subscription primitive was found on the `rig queue` surface
(`--help` enumeration); adding one means an upstream `@openrig/cli` change
(HANDOFF already routes #42/#44 upstream — same reasoning applies). Polling
existing read-only verbs needs zero upstream work and is sufficient for
minute-scale health signals. Cost: pickup-latency resolution is bounded by
poll cadence; documented as a known limitation, acceptable for a gate (not
an alerting pager).

## Threshold defaults (starting point, implementer calibrates)
- `T_pickup`: 15m (the W4 incident was ~50m; 15m catches it with margin
  while tolerating slow-seat starts).
- `T_stuck` (overdue age past deadline): 30m.
- `T_undelivered`: 15m (a failed nudge with no reconciliation is already
  anomalous at creation+minutes).
- `T_hb`: 3× the role's `heartbeat_sec` (adapts to per-role intervals once
  P0 lands; before P0, everything is UNCONFIGURED → WARN per REQ-LH3).
All tunable via flags/env; every run prints effective values (reproducibility
for QA red-proofs).

## Fail-closed / fail-loud modes
| Condition | Gate behavior |
|---|---|
| Daemon unreachable | All live sub-checks SKIP; summary names them; exit 0 with `sources: 0 ok` banner — MUST NOT print healthy |
| `heartbeat_sec: 0` roles present | UNCONFIGURED count named; heartbeat sub-check at most WARN |
| Threshold env/flag unparseable | Die with usage error (fail-closed on config, distinct from fleet state) |
| CLI output schema drift (unparseable JSON) | Affected sub-check SKIP + WARN naming the verb; never assume healthy |
| Any breach post-promotion | FAIL + nonzero exit + all breaching row IDs |

## Risks
- `rig queue` JSON output mixes a human trailer on default output (#44):
  the gate MUST use `--json` consistently (bare `--json` still mixes per
  #44 — implementer verifies the exact flag combo that yields parseable
  output and pins it; if none exists, this change depends on the #44 fix and
  tasks.md T1 proves it first).
- `rig ps --nodes` needs `--rig <name>` (or `-A`) outside a managed session
  (AGENTS.md live-notes): the gate MUST pass explicit scope flags, never rely
  on ambient session env.
- P0 (fleet.yaml heartbeat edit + regen) touches generated leaves via the
  sanctioned path only (edit `fleet/`, regen, `make verify` 22/0).
