---
title: "DB Architecture and Schema - Migration and Scaling"
area: shared
tags:
  - shared
  - db
  - migration
  - constraints
  - scaling-limits
  - ai-reference
related:
  - shared_00_document-guide.md
  - db_01_architecture_and_schema-overview-and-config.md
  - db_02_architecture_and_schema-schema-reference.md
  - db_04_api_and_operations-module-boundaries-and-helper.md
  - db_07_api_and_operations-recovery-and-reference.md
---

# DB Architecture and Schema

- Overview → [shared_00_document-guide.md](../40_shared/shared_00_document-guide.md)
- DB API → [db_04_api_and_operations-module-boundaries-and-helper.md](db_04_api_and_operations-module-boundaries-and-helper.md)

## 8. Schema Generation and Migration Policy

`create_schema()` (`db/create_schema.py`) initializes all four schemas (rag, session, workflow, eventbus).

- For create-only DDL (used by `create_schema()` bootstrap): all statements use `IF NOT EXISTS` — idempotent and safe to run multiple times.
- **`rag.sqlite` and `session.sqlite` do not support backward-compatible migrations.** Changes to these schemas require database recreation: Archive → Delete → Recreate via `create_schema()`. Refer to [db_07 section 11](db_07_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure) for the full procedure. `workflow.sqlite` (section 8a), `eventbus.sqlite` (section 8b), and `mdq.sqlite` (section 8d) are each create-only — see respective sections for details.
- `create_schema()` is a wrapper that calls the four per-database initializers in order, and the responsibilities differ per database: `create_rag_schema()` and `create_session_schema()` run create-only DDL (idempotent, no migration); `create_workflow_schema()` runs the DDL, then records the schema version (section 8a); `create_eventbus_schema()` runs the create-only DDL read from `scripts/eventbus/schema.sql` (section 8b). Against an existing file the rag, session, and workflow initializers change nothing (the workflow initializer refuses a different recorded version), while the eventbus initializer leaves it unchanged.
- The embedding dimension is a fixed code-level constant (`get_embedding_dims()`), not a config key.

### Recreating `session.sqlite`: Session and Memory Recovery

Recreating `session.sqlite` physically removes both sessions and memories, but they are recovered by different paths:

1. Export any conversation worth keeping with `/session export` before recreating.
2. Recreate `session.sqlite` (Archive → Delete → Recreate).
3. Recover memory only, from the JSONL archive, with `/memory rebuild`.
4. Past session history is not restored into the database; `/memory rebuild` does not recover sessions and `/session export` output is for human reference only.

### 8a. Create-Only Bootstrap for `workflow.sqlite`

`workflow.sqlite` is created from the base DDL in `db/schema_sql.py` and has no migration mechanism; a database older than the supported baseline is recreated (section 8e).

- `create_workflow_schema()` creates the base tables with `IF NOT EXISTS` statements and then records the schema version.
- `workflow_schema_version` is an append-only log. An empty log records the current `WORKFLOW_SCHEMA_VERSION`; a log whose latest version is the current one is left unchanged; any other latest version makes `create_workflow_schema()` raise instead of recording the current version, so an older database is never marked as current.
- The agent startup check rejects a database whose latest recorded version differs from `WORKFLOW_SCHEMA_VERSION`; recovery is recreating the database ([db_07 section 11](db_07_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure)).

### 8b. Create-Only Schema for `eventbus.sqlite`

`create_eventbus_schema()` (`db/create_schema.py`) and the EventBus service (`open_db()`) both create the schema from the single DDL definition in `scripts/eventbus/schema.sql`, read through `build_eventbus_schema_sql()`. `schema.sql` ends with `PRAGMA user_version = N;`, the schema version. There is no incremental migration: `open_db()` refuses a database stamped with a different version, stamps an unstamped existing database only when its tables match `schema.sql` column for column, and refuses any other; `create_eventbus_schema()` refuses a database stamped with a different version. Recovery is recreating the database. Table roles: `eventbus_06_persistence_schema_and_replay.md`.

`events.published_at` has a `DEFAULT` expression in `schema.sql`. SQLite cannot change a column default without rebuilding the table, so existing databases created before the default was added are not rebuilt; the difference has no effect because every insert path (`POST /publish` and the DLQ requeue) supplies `published_at` explicitly.

### 8c. RAG Consistency Verification

`db/rag_consistency.py::check_rag_consistency()` is a read-only verification function that compares row counts of `chunks`, `chunks_fts`, and `chunks_vec`, returning a `RagConsistencyReport` (`db/models.py`). See code for details on consistency conditions and error message generation logic.

### 8d. Create-Only Tables for `mdq.sqlite`

`scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` creates the `mdq.sqlite` tables, triggers, and index state with `IF NOT EXISTS` statements every time the MDQ service starts; nothing is dropped or rewritten. `mdq.sqlite` is a derived store: a store older than the supported baseline is recovered by deleting the file and re-indexing the Markdown files (section 8e).

The `chunks_vec` (`rag.sqlite`) and `memories_vec` (`session.sqlite`) tables defined in `db/schema_sql.py` are unrelated to the MDQ schema and are unaffected.

### 8e. Supported Upgrade Baseline

The minimum supported source schema of each database is the schema of the current release. A database older than that is recreated, not migrated, so no supported database depends on the migration mechanisms of sections 8a, 8b, and 8d. Every one of those migrations is classified removable; each database's migration code is removed by its own change.

