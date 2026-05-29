# MCP プロトコル層モジュール

MCP (Model Context Protocol) サーバとのプロトコル通信を担うモジュール群。

| モジュール | 役割 |
|---|---|
| `mcp/models.py` | `/v1/call_tool` 統合エンドポイント共通 Pydantic モデル |
| `mcp/server.py` | MCP サーバ HTTP 起動共通基底クラス |
| `shared/tool_executor.py` | `ToolExecutor` — MCP HTTP ルーティング・TTL キャッシュ・エラーハンドリング |

---

## 1. mcp/models.py

### 1.1 機能概要

`mcp/file/server.py` / `mcp/web_search/server.py` / `mcp/github/server.py` の `/v1/call_tool` 統合エンドポイントで共用する Pydantic モデルを定義。各サーバで同一のリクエスト/レスポンス型を共有することで重複を排除。

### 1.2 API

```python
from mcp.models import CallToolRequest, CallToolResponse
```

| クラス | フィールド | 説明 |
|---|---|---|
| `CallToolRequest` | `name: str` | 呼び出すツール名 |
| | `args: dict` | ツール引数 (省略時は空 dict) |
| `CallToolResponse` | `result: str` | フォーマット済み結果テキスト |
| | `is_error: bool` | ツール呼び出しが失敗した場合 `True` |

### 1.3 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `mcp/web_search/server.py` | `POST /v1/call_tool` エンドポイントの Request/Response モデル |
| `mcp/file/read_server.py` / `write_server.py` / `delete_server.py` | `POST /v1/call_tool` エンドポイントの Request/Response モデル |
| `mcp/github/server.py` | `POST /v1/call_tool` エンドポイントの Request/Response モデル |

---

## 2. mcp/server.py

### 2.1 機能概要

MCP サーバの HTTP 起動ロジックを提供する基底クラス。`mcp/file/server.py` / `mcp/web_search/server.py` / `mcp/github/server.py` が継承。`run()` は uvicorn で HTTP サーバを起動。

### 2.2 クラス属性

サブクラスはクラス属性として以下を宣言する:

| クラス属性 | 型 | 説明 |
|---|---|---|
| `server_name` | `str` | サーバ識別名 (例: `"web-search-mcp"`) |
| `server_version` | `str` | バージョン文字列 (例: `"3.0.0"`) |
| `http_host` | `str` | HTTP 待受ホスト (デフォルト: `"127.0.0.1"`) |
| `http_port` | `int` | HTTP 待受ポート番号 (例: `8004`) |
| `app_module` | `str` | uvicorn 起動ターゲット (例: `"mcp.web_search.server:app"`) |
| `mcp_tools` | `list[dict]` | `tools/list` レスポンスに返すツール定義リスト |

### 2.3 API

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | ツール呼び出しを処理する抽象メソッド。サブクラスが必ずオーバーライド。`(result_text, is_error)` を返す |
| `run() -> None` | uvicorn で HTTP サーバを起動 |

### 2.4 モジュールレベル関数・型エイリアス

`mcp/server.py` はクラスに加え、型エイリアスとサブクラス共通の dispatch エラーハンドリングをまとめたユーティリティ関数を公開。

```python
from mcp.server import ToolArgs, dispatch_tool
```

型エイリアス:

| エイリアス | 定義 | 説明 |
|---|---|---|
| `ToolArgs` | `dict[str, Any]` | MCP ツール引数辞書の型エイリアス。ディスパッチテーブルのシグネチャを統一するために使用 |

関数:

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `dispatch_tool` | `(table: dict[str, Callable[[ToolArgs], Awaitable[str]]], name: str, args: ToolArgs) -> tuple[str, bool]` | ディスパッチテーブル経由でツール呼び出しを実行し、`(result_text, is_error)` を返す。未知のツール名は `("Unknown tool: <name>", True)` を返す。`FastAPI.HTTPException` はダックタイピング (`hasattr(e, "status_code")`) で検出して HTTP エラーコードとメッセージを返す。それ以外の例外は `("Tool error: <e>", True)` に変換する |

`mcp/file/server.py` / `mcp/web_search/server.py` / `mcp/github/server.py` の各 `_dispatch_*_tool()` 関数がこれを使用。

### 2.5 サブクラス実装パターン

```python
from mcp.server import MCPServer

class WebSearchMCPServer(MCPServer):
    server_name    = "web-search-mcp"
    server_version = "3.0.0"
    http_port      = 8004
    app_module     = "mcp.web_search.server:app"
    mcp_tools      = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        return await _dispatch_web_tool(name, args)

if __name__ == "__main__":
    WebSearchMCPServer().run()
```

---


---

## 3. shared/tool_executor.py

### 3.1 機能概要

`AgentREPL` から抽出したツール実行レイヤー。ツール名による MCP サーバルーティング・TTL キャッシュ・エラーハンドリングを担当。`AgentREPL._init_components()` で `ToolExecutor` インスタンスを生成し、`ctx.services.tools` として保持。

