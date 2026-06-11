# MCP サーバー仕様

## 1. 目的

Model Context Protocol（MCP）に基づいた HTTP および stdio トランスポート対応のツールサーバー群を提供し、エージェントが外部リソース（ファイルシステム・GitHub・Web 検索・SQLite・シェル実行・Git 操作等）に安全にアクセスできるようにする。

---

## 2. スコープ

- **対象コンポーネント:** `mcp/` 配下の全サーバー、`shared/tool_executor.py`、`shared/route_resolver.py`、`shared/mcp_config.py`
- **MCP サーバー:** web-search・file-read/write/delete・github・shell・rag-pipeline・sqlite・cicd・mdq・git（11 サーバー、合計 62 ツール）
- **対象外:** エージェント REPL の内部実装、RAG パイプラインの検索ロジック

---

## 3. 背景

エージェントは外部システムへのアクセスをすべて MCP サーバー経由で行う。これにより、ツールの追加・変更がエージェント本体に影響しない疎結合な設計を実現する。すべての MCP サーバーは HTTP と stdio の両方のトランスポートをサポートする。

---

## 4. 前提条件

1. Python 3.13 以上がインストールされていること。
2. `uv` による依存関係管理が設定済みであること。
3. 各サーバーに必要な認証情報（GITHUB_TOKEN、BRAVE_API_KEY 等）が環境変数として設定されていること。
4. `config/mcp_servers.toml` で各サーバーの接続情報が設定されていること。
5. HTTP モードの場合、OpenRC または直接起動でサーバープロセスが稼働していること。

---

## 5. 制約

| 制約 | 内容 |
|---|---|
| ファイルアクセス | `allowed_dirs` に登録されたパス配下のみアクセス可能 |
| GitHub 操作 | `approval_github_allowed_repos` が空の場合は全リポジトリに操作可 |
| シェル実行 | `command_allowlist` 内のコマンドのみ実行可 |
| SQLite | 読み取り専用（SELECT のみ）、`db_allowlist` 内のデータベースのみ |
| レスポンスサイズ | `MCP_MAX_RESPONSE_BYTES = 512 * 1024`（512 KB）を超える場合は切り詰め |
| stdio タイムアウト | `_STDIO_CALL_TIMEOUT = 60.0`（秒） |
| 認証 | `auth_token` が設定された場合、`Authorization: Bearer <token>` ヘッダーを要求 |

---

## 6. 機能要件

### 6.1 共通機能（全サーバー）
- `GET /health` — ヘルスチェックエンドポイント
- `GET /v1/tools` — ツール定義一覧の返却
- `POST /v1/call_tool` — ツール実行
- `--stdio` フラグによる stdio モード起動
- `__list_tools__` 予約 RPC（stdio モードでのツール一覧取得）

### 6.2 各サーバーの機能

| サーバー | ポート | 主要ツール |
|---|---|---|
| web-search-mcp | 8004 | `search_web`（Brave/Bing/DuckDuckGo フォールバック） |
| file-read-mcp | 8005 | `read_text_file`, `list_directory`, `directory_tree`, `search_files`, `grep_files`, `get_file_info`, `list_directory_with_sizes`, `read_media_file`, `read_multiple_files`（9 ツール） |
| github-mcp | 8006 | `github_search_repositories`, `github_get_file_contents`, `github_push_files`, `github_create_pull_request`, `github_merge_pull_request`, `github_create_issue`, `github_add_issue_comment`, 他（21 ツール） |
| file-write-mcp | 8007 | `write_file`, `edit_file`, `create_directory`, `move_file`（4 ツール） |
| file-delete-mcp | 8008 | `delete_file`, `delete_directory`（2 ツール） |
| shell-mcp | 8009 | `shell_run`（1 ツール、`shell_run_bg` は未実装） |
| rag-pipeline-mcp | 8010 | `rag_run_pipeline`, `rag_debug_pipeline`（2 ツール） |
| sqlite-mcp | 8011 | `query_sqlite`（1 ツール） |
| cicd-mcp | 8012 | GitHub Actions 関連 4 ツール |
| mdq-mcp | 8013 | `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`（7 ツール） |
| git-mcp / rag-mcp | 8014 | `git_status`, `git_log`, `git_diff`, `git_branch`, `git_show`, `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push`（10 ツール）※ `/rag/server.py` も同一ポートで競合（未文書化） |

---

## 7. 入出力

### 7.1 HTTP トランスポート

