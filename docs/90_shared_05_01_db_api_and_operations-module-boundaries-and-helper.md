# DB API and Operations

- Schema $\rightarrow$ [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 1. Purpose

To document the `SQLiteHelper` API, the protocol groups and implementations in `db/store.py`, memory-related table operations, maintenance functions, recovery procedures in case of corruption, error handling, and operational verification plans.

---

## 1a. DB Store Module Boundaries

### 1a. DB Store module boundaries

The DB store layer is split into three modules with clear import boundaries. `db/store.py` is the public API surface — it re-exports protocols and embedding helpers; callers should import from here to maintain a stable contract. `db/store_protocols.py` is the extension point — containing protocol definitions for storage contracts; implementers import this, while callers rarely use it directly. `db/store_impl.py` is the SQLite implementation layer — providing concrete implementations of the protocols; do not import directly unless intentionally working at the protocol/implementation level. **Rule:** Callers must always import from `db.store`; direct imports from `store_protocols.py` or `store_impl.py` are discouraged and should only be used for intentional protocol/implementation development.

### How to extend the DB store

1. Add a new `Protocol` class to `db/store_protocols.py` (e.g., `class NewStorageProtocol(Protocol): ...`).
2. Implement the protocol in `db/store_impl.py` (e.g., `class NewStorageImpl(NewStorageProtocol): ...`).
3. Export it from `db/store.py` — callers should import from `db.store` rather than internal modules.

**Anti-pattern:** Do not import directly from `store_protocols.py` or `store_impl.py` in caller code.

```python
# BAD — direct import of internal module
from db.store_impl import NewStorageImpl  # breaks abstraction

# GOOD — import from public API
from db.store import NewStorageProtocol, NewStorageImpl  # stable contract
```

---

## 2. `SQLiteHelper` (`db/helper.py`)

`SQLiteHelper(target='rag', *, db_path=None, sqlite_vec_so='', sqlite_timeout=30, sqlite_busy_timeout_ms=30000)`. Targets include `DbTarget.RAG`/`SESSION`/`WORKFLOW`/`EVENTBUS` or string literals (`'rag'` $\rightarrow$ `rag.sqlite`, `'session'` $\rightarrow$ `session.sqlite`, `'workflow'` $\rightarrow$ `workflow.sqlite`, `'eventbus'` $\rightarrow$ `eventbus.sqlite`); invalid targets raise `ValueError`. `build_db_config()` is called within `__init__()` to resolve all paths and settings; if `db_path` is explicitly passed, `build_db_config()` is fully bypassed and the specified `db_path`/`sqlite_vec_so`/`sqlite_timeout`/`sqlite_busy_timeout_ms` are used directly (allowing MCP servers, etc., to self-contain DB configuration without reading `agent.toml`). The `DB_PATH` property provides read-only access to the resolved DB path for the instance. `open(*, write_mode=False, row_factory=False, load_vec=None, reuse_connection=False)` returns `self` for chaining and sets `self.conn`. `write_mode=True` enables `PRAGMA foreign_keys=ON`; `row_factory=True` sets `conn.row_factory = sqlite3.Row` (enabling column-name access); `load_vec=None` uses the target default (`rag` $\rightarrow$ `True`, `session`/`workflow` $\rightarrow$ `False`); `load_vec=True` forces the `sqlite-vec` extension to load; `load_vec=False` skips the extension; `reuse_connection=True` skips reconnection if an existing `self.conn` is available and skips `close()` in `__exit__` (allowing connection reuse). Always applied: `vec` loading (if valid), `WAL` mode, `NORMAL` sync, and `busy_timeout`. For more on `reuse_connection`, see [90_shared_04_01 §4b]. `execute(sql, params=())` $\rightarrow$ `sqlite3.Cursor`: supports parameter tuples (`?`) or dictionaries (`:name`); raises `RuntimeError` if `conn` is `None`, or `ValueError` if `sql` is empty. `executescript(sql_script)` $\rightarrow$ `None`: executes multiple SQL statements and commits pending transactions before execution. `executemany(sql, params_seq)` $\rightarrow$ `sqlite3.Cursor`: performs batch `INSERT`/`UPDATE` using `params_seq` as a list of tuples. `fetchall(sql, params=())` $\rightarrow$ `list[Any]`: combines `execute` and `fetchall`. `commit()` $\rightarrow$ `None`: logs `ERROR` then re-raises `sqlite3.OperationalError`. `close()` $\rightarrow$ `None`: idempotent; a `WARNING` is logged on close errors, but no exception is thrown. `@contextmanager` methods like `begin_immediate()` provide atomic transaction control.

---
