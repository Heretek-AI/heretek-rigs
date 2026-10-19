---
name: blameless-incident-triage-and-postmortem
description: Triages active production incidents using metric queries, identifies blast radius, and drafts a structured blameless post-mortem.
---

# Blameless Incident Triage and Postmortem Procedure

1. Ingest alert details (Alert name, affected service, timestamp).
2. Execute instant PromQL queries via Prometheus MCP to determine current error rates, latency p99, and impacted endpoints.
3. Identify blast radius: percentage of traffic affected and customer impact.
4. Execute non-destructive diagnostics (health checks, status endpoints).
5. Document timeline of events with exact UTC timestamps.
6. Author blameless post-mortem in `docs/incidents/` covering:
   - Executive Summary.
   - Root Cause Analysis (5 Whys).
   - What Went Well / What Went Wrong / Where We Got Lucky.
   - Corrective Action Items with assigned owners and Paperclip ticket IDs.
