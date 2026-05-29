# sqlite_helper.py リファレンス

インフラ共通モジュール → [`docs/06_ref-infra.md`](06_ref-infra.md)

## sqlite_helper.py

### 機能概要

SQLite (sqlite-vec 拡張付き) の接続ライフサイクル管理と SQL 実行を提供する接続マネージャ。
`target="rag"` (デフォルト) で `rag.sqlite`、`target="session"` で `session.sqlite` に接続する。

### コンストラクタ

```python
SQLiteHelper(target: str = "rag")
# target: "rag" | "session"
```

| target | DB ファイル | 格納テーブル |
|---|---|---|
| `"rag"` (デフォルト) | `rag.sqlite` (`rag_db_path`) | documents, chunks, chunks_vec, chunks_fts |
| `"session"` | `session.sqlite` (`session_db_path`) | sessions, messages, notes, tool_results, memory_entries, memory_vec |

不正な `target` 値は `ValueError` を送出する。

### クラス属性

```python
SQLiteHelper._ensure_config()   # 一度呼べばクラス変数が確定する
print(SQLiteHelper._RAG_PATH)   # rag.sqlite の絶対パス
print(SQLiteHelper._SESSION_PATH)  # session.sqlite の絶対パス
print(SQLiteHelper.SQLITE_VEC_SO)  # vec0.so の絶対パス
```

| クラス属性 | 説明 |
|---|---|
| `SQLiteHelper._RAG_PATH` | `config/common.toml` の `rag_db_path` (例: `/opt/llm/db/rag.sqlite`)。`_ensure_config()` 後に確定 |
| `SQLiteHelper._SESSION_PATH` | `config/common.toml` の `session_db_path` (例: `/opt/llm/db/session.sqlite`)。同上 |
| `SQLiteHelper.SQLITE_VEC_SO` | `config/common.toml` の `sqlite_vec_so` (例: `/opt/llm/sqlite-vec/vec0.so`)。同上 |

インスタンス属性 `DB_PATH` はプロパティ — `target` に応じて `_RAG_PATH` か `_SESSION_PATH` を返す。
`open()` は内部で `_ensure_config()` を呼ぶため、接続前に明示的な初期化は不要。

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
| `execute(sql, params=()) -> sqlite3.Cursor` | SQL を実行してカーソルを返す。`params` は tuple (位置) または dict (名前付き) |
| `fetchall(sql, params=()) -> list[Any]` | SQL を実行して全結果行をリストで返す (execute + fetchall の合成) |
| `commit() -> None` | `self.conn` のトランザクションをコミット |
| `close() -> None` | `self.conn` を閉じて `None` にリセットする (冪等) |
| `__enter__() -> SQLiteHelper` | コンテキストマネージャ開始。`self` を返す |
| `__exit__(...) -> None` | コンテキストマネージャ終了。`close()` を呼び出す |

#### SQLiteHelper.open

```python
def open(self, *, write_mode: bool = False, row_factory: bool = False) -> "SQLiteHelper"
```

sqlite-vec 拡張をロード済みの接続を `self.conn` に格納し、`self` を返す。拡張ロード後に `enable_load_extension(False)` を呼んでセキュリティを確保。`self` を返すことで `with SQLiteHelper("rag").open(...) as db:` パターンが使用可能。

| キーワード引数 | デフォルト | 説明 |
|---|---|---|
| `write_mode` | `False` | `True` のとき `PRAGMA foreign_keys=ON` を追加設定 |
| `row_factory` | `False` | `True` のとき `conn.row_factory = sqlite3.Row` を設定し、列名属性アクセスを有効化 |

呼び出しパターン:

| 呼び出し元 | パターン |
|---|---|
| `create_schema.py` | `with SQLiteHelper("rag").open(write_mode=True) as db:` — RAG スキーマ作成 |
| `create_schema.py` | `with SQLiteHelper("session").open(write_mode=True) as db:` — セッションスキーマ作成 |
| `rag/ingestion/ingester.py` | `db.open(write_mode=True)` — WAL + 外部キー有効 (一括投入のため手動管理) |
| `agent/repl.py` | `with SQLiteHelper("rag").open(row_factory=True) as db:` — RAG クエリ |
| `agent/session.py` | `with SQLiteHelper("session").open(write_mode=True) as db:` — セッション永続化 |
| `agent/memory/store.py` | `with SQLiteHelper("session").open(write_mode=True) as db:` — メモリ層 |
| `db/tool_results.py` | `with SQLiteHelper("session").open(...) as db:` — ツール結果保存 |

