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

以下の4つのフィールドのみが agent.toml に含まれる:

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `startup_mode` | `str` | `"none"` | `"none"` / `"persistent"` / `"subprocess"` |
| `transport` | `TransportType` | 必須 | `TransportType.HTTP`（`"http"`）；TOMLの文字列値はconfig loaderによって変換される（実行時ではない） |
| `url` | `str` | 必須 | HTTPサーバのベースURL |
| `cmd` | `list[str]` | `[]` | `startup_mode=subprocess` 用の起動コマンド；subprocessモード使用時は空であってはならない |

**廃止に関する注記(2026-07-17):** `healthcheck_mode`フィールドと`HealthcheckMode` enumは削除された。HTTPが唯一サポートされるtransportであり、`healthcheck_mode`は設定値の有無・内容に関わらず常に`_derive_healthcheck_mode()`によって`HealthcheckMode.HTTP`（`"http"`）に導出されていた — フィールド自体、バリデーション分岐、および`config_reload.py`の`_MCP_SERVER_FIELDS`エントリはすべて実装されたことのない第2のヘルスチェック方式のための不要な配線だった。第2のtransport/healthcheck方式を実装する際に再度検討する。

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
