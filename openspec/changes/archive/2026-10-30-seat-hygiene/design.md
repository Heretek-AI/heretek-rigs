# Design: 2026-10-30-seat-hygiene

## Where live configs live (read-only)

Live per-seat daemon state sits under `~/.openrig/state/pi/<seat>/`:

- `agent/settings.json` — pi config: `shellPath` (the seat's shell; the
  M4 bubblewrap wrapper), `packages[]` (permission-system install path).
- `agent/mcp.json` — MCP servers: absolute `command` paths plus
  `enabled` / `exposure` flags (a missing binary under a disabled or
  deferred server is never loaded — benign, recorded separately).
- `agent/sandbox.env` — `HERETEK_SANDBOX_WRITE` (relative bind roots),
  `HERETEK_SECRET_STORE` (absolute secrets dir; `!cat` references only,
  never read).
- `<seat>/runner-state.json` — `sessionFile` (absolute path into the
  seat's own `sessions/` dir).
- `rig seat status <seat> --json` (read-only) — `launch_cwd` ("Working
  directory for future launches"), session/occupant/startup state,
  `handover_at`. `rig ps --nodes --json -A` carries NO path fields
  (verified: keys are status/activity/identity only), so it serves as the
  fleet-membership oracle, not a path source.

All reads are plain filesystem reads plus `rig ps` / `rig seat status`
(both documented read-only; `--help` checked before use). No command in
this wave takes a launch, write, send, or edit path.

## Field inventory (what counts as path-like)

| # | Field | Source | Worktree-coupled? |
|---|---|---|---|
| 1 | `shellPath` | `settings.json` | YES — seeded absolute; bakes the seeding worktree (`render-seat.py:1090` resolves the wrapper absolute to the seeding cwd) |
| 2 | `packages[]` | `settings.json` | NO — host tool installs under `~/.local/share` |
| 3 | MCP `command` | `mcp.json` | NO — host tool installs; gate on `enabled`/`exposure` |
| 4 | `launch_cwd` | `seat status --json` | YES in principle — checked per seat |
| 5 | `sessionFile` | `runner-state.json` | Self-referential (own `sessions/` dir); checked |
| 6 | `sandbox.env` paths | `sandbox.env` | `HERETEK_SECRET_STORE` host-absolute; write roots relative |

## What counts as dangling

A path-like field value is DANGLING iff it is absolute, worktree-coupled
(or otherwise expected on disk), and its target does not exist — in this
wave, specifically any value under `.lane/trees/<name>/...` where that
worktree no longer exists on disk. The fleet-proofs worktree (seed source)
is pruned; `.lane/trees/` now holds only the audit worktree. A missing
binary under a disabled/deferred MCP server is NOT dangling (never
loaded); it is recorded as a benign provisioning note.

## Impact classes

- `lobotomized`: seat fresh-launched into a dangling `shellPath` AFTER the
  prune — pi starts with no working shell (missing `shellPath` fails
  closed, no `/bin/bash` fallback). Proven only by launch-window evidence
  (launch timestamp post-prune + occupant never responding). This wave
  knows exactly 2: the race's original racers A/B.
- `stale`: seat carries a dangling path but its current occupant predates
  the prune and still reports `running/active/ready`. Harmless TODAY;
  the NEXT fresh launch on that seat lands lobotomized. All 22 others.
- Daemon-side `running/active/ready` does NOT validate `shellPath` — the
  breakage materializes only at next fresh launch. That is why a
  prune-time check (repair/prevention wave) matters.

## Repair-wave input contract

`docs/evidence/seat-hygiene-<date>/dangling-seats.json` is the repair
wave's ONLY required input. Schema per entry: `seat`, `field`,
`stale_value`, `target_exists` (bool), `launch_cwd`, `session_status`,
`occupant_lifecycle`, `startup_status`, `handover_at` (nullable),
`impact` (`lobotomized` | `stale`), `provenance` (evidence run that
proved the label). Top-level: `generated` (date), `issue` (147),
`stale_shell_target`, `expected_shell` (the in-repo wrapper the 27 clean
seats already point at). Repair scoping (re-resolve vs relaunch, launch
budget, approval shape) belongs to the repair wave, not here.
