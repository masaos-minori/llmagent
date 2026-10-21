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
- **`rag.sqlite` and `session.sqlite` do not support backward-compatible migrations.** Changes to these schemas require database recreation: Archive → Delete → Recreate via `create_schema()`. Refer to [db_07 section 11](db_07_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure) for the full procedure. `workflow.sqlite` (section 8a), `eventbus.sqlite` (section 8b below), and `mdq.sqlite` (section 8d) each have their own incremental migration/auto-update mechanisms — see respective sections for details.
- `create_schema()` is a wrapper that calls the four per-database initializers in order, and the responsibilities differ per database: `create_rag_schema()` and `create_session_schema()` run create-only DDL (idempotent, no migration); `create_workflow_schema()` runs the DDL, then applies the incremental migrations and records the schema version (section 8a); `create_eventbus_schema()` runs the DDL read from `scripts/eventbus/schema.sql`, then applies the incremental migration list (section 8b). Against an existing file the rag and session initializers change nothing, while the workflow and eventbus initializers migrate it.
- The embedding dimension is a fixed code-level constant (`get_embedding_dims()`), not a config key.

### Recreating `session.sqlite`: Session and Memory Recovery

Recreating `session.sqlite` physically removes both sessions and memories, but they are recovered by different paths:

1. Export any conversation worth keeping with `/session export` before recreating.
2. Recreate `session.sqlite` (Archive → Delete → Recreate).
3. Recover memory only, from the JSONL archive, with `/memory rebuild`.
4. Past session history is not restored into the database; `/memory rebuild` does not recover sessions and `/session export` output is for human reference only.

### 8a. Incremental Migrations for `workflow.sqlite` Only

The principle that "rag/session do not support backward-compatible migrations" applies only to those two databases. `workflow.sqlite` is an exception, as `db/schema_sql.py` implements a dedicated incremental migration mechanism.

- `db/schema_sql.py` maintains an ordered list of (ID, SQL statement) pairs applied by `apply_workflow_migrations()`. A `"duplicate column name"` `sqlite3.OperationalError` is treated as already applied; other errors are re-raised.
- `create_workflow_schema()` creates base tables, then applies migrations, and finally records the schema version.
- Each list entry holds exactly one SQL statement: `conn.execute` rejects several statements in one entry, which would abort startup.
- Column-addition migrations are no-ops for new databases (the base schema already has the columns) and incremental additions for existing ones. Two entries remove the post-execution approval stage from existing databases, in this order: one marks tasks left waiting in that stage as failed, and one drops the `approvals` table. Both are idempotent and neither changes a new database.

Incremental migration mechanisms like this do not exist for `rag.sqlite` or `session.sqlite`.

### 8b. Incremental Migration for `eventbus.sqlite`

`scripts/eventbus/schema.py::_migrate()` performs incremental, additive schema evolution on `eventbus.sqlite` at every EventBus service startup, called from `_init_schema()` when the `events` table already exists. The base schema for `events`, `consumer_delivery` and `consumer_offsets` is defined in `scripts/eventbus/schema.sql`, the only DDL definition; `create_schema()` reads it through `build_eventbus_schema_sql()`. Table roles: `eventbus_06_persistence_schema_and_replay.md`.

`events.published_at` has a `DEFAULT` expression in `schema.sql`. SQLite cannot change a column default without rebuilding the table, so existing databases created before the default was added are not rebuilt; the difference has no effect because every insert path (`POST /publish` and the DLQ requeue) supplies `published_at` explicitly.

Migration rules (all idempotent; duplicate-column, duplicate-index and missing-column errors are caught and ignored):

