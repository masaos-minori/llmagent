---
title: "DB Architecture and Schema - Overview and Config"
area: shared
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

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 1. Purpose

Describes the `db/` layer structure, DB file configuration, `DbConfig`, `SQLiteHelper` connection behavior, WAL/FTS5/sqlite-vec settings, all table schemas, and schema initialization methods.

---

## 2. DB Layer Overall Structure

`db/` contains `helper.py` (connection lifecycle, PRAGMA, vec extension), `create_schema.py` (DDL creation idempotent for rag/session/workflow/eventbus schemas), `store_protocols.py` (MemoryDeleteStore, VectorStore protocol definitions), `store_impl.py` (SQLite implementations of store protocols), `store.py` (public re-export layer for `db.store` imports), `maintenance.py` (WAL checkpoint, VACUUM, purge, rotate, recover).

Four DB files exist: `rag.sqlite` (agent.toml::rag_db_path, documents/chunks/chunks_fts/chunks_vec tables), `session.sqlite` (agent.toml::session_db_path, sessions/messages/memories/memories_fts/memories_vec/memory_links/session_diagnostics tables), `workflow.sqlite` (agent.toml::workflow_db_path, tasks/attempts/processed_events/artifacts/approvals tables), `eventbus.sqlite` (agent.toml::eventbus_db_path, events table). DB files separated because RAG indexing and conversation state have different access patterns; `rag.sqlite` writes heavily during ingestion and reads during query; `session.sqlite` appends heavily during conversations; separation avoids WAL contention.

**Why separate DB files?** RAG indexing and conversation state have different access patterns. `rag.sqlite` has high write volume during ingestion and high read volume during queries. `session.sqlite` is append-heavy during conversations. Separation avoids WAL contention.

**Import Boundaries:** For complete import rules, see [90_shared_05 section 1a](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries). Callers should always import from `db.store` and must not import directly from internal modules.

---

## 3. `DbConfig` (`db/config.py`)

Frozen dataclass for DB configuration. `rag_db_path` (path to `rag.sqlite`), `session_db_path` (path to `session.sqlite`), `workflow_db_path` (default `/opt/llm/db/workflow.sqlite`), `eventbus_db_path` (default `/opt/llm/db/eventbus.sqlite`), `sqlite_vec_so` (path to `vec0.so`, empty = vec extension not needed), `sqlite_timeout` (sqlite3.connect() timeout seconds >= 1), `sqlite_busy_timeout_ms` (PRAGMA busy_timeout ms default 30000), `embedding_dims` (embedding vector dimension default 384). `__post_init__` validates all path fields non-empty, `sqlite_timeout` >= 1, `embedding_dims` >= 1, parent directories exist (DB files themselves created on first open). No `embed_url` field exists. Built by `build_db_config()` in `db/config.py`. `agent.toml` loaded via `ConfigLoader().load_all()` (_BASE_CONFIG_FILES index 0 included).

---

## 4. DB File Structure and `SQLiteHelper`

`SQLiteHelper` manages connection lifecycle. Constructor accepts target parameter resolving to specific DB file: `DbTarget.RAG` → `rag.sqlite`, `DbTarget.SESSION` → `session.sqlite`, `DbTarget.WORKFLOW` → `workflow.sqlite`, `DbTarget.EVENTBUS` → `eventbus.sqlite` (Event Bus DDL only; no runtime integration yet). `DbTarget` is `StrEnum` defined in `db/helper.py` (`RAG`/`SESSION`/`WORKFLOW`/`EVENTBUS`); target parameter accepts enum member or same-named string literal. Connection setup per `open()` call: load `sqlite-vec` extension (rag target only), then `enable_load_extension(False)`; set `PRAGMA journal_mode=WAL`; set `PRAGMA synchronous=NORMAL`; set `PRAGMA busy_timeout=30000` (from `agent.toml::sqlite_busy_timeout_ms`); set `PRAGMA foreign_keys=ON` (when `write_mode=True`). `sqlite-vec` loaded only when `target='rag'`; `session` and `workflow` targets do not load `vec`.

### 4a. `SQLiteHelper` constructor `db_path` override (Explicit in code)

`SQLiteHelper.__init__()` can accept a `db_path` keyword argument. If provided, it completely bypasses `build_db_config()` (i.e., loading `agent.toml`) and uses the provided `db_path` / `sqlite_vec_so` / `sqlite_timeout` / `sqlite_busy_timeout_ms` directly (`db/helper.py` `SQLiteHelper.__init__`). This provides a path for callers like MCP servers that want to specify a DB path independently of `agent.toml`. If `db_path` is not specified, paths are resolved from the results of `build_db_config()` according to the `target` as before.

### 4b. Additional options for `open()` (Explicit in code)

`open()` accepts the following in addition to the `write_mode` / `row_factory` mentioned in the text:

- `load_vec: bool | None = None` — If `None`, follows the target-specific default (only `rag` is `True`). Passing `True` or `False` explicitly overrides the default.
- `reuse_connection: bool = False` — If `True` and an existing `self.conn` is present, reconnection is skipped. In this case, `close()` is not called in `__exit__` (allowing connection reuse).

### 4c. Transaction helpers (Explicit in code)

`SQLiteHelper` provides context managers `begin_immediate()` / `begin_exclusive()` that wrap `BEGIN IMMEDIATE` / `BEGIN EXCLUSIVE`. Both attempt a `ROLLBACK` upon normal exceptions (swallowing `sqlite3.OperationalError`) and re-raise the original exception. They do not catch `BaseException` (e.g., `KeyboardInterrupt`/`SystemExit`). `begin_exclusive()` is intended specifically for operations requiring exclusive locks, such as `VACUUM` or schema changes (`see db/helper.py` docstring).

---