| Database | Minimum supported source schema | Why the migration code is kept | Removal condition | Owner |
|---|---|---|---|---|
| `workflow.sqlite` | The current release schema: the recorded workflow schema version equals the current `WORKFLOW_SCHEMA_VERSION` | N/A — create-only DDL; no migration code exists | N/A — no migration code to remove | The workflow engine |
| `eventbus.sqlite` | The current release schema defined by `scripts/eventbus/schema.sql` | N/A — create-only DDL; no migration code exists | N/A — no migration code to remove | The EventBus service |
| `mdq.sqlite` | The current `chunks` shape, keyed by `chunk_id` | Same; a rebuilt store is recovered by re-indexing the Markdown files | Same | The `mdq-mcp` server |

Recreation impact when a database is older than the baseline (procedure: [db_07 section 11](db_07_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure)):

| Database | Data loss possible | Backup before recreation | Rollback |
|---|---|---|---|
| `workflow.sqlite` | Yes — the recreated database is empty | Required: `rotate_all_dbs()` archives it (db_07 section 11, step 1) | Restore the archived file |
| `eventbus.sqlite` | Yes — events and delivery state are not carried over | Required: `rotate_all_dbs()` archives it (`rotate_eventbus_db()`) | Restore the archived file manually; no automated restoration path exists (db_07 section 9) |
| `mdq.sqlite` | No lasting loss — derived store, rebuilt from the Markdown files | Not required | Delete the file and re-index (section 8d) |

How to read a database's current schema without changing it: [DB API and Operations](db_07_api_and_operations-recovery-and-reference.md#11a-identifying-a-databases-current-schema) (section 11a).

---

## 9. Schema Evolution

Schema evolution rules per database are defined in sections 8 through 8d; the minimum supported source schema of each database is in section 8e. `eventbus.sqlite` is created from its DDL and recreated when older than the current release schema.

---

## 10. Source of Truth

DDL source: `db/schema_sql.py`; schema initialization entry point: `db/create_schema.py::create_schema()`; deploy initialization entry point: `deploy/init_db.sh`; DB connection helper: `db/helper.py::SQLiteHelper`; DB files: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`; Event Bus schema (DDL only): `scripts/eventbus/schema.sql`; mdq.sqlite schema creation source: `scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` (see section 8d).

## 11. Storage Growth

The `consumer_delivery` table grows proportionally to the product of (number of consumers × number of events). For a single consumer, this is bounded by the total number of events. For multiple consumers, the growth is linear with respect to the number of consumers.

**Mitigation strategies:**
- Periodic cleanup of old delivery-state rows (e.g., events older than N days).
- Partitioning by consumer_id or event_id if the dataset becomes very large.
- Using a separate database per consumer if the workload requires strict isolation.

The `consumer_offsets` table has constant-size growth (one row per consumer), regardless of the number of events.

## 12. Scaling Limits and Migration Indicators

The current RAG architecture uses single-node SQLite. This is suitable for team-scale deployments where corpus size is moderate and concurrent writes are infrequent.
The following indicators suggest a need for re-evaluation.

### Corpus Size

- **When the `chunks` table grows large:** KNN scan time in `chunks_vec` increases linearly with corpus size. Monitor RAG query latency as the corpus grows. *(Note: Actual thresholds depend on hardware and embedding dimensions.)*
- **When the DB file grows large:** Latency for `VACUUM`, backups, and WAL checkpoints will increase, and `/session vacuum` will take longer.

### Write Concurrency

- When multiple `RagIngester` processes write to the same `rag.sqlite`, they are serialized at the WAL layer. If ingestion throughput becomes a bottleneck, SQLite write serialization may become a constraint.
- **Indicator:** WAL files grow faster than checkpointing can shrink them. Monitor via `/session health`.

### FTS5 Search Latency

- **Indicator:** RAG query latency is consistently higher than the deployment's accepted latency. Since FTS5 BM25 scales with document count, search speed may decrease with very large corpora.

### Operational Complexity Indicators

- Backups and point-in-time recovery become more complex as file sizes increase.
- Sharing the same DB file across multiple environments is not supported (SQLite is a single-file system).
- Resolving issues with `/session rag-consistency` becomes harder as scale increases.

### Migration Indicator Checklist

Consider architectural review if two or more apply:

- [ ] p95 KNN search latency exceeds the deployment's accepted latency
- [ ] DB file size makes backup, `VACUUM`, or recovery windows unacceptable
- [ ] WAL checkpoints consistently take longer than the deployment's accepted duration
- [ ] Ingestion queue depth keeps growing faster than it drains
- [ ] Multiple teams or processes require simultaneous write access

Monitor these indicators during normal operation using `/session health` and `/session rag-consistency`.

### Considerations when limits are approached

- **Vector Search:** Dedicated vector databases (Approximate Nearest Neighbor search, distributed indexing) outperform `sqlite-vec` at very large vector counts.
- **Full-Text Search:** Full-text search services offer lower latency for large corpora.
- **Hybrid Store:** Relational DB + Vector extensions (e.g., `pgvector` compatible) allow scaling write concurrency while maintaining SQL semantics.

> **Note:** The indicators above are qualitative and not backed by benchmarking. Actual limits depend on hardware, embedding dimensions, query patterns, and corpus characteristics. Always verify in individual deployment environments before treating any threshold as definitive.

## 13. Schema Change Checklist

Before performing a schema change task, answer all of the following:

- [ ] Which DB is affected? (rag/session/workflow/eventbus/mdq)
- [ ] Which schema source files are affected?
- [ ] Is this a DDL change exclusive to new installations?
- [ ] Is a migration required for existing databases?
- [ ] If no migration is provided, is database recreation required?
- [ ] Is there a possibility of data loss?
- [ ] Are tests updated to reflect the schema behavior?
- [ ] Which component is affected: RAG, session, workflow, eventbus, or MDQ?

## Keywords

- shared
- db
- migration
- constraints
- scaling-limits
- ai-reference
