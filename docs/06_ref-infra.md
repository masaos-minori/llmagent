# インフラ共通モジュール

`scripts/` に配置されたインフラ共通ユーティリティ群。依存なし (他の `06_ref-*.md` に依存しない底辺レイヤ)。

| モジュール | 役割 |
|---|---|
| `config_loader.py` | JSON 設定ファイルの読込・マージ |
| `rag_utils.py` | テキスト正規化・埋込 BLOB 変換 |
| `sqlite_helper.py` | SQLite 接続ライフサイクル管理と SQL 実行 |
| `logger.py` | ロギング共通セットアップ |
| `formatters.py` | MCP ツール結果・ログメッセージ共通フォーマットユーティリティ |

---

## 1. config_loader.py

### 1.1 機能概要

`config/` ディレクトリ内の JSON ファイルを読み込んで辞書にマージ。
`_` で始まるキー (例: `_doc`) はドキュメントメタデータとして除外。

### 1.2 API

```python
from config_loader import ConfigLoader

cfg = ConfigLoader().load("common.json", "agent.json")
```

| クラス / メソッド | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `ConfigLoader(config_dir=None)` | `config_dir: Path` — 省略時はスクリプト 2 階層上の `config/` | `ConfigLoader` | インスタンスを生成 |
| `ConfigLoader.load(*names)` | `names: str` — `config/` 相対のファイル名 (複数可) | `dict` | JSON ファイルを順に読み込んでマージ。後から読んだキーで上書き。ファイル未存在・JSON 不正の場合は `ValueError` を送出 |

### 1.3 設定ファイルの検索パス

スクリプトファイルの 2 階層上の `config/` ディレクトリを使用:

```
/opt/llm/scripts/config_loader.py
         ↑2つ上
/opt/llm/config/
```

### 1.4 使用スクリプト

全スクリプト (`web_crawler.py`, `chunk_splitter.py`, `rag_ingester.py`, `create_schema.py`, `agent.py` など)

---

## 2. rag_utils.py

### 2.1 機能概要

RAG 取込パイプライン (`web_crawler.py`, `chunk_splitter.py`, `rag_ingester.py`) とベクトル検索 (`agent_rag.py`) で共用するテキスト処理ユーティリティ。

### 2.2 API

```python
from rag_utils import normalize_unicode, floats_to_blob, validate_url
```

| 関数 | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `normalize_unicode(text)` | `text: str` | `str` | NFKC 正規化。全角英数字・異体字を標準形に変換 |
| `floats_to_blob(values)` | `values: list[float]` | `bytes` | float リストを little-endian float32 BLOB に変換 |
| `validate_url(url)` | `url: str` | `bool` | `http`/`https` スキームかつ netloc が空でない場合に `True` を返す |

### 2.3 実装注意

`floats_to_blob` は sqlite-vec の `MATCH` 演算子が要求するバイト形式 (little-endian float32 = `struct.pack("<{N}f", ...)`) で出力。埋込次元が 384 の場合、出力は 384 × 4 = 1536 バイト。

### 2.4 使用スクリプト

| スクリプト | 使用関数 |
|---|---|
| `chunk_splitter.py` | `normalize_unicode` |
| `agent_rag.py` | `floats_to_blob` |
| `rag_ingester.py` | `floats_to_blob`, `validate_url` |
| `web_crawler.py` | `validate_url` |

---

## 3. sqlite_helper.py

### 3.1 機能概要

SQLite (sqlite-vec 拡張付き) の接続ライフサイクル管理と SQL 実行を提供する接続マネージャ。
`rag_ingester.py` / `create_schema.py` / `agent_repl.py` / `agent_session.py` が使用。

### 3.2 クラス定数

```python
from sqlite_helper import SQLiteHelper

print(SQLiteHelper.DB_PATH)
print(SQLiteHelper.SQLITE_VEC_SO)
```

| クラス属性 | 説明 |
|---|---|
| `SQLiteHelper.DB_PATH` | `config/common.json` の `db_path` (例: `/opt/llm/db/rag.sqlite`)。`_ensure_config()` 後に確定する |
| `SQLiteHelper.SQLITE_VEC_SO` | `config/common.json` の `sqlite_vec_so` (例: `/opt/llm/sqlite-vec/vec0.so`)。同上 |

`DB_PATH` / `SQLITE_VEC_SO` はモジュール import 時は空文字列で初期化され、`_ensure_config()` の初回呼び出し時に確定。`open()` は内部で `_ensure_config()` を呼ぶため、接続前に明示的な初期化は不要。外部から表示のみ行う場合 (`/config` コマンド等) は `SQLiteHelper._ensure_config()` を呼んでから参照。`sqlite_timeout` は `open()` 内で `_get_cfg()` から都度取得 (デフォルト: `30`)。

