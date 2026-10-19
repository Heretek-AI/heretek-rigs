---
name: feedback-clustering-analysis
description: Analyzes telemetry datasets and feedback issues to extract sentiment, frequency, and core user friction points.
---

# Feedback Clustering Analysis Procedure

1. Load telemetry or feedback datasets into DuckDB via `mcp-server-duckdb`.
2. Execute aggregate queries grouping friction events by user action and error code.
3. Categorize feedback items into:
   - Bugs / Broken Expectations.
   - Usability & Affordance Friction.
   - Feature Requests.
4. Calculate user impact score (Frequency x Severity).
5. Generate an executive research summary in `docs/research/`.
6. Submit top 3 recommended product interventions to `product-director`.
