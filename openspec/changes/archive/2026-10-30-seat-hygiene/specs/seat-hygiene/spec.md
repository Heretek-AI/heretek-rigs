# Seat-hygiene

## Purpose

Fleet-wide audit for #147: every live seat's path-like config fields are
checked against the filesystem, each dangling reference is recorded with
seat + field + stale target + impact, the dangling set is published as
machine-readable JSON for the repair wave, and the audit itself is proven
to mutate nothing. Refs #147 — never Closes.

## ADDED Requirements

### Requirement: REQ-H1 — audit completeness: every seat, every path-like field, every finding recorded

The audit MUST enumerate every seat dir under the live daemon state root,
and for each seat check EVERY path-like field against disk: `shellPath`
and `packages[]` (pi `settings.json`), absolute MCP `command` paths
(`mcp.json`), `launch_cwd` (`rig seat status --json`), `sessionFile`
(`runner-state.json`), and absolute paths in `sandbox.env`. Each dangling
reference MUST be recorded with seat + field + stale target + impact
(lobotomized vs stale). Seats with no agent state on this host MUST be
listed as unscannable-with-reason, not silently skipped.

#### Scenario: full coverage with per-seat findings

- When the audit closes, the runbook shows one row per live seat with the
  observed value and existence verdict of every path-like field, plus a
  separate list of seat dirs carrying no agent state; the dangling count
  reconciles exactly with the machine-readable list (no dangling seat
  missing, no listed seat clean).

#### Scenario: impact classified per seat

- When the audit closes, every dangling seat carries exactly one impact
  label with provenance: `lobotomized` (fresh-launched into the dangling
  path with broken bash, proven by launch-window evidence) or `stale`
  (carries the dangling path while its current occupant predates the
  prune; next fresh launch will lobotomize it).

### Requirement: REQ-H2 — machine-readable output: JSON list as the repair wave's input

The audit MUST publish `dangling-seats.json` alongside the human report:
one entry per dangling seat with seat, field, stale value, target-exists
flag, `launch_cwd`, session/occupant/startup state, `handover_at`, and the
REQ-H1 impact label. The repair wave MUST be able to consume this file
without re-running the scan.

#### Scenario: repair input is complete and self-describing

- When a repair-wave author reads `dangling-seats.json`, every entry
  contains the seat identity, the exact stale value, and the impact label
  needed to decide re-resolve vs relaunch — with zero additional live
  inspection required to scope the repair set.

### Requirement: REQ-H3 — zero mutation: pre/post fleet snapshots identical

The audit MUST perform zero launches, zero queue writes, zero sends, and
zero config edits. `rig ps --nodes -A` snapshots taken before and after
the scan MUST be byte-identical, filed as `ps-pre.txt` / `ps-post.txt`.

#### Scenario: snapshot proof of non-interference

- When the audit closes, `cmp ps-pre.txt ps-post.txt` succeeds
  (byte-identical) and the runbook records rc=0 for every inspection
  command — or records any deviating field as unobservable-with-reason
  with the read-only equivalent used instead.