### 3.3 API

```python
from sqlite_helper import SQLiteHelper

# コンテキストマネージャパターン (推奨)
with SQLiteHelper().open(write_mode=True) as db:
    cur  = db.execute("SELECT doc_id FROM documents WHERE url = ?", (url,))
    rows = db.fetchall("SELECT * FROM documents WHERE lang = :lang", {"lang": "ja"})
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

sqlite-vec 拡張をロード済みの接続を `self.conn` に格納し、`self` を返す。拡張ロード後に `enable_load_extension(False)` を呼んでセキュリティを確保。`self` を返すことで `with SQLiteHelper().open(...) as db:` パターンが使用可能。

| キーワード引数 | デフォルト | 説明 |
|---|---|---|
| `write_mode` | `False` | `True` のとき `PRAGMA journal_mode=WAL` と `PRAGMA foreign_keys=ON` を設定 |
| `row_factory` | `False` | `True` のとき `conn.row_factory = sqlite3.Row` を設定し、列名属性アクセスを有効化 |

呼び出しパターン:

| 呼び出し元 | パターン |
|---|---|
| `create_schema.py` | `with SQLiteHelper().open() as db:` — スキーマ作成 |
| `rag_ingester.py` | `db.open(write_mode=True)` — WAL + 外部キー有効 (一括投入のため手動管理) |
| `agent_repl.py` | `with SQLiteHelper().open(row_factory=True) as db:` — RAG クエリごとにオープン/クローズ |
| `agent_session.py` | `with SQLiteHelper().open(write_mode=True) as db:` — セッション永続化 |

#### SQLiteHelper.fetchall

```python
def fetchall(self, sql: str, params: dict | tuple = ()) -> list[Any]
```

`self.conn.execute(sql, params).fetchall()` を呼び出して全結果行をリストで返す。`execute()` + `fetchall()` の合成。`params` の形式は `execute()` と同じ (tuple または dict)。

#### SQLiteHelper.commit

```python
def commit(self) -> None
```

`self.conn.commit()` を呼び出して現在のトランザクションをコミット。

#### SQLiteHelper.execute

```python
def execute(self, sql: str, params: dict | tuple = ()) -> sqlite3.Cursor
```

`self.conn.execute(sql, params)` を呼び出してカーソルを返す。

| `params` の形式 | プレースホルダ構文 | 例 |
|---|---|---|
| `tuple` | `?` (位置) | `db.execute("SELECT * FROM t WHERE id = ?", (1,))` |
| `dict` (ハッシュ) | `:name` (名前付き) | `db.execute("SELECT * FROM t WHERE id = :id", {"id": 1})` |

#### SQLiteHelper.close

```python
def close(self) -> None
```

`self.conn` が開いていれば閉じて `None` にリセット。`with` ブロック (`__exit__`) から自動的に呼ばれる。`self.conn` が `None` の場合は何もしない (冪等)。

### 3.4 使用スクリプト

| スクリプト | 使用内容 |
|---|---|
| `create_schema.py` | `with SQLiteHelper().open() as db:` — `conn.executescript()` |
| `rag_ingester.py` | `with SQLiteHelper().open(write_mode=True) as db:` — `ingest_all` で一括投入 |
| `agent_repl.py` | `with SQLiteHelper().open(row_factory=True) as db:` (agent_rag 経由) |
| `agent_session.py` | `with SQLiteHelper().open(write_mode=True) as db:` — セッション/メッセージ操作 |
| `agent_rag.py` | `fetchall(...)` — `vector_search` / `fts_search` が SQLiteHelper を受け取る |

---

## 4. logger.py

### 4.1 機能概要

エントリスクリプト専用のロギングセットアップクラス。`FileHandler` と `StreamHandler` を名前付きロガーに直接付与することで、複数のエントリスクリプトがそれぞれ独立したログファイルに書き込める。`propagate=False` でルートロガーへの伝播を遮断し重複出力を防止。

### 4.2 API

```python
from logger import Logger

