# MCP プロトコル仕様

## 1. HTTP API フォーマット早見表

各サービスのエンドポイント形式をまとめる。

| サービス | エンドポイント | リクエスト / レスポンス |
|---|---|---|
| Chat / Code LLM | `POST /v1/chat/completions` | OpenAI 互換形式 (`messages`, `tools`, `temperature`, `max_tokens`, `stream`) |
| Embed LLM | `POST /embedding` | req: `{"content": "query: <text>"}` / res: `{"embedding": [...]}` |
| MCP HTTP サーバー 11 本 | `POST /v1/call_tool` | req: `{"name": str, "args": {...}}` / res: `{"result": str, "is_error": bool}` |

- Chat/Code LLM は OpenAI 互換。ストリーミングは `"stream": true` で SSE を返す
- Embed LLM は llama.cpp レガシーエンドポイント。E5 モデルのプレフィックス (`passage:` / `query:`) を呼び出し元が付与する
- MCP HTTP サーバー 11 本 (:8004/:8005/:8006/:8007/:8008/:8009/:8010/:8011/:8012/:8013/:8014) はすべて同一の `/v1/call_tool` 形式を共有する (`mcp/models.py` の `CallToolRequest`/`CallToolResponse`)

| ポート | サービス名 | 用途 |
|---|---|---|
| 8004 | web-search-mcp | Web 検索 |
| 8005 | file-read-mcp | ローカルファイル読み取り |
| 8006 | github-mcp | GitHub 操作 |
| 8007 | file-write-mcp | ローカルファイル書き込み |
| 8008 | file-delete-mcp | ローカルファイル削除 |
| 8009 | shell-mcp | シェル実行 |
| 8010 | rag-pipeline-mcp | RAG パイプライン |
| 8011 | sqlite-mcp | SQLite 読み取り専用クエリ |
| 8012 | cicd-mcp | GitHub Actions CI/CD 操作 |
| 8013 | mdq-mcp | Markdown Context Compression Engine |
| 8014 | git-mcp | ローカル git 操作 |

---

## 2. MCP トランスポートモード

AgentREPL は `config/agent.toml` の `[mcp_servers.*]` 設定に基づき各サーバの `/v1/call_tool` を HTTP POST または stdio JSON-RPC で呼び出す。HTTP モードのサーバー (OpenRC サービス) は事前に起動済みである必要がある。stdio モードのサーバーは `startup_mode` に応じてエージェント起動時または初回ツール呼び出し時に自動起動する。

### 2.1 ツール定義チェック

各 MCP サーバは `/v1/tools` (GET) でツール名・説明一覧を返す。`AgentREPL.run()` が `_init_components()` 後に `_check_tool_definitions()` を呼び、`agent.toml` の `tool_definitions` ツール名セットと比較して差分を警告する。`tool_definitions_strict=true` のとき差分があれば `RuntimeError` で起動中止。全サーバ未到達時はスキップ。

### 2.2 MCP ウォッチドッグ (`mcp_watchdog_interval`)

`_watchdog_loop()` が asyncio バックグラウンドタスクで動作。`mcp_watchdog_interval` 秒ごとに `_probe_mcp_health()` で `/health` を probe し、失敗時に `subprocess.run(["rc-service", name, "restart"])` を実行する (最大 `mcp_watchdog_max_restarts` 回)。再起動対象サービス名は `ctx.cfg.mcp_servers` の各 `McpServerConfig.openrc_service` フィールドから取得する (HTTP トランスポートのみ対象)。`run()` の `finally` でタスクをキャンセルする。`mcp_watchdog_interval=0` (デフォルト) でウォッチドッグは無効。

### 2.3 デュアル起動モード (startup_mode)

`McpServerConfig.startup_mode` で各サーバの起動ポリシーを制御する。

| 値 | 動作 | 対象トランスポート |
|---|---|---|
| `persistent` (デフォルト) | エージェント起動時に即座に `StdioTransport.start()` を実行 | stdio のみ |
| `ondemand` | 初回ツール呼び出し時に `ServerLifecycleManager.ensure_ready()` が自動起動 | stdio のみ |
| `subprocess` | エージェント起動時に `ServerLifecycleManager.start_http_subprocess()` で uvicorn を起動し `/health` ポーリング | HTTP のみ |

`subprocess` モードは OpenRC 不要でエージェント自身がサーバプロセスを管理する。`startup_timeout_sec` 秒以内に `/health` が 200 を返さなければ `RuntimeError` で起動中止。`shutdown_all()` がエージェント終了時に全 HTTP サブプロセスを `terminate()` する。

**config/agent.toml 設定例:**

