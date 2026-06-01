# インフラ共通モジュール

`scripts/` に配置されたインフラ共通ユーティリティ群。依存なし (他の `06_ref-*.md` に依存しない底辺レイヤ)。

| モジュール | 役割 |
|---|---|
| `shared/config_loader.py` | JSON 設定ファイルの読込・マージ |
| `rag/utils.py` | テキスト正規化・埋込 BLOB 変換 |
| `shared/logger.py` | ロギング共通セットアップ |
| `shared/formatters.py` | MCP ツール結果・ログメッセージ共通フォーマットユーティリティ |
| `shared/otel_tracer.py` | OpenTelemetry トレーサー初期化 (`build_tracer()`) |
| `shared/git_helper.py` | ローカル git リポジトリメタデータ取得 (`get_repo_info()`) |
| `shared/tool_constants.py` | ツール分類の正規 `frozenset` 定義 (`READ_TOOLS` / `WRITE_TOOLS` / `DELETE_TOOLS` / `RAG_TOOLS` / `CICD_TOOLS` / `MDQ_TOOLS` / `GIT_TOOLS`) |
| `shared/route_resolver.py` | ツール名 → サーバキーのマッピング (`ToolRouteResolver`) |

SQLite 接続マネージャ → [`docs/06_ref-sqlite.md`](06_ref-sqlite.md)

---

## 1. config_loader.py

### 1.1 機能概要

`config/` ディレクトリ内の JSON ファイルを読み込んで辞書にマージ。
`_` で始まるキー (例: `_doc`) はドキュメントメタデータとして除外。

### 1.2 API

```python
from shared.config_loader import ConfigLoader

cfg = ConfigLoader().load("common.toml", "agent.toml")
```

| クラス / メソッド | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `ConfigLoader(config_dir=None)` | `config_dir: Path` — 省略時はスクリプト 2 階層上の `config/` | `ConfigLoader` | インスタンスを生成 |
| `ConfigLoader.load(*names)` | `names: str` — `config/` 相対のファイル名 (複数可) | `dict[str, Any]` | TOML ファイルを順に読み込んでマージ。後から読んだキーで上書き。ファイル未存在・TOML 不正の場合は `ValueError` を送出 |

### 1.3 設定ファイルの検索パス

スクリプトファイルの 2 階層上の `config/` ディレクトリを使用:

```
/opt/llm/scripts/config_loader.py
         ↑2つ上
/opt/llm/config/
```

### 1.4 使用スクリプト

全スクリプト (`rag/ingestion/crawler.py`, `rag/ingestion/chunk_splitter.py`, `rag/ingestion/ingester.py`, `create_schema.py`, `agent.py` など)

---

## 2. rag/utils.py

### 2.1 機能概要

RAG 取込パイプライン (`rag/ingestion/crawler.py`, `rag/ingestion/chunk_splitter.py`, `rag/ingestion/ingester.py`) とベクトル検索 (`rag/pipeline.py`) で共用するテキスト処理ユーティリティ。

### 2.2 API

```python
from rag.utils import normalize_unicode, floats_to_blob, validate_url
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
| `rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
| `rag/pipeline.py` | `floats_to_blob` |
| `rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `rag/ingestion/crawler.py` | `validate_url` |

---

## 3. logger.py

### 3.1 機能概要

エントリスクリプト専用のロギングセットアップクラス。`FileHandler` と `StreamHandler` を名前付きロガーに直接付与することで、複数のエントリスクリプトがそれぞれ独立したログファイルに書き込める。`propagate=False` でルートロガーへの伝播を遮断し重複出力を防止。

`structured_log=True` を指定するとすべてのハンドラが JSON Lines フォーマット (`_JsonFormatter`) に切り替わり、1 行 1 エントリの構造化ログを出力する。監査ログ (`audit.log`) のように機械処理を前提とするログファイルに使用する。

`set_context()` / `clear_context()` はターン境界でコンテキストフィールド (`turn_id` / `session_id` / `rag_query_id`) を全レコードに自動付与する。実装は `_ContextFilter` (内部クラス) が `logging.Filter.filter()` でフィールドを `LogRecord` に注入する。

### 3.2 API

```python
from shared.logger import Logger

