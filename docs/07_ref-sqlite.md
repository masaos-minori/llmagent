# db 層リファレンス

インフラ共通モジュール → [`docs/06_ref-infra.md`](06_ref-infra.md)

## db/helper.py — SQLiteHelper

### 機能概要

SQLite (sqlite-vec 拡張付き) の接続ライフサイクル管理と SQL 実行を提供する接続マネージャ。
`target="rag"` (デフォルト) で `rag.sqlite`、`target="session"` で `session.sqlite` に接続する。

全接続に `PRAGMA journal_mode=WAL` / `PRAGMA synchronous=NORMAL` / `PRAGMA busy_timeout=<ms>` を適用する。`busy_timeout` は `common.toml` の `sqlite_busy_timeout_ms`（デフォルト 30000 ms）から取得する。

### コンストラクタ

```python
SQLiteHelper(target: str = "rag")
# target: "rag" | "session" | "workflow"
```

| target | DB ファイル | 格納テーブル |
|---|---|---|
| `"rag"` (デフォルト) | `rag.sqlite` (`rag_db_path`) | documents, chunks, chunks_vec, chunks_fts |
| `"session"` | `session.sqlite` (`session_db_path`) | sessions, messages, notes, tool_results, memories, memories_fts, memories_vec, memory_links |
| `"workflow"` | `workflow.sqlite` (`workflow_db_path`) | tasks, attempts, processed_events, artifacts |

不正な `target` 値は `ValueError` を送出する。sqlite-vec 拡張は `target="rag"` のみロードする（`target="workflow"` / `"session"` はロードしない）。

インスタンス属性 `conn: sqlite3.Connection | None` は `open()` 前は `None`。

### インスタンス属性 (コンストラクタ時に `build_db_config()` で解決)

```python
db = SQLiteHelper("rag")
print(db._db_path)           # rag.sqlite の絶対パス
print(db._vec_so)            # vec0.so の絶対パス (空文字列の場合は vec 不要)
print(db._sqlite_timeout)    # sqlite3.connect() timeout (秒、デフォルト 30)
print(db._busy_timeout_ms)   # PRAGMA busy_timeout 値 (ミリ秒、デフォルト 30000)
print(db._default_load_vec)  # target="rag" → True、target="session" → False
```

| インスタンス属性 | 説明 |
|---|---|
| `db._db_path` | `DbConfig.rag_db_path` / `session_db_path` / `workflow_db_path`。`__init__()` 時に確定 |
| `db._vec_so` | `config/common.toml` の `sqlite_vec_so`。空文字列は vec 拡張不要を意味する |
| `db._sqlite_timeout` | `config/common.toml` の `sqlite_timeout` (デフォルト 30 秒) |
| `db._busy_timeout_ms` | `config/common.toml` の `sqlite_busy_timeout_ms` (デフォルト 30000 ms) |
| `db._default_load_vec` | `target="rag"` → `True`、`target="session"` → `False`。`open()` で vec ロードのデフォルト値 |

`__init__()` は内部で `build_db_config()` (`db.config`) を呼び出し、インスタンス属性に格納する。不正な `target` 値は `ValueError` を送出する。

インスタンス属性 `DB_PATH` はプロパティ — `self._db_path` を返す。

### API

```python
from db.helper import SQLiteHelper

# RAG DB (rag.sqlite)
with SQLiteHelper("rag").open() as db:
    rows = db.fetchall("SELECT * FROM documents WHERE lang = :lang", {"lang": "ja"})

# セッション DB (session.sqlite)
with SQLiteHelper("session").open(write_mode=True) as db:
    cur = db.execute("INSERT INTO sessions DEFAULT VALUES")
    db.commit()
```

