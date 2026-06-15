# MCP プロトコル層モジュール

MCP (Model Context Protocol) サーバとのプロトコル通信を担うモジュール群。

| モジュール | 役割 |
|---|---|
| `mcp/models.py` | `/v1/call_tool` 統合エンドポイント共通 Pydantic モデル |
| `mcp/server.py` | MCP サーバ HTTP/stdio 起動共通基底クラス |
| `mcp/dispatch.py` | `dispatch_tool()` — ディスパッチテーブル経由のツール呼び出しヘルパー |
| `mcp/audit.py` | `_audit_log()` — 構造化監査ログ出力ヘルパー |
| `shared/mcp_config.py` | `McpServerConfig` データクラス — 1 サーバのトランスポート設定を保持 |
| `shared/tool_constants.py` | MCP ツール分類 frozenset の正規定義 (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT) |
| `shared/route_resolver.py` | `ToolRouteResolver` — config-driven + 静的プレフィックス fallback ルーティング |
| `shared/tool_executor.py` | `ToolExecutor` — トランスポート透過的なツール実行・TTL キャッシュ・lifecycle 連携 |

---

## 1. mcp/models.py

### 1.1 機能概要

`mcp/file/read_server.py` / `mcp/file/write_server.py` / `mcp/file/delete_server.py` / `mcp/web_search/server.py` / `mcp/github/server.py` の `/v1/call_tool` 統合エンドポイントで共用する Pydantic モデルを定義。各サーバで同一のリクエスト/レスポンス型を共有することで重複を排除。

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

MCP サーバの HTTP 起動ロジックを提供する基底クラス。`mcp/file/read_server.py` / `mcp/file/write_server.py` / `mcp/file/delete_server.py` / `mcp/web_search/server.py` / `mcp/github/server.py` などが継承。`run_http()` は uvicorn で HTTP サーバを起動。

### 2.2 クラス属性

サブクラスはクラス属性として以下を宣言する:

| クラス属性 | 型 | 説明 |
|---|---|---|
| `server_name` | `str` | サーバ識別名 (例: `"web-search-mcp"`) |
| `server_version` | `str` | バージョン文字列 (例: `"3.0.0"`) |
| `http_host` | `str` | HTTP 待受ホスト (デフォルト: `"127.0.0.1"`) |
| `http_port` | `int` | HTTP 待受ポート番号 (例: `8004`) |
| `app_module` | `str` | uvicorn 起動ターゲット (例: `"web_search_mcp_server:app"`) |
| `mcp_tools` | `list[dict[str, Any]]` | `tools/list` レスポンスに返すツール定義リスト |

### 2.3 モジュールレベル関数

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `_truncate_with_meta(text, max_bytes=MCP_MAX_RESPONSE_BYTES) -> TruncationResult` | `(text: str, max_bytes: int = 524288) -> TruncationResult` | テキストを UTF-8 バイト単位で `max_bytes` に切り詰め、`TruncationResult(text, truncated, total_bytes)` を返す。stdio モードのレスポンスサイズ制限に使用 |
| `attach_auth_middleware(app, token) -> None` | `(app: Any, token: str) -> None` | FastAPI アプリに Bearer トークン認証 + `X-Request-Id` レスポンスヘッダ注入ミドルウェアを登録する。`token` が非空のとき `Authorization: Bearer <token>` ヘッダが一致しないリクエストには 401 を返す。`token` が空のとき認証チェックをスキップし、`X-Request-Id` ヘッダのみ注入する |

### 2.4 API

| メソッド | 説明 |
|---|---|
| `async dispatch(name, args) -> DispatchResult` | ツール呼び出しを処理する抽象メソッド。サブクラスが必ずオーバーライド。`DispatchResult(output, is_error)` dataclass を返す。未実装の場合は `NotImplementedError` を送出する |
| `list_tools() -> list[str]` | `mcp_tools` クラス属性 (またはインスタンス属性) からツール名リストを返す。`mcp_tools` 未定義なら空リスト |
| `health() -> dict[str, str]` | `{"status": "ok"}` を返す。HTTP サブクラスでオーバーライド (例: github-mcp は `{"status":"ok","github_token":"set"}` / `"not_set"` 追加)。stdio サブクラスはプロセス生存確認を使用 |
| `run_http() -> None` | uvicorn で HTTP サーバを起動する主要メソッド |
| `async run_stdio() -> None` | stdin/stdout で行区切り JSON-RPC を処理。リクエスト形式: `{"id": <int>, "name": <str>, "args": {}}` / レスポンス形式: `{"id": <int>, "result": <str>, "is_error": <bool>, "truncated": <bool>, "total_bytes": <int>}`。`__list_tools__` を予約 RPC として intercept しツール名リストを返す。stdin EOF でループを終了する |

