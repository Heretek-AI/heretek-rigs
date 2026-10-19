---
name: epic-roadmap-authoring
description: Translates executive strategic objectives into structured, phased Product Requirement Documents and GitHub epics.
---

# Epic Roadmap Authoring Procedure

1. Read executive targets from `docs/executive/OKRS.md`.
2. Retrieve current system capabilities and product context from the memory graph (`search_nodes`).
3. Author a structured PRD in `docs/product/prds/<epic-id>.md` covering:
   - Problem Statement & Target Personas.
   - Non-Goals (Scope bounds).
   - Core User Journeys.
   - Success Metrics & Release Gates.
4. Establish GitHub Milestones and project board epics via GitHub MCP.
5. Notify `tpm-scrum-lead` with the approved PRD path for sprint ticket decomposition.