| メソッド | 説明 |
|---|---|
| `open(*, write_mode=False, row_factory=False) -> SQLiteHelper` | 接続を開いて `self.conn` に格納し `self` を返す。`with` ブロックと組み合わせて使用可 |
| `execute(sql, params=()) -> sqlite3.Cursor` | SQL を実行してカーソルを返す。`params` は tuple (位置) または dict (名前付き)。接続未開時は `RuntimeError`、空 SQL は `ValueError` |
| `executemany(sql, params_seq) -> sqlite3.Cursor` | 複数行を一括実行する。`params_seq` は `list[tuple[Any, ...]]`。接続未開時は `RuntimeError`、空 SQL は `ValueError` |
| `fetchall(sql, params=()) -> list[Any]` | SQL を実行して全結果行をリストで返す (execute + fetchall の合成) |
| `commit() -> None` | `self.conn` のトランザクションをコミット。`OperationalError` はログ出力後に再送出 |
| `close() -> None` | `self.conn` を閉じて `None` にリセットする (冪等) |
| `begin_immediate() -> contextmanager` | `BEGIN IMMEDIATE` トランザクションブロック。例外時は自動 `ROLLBACK` |
| `begin_exclusive() -> contextmanager` | `BEGIN EXCLUSIVE` トランザクションブロック。例外時は自動 `ROLLBACK` |
| `health_check() -> DbHealthMetrics` | DB ヘルスメトリクス (`DbHealthMetrics`) を返す |
| `checkpoint(mode="TRUNCATE") -> WalCheckpointCounts` | WAL チェックポイントを実行し `{busy, log_size, pages_checkpointed}` を返す |
| `vacuum() -> None` | `VACUUM` を実行してDBファイルをインプレース再構築 |
| `__enter__() -> SQLiteHelper` | コンテキストマネージャ開始。`self` を返す |
| `__exit__(...) -> None` | コンテキストマネージャ終了。`close()` を呼び出す |

#### SQLiteHelper.open

```python
def open(self, *, write_mode: bool = False, row_factory: bool = False, load_vec: bool | None = None) -> "SQLiteHelper"
```

sqlite-vec 拡張をロード済みの接続を `self.conn` に格納し、`self` を返す。

接続確立後に以下を順番に適用する:

1. sqlite-vec 拡張ロード (`self._vec_so`)。ロード後に `enable_load_extension(False)` を呼んでセキュリティを確保
2. `PRAGMA journal_mode=WAL`
3. `PRAGMA synchronous=NORMAL`
4. `PRAGMA busy_timeout=<sqlite_busy_timeout_ms>` (デフォルト 30000 ms)
5. `write_mode=True` のとき `PRAGMA foreign_keys=ON` を追加設定

| キーワード引数 | デフォルト | 説明 |
|---|---|---|
| `write_mode` | `False` | `True` のとき `PRAGMA foreign_keys=ON` を追加設定 |
| `row_factory` | `False` | `True` のとき `conn.row_factory = sqlite3.Row` を設定し、列名属性アクセスを有効化 |
| `load_vec` | `None` (= target 依存) | `True` で vec 強制ロード、`False` でスキップ。`None` は target="rag" → 有効、target="session" → 無効のインスタンスデフォルトを使用 |

呼び出しパターン:

| 呼び出し元 | パターン |
|---|---|
| `create_schema.py` | `with SQLiteHelper("rag").open(write_mode=True) as db:` — RAG スキーマ作成 |
| `create_schema.py` | `with SQLiteHelper("session").open(write_mode=True) as db:` — セッションスキーマ作成 |
| `rag/ingestion/ingester.py` | `db.open(write_mode=True)` — WAL + 外部キー有効 (一括投入のため手動管理) |
| `agent/repl.py` | `with SQLiteHelper("rag").open() as db:` — 起動バナー用チャンク数取得 |
| `agent/session.py` | `with SQLiteHelper("session").open(write_mode=True) as db:` — セッション永続化 |
| `agent/memory/store.py` | `with SQLiteHelper("session").open(write_mode=True) as db:` — メモリ層 |
| `db/tool_results.py` | `with SQLiteHelper("session").open(...) as db:` — ツール結果保存 |

#### SQLiteHelper.execute

```python
def execute(self, sql: str, params: dict[str, Any] | tuple[Any, ...] = ()) -> sqlite3.Cursor
```

接続が未開 (`conn is None`) の場合は `RuntimeError`、`sql` が空または文字列でない場合は `ValueError` を送出する。

| `params` の形式 | プレースホルダ構文 | 例 |
|---|---|---|
| `tuple` | `?` (位置) | `db.execute("SELECT * FROM t WHERE id = ?", (1,))` |
| `dict` | `:name` (名前付き) | `db.execute("SELECT * FROM t WHERE id = :id", {"id": 1})` |

#### SQLiteHelper.executemany

```python
def executemany(self, sql: str, params_seq: list[tuple[Any, ...]]) -> sqlite3.Cursor
```

`self.conn.executemany(sql, params_seq)` を呼び出して複数行を一括実行する。接続が未開 (`conn is None`) の場合は `RuntimeError`、`sql` が空または文字列でない場合は `ValueError` を送出する。バッチINSERT / UPDATE に使用する。

