---
name: duckdb-dbt-pipeline-execution
description: Executes and tests dbt transformation models against local or remote DuckDB parquet lakes with strict schema assertions.
---

# DuckDB dbt Pipeline Execution Procedure

1. Read incoming data schema and transformation requirements.
2. Author modular dbt SQL models in `dbt/models/`:
   - Enforce dimensional modeling (Staging, Intermediate, Marts).
   - Add column descriptions and documentation.
3. Configure data quality tests in `schema.yml`:
   - `unique`, `not_null`, `accepted_values`, `relationships`.
4. Execute dbt models via CLI: `dbt run --profiles-dir dbt/`.
5. Run automated data tests: `dbt test --profiles-dir dbt/`.
6. Inspect output Parquet metadata via DuckDB MCP to assert compression and partition pruning efficiency.
7. Commit models and test definitions.
