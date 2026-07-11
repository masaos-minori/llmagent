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

## McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `transport` | `TransportType` | 必須 | `TransportType.HTTP`（`"http"`）；TOMLの文字列値はconfig loaderによって変換される（実行時ではない） |
| `url` | `str` | 必須 | HTTPサーバのベースURL |
| `startup_mode` | `str` | `"none"` | `"none"` / `"persistent"` / `"subprocess"` |
| `cmd` | `list[str]` | `[]` | `startup_mode=subprocess` 用の起動コマンド；subprocessモード使用時は空であってはならない |
| `env` | `dict[str, str]` | `{}` | subprocessに渡す追加の環境変数 |
| `healthcheck_mode` | `str` | *(自動導出)* | `"http"` — 現時点で唯一のtransport/healthcheckモード；キーを省略すると自動的に導出される。指定する場合は厳密に `"http"` でなければならない。 |
| `idle_timeout_sec` | `int` | `0` | subprocessの自動停止までの遅延（0 = 無効） |
| `startup_timeout_sec` | `int` | `30` | subprocessモード: ヘルスポーリングのタイムアウト |
| `call_timeout_sec` | `float` | `60.0` | HttpTransportの呼び出しごとのタイムアウト；0 = タイムアウトなし |
| `tool_names` | `list[str]` | `[]` | 検証用のヒント（任意）；registryはこれに関わらずルーティングする。空 = 検証なし。[Routing Source of Truth](04_mcp_03_routing_lifecycle_and_execution.md#routing-source-of-truth) を参照。 |
| `auth_token` | `str` | `""` | 認証用のBearerトークン（空 = 認証なし） |

> `auth_token=""`（Bearer認証なし）は
> `security_profile="local"` の場合にのみ許可される；
> `security_profile="production"` では起動時に拒否される。
> local/productionの区別とその強制箇所の詳細は
> [04_mcp_05 §Authentication](04_mcp_05_security_and_safety_model.md#authentication-auth_token)
> および [§Security Profile](04_mcp_05_security_and_safety_model.md#security-profile-security_profile)
> を参照。

**廃止に関する注記:** 以前のバージョンでは、`healthcheck_mode=""` を自動推論の明示的リクエストとして受け付けていた（本フィールド導入以前のconfigとの互換性のため）。この空文字列によるsentinelは廃止された — キーを完全に省略して自動導出させるか、厳密な文字列 `"http"` を設定すること。明示的な空文字列は、他の未知の文字列と同様に無効な値として拒否される。

| `role` | `str` | `""` | `/mcp` 表示用の人間が読める役割ラベル |

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
