# MCP プロトコル仕様

## 1. HTTP API フォーマット早見表

各サービスのエンドポイント形式をまとめる。

| サービス | エンドポイント | リクエスト / レスポンス |
|---|---|---|
| Chat / Code LLM | `POST /v1/chat/completions` | OpenAI 互換形式 (`messages`, `tools`, `temperature`, `max_tokens`, `stream`) |
| Embed LLM | `POST /embedding` | req: `{"content": "query: <text>"}` / res: `{"embedding": [...]}` |
| MCP HTTP サーバー 7 本 | `POST /v1/call_tool` | req: `{"name": str, "args": {...}}` / res: `{"result": str, "is_error": bool}` |

- Chat/Code LLM は OpenAI 互換。ストリーミングは `"stream": true` で SSE を返す
- Embed LLM は llama.cpp レガシーエンドポイント。E5 モデルのプレフィックス (`passage:` / `query:`) を呼び出し元が付与する
- MCP HTTP サーバー 7 本 (:8004/:8005/:8006/:8007/:8008/:8009/:8010) はすべて同一の `/v1/call_tool` 形式を共有する (`mcp/server.py` の `CallToolRequest`/`CallToolResponse`)

---

## 2. MCP トランスポートモード

AgentREPL は `:8004/:8005/:8006` の `/v1/call_tool` を直接 HTTP POST で呼び出す (stdio モード・サイドカー方式ではない)。MCP サーバー (OpenRC サービス) は事前に起動済みである必要がある。

### 2.1 ツール定義チェック

各 MCP サーバは `/v1/tools` (GET) でツール名・説明一覧を返す。`AgentREPL.run()` が `_init_components()` 後に `_check_tool_definitions()` を呼び、`agent.toml` の `tool_definitions` ツール名セットと比較して差分を警告する。`tool_definitions_strict=true` のとき差分があれば `RuntimeError` で起動中止。全サーバ未到達時はスキップ。

### 2.2 MCP ウォッチドッグ (`mcp_watchdog_interval`)

`_watchdog_loop()` が asyncio バックグラウンドタスクで動作。`mcp_watchdog_interval` 秒ごとに `_probe_mcp_health()` で `/health` を probe し、失敗時に `subprocess.run(["rc-service", name, "restart"])` を実行する (最大 `mcp_watchdog_max_restarts` 回)。再起動対象サービス名は `ctx.cfg.mcp_servers` の各 `McpServerConfig.openrc_service` フィールドから取得する (HTTP トランスポートのみ対象)。`run()` の `finally` でタスクをキャンセルする。`mcp_watchdog_interval=0` (デフォルト) でウォッチドッグは無効。

### 2.3 デュアル起動モード (startup_mode)

`McpServerConfig.startup_mode` で各サーバの起動ポリシーを制御する。

| 値 | 動作 | 対象トランスポート |
|---|---|---|
| `persistent` (デフォルト) | エージェント起動時に即座に `StdioTransport.start()` を実行 | stdio のみ (HTTP はプロセス管理不要) |
| `ondemand` | 初回ツール呼び出し時に `ServerLifecycleManager.ensure_ready()` が自動起動 | stdio のみ |

**config/agent.toml 設定例:**

```toml
[mcp_servers.file_read]
transport = "http"
url = "http://127.0.0.1:8005"
openrc_service = "file-mcp"
# startup_mode = "persistent"  # HTTP は常にデフォルトで persistent 相当

[mcp_servers.shell]
transport = "stdio"
cmd = ["/opt/llm/venv/bin/python", "-m", "mcp.shell.server", "--stdio"]
startup_mode = "ondemand"          # 初回呼び出し時に起動
healthcheck_mode = "ping_tool"     # __list_tools__ でヘルスチェック
tool_names = ["shell_run", "shell_run_bg"]  # 明示的ルーティング
```

**ToolRouteResolver のルーティング優先順位:**

1. `tool_names` に名前が列挙されているサーバを先に検索 (config-driven routing)
2. 見つからない場合は静的プレフィックス判定 (frozenset) にフォールバック

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
```

#### `idle_timeout_sec` の動作

- `0` (デフォルト): アイドル停止無効 — ondemand サーバは起動後、エージェント終了まで停止しない
- 正値: `watchdog_loop()` の各サイクルで `ServerLifecycleManager.shutdown_idle()` が評価する。最後のツール呼び出しから `idle_timeout_sec` 秒以上経過し、かつ `transport.is_alive()` が `True` のサーバのみ停止する
- 実際の停止タイミングは `idle_timeout_sec + mcp_watchdog_interval` まで遅延する場合がある (watchdog が無効の場合は停止しない)

#### `startup_mode` 別の動作まとめ

| 値 | HTTP サーバ | stdio サーバ |
|---|---|---|
| `persistent` (デフォルト) | 管理不要 (外部プロセス) | エージェント起動時に `StdioTransport.start()` |
| `ondemand` | 使用不可 (HTTP は常に外部管理) | 初回 `ensure_ready()` 呼び出し時に自動起動 |

### 2.5 GitHub 許可リスト (`allowed_repos`)

`GitHubService._assert_allowed_repo(owner, repo)` が `github_mcp_server.toml["allowed_repos"]` を確認する。空リストは全リポジトリ許可。書き込み系 9 メソッド (`create_branch`, `create_or_update_file`, `push_files`, `delete_repo_file`, `create_issue`, `add_issue_comment`, `create_pull_request`, `update_pull_request`, `merge_pull_request`) の先頭で呼ばれる。

### 2.6 新規 MCP サーバー追加手順

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