#### SQLiteHelper.fetchall

```python
def fetchall(self, sql: str, params: dict[str, Any] | tuple[Any, ...] = ()) -> list[Any]
```

`self.conn.execute(sql, params).fetchall()` を呼び出して全結果行をリストで返す。`params` の形式は `execute()` と同じ (tuple または dict)。接続が未開の場合は `RuntimeError`。

#### SQLiteHelper.commit

```python
def commit(self) -> None
```

接続が未開 (`conn is None`) の場合は `RuntimeError` を送出する。`sqlite3.OperationalError` 発生時はエラーをログ出力してから再送出する。

#### SQLiteHelper.close

```python
def close(self) -> None
```

`self.conn` が開いていれば閉じて `None` にリセット。`with` ブロック (`__exit__`) から自動的に呼ばれる。`self.conn` が `None` の場合は何もしない (冪等)。クローズ中の例外は `WARNING` レベルでログ出力するが送出しない。

#### SQLiteHelper.begin_immediate / begin_exclusive

```python
with SQLiteHelper("rag").open(write_mode=True) as db:
    with db.begin_immediate():
        db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        # COMMIT は with ブロック終了時に自動実行; 例外時は ROLLBACK
```

| メソッド | 用途 |
|---|---|
| `begin_immediate()` | `BEGIN IMMEDIATE` で書き込みロックを取得。複数ステートメントをアトミックに実行する書き込みトランザクション (chunk 投入、ドキュメント削除など) に使用 |
| `begin_exclusive()` | `BEGIN EXCLUSIVE` で読み書き全排他ロック。VACUUM やスキーママイグレーションなど他のリーダーを完全にブロックする必要がある場合のみ使用 |

どちらも `@contextmanager` — `with db.begin_immediate():` の形式で使用。`open()` 前に呼ぶと `RuntimeError`。例外発生時は自動的に `ROLLBACK`。

#### SQLiteHelper.health_check

```python
metrics = SQLiteHelper("rag").open().health_check()
# {"journal_mode": "wal", "integrity": "ok", "page_count": 1024,
#  "page_size": 4096, "freelist_count": 10, "db_size_bytes": 4194304}
```

`PRAGMA quick_check` (高速版 integrity check) を実行し、journal mode / integrity / page stats を dict で返す。`/db health` コマンドから呼ばれる。`open()` 前に呼ぶと `RuntimeError`。

#### SQLiteHelper.checkpoint

```python
result = db.checkpoint(mode="TRUNCATE")
# WalCheckpointCounts(busy=0, log_size=512, pages_checkpointed=512)
```

| mode | 動作 |
|---|---|
| `PASSIVE` | リーダーを待たずにフラッシュ (非ブロッキング) |
| `FULL` | 全リーダー終了後にフラッシュ |
| `RESTART` | FULL + WAL 書き込み位置をリセット |
| `TRUNCATE` | RESTART + WAL を 0 バイトに切り詰め (デフォルト。大量書き込み後のディスク回収に使用) |

不正な `mode` 値は `ValueError` を送出する。`open()` 前に呼ぶと `RuntimeError`。

#### SQLiteHelper.vacuum

```python
db.vacuum()
```

`VACUUM` を実行してDBファイルをインプレース再構築。空きページを回収してデフラグ。実行にはDB サイズの約2倍の空きディスクが必要。トランザクション外で呼ぶこと。`open()` 前に呼ぶと `RuntimeError`。

### 使用スクリプト

| スクリプト | target | 使用内容 |
|---|---|---|
| `create_schema.py` | `"rag"` / `"session"` | `create_rag_schema()` / `create_session_schema()` |
| `rag/ingestion/ingester.py` | `"rag"` | `with SQLiteHelper("rag").open(write_mode=True) as db:` — 一括投入 |
| `agent/repl.py` | `"rag"` | 起動バナー用チャンク数取得 |
| `agent/session.py` | `"session"` | `with SQLiteHelper("session").open(write_mode=True) as db:` — セッション/メッセージ操作 |
| `agent/memory/store.py` | `"session"` | `with SQLiteHelper("session").open(...) as db:` — メモリ層 |
| `db/tool_results.py` | `"session"` | `with SQLiteHelper("session").open(...) as db:` — ツール結果保存 |
| `rag/pipeline.py` | `"rag"` | `fetchall(...)` — `vector_search` / `fts_search` が SQLiteHelper を受け取る |

---

## db/store.py

### 機能概要