### 2.5 サブクラス実装パターン

```python
from mcp.server import MCPServer

class WebSearchMCPServer(MCPServer):
    server_name    = "web-search-mcp"
    server_version = "3.0.0"
    http_port      = 8004
    app_module     = "web_search_mcp_server:app"  # uvicorn 起動ターゲット
    mcp_tools      = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict) -> DispatchResult:
        return await _dispatch_web_tool(name, args)

if __name__ == "__main__":
    WebSearchMCPServer().run_http()
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
from shared.mcp_config import McpServerConfig  # shared/mcp_config.py; re-exported from agent/config.py

server_configs = {
    "web_search":  McpServerConfig(transport="http", url="http://127.0.0.1:8004", cmd=[], openrc_service="web-search-mcp"),
    "file_read":   McpServerConfig(transport="http", url="http://127.0.0.1:8005", cmd=[], openrc_service="file-read-mcp"),
    "file_write":  McpServerConfig(transport="http", url="http://127.0.0.1:8007", cmd=[], openrc_service="file-write-mcp"),
    "file_delete": McpServerConfig(transport="http", url="http://127.0.0.1:8008", cmd=[], openrc_service="file-delete-mcp"),
    "github":      McpServerConfig(transport="http", url="http://127.0.0.1:8006", cmd=[], openrc_service="github-mcp"),
}
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    cache_ttl=300.0,
    server_configs=server_configs,
    cache_max_size=200,
    concurrency_limits={"file_write": 1},  # optional per-server limit
)
res: ToolCallResult = await executor.execute("read_text_file", {"path": "/opt/llm/..."})
# res.output, res.is_error, res.request_id, res.server_key
```

#### LifecycleProtocol

`shared/tool_executor.py` に定義された `typing.Protocol`。`factory.py` の `_ServerLifecycleRouter` が実装する。`agent/lifecycle.py` の `restart_stdio()` は残存 (非推奨)。

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `ensure_ready` | `async (server_key: str) -> None` | 指定サーバーが呼び出し可能な状態であることを保証する。ondemand stdio サーバを初回呼び出し時に自動起動する |

#### _ServerLifecycleRouter

`factory.py`。HTTP subprocess と stdio サーバのルーティングを一元管理。`LifecycleProtocol` を実装し `ToolExecutor.set_lifecycle()` で注入する。`AgentREPL._init_components()` で生成し `ctx.services.lifecycle` として保持する。

**コンストラクタ:**

```python
_ServerLifecycleRouter(
    server_configs: dict[str, McpServerConfig],
    tool_executor: ToolExecutor,
    stdio_procs: dict[str, StdioTransport],
)
```

**主要メソッド:**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `ensure_ready` | `async (server_key: str) -> None` | `http+subprocess` → `_verify_http_subprocess()` で生死確認 (起動はしない)。`persistent` stdio → no-op。`ondemand` stdio → `_ensure_ondemand_stdio()` で per-server `asyncio.Lock` によるダブルチェックロッキングで単一起動を保証 |
| `shutdown_all` | `async () -> None` | 実行中のすべての stdio サーバを停止する |
| `shutdown_idle` | `async () -> None` | `idle_timeout_sec` を超えたアイドル ondemand サーバを停止する |

**ensure_ready の内部フロー (ondemand):**

1. ロック取得前に `transport.is_alive()` をチェック (fast path)
2. per-server `asyncio.Lock` を取得 (`_start_locks.setdefault(server_key, asyncio.Lock())`)
3. ロック取得後に再度 `transport.is_alive()` をチェック (double-check)
4. 未起動の場合のみ `StdioTransport.start()` を呼び出し、`tool_executor.set_transport()` で登録する

#### HttpTransport

`shared/tool_executor.py`。HTTP MCP サーバーへの非同期 POST を担当。

**コンストラクタ:**

```python
HttpTransport(
    http: httpx.AsyncClient,
    base_url: str,
    server_key: str,
    cfg: McpServerConfig | None = None,
)
```

- `cfg.auth_token` が非空のとき `Authorization: Bearer <token>` ヘッダを付与する
- `cfg` が `None` のとき認証なし

**主要メソッド:**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `call` | `async (name: str, args: dict[str, Any]) -> ToolCallResult` | `POST /v1/call_tool` を実行し `ToolCallResult(output, is_error, request_id, server_key)` を返す。`httpx.HTTPStatusError` / `httpx.RequestError` / その他例外はすべてキャッチし `is_error=True` で返す |

#### StdioTransport

