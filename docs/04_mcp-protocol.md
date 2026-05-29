# MCP プロトコル仕様

## 1. HTTP API フォーマット早見表

各サービスのエンドポイント形式をまとめる。

| サービス | エンドポイント | リクエスト / レスポンス |
|---|---|---|
| Chat / Code LLM | `POST /v1/chat/completions` | OpenAI 互換形式 (`messages`, `tools`, `temperature`, `max_tokens`, `stream`) |
| Embed LLM | `POST /embedding` | req: `{"content": "query: <text>"}` / res: `{"embedding": [...]}` |
| MCP HTTP サーバー 3 本 | `POST /v1/call_tool` | req: `{"name": str, "args": {...}}` / res: `{"result": str, "is_error": bool}` |

- Chat/Code LLM は OpenAI 互換。ストリーミングは `"stream": true` で SSE を返す
- Embed LLM は llama.cpp レガシーエンドポイント。E5 モデルのプレフィックス (`passage:` / `query:`) を呼び出し元が付与する
- MCP HTTP サーバー 3 本 (:8004/:8005/:8006) はすべて同一の `/v1/call_tool` 形式を共有する (`mcp/models.py` の `CallToolRequest`/`CallToolResponse`)

---

## 2. MCP トランスポートモード

AgentREPL は `:8004/:8005/:8006` の `/v1/call_tool` を直接 HTTP POST で呼び出す (stdio モード・サイドカー方式ではない)。MCP サーバー (OpenRC サービス) は事前に起動済みである必要がある。

### 2.1 ツール定義チェック

各 MCP サーバは `/v1/tools` (GET) でツール名・説明一覧を返す。`AgentREPL.run()` が `_init_components()` 後に `_check_tool_definitions()` を呼び、`agent.json` の `tool_definitions` ツール名セットと比較して差分を警告する。`tool_definitions_strict=true` のとき差分があれば `RuntimeError` で起動中止。全サーバ未到達時はスキップ。

### 2.2 MCP ウォッチドッグ (`mcp_watchdog_interval`)

`_watchdog_loop()` が asyncio バックグラウンドタスクで動作。`mcp_watchdog_interval` 秒ごとに `_probe_mcp_health()` で `/health` を probe し、失敗時に `subprocess.run(["rc-service", name, "restart"])` を実行する (最大 `mcp_watchdog_max_restarts` 回)。再起動対象サービス名は `ctx.cfg.mcp_servers` の各 `McpServerConfig.openrc_service` フィールドから取得する (HTTP トランスポートのみ対象)。`run()` の `finally` でタスクをキャンセルする。`mcp_watchdog_interval=0` (デフォルト) でウォッチドッグは無効。

### 2.3 GitHub 許可リスト (`allowed_repos`)

`GitHubService._assert_allowed_repo(owner, repo)` が `github_mcp_server.toml["allowed_repos"]` を確認する。空リストは全リポジトリ許可。書き込み系 9 メソッド (`create_branch`, `create_or_update_file`, `push_files`, `delete_repo_file`, `create_issue`, `add_issue_comment`, `create_pull_request`, `update_pull_request`, `merge_pull_request`) の先頭で呼ばれる。

### 2.4 新規 MCP サーバー追加手順

**テンプレート自動生成 (推奨)**

エージェント REPL で以下を実行するとウィザードが起動し、手順 1-2 相当のファイル群を自動生成する。

```
agent[chat]> /mcp install <server-name>
```

生成されるファイル:
- `scripts/<module>_mcp_server.py` — FastAPI サーバ骨格 (`MCPServer` サブクラス、`dispatch()` 実装、`/health` / `/v1/tools` / `/v1/call_tool` エンドポイント)
- `config/<module>_mcp_server.json` — 設定 JSON テンプレート
- `init.d/<server-name>` — OpenRC 起動スクリプト (755)
- `conf.d/<server-name>` — API キー env テンプレート (オプション)

ウィザード完了後、コンソールに手順 3-6 の詳細 (agent.json の差分、deploy.sh への追記内容等) が表示される。

**手動手順 (全手順)**

1. `mcp/server.py` の `MCPServer` をサブクラス化し `dispatch()` をオーバーライドする
2. FastAPI に `/v1/tools` GET エンドポイントを追加する
3. `agent.json` の `tool_definitions` にツール定義を追加する
4. `config/agent.toml` の `mcp_servers` セクションに新サーバのエントリ (`transport`, `url`, `openrc_service` 等) を追加する
5. `deploy/deploy.sh` のコピーリストに新ファイルを追加する
6. `init.d/` に OpenRC スクリプトを追加し `deploy/setup_services.sh` に起動手順を追加する