- **Additive changes:** missing columns, indexes, and the `consumer_delivery` and `consumer_offsets` tables are added to existing databases.
- **Column removal:** a retired `retry_count` column, if present, is dropped.
- **Column conversion:** `consumer_delivery.acked_at` (a timestamp, `NULL` = not acked) predates the boolean `acked` column. `_migrate()` gates the conversion on `acked_at` being present, so a current database never rebuilds its index. The conversion drops the stale `idx_consumer_delivery_consumer_ack` index (SQLite refuses to drop a column an index still references), adds `acked INTEGER NOT NULL DEFAULT 0`, converts `acked_at IS NOT NULL` to `1`, drops `acked_at`, commits (the conversion is DML, so the DDL's implicit commit does not cover it), and recreates the index on `(consumer_id, acked)`.
- **Separate data seeding:** `migrate_legacy_offsets()` (see Schema Evolution below) is distinct from `_migrate()`'s schema-DDL role.
- **Two initialization paths:** `create_schema()` bootstrap (`apply_eventbus_migrations()` in `scripts/db/schema_sql.py` runs first, then the DDL read from `scripts/eventbus/schema.sql` via `build_eventbus_schema_sql()`) vs. `open_db()` live-service startup (defined in `scripts/eventbus/db_conn.py`, re-exported by `scripts/eventbus/db.py`), which applies its own incremental ALTER TABLE operations. Migrations must precede the bootstrap DDL because `idx_consumer_delivery_consumer_ack` in `schema.sql` references `consumer_delivery.acked`, and a database still carrying `acked_at` aborts that DDL. `apply_eventbus_migrations()` swallows `sqlite3.OperationalError` for duplicate-column, missing-column, and missing-table scenarios — the last because a fresh database has no table to migrate before the DDL creates it — and re-raises the rest. `_EVENTBUS_MIGRATIONS` carries the same conversion statements as `_migrate()`; the two cannot share code because the `eventbus-is-isolated` import contract forbids `eventbus` from importing `db`. A reader must distinguish them — each path migrates an existing database, but they are separate code paths.

### 8c. RAG Consistency Verification

`db/rag_consistency.py::check_rag_consistency()` is a read-only verification function that compares row counts of `chunks`, `chunks_fts`, and `chunks_vec`, returning a `RagConsistencyReport` (`db/models.py`). See code for details on consistency conditions and error message generation logic.

### 8d. Automatic Legacy Schema Detection for `mdq.sqlite` Only

`scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` is a third pattern of schema update, distinct from rag/session/eventbus and workflow, which runs automatically upon MDQ service startup.

- **Trigger:** Called every time the MDQ service starts (no explicit migration command required).
- **Detection:** Determines if the schema is legacy using `PRAGMA table_info(chunks)`.
- **Action:** If a legacy schema is detected, it unconditionally `DROP`s the `chunks`/`chunks_fts` tables and related triggers, then recreates them with the current schema.
- **Comparison:** Unlike 8a's `workflow.sqlite`, there are no version control columns or explicit `ALTER TABLE` migration lists — it simply inspects the schema shape at startup and rebuilds it silently if it is outdated.
- **Data Loss Warning:** The `DROP` during legacy schema detection is unconditional; existing data is lost after recreation.

The `chunks_vec` (`rag.sqlite`) and `memories_vec` (`session.sqlite`) tables defined in `db/schema_sql.py` are unrelated to the MDQ schema and are unaffected.

### 8e. Supported Upgrade Baseline

The minimum supported source schema of each database is the schema of the current release. A database older than that is recreated, not migrated, so no supported database depends on the migration mechanisms of sections 8a, 8b, and 8d. Every one of those migrations is classified removable; each database's migration code is removed by its own change.

| Database | Minimum supported source schema | Why the migration code is kept | Removal condition | Owner |
|---|---|---|---|---|
| `workflow.sqlite` | The current release schema: the recorded workflow schema version equals the current `WORKFLOW_SCHEMA_VERSION` | It stays until the change that removes it lands; no supported database needs it | No supported database is older than the minimum supported source schema | The workflow engine |
| `eventbus.sqlite` | The current release schema defined by `scripts/eventbus/schema.sql` | Same | Same | The EventBus service |
| `mdq.sqlite` | The current `chunks` shape, keyed by `chunk_id` | Same; a rebuilt store is recovered by re-indexing the Markdown files | Same | The `mdq-mcp` server |

How to read a database's current schema without changing it: [DB API and Operations](db_07_api_and_operations-recovery-and-reference.md#11a-identifying-a-databases-current-schema) (section 11a).

Open decisions (owner in parentheses):

- Whether the two EventBus migration paths of section 8b stay separate while they exist (the EventBus service).
- Whether `eventbus.sqlite` needs a schema-version marker; it has none (the EventBus service).
- Whether a failed migration needs a rollback beyond the pre-upgrade backup of `workflow.sqlite` that the deployment guide requires (the repository maintainers).

---

## 9. Schema Evolution

Schema evolution rules per database are defined in sections 8 through 8d; the minimum supported source schema of each database is in section 8e. For `eventbus.sqlite`, `scripts/eventbus/schema.py::_migrate()` applies the idempotent additive changes described in section 8b.

### Offset Seeding

`scripts/eventbus/offset_migrator.py::migrate_legacy_offsets()` is called at EventBus startup (`scripts/eventbus/app.py`). It seeds the `consumer_offsets` table from files under `offsets_dir`. It reads each `.map` companion file to recover the original `consumer_id` (falling back to the sanitized filename when no companion exists, with a warning), then inserts the offset using `INSERT OR IGNORE` (idempotent). It does not modify or delete the offset files. The service keeps the files; the end condition of the import, the retention rule, and the owner are in [EventBus configuration and operations](../24_eventbus/eventbus_07_configuration-and-operations.md#legacy-offset-files), and the supported baseline is in section 8e.

---

## 10. Source of Truth

DDL source: `db/schema_sql.py`; schema initialization entry point: `db/create_schema.py::create_schema()`; deploy initialization entry point: `deploy/init_db.sh`; DB connection helper: `db/helper.py::SQLiteHelper`; DB files: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`; Event Bus schema (DDL only): `scripts/eventbus/schema.sql`; mdq.sqlite schema/auto-update source: `scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` (see section 8d).

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