# 通常ロギング (テキスト形式)
logger = Logger(__name__, "/opt/llm/logs/agent.log")

# 構造化ロギング (JSON Lines 形式)
audit = Logger(__name__, "/opt/llm/logs/audit.log", structured_log=True)
audit.set_context(turn_id="abc", session_id="1")
audit.clear_context()
```

| クラス / メソッド | シグネチャ | 説明 |
|---|---|---|
| `Logger(name, log_file, *, structured_log=False)` | `name: str`, `log_file: str`, `structured_log: bool` | 名前付きロガーに `FileHandler` と `StreamHandler` を付与し `propagate=False` に設定。`name` または `log_file` が空文字列の場合は `ValueError` を送出 |
| `Logger.set_context(**fields)` | `**fields: Any` — `turn_id` / `session_id` / `rag_query_id` など | 以降のすべてのログレコードに指定フィールドを注入。`None` 値のキーは除外される |
| `Logger.clear_context()` | — | 注入済みコンテキストフィールドをすべてクリアする |
| `Logger.info / warning / error / exception / debug` | `msg: str, *args, **kwargs` | 内部 `logging.Logger` の同名メソッドに委譲 (`__getattr__` 経由) |

### 3.3 ログ設定

#### テキスト形式 (`structured_log=False`、デフォルト)

| 項目 | 値 |
|---|---|
| レベル | `INFO` |
| フォーマット | `%(asctime)s %(levelname)s [%(funcName)s] %(message)s` |
| ハンドラ 1 | `FileHandler(log_file)` — 指定ファイルに出力 |
| ハンドラ 2 | `StreamHandler(sys.stderr)` — stderr にも同時出力 |
| propagate | `False` — ルートロガーへの伝播を遮断 |

#### JSON Lines 形式 (`structured_log=True`)

| 項目 | 値 |
|---|---|
| レベル | `INFO` |
| フォーマット | `_JsonFormatter` — 1 行 1 エントリ (orjson でシリアライズ) |
| JSON フィールド | `ts` / `level` / `func` / `msg` に加え、コンテキストキー (`turn_id` / `session_id` / `rag_query_id`) を条件付きで出力。例外発生時は `exc` を追加 |
| ハンドラ 1 | `FileHandler(log_file)` |
| ハンドラ 2 | `StreamHandler(sys.stderr)` |
| propagate | `False` |

ログファイルが開けない場合は stderr 出力のみにフォールバック。同一プロセス内で同じ `name` で 2 回目の `Logger()` を生成してもハンドラが重複付与されないよう (`self._logger.handlers` チェック) 冪等に動作。

### 3.4 使用パターン

エントリスクリプト (スクリプトごとに異なる log_file を指定):
```python
from shared.logger import Logger
logger = Logger(__name__, "/opt/llm/logs/xxx.log")
```

構造化ログ (監査ログ等):
```python
from shared.logger import Logger
audit = Logger(__name__, "/opt/llm/logs/audit.log", structured_log=True)
audit.set_context(turn_id="t-001", session_id="s-abc")
audit.info("tool executed")  # → {"ts":"...","level":"INFO","func":"...","msg":"tool executed","turn_id":"t-001","session_id":"s-abc"}
audit.clear_context()
```

ライブラリモジュール (エントリスクリプトのロガーが上位で設定済みであることを前提とする):
```python
import logging
logger = logging.getLogger(__name__)
```

### 3.5 ログファイル一覧

`Logger(__name__, log_file)` で直接ログファイルを指定しているスクリプト一覧。

| スクリプト | ログファイル | 備考 |
|---|---|---|
| `db/create_schema.py` | `/opt/llm/logs/create_schema.log` | — |
| `db/migrate.py` | `/opt/llm/logs/migrate_db.log` | — |
| `rag/ingestion/crawler.py` | `/opt/llm/logs/crawl.log` | — |
| `rag/ingestion/chunk_splitter.py` | `/opt/llm/logs/chunk.log` | — |
| `rag/ingestion/chunk_japanese.py` | `/opt/llm/logs/chunk.log` | chunk_splitter と共用 |
| `rag/ingestion/ingester.py` | `/opt/llm/logs/ingest.log` | — |
| `agent/repl.py` | `/opt/llm/logs/agent.log` | — |
| `agent/repl_health.py` | `/opt/llm/logs/agent.log` | repl と共用 |
| `agent/repl_tool_exec.py` | `/opt/llm/logs/agent.log` | repl と共用 |
| `agent/orchestrator.py` | `/opt/llm/logs/agent.log` | repl と共用 |
| `agent/repl.py` (`audit_logger`) | `cfg.audit_log_file` (デフォルト `/opt/llm/logs/audit.log`) | `structured_log=True` (JSON Lines) |
| `mcp/file/read_server.py` | `/opt/llm/logs/file-read-mcp.log` | — |
| `mcp/file/write_server.py` | `/opt/llm/logs/file-write-mcp.log` | — |
| `mcp/file/delete_server.py` | `/opt/llm/logs/file-delete-mcp.log` | — |
| `mcp/web_search/server.py` | `/opt/llm/logs/web-search-mcp.log` | — |
| `mcp/github/server.py` | `/opt/llm/logs/github-mcp.log` | — |
| `mcp/shell/server.py` | `/opt/llm/logs/shell-mcp.log` | — |
| `mcp/rag_pipeline/server.py` | `/opt/llm/logs/rag-mcp.log` | — |
| `mcp/cicd/models.py` | `/opt/llm/logs/cicd-mcp.log` | — |
| `mcp/sqlite/models.py` | `/opt/llm/logs/sqlite-mcp.log` | — |
| `mcp/git/models.py` | `/opt/llm/logs/git-mcp.log` | — |

---

## 4. shared/formatters.py

### 4.1 機能概要

MCP サーバのツール結果テキスト整形と構造化ログ出力に使う共通ユーティリティ。複数の MCP サーバが import。Pure 関数のみで副作用なし。

### 4.2 定数

| 定数 | 型 | 値 | 説明 |
|---|---|---|---|
| `MAX_SNIPPET_CHARS` | `int` | `400` | 検索スニペットの切り詰め上限文字数。`WebSearchMCPServer._fmt_search_result()` が使用する |

### 4.3 API

```python
from shared.formatters import MAX_SNIPPET_CHARS, truncate, fmt_size, fmt_md_link, fmt_kvlog
```

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `truncate` | `(text: str, max_chars: int) -> str` | `text` が `max_chars` を超える場合、`max_chars` 文字で切り詰めて末尾に `"..."` を付与。超えない場合はそのまま返す |
| `fmt_size` | `(size: int) -> str` | バイト数を `"N B"` / `"N KB"` / `"N MB"` に変換して返す。`FileopMCPServer` のディレクトリ一覧エントリで使用する |
| `fmt_md_link` | `(text: str, url: str) -> str` | `[text](url)` 形式の Markdown リンク文字列を返す。`GitHubService.fmt_search_repositories()` が使用する |
| `fmt_kvlog` | `(op: str, **kwargs: object) -> str` | `op=<op> key=val ...` 形式のキーバリューログ文字列を生成。`None` 値のキーは出力に含めない。`logger.info(fmt_kvlog("search", q=..., n=5, ms=12))` のように使う |

### 4.4 fmt_kvlog 出力例

```python
fmt_kvlog("search", q="python asyncio", provider="brave", n=10, ms="12")
# → "op=search q=python asyncio provider=brave n=10 ms=12"