RAG パイプライン向けの抽象 Protocol 定義と SQLite バックエンド実装を提供する。構造的部分型 (`Protocol`) により将来的な非 SQLite バックエンドへの差し替えを可能にする。

埋込ヘルパー関数:

```python
from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob

dims = get_embedding_dims()    # config/common.toml の embedding_dims (デフォルト 384)
nbytes = get_embedding_bytes() # float32 BLOB サイズ (dims * 4)
validate_embedding_blob(blob)  # bytes でない場合は TypeError、不正サイズで ValueError を送出
```

| 関数 | 説明 |
|---|---|
| `get_embedding_dims() -> int` | `common.toml` の `embedding_dims` を読み込む。設定なし・失敗時は `384` を返す |
| `get_embedding_bytes() -> int` | `get_embedding_dims() * 4` を返す (float32 = 4 bytes/dim) |
| `validate_embedding_blob(blob)` | BLOB サイズが `get_embedding_bytes()` と一致しない場合 `ValueError` を送出 |

### Protocol 定義

| Protocol | 対象テーブル | 主なメソッド |
|---|---|---|
| `VectorStore` | `chunks_vec` | `vec_insert(chunk_id, embedding)` / `vec_search(embedding, k) -> list[tuple[int, float]]` / `vec_delete(chunk_id)` / `vec_count() -> int` |
| `DocumentStore` | `documents` / `chunks` | `doc_upsert(url, title, lang, etag, last_modified) -> int` / `doc_get(url) -> dict \| None` / `doc_list(lang, limit) -> list[dict]` / `doc_delete(url) -> bool` / `chunk_insert(doc_id, index, content, normalized) -> int` / `chunk_count() -> int` |
| `SessionStore` | `sessions` / `messages` | `session_create() -> int` / `session_list(limit) -> list[dict]` / `session_rename(session_id, title)` / `session_delete(session_id)` / `message_save(session_id, role, content, tool_calls)` / `message_list(session_id) -> list[dict]` |

全 Protocol は `@runtime_checkable` — `isinstance()` でチェック可能。

### VectorStore Protocol

```python
@runtime_checkable
class VectorStore(Protocol):
    def vec_insert(self, chunk_id: int, embedding: bytes) -> None: ...
    def vec_search(self, embedding: bytes, k: int) -> list[tuple[int, float]]: ...
    def vec_delete(self, chunk_id: int) -> None: ...
    def vec_count(self) -> int: ...
```

| メソッド | 説明 |
|---|---|
| `vec_insert(chunk_id, embedding)` | `chunks_vec` に float32 BLOB を挿入する |
| `vec_search(embedding, k)` | `embedding` に近い上位 `k` 件の `(chunk_id, distance)` ペアを返す |
| `vec_delete(chunk_id)` | `chunk_id` の埋め込みを削除する。存在しない場合は no-op |
| `vec_count()` | 格納済みの埋め込み数を返す |

### DocumentStore Protocol

```python
@runtime_checkable
class DocumentStore(Protocol):
    def doc_upsert(self, url: str, title: str | None, lang: str,
                   etag: str | None, last_modified: str | None) -> int: ...
    def doc_get(self, url: str) -> dict[str, Any] | None: ...
    def doc_list(self, lang: str | None, limit: int) -> list[dict[str, Any]]: ...
    def doc_delete(self, url: str) -> bool: ...
    def chunk_insert(self, doc_id: int, index: int, content: str,
                     normalized: str | None) -> int: ...
    def chunk_count(self) -> int: ...
```

| メソッド | 説明 |
|---|---|
| `doc_upsert(url, title, lang, etag, last_modified)` | URL で SELECT し、存在すれば UPDATE、なければ INSERT して `doc_id` を返す。`title` は `str \| None` |
| `doc_get(url)` | `url` に対応するドキュメント行を返す。見つからない場合は `None`。返り値は `{doc_id, url, title, lang, fetched_at, etag, last_modified}` |
| `doc_list(lang, limit)` | 最大 `limit` 件のドキュメント行を `fetched_at DESC` 順で返す。`lang` が `None` の場合は全言語。返り値は `{doc_id, url, title, lang, fetched_at}` |
| `doc_delete(url)` | ドキュメントと CASCADE されたチャンクを削除。見つかった場合は `True` |
| `chunk_insert(doc_id, index, content, normalized)` | `chunks` テーブル (`chunk_index` カラム) に 1 行挿入して `chunk_id` を返す |
| `chunk_count()` | `chunks` テーブルの総チャンク数を返す |

