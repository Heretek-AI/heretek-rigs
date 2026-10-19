---
name: sprint-ticket-decomposition
description: Breaks down high-level product epics into atomic engineering issues with unambiguous acceptance criteria and role assignments.
---

# Sprint Ticket Decomposition Procedure

1. Read the target PRD from `docs/product/prds/`.
2. Identify all technical layers required (Backend, Frontend, Database, QA).
3. Break down work into atomic units of effort (< 1 day execution for an autonomous agent).
4. Write each issue following the standard schema:
   - Context & User Story.
   - Technical Implementation Guide.
   - Acceptance Criteria (Given / When / Then).
   - Target Role ID (e.g., `rust-systems-spec`, `e2e-browser-qa`).
5. Publish issues via GitHub MCP and wire dependency linkages.
