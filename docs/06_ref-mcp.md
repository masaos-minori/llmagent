# MCP プロトコル層モジュール

MCP (Model Context Protocol) サーバとのプロトコル通信を担うモジュール群。

| モジュール | 役割 |
|---|---|
| `mcp_models.py` | `/v1/call_tool` 統合エンドポイント共通 Pydantic モデル |
| `mcp_server.py` | MCP サーバ HTTP 起動共通基底クラス |
| `tool_executor.py` | `ToolExecutor` — MCP HTTP ルーティング・TTL キャッシュ・エラーハンドリング |

---

## 1. mcp_models.py

### 1.1 機能概要

`fileop_mcp_server.py` / `web_search_mcp_server.py` / `github_mcp_server.py` の `/v1/call_tool` 統合エンドポイントで共用する Pydantic モデルを定義。3 サーバで同一のリクエスト/レスポンス型を共有することで重複を排除。

### 1.2 API

```python
from mcp_models import CallToolRequest, CallToolResponse
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
| `web_search_mcp_server.py` | `POST /v1/call_tool` エンドポイントの Request/Response モデル |
| `fileop_mcp_server.py` | `POST /v1/call_tool` エンドポイントの Request/Response モデル |
| `github_mcp_server.py` | `POST /v1/call_tool` エンドポイントの Request/Response モデル |

---

## 2. mcp_server.py

### 2.1 機能概要

MCP サーバの HTTP 起動ロジックを提供する基底クラス。`fileop_mcp_server.py` / `web_search_mcp_server.py` / `github_mcp_server.py` が継承。`run()` は uvicorn で HTTP サーバを起動。

### 2.2 クラス属性

サブクラスはクラス属性として以下を宣言する:

| クラス属性 | 型 | 説明 |
|---|---|---|
| `server_name` | `str` | サーバ識別名 (例: `"web-search-mcp"`) |
| `server_version` | `str` | バージョン文字列 (例: `"3.0.0"`) |
| `http_host` | `str` | HTTP 待受ホスト (デフォルト: `"127.0.0.1"`) |
| `http_port` | `int` | HTTP 待受ポート番号 (例: `8004`) |
| `app_module` | `str` | uvicorn 起動ターゲット (例: `"web_search_mcp_server:app"`) |
| `mcp_tools` | `list[dict]` | `tools/list` レスポンスに返すツール定義リスト |

### 2.3 API

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | ツール呼び出しを処理する抽象メソッド。サブクラスが必ずオーバーライド。`(result_text, is_error)` を返す |
| `run() -> None` | uvicorn で HTTP サーバを起動 |

### 2.4 モジュールレベル関数・型エイリアス

`mcp_server.py` はクラスに加え、型エイリアスとサブクラス共通の dispatch エラーハンドリングをまとめたユーティリティ関数を公開。

```python
from mcp_server import ToolArgs, dispatch_tool
```

型エイリアス:

| エイリアス | 定義 | 説明 |
|---|---|---|
| `ToolArgs` | `dict[str, Any]` | MCP ツール引数辞書の型エイリアス。ディスパッチテーブルのシグネチャを統一するために使用 |

関数:

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `dispatch_tool` | `(table: dict[str, Callable[[ToolArgs], Awaitable[str]]], name: str, args: ToolArgs) -> tuple[str, bool]` | ディスパッチテーブル経由でツール呼び出しを実行し、`(result_text, is_error)` を返す。未知のツール名は `("Unknown tool: <name>", True)` を返す。`FastAPI.HTTPException` はダックタイピング (`hasattr(e, "status_code")`) で検出して HTTP エラーコードとメッセージを返す。それ以外の例外は `("Tool error: <e>", True)` に変換する |

`fileop_mcp_server.py` / `web_search_mcp_server.py` / `github_mcp_server.py` の各 `_dispatch_*_tool()` 関数がこれを使用。

### 2.5 サブクラス実装パターン

```python
from mcp_server import MCPServer

class WebSearchMCPServer(MCPServer):
    server_name    = "web-search-mcp"
    server_version = "3.0.0"
    http_port      = 8004
    app_module     = "web_search_mcp_server:app"
    mcp_tools      = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        return await _dispatch_web_tool(name, args)

if __name__ == "__main__":
    WebSearchMCPServer().run()
```

---


---

## 3. tool_executor.py

### 3.1 機能概要

`AgentREPL` から抽出したツール実行レイヤー。ツール名による MCP サーバルーティング・TTL キャッシュ・エラーハンドリングを担当。`AgentREPL().run()` で `ToolExecutor` インスタンスを生成し、`self._tools` として保持。

2 種類のトランスポートをサポート:
- `HttpTransport` — `httpx.AsyncClient` で HTTP MCP サーバの `/v1/call_tool` を呼び出す
- `StdioTransport` — `asyncio.create_subprocess_exec` でサブプロセスを起動し stdin/stdout 行区切り JSON-RPC で通信する (MCP サーバの `--stdio` フラグ対応)

### 3.2 API

```python
from tool_executor import HttpTransport, StdioTransport, ToolExecutor
from agent_config import McpServerConfig

server_configs = {
    "web_search": McpServerConfig("http", "http://127.0.0.1:8004", [], "web-search-mcp"),
    "file":       McpServerConfig("http", "http://127.0.0.1:8005", [], "file-mcp"),
    "github":     McpServerConfig("http", "http://127.0.0.1:8006", [], "github-mcp"),
}
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    cache_ttl=300.0,
    server_configs=server_configs,
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
| `execute(tool_name, args) -> tuple[str, bool]` | TTL キャッシュを確認し、ヒットすれば返す。なければ `_raw_execute()` を呼んで成功結果を格納 |
| `clear_cache() -> None` | ツール結果キャッシュを全クリア (`/clear` コマンドから呼ばれる) |

ルーティング規則 (`_route()`):
- `search_web` → `"web_search"`
- `github_*` → `"github"`
- その他 → `"file"`

統計属性:
- `stat_cache_hits: int` — セッション通算キャッシュヒット回数

### 3.3 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent_repl.py` | `_init_components()` で `ToolExecutor` を生成し `ctx.tools` に保持。stdio サーバは `_start_stdio_servers()` で起動後に `set_transport()` で登録 |

---