`shared/tool_executor.py`。stdin/stdout 経由の行区切り JSON-RPC でサブプロセス MCP サーバーを呼び出す。per-instance `asyncio.Lock` で同時呼び出しをシリアル化する。

**コンストラクタ:**

```python
StdioTransport(
    cmd: list[str],
    server_key: str,
    working_dir: str = "",
    env: dict[str, str] | None = None,
)
```

- `working_dir` が非空のとき `start()` 前に `Path(working_dir).is_dir()` を確認し、存在しなければ `ValueError`
- `env` が非空のとき `{**os.environ, **env}` でマージしてサブプロセスに渡す

**主要メソッド:**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `start` | `async () -> None` | サブプロセスを起動する。既に生存中なら no-op |
| `is_alive` | `() -> bool` | サブプロセスが実行中 (`returncode is None`) のとき `True` |
| `call` | `async (name: str, args: dict[str, Any]) -> ToolCallResult` | JSON-RPC リクエストを送信し `ToolCallResult(output, is_error, request_id, server_key)` を返す。`request_id` は常に `""`。タイムアウト (`_STDIO_CALL_TIMEOUT = 60.0` 秒) / 未起動 / 不正レスポンスはいずれも `is_error=True` で返す |
| `stop` | `async () -> None` | stdin クローズ → 5 秒 wait → `terminate()` → 3 秒 wait → `kill()` の順で終了処理 |

#### ToolRouteResolver

`shared/route_resolver.py`。ツール名 → サーバーキーの解決を担当。

**コンストラクタ:**

```python
ToolRouteResolver(server_configs: dict[str, McpServerConfig])
```

コンストラクタで `cfg.tool_names` から逆引きマップ (`tool_name -> server_key`) を構築する。

**主要メソッド:**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `resolve` | `(tool_name: str) -> str` | config-driven マップを検索し、見つからなければ `_fallback_route()` にフォールバック。いずれにも該当しない場合は `ValueError` |
| `_fallback_route` | `(tool_name: str) -> str` | `shared/tool_constants.py` の frozenset と文字列一致で静的ルーティング |

#### ToolExecutor

`shared/tool_executor.py`。`ToolRouteResolver` でルーティングし、TTL キャッシュ付きでツール呼び出しを実行する中心クラス。

**コンストラクタ:**

```python
ToolExecutor(
    http: httpx.AsyncClient,
    cache_ttl: float,
    server_configs: dict[str, McpServerConfig],
    cache_max_size: int = 0,
    concurrency_limits: dict[str, int] | None = None,
    lifecycle: LifecycleProtocol | None = None,
)
```

- HTTP サーバーは構築時に `HttpTransport` を生成する
- stdio サーバーのトランスポートは `None` で初期化され、`set_transport()` で後から登録する
- `cache_max_size=0` のときキャッシュサイズ上限なし
- `concurrency_limits`: サーバーキー → 最大同時実行数。`asyncio.Semaphore` を `_raw_execute()` 内で遅延生成する
- `concurrency_limits` に存在しないサーバーキーが指定された場合は警告ログのみ (エラーにならない)

**主要メソッド:**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `set_transport` | `(server_key: str, transport: StdioTransport) -> None` | 起動済み `StdioTransport` を指定サーバーキーに登録する |
| `set_lifecycle` | `(lifecycle: LifecycleProtocol | None) -> None` | 構築後に lifecycle manager を注入・差し替える |
| `execute` | `async (tool_name: str, args: dict[str, Any]) -> ToolCallResult` | プラグインツールを優先確認し、次いでキャッシュ付きで MCP ツール実行する。戻り値は `ToolCallResult(output, is_error, request_id, server_key)` |
| `clear_cache` | `() -> None` | キャッシュエントリをすべて削除する |

**キャッシュ仕様:**
- 成功結果 (`is_error=False`) のみキャッシュする
- キャッシュキーは `tool_name + orjson(args, OPT_SORT_KEYS)`
- `cache_ttl` 秒を超えたエントリはミス扱いでキャッシュから削除される
- `cache_max_size > 0` のとき LRU で古いエントリを evict する
- キャッシュヒット時の `x_request_id` は `""` (ライブリクエストなし)

**副作用ツールの判定 (`is_side_effect`):**

`_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})` が定義されており、`is_side_effect(tool_name: str) -> bool` でチェックできる。`execute_all_tool_calls()` (呼び出し元) が副作用ツールを含む場合は並列実行をシリアルに切り替える。

**plugin tool サポート**

`@register_tool("tool_name")` で登録したローカル Python 関数は、`execute()` 内で最初に照合する。マッチした場合はキャッシュおよび MCP ルーティングをスキップして直接呼び出す。戻り値は `tuple[str, bool]` (result_text, is_error)。