**ツール呼び出しリクエスト:**
```
POST /v1/call_tool
Content-Type: application/json
Authorization: Bearer <token>  (auth_token 設定時)
X-Session-Id: <session_id>     (エージェントが付与)

{"name": "read_text_file", "args": {"path": "/opt/llm/docs/README.md"}}
```

**レスポンス:**
```json
{"result": "<テキスト内容>", "is_error": false}
```

**ツール一覧取得:**
```
GET /v1/tools
→ {"tools": [{"name": "read_text_file", "description": "..."}, ...]}
```

**ヘルスチェック:**
```
GET /health
→ {"status": "ok", ...}
```

### 7.2 stdio トランスポート

**リクエスト行（改行区切り JSON）:**
```json
{"id": 1, "name": "search_docs", "args": {"query": "watchdog", "limit": 10}}
```

**レスポンス行:**
```json
{"id": 1, "result": "...", "is_error": false, "truncated": false, "total_bytes": 1234}
```

**ツール一覧取得（予約 RPC）:**
```json
{"id": 1, "name": "__list_tools__", "args": {}}
→ {"id": 1, "result": "{\"tools\": [\"search_docs\", ...]}", "is_error": false, ...}
```

---

## 8. 処理フロー

### 8.1 ツール呼び出しフロー（エージェントサイド）

```
LLM が tool_call を返す
  → ToolRouteResolver.resolve(tool_name) → server_key
  → ServerLifecycleManager.ensure_ready(server_key)
      [persistent HTTP]  → 起動確認のみ
      [subprocess HTTP]  → /health が 200 になるまでポーリング
      [stdio ondemand]   → StdioTransport.start() 起動
      [stdio persistent] → 起動時に起動済み
  → キャッシュ確認（TTL 以内なら結果を返す）
  → HttpTransport.call() または StdioTransport.call()
  → 結果をキャッシュ（is_error=false の場合のみ）
  → (result, is_error, x_request_id) を返す
```

### 8.2 ツールルーティング優先順

1. `mcp_servers.toml` の `tool_names` リスト（設定駆動、優先）
2. `shared/tool_constants.py` のフォールバック静的テーブル

---

## 9. データ仕様

### 9.1 McpServerConfig フィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `transport` | `str` | `"http"` または `"stdio"` |
| `url` | `str` | HTTP サーバーのベース URL |
| `cmd` | `list[str]` | stdio サブプロセス起動コマンド |
| `openrc_service` | `str` | OpenRC サービス名（watchdog 再起動用） |
| `startup_mode` | `str` | `"persistent"` / `"ondemand"` / `"subprocess"` |
| `healthcheck_mode` | `str` | `"http"` / `"process"` / `"ping_tool"` |
| `idle_timeout_sec` | `int` | ondemand サーバーのアイドルタイムアウト（秒、0=無効） |
| `startup_timeout_sec` | `int` | subprocess 起動待ちタイムアウト（デフォルト 30 秒） |
| `working_dir` | `str` | stdio subprocess の作業ディレクトリ |
| `env` | `dict[str, str]` | stdio subprocess の環境変数 |
| `tool_names` | `list[str]` | 設定駆動ルーティング用ツール名リスト |
| `auth_token` | `str` | Bearer 認証トークン |
| `role` | `str` | /mcp 表示用ロールラベル |

### 9.2 スタートアップモード対応表

| transport | startup_mode | 挙動 |
|---|---|---|
| `http` | `persistent` | エージェント外で常時稼働（OpenRC 管理） |
| `http` | `subprocess` | エージェント起動時にサブプロセスとして起動し /health をポーリング |
| `stdio` | `persistent` | エージェント起動時にサブプロセス起動、セッション中ずっと稼働 |
| `stdio` | `ondemand` | 最初のツール呼び出し時に起動、`idle_timeout_sec` 後に自動停止 |

### 9.3 MCPServer 基底クラス属性

```python
class MCPServer:
    server_name: str          # 例: "web-search-mcp"
    server_version: str       # 例: "3.0.0"
    http_host: str            # デフォルト: "127.0.0.1"
    http_port: int            # 例: 8004
    app_module: str           # uvicorn ターゲット
    mcp_tools: list[dict]     # ツール定義リスト
```

### 9.4 TruncationResult

```python
@dataclass(frozen=True)
class TruncationResult:
    text: str           # 切り詰め後テキスト
    truncated: bool     # 切り詰めが発生したか
    total_bytes: int    # 元のバイト数
```

---

## 10. 公開インターフェース仕様

### 10.1 MCPServer（mcp/server.py）