```toml
# HTTP サーバをエージェントがサブプロセスとして起動 (OpenRC 不要)
[mcp_servers.file_read]
transport        = "http"
url              = "http://127.0.0.1:8005"
cmd              = ["/opt/llm/venv/bin/uvicorn", "mcp.file.read_server:app", "--host", "127.0.0.1", "--port", "8005", "--workers", "1"]
startup_mode     = "subprocess"
startup_timeout_sec = 30

# stdio ondemand サーバ
[mcp_servers.shell]
transport = "stdio"
cmd = ["/opt/llm/venv/bin/python", "-m", "mcp.shell.server", "--stdio"]
startup_mode = "ondemand"          # 初回呼び出し時に起動
healthcheck_mode = "ping_tool"     # __list_tools__ でヘルスチェック
tool_names = ["shell_run", "shell_run_bg"]  # 明示的ルーティング
```

**ToolRouteResolver のルーティング優先順位:**

1. `tool_names` に名前が列挙されているサーバを先に検索 (config-driven routing)
2. 見つからない場合は静的ルーティング (`_fallback_route`) にフォールバック

**`_fallback_route` の静的ルーティングテーブル:**

| ツール名 / 判定条件 | サーバーキー |
|---|---|
| `READ_TOOLS` (`list_directory` / `read_text_file` / `search_files` 等 9 ツール) | `file_read` |
| `WRITE_TOOLS` (`write_file` / `edit_file` / `create_directory` / `move_file`) | `file_write` |
| `DELETE_TOOLS` (`delete_file` / `delete_directory`) | `file_delete` |
| `shell_run` | `shell` |
| `search_web` | `web_search` |
| `github_*` (プレフィックス一致) | `github` |
| `RAG_TOOLS` (`rag_run_pipeline` / `rag_debug_pipeline`) | `rag_pipeline` |
| `CICD_TOOLS` (`trigger_workflow` / `get_workflow_runs` / `get_workflow_status` / `get_workflow_logs`) | `cicd` |
| `MDQ_TOOLS` (`search_docs` / `get_chunk` / `outline` / `index_paths` / `refresh_index` / `stats` / `grep_docs`) | `mdq` |
| `GIT_TOOLS` (`git_status` / `git_log` / `git_diff` / `git_branch` / `git_show` / `git_add` / `git_commit` / `git_checkout` / `git_pull` / `git_push`) | `git` |
| いずれにも該当しない | `ValueError` 送出 |

いずれの frozenset も `shared/tool_constants.py` で定義。tool_names に列挙されていないツール（`shell_run_bg` 等）は config-driven で解決できないため、静的テーブルに存在しない場合は `ValueError` になる。`tool_names` に明示的に列挙すること。

**`__list_tools__` 予約 RPC (stdio introspection):**

stdio サーバに対して `{"id": N, "name": "__list_tools__", "args": {}}` を送ると、
`{"id": N, "result": "{\"tools\": [\"tool_a\", \"tool_b\"]}", "is_error": false}` が返る。
`healthcheck_mode = "ping_tool"` のウォッチドッグはこの RPC を使ってサーバが生存しているか確認する。
`__` プレフィックスは予約名規約 — ユーザーが定義するツール名には使用しないこと。

### 2.4 stdio サーバの運用例

#### エントリポイント パターン

全 MCP サーバの `if __name__ == "__main__":` は以下の形式に統一されている。

```python
if __name__ == "__main__":
    import sys
    server = MyMCPServer()
    if "--stdio" in sys.argv:
        asyncio.run(server.run_stdio())
    else:
        server.run_http()   # uvicorn で HTTP サーバとして起動
```

- `python -m mcp.<name>.server` → HTTP モード (uvicorn, 指定ポートで起動)
- `python -m mcp.<name>.server --stdio` → stdio モード (AgentREPL のサブプロセスとして起動)

`MCPServer.run()` は `run_http()` の後方互換エイリアスとして残しているが、新規コードでは `run_http()` を使うこと。

#### ondemand stdio サーバの設定例

```toml
[mcp_servers.shell]
transport        = "stdio"
cmd              = ["/opt/llm/venv/bin/python", "-m", "mcp.shell.server", "--stdio"]
openrc_service   = ""
startup_mode     = "ondemand"      # 初回ツール呼び出し時に自動起動
healthcheck_mode = "ping_tool"     # __list_tools__ RPC でヘルスチェック
idle_timeout_sec = 300             # 5分アイドル後に自動停止 (watchdog サイクルで評価)
tool_names       = ["shell_run"]   # config-driven routing; 未設定時は静的プレフィックス照合
working_dir      = "/opt/llm"      # サブプロセスの作業ディレクトリ; "" = エージェントの cwd を継承
env              = { EXTRA_VAR = "value" }  # サブプロセスに追加注入する環境変数 (OS 環境にマージ)
```

