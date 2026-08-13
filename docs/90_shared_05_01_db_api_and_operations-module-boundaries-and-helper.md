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
  - 90_shared_05_02_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
  - 90_shared_05_04_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- スキーマ → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 1. 目的

`SQLiteHelper` API、`db/store.py` のプロトコルグループと実装、
メモリ関連のテーブル操作、メンテナンス機能、破損時の
リカバリ、エラーハンドリング、運用上の検証計画を文書化する。

---

## 1a. DB Store モジュールの境界

### 1a. DB Store module boundaries

DB store layer split into three modules with clear import boundaries. db/store.py is public API surface — re-exports protocols and embedding helpers; callers should import from here for stable contract. db/store_protocols.py is extension point — protocol definitions for storage contracts; implementers import this, callers rarely use directly. db/store_impl.py is SQLite implementation layer — concrete implementations of protocols; do not import directly except when intentionally working at protocol/implementation level. Rule: callers always import from db.store; direct imports from store_protocols.py or store_impl.py discouraged, only for intentional protocol/implementation work.

### DB store を拡張する方法

1. `db/store_protocols.py` に新しい Protocol クラスを追加する（例: `class NewStorageProtocol(Protocol): ...`）
2. `db/store_impl.py` でプロトコルを実装する（例: `class NewStorageImpl(NewStorageProtocol): ...`）
3. `db/store.py` から export する — 呼び出し側は内部モジュールからではなく `db.store` からインポートする

**アンチパターン:** 呼び出し側コードで `store_protocols.py` や `store_impl.py` から直接インポートしないこと。

```python
# BAD — direct import of internal module
from db.store_impl import NewStorageImpl  # breaks abstraction

# GOOD — import from public API
from db.store import NewStorageProtocol, NewStorageImpl  # stable contract
```

---

## 2. `SQLiteHelper` (`db/helper.py`)

SQLiteHelper(target='rag', *, db_path=None, sqlite_vec_so='', sqlite_timeout=30, sqlite_busy_timeout_ms=30000). DbTarget.RAG/SESSION/WORKFLOW/EVENTBUS or string literal ('rag'→rag.sqlite, 'session'→session.sqlite, 'workflow'→workflow.sqlite, 'eventbus'→eventbus.sqlite); invalid target raises ValueError. build_db_config() called within __init__() to resolve all paths and settings; if db_path explicitly passed, build_db_config() fully bypassed and specified db_path/sqlite_vec_so/sqlite_timeout/sqlite_busy_timeout_ms used directly (allows MCP servers etc. to self-contain DB config without reading agent.toml). DB_PATH property provides read-only access to resolved DB path for instance. open(*, write_mode=False, row_factory=False, load_vec=None, reuse_connection=False) returns self for chaining, sets self.conn. write_mode=True adds PRAGMA foreign_keys=ON; row_factory=True sets conn.row_factory = sqlite3.Row (column-name access); load_vec=None uses target default (rag→True, session/workflow→False); load_vec=True forces sqlite-vec extension load; load_vec=False skips vec extension; reuse_connection=True skips reconnect if existing self.conn available, also skips close() in __exit__ (allows connection reuse). Always applied: vec load (if valid), WAL, NORMAL sync, busy_timeout. For reuse_connection details see 90_shared_04_01 §4b. execute(sql, params=()) → sqlite3.Cursor: params tuple (positional ?) or dict (named :name); RuntimeError if conn None, ValueError if sql empty. executescript(sql_script) → None: executes multiple SQL statements, commits pending transactions before execution. executemany(sql, params_seq) → sqlite3.Cursor: batch INSERT/UPDATE, params_seq list[tuple[Any,...]]. fetchall(sql, params=()) → list[Any]: combine execute + fetchall. commit() → None: logs ERROR then re-raises sqlite3.OperationalError. close() → None: idempotent, WARNING logged on close error but no exception thrown. begin_immediate() → @contextmanager: BEGIN IMMEDIATE...COMMIT, auto ROLLBACK on Exception (not BaseException). begin_exclusive() → @contextmanager: BEGIN EXCLUSIVE...COMMIT, VACUUM/DDL only, auto ROLLBACK on Exception (not BaseException). health_check() → DbHealthMetrics: PRAGMA quick_check, returns {journal_mode, integrity, page_count, page_size, freelist_count, db_size_bytes}. checkpoint(mode='TRUNCATE') → WalCheckpointCounts: modes PASSIVE/FULL/RESTART/TRUNCATE, invalid mode raises ValueError. vacuum() → None: rebuilds DB in-place, requires ~2x DB size free disk space, call outside transaction. apply_connection_pragmas(): module-level function exposing WAL/synchronous=NORMAL/busy_timeout/foreign_keys pragma application logic that SQLiteHelper.open() uses internally, allowing raw sqlite3.Connection to receive same pragmas without going through SQLiteHelper. Called directly by mcp_servers/mdq/db_schema.py, mcp_servers/mdq/service.py, mcp_servers/mdq/health_check.py, eventbus/db.py.

---