fmt_kvlog("list_directory", path="/opt/llm", n=8, ms="3")
# → "op=list_directory path=/opt/llm n=8 ms=3"

fmt_kvlog("search_try", provider="bing", q="test", n=0, result="zero_results_fallback")
# → "op=search_try provider=bing q=test n=0 result=zero_results_fallback"
```

### 4.5 使用スクリプト

| スクリプト | 使用関数 |
|---|---|
| `mcp/file/read_server.py` | `fmt_kvlog` |
| `mcp/file/read_service.py` | `fmt_size` |
| `mcp/file/write_server.py` | `fmt_kvlog` |
| `mcp/file/delete_server.py` | `fmt_kvlog` |
| `mcp/web_search/server.py` | `MAX_SNIPPET_CHARS`, `truncate`, `fmt_kvlog` |
| `mcp/github/server.py` | `fmt_kvlog` |
| `mcp/github/service.py` | `fmt_md_link` |
| `mcp/shell/server.py` | `fmt_kvlog` |
| `mcp/rag_pipeline/server.py` | `fmt_kvlog` |

---

## 5. shared/otel_tracer.py

### 5.1 機能概要

OpenTelemetry (OTel) トレーサーの初期化ユーティリティ。`build_tracer()` はプライベートな `TracerProvider` インスタンスを生成し、グローバルプロバイダ (`trace.set_tracer_provider()`) を設定しない。これによりテスト間のプロバイダ汚染を防ぎ、同一プロセス内で複数の独立したトレーサーが共存できる。

`enabled=False` のとき、OpenTelemetry SDK をインポートせずに `_NoOpTracer` を返す。SDK がオプション依存のまま維持される。

### 5.2 API

```python
from shared.otel_tracer import build_tracer

