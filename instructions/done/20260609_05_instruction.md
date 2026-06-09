# 改修計画要約

## 1. 全体改修方針

- DB 層全体を 設定管理, 接続管理, スキーマ管理, 永続化 API, 保守運用 に再分離し、責務が混在した現行構造を整理する。特に `DbConfig` が存在するにもかかわらず `helper.py`、`store.py`、`maintenance.py` が個別に `ConfigLoader` を参照している状態を解消する。
- 後方互換性維持のために残された実装は削除する。具体的には、旧実装への無改修適合前提、旧スキーマ共存前提、DB エラー時の silent fallback、`IF NOT EXISTS` と safe migration error による暫定共存を廃止する。
- 設定は `config.py` の `DbConfig` を唯一の入口とし、各モジュールの `ConfigLoader` 直読込を廃止する。設定値の真実の所在を 1 か所に統一する。
- `SQLiteHelper` は接続管理専用に限定し、class-level 状態や private 属性を利用した周辺モジュールからの依存を解消する。
- スキーマ管理は `create_schema.py` の「初期化 + 互換 migration 混在」から、versioned migration 前提の明示的管理へ移行する。
- 永続化 API は「失敗しても黙って継続」ではなく、失敗を構造化して呼び出し元へ返す 方針へ統一する。
- transaction/commit 境界はストアごとの暗黙実装ではなく、統一した単位で管理する。現状は `store.py` と `maintenance.py` で commit 方針が不揃いである。

## 2. ファイルごとの改修内容

### 2.1 `helper.py`

- `ConfigLoader` を用いた class-level lazy 初期化を廃止し、`DbConfig` を明示注入する構成へ変更する。`_RAG_PATH`、`_SESSION_PATH`、`SQLITE_VEC_SO`、`_config_loaded` を用いた共有状態をなくす。
- `SQLiteHelper` の責務を接続管理に限定し、`health_check()`、`checkpoint()`、`vacuum()` などの保守系操作は maintenance 層へ移管する。
- `open()` で常に sqlite-vec extension を load する設計を見直し、RAG 用など必要なケースに限定する。
- `execute()`、`executemany()`、`fetchall()` などの SQL 実行窓口は、接続 helper に残す範囲を最小化し、repository/store 層との境界を整理する。
- `assert self.conn is not None` に依存した前提チェックは、専用例外ベースへ変更する。

### 2.2 `config.py`

- `DbConfig` を DB 層唯一の設定入口として再定義し、他モジュールからの `ConfigLoader` 直接利用を廃止する。
- `__post_init__()` の DB ファイル実在チェックは、新規 DB 作成フローと整合するように見直し、ファイル実在必須ではなく親ディレクトリや書込可能性の検証へ変更する。
- `sqlite_busy_timeout_ms`、archive 先、retention、checkpoint mode、`embedding_dims` など DB 運用関連設定を `DbConfig` へ集約する。
- パス検証は `exists()` のみでなく、ファイル/ディレクトリ種別も含めて厳密化する。

### 2.3 `store.py`

- `VectorStore` / `DocumentStore` / `SessionStore` / `MemoryDeleteStore` の設計は維持しつつ、既存 `RagRepository` が無改修で適合することを前提にしない 形へ再定義する。必要であれば adapter を別途実装する。
- `get_embedding_dims()` / `get_embedding_bytes()` / `validate_embedding_blob()` の設定依存を `DbConfig` または schema metadata に統合し、`ConfigLoader` 直読込を廃止する。
- `SQLiteDocumentStore.doc_upsert()` は read-then-update/insert から UPSERT ベースへ変更し、競合や整合性の観点を改善する。
- `SQLiteSessionStore` は `messages.tool_call_id` を扱える API へ拡張し、`create_schema.py` の schema と整合させる。
- `SQLiteMemoryDeleteStore` を含む各ストアの commit 方針を統一し、Unit of Work または transaction coordinator に集約する。
- 戻り値の `dict[str, Any]` を typed DTO / `TypedDict` に置換し、構造を明示する。

### 2.4 `tool_results.py`

- `ToolResultStore` の DB エラー時 fallback を廃止し、失敗を `None` や空配列に潰さず、呼び出し元で判定可能な結果型または例外へ変更する。
- `SQLiteHelper("session").open(...)` をメソッド内で毎回 new する構成をやめ、接続または transaction を外部注入する。
- `get()` / `list_recent()` の戻り値は型付き DTO に変更し、「データなし」と「DB 異常」を区別可能にする。
- `list_recent()` の返却順序は SQL か API 契約のどちらかに明示固定し、Python 側 `reversed()` 依存をなくす。
- `is_error` の SQLite 向け整数表現は store 内部に閉じ込め、上位 API では bool を維持する。

### 2.5 `maintenance.py`

- `SQLiteHelper._ensure_config()` や `_RAG_PATH` / `_SESSION_PATH` といった private/class-level 状態への依存を廃止し、`DbConfig` または公開 API 経由で DB パスと接続情報を扱う。
- `_run_integrity_check(db_path)` はシグネチャどおり指定パスを検査する汎用関数へ修正し、現状の `SQLiteHelper("rag").open()` 固定実装を改める。
- WAL checkpoint、VACUUM、session retention、memory prune、rotation、corruption recovery を DB 種別別・責務別に整理し、保守 API を再編する。
- `purge_old_sessions()` と `prune_old_memories()` の transaction/commit 境界を統一する。
- archive 処理は単純 `copy2()` だけでなく、checkpoint/整合性確保と一体で扱う構成へ見直す。
- `RecoveryResult.action` や各メンテナンス戻り値を Enum / DTO ベースに統一する。

### 2.6 `create_schema.py`

- schema 初期化と migration を分離し、`create_schema.py` は versioned migration 前提へ再設計する。`IF NOT EXISTS` と `_SAFE_MIGRATION_ERRORS` に依存した旧状態共存はやめる。
- `memories_vec` の次元定義を `embedding_dims` に統一し、migration に残る固定 `float[384]` を廃止する。
- `messages.tool_call_id` などの migration 検証失敗時は `logger.error()` のみで継続せず、明示的に fail させる。
- `schema_version` を実際の migration 管理に接続し、適用済み version を記録・検証する仕組みへ強化する。
- DDL 直書き主体の方式は migration artifact 管理へ移行し、変更履歴を追跡可能にする。
- `Logger(__name__, "/opt/llm/logs/create_schema.log")` の固定パス依存を設定化する。

## 3. 削除対象

- `helper.py` の `_config_loaded` を前提とした class-level 設定キャッシュ。
- `maintenance.py` からの `SQLiteHelper._ensure_config()`、`_RAG_PATH`、`_SESSION_PATH` への private 依存。
- `store.py` に記載された「既存 `RagRepository` が無改修で Protocol に適合する」という後方互換前提。
- `SQLiteMemoryDeleteStore` の `memories_vec` 削除失敗を non-fatal とする旧スキーマ共存前提。
- `tool_results.py` の「DB エラーでも REPL 継続」を目的とした silent fallback。
- `create_schema.py` の `IF NOT EXISTS`、safe migration error スキップ、固定 `384` による旧 migration 互換。
- DB 層各所に分散した `ConfigLoader` 直接読込。