logger = Logger(__name__, "/opt/llm/logs/agent.log")
```

| クラス / メソッド | 引数 | 説明 |
|---|---|---|
| `Logger(name, log_file)` | `name: str` — `__name__` を渡す / `log_file: str` — ログファイルの絶対パス | 名前付きロガーに `FileHandler` と `StreamHandler` を付与し `propagate=False` に設定 |
| `Logger.info / warning / error / exception / debug` | `msg: str, *args, **kwargs` | 内部 `logging.Logger` の同名メソッドに委譲 |

### 4.3 ログ設定

| 項目 | 値 |
|---|---|
| レベル | `INFO` |
| フォーマット | `%(asctime)s %(levelname)s [%(funcName)s] %(message)s` |
| ハンドラ 1 | `FileHandler(log_file)` — 指定ファイルに出力 |
| ハンドラ 2 | `StreamHandler(sys.stderr)` — stderr にも同時出力 |
| propagate | `False` — ルートロガーへの伝播を遮断 |

ログファイルが開けない場合は stderr 出力のみにフォールバック。同一プロセス内で同じ `name` で 2 回目の `Logger()` を生成してもハンドラが重複付与されないよう (`self._logger.handlers` チェック) 冪等に動作。

### 4.4 使用パターン

エントリスクリプト (スクリプトごとに異なる log_file を指定):
```python
from Logger import Logger
logger = Logger(__name__, "/opt/llm/logs/xxx.log")
```

ライブラリモジュール (エントリスクリプトのロガーが上位で設定済みであることを前提とする):
```python
import logging
logger = logging.getLogger(__name__)
```

### 4.5 ログファイル一覧

| スクリプト | ログファイル |
|---|---|
| `create_schema.py` | `/opt/llm/logs/create_schema.log` |
| `web_crawler.py` | `/opt/llm/logs/crawl.log` |
| `chunk_splitter.py` | `/opt/llm/logs/chunk.log` |
| `rag_ingester.py` | `/opt/llm/logs/ingest.log` |
| `agent.py` | `/opt/llm/logs/agent.log` |
| `fileop_mcp_server.py` | `/opt/llm/logs/file-mcp.log` |
| `web_search_mcp_server.py` | `/opt/llm/logs/web-search-mcp.log` |
| `github_mcp_server.py` | `/opt/llm/logs/github-mcp.log` |

---


---

## 5. formatters.py

### 5.1 機能概要

MCP サーバのツール結果テキスト整形と構造化ログ出力に使う共通ユーティリティ。`fileop_mcp_server.py` / `web_search_mcp_server.py` / `github_mcp_server.py` の 3 サーバが import。Pure 関数のみで副作用なし。

### 5.2 定数

| 定数 | 型 | 値 | 説明 |
|---|---|---|---|
| `MAX_SNIPPET_CHARS` | `int` | `400` | 検索スニペットの切り詰め上限文字数。`WebSearchMCPServer._fmt_search_result()` が使用する |

### 5.3 API

```python
from formatters import MAX_SNIPPET_CHARS, truncate, fmt_size, fmt_md_link, fmt_kvlog
```

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `truncate` | `(text: str, max_chars: int) -> str` | `text` が `max_chars` を超える場合、`max_chars` 文字で切り詰めて末尾に `"..."` を付与。超えない場合はそのまま返す |
| `fmt_size` | `(size: int) -> str` | バイト数を `"N B"` / `"N KB"` / `"N MB"` に変換して返す。`FileopMCPServer` のディレクトリ一覧エントリで使用する |
| `fmt_md_link` | `(text: str, url: str) -> str` | `[text](url)` 形式の Markdown リンク文字列を返す。`GitHubService.fmt_search_repositories()` が使用する |
| `fmt_kvlog` | `(op: str, **kwargs: object) -> str` | `op=<op> key=val ...` 形式のキーバリューログ文字列を生成。`None` 値のキーは出力に含めない。`logger.info(fmt_kvlog("search", q=..., n=5, ms=12))` のように使う |

### 5.4 fmt_kvlog 出力例

```python
fmt_kvlog("search", q="python asyncio", provider="brave", n=10, ms="12")
# → "op=search q=python asyncio provider=brave n=10 ms=12"

fmt_kvlog("list_directory", path="/opt/llm", n=8, ms="3")
# → "op=list_directory path=/opt/llm n=8 ms=3"

fmt_kvlog("search_try", provider="bing", q="test", n=0, result="zero_results_fallback")
# → "op=search_try provider=bing q=test n=0 result=zero_results_fallback"
```

### 5.5 使用スクリプト

| スクリプト | 使用関数 |
|---|---|
| `fileop_mcp_server.py` | `fmt_size`, `fmt_kvlog` |
| `web_search_mcp_server.py` | `MAX_SNIPPET_CHARS`, `truncate`, `fmt_kvlog` |
| `github_mcp_server.py` | `fmt_md_link`, `fmt_kvlog` |