**`working_dir` / `env` の挙動:**
- `working_dir` が非空のとき、`StdioTransport.start()` は起動前に `Path(working_dir).is_dir()` を確認する。存在しない場合は `ValueError` を送出し、呼び出し側 (`_start_stdio_servers` / `ensure_ready`) がエラーをキャッチして `[warn]` ログを出力し続行する
- `env` が非空のとき、`start()` 呼び出し時に `{**os.environ, **env}` でマージしてサブプロセスに渡す。空 dict のときは OS 環境をそのまま継承する

#### `idle_timeout_sec` の動作

- `0` (デフォルト): アイドル停止無効 — ondemand サーバは起動後、エージェント終了まで停止しない
- 正値: `watchdog_loop()` の各サイクルで `ServerLifecycleManager.shutdown_idle()` が評価する。最後のツール呼び出しから `idle_timeout_sec` 秒以上経過し、かつ `transport.is_alive()` が `True` のサーバのみ停止する
- 実際の停止タイミングは `idle_timeout_sec + mcp_watchdog_interval` まで遅延する場合がある (watchdog が無効の場合は停止しない)

#### `startup_mode` 別の動作まとめ

| 値 | HTTP サーバ | stdio サーバ |
|---|---|---|
| `persistent` (デフォルト) | 管理不要 (外部プロセス) | エージェント起動時に `StdioTransport.start()` |
| `ondemand` | 使用不可 (HTTP は常に外部管理) | 初回 `ensure_ready()` 呼び出し時に自動起動 |

### 2.5 ToolExecutor / トランスポート クラスリファレンス

#### LifecycleProtocol

`shared/tool_executor.py` に定義された `typing.Protocol`。`agent/lifecycle.py` の `ServerLifecycleManager` が実装する。

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `ensure_ready` | `async (server_key: str) -> None` | 指定サーバーが呼び出し可能な状態であることを保証する。ondemand stdio サーバを初回呼び出し時に自動起動する |

#### ServerLifecycleManager

`agent/lifecycle.py`。stdio MCP サーバのサブプロセスライフサイクル管理を担当。`LifecycleProtocol` を実装し `ToolExecutor.set_lifecycle()` で注入する。`AgentREPL._init_components()` で生成し `ctx.services.lifecycle` として保持する。

**コンストラクタ:**

```python
ServerLifecycleManager(
    server_configs: dict[str, McpServerConfig],
    tool_executor: ToolExecutor,
    stdio_procs: dict[str, StdioTransport],
)
```

**主要メソッド:**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `ensure_ready` | `async (server_key: str) -> None` | HTTP / persistent stdio → no-op。ondemand stdio → per-server `asyncio.Lock` によるダブルチェックロッキングで単一起動を保証 |
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
| `call` | `async (name: str, args: dict[str, Any]) -> tuple[str, bool, str]` | `POST /v1/call_tool` を実行し `(result, is_error, x_request_id)` を返す。`httpx.HTTPStatusError` / `httpx.RequestError` / その他例外はすべてキャッチし `is_error=True` で返す |

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
| `call` | `async (name: str, args: dict[str, Any]) -> tuple[str, bool, str]` | JSON-RPC リクエストを送信し `(result, is_error, x_request_id)` を返す。`x_request_id` は常に `""`。タイムアウト (`_STDIO_CALL_TIMEOUT = 60.0` 秒) / 未起動 / 不正レスポンスはいずれも `is_error=True` で返す |
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
| `set_lifecycle` | `(lifecycle: LifecycleProtocol \| None) -> None` | 構築後に lifecycle manager を注入・差し替える |
| `execute` | `async (tool_name: str, args: dict[str, Any]) -> tuple[str, bool, str]` | プラグインツールを優先確認し、次いでキャッシュ付きで MCP ツール実行する。戻り値は `(result, is_error, x_request_id)` |
| `clear_cache` | `() -> None` | キャッシュエントリをすべて削除する |

**キャッシュ仕様:**
- 成功結果 (`is_error=False`) のみキャッシュする
- キャッシュキーは `tool_name + orjson(args, OPT_SORT_KEYS)`
- `cache_ttl` 秒を超えたエントリはミス扱いでキャッシュから削除される
- `cache_max_size > 0` のとき LRU で古いエントリを evict する
- キャッシュヒット時の `x_request_id` は `""` (ライブリクエストなし)

**副作用ツールの判定 (`is_side_effect`):**

`_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})` が定義されており、`is_side_effect(tool_name: str) -> bool` でチェックできる。`execute_all_tool_calls()` (呼び出し元) が副作用ツールを含む場合は並列実行をシリアルに切り替える。

### 2.7 shared/tool_constants.py セット一覧

`shared/tool_constants.py` に正規定義されている frozenset。`route_resolver.py` / `tool_executor.py` / `repl_tool_exec.py` の 3 箇所で参照する。ツール名を変更・追加する場合はここのみを修正し、他ファイルに重複定義しないこと。