### SessionStore Protocol

```python
@runtime_checkable
class SessionStore(Protocol):
    def session_create(self) -> int: ...
    def session_list(self, limit: int) -> list[dict[str, Any]]: ...
    def session_rename(self, session_id: int, title: str) -> None: ...
    def session_delete(self, session_id: int) -> None: ...
    def message_save(self, session_id: int, role: str, content: str,
                     tool_calls: str | None) -> None: ...
    def message_list(self, session_id: int) -> list[dict[str, Any]]: ...
```

| メソッド | 説明 |
|---|---|
| `session_create()` | `sessions` テーブルに新規行を挿入して `session_id` を返す |
| `session_list(limit)` | 最新 `limit` 件のセッション行を `created_at DESC` 順で返す。返り値は `{session_id, created_at, title}` |
| `session_rename(session_id, title)` | 指定セッションの `title` を更新する |
| `session_delete(session_id)` | セッションを削除する。`ON DELETE CASCADE` でメッセージも削除される |
| `message_save(session_id, role, content, tool_calls)` | `messages` テーブルにメッセージを追記する。`tool_calls` は `str \| None` |
| `message_list(session_id)` | `session_id` の全メッセージを挿入順 (`message_id` 昇順) で返す。返り値は `{role, content, tool_calls}` |

### SQLite バックエンド実装

| 実装クラス | Protocol | コンストラクタ引数 | 説明 |
|---|---|---|---|
| `SQLiteVectorStore(db)` | `VectorStore` | `db: SQLiteHelper` | `chunks_vec` 仮想テーブル経由の sqlite-vec KNN 検索。`vec_insert` は `validate_embedding_blob` で BLOB サイズを検証する |
| `SQLiteDocumentStore(db)` | `DocumentStore` | `db: SQLiteHelper` | `documents` / `chunks` テーブルへの CRUD。`doc_upsert` は URL で SELECT し、存在すれば UPDATE、なければ INSERT する |
| `SQLiteSessionStore(db)` | `SessionStore` | `db: SQLiteHelper` | `sessions` / `messages` テーブルへの CRUD。`session_list` は `created_at DESC` 順で返す |
| `SQLiteMemoryDeleteStore(db)` | `MemoryDeleteStore` | `db: SQLiteHelper` | `memories` / `memories_fts` / `memories_vec` の cross-table 削除。アトミックに実行し `MemoryDeleteResult(deleted=N)` を返す |

#### MemoryDeleteStore / SQLiteMemoryDeleteStore

```python
from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore, MemoryDeleteResult

store = SQLiteMemoryDeleteStore(db)
result: MemoryDeleteResult = store.delete_memories_before(older_than_days=30)
# result.deleted — 削除件数
```

`maintenance.py` の `prune_old_memories()` は内部でこのクラスに委譲する。

---

## db/maintenance.py

### 機能概要

SQLite 運用メンテナンス操作 (WAL チェックポイント / VACUUM / DB ローテーション / セッション保持期限 / 破損回復) を提供する。全関数はポリシー決定を担い、接続管理は `SQLiteHelper` に委譲する。

### API

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `checkpoint_wal(db, mode=None) -> WalCheckpointCounts` | `(db: SQLiteHelper, mode: str \| None = None)` | WAL をフラッシュして `{busy, log_size, pages_checkpointed}` を返す。`mode` 未指定時は `common.toml` の `sqlite_wal_checkpoint_mode` (デフォルト `TRUNCATE`) を使用 |
| `vacuum_db(db) -> None` | `(db: SQLiteHelper)` | `db.vacuum()` に委譲。トランザクション外で呼ぶこと |
| `purge_old_sessions(db, cfg=None) -> PurgeCounts` | `(db: SQLiteHelper, cfg: RetentionConfig \| None = None)` | 保持ポリシーに従いセッションを削除。`PurgeCounts(age_deleted, count_deleted)` を返す |
| `prune_old_memories(db, older_than_days) -> int` | `(db: SQLiteHelper, older_than_days: int)` | `memories` / `memories_fts` / `memories_vec` テーブルから古いメモリを削除して削除数を返す |
| `rotate_rag_db(archive_dir=None) -> Path` | `(archive_dir: str \| Path \| None = None)` | `rag.sqlite` をタイムスタンプ付きファイル名でアーカイブ。SQLite online backup API で WAL 整合性を保証 |
| `rotate_session_db(archive_dir=None) -> Path` | `(archive_dir: str \| Path \| None = None)` | `session.sqlite` をタイムスタンプ付きでアーカイブ |
| `rotate_db(archive_dir=None) -> tuple[Path, Path]` | `(archive_dir: str \| Path \| None = None)` | `rag.sqlite` と `session.sqlite` を両方アーカイブ。`(rag_dest, session_dest)` を返す |
| `recover_corruption(backup_path=None, *, target="rag", dry_run=False) -> RecoveryResult` | `(backup_path: str \| Path \| None = None, *, target: str = "rag", dry_run: bool = False)` | `target` の DB に対して integrity_check → 正常時は VACUUM。破損時はアーカイブしてバックアップから復元。`RecoveryResult` を返す |

