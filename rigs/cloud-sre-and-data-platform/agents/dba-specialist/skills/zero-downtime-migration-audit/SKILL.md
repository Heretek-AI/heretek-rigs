---
name: zero-downtime-migration-audit
description: Audits SQL migration files to guarantee zero exclusive table locks, backward compatibility, and concurrent index creation.
---

# Zero-Downtime Migration Audit Procedure

1. Read target migration SQL files in `migrations/`.
2. Check for dangerous DDL operations:
   - Reject `ALTER TABLE ... ADD COLUMN ... DEFAULT <non-null>` without check constraints.
   - Reject `CREATE INDEX` that omits `CONCURRENTLY`.
   - Reject unbatched large table updates (`UPDATE table SET ...`).
3. Connect to staging database via PostgreSQL MCP and execute `EXPLAIN (ANALYZE, BUFFERS)` on affected queries.
4. Verify foreign key constraints are backed by supporting indexes to prevent full-table scan locks on deletes.
5. Author zero-downtime migration revision.
6. Verify migration applies cleanly and rolls back cleanly in staging.
