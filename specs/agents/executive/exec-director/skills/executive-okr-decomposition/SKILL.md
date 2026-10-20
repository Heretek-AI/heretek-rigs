---
name: executive-okr-decomposition
description: Decomposes high-level strategic company objectives into departmental OKRs and delegates milestone tracking to Product and Architecture leads.
---

# Executive OKR Decomposition Procedure

1. Ingest the strategic directive from human stakeholders or executive tickets.
2. Query the enterprise memory graph (`read_graph`) to inspect existing commitments, active departmental roadmaps, and cross-team dependencies.
3. Formulate Objectives and Key Results (OKRs) following the strict format:
   - Objective: High-impact qualitative goal.
   - Key Results: 3 to 5 quantitative, verifiable metrics with target deadlines.
4. Verify resource feasibility against departmental budget allocations.
5. Create or update the executive roadmap in `docs/executive/OKRS.md`.
6. Emit structured delegation tickets to Paperclip targeting `product-director` (for delivery milestones) and `system-architect` (for technical feasibility and ADRs).