2 種類のトランスポートをサポート:
- `HttpTransport` — `httpx.AsyncClient` で HTTP MCP サーバの `/v1/call_tool` を呼び出す
- `StdioTransport` — `asyncio.create_subprocess_exec` でサブプロセスを起動し stdin/stdout 行区切り JSON-RPC で通信する (MCP サーバの `--stdio` フラグ対応)

### 3.2 API

```python
from shared.tool_executor import HttpTransport, StdioTransport, ToolExecutor
from agent.config import McpServerConfig

server_configs = {
    "web_search": McpServerConfig("http", "http://127.0.0.1:8004", [], "web-search-mcp"),
    "file_read":  McpServerConfig("http", "http://127.0.0.1:8005", [], "file-mcp"),
    "file_write": McpServerConfig("http", "http://127.0.0.1:8005", [], "file-mcp"),
    "file_delete":McpServerConfig("http", "http://127.0.0.1:8005", [], "file-mcp"),
    "github":     McpServerConfig("http", "http://127.0.0.1:8006", [], "github-mcp"),
}
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    cache_ttl=300.0,
    server_configs=server_configs,
    cache_max_size=200,
    concurrency_limits={"file_write": 1},  # optional per-server limit
)
result, is_error = await executor.execute("read_text_file", {"path": "/opt/llm/..."})
```

`HttpTransport` クラス:

| メソッド | 説明 |
|---|---|
| `call(name, args) -> tuple[str, bool]` | `POST /v1/call_tool` を呼び出す。HTTP エラー / 接続エラー時は `(msg, True)` を返す |

`StdioTransport` クラス:

| メソッド | 説明 |
|---|---|
| `start() -> None` | サブプロセスを起動。既に起動済みなら無操作 |
| `is_alive() -> bool` | サブプロセスが実行中 (returncode is None) なら `True` |
| `call(name, args) -> tuple[str, bool]` | JSON-RPC リクエストを送信して応答を受け取る。タイムアウト (`_STDIO_CALL_TIMEOUT=60s`) で `(msg, True)` を返す |
| `stop() -> None` | stdin をクローズして graceful shutdown。5 秒でタイムアウト後 terminate/kill |

`ToolExecutor` クラス:

| メソッド | 説明 |
|---|---|
| `set_transport(server_key, transport) -> None` | stdio サーバのプロセス起動後に `StdioTransport` を登録 |
| `execute(tool_name, args) -> tuple[str, bool]` | plugin ツール → キャッシュ → `_raw_execute()` の順で解決。成功結果のみキャッシュ |
| `clear_cache() -> None` | ツール結果キャッシュを全クリア (`/clear` コマンドから呼ばれる) |

ルーティング規則 (`_route()`):
- `search_web` → `"web_search"`
- `github_*` → `"github"`
- `shell_run` → `"shell"`
- `write_file`, `edit_file`, `create_directory`, `move_file` → `"file_write"`
- `delete_file`, `delete_directory` → `"file_delete"`
- その他 → `"file_read"`

**plugin tool サポート**

`@register_tool("tool_name")` で登録したローカル Python 関数は、`execute()` 内で最初に照合する。マッチした場合はキャッシュおよび MCP ルーティングをスキップして直接呼び出す。戻り値は `tuple[str, bool]` (result_text, is_error)。

```python
from plugin_registry import register_tool

@register_tool("my_tool")
async def my_tool(args: dict) -> tuple[str, bool]:
    return "result", False
```

**並行数制限 (concurrency_limits)**

`ToolExecutor(concurrency_limits={"file_write": 1})` のように渡すと、指定したサーバキーへの同時呼び出しを `asyncio.Semaphore` で制限する。Semaphore はイベントループ生成後に遅延初期化する。不明なサーバキーは `logger.warning` を出力してスルーする。有効なサーバキー: `file_read` / `file_write` / `file_delete` / `shell` / `web_search` / `github`。

統計属性:
- `stat_cache_hits: int` — セッション通算キャッシュヒット回数

モジュールレベルユーティリティ:

| 関数 | 説明 |
|---|---|
| `is_side_effect(tool_name) -> bool` | write / delete / shell_run ツールのとき `True` を返す。`execute_all_tool_calls()` の直列化判定に使用 |
| `format_transport_error(*, source, phase, kind, url, status_code, retryable, partial) -> dict[str, str]` | LLM / ツール transport 失敗の `{"summary", "detail"}` 辞書を生成 |
| `tool_call_key(name, args) -> str` | `(tool_name, args)` の正規化 MD5 ハッシュキー。dedup 判定で使用 |

### 3.3 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `_init_components()` で `ToolExecutor` を生成し `ctx.tools` に保持。stdio サーバは `_start_stdio_servers()` で起動後に `set_transport()` で登録 |

---

