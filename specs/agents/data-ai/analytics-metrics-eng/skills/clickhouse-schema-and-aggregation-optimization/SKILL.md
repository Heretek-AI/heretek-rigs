---
name: clickhouse-schema-and-aggregation-optimization
description: Optimizes ClickHouse table sorting keys and creates Materialized Views using AggregatingMergeTree for sub-second queries.
---

# ClickHouse Schema and Aggregation Optimization Procedure

1. Read analytical metric query patterns.
2. Design ClickHouse table using `ReplacingMergeTree` or `AggregatingMergeTree`:
   - Set primary sorting key (`ORDER BY`) aligned with highest-filter cardinality columns.
   - Configure TTL for automated data aging and cold storage tiering.
3. Author Materialized Views to pre-aggregate high-frequency counts, sums, and unique user states (`State()` and `Merge()` functions).
4. Test query execution plan: `EXPLAIN SYNTAX` and `EXPLAIN PLAN`.
5. Verify queries scan < 1% of total dataset rows for 95% of standard dashboard views.
6. Commit DDL migrations to `migrations/clickhouse/`.
