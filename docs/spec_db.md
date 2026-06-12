# データベース層仕様

## 1. 目的

エージェントシステムの永続データ（RAG インデックス・会話セッション・メモリ・ツール結果）を SQLite で管理し、型安全なアクセスインターフェースを提供する。sqlite-vec 拡張によるベクター検索と FTS5 による全文検索を統合する。

---

## 2. スコープ

- **対象コンポーネント:** `db/` 配下の全モジュール（helper.py、create_schema.py、store.py、maintenance.py、tool_results.py）
- **DB ファイル:** `rag.sqlite`（RAG インデックス）、`session.sqlite`（会話・メモリ）
- **対象外:** RAG クエリ/インジェストロジック（`rag/`）、MCP サーバー、エージェント REPL

---

## 3. 背景

エージェントの全永続データを単一ノード SQLite で管理する。RAG インデックス用と会話セッション用でデータベースファイルを分離し、それぞれに FTS5（全文検索）と sqlite-vec（ベクター類似度検索）を統合する。WAL モードと `busy_timeout` で並行アクセスを許容する。

---

## 4. 前提条件

1. SQLite 3.35 以上がインストールされていること。
2. sqlite-vec 拡張（`/opt/llm/sqlite-vec/vec0.so`）がロード可能であること。
3. DB ファイルパス（`rag_db_path`、`session_db_path`）が `common.toml` で設定されていること。
4. `db/create_schema.py` でスキーマ初期化が完了していること。

---

## 5. 制約

| 制約 | 内容 |
|---|---|
| 単一ノード | SQLite の分散・レプリカ構成は対象外 |
| WAL モード | 書き込みと読み取りを分離するため WAL（Write-Ahead Logging）を有効化 |
| `busy_timeout` | ロック待ち時間を設定（`config/common.toml` の `sqlite_timeout`、デフォルト 30 秒）で指定 |
| 埋め込み次元 | 384 次元固定（`get_embedding_dims()` でコンフィグ取得、fallback=384） |
| `common.toml` 非統合 | `load_all()` が `common.toml` を読み込まないため、`build_db_config()` で空文字列になる可能性あり（既知問題） |

---

## 6. 機能要件

### 6.1 接続管理
- `SQLiteHelper(db_type="rag"|"session")` でデータベースごとの接続を管理
- WAL モード・`PRAGMA synchronous = NORMAL`・`busy_timeout` の自動設定
- sqlite-vec 拡張の自動ロード

### 6.2 スキーマ管理
- `create_rag_schema()` / `create_session_schema()` でテーブル・インデックス・FTS5・vec0 テーブルを作成
- migration コードは削除済み。スキーマは常に最新版のみを `CREATE TABLE IF NOT EXISTS` で作成
- `IF NOT EXISTS` による冪等性を保証（再実行しても既存テーブルを壊さない）

### 6.3 保守機能
- `checkpoint_wal()` — WAL ファイルのフラッシュ
- `vacuum_db()` — データベースの VACUUM（フラグメント解消）
- `purge_old_sessions()` — 保持ポリシーを超えた古いセッションの削除（年齢・件数）
- `prune_old_memories(days)` — 保持期間を超えたメモリエントリの削除
- `rotate_rag_db()` / `rotate_session_db()` / `rotate_db()` — DB ファイルのタイムスタンプ付きアーカイブ
- `recover_corruption()` — rag.sqlite の整合性検査と破損時バックアップ復旧

---

## 7. 入出力

### 7.1 SQLiteHelper API 入出力

```python
# 接続取得
db = SQLiteHelper(target="session").open(row_factory=True)
# target: "rag" → rag.sqlite, "session" → session.sqlite

# コンテキストマネージャーとして使用
with SQLiteHelper(db_type="rag") as db:
    result = db.conn.execute("SELECT ...", params)
```

### 7.2 DbConfig

```python
@dataclass(frozen=True)
class DbConfig:
    rag_db_path: str          # rag.sqlite のパス
    session_db_path: str      # session.sqlite のパス
    sqlite_vec_so: str = ""   # sqlite-vec 拡張ファイルパス（空文字列 = 不要）
    sqlite_timeout: int = 30  # busy_timeout（秒、1 以上）

※ embed_url は DbConfig に存在しない（agent/config.py の EmbeddingConfig が担当）
```

---

## 8. 処理フロー

### 8.1 DB 初期化フロー

```
db/create_schema.py
  → _build_rag_schema_sql(dims) → RAG テーブル DDL 生成
  → _build_session_schema_sql(dims) → Session テーブル DDL 生成
  → executescript() でスキーマ DDL を一括実行
      → migration コードは削除済み（最新スキーマのみ）

SQLiteHelper.open()
  → PRAGMA journal_mode = WAL
  → PRAGMA synchronous = NORMAL
  → PRAGMA busy_timeout = <config>
  → load_extension('/opt/llm/sqlite-vec/vec0.so')
  → row_factory = sqlite3.Row（row_factory=True の場合）
```

