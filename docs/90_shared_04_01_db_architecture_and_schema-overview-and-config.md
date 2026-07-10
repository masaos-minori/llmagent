---
title: "DB Architecture and Schema - Overview and Config"
category: shared
tags:
  - shared
  - db
  - dbconfig
  - sqlitehelper
  - layer-structure
related:
  - 90_shared_00_document-guide.md
  - 90_shared_04_02_db_architecture_and_schema-schema-reference.md
  - 90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md
source:
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
---

# DB Architecture and Schema

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 1. Purpose

Documents the `db/` layer structure, DB file organization, `DbConfig`, `SQLiteHelper`
connection behavior, WAL/FTS5/sqlite-vec configuration, all table schemas, and schema
initialization approach.

---

## 2. Overall DB Layer Structure

```
db/
├── helper.py          SQLiteHelper — connection lifecycle, PRAGMA, vec extension
├── create_schema.py   DDL creation (rag + session schemas; idempotent)
├── store_protocols.py Protocol definitions (MemoryDeleteStore, VectorStore, ...)
├── store_impl.py      SQLite implementations of store protocols
├── store.py           Re-export stub — public API surface for db.store imports
├── maintenance.py     WAL checkpoint, VACUUM, purge, rotate, recover
└── create_schema.py DDL creation (rag + session + workflow + eventbus schemas; idempotent)
```

Four DB files:

| DB | Default path | Tables |
|---|---|---|
| `rag.sqlite` | `agent.toml::rag_db_path` | `documents`, `chunks`, `chunks_fts`, `chunks_vec` |
| `session.sqlite` | `agent.toml::session_db_path` | `sessions`, `messages`, `memories`, `memories_fts`, `memories_vec`, `memory_links`, `session_diagnostics` |
| `workflow.sqlite` | `agent.toml::workflow_db_path` | `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals` |
| `eventbus.sqlite` | `agent.toml::eventbus_db_path` | `events` |

**Why separate DB files?** RAG indexing and conversation state have different access patterns.
`rag.sqlite` is write-heavy during ingestion, read-heavy during queries.
`session.sqlite` is append-heavy during conversations. Separation avoids WAL contention.

**Import boundary:** See [90_shared_05 §1a](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries) for the full import rules — callers should always import from `db.store`, never from internal modules directly.

---

## 3. `DbConfig` (`db/config.py`)

```python
@dataclass(frozen=True)
class DbConfig:
    rag_db_path: str           # path to rag.sqlite
    session_db_path: str       # path to session.sqlite
    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"  # path to workflow.sqlite
    eventbus_db_path: str = "/opt/llm/db/eventbus.sqlite"  # path to eventbus.sqlite
    sqlite_vec_so: str = ""    # path to vec0.so (empty = vec extension not needed)
    sqlite_timeout: int = 30   # sqlite3.connect() timeout (seconds, >= 1)
    sqlite_busy_timeout_ms: int = 30000   # PRAGMA busy_timeout (ms)
    embedding_dims: int = 384  # embedding vector dimension
```

- `__post_init__` validates all path fields are non-empty, `sqlite_timeout >= 1`, `embedding_dims >= 1`, and that each DB path's parent directory exists (the DB file itself is created by SQLite on first open)
- `embed_url` field does NOT exist in `DbConfig`
- Constructed by `build_db_config()` in `db/config.py`
- `agent.toml` is loaded via `ConfigLoader().load_all()` (included at index 0 of `_BASE_CONFIG_FILES`) — see [90_shared_03](90_shared_03_01_runtime_and_execution-config-and-logging.md) §2a Config Ownership for the full ownership table

---

## 4. DB File Structure and `SQLiteHelper`

`SQLiteHelper` manages connection lifecycle. Constructor resolves config at init time.

```python
SQLiteHelper(target: DbTarget | str = "rag")
# DbTarget.RAG, DbTarget.SESSION, DbTarget.WORKFLOW, or string literal
# "rag"      → rag.sqlite
# "session"  → session.sqlite
# "workflow" → workflow.sqlite
# "eventbus" → eventbus.sqlite (Event Bus DDL only; no runtime integration yet)
```

**Note:** Event Bus runtime (publisher/subscriber/dispatcher/DLQ worker) is out of scope for this cleanup. Future Event Bus writers must use ISO-8601 UTC Z suffix timestamps.

**Connection setup (every `open()` call):**
1. Load sqlite-vec extension (rag target only); then `enable_load_extension(False)`
2. `PRAGMA journal_mode=WAL`
3. `PRAGMA synchronous=NORMAL`
4. `PRAGMA busy_timeout=30000` (from `agent.toml::sqlite_busy_timeout_ms`)
5. `PRAGMA foreign_keys=ON` (when `write_mode=True`)

sqlite-vec is loaded only for `target="rag"`. Session and workflow targets do not load vec.

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_04_02_db_architecture_and_schema-schema-reference.md`
- `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

## Keywords

DbConfig
SQLiteHelper
DB layer structure
DB file structure
