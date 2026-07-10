---
title: "DB Architecture - Timestamp Policy, Schema Generation, Constraints, and Source of Truth"
category: shared
tags:
  - db
  - architecture
  - timestamp
  - schema generation
  - constraint
  - ai reference guide
  - source of truth
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_04_db_overview_and_config.md
  - 90_shared_04_db_rag_schema.md
  - 90_shared_04_session_workflow_schemas.md
source:
  - 90_shared_04_db_overview_and_config.md
---

# DB Architecture - Timestamp Policy, Schema Generation, Constraints, and Source of Truth

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

---

## 7a. Timestamp Format Policy

All SQLite schema DEFAULT timestamps use `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` for consistency.

Tables using this format:

- `session_diagnostics.created_at` (Z suffix)
- `documents.fetched_at`, `sessions.created_at`, `messages.created_at`, `memories.created_at`, `memories.updated_at` (Z suffix)
- Event Bus: `events.published_at` (Z suffix)

Python-side timestamp generation (for workflow tables without DEFAULT): `datetime.now(UTC).isoformat()` — produces ISO-8601 with `+00:00` suffix (e.g., `2024-01-01T00:00:00+00:00`).

---

## 8. Schema Generation and Migration Approach

```python
# Initialize all schemas (rag + session + workflow + eventbus)
from db.create_schema import create_schema
create_schema()
```

- All DDL uses `IF NOT EXISTS` — idempotent; safe to run multiple times
- **Compatible migration is unsupported.** Schema changes require DB recreation: archive → delete → recreate via `create_schema()`. See [90_shared_05 §11](90_shared_05_db_module_boundaries_and_sqlitehelper.md#11-db-recreation-procedure) for the full procedure.
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
| `agent.toml` loading | Included in `ConfigLoader().load_all()` at index 0 — see [90_shared_03](90_shared_03_runtime_and_execution_infra.md) §2a Config Ownership for ownership table |

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

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)
- [90_shared_04_db_rag_schema.md](90_shared_04_db_rag_schema.md)
- [90_shared_04_session_workflow_schemas.md](90_shared_04_session_workflow_schemas.md)
- [90_shared_04_db_scaling_limits.md](90_shared_04_db_scaling_limits.md)
- [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

## Keywords

timestamp
schema generation
constraint
ai reference guide
source of truth