### 8.2 ベクター検索フロー

```
RagRepository.vector_search(query, db, top_k)
  → floats_to_blob(query_embedding)  # struct.pack("<384f", ...)
  → SELECT chunk_id, distance FROM chunks_vec
      WHERE embedding MATCH ?
      ORDER BY distance LIMIT top_k
  → JOIN chunks, documents で content・url・title を取得
  → list[RagHit] を返す
```

---

## 9. データ仕様

### 9.1 rag.sqlite スキーマ

**documents テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `doc_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `url` | TEXT | UNIQUE NOT NULL |
| `title` | TEXT | |
| `lang` | TEXT | NOT NULL CHECK (lang IN ('ja', 'en')) |
| `fetched_at` | TEXT | NOT NULL DEFAULT (datetime('now')) |
| `etag` | TEXT | |
| `last_modified` | TEXT | |

**chunks テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `chunk_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `doc_id` | INTEGER | FK → documents |
| `chunk_index` | INTEGER | NOT NULL |
| `content` | TEXT | NOT NULL |
| `normalized_content` | TEXT | |

**chunks_fts（FTS5 バーチャルテーブル）:**
```sql
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content       = 'chunks',
    content_rowid = 'chunk_id',
    tokenize      = 'unicode61'
)
```

**chunks_vec（sqlite-vec バーチャルテーブル）:**
```sql
CREATE VIRTUAL TABLE chunks_vec USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[384]
)
```

### 9.2 session.sqlite スキーマ

**sessions テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `session_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `created_at` | TEXT | NOT NULL DEFAULT (datetime('now')) |
| `title` | TEXT | |

**messages テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `message_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `session_id` | INTEGER | FK → sessions ON DELETE CASCADE |
| `role` | TEXT | NOT NULL |
| `content` | TEXT | NOT NULL |
| `tool_calls` | TEXT | |
| `tool_call_id` | TEXT | |
| `created_at` | TEXT | NOT NULL DEFAULT (datetime('now')) |

**notes テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `note_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `content` | TEXT | NOT NULL |
| `created_at` | TEXT | NOT NULL DEFAULT datetime('now') |

**tool_results テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `session_id` | INTEGER | |
| `turn` | INTEGER | NOT NULL |
| `tool_name` | TEXT | NOT NULL |
| `args_masked` | TEXT | |
| `full_text` | TEXT | NOT NULL |
| `summary` | TEXT | |
| `is_error` | INTEGER | NOT NULL DEFAULT 0 |
| `created_at` | TEXT | NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) |

インデックス: `idx_tool_results_session ON tool_results(session_id)`

**memories テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `memory_id` | TEXT | PRIMARY KEY |
| `memory_type` | TEXT | CHECK (semantic/episodic) |
| `source_type` | TEXT | NOT NULL DEFAULT 'conversation' |
| `session_id` | INTEGER | |
| `turn_id` | TEXT | |
| `project` | TEXT | NOT NULL DEFAULT '' |
| `repo` | TEXT | NOT NULL DEFAULT '' |
| `branch` | TEXT | NOT NULL DEFAULT '' |
| `content` | TEXT | NOT NULL |
| `summary` | TEXT | NOT NULL DEFAULT '' |
| `tags` | TEXT | NOT NULL DEFAULT '[]' |
| `importance` | REAL | NOT NULL DEFAULT 0.5 |
| `pinned` | INTEGER | NOT NULL DEFAULT 0 |
| `created_at` | TEXT | NOT NULL |
| `updated_at` | TEXT | NOT NULL |

**memories_fts（FTS5 バーチャルテーブル）:**
- `memory_id UNINDEXED`, `content`, `summary`, `tags`

**memories_vec（sqlite-vec バーチャルテーブル）:**
- `memory_id TEXT PRIMARY KEY`, `embedding float[384]`

**memory_links テーブル:**

| カラム | 型 | 制約 |
|---|---|---|
| `src_id` | TEXT | NOT NULL FK → memories ON DELETE CASCADE |
| `dst_id` | TEXT | NOT NULL FK → memories ON DELETE CASCADE |
| PRIMARY KEY | (src_id, dst_id) | |

---

## 10. 公開インターフェース仕様

### 10.1 SQLiteHelper（db/helper.py）

```python
class SQLiteHelper:
    def __init__(target: str = "rag")  # "rag" | "session"
    @property
    def DB_PATH(self) -> str
    def open(*, write_mode: bool = False, row_factory: bool = False, load_vec: bool | None = None) -> "SQLiteHelper"
    # load_vec=None: instance デフォルト (rag=True, session=False)
    def __enter__() -> "SQLiteHelper"
    def __exit__(...) -> None
    def close() -> None
    @contextmanager
    def begin_immediate() -> Generator[None]  # BEGIN IMMEDIATE...COMMIT
    @contextmanager
    def begin_exclusive() -> Generator[None]  # BEGIN EXCLUSIVE...COMMIT (VACUUM/DDL 用)
    def health_check() -> dict[str, Any]  # {journal_mode, integrity, page_count, page_size, freelist_count, db_size_bytes}
    def checkpoint(mode: str = "TRUNCATE") -> dict[str, int]  # {"PASSIVE", "FULL", "RESTART", "TRUNCATE"} → {busy, pages_in_wal, pages_checkpointed}
    def vacuum() -> None
    def execute(sql: str, params=()) -> sqlite3.Cursor
    def executemany(sql: str, params_seq: list[tuple[Any, ...]]) -> sqlite3.Cursor
    def fetchall(sql: str, params=()) -> list[Any]
    def commit() -> None
    # conn: sqlite3.Connection が利用可能
    # write_mode=True: FK 制約を有効化する書き込みセッション
