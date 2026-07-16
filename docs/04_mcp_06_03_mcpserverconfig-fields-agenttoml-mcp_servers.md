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

**廃止に関する注記:** 以前のバージョンでは、`healthcheck_mode=""` を自動推論の明示的リクエストとして受け付けていた（本フィールド導入以前のconfigとの互換性のため）。この空文字列によるsentinelは廃止された — キーを完全に省略して自動導出させるか、厳密な文字列 `"http"` を設定すること。明示的な空文字列は、他の未知の文字列と同様に無効な値として拒否される。

**`key` フィールドについて:** `McpServerConfig` には上記に加えて `key: str = ""` フィールドが存在するが、TOMLで直接指定する設定項目ではない。`_build_single_server()` が `[mcp_servers.<key>]` のセクション名から自動的に設定する内部識別子であり、エラーメッセージのプレフィックス（例: `McpServerConfig['github']: ...`）に用いられる。`compare=False, repr=False` が指定されており、`McpServerConfig` 同士の等価比較（`/reload` の差分検出等）には影響しない (Explicit in code)。

**`startup_mode="none"`:** このサーバはsubprocessとして起動されず、起動時のヘルスチェックも行われない。
このサーバへルーティングされるすべてのtool callは、ネットワークへのアクセスを試みる前に
`ToolExecutor` の startup_mode チェック処理によって即座に `"disabled (startup_mode=none)"` エラーで拒否される。
これはconfigで `startup_mode` を省略した場合のデフォルトである —
サーバを利用可能にするには `"persistent"` または `"subprocess"` を明示的に指定する必要がある。

**検証ルール:**
- `transport="http"` → `url` は空でなく、有効なHTTP/HTTPS URLでなければならない
- `startup_mode="subprocess"` → `cmd` は空であってはならない

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
McpServerConfig
key
idle_timeout_sec (廃止/未実装)