#### RetentionConfig

```python
@dataclass(frozen=True)
class RetentionConfig:
    max_sessions: int = 100   # 最大保持セッション数
    max_age_days: int = 90    # 保持日数 (0 = 無効)
```

`RetentionConfig.from_config()` で `common.toml` の `sqlite_retention_max_sessions` / `sqlite_retention_max_age_days` から構築する。

#### purge_old_sessions の動作

1. `max_age_days > 0` のとき、`created_at` が `N` 日より古いセッションを削除 (`age_deleted` に計上)
2. 残存セッション数が `max_sessions` を超える場合、古い順から超過分を削除 (`count_deleted` に計上)
3. `sessions` テーブルに `ON DELETE CASCADE` が設定されていることを前提とする (`messages` が連動削除)
4. 完了後に `db.conn.commit()` を呼ぶ

#### prune_old_memories の動作

1. `memories` テーブルから `older_than_days` より古い `memory_id` を収集する
2. `memories` / `memories_fts` / `memories_vec` の 3 テーブルから対象行を削除する
3. `db.commit()` を呼び、`MemoryDeleteResult(deleted=N)` を返す。失敗時は例外が伝播する

#### RecoveryResult

```python
@dataclass(frozen=True)
class RecoveryResult:
    success: bool
    action: str        # "vacuum" | "vacuum_failed" | "restored" | "no_backup" | "error"
    detail: str | None = None
    dry_run: bool = False
```

| `action` 値 | 意味 |
|---|---|
| `"vacuum"` | integrity_check OK。VACUUM を実行 (または dry_run でスキップ) |
| `"vacuum_failed"` | integrity_check OK だが VACUUM 実行中に失敗 |
| `"restored"` | 破損検出。`backup_path` から復元成功 |
| `"no_backup"` | 破損検出。使用可能な backup_path なし |
| `"error"` | DB オープン失敗または OS レベルのエラー |

#### recover_corruption の動作

1. `target` で指定された DB に対して `PRAGMA integrity_check` を実行する
2. `dry_run=True` の場合: VACUUM/復元を行わず integrity 結果のみ返す
3. 結果が `"ok"` の場合: VACUUM を実行して `RecoveryResult(success=True, action="vacuum")` を返す。VACUUM 失敗は `RecoveryResult(success=False, action="vacuum_failed", detail=...)` を返す
4. 結果が `"ok"` 以外の場合: 破損ファイルを `{stem}_corrupt_{timestamp}{suffix}` 名でアーカイブし、`backup_path` からコピーして復元する。成功時は `action="restored"`、`backup_path` 未指定・不存在時は `action="no_backup"`、OSError 発生時は `action="error"`

#### rotate_* の動作

`archive_dir` 未指定時は `common.toml` の `sqlite_archive_dir` (デフォルト `/opt/llm/db/archive`) を使用する。アーカイブ先ファイル名は `{stem}_{YYYYMMDD_HHMMSS}{suffix}` 形式。SQLite online backup API (`src.backup(dst)`) で WAL 整合性を保証したコピーを作成する。

---

## db/tool_results.py — ToolResultStore

### 機能概要

ツール実行結果の全文を `tool_results` テーブルに保存する。LLM 履歴には要約または切り詰めのみが含まれるため、全文は `/tool show <id>` で後追い確認できるようにここに保持する。DB エラー時は例外を送出し、呼び出し元で処理する。

### コンストラクタ

```python
ToolResultStore()
# 引数なし
```

### API