tracer = build_tracer(enabled=True, service_name="llm-agent", otlp_endpoint="")
```

| 関数/クラス | シグネチャ | 説明 |
|---|---|---|
| `build_tracer` | `(enabled: bool, service_name: str = "llm-agent", otlp_endpoint: str = "") -> Any` | OTel トレーサー (または `_NoOpTracer`) を生成して返す。グローバルプロバイダは変更しない。`otlp_endpoint` が非空のとき `OTLPSpanExporter` + `BatchSpanProcessor` を使用し、空のとき `ConsoleSpanExporter` + `SimpleSpanProcessor` を使用。`opentelemetry-sdk` 未インストール時は `_NoOpTracer` にフォールバック。OTLP エクスポーター (`opentelemetry-exporter-otlp`) のみ未インストールの場合も `ConsoleSpanExporter` にフォールバックする |
| `_NoOpTracer` | — | `enabled=False` または SDK 未インストール時に返すスタブ。`start_as_current_span(name, **kwargs) -> _NoOpSpan` を実装。呼び出し元は `enabled` フラグを確認する必要がない |
| `_NoOpSpan` | — | コンテキストマネージャプロトコルと `set_attribute(_key, _value)` を実装するスタブ。`__enter__` / `__exit__` / `set_attribute` はすべて無操作 |

#### エクスポーター選択ロジック

```
enabled=False
  → _NoOpTracer (SDKインポートなし)

enabled=True, otlp_endpoint 非空
  → OTLPSpanExporter + BatchSpanProcessor
  ※ opentelemetry-exporter-otlp 未インストール → ConsoleSpanExporter + SimpleSpanProcessor にフォールバック

enabled=True, otlp_endpoint 空
  → ConsoleSpanExporter + SimpleSpanProcessor
```

### 5.3 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `_init_components()` で `build_tracer()` を呼び出し、`ctx.services.tracer` として保持 |

---

## 6. shared/git_helper.py

### 6.1 機能概要

GitPython を使用してローカル git リポジトリのメタデータ (ブランチ名・コミット情報) を取得するユーティリティ。`/context` コマンドの出力に git 情報を追加するために `agent/commands/cmd_context.py` が使用。lazy import でスタートアップ時のオーバーヘッドを抑制する。

### 6.2 API

```python
from shared.git_helper import get_repo_info

info = get_repo_info("/opt/llm")  # git リポジトリ外では None
```

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `get_repo_info` | `(path: str = ".") -> dict[str, Any] \| None` | 現在のブランチと最新コミット情報を返す。git リポジトリ外、または GitPython 例外発生時は `None` を返す。`search_parent_directories=True` で親ディレクトリを遡って検索。HEAD デタッチ時はブランチ名に `"HEAD (detached)"` を返す |

戻り値 dict のフィールド:

| キー | 型 | 説明 |
|---|---|---|
| `branch` | `str` | 現在のブランチ名。デタッチ HEAD の場合は `"HEAD (detached)"` |
| `commit` | `str` | コミットハッシュの先頭 8 文字 |
| `message` | `str` | コミットメッセージの 1 行目 |
| `author` | `str` | コミット作者名 |

### 6.3 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/commands/cmd_context.py` | `/context` コマンドの出力に git ブランチ・コミット情報を追加 |

