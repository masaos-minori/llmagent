---
title: "DB API and Operations - Module Boundaries and Helper"
category: shared
tags:
  - shared
  - db
  - sqlitehelper
  - module-boundaries
  - store-protocols
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_db_api_and_operations-maintenance-and-rotation.md
  - 90_shared_05_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- Schema → [90_shared_04_db_architecture_and_schema-overview-and-config.md](90_shared_04_db_architecture_and_schema-overview-and-config.md)

## 1. Purpose

Documents the `SQLiteHelper` API, `db/store.py` protocol groups and implementations,
memory-related table operations, maintenance functions, corruption
recovery, error handling, and the operational verification plan.

---

## 1a. DB Store Module Boundaries

The DB store layer is split into three modules with clear import boundaries:

| Module | Role | Import boundary |
|---|---|---|
| `db/store.py` | **Public API surface** — re-exports protocols and embedding helpers | Callers should import from here. Stable contract. |
| `db/store_protocols.py` | **Extension point** — Protocol definitions for storage contracts | Implementations import this; callers rarely need to. |
| `db/store_impl.py` | **SQLite implementation layer** — concrete implementations of protocols | Never import directly unless intentionally bypassing the protocol abstraction. |

**Rule:** Callers should always import from `db.store`. Direct imports from `store_protocols.py` or `store_impl.py` are discouraged and should only be used when intentionally working at the protocol/implementation level.

### How to extend the DB store

1. Add a new Protocol class to `db/store_protocols.py` (e.g., `class NewStorageProtocol(Protocol): ...`)
2. Implement the protocol in `db/store_impl.py` (e.g., `class NewStorageImpl(NewStorageProtocol): ...`)
3. Export from `db/store.py` — callers import from `db.store`, not from internal modules

**Anti-pattern:** Never import directly from `store_protocols.py` or `store_impl.py` in caller code:

```python
# BAD — direct import of internal module
from db.store_impl import NewStorageImpl  # breaks abstraction

# GOOD — import from public API
from db.store import NewStorageProtocol, NewStorageImpl  # stable contract
```

---

## 2. `SQLiteHelper` (`db/helper.py`)

### Constructor

```python
SQLiteHelper(target: DbTarget | str = "rag")
# DbTarget.RAG, DbTarget.SESSION, DbTarget.WORKFLOW, or string literal
# "rag" → rag.sqlite  |  "session" → session.sqlite  |  "workflow" → workflow.sqlite
# Invalid target → ValueError
```

`build_db_config()` is called in `__init__()` to resolve all paths and settings.

### `open()` method

```python
def open(
    self,
    *,
    write_mode: bool = False,
    row_factory: bool = False,
    load_vec: bool | None = None,
) -> "SQLiteHelper"
```

Returns `self` for chaining. Sets `self.conn`.

| Argument | Effect |
|---|---|
| `write_mode=True` | Adds `PRAGMA foreign_keys=ON` |
| `row_factory=True` | Sets `conn.row_factory = sqlite3.Row` (column name access) |
| `load_vec=None` | Uses target default: `rag` → True; `session`/`workflow` → False |
| `load_vec=True` | Force load sqlite-vec extension |
| `load_vec=False` | Skip vec extension |

Always applies: vec load (if enabled), WAL, NORMAL sync, busy_timeout.

### Core methods

| Method | Signature | Notes |
|---|---|---|
| `execute(sql, params=())` | `-> sqlite3.Cursor` | `params`: tuple (positional `?`) or dict (named `:name`). `RuntimeError` if conn None; `ValueError` if sql empty |
| `executemany(sql, params_seq)` | `-> sqlite3.Cursor` | Batch INSERT/UPDATE. `params_seq: list[tuple[Any, ...]]` |
| `fetchall(sql, params=())` | `-> list[Any]` | `execute + fetchall` combined |
| `commit()` | `-> None` | Logs ERROR on `sqlite3.OperationalError` then re-raises |
| `close()` | `-> None` | Idempotent; logs WARNING on close error but does not raise |
| `begin_immediate()` | `@contextmanager` | `BEGIN IMMEDIATE ... COMMIT`; auto-ROLLBACK on `Exception` (not `BaseException`) |
| `begin_exclusive()` | `@contextmanager` | `BEGIN EXCLUSIVE ... COMMIT`; for VACUUM/DDL only; auto-ROLLBACK on `Exception` (not `BaseException`) |
| `health_check()` | `-> DbHealthMetrics` | `PRAGMA quick_check`; returns `{journal_mode, integrity, page_count, page_size, freelist_count, db_size_bytes}` |
| `checkpoint(mode="TRUNCATE")` | `-> WalCheckpointCounts` | Modes: PASSIVE/FULL/RESTART/TRUNCATE. Invalid mode → `ValueError` |
| `vacuum()` | `-> None` | In-place DB rebuild; requires ~2× DB size free disk; call outside transaction |

### Typical usage patterns

```python
# Read-only query
with SQLiteHelper("rag").open(row_factory=True) as db:
    rows = db.fetchall("SELECT url, title FROM documents WHERE lang = :lang", {"lang": "ja"})

# Write with transaction
with SQLiteHelper("session").open(write_mode=True) as db:
    db.execute("INSERT INTO sessions DEFAULT VALUES")
    db.commit()

# Atomic multi-statement write
with SQLiteHelper("rag").open(write_mode=True) as db:
    with db.begin_immediate():
        db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # COMMIT auto on exit; ROLLBACK on exception
```

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_db_api_and_operations-protocol-and-backend.md`
- `90_shared_05_db_api_and_operations-maintenance-and-rotation.md`
- `90_shared_05_db_api_and_operations-recovery-and-reference.md`

## Keywords

DB store module boundaries
SQLiteHelper
db/helper.py
