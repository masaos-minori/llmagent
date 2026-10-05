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
  - shared_00_document-guide.md
  - db_02_architecture_and_schema-schema-reference.md
  - db_03_architecture_and_schema-migration-and-scaling.md
---

# DB Architecture and Schema

- Overview → [shared_00_document-guide.md](../40_shared/shared_00_document-guide.md)
- DB API → [db_04_api_and_operations-module-boundaries-and-helper.md](db_04_api_and_operations-module-boundaries-and-helper.md)

## 1. Purpose

Describes the `db/` layer structure, DB file configuration, `DbConfig`, `SQLiteHelper` connection behavior, WAL/FTS5/sqlite-vec settings, all table schemas, and schema initialization methods.

---

## 2. DB Layer Overall Structure

`db/` contains `helper.py` (connection lifecycle, PRAGMA, vec extension), `create_schema.py` (DDL creation idempotent for rag/session/workflow/eventbus schemas), `store_protocols.py` (MemoryDeleteStore, VectorStore protocol definitions), `store_impl.py` (SQLite implementations of store protocols), `store.py` (public re-export layer for `db.store` imports), `maintenance.py` (WAL checkpoint, VACUUM, purge, rotate, recover).

Four DB files exist: `rag.sqlite` (agent.toml::rag_db_path, documents/chunks/chunks_fts/chunks_vec tables), `session.sqlite` (agent.toml::session_db_path, sessions/messages/memories/memories_fts/memories_vec/memory_links/session_diagnostics tables), `workflow.sqlite` (agent.toml::workflow_db_path, tasks/attempts/processed_events/artifacts/approvals tables), `eventbus.sqlite` (agent.toml::eventbus_db_path, events/consumer_delivery/consumer_offsets tables). DB files separated because RAG indexing and conversation state have different access patterns; `rag.sqlite` writes heavily during ingestion and reads during query; `session.sqlite` appends heavily during conversations; separation avoids WAL contention.

**Import Boundaries:** For complete import rules, see [db_04 section 1a](db_04_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries). Callers should always import from `db.store` and must not import directly from internal modules.

---

## 3. `DbConfig` (`db/config.py`)

Frozen dataclass for DB configuration. `rag_db_path` (path to `rag.sqlite`), `session_db_path` (path to `session.sqlite`), `workflow_db_path` and `eventbus_db_path` (both fall back to code-level defaults when absent from `agent.toml`), `sqlite_vec_so` (path to `vec0.so`, empty = vec extension not needed), `sqlite_timeout` (sqlite3.connect() timeout seconds >= 1), `sqlite_busy_timeout_ms` (PRAGMA busy_timeout in ms). `__post_init__` validates all path fields non-empty, `sqlite_timeout` >= 1, parent directories exist (DB files themselves created on first open). Embedding dimension is sourced from `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed code constant), not a `DbConfig` field. No `embed_url` field exists. Built by `build_db_config()` in `db/config.py`. `agent.toml` loaded via `ConfigLoader().load_all()` (_BASE_CONFIG_FILES index 0 included).

---

## 4. DB File Structure and `SQLiteHelper`

`SQLiteHelper` manages connection lifecycle. Constructor accepts target parameter resolving to specific DB file: `DbTarget.RAG` → `rag.sqlite`, `DbTarget.SESSION` → `session.sqlite`, `DbTarget.WORKFLOW` → `workflow.sqlite`, `DbTarget.EVENTBUS` → `eventbus.sqlite` (used only by `create_schema()` for Event Bus DDL; the Event Bus service opens its own connection through `open_db()` in `scripts/eventbus/db_conn.py` and does not use `SQLiteHelper`). `DbTarget` is `StrEnum` defined in `db/helper.py` (`RAG`/`SESSION`/`WORKFLOW`/`EVENTBUS`); target parameter accepts enum member or same-named string literal. Connection setup per `open()` call: load `sqlite-vec` extension (default for the rag target only, and only when `sqlite_vec_so` is non-empty), then `enable_load_extension(False)`; set `PRAGMA journal_mode=WAL`; set `PRAGMA synchronous=NORMAL`; set `PRAGMA busy_timeout` (from `agent.toml::sqlite_busy_timeout_ms`); set `PRAGMA foreign_keys=ON` (when `write_mode=True`). By default `sqlite-vec` is loaded only when `target='rag'`; `session`, `workflow`, and `eventbus` targets do not load `vec`. When `db_path` is passed explicitly (see 4a), the default instead follows whether `sqlite_vec_so` is non-empty (Explicit in code, `SQLiteHelper.__init__`).

### 4a. `SQLiteHelper` constructor `db_path` override (Explicit in code)

`SQLiteHelper.__init__()` can accept a `db_path` keyword argument. If provided, it completely bypasses `build_db_config()` (i.e., loading `agent.toml`) and uses the provided `db_path` / `sqlite_vec_so` / `sqlite_timeout` / `sqlite_busy_timeout_ms` directly (`db/helper.py` `SQLiteHelper.__init__`). This provides a path for callers like MCP servers that want to specify a DB path independently of `agent.toml`. If `db_path` is not specified, paths are resolved from the results of `build_db_config()` according to the `target` as before.

### 4b. Additional options for `open()` (Explicit in code)

`open()` accepts the following in addition to the `write_mode` / `row_factory` mentioned in the text:

- `load_vec: bool | None = None` — If `None`, follows the instance default (`True` for the `rag` target; with an explicit `db_path`, `True` only when `sqlite_vec_so` is non-empty; `False` otherwise). The extension is loaded only when the resolved flag is `True` and `sqlite_vec_so` is non-empty. Passing `True` or `False` explicitly overrides the default.
- `reuse_connection: bool = False` — If `True` and an existing `self.conn` is present, reconnection is skipped. In this case, `close()` is not called in `__exit__` (allowing connection reuse).

### 4c. Transaction helpers (Explicit in code)

`SQLiteHelper` provides context managers `begin_immediate()` / `begin_exclusive()` that wrap `BEGIN IMMEDIATE` / `BEGIN EXCLUSIVE`. Both attempt a `ROLLBACK` upon normal exceptions (swallowing `sqlite3.OperationalError`) and re-raise the original exception. They do not catch `BaseException` (e.g., `KeyboardInterrupt`/`SystemExit`). `begin_exclusive()` is intended specifically for operations requiring exclusive locks, such as `VACUUM` or schema changes (`see db/helper.py` docstring).

---

## Keywords

- shared
- db
- dbconfig
- sqlitehelper
- layer-structure