| 定数名 | ツール名一覧 | 用途 |
|---|---|---|
| `READ_TOOLS` | `list_directory` / `list_directory_with_sizes` / `directory_tree` / `read_text_file` / `read_media_file` / `read_multiple_files` / `search_files` / `grep_files` / `get_file_info` | ファイル読み取り系 |
| `WRITE_TOOLS` | `write_file` / `edit_file` / `create_directory` / `move_file` | ファイル書き込み系 |
| `DELETE_TOOLS` | `delete_file` / `delete_directory` | ファイル削除系 |
| `RAG_TOOLS` | `rag_run_pipeline` / `rag_debug_pipeline` | RAG パイプライン |
| `CICD_TOOLS` | `trigger_workflow` / `get_workflow_runs` / `get_workflow_status` / `get_workflow_logs` | GitHub Actions CI/CD |
| `MDQ_TOOLS` | `search_docs` / `get_chunk` / `outline` / `index_paths` / `refresh_index` / `stats` / `grep_docs` | Markdown Context Compression Engine (mdq-mcp, port 8013) |
| `GIT_TOOLS` | `git_status` / `git_log` / `git_diff` / `git_branch` / `git_show` / `git_add` / `git_commit` / `git_checkout` / `git_pull` / `git_push` | ローカル git 操作 (git-mcp, port 8014) |

### 2.8 モジュールレベル関数 (shared/tool_executor.py)

| 関数名 | シグネチャ | 説明 |
|---|---|---|
| `is_side_effect` | `(tool_name: str) -> bool` | `_SIDE_EFFECT_TOOLS` (`WRITE_TOOLS \| DELETE_TOOLS \| {"shell_run"}`) に含まれるとき `True` を返す |
| `tool_call_key` | `(name: str, args: dict[str, Any]) -> str` | `(tool_name, args)` ペアを dict キー順正規化した上で MD5 ハッシュ化し文字列で返す。重複排除用の一意キー生成に使用 (非セキュリティ用途) |
| `format_transport_error` | `(*, source, phase, kind, url, status_code, retryable, partial) -> dict[str, str]` | LLM / ツール トランスポート失敗を統一形式 `{"summary": str, "detail": str}` に整形する。`summary` はユーザー向け一行メッセージ、`detail` は orjson シリアライズされた JSON 文字列 |

### 2.9 GitHub 許可リスト (`allowed_repos`)

`GitHubService._assert_allowed_repo(owner, repo)` が `github_mcp_server.toml["allowed_repos"]` を確認する。動作は `allowed_repos_mode` で制御される。書き込み系 9 メソッド (`create_branch`, `create_or_update_file`, `push_files`, `delete_repo_file`, `create_issue`, `add_issue_comment`, `create_pull_request`, `update_pull_request`, `merge_pull_request`) の先頭で呼ばれる。

| `allowed_repos_mode` | `allowed_repos` が空 | `allowed_repos` に列挙あり |
|---|---|---|
| `"fail_open"` (デフォルト) | 全リポジトリを許可 | 列挙済みのみ許可 |
| `"fail_closed"` | 全リポジトリを拒否 | 列挙済みのみ許可 |

### 2.10 新規 MCP サーバー追加手順

**テンプレート自動生成 (推奨)**

エージェント REPL で以下を実行するとウィザードが起動し、手順 1-2 相当のファイル群を自動生成する。

```
agent[chat]> /mcp install <server-name>
```

生成されるファイル:
- `scripts/mcp/<name>/server.py` — FastAPI サーバ骨格 (`MCPServer` サブクラス、`dispatch()` 実装、`/health` / `/v1/tools` / `/v1/call_tool` エンドポイント)
- `config/<module>_mcp_server.json` — 設定 JSON テンプレート
- `init.d/<server-name>` — OpenRC 起動スクリプト (755)
- `conf.d/<server-name>` — API キー env テンプレート (オプション)

ウィザード完了後、コンソールに手順 3-6 の詳細 (agent.toml の差分、deploy.sh への追記内容等) が表示される。

**手動手順 (全手順)**

1. `mcp/server.py` の `MCPServer` をサブクラス化し `dispatch()` をオーバーライドする
2. FastAPI に `/v1/tools` GET エンドポイントを追加する
3. `config/agent.toml` の `tool_definitions` にツール定義を追加する
4. `config/agent.toml` の `mcp_servers` セクションに新サーバのエントリ (`transport`, `url`, `openrc_service` 等) を追加する
5. `deploy/deploy.sh` のコピーリストに新ファイルを追加する
6. `init.d/` に OpenRC スクリプトを追加し `deploy/setup_services.sh` に起動手順を追加する