```python
from plugin_registry import register_tool

@register_tool("my_tool")
async def my_tool(args: dict) -> tuple[str, bool]:
    return "result", False
```

**並行数制限 (concurrency_limits)**

`ToolExecutor(concurrency_limits={"file_write": 1})` のように渡すと、指定したサーバキーへの同時呼び出しを `asyncio.Semaphore` で制限する。Semaphore はイベントループ生成後に遅延初期化する。不明なサーバキーは `logger.warning` を出力してスルーする (`ValueError` にはしない)。

ルーティング規則 (`ToolRouteResolver.resolve()`):

1. **config-driven**: `McpServerConfig.tool_names` にツール名が列挙されているサーバを優先
2. **静的 fallback** (tool_names が空のとき、`shared/tool_constants.py` の frozenset を使用):
    - `READ_TOOLS` (`list_directory`, `read_text_file`, …) → `"file_read"`
    - `WRITE_TOOLS` (`write_file`, `edit_file`, `create_directory`, `move_file`) → `"file_write"`
    - `DELETE_TOOLS` (`delete_file`, `delete_directory`) → `"file_delete"`
    - `shell_run` → `"shell"`
    - `search_web` → `"web_search"`
    - `github_*` → `"github"`
    - `RAG_TOOLS` (`rag_run_pipeline`, `rag_debug_pipeline`) → `"rag_pipeline"`
    - `CICD_TOOLS` (`trigger_workflow`, `get_workflow_runs`, `get_workflow_status`, `get_workflow_logs`) → `"cicd"`
    - `MDQ_TOOLS` (`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`) → `"mdq"`
    - `GIT_TOOLS` (`git_status`, `git_log`, `git_diff`, `git_branch`, `git_show`, `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push`) → `"git"`
    - `query_sqlite` → `"sqlite"`（ただし `tool_constants.py` には含まれず、`route_resolver.py` の `_SET_ROUTES` で prefix ルールとして定義）
    - いずれにも該当しない → `ValueError` を送出 (未知のツール名は登録必須)

**plugin tool サポート**

`@register_tool("tool_name")` で登録したローカル Python 関数は、`execute()` 内で最初に照合する。マッチした場合はキャッシュおよび MCP ルーティングをスキップして直接呼び出す。戻り値は `tuple[str, bool]` (result_text, is_error)。

```python
from plugin_registry import register_tool

@register_tool("my_tool")
async def my_tool(args: dict) -> tuple[str, bool]:
    return "result", False
```

**並行数制限 (concurrency_limits)**

`ToolExecutor(concurrency_limits={"file_write": 1})` のように渡すと、指定したサーバキーへの同時呼び出しを `asyncio.Semaphore` で制限する。Semaphore はイベントループ生成後に遅延初期化する。不明なサーバキーは `logger.warning` を出力してスルーする (`ValueError` にはしない)。サーバキーは `server_configs` に登録されているキー (例: `file_read` / `file_write` / `file_delete` / `shell` / `web_search` / `github` / `rag_pipeline` / `sqlite` / `cicd` / `mdq` / `git`) と一致する必要がある。

統計属性:
- `stat_cache_hits: int` — セッション通算キャッシュヒット回数

**副作用ツールの判定 (`is_side_effect`):**

`_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})` が定義されており、`is_side_effect(tool_name: str) -> bool` でチェックできる。`execute_all_tool_calls()` (呼び出し元) が副作用ツールを含む場合は並列実行をシリアルに切り替える。

モジュールレベルユーティリティ:

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `is_side_effect` | `(tool_name: str) -> bool` | `_SIDE_EFFECT_TOOLS` (`WRITE_TOOLS | DELETE_TOOLS | {"shell_run"}`) に含まれるとき `True` を返す |
| `tool_call_key` | `(name: str, args: dict[str, Any]) -> str` | `(tool_name, args)` ペアを dict キー順正規化した上で MD5 ハッシュ化し文字列で返す。重複排除用の一意キー生成に使用 (非セキュリティ用途) |
| `format_transport_error` | `(*, source, phase, kind, url, status_code, retryable, partial) -> TransportErrorInfo` | LLM / ツール トランスポート失敗を `TransportErrorInfo(summary, detail)` dataclass に整形する。`summary` はユーザー向け一行メッセージ、`detail` は orjson シリアライズされた JSON 文字列 |

### 3.3 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/factory.py` | `build_agent_context()` で `ToolExecutor` を生成し `ctx.services.tools` に保持。`_start_subprocess_servers()` で persistent stdio / HTTP subprocess サーバを起動後に `set_transport()` で登録。routing は `_ServerLifecycleRouter` が担当 |