---

## 7. shared/tool_constants.py

### 7.1 機能概要

MCP ツール分類の正規 `frozenset` 定義を集中管理するモジュール。ツールリストが変更された際にここのみを更新し、参照側での重複定義を防ぐ。

```python
from shared.tool_constants import READ_TOOLS, WRITE_TOOLS, DELETE_TOOLS
from shared.tool_constants import RAG_TOOLS, CICD_TOOLS, MDQ_TOOLS, GIT_TOOLS
```

### 7.2 定義一覧

| frozenset | 説明 | 含まれるツール例 |
|---|---|---|
| `READ_TOOLS` | 読み取り専用ファイル操作ツール | `list_directory` / `read_text_file` / `grep_files` など 9 ツール |
| `WRITE_TOOLS` | ファイル書き込みツール | `write_file` / `edit_file` / `create_directory` / `move_file` |
| `DELETE_TOOLS` | ファイル削除ツール | `delete_file` / `delete_directory` |
| `RAG_TOOLS` | RAG パイプライン MCP ツール | `rag_run_pipeline` / `rag_debug_pipeline` |
| `CICD_TOOLS` | CI/CD 操作ツール (GitHub Actions) | `trigger_workflow` / `get_workflow_runs` / `get_workflow_status` / `get_workflow_logs` |
| `MDQ_TOOLS` | Markdown Context Compression Engine ツール | `search_docs` / `get_chunk` / `outline` / `index_paths` / `refresh_index` / `stats` / `grep_docs` |
| `GIT_TOOLS` | ローカル git 操作ツール (git-mcp, :8014) | `git_status` / `git_log` / `git_diff` / `git_branch` / `git_show` / `git_add` / `git_commit` / `git_checkout` / `git_pull` / `git_push` |

### 7.3 使用スクリプト

| スクリプト | 使用内容 |
|---|---|
| `shared/route_resolver.py` | 静的ルーティング (ツール名 → サーバキー) |
| `shared/tool_executor.py` | 副作用検出 (`is_side_effect()` 関数; `WRITE_TOOLS \| DELETE_TOOLS \| {"shell_run"}` を `_SIDE_EFFECT_TOOLS` として使用) |
| `agent/repl_tool_exec.py` | リスク分類・承認ロジック |

---

## 8. shared/route_resolver.py

### 8.1 機能概要

ツール名からサーバキーへのマッピングを担当する `ToolRouteResolver` クラス。設定ドリブン (`McpServerConfig.tool_names` フィールド) を優先し、設定に含まれない場合は `tool_constants.py` の frozenset を使った静的フォールバックで解決する。

```python
from shared.route_resolver import ToolRouteResolver
from shared.mcp_config import McpServerConfig

resolver = ToolRouteResolver(server_configs)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

### 8.2 API

| クラス / メソッド | シグネチャ | 説明 |
|---|---|---|
| `ToolRouteResolver(server_configs)` | `server_configs: dict[str, McpServerConfig]` | 初期化時に `cfg.tool_names` から逆引き辞書 (`tool_name → server_key`) を構築する |
| `resolve(tool_name)` | `(tool_name: str) -> str` | まず設定マップを参照し、なければ `_fallback_route()` で静的ルーティングを試みる。どちらも一致しない場合は `ValueError` を送出する |
| `_fallback_route(tool_name)` | `(tool_name: str) -> str` | `tool_constants.py` の各 frozenset と `github_` プレフィックスを使った静的フォールバック。`READ_TOOLS` → `"file_read"` / `WRITE_TOOLS` → `"file_write"` / `DELETE_TOOLS` → `"file_delete"` / `"shell_run"` → `"shell"` / `"search_web"` → `"web_search"` / `github_*` → `"github"` / `RAG_TOOLS` → `"rag_pipeline"` / `CICD_TOOLS` → `"cicd"` / `MDQ_TOOLS` → `"mdq"` / `GIT_TOOLS` → `"git"` |

### 8.3 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `shared/tool_executor.py` | `ToolExecutor.__init__()` で `ToolRouteResolver(server_configs)` を生成し、`_raw_execute()` 内でツールのルーティングに使用する |
