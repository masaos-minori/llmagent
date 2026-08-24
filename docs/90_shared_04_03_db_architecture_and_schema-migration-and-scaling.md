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
  - 90_shared_00_document-guide.md
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
  - 90_shared_04_02_db_architecture_and_schema-schema-reference.md
source:
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
---

# DB Architecture and Schema

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 8. Schema Generation and Migration Policy

```python
# Initialize all schemas (rag + session + workflow + eventbus)
from db.create_schema import create_schema
create_schema()
```

- All DDL uses `IF NOT EXISTS` — idempotent and safe to run multiple times.
- **`rag.sqlite`, `session.sqlite`, and `eventbus.sqlite` do not support backward-compatible migrations.** Changes to these schemas require database recreation: Archive → Delete → Recreate via `create_schema()`. Refer to [90_shared_05 section 11](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure) for the full procedure. `workflow.sqlite` (section 8a) and `mdq.sqlite` (section 8c) each have different migration/automatic schema update mechanisms — see respective sections for details.
- `embedding_dims` is dynamically replaced from config at runtime (default 384).

### 8a. Incremental Migrations for `workflow.sqlite` Only (Explicit in code)

The principle that "rag/session/eventbus do not support backward-compatible migrations" applies only to those three databases. `workflow.sqlite` is an exception, as `db/schema_sql.py` implements a dedicated incremental migration mechanism.

- `db/schema_sql.py` maintains a migration list in `list[tuple[str, str]]` format (ID + SQL statement pairs) and applies them sequentially using `apply_workflow_migrations()`.
- It catches `sqlite3.OperationalError` containing `"duplicate column name"` (treating it as already applied) while re-raising others.
- `create_workflow_schema()` creates base tables, then applies migrations, and finally records the version.
- For new databases, migrations are no-ops since base schemas already contain the required columns. They function as incremental column additions for existing databases.

Incremental migration mechanisms like this do not exist for `rag.sqlite`, `session.sqlite`, or `eventbus.sqlite`.

### 8b. RAG Consistency Verification (Explicit in code)

`db/rag_consistency.py::check_rag_consistency()` is a read-only verification function that compares row counts of `chunks`, `chunks_fts`, and `chunks_vec`, returning a `RagConsistencyReport` (`db/models.py`). See code for details on consistency conditions and error message generation logic.

### 8c. Automatic Legacy Schema Detection for `mdq.sqlite` Only (Explicit in code)

`scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` is a third pattern of schema update, distinct from rag/session/eventbus and workflow, which runs automatically upon MDQ service startup.

- **Trigger:** Called every time the MDQ service starts (no explicit migration command required).
- **Detection:** Determines if the schema is legacy using `PRAGMA table_info(chunks)`.
- **Action:** If a legacy schema is detected, it unconditionally `DROP`s the `chunks`/`chunks_fts` tables and related triggers, then recreates them with the current schema.
- **Comparison:** Unlike 8a's `workflow.sqlite`, there are no version control columns or explicit `ALTER TABLE` migration lists — it simply inspects the schema shape at startup and rebuilds it silently if it is outdated.
- **Data Loss Warning:** The `DROP` during legacy schema detection is unconditional; existing data is lost after recreation.

The `chunks_vec`/`memories_vec` (`db/schema_sql.py`) for `rag.sqlite`, `session.sqlite`, and `eventbus.sqlite` are unrelated to the MDQ schema/hybrid search cleanup and are unaffected.

---

## 9. Constraints List

SQLite 3.35+ required; sqlite-vec path `/opt/llm/sqlite-vec/vec0.so` (`agent.toml::sqlite_vec_so`); WAL mode enabled on all connections (`PRAGMA journal_mode=WAL`); default `busy_timeout` 30,000 ms (`agent.toml::sqlite_busy_timeout_ms`); default embedding dimension 384 (`agent.toml::embedding_dims`); float format: float32 little-endian BLOB; single-node only (no distributed/replica support); `agent.toml` included in `ConfigLoader().load_all()` at index 0 (see 90_shared_03 section 2a).

---

## 9a. AI Reference Guide