---

## 4. shared/tool_constants.py

MCP ツール分類 frozenset の正規定義。詳細は [`06_ref-infra.md`](06_ref-infra.md) §7 を参照。`route_resolver.py` / `tool_executor.py` / `tool_runner.py` の 3 箇所で参照する。

---

## 5. shared/route_resolver.py

ツール名 → サーバキー変換ロジック。詳細は [`06_ref-infra.md`](06_ref-infra.md) §8 を参照。

---

## 6. shared/mcp_config.py

### 6.1 機能概要

1 つの MCP サーバのトランスポート設定を保持するデータクラス。`agent/config.py` から re-export される。`_build_mcp_servers()` が `agent.toml` の `[mcp_servers.*]` セクションを解析して `dict[str, McpServerConfig]` を構築する。

### 6.2 McpServerConfig フィールド

詳細は [`05_ref-agent-config.md`](05_ref-agent-config.md) §2 を参照（フィールド一覧・バリデーション・起動モード・working_dir/env ルール・tool_names ルーティング）。

### 6.3 McpServerHealthRegistry

`ToolExecutor` に注入されるサーバヘルス状態追跡クラス。連続障害回数が閾値 (既定 3) を超えると `UNAVAILABLE` 状態になり、`ToolExecutor._raw_execute()` でディスパッチがブロックされる。

| メソッド | 説明 |
|---|---|
| `record_failure(server_key)` | 障害を記録。閾値未満なら `DEGRADED`、以上なら `UNAVAILABLE` を返す |
| `record_success(server_key)` | 成功を記録。状態を `HEALTHY` にリセットし障害回数を 0 にする |
| `get_state(server_key)` | 現在の健康状態を返す。未登録なら `HEALTHY` |
| `is_unavailable(server_key)` | `UNAVAILABLE` 状態なら `True` |

---

## 7. mcp/dispatch.py

### 7.1 機能概要

MCP ツールディスパッチテーブル経由のツール呼び出しヘルパー。`mcp/server.py` から Phase D で分離。MCP サーバが `MCPServer` 基底クラス全体を import せずに `dispatch_tool` を利用できるようにするための独立モジュール。

### 7.2 API

```python
from mcp.dispatch import ToolArgs, dispatch_tool
# ToolArgs は mcp/server.py と mcp/dispatch.py の両方で定義 (同一型)
```

型エイリアス:

| エイリアス | 定義 | 説明 |
|---|---|---|
| `ToolArgs` | `dict[str, Any]` | MCP ツール引数辞書の型エイリアス。ディスパッチテーブルのシグネチャを統一するために使用。`mcp/dispatch.py:16` で定義され、`mcp/server.py:27` でも同義の型エイリアスが定義されている |

関数:

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `dispatch_tool` | `async (table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]], name: str, args: ToolArgs) -> DispatchResult` | ディスパッチテーブル経由でツール呼び出しを実行し `DispatchResult(output, is_error)` dataclass を返す。`name` が空文字または空白文字のみのとき `("Tool name must be a non-empty string", True)` を返す。未知のツール名は `("Unknown tool: <name>", True)` を返す。`ValueError` はバリデーションエラーとして `("Validation error: <e>", True)` に変換。その他の例外 (RuntimeError, IOError, HTTPException など) は呼び出し元に伝搬する |

各 MCP サーバの `_dispatch_*_tool()` 関数が `dispatch_tool` を使用。

---

## 9. mcp/audit.py

### 9.1 機能概要

MCP サーバ向け構造化監査ログ出力ヘルパー。`mcp/server.py` から Phase D で分離。

### 9.2 API

```python
from mcp.audit import _audit_log
```

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `_audit_log` | `(server_logger: Any, session_id: str, request_id: str, action: str, target: str, outcome: str, detail: str = "") -> None` | `server_logger.info()` 経由で `AUDIT session=... request=... action=... target=... outcome=... detail=...` 形式の構造化ログ行を 1 行出力する |

| パラメータ | 説明 |
|---|---|
| `server_logger` | サーバモジュール固有の `logging.Logger` インスタンス |
| `session_id` | セッション識別子。空のとき `"-"` で出力 |
| `request_id` | リクエスト識別子 (`X-Request-Id`)。空のとき `"-"` で出力 |
| `action` | 操作種別 (例: `"call_tool"`) |
| `target` | 操作対象 (例: ツール名、ファイルパス) |
| `outcome` | 結果 (例: `"ok"`, `"error"`) |
| `detail` | 補足情報 (省略可) |

---
