---
name: madr-architecture-decision
description: Authors standardized, rigorous Architectural Decision Records (ADRs) analyzing trade-offs, options, and consequences.
---

# MADR Architecture Decision Procedure

1. Inspect existing architecture graph using `get_architecture` and `query_graph` from codebase memory.
2. Identify the technical problem, constraints, and business drivers.
3. Evaluate a minimum of three viable alternatives, documenting:
   - Positive consequences.
   - Negative consequences / trade-offs.
   - Security, latency, and cost impacts.
4. Author the ADR in `docs/adr/<next_number>-<slug>.md` following MADR 3.0 standard.
5. Generate a Mermaid diagram visualizing the proposed component topology.
6. Commit the ADR and notify `tpm-scrum-lead` for implementation scheduling.
