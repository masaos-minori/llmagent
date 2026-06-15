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

`_watchdog_loop()` が asyncio バックグラウンドタスクで動作。`mcp_watchdog_interval` 秒ごとに `_probe_mcp_health()` で `/health` を probe し、失敗時に `_ServerLifecycleRouter.restart(server_key)` を呼び出してサブプロセスを再起動する (最大 `mcp_watchdog_max_restarts` 回)。`startup_mode = "subprocess"` のサーバのみ対象 (他モードはログ警告のみ)。`run()` の `finally` でタスクをキャンセルする。`mcp_watchdog_interval=0` (デフォルト) でウォッチドッグは無効。

**`_ServerLifecycleRouter.restart(server_key)` の動作:**

1. `_http_procs[server_key]` を取り出し `proc.terminate()` を呼ぶ
2. 3 秒以内に終了しない場合は `proc.kill()`
3. `start_http_subprocess(server_key, cfg)` で uvicorn を再起動し `/health` をポーリング

### 2.2.1 監査ログ仕様

MCP サーバの `POST /v1/call_tool` エンドポイントは各ツール呼び出しを以下の形式で INFO ログに出力する。

```
AUDIT session=<session_id> request=<x_request_id> action=<tool_name> target=<主要引数> outcome=<ok|error> detail=<補足>
```

| フィールド | 内容 |
|---|---|
| `session` | `X-Session-Id` リクエストヘッダ値。未設定時は `-` |
| `request` | `X-Request-Id` ミドルウェア注入値。未設定時は `-` |
| `action` | ツール名 (`req.name`) |
| `target` | 主要引数 (server ごとに異なる: repo スラグ / コマンド先頭 80 文字 / クエリ 80 文字 等) |
| `outcome` | `ok` または `error` |
| `detail` | 補足情報 (省略時は空文字) |

`X-Session-Id` は `ToolExecutor.set_session_id(session_id)` がエージェント起動直後にセットする。`HttpTransport.call()` が各 POST リクエストにヘッダを注入する。

### 2.3 デュアル起動モード (startup_mode)

`McpServerConfig.startup_mode` で各サーバの起動ポリシーを制御する。

| 値 | 動作 | 対象トランスポート |
|---|---|---|
| `persistent` (デフォルト) | エージェント起動時に即座に `StdioTransport.start()` を実行 | stdio のみ |
| `ondemand` | 初回ツール呼び出し時に `_ServerLifecycleRouter.ensure_ready()` が自動起動 | stdio のみ |
| `subprocess` | エージェント起動時に `_ServerLifecycleRouter.start_http_subprocess()` で uvicorn を起動し `/health` ポーリング | HTTP のみ |

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

`MCPServer.run_http()` で HTTP サーバを起動する。

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
- `working_dir` が非空のとき、`StdioTransport.start()` は起動前に `Path(working_dir).is_dir()` を確認する。存在しない場合は `ValueError` を送出し、呼び出し側 (`_start_subprocess_servers` / `_start_ondemand_server`) がエラーをキャッチして `[warn]` ログを出力し続行する
- `env` が非空のとき、`start()` 呼び出し時に `{**os.environ, **env}` でマージしてサブプロセスに渡す。空 dict のときは OS 環境をそのまま継承する

#### `idle_timeout_sec` の動作

- `0` (デフォルト): アイドル停止無効 — ondemand サーバは起動後、エージェント終了まで停止しない
- 正値: `watchdog_loop()` の各サイクルで `_ServerLifecycleRouter.shutdown_idle()` が評価する。最後のツール呼び出しから `idle_timeout_sec` 秒以上経過し、かつ `transport.is_alive()` が `True` のサーバのみ停止する
- 実際の停止タイミングは `idle_timeout_sec + mcp_watchdog_interval` まで遅延する場合がある (watchdog が無効の場合は停止しない)

#### `startup_mode` 別の動作まとめ

| 値 | HTTP サーバ | stdio サーバ |
|---|---|---|
| `persistent` (デフォルト) | 使用不可 | エージェント起動時に `StdioTransport.start()` |
| `ondemand` | 使用不可 | 初回 `ensure_ready()` 呼び出し時に自動起動 |
| `subprocess` | エージェント起動時に uvicorn サブプロセスを起動し `/health` ポーリング | 使用不可 |

### 2.5 ToolExecutor / トランスポート クラスリファレンス

詳細は [`06_ref-mcp.md`](06_ref-mcp.md) §3 を参照。

| クラス | 定義場所 | 説明 |
|---|---|---|
| `LifecycleProtocol` | `shared/tool_executor.py` | `_ServerLifecycleRouter` が実装する protocol |
| `_ServerLifecycleRouter` | `factory.py` | HTTP subprocess と stdio サーバのルーティングを一元管理 |
| `HttpTransport` | `shared/tool_executor.py` | HTTP MCP サーバーへの非同期 POST |
| `StdioTransport` | `shared/tool_executor.py` | stdin/stdout 行区切り JSON-RPC |
| `ToolRouteResolver` | `shared/route_resolver.py` | ツール名 → サーバーキーの解決 |
| `ToolExecutor` | `shared/tool_executor.py` | ルーティング・TTL キャッシュ付きツール実行の中心クラス |

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

### 2.7 shared/tool_constants.py セット一覧

ツール分類 frozenset の正定義は [`06_ref-infra.md`](06_ref-infra.md) §7 を参照。`route_resolver.py` / `tool_executor.py` / `tool_runner.py` の 3 箇所で参照する。

### 2.8 モジュールレベル関数 (shared/tool_executor.py)

ユーティリティ関数の詳細は [`06_ref-mcp.md`](06_ref-mcp.md) §3 を参照。

| 関数名 | 説明 |
|---|---|
| `is_side_effect` | `_SIDE_EFFECT_TOOLS` に含まれるツールかどうか判定 |
| `tool_call_key` | `(tool_name, args)` の MD5 ハッシュキー生成 |
| `format_transport_error` | トランスポート失敗を `TransportErrorInfo` に整形 |

### 2.9 GitHub 許可リスト (`allowed_repos`)

`GitHubService._assert_allowed_repo(owner, repo)` が `github_mcp_server.toml["allowed_repos"]` を確認する。動作は `allowed_repos_mode` で制御される。書き込み系 9 メソッド (`create_branch`, `create_or_update_file`, `push_files`, `delete_repo_file`, `create_issue`, `add_issue_comment`, `create_pull_request`, `update_pull_request`, `merge_pull_request`) の先頭で呼ばれる。

| `allowed_repos_mode` | `allowed_repos` が空 | `allowed_repos` に列挙あり |
|---|---|---|
| `"fail_closed"` (デフォルト) | 全リポジトリを拒否 | 列挙済みのみ許可 |
| `"fail_open"` | 全リポジトリを許可 | 列挙済みのみ許可 |

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
