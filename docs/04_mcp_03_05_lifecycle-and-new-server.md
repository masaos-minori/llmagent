---
title: "Process Introspection and Adding a New MCP Server"
category: mcp
tags:
  - mcp
  - lifecycle
  - new-server-setup
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_03_transport-and-health-part1.md
  - 04_mcp_03_03_transport-and-health-part2.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
---

# プロセスの内部確認と新しい MCP サーバーの追加

### プロセスの内部確認

`HttpServerLifecycleManager` は診断用途（例: `/mcp status` コマンド、`mcp_status.py`）のために、
管理下の subprocess の読み取り専用スナップショットを公開する。

- `get_process_snapshot(server_key) -> dict | None` — 既知の `server_key` に対して
  `{pid, pgid, running, last_exit_code}` を返す。未知の場合は `None`。`pgid` は `_http_pgids`
  から取得される（`start()` 時に `os.getpgid()` によって設定される、H-8 プロセスグループシャットダウン）。
- `get_process_info(server_key) -> ProcessInfoSnapshot | None` — 同じフィールドに加えて
  `managed` と `stderr_log` を含む型付き dataclass。
- `list_processes() -> list[ProcessInfoSnapshot]` — 現在管理されている全 subprocess サーバーの
  スナップショット。

これらのメソッドは `proc.poll()` やキャッシュ状態の読み取りのみを行う; プロセスの終了や
再起動は一切行わない。

`_ServerLifecycleRouter`（`factory.py` 内のファサード）はこれら3つ全てを
`HttpServerLifecycleManager` への薄い委譲として公開しているため、`McpStatusService` などの
呼び出し元は `_http_mgr` の内部に直接アクセスすることなく、
`getattr(lifecycle, "get_process_snapshot", None)` のダックタイピングでアクセスできる。

---

## 新しい MCP サーバーの追加

### Adding a new tool

### 新しいツールを安全に追加する方法

新しいツールを追加する際は、上記の [Adding a new tool](#adding-a-new-tool) セクションにある
標準的な7ステップの手順に従うこと。

要点:
1. **`shared/tool_constants.py` の frozenset にツール名を追加する** [必須] — 内部レジストリ登録関数がインポート時にこれらの frozenset を読み込み、ルーティングレジストリを自動的に構築する。レジストリの手動編集は不要。
2. **`GET /v1/tools` エンドポイントを追加する** [推奨] — `check_routing_drift_vs_live()` による起動時ドリフト検証を可能にする; ルーティングには影響しない。
3. **サーバー設定に `tool_names` を追加する** [任意] — ドリフト検証のヒントのみ; ルーティングには不要。
4. **`config/agent.toml` の `[[tool_definitions]]` に LLM スキーマを追加する** [ツールを LLM に見せる場合は必須]
5. **`config/agent.toml` に `tool_safety_tiers` エントリを追加する** [必須 — 全てのツールは安全性ティアを宣言しなければならない]

```toml
[mcp_servers.my_server]
transport = "http"
url = "http://127.0.0.1:8015"
tool_names = ["my_tool_a", "my_tool_b"]
```

### ルーティング優先度の要約

| 層 | 役割 | ルーティングに使用するか |
|---|---|---|
| `ToolRegistry`（`tool_constants.py` の frozenset からインポート時に自動構築） | **唯一のルーティング権威**; 内部レジストリ登録関数によって構築される | Yes |
| ライブの `/v1/tools` discovery | **検証専用のソース**; 起動時に `check_routing_drift_vs_live()` によってドリフト検出に使用 | No |

**重要なルール:**
- **新しいツールは常に `ToolRegistry` を経由して登録しなければならない**。未知のツールは `ValueError` で即時失敗する。
- **ライブ discovery はルーティングに影響しない** — `/v1/tools` が異なる `server_key` を返す場合、ルーティングの上書きとしてではなく、ドリフトとしてフラグが立てられる。
- **config の `tool_names` はルーティングの入力ではない** — あくまでドリフト検出用の検証ヒントである。

### 新規サーバー/ツール登録チェックリスト

| 対象物 | 必須か | 備考 |
|---|---|---|
| `shared/tool_constants.py` — frozenset にツールを追加 | **必須** | レジストリはインポート時に frozenset を読み込む |
| `config/agent.toml` の `[[tool_definitions]]` — LLM スキーマを追加 | **必須**（ツールを LLM に見せる場合） | OpenAI function-calling 形式; LLM がツールを呼び出すために必要 |
| `config/agent.toml` — `tool_safety_tiers` エントリを追加 | **必須** | 全てのツールは安全性ティアを宣言しなければならない |
| `config/<key>_mcp_server.toml` — サーバー設定ファイル | **必須** | サーバーアプリ設定(サーバー固有の値のみ)。`[mcp_servers.<key>]` トランスポートセクションは別ファイルの `config/agent.toml` 側に追加する |
| `deploy/deploy.sh` — インストール/コピーステップを追加 | **必須**（新規サーバーの場合） | デプロイに新規サーバーを含める必要がある |
| `routing.md` の更新 | **必須** | ドキュメントガイドは新規サーバーを参照する必要がある |

### 手動での作業手順

1. `mcp_servers/<name>/server.py` で `MCPServer` をサブクラス化し、`dispatch()` をオーバーライドする
2. `server_key` フィールドを含むツール定義を返す `GET /v1/tools` エンドポイントを追加する
3. `shared/tool_constants.py` の frozenset にツール名を追加する（このサーバーが所有）
4. `config/agent.toml` の `[[tool_definitions]]` に LLM スキーマを追加する（OpenAI function-calling 形式）
5. 各ツールについて `config/agent.toml` に `tool_safety_tiers` エントリを追加する
6. サーバーアプリ設定を含む `config/<key>_mcp_server.toml` を作成し、`config/agent.toml` に `[mcp_servers.<key>]` トランスポートセクションを追加する
7. `deploy/deploy.sh` のコピーリストに新しいファイルを追加する
8. `deploy/setup_services.sh` に起動ステップを追加する

### Tool_names の設定（ドリフト検出専用）

ツールレジストリは `tool_constants.py` の frozenset からインポート時に自動構築される。
ドリフト検出のため、`config/agent.toml` の `[mcp_servers.<key>]` サーバー設定に任意で `tool_names` を追加できる。

```toml
[mcp_servers.my_server]
transport = "http"
url = "http://127.0.0.1:8015"
tool_names = ["my_tool_a", "my_tool_b"]
```

`tool_names` が省略されている、または不完全であっても、レジストリは引き続き正しくルーティングする
（優先度2）が、起動時のドリフト検証で警告が出力される。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_03_transport-and-health-part1.md`
- `04_mcp_03_03_transport-and-health-part2.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`

## Keywords

mcp
lifecycle
process introspection
new mcp server
tool_constants
tool_safety_tiers
deploy