```

### 10.2 スキーマ管理（db/create_schema.py）

```python
def run_schema(db: SQLiteHelper, db_type: str) -> None
def get_schema_version(db: SQLiteHelper) -> int
def get_embedding_dims() -> int  # コンフィグから取得、fallback=384
```

### 10.3 保守関数（db/maintenance.py）

```python
# WAL チェックポイント
def checkpoint_wal(db: SQLiteHelper, mode: str | None = None) -> dict[str, int]

# VACUUM
def vacuum_db(db: SQLiteHelper) -> None

# セッション保持ポリシー
def purge_old_sessions(db: SQLiteHelper, cfg: RetentionConfig | None = None) -> dict[str, int]
# RetentionConfig: @dataclass(max_age_days, max_sessions) — from_config() で common.toml から生成

# メモリ保持
def prune_old_memories(db: SQLiteHelper, older_than_days: int) -> int

# DB アーカイブ（rotate）
def rotate_rag_db(archive_dir: str | Path | None = None) -> Path
def rotate_session_db(archive_dir: str | Path | None = None) -> Path
def rotate_db(archive_dir: str | Path | None = None) -> tuple[Path, Path]

# 障害復旧
def recover_corruption(backup_path: str | Path | None = None, *, dry_run: bool = False) -> RecoveryResult
# RecoveryResult: @dataclass(success: bool, action: str, detail: str|None=None, dry_run: bool=False) — action: "vacuum" | "restored" | "no_backup" | "error"
```

### 10.4 ツール結果（db/tool_results.py）

```python
class ToolResultStore:
    def store(session_id: int | None, turn: int, tool_name: str, args_masked: str,
              full_text: str, summary: str | None, is_error: bool) -> int | None
    # 戻り値: 新規行の id（DB エラー時は None）
    def get(result_id: int) -> dict | None
    def list_recent(session_id: int | None, n: int = 20) -> list[dict]
```

---

## 11. エラーハンドリング

| エラー種別 | 対応 |
|---|---|
| `sqlite3.OperationalError` (busy/locked) | `busy_timeout` によって自動待機（デフォルト 30 秒） |
| `sqlite3.IntegrityError` | 呼び出し元に例外を伝播。upsert を使用している場所では発生しない |
| sqlite-vec 拡張ロードエラー | `sqlite3.OperationalError` → DB 接続失敗として処理 |
| スキーマ DDL 実行エラー | `executescript()` 失敗時は例外を再送出 |
| 整合性チェック失敗 | エラーログ出力 + バックアップが存在する場合は復旧処理を試みる |
| `prune_old_memories()` の失敗 | `logger.warning()` を出力して継続（REPL を停止しない） |

---

## 12. 検証計画

| 検証項目 | ツール | 合格基準 |
|---|---|---|
| スキーマ初期化 | `uv run pytest tests/test_create_schema.py` | 全パス |
| DB 保守 | `uv run pytest tests/test_db_maintenance.py` | 全パス |
| ツール結果 | `uv run pytest tests/test_tool_result_store.py` | 全パス |
| 型チェック | `uv run mypy scripts/db/` | 新規エラーなし |
| 統合テスト | 新規 DB 作成 → スキーマ確認 | 全テーブル存在 |

---

## 13. 未解決事項・既知問題

| 項目 | 詳細 |
|---|---|
| `common.toml` 非統合 | `build_db_config()` が `load_all()` から `rag_db_path` 等を取得できない。`db/helper.py` と `rag/pipeline.py` が個別に `ConfigLoader().load("common.toml")` を呼ぶ回避策になっている。将来的に `common.toml` を `load_all()` の対象に含めることを検討中 |
| 埋め込み次元のハードコード | `384` が DDL と `store.py` の両方に重複定義されている。`get_embedding_dims()` で統一済みだが DDL の `float[DIMS]` への統一が必要 |
