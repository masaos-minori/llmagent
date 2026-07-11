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

DB ファイルは4つ存在する。

| DB | デフォルトパス | テーブル |
|---|---|---|
| `rag.sqlite` | `agent.toml::rag_db_path` | `documents`, `chunks`, `chunks_fts`, `chunks_vec` |
| `session.sqlite` | `agent.toml::session_db_path` | `sessions`, `messages`, `memories`, `memories_fts`, `memories_vec`, `memory_links`, `session_diagnostics` |
| `workflow.sqlite` | `agent.toml::workflow_db_path` | `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals` |
| `eventbus.sqlite` | `agent.toml::eventbus_db_path` | `events` |

**なぜ DB ファイルを分離するのか。** RAG インデキシングと会話状態はアクセスパターンが異なる。
`rag.sqlite` は取り込み時に書き込みが多く、クエリ時に読み込みが多い。
`session.sqlite` は会話中に追記が多い。分離することで WAL の競合を避けられる。

**インポート境界:** 完全なインポートルールは [90_shared_05 §1a](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries) を参照。呼び出し側は常に `db.store` からインポートすべきであり、内部モジュールから直接インポートしてはならない。

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

- `__post_init__` は、すべてのパスフィールドが空でないこと、`sqlite_timeout >= 1` であること、`embedding_dims >= 1` であること、および各 DB パスの親ディレクトリが存在すること（DB ファイル自体は SQLite が初回オープン時に作成する）を検証する
- `embed_url` フィールドは `DbConfig` に存在しない
- `db/config.py` の `build_db_config()` によって構築される
- `agent.toml` は `ConfigLoader().load_all()` 経由でロードされる（`_BASE_CONFIG_FILES` のインデックス0に含まれる）— 完全な所有関係表は [90_shared_03](90_shared_03_01_runtime_and_execution-config-and-logging.md) §2a Config Ownership を参照

---

## 4. DB ファイル構造と `SQLiteHelper`

`SQLiteHelper` は接続のライフサイクルを管理する。コンストラクタは初期化時に設定を解決する。

```python
SQLiteHelper(target: DbTarget | str = "rag")
# DbTarget.RAG, DbTarget.SESSION, DbTarget.WORKFLOW, or string literal
# "rag"      → rag.sqlite
# "session"  → session.sqlite
# "workflow" → workflow.sqlite
# "eventbus" → eventbus.sqlite (Event Bus DDL only; no runtime integration yet)
```

**注記:** Event Bus のランタイム（publisher/subscriber/dispatcher/DLQ worker）は本クリーンアップの対象範囲外である。今後 Event Bus の書き込み側を実装する際は、ISO-8601 UTC の Z サフィックス付きタイムスタンプを使用しなければならない。

**接続セットアップ（`open()` 呼び出しごと）:**
1. sqlite-vec 拡張をロード（rag ターゲットのみ）。その後 `enable_load_extension(False)`
2. `PRAGMA journal_mode=WAL`
3. `PRAGMA synchronous=NORMAL`
4. `PRAGMA busy_timeout=30000`（`agent.toml::sqlite_busy_timeout_ms` から取得）
5. `PRAGMA foreign_keys=ON`（`write_mode=True` の場合）

sqlite-vec は `target="rag"` の場合のみロードされる。session および workflow ターゲットでは vec はロードされない。

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
