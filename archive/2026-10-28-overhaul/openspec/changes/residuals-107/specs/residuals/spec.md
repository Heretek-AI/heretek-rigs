# Delta spec: residuals-107

## ADDED Requirements

### REQ-R1: V13 rate-limit skip
`scripts/verify-rigs.sh:1781` skip pattern MUST also match `toomanyrequests` and `rate limit` (case-insensitive handling as the block already does). Rationale: quota-burned registry is transport-adjacent fail-closed noise, RED twice. All other V13 behavior MUST stay identical.

### REQ-R2: live-doc counts
`AGENTS.md`, `docs/USER_GUIDE.md`, `README.md` MUST state the post-V15 verified count (31 checks passed) wherever they state a check count. Rationale: single-source drift fix per HANDOFF (the #102 canonical guard belongs to Wave D).

### REQ-R3: firecrawl pin doc
`docs/TECHNICAL_DOCUMENTATION.md:408` MUST reference `ghcr.io/firecrawl/firecrawl:2.10.19` (matching `docker-compose.sidecars.yml:93` + `docs/NOTES.md:305`), not `ghcr.io/mendable/firecrawl:1.6.0`. Rationale: org `mendable` denied live; stale doc misdirects boot attempts.

## MODIFIED Requirements

### REQ-G1: no renumber, no policy loosening
V13 edit MUST NOT renumber/reword any check; governance probes (`check-envelope.py:544-557`, `reconcile_model.py:39-67`, `send-authenticated.sh:16-21`) MUST remain byte-identical in this change. Deferred items stay fail-closed.

### REQ-G2: no history rewrites
Existing `docs/reports/*` (including `YZ9W` footer occurrence) MUST remain byte-identical. Session-URL canonical (`nx9` for future footers) is recorded in B2 evidence only.
