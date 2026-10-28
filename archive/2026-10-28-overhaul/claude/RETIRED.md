# SUPERSEDED — `claude/` planning spike snapshots

All files in this directory are pre-implementation planning snapshots.
They are retained for audit provenance only and are **superseded by**:

- canonical `docs/OSINT_ECOSYSTEM_REPORT.md` (fleet decisions, Reject rows),
- canonical `docs/OPENRIG_MUSE_GO_ARCHITECTURE.md` (ground-truth invariants),
- canonical `fleet/fleet.yaml` + `fleet/mcp-servers.yaml` (shipped pins).

`claude/` snapshots correctly Reject `pi-subagents` (no second delegation path),
consistent with the shipped fleet (HR-6.2-stale-legacy-pins). Do not treat any
`claude/` table as authoritative; follow `docs/OSINT_ECOSYSTEM_REPORT.md`.
