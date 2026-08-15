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

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 1. 目的

`db/` レイヤー構造、DB ファイル構成、`DbConfig`、`SQLiteHelper` の接続動作、
WAL/FTS5/sqlite-vec の設定、全テーブルスキーマ、およびスキーマ初期化方式について
記述する。

---

## 2. DB レイヤー全体構造

db/ contains helper.py (connection lifecycle, PRAGMA, vec extension), create_schema.py (DDL creation idempotent for rag/session/workflow/eventbus schemas), store_protocols.py (MemoryDeleteStore, VectorStore protocol definitions), store_impl.py (SQLite implementations of store protocols), store.py (public re-export layer for db.store imports), maintenance.py (WAL checkpoint, VACUUM, purge, rotate, recover).

Four DB files exist: rag.sqlite (agent.toml::rag_db_path, documents/chunks/chunks_fts/chunks_vec tables), session.sqlite (agent.toml::session_db_path, sessions/messages/memories/memories_fts/memories_vec/memory_links/session_diagnostics tables), workflow.sqlite (agent.toml::workflow_db_path, tasks/attempts/processed_events/artifacts/approvals tables), eventbus.sqlite (agent.toml::eventbus_db_path, events table). DB files separated because RAG indexing and conversation state have different access patterns; rag.sqlite writes heavily during ingestion and reads during query; session.sqlite appends heavily during conversations; separation avoids WAL contention.

**なぜ DB ファイルを分離するのか。** RAG インデキシングと会話状態はアクセスパターンが異なる。
`rag.sqlite` は取り込み時に書き込みが多く、クエリ時に読み込みが多い。
`session.sqlite` は会話中に追記が多い。分離することで WAL の競合を避けられる。

**インポート境界:** 完全なインポートルールは [90_shared_05 §1a](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries) を参照。呼び出し側は常に `db.store` からインポートすべきであり、内部モジュールから直接インポートしてはならない。

---

## 3. `DbConfig` (`db/config.py`)

Frozen dataclass for DB configuration. rag_db_path (path to rag.sqlite), session_db_path (path to session.sqlite), workflow_db_path (default /opt/llm/db/workflow.sqlite), eventbus_db_path (default /opt/llm/db/eventbus.sqlite), sqlite_vec_so (path to vec0.so, empty = vec extension not needed), sqlite_timeout (sqlite3.connect() timeout seconds >= 1), sqlite_busy_timeout_ms (PRAGMA busy_timeout ms default 30000), embedding_dims (embedding vector dimension default 384). __post_init__ validates all path fields non-empty, sqlite_timeout >= 1, embedding_dims >= 1, parent directories exist (DB files themselves created on first open). No embed_url field exists. Built by build_db_config() in db/config.py. agent.toml loaded via ConfigLoader().load_all() (_BASE_CONFIG_FILES index 0 included).

---

## 4. DB ファイル構造と `SQLiteHelper`

`SQLiteHelper` manages connection lifecycle. Constructor accepts target parameter resolving to specific DB file: DbTarget.RAG → rag.sqlite, DbTarget.SESSION → session.sqlite, DbTarget.WORKFLOW → workflow.sqlite, DbTarget.EVENTBUS → eventbus.sqlite (Event Bus DDL only; no runtime integration yet). DbTarget is StrEnum defined in db/helper.py (RAG/SESSION/WORKFLOW/EVENTBUS); target parameter accepts enum member or same-named string literal. Connection setup per open() call: load sqlite-vec extension (rag target only), then enable_load_extension(False); set PRAGMA journal_mode=WAL; set PRAGMA synchronous=NORMAL; set PRAGMA busy_timeout=30000 (from agent.toml::sqlite_busy_timeout_ms); set PRAGMA foreign_keys=ON (when write_mode=True). sqlite-vec loaded only when target='rag'; session and workflow targets do not load vec.

### 4a. `SQLiteHelper` コンストラクタの `db_path` オーバーライド (Explicit in code)

`SQLiteHelper.__init__()` は `db_path` キーワード引数を受け取ることができる。指定された場合、`build_db_config()`（＝`agent.toml` 読み込み）を完全にバイパスし、渡された `db_path` / `sqlite_vec_so` / `sqlite_timeout` / `sqlite_busy_timeout_ms` をそのまま使用する（`db/helper.py` `SQLiteHelper.__init__`）。これは MCP サーバーなど、`agent.toml` に依存せず自己完結的に DB パスを指定したい呼び出し元向けの経路である。`db_path` を指定しない場合は従来どおり `target` に応じて `build_db_config()` の結果からパスを解決する。

### 4b. `open()` の追加オプション (Explicit in code)

`open()` は本文記載の `write_mode` / `row_factory` に加えて以下を受け取る。

- `load_vec: bool | None = None` — `None` の場合はターゲットごとのデフォルト（rag のみ True）に従う。明示的に `True`/`False` を渡すとデフォルトを上書きできる。
- `reuse_connection: bool = False` — `True` かつ既存の `self.conn` がある場合は再接続をスキップする。この場合 `__exit__` でも `close()` を呼ばない（コネクションの使い回しを許可する）。

### 4c. トランザクションヘルパー (Explicit in code)

`SQLiteHelper` は `BEGIN IMMEDIATE` / `BEGIN EXCLUSIVE` をラップするコンテキストマネージャ `begin_immediate()` / `begin_exclusive()` を提供する。いずれも通常の例外発生時は `ROLLBACK` を試み（`sqlite3.OperationalError` は握りつぶす）、元の例外を再送出する。`BaseException`（`KeyboardInterrupt`/`SystemExit`）は捕捉しない。`begin_exclusive()` は VACUUM やスキーマ変更など、排他ロックが必要な操作専用（`db/helper.py` docstring より）。

---