```python
class MCPServer:
    async def dispatch(name: str, args: ToolArgs) -> tuple[str, bool]
    def list_tools() -> list[str]
    def health() -> dict[str, str]
    def run_http() -> None
    async def run_stdio() -> None
```

### 10.2 ToolExecutor（shared/tool_executor.py）

```python
class ToolExecutor:
    async def execute(tool_name: str, args: dict) -> tuple[str, bool, str]
    def set_transport(server_key: str, transport: StdioTransport) -> None
    def set_lifecycle(lifecycle: LifecycleProtocol) -> None
    def set_session_id(session_id: str) -> None
    def apply_config(*, cache_ttl: float | None) -> None
    def clear_cache() -> None
```

### 10.3 HttpTransport（shared/tool_executor.py）

```python
class HttpTransport:
    async def call(name: str, args: dict) -> tuple[str, bool, str]
    def set_session_id(session_id: str) -> None
```

### 10.4 StdioTransport（shared/tool_executor.py）

```python
class StdioTransport:
    async def start() -> None
    def is_alive() -> bool
    async def call(name: str, args: dict) -> tuple[str, bool, str]
    async def stop() -> None
```

### 10.5 ServerLifecycleManager（agent/lifecycle.py）

```python
class ServerLifecycleManager:
    async def ensure_ready(server_key: str) -> None
    async def shutdown_all() -> None
    async def shutdown_idle() -> None
    async def restart(server_key: str) -> None
    async def restart_stdio(server_key: str) -> None
    def get_transport_state(server_key: str) -> LifecycleState
```

### 10.6 ToolRouteResolver（shared/route_resolver.py）

```python
class ToolRouteResolver:
    def __init__(server_configs: dict[str, McpServerConfig])
    def resolve(tool_name: str) -> str  # raises ValueError on no match
```

---

## 11. エラーハンドリング

| エラー種別 | 対応 |
|---|---|
| HTTP 接続エラー | `(エラーメッセージ, True, "")` を返す。`/health` 確認を促すメッセージを含む |
| HTTP 4xx/5xx | ステータスコードとレスポンス本文（先頭 300 文字）をエラーメッセージに含める |
| stdio タイムアウト（60 秒） | `TimeoutError` をキャッチして `(タイムアウトメッセージ, True, "")` を返す |
| stdio 接続切断 | 空バイト検出で `(接続切断メッセージ, True, "")` を返す |
| stdio 不正 JSON | `orjson.JSONDecodeError` をキャッチしてエラーメッセージを返す |
| レスポンスサイズ超過 | 512 KB を超える部分を切り詰めて `[TRUNCATED: X bytes total, showing Y bytes]` を付加 |
| ツール名未解決 | `ValueError: Unknown tool: 'xxx'` を送出 |
| サーバー起動タイムアウト | `RuntimeError` を送出し、stderr（先頭 200 文字）をログに含める |

---

## 12. 検証計画

| 検証項目 | ツール | 合格基準 |
|---|---|---|
| ユニットテスト | `uv run pytest tests/test_lifecycle.py tests/test_mcp_server_base.py tests/test_tool_executor_routing.py tests/test_route_resolver.py tests/test_mcp_config.py` | 全パス |
| 型チェック | `uv run mypy scripts/shared/ scripts/mcp/` | 新規エラーなし |
| セキュリティ | `uv run bandit -r scripts/mcp/` | HIGH 未対応なし |
| 統合テスト | `/mcp status` で全サーバー HEALTHY | /mcp で全サーバー OK 表示 |

---

## 13. 未解決事項・既知問題

| 項目 | 詳細 |
|---|---|
| `McpServerConfig.transport` 型 | 現在 `str` 型。`Literal["http", "stdio"]` への型強化が未実装 (`implementations/20260606-194710_shared_types.md` 参照) |
| MCP ヘルス劣化制御 | `healthy/degraded/unavailable` 状態管理が未実装。現在は起動時警告表示のみ (`implementations/20260606-195339_mcp_health_states.md` 参照) |
| ツール依存関係スケジューリング | `resource_scope` による部分並列化が未実装。現在は全並列/全直列の二択 (`implementations/20260606-195109_tool_scheduler.md` 参照) |
| `CallToolRequest.args` バリデーション | ツール名ベースのバリデーション層が未実装 |
| mdq サーバーの Phase 2/3 機能 | 埋め込みインデックス（`md_chunks_vec`）、サマリーキャッシュ、AST パーサーが未実装 |
