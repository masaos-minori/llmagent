---
title: "DB Architecture and Schema - Migration and Scaling"
category: shared
tags:
  - shared
  - db
  - migration
  - constraints
  - scaling-limits
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_04_db_architecture_and_schema-overview-and-config.md
  - 90_shared_04_db_architecture_and_schema-schema-reference.md
source:
  - 90_shared_04_db_architecture_and_schema-overview-and-config.md
---

# DB Architecture and Schema

- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_db_api_and_operations-module-boundaries-and-helper.md)

## 8. Schema Generation and Migration Approach

```python
# Initialize all schemas (rag + session + workflow + eventbus)
from db.create_schema import create_schema
create_schema()
```

- All DDL uses `IF NOT EXISTS` — idempotent; safe to run multiple times
- **Compatible migration is unsupported.** Schema changes require DB recreation: archive → delete → recreate via `create_schema()`. See [90_shared_05 §11](90_shared_05_db_api_and_operations-module-boundaries-and-helper.md#11-db-recreation-procedure) for the full procedure.
- `embedding_dims` is substituted dynamically at runtime from config (default 384)

---

## 9. Constraint List

| Constraint | Value |
|---|---|
| SQLite version | 3.35+ required |
| sqlite-vec path | `/opt/llm/sqlite-vec/vec0.so` (from `agent.toml::sqlite_vec_so`) |
| WAL mode | All connections; `PRAGMA journal_mode=WAL` |
| busy_timeout | 30,000 ms default (`agent.toml::sqlite_busy_timeout_ms`) |
| Embedding dimension | 384 default (`agent.toml::embedding_dims`) |
| Float format | float32 little-endian BLOB |
| Single-node only | No distributed/replica support |
| `agent.toml` loading | Included in `ConfigLoader().load_all()` at index 0 — see [90_shared_03](90_shared_03_runtime_and_execution-config-and-logging.md) §2a Config Ownership for ownership table |

---

## 9a. AI Reference Guide

| Question | Answer |
|---|---|
| Where is rag.sqlite schema? | This document §5 |
| Where is session.sqlite schema? | This document §6 |
| Does `SQLiteHelper` support workflow.sqlite? | Yes — `target="workflow"` (undocumented in spec, see §4) |
| How is embedding dimension set? | `agent.toml::embedding_dims` (default 384) |
| What initializes schemas? | `create_schema()` — idempotent DDL-only initialization; no migration |
| Are DB triggers documented? | Yes — chunks_fts auto-sync triggers (§5), memories_fts auto-sync triggers (§6) |

---

## 10. Source of Truth

| Category | Source |
|---|---|
| DDL source | `db/schema_sql.py` |
| Schema initialization entry point | `db/create_schema.py::create_schema()` |
| Deploy initialization entry point | `deploy/init_db.sh` |
| DB connection helper | `db/helper.py::SQLiteHelper` |
| DB files | `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite` |
| Event Bus schema (DDL only) | `scripts/eventbus/schema.sql` |
| Deleted entry point | `db/workflow_schema.py` — removed in plan 54 |

**Note:** Event Bus runtime (publisher/subscriber/dispatcher/DLQ worker) is out of scope for this cleanup. Future Event Bus writers must use ISO-8601 UTC Z suffix timestamps.

## 11. Scaling Limits and Migration Signals

The current RAG architecture uses single-node SQLite. This is appropriate for
team-scale deployments with moderate corpus sizes and infrequent concurrent writes.
The following signals indicate when re-evaluation may be warranted.

### Corpus size

- **`chunks` table > ~500K rows:** KNN scan time in `chunks_vec` grows linearly with corpus
  size; start monitoring `/rag search` latency at this scale.
  *(Needs confirmation: actual threshold depends on hardware and embedding dimensions.)*
- **DB file size > ~10 GB:** VACUUM time, backup duration, and WAL checkpoint latency all
  increase; `/db vacuum` may take minutes instead of seconds.
  *(Needs confirmation.)*

### Write concurrency

- Multiple simultaneous `RagIngester` processes writing to the same `rag.sqlite` serialize
  at the WAL layer. If ingestion throughput becomes a bottleneck, SQLite write serialization
  may be limiting.
- **Signal:** WAL file grows faster than checkpoint reduces it. Monitor with `/db health`.

### FTS5 search latency

- **Signal:** `/rag search` consistently takes > 500 ms. FTS5 BM25 scales with document
  count; very large corpora may see degraded search speed.
  *(Needs confirmation.)*

### Operational complexity signals

- Backup and point-in-time recovery become complex as file size grows
- Multiple environments sharing the same DB file is not supported (SQLite is single-file)
- `/db consistency` issues become harder to repair at scale

### Migration signal checklist

When two or more of the following apply, consider an architecture review:

- [ ] KNN search latency > 1 s at p95
- [ ] DB file size > 20 GB
- [ ] WAL checkpoint consistently takes > 30 s
- [ ] Ingest queue depth consistently > 10 K unprocessed chunk files
- [ ] Multiple teams or processes need simultaneous write access

Use `/db health` and `/db consistency` to monitor these signals in normal operations.

### What to evaluate when limits approach

- **Vector search:** Dedicated vector databases (approximate nearest neighbor, distributed
  index) outperform `sqlite-vec` at > 1 M vectors
- **Full-text search:** Inverted-index search services handle large corpora with lower latency
- **Hybrid stores:** Relational DB + vector extension (e.g. `pgvector`-compatible) preserves
  SQL semantics while scaling write concurrency

> **Note:** All numeric thresholds above are planning estimates, not benchmarked guarantees.
> Actual limits depend on hardware, embedding dimensions, query patterns, and corpus
> characteristics. Validate with your specific deployment before treating any threshold as firm.

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_04_db_architecture_and_schema-overview-and-config.md`
- `90_shared_04_db_architecture_and_schema-schema-reference.md`

## Keywords

schema generation
migration approach
constraint list
source of truth
scaling limits
