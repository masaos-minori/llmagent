---
title: "McpServerConfig Fields (agent.toml `[mcp_servers.*]`)"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

**所有権:** このファイルに記載のフィールドは `config/agent.toml` のみで定義される。
各MCPサーバーのアプリケーション設定は対応する `*_mcp_server.toml` に記述する。

## Agent-side MCP fields (agent.toml `[mcp_servers.*]`)

以下の5つのフィールドのみが agent.toml に含まれる:

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `startup_mode` | `str` | `"none"` | `"none"` / `"persistent"` / `"subprocess"` |
| `transport` | `TransportType` | 必須 | `TransportType.HTTP`（`"http"`）；TOMLの文字列値はconfig loaderによって変換される（実行時ではない） |
| `url` | `str` | 必須 | HTTPサーバのベースURL |
| `healthcheck_mode` | `str` | *(自動導出)* | `"http"` — 現時点で唯一のtransport/healthcheckモード；キーを省略すると自動的に導出される。指定する場合は厳密に `"http"` でなければならない。 |
| `cmd` | `list[str]` | `[]` | `startup_mode=subprocess` 用の起動コマンド；subprocessモード使用時は空であってはならない |

## Additional agent.toml fields (optional)

以下のフィールドは agent.toml に含まれる場合があるが、必須ではない:

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `env` | `dict[str, str]` | `{}` | subprocessに渡す追加の環境変数 |
| `startup_timeout_sec` | `int` | `30` | subprocessモード: ヘルスポーリングのタイムアウト |
| `call_timeout_sec` | `float` | `60.0` | HttpTransportの呼び出しごとのタイムアウト；0 = タイムアウトなし |
| `tool_names` | `list[str]` | `[]` | 検証用のヒント（任意）；registryはこれに関わらずルーティングする。空 = 検証なし。[Routing Source of Truth](04_mcp_03_01_dispatch-and-routing.md#routing-source-of-truth) を参照。 |

Routing is identical in all three cases — `tool_names` never determines which server a tool routes to; only whether config-vs-registry drift validation runs for this server.

```toml
# Omitted — identical to tool_names = [] (both skip config-vs-registry validation for this server)
[mcp_servers.example_a]
cmd = ["..."]

# Explicit empty — same effect as omitting the key entirely
[mcp_servers.example_b]
cmd = ["..."]
tool_names = []

# Populated — validated against the registry at startup; mismatches are drift, not routing changes
[mcp_servers.example_c]
cmd = ["..."]
tool_names = ["read_text_file", "list_directory"]
```

**廃止に関する注記:** 以前のバージョンでは、`healthcheck_mode=""` を自動推論の明示的リクエストとして受け付けていた（本フィールド導入以前のconfigとの互換性のため）。この空文字列によるsentinelは廃止された — キーを完全に省略して自動導出させるか、厳密な文字列 `"http"` を設定すること。明示的な空文字列は、他の未知の文字列と同様に無効な値として拒否される。

**ドキュメント修正に関する注記:** 本ドキュメントの旧版には `idle_timeout_sec`（subprocessの自動停止までの遅延）というフィールドが記載されていたが、`shared/mcp_config.py` の `McpServerConfig` データクラスにはこのフィールドは存在しない。`config/agent.toml` の `[mcp_servers.*]` にも対応するキーはなく、`agent/services/config_reload.py` の `_MCP_SERVER_FIELDS`（reload時の差分比較対象フィールド一覧）にも含まれていない。実装にはsubprocessの自動アイドル停止機構は存在しないため、当該記載は削除した (Explicit in code)。

| `role` | `str` | `""` | `/mcp` 表示用の人間が読める役割ラベル |

**`key` フィールドについて:** `McpServerConfig` には上記に加えて `key: str = ""` フィールドが存在するが、TOMLで直接指定する設定項目ではない。`_build_single_server()` が `[mcp_servers.<key>]` のセクション名から自動的に設定する内部識別子であり、エラーメッセージのプレフィックス（例: `McpServerConfig['github']: ...`）に用いられる。`compare=False, repr=False` が指定されており、`McpServerConfig` 同士の等価比較（`/reload` の差分検出等）には影響しない (Explicit in code)。

**`startup_mode="none"`:** このサーバはsubprocessとして起動されず、起動時のヘルスチェックも行われない。
このサーバへルーティングされるすべてのtool callは、ネットワークへのアクセスを試みる前に
`ToolExecutor._check_startup_mode()` によって即座に `"disabled (startup_mode=none)"` エラーで拒否される。
これはconfigで `startup_mode` を省略した場合のデフォルトである —
サーバを利用可能にするには `"persistent"` または `"subprocess"` を明示的に指定する必要がある。

**検証ルール:**
- `transport="http"` → `url` は空でなく、有効なHTTP/HTTPS URLでなければならない
- `startup_mode="subprocess"` → `cmd` は空であってはならない
- `call_timeout_sec` は `>= 0` でなければならない（0 = タイムアウトなし）
- `startup_timeout_sec` は `>= 0` でなければならない（0 = ヘルスポーリングをスキップ）
- `tool_names` の各要素は空でない文字列であり、重複してはならない
- `auth_token` は文字列でなければならない
- `env` のキーと値はすべて文字列でなければならない

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
McpServerConfig
key
idle_timeout_sec (廃止/未実装)
