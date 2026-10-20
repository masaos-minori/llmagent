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
  - db_04_api_and_operations-module-boundaries-and-helper.md
---

# DB Architecture and Schema

- Overview → [shared_00_document-guide.md](../40_shared/shared_00_document-guide.md)
- DB API → [db_04_api_and_operations-module-boundaries-and-helper.md](db_04_api_and_operations-module-boundaries-and-helper.md)

## 1. Purpose

Describes the `db/` layer responsibilities, DB file separation, `DbConfig` boundaries, and `SQLiteHelper` connection behavior (WAL, FTS5, sqlite-vec).

---

## 2. DB Layer Overall Structure

`db/` separates connection lifecycle (`helper.py`), idempotent DDL creation (`create_schema.py`), store protocols and their SQLite implementations (`store_protocols.py`, `store_impl.py`, re-exported through `store.py`), and maintenance operations (`maintenance.py`: WAL checkpoint, VACUUM, purge, rotate, recover).

Four DB files exist, each with its own path in `agent.toml`: `rag.sqlite` (documents, chunks, FTS and vector index), `session.sqlite` (sessions, messages, long-term memory with FTS and vector index), `workflow.sqlite` (task tracking) and `eventbus.sqlite` (event, delivery and offset state). Table definitions are in `db_02`. The files are separated because RAG indexing and conversation state have different access patterns (`rag.sqlite` writes heavily during ingestion and reads during query; `session.sqlite` appends heavily during conversations); separation avoids WAL contention.

**Import Boundaries:** For complete import rules, see [db_04 section 1a](db_04_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries). Callers should always import from `db.store` and must not import directly from internal modules.

---

## 3. `DbConfig` (`db/config.py`)

`DbConfig` is the frozen configuration for the DB files (field list and validation: `shared_02_03_types_and_protocols-reference.md`). The `workflow` and `eventbus` paths fall back to code-level defaults when absent from `agent.toml`. DB files themselves are created on first open; parent directories must exist. The embedding dimension is a fixed code constant (`scripts/db/store_protocols.py::get_embedding_dims()`), not a `DbConfig` field. `build_db_config()` builds it from `agent.toml`.

---

## 4. DB File Structure and `SQLiteHelper`

`SQLiteHelper` manages connection lifecycle. Its `target` (`DbTarget`: `RAG`/`SESSION`/`WORKFLOW`/`EVENTBUS`, enum member or same-named string) selects the DB file. `DbTarget.EVENTBUS` is used only by `create_schema()` for Event Bus DDL; the Event Bus service opens its own connection through `open_db()` in `scripts/eventbus/db_conn.py` and does not use `SQLiteHelper`.

Each `open()` call loads the `sqlite-vec` extension when enabled (then `enable_load_extension(False)`), sets `PRAGMA journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout` (from `agent.toml::sqlite_busy_timeout_ms`) and, when `write_mode=True`, `foreign_keys=ON`. The extension is loaded by default for the `rag` and `session` targets (the targets that own vec0 tables), and only when `sqlite_vec_so` is non-empty; `workflow` and `eventbus` do not load it. When `db_path` is passed explicitly (see 4a), the default follows whether `sqlite_vec_so` is non-empty.

### 4a. `SQLiteHelper` constructor `db_path` override

`SQLiteHelper.__init__()` can accept a `db_path` keyword argument. If provided, it completely bypasses `build_db_config()` (i.e., loading `agent.toml`) and uses the provided `db_path` / `sqlite_vec_so` / `sqlite_timeout` / `sqlite_busy_timeout_ms` directly. This provides a path for callers like MCP servers that want to specify a DB path independently of `agent.toml`. If `db_path` is not specified, paths are resolved from the results of `build_db_config()` according to the `target` as before.

### 4b. Additional options for `open()`

`open()` accepts these options in addition to `write_mode` / `row_factory`:

- `load_vec` — `None` follows the instance default described above; an explicit `True` or `False` overrides it. The extension is loaded only when the resolved flag is `True` and `sqlite_vec_so` is non-empty. When `sqlite_vec_so` is empty the extension is not loaded even if the resolved flag is `True`, so a later access to a vec0 table fails with `sqlite3.OperationalError` instead of being skipped; a load error raises at open time. This applies to both `rag` and `session`.
- `reuse_connection` — when `True` and a connection already exists, reconnection is skipped and `__exit__` does not close it.

### 4c. Transaction helpers

`SQLiteHelper` provides context managers `begin_immediate()` / `begin_exclusive()` that wrap `BEGIN IMMEDIATE` / `BEGIN EXCLUSIVE`. Both attempt a `ROLLBACK` upon normal exceptions (swallowing `sqlite3.OperationalError`) and re-raise the original exception. They do not catch `BaseException` (e.g., `KeyboardInterrupt`/`SystemExit`). `begin_exclusive()` is intended specifically for operations requiring exclusive locks, such as `VACUUM` or schema changes.

---

## Keywords

- shared
- db
- dbconfig
- sqlitehelper
- layer-structure