```python
from db.tool_results import ToolResultStore

store = ToolResultStore()
```

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `store(session_id, turn, tool_name, args_masked, full_text, summary, is_error) -> int \| None` | `(session_id: int \| None, turn: int, tool_name: str, args_masked: str, full_text: str, summary: str \| None, is_error: bool)` | `tool_results` テーブルに 1 行 INSERT して新規 `id` を返す。DB エラー時は例外を送出（戻り値の `None` は安全性のため残り） |
| `get(result_id) -> ToolResultRow \| None` | `(result_id: int)` | `id` で 1 件取得。見つからない場合は `None`。`ToolResultRow(id, tool_name, is_error, summary, session_id, turn, args_masked, full_text, created_at)` を返す |
| `list_recent(session_id, n=20) -> list[ToolResultRow]` | `(session_id: int \| None, n: int = 20)` | 指定セッションの最新 `n` 件を古い順 (昇順) で返す。`session_id=None` の場合は `[]` を返す。DB エラー時は例外を送出 |

#### list_recent の実装詳細

内部では `ORDER BY id DESC LIMIT ?` で最新 `n` 件を取得し、`reversed()` で古い順に並べ直して返す。返り値の各要素は `{id, tool_name, summary, is_error}` を明示的に設定 (`session_id=None`, `turn=0`, `args_masked=""`, `full_text=""`, `created_at=""` のデフォルト値を持つ)。

#### get の返り値フィールド

`row_factory=True` で取得するため、`tool_results` テーブルの全カラムを含む `ToolResultRow` を返す:

`id` / `session_id` / `turn` / `tool_name` / `args_masked` / `full_text` / `summary` / `is_error` / `created_at`

### tool_results テーブルスキーマ

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | 自動採番 ID |
| `session_id` | INTEGER | セッション ID (NULL 許可) |
| `turn` | INTEGER | ターン番号 |
| `tool_name` | TEXT | ツール名 |
| `args_masked` | TEXT | マスク済みツール引数の JSON 文字列 |
| `full_text` | TEXT | ツール実行結果の全文 |
| `summary` | TEXT | 要約テキスト (NULL 許可) |
| `is_error` | INTEGER | エラー有無 (0/1) |
| `created_at` | TEXT | 作成日時 (ISO 8601) |

---

## memories / memories_fts / memories_vec テーブル

`session.sqlite` に配置。`MemoryStore` (`agent/memory/store.py`) が CRUD を担当。`MemoryServices` (`agent/memory/services.py`) 経由の各サブサービスが SessionStart / UserPrompt / Stop ライフサイクルで読み書きする。

### memories テーブルスキーマ

| カラム | 型 | 説明 |
|---|---|---|
| `memory_id` | TEXT PRIMARY KEY | UUID v4 |
| `memory_type` | TEXT | `"semantic"` (ルール/方針/事実) または `"episodic"` (Q&A/失敗/履歴) |
| `source_type` | TEXT | 抽出元: `"conversation"` / `"rule"` / `"tool_result"` など |
| `session_id` | INTEGER | 関連セッション ID (NULL 許可) |
| `turn_id` | TEXT | 関連ターン ID (NULL 許可) |
| `project` | TEXT | プロジェクト名 (フィルタ用) |
| `repo` | TEXT | リポジトリ名 (フィルタ用) |
| `branch` | TEXT | ブランチ名 (フィルタ用) |
| `content` | TEXT | メモリ本文 |
| `summary` | TEXT | 要約テキスト (NULL 許可) |
| `tags` | TEXT | JSON 配列形式のタグ |
| `importance` | REAL | 重要度スコア (0.0〜1.0) |
| `pinned` | INTEGER | ピン留めフラグ (0/1); ピン留め済みエントリは `on_session_start` で優先注入 |
| `created_at` | DATETIME | 作成日時 (ISO 8601) |
| `updated_at` | DATETIME | 更新日時 (ISO 8601) |

### memories_fts テーブル

`memories` テーブルのコンテンツと同期する FTS5 仮想テーブル (`content_rowid=memory_id` は不使用; `rowid` は `memories` の rowid に対応)。`FtsRetriever.search()` が BM25 全文検索に使用する。

### memories_vec テーブル

`vec0` 仮想テーブル (sqlite-vec 拡張)。`memory_id TEXT` と `embedding FLOAT[384]` を持つ。`embed_enabled=True` かつ埋込生成に成功した場合のみ書き込まれる。`VectorRetriever.knn_search()` が KNN 近傍検索に使用する。

### memory_links テーブル

`src_id TEXT` / `dst_id TEXT` の 2 カラム (PRIMARY KEY は `(src_id, dst_id)`)。`MemoryIngestionService._link_duplicates()` がコサイン距離 `< dedup_threshold` のエントリ間にリンクを記録する (重複排除用)。

