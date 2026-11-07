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

## 8. Schema Generation and Current-Schema-Only Policy

`create_schema()` (`db/create_schema.py`) initializes all four schemas (rag, session, workflow, eventbus).

- All statements in create-only DDL use `IF NOT EXISTS` — idempotent and safe to run multiple times.
- **No automatic migration and no version stamping of existing databases exist for any domain.** A database that does not match the current schema is refused at startup or by a health/deploy gate and is never mutated, archived, or deleted by the software. The operator archives it and recreates it from the current canonical DDL.
- Refusal wording (identical policy, per-domain wording): "The database does not match the current schema. Automatic migration and version stamping are not supported. Stop the service, archive the existing database if required, remove or rename it, and create a new database using the current schema."
- `create_schema()` is a wrapper that calls the four per-database initializers in order: `create_rag_schema()` and `create_session_schema()` run create-only DDL; `create_workflow_schema()` runs the create-only DDL without recording any version; `create_eventbus_schema()` runs the create-only DDL read from `scripts/eventbus/schema.sql` (section 8b). Against an existing matching file all four change nothing.
- The embedding dimension is a fixed code-level constant (`get_embedding_dims()`), not a config key.

### Recreating `session.sqlite`: Session and Memory Recovery

Recreating `session.sqlite` physically removes both sessions and memories, but they are recovered by different paths:

1. Export any conversation worth keeping with `/session export` before recreating.
2. Recreate `session.sqlite` (Archive → Delete → Recreate).
3. Recover memory only, from the JSONL archive, with `/memory rebuild`.
4. Past session history is not restored into the database; `/memory rebuild` does not recover sessions and `/session export` output is for human reference only.

### 8a. Startup Validation for `workflow.sqlite`

`workflow.sqlite` is accepted only when the current required tables (`tasks`, `attempts`, `processed_events`, `artifacts`) and their required columns are present. `check_workflow_schema()` (agent startup) enforces this shape. A database that carries `schema_migrations` or `workflow_schema_version` is a legacy migration-era database: `check_workflow_schema()` and the deploy pre-flight (`deploy/init_db.sh`) refuse it with the fixed message, and the file is left untouched for manual archive-and-recreate. The workflow domain has no version identifier and no migration path.

### 8b. Startup Validation for `eventbus.sqlite`

`create_eventbus_schema()` (`db/create_schema.py`) and the EventBus service (`open_db()`) both create the schema from the single DDL definition in `scripts/eventbus/schema.sql`, read through `build_eventbus_schema_sql()`. `schema.sql` ends with `PRAGMA user_version = 6;`: new databases receive that stamp from the canonical DDL itself. Validation gates:

- An existing database is accepted only when `PRAGMA user_version` equals the version stamped by the canonical DDL and its tables, columns, and indexes match the `shared/eventbus_schema_fingerprint.py` fingerprint computed from `schema.sql` at runtime.
- An unstamped existing database (`user_version 0`) is refused and left unstamped, even when its shape matches.
- Any other version or shape difference is refused. Every refusal names the database path and leaves the file unmodified.

`events.published_at` has a `DEFAULT` expression in `schema.sql`; every insert path (`POST /publish` and the DLQ requeue) supplies `published_at` explicitly. Table roles: `eventbus_06_persistence_schema_and_replay.md`.

### 8c. RAG Consistency Verification

`db/rag_consistency.py::check_rag_consistency()` is a read-only verification function that compares row counts of `chunks`, `chunks_fts`, and `chunks_vec`, returning a `RagConsistencyReport` (`db/models.py`). See code for details on consistency conditions and error message generation logic.

### 8d. Create-Only Tables for `mdq.sqlite`

`scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` creates the `mdq.sqlite` tables, triggers, and index state with `IF NOT EXISTS` statements every time the MDQ service starts; nothing is dropped or rewritten. `mdq.sqlite` is a derived store: a store older than the supported baseline is recovered by deleting the file and re-indexing the Markdown files (section 8e).

The `chunks_vec` (`rag.sqlite`) and `memories_vec` (`session.sqlite`) tables defined in `db/schema_sql.py` are unrelated to the MDQ schema and are unaffected.

### 8e. Supported Baseline and Archive-and-Recreate Runbook

The only supported source schema of each database is the schema of the current release. Nothing migrates: `rag`, `session`, `workflow`, `eventbus`, and `mdq` all accept the current shape only, and an older or marker-carrying database is refused (workflow/eventbus) or simply not upgraded (rag/session/mdq).

| Database | Accepted schema | Recovery when not accepted | Owner |
|---|---|---|---|
| `workflow.sqlite` | Current task-table shape, no legacy `schema_migrations` / `workflow_schema_version` markers | Archive and recreate (runbook below) | The workflow engine |
| `eventbus.sqlite` | `PRAGMA user_version = 6` plus the canonical `schema.sql` fingerprint | Archive and recreate (runbook below) | The EventBus service |
| `mdq.sqlite` | The current `chunks` shape, keyed by `chunk_id` | Delete the file and re-index the Markdown files (section 8d) | The `mdq-mcp` server |
| `rag.sqlite`, `session.sqlite` | Current create-only shape | Archive and recreate (runbook below) | RAG / session layers |

Recreation impact when a database is not accepted (full procedure: [db_07 section 11](db_07_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure)):

| Database | Data loss possible | Backup before recreation | Rollback |
|---|---|---|---|
| `workflow.sqlite` | Yes — task history is not carried over | Required: `rotate_all_dbs()` archives it (db_07 section 11, step 1) | Restore the archived file |
| `eventbus.sqlite` | Yes — events and delivery state are not carried over | Required: `rotate_all_dbs()` archives it (`rotate_eventbus_db()`) | Restore the archived file manually; no automated restoration path exists (db_07 section 9) |
| `mdq.sqlite` | No lasting loss — derived store, rebuilt from the Markdown files | Not required | Delete the file and re-index (section 8d) |

Archive-and-recreate runbook (operator procedure; details in [db_07 section 11](db_07_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure)):

1. Stop the affected service.
2. Archive the refused database with `rotate_all_dbs()` (per-DB archive helpers, verified copies).
3. Remove or rename the refused file. Automatic migration is not supported; do not attempt one.
4. Recreate the database with the current canonical DDL (`deploy/init_db.sh` or `create_schema()`).
5. Restart the service; the startup gate now accepts the new file.

How to read a database's current schema without changing it: [DB API and Operations](db_07_api_and_operations-recovery-and-reference.md#11a-identifying-a-databases-current-schema) (section 11a).

---

## 9. Schema Evolution

Schema evolution rules per database are defined in sections 8 through 8d. A canonical DDL change (workflow `schema_sql.py`, eventbus `schema.sql`, rag/session create-only DDL) lands as a new current shape: databases matching the previous shape stop matching and must be archived and recreated by the operator; there is no registered migration path to bridge shapes. The minimum supported source schema is always the current release (section 8e).

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

> **Note:** The indicators above are qualitative and are not backed by benchmarking. Actual limits depend on hardware, embedding dimensions, query patterns, and corpus characteristics. Always verify in individual deployment environments before treating any threshold as definitive.

## 13. Schema Change Checklist

Before performing a schema change task, answer all of the following:

- [ ] Which DB is affected? (rag/session/workflow/eventbus/mdq)
- [ ] Which schema source files are affected?
- [ ] Is this a DDL change exclusive to new installations?
- [ ] Which gate (startup, health check, deploy pre-flight) will refuse databases matching the old shape, and which docs and manifests must be regenerated with the new shape?
- [ ] Is database recreation required for existing databases? (No migration path exists; recreation is the only recovery)
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