#### SQLiteHelper.fetchall

```python
def fetchall(self, sql: str, params: dict | tuple = ()) -> list[Any]
```

`self.conn.execute(sql, params).fetchall()` を呼び出して全結果行をリストで返す。`params` の形式は `execute()` と同じ (tuple または dict)。

#### SQLiteHelper.commit

```python
def commit(self) -> None
```

`self.conn.commit()` を呼び出して現在のトランザクションをコミット。

#### SQLiteHelper.execute

```python
def execute(self, sql: str, params: dict | tuple = ()) -> sqlite3.Cursor
```

| `params` の形式 | プレースホルダ構文 | 例 |
|---|---|---|
| `tuple` | `?` (位置) | `db.execute("SELECT * FROM t WHERE id = ?", (1,))` |
| `dict` (ハッシュ) | `:name` (名前付き) | `db.execute("SELECT * FROM t WHERE id = :id", {"id": 1})` |

#### SQLiteHelper.close

```python
def close(self) -> None
```

`self.conn` が開いていれば閉じて `None` にリセット。`with` ブロック (`__exit__`) から自動的に呼ばれる。`self.conn` が `None` の場合は何もしない (冪等)。

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

どちらも `@contextmanager` — `with db.begin_immediate():` の形式で使用。例外発生時は自動的に `ROLLBACK`。

#### SQLiteHelper.health_check

```python
metrics = SQLiteHelper("rag").open().health_check()
# {"journal_mode": "wal", "integrity": "ok", "page_count": 1024,
#  "page_size": 4096, "freelist_count": 10, "db_size_bytes": 4194304}
```

`PRAGMA quick_check` (高速版 integrity check) を実行し、journal mode / integrity / page stats を dict で返す。`/db health` コマンドから呼ばれる。

#### SQLiteHelper.checkpoint

```python
result = db.checkpoint(mode="TRUNCATE")
# {"busy": 0, "pages_in_wal": 512, "pages_checkpointed": 512}
```

| mode | 動作 |
|---|---|
| `PASSIVE` | リーダーを待たずにフラッシュ (非ブロッキング) |
| `FULL` | 全リーダー終了後にフラッシュ |
| `RESTART` | FULL + WAL 書き込み位置をリセット |
| `TRUNCATE` | RESTART + WAL を 0 バイトに切り詰め (デフォルト。大量書き込み後のディスク回収に使用) |

#### SQLiteHelper.vacuum

```python
db.vacuum()
```

`VACUUM` を実行してDBファイルをインプレース再構築。空きページを回収してデフラグ。実行にはDB サイズの約2倍の空きディスクが必要。トランザクション外で呼ぶこと。

### 使用スクリプト

| スクリプト | target | 使用内容 |
|---|---|---|
| `create_schema.py` | `"rag"` / `"session"` | `create_rag_schema()` / `create_session_schema()` |
| `migrate_db.py` | 両方 | rag.sqlite の session テーブルを session.sqlite に一回限り移行 |
| `rag/ingestion/ingester.py` | `"rag"` | `with SQLiteHelper("rag").open(write_mode=True) as db:` — 一括投入 |
| `agent/repl.py` | `"rag"` | `with SQLiteHelper("rag").open(row_factory=True) as db:` (rag/pipeline.py 経由) |
| `agent/session.py` | `"session"` | `with SQLiteHelper("session").open(write_mode=True) as db:` — セッション/メッセージ操作 |
| `agent/memory/store.py` | `"session"` | `with SQLiteHelper("session").open(...) as db:` — メモリ層 |
| `db/tool_results.py` | `"session"` | `with SQLiteHelper("session").open(...) as db:` — ツール結果保存 |
| `rag/pipeline.py` | `"rag"` | `fetchall(...)` — `vector_search` / `fts_search` が SQLiteHelper を受け取る |