### MemoryStore API

```python
from agent.memory.store import MemoryStore

store = MemoryStore()
```

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `add(entry, embedding=None)` | `(entry: MemoryEntry, embedding: list[float] \| None)` | `memories` + `memories_fts` に挿入。`embedding` があれば `memories_vec` にも挿入 |
| `upsert(entry, embedding=None)` | `(entry: MemoryEntry, embedding: list[float] \| None)` | `memory_id` で INSERT OR REPLACE。`memories_fts` / `memories_vec` も同期 |
| `delete(memory_id)` | `(memory_id: str) -> bool` | 1 件削除。見つかった場合は `True` |
| `get_by_id(memory_id)` | `(memory_id: str) -> MemoryEntry \| None` | `memory_id` で 1 件取得 |
| `search_by_type(memory_type, limit)` | `(memory_type: str, limit: int = 20) -> list[MemoryEntry]` | `memory_type` でフィルタして `importance DESC, pinned DESC` 順で返す |
| `count_by_type()` | `() -> dict[str, int]` | `memory_type` ごとの件数を dict で返す |
| `count_vec()` | `() -> int` | `memories_vec` の総行数を返す。`vec0` 未ロード時は `0` |
| `pin(memory_id)` / `unpin(memory_id)` | `(memory_id: str) -> bool` | ピン留め / 解除。見つかった場合は `True` |
| `clear_by_session(session_id)` | `(session_id: int) -> int` | 指定セッションの全エントリを削除して削除数を返す |
| `count_entries()` | `() -> int` | 全メモリ件数を返す。DB エラー時は `0` |

---

## db/workflow_schema.py — Metadata DB

### 機能概要

`workflow.sqlite` の DDL 定義と初期化エントリポイント。`agent/workflow/state_store.py` が使用する 4 テーブルを `CREATE TABLE IF NOT EXISTS` で作成する（冪等）。

```bash
# 初期化コマンド (deploy/init_db.sh から呼び出される)
PYTHONPATH=scripts python -m db.workflow_schema
```

### スキーマ（workflow.sqlite）

**tasks テーブル:**

| カラム | 型 | 説明 |
|---|---|---|
| `task_id` | TEXT PK | UUID4 |
| `session_id` | TEXT | セッション ID |
| `turn_number` | INTEGER | ターン番号 |
| `workflow_version` | TEXT | ワークフロー定義バージョン |
| `status` | TEXT | `pending` / `running` / `completed` / `failed` / `halted` |
| `idempotency_key` | TEXT UNIQUE | `session_id:turn_number` — 重複防止 |
| `created_at` | TEXT | ISO-8601 UTC |
| `updated_at` | TEXT | ISO-8601 UTC |

**attempts テーブル:**

| カラム | 型 | 説明 |
|---|---|---|
| `attempt_id` | TEXT PK | UUID4 |
| `task_id` | TEXT FK | `tasks(task_id)` ON DELETE CASCADE |
| `stage_id` | TEXT | `plan` / `execute` / `verify` |
| `status` | TEXT | `running` / `completed` / `failed` |
| `started_at` | TEXT | ISO-8601 UTC |
| `ended_at` | TEXT \| NULL | 完了時刻 |
| `error_msg` | TEXT \| NULL | 失敗理由 |

**processed_events テーブル:**

| カラム | 型 | 説明 |
|---|---|---|
| `event_id` | TEXT PK | `{task_id}:{stage_id}:{attempt}` — ステージの冪等キー |
| `task_id` | TEXT FK | `tasks(task_id)` ON DELETE CASCADE |
| `stage_id` | TEXT | ステージ名 |
| `recorded_at` | TEXT | ISO-8601 UTC |

**artifacts テーブル:**

| カラム | 型 | 説明 |
|---|---|---|
| `artifact_id` | TEXT PK | UUID4 |
| `task_id` | TEXT FK | `tasks(task_id)` ON DELETE CASCADE |
| `stage_id` | TEXT | ステージ名 |
| `uri` | TEXT | アーティファクトの URI |
| `created_at` | TEXT | ISO-8601 UTC |

### API

```python
from db.workflow_schema import init_schema

init_schema("/opt/llm/db/workflow.sqlite")
# → 4 テーブルを CREATE TABLE IF NOT EXISTS で作成
```
| `count_prunable(days)` | `(days: int) -> int` | `days` 日より古いエントリ件数を返す (削除なし) |
