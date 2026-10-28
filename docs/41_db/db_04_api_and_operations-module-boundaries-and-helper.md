---
title: "DB API and Operations — Module Boundaries and Helper"
area: shared
tags:
  - shared
  - db
  - module-boundaries
related:
  - db_05_api_and_operations-protocol-and-backend.md
  - db_06_api_and_operations-maintenance-and-rotation.md
  - db_01_architecture_and_schema-overview-and-config.md
---
# DB API and Operations

- Schema → [db_01_architecture_and_schema-overview-and-config.md](db_01_architecture_and_schema-overview-and-config.md)

## 1. Purpose

To document the `SQLiteHelper` behavior contract, the protocol groups and implementations in `db/store.py`, memory-related table operations, maintenance functions, recovery procedures in case of corruption, error handling, and operational verification plans.

---

## 1a. DB Store Module Boundaries

The DB store layer is split into modules with clear import boundaries. `db/store.py` is the public API surface — it re-exports protocols and embedding helpers; callers should import from here to maintain a stable contract. `db/store_protocols.py` is the extension point — containing protocol definitions for storage contracts; implementers import this, while callers rarely use it directly. `db/store_impl.py` is the SQLite implementation layer — providing concrete implementations of the protocols; do not import directly unless intentionally working at the protocol/implementation level. **Rule:** Callers must always import from `db.store`; direct imports from `store_protocols.py` or `store_impl.py` are discouraged and should only be used for intentional protocol/implementation development.

### How to extend the DB store

Add the `Protocol` to `db/store_protocols.py`, implement it in `db/store_impl.py`, and export it from `db/store.py`. Caller code imports from `db.store` only; importing `store_protocols.py` or `store_impl.py` directly breaks the abstraction.

---

## 2. `SQLiteHelper` (`db/helper.py`)

`SQLiteHelper` resolves its DB file from `target` (`DbTarget` member or string; an invalid target raises `ValueError`). Path and settings come from `build_db_config()` unless `db_path` is passed explicitly, in which case `build_db_config()` is bypassed entirely and `sqlite_vec_so` / `sqlite_timeout` / `sqlite_busy_timeout_ms` are taken from the arguments, so MCP servers can self-contain DB configuration without reading `agent.toml`. Connection options (`write_mode`, `row_factory`, `load_vec`, `reuse_connection`, `check_same_thread`) and the PRAGMAs applied on every open are specified in [db_01 section 4](db_01_architecture_and_schema-overview-and-config.md#4-db-file-structure-and-sqlitehelper); the `load_vec` default depends on the target and `sqlite_vec_so`. `check_same_thread` can be set per instance (`__init__`) and per open (`open()`); an explicit value passed to `open()` also carries over as the instance setting for subsequent opens.

### Threading boundary

- Default rule: a helper connection is opened, used, and closed on one thread
  (connection-per-call). `check_same_thread=True` enforcement stays in force
  for all non-turn paths; touching a connection from a thread other than its
  creating thread raises `sqlite3.ProgrammingError`.
- Turn-boundary writes (`agent/turn_persistence.py` delegating to
  `agent/session_message_repo.py`) execute on worker threads via
  `asyncio.to_thread`. Each repository call opens its own short-lived
  connection and uses it inside the same worker thread; sequential awaits in
  the boundary preserve within-turn write ordering. The event loop never
  executes turn-path SQLite calls.
- Single authorized exception: a connection intentionally reused across
  threads must be opened with `check_same_thread=False` and used
  sequentially only, never concurrently. No turn-boundary connection is reused
  across threads today; the per-call pattern inside the worker thread is what
  ships.

The session persistence boundary these rules apply to is described in
[agent_04_03](../23_agent/agent_04_03_state-and-persistence-platform-databases.md).

Error semantics:
- `execute()` raises `RuntimeError` when no connection is open and `ValueError` for an empty `sql`.
- `executescript()` commits pending transactions before execution.
- `commit()` logs `ERROR` and re-raises `sqlite3.OperationalError`.
- `close()` is idempotent; close errors are logged as `WARNING` and not raised.
- Context-manager methods such as `begin_immediate()` provide atomic transaction control.

---

## Keywords

- shared
- db
- module-boundaries