rag.sqlite schema location: this doc section 5; session.sqlite schema location: this doc section 6; SQLiteHelper supports workflow.sqlite: yes (target="workflow", not documented in spec, see section 4); embedding dimension set via `agent.toml::embedding_dims` (default 384); schema initializer: `create_schema()` — idempotent DDL-only initialization, not migration; DB triggers documented: `chunks_fts` auto-sync triggers (section 5), `memories_fts` auto-sync triggers (section 6).

---

## 10. Source of Truth

DDL source: `db/schema_sql.py`; schema initialization entry point: `db/create_schema.py::create_schema()`; deploy initialization entry point: `deploy/init_db.sh`; DB connection helper: `db/helper.py::SQLiteHelper`; DB files: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`; Event Bus schema (DDL only): `scripts/eventbus/schema.sql`; mdq.sqlite schema/auto-update source: `scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` (see section 8c); deleted entry point: `db/workflow_schema.py` — removed in plan 54.

**Note:** The Event Bus runtime (publisher/subscriber/dispatcher/DLQ worker) is outside the scope of this cleanup. Future Event Bus write operations must use ISO-8601 UTC Z-suffix timestamps.

## 11. Scaling Limits and Migration Indicators

The current RAG architecture uses single-node SQLite. This is suitable for team-scale deployments where corpus size is moderate and concurrent writes are infrequent.
The following indicators suggest a need for re-evaluation.

### Corpus Size

- **When `chunks` table exceeds ~500,000 rows:** KNN scan time in `chunks_vec` increases linearly with corpus size. Start monitoring `/rag search` latency at this scale. *(Note: Actual thresholds depend on hardware and embedding dimensions.)*
- **When DB file size exceeds ~10GB:** Latency for `VACUUM`, backups, and WAL checkpoints will increase, and `/db vacuum` may take minutes instead of seconds. *(Note: To be verified.)*

### Write Concurrency

- When multiple `RagIngester` processes write to the same `rag.sqlite`, they are serialized at the WAL layer. If ingestion throughput becomes a bottleneck, SQLite write serialization may become a constraint.
- **Indicator:** WAL files grow faster than checkpointing can shrink them. Monitor via `/db health`.

### FTS5 Search Latency

- **Indicator:** `/rag search` consistently takes over 500ms. Since FTS5 BM25 scales with document count, search speed may decrease with very large corpora. *(Note: To be verified.)*

### Operational Complexity Indicators

- Backups and point-in-time recovery become more complex as file sizes increase.
- Sharing the same DB file across multiple environments is not supported (SQLite is a single-file system).
- Resolving issues with `/session rag-consistency` becomes harder as scale increases.

### Migration Indicator Checklist

Consider architectural review if two or more apply:

- [ ] p95 KNN search latency exceeds 1 second
- [ ] DB file size exceeds 20GB
- [ ] WAL checkpoints consistently exceed 30 seconds
- [ ] Ingestion queue depth consistently exceeds 10,000 unprocessed chunk files
- [ ] Multiple teams or processes require simultaneous write access

Monitor these indicators during normal operation using `/db health` and `/session rag-consistency`.

### Considerations when limits are approached

- **Vector Search:** Dedicated vector databases (Approximate Nearest Neighbor search, distributed indexing) outperform `sqlite-vec` at scales exceeding 1 million vectors.
- **Full-Text Search:** Full-text search services offer lower latency for large corpora.
- **Hybrid Store:** Relational DB + Vector extensions (e.g., `pgvector` compatible) allow scaling write concurrency while maintaining SQL semantics.

> **Note:** The numerical thresholds above are estimates and not guaranteed by benchmarking. Actual limits depend on hardware, embedding dimensions, query patterns, and corpus characteristics. Always verify in individual deployment environments before treating any threshold as definitive.

## 12. Schema Change Checklist

Before performing a schema change task, answer all of the following:

- [ ] Which DB is affected? (rag/session/workflow/eventbus/mdq)
- [ ] Which schema source files are affected?
- [ ] Is this a DDL change exclusive to new installations?
- [ ] Is a migration required for existing databases?
- [ ] If no migration is provided, is database recreation required?
- [ ] Is there a possibility of data loss?
- [ ] Are tests updated to reflect the schema behavior?
- [ ] Which component is affected: RAG, session, workflow, eventbus, or MDQ?
