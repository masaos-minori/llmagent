---
title: "MCP System Overview"
category: mcp
tags:
  - mcp
  - system
  - overview
  - architecture
related:
  - 04_mcp_00_document-guide.md
---

# MCP System Overview

- ドキュメントガイド → [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md)

## Purpose

MCP（Model Context Protocol）レイヤーは、独立したサーバプロセス群を通じて、
エージェントに対して外部リソース（ファイルシステム、GitHub、Web検索、SQLite、shell、RAG、CI/CD、Git）への
安全かつ制御されたアクセスを提供する。

---

## Scope

**対象範囲:**
- `mcp_servers/` のサーバ実装
- `shared/tool_executor.py`、`shared/route_resolver.py`、`shared/mcp_config.py`
- MCPサーバは `config/agent.toml` の `[mcp_servers.*]` に定義され、各サーバが提供するtoolは `tool_constants.py` のfrozensetで管理され、`ToolRegistry` 経由で登録される

**対象外:**
- Agent REPLの内部実装
- RAGパイプラインの検索ロジック

---

## 構成モデル（2層）

MCPサーバーの設定は2つのレイヤーに分離されている。

**レイヤー1 — エージェントプロセス設定 (`config/agent.toml`)**

エージェント側でMCPサーバーのライフサイクルとトランスポートを管理するための設定:
- `mcp_servers.<key>.startup_mode` — subprocess / persistent / none
- `mcp_servers.<key>.transport` — http
- `mcp_servers.<key>.url` — HTTPエンドポイント
- `mcp_servers.<key>.cmd` — サブプロセス起動コマンド

（`healthcheck_mode`は2026-07-17に削除 — HTTPが唯一のtransportであり、常に`"http"`に自動導出される不要な配線だった）

**レイヤー2 — MCPサーバーローカルアプリケーション設定 (`config/*_mcp_server.toml`)**

各MCPサーバー固有のアプリケーション設定:
- allowlists / denylists
- リソース制限
- 監査パス
- allowed_repos / allowed_repos_mode（GitHub固有）
- command_allowlist（shell固有）
- allowed_dirs（fileサーバー固有）
- auth_token_env / auth_token_file（シークレット参照）

---

## Server Catalog

サーバごとのconfiguration、tool、セキュリティ設定、運用上の注意事項 → [04_mcp_04_01_web-search-file-read-github.md](04_mcp_04_01_web-search-file-read-github.md)（正典となるカタログ）。

| サーバ | ポート | トランスポート | 起動モード | tool数 | 役割 |
|---|---|---|---|---|---|
| web-search-mcp | 8004 | HTTP | persistent | 1 | Web検索（DuckDuckGo） |
| file-read-mcp | 8005 | HTTP | persistent | 9 | ローカルファイル読み取り |
| github-mcp | 8006 | HTTP | persistent | 21 | GitHub API |
| file-write-mcp | 8007 | HTTP | persistent | 4 | ローカルファイル書き込み |
| file-delete-mcp | 8008 | HTTP | persistent | 2 | ローカルファイル削除 |
| shell-mcp | 8009 | HTTP | persistent | 1 | サンドボックス化されたshell実行 |
| rag-pipeline-mcp | 8010 | HTTP | persistent | 4 | RAG検索パイプライン |
| cicd-mcp | 8012 | HTTP | persistent | 4 | GitHub Actions CI/CD |
| mdq-mcp | 8013 | HTTP | persistent | 9 | Markdownコンテキスト圧縮 |
| git-mcp | 8014 | HTTP | persistent | 10 | ローカルgit操作 |

---

## Transport Mechanisms

### HTTP transport（大半のサーバ）

```
Agent ToolExecutor
  → POST http://127.0.0.1:{port}/v1/call_tool
  → {"name": "tool_name", "args": {...}}
  ← {"result": "...", "is_error": false}
```

サーバはloopback上でpersistentなHTTPプロセスとして動作する。

### Transport Selection Guide

> **本番環境のデフォルト: 常にHTTPを使用する（`transport = "http"`。agent管理下のHTTPサーバ（agentがuvicornを起動する場合）は `startup_mode = "subprocess"`、既存のHTTPサーバ（agentは接続のみ）は `startup_mode = "persistent"`）。**
> HTTPはヘルスチェック、並行リクエスト、リモート監視をサポートする。

---

## Startup Modes

| `startup_mode` | `transport` | 動作 |
|---|---|---|
| `none` | N/A | 無効化モード — subprocessの起動もライフサイクル動作も行わない |
| `persistent` | `http` | 外部で管理されるサーバ；agentは既存のHTTPエンドポイントに接続する |
| `subprocess` | `http` | agentが起動時にuvicorn subprocessを開始し、`/health` をポーリングする |

**デフォルト値:** configで `startup_mode` を省略すると `"none"` になる — サーバを利用可能にするには `"persistent"` または `"subprocess"` を明示的に指定する必要がある。

---

## Major Components

| コンポーネント | ファイル | 責務 |
|---|---|---|
| `MCPServer` | `mcp_servers/server.py` | 基底クラス: HTTP起動、`/v1/call_tool`、`/v1/tools`、`/health` |
| `CallToolRequest` / `CallToolResponse` | `mcp_servers/models.py` | 全サーバ共通のPydanticモデル |
| `ToolExecutor` | `shared/tool_executor.py` | ルーティング、TTLキャッシュ、並行実行、ヘルスレジストリ |
| `ToolRouteResolver` | `shared/route_resolver.py` | tool_name → server_key の解決 |
| `ToolRegistry` | `shared/tool_registry.py` | tool定義と所有権に関する単一の正典 |
| `McpServerConfig` | `shared/mcp_config.py` | サーバごとのtransport設定 |
| `McpServerHealthRegistry` | `shared/mcp_health.py` | サーバごとのHEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN状態（`shared/mcp_config.py` は再エクスポートのみ） |
| `HttpTransport` | `shared/http_transport.py` | MCPサーバへのHTTP POST |

---

## server、protocol、sharedの関係

```
agent/factory.py
  → builds ToolExecutor (shared/tool_executor.py)
       → uses ToolRouteResolver (shared/route_resolver.py)
       → uses HttpTransport (shared/http_transport.py)
       → uses McpServerConfig (shared/mcp_config.py)
       → uses McpServerHealthRegistry (shared/mcp_health.py)

MCP server processes (mcp_servers/<name>/server.py)
   → inherit MCPServer (mcp_servers/server.py)
   → use CallToolRequest / CallToolResponse (mcp_servers/models.py)
  → implement dispatch(name, args) → DispatchResult
```

---

## Major Constraints

| 制約 | 値 | 出典 |
|---|---|---|
| 最大レスポンスサイズ | 512 KB（`MCP_MAX_RESPONSE_BYTES = 524288`） | `mcp_servers/server.py` |

| 認証ヘッダ | `Authorization: Bearer <token>`（`auth_token` 設定時） | `mcp_servers/server.py` |
| ヘルス状態の閾値 | 既定 `failure_threshold=3`回連続失敗 → UNAVAILABLE | `shared/mcp_health.py`（`McpServerHealthRegistry`） |

---

### 実装上の補足（Current behavior）

- `McpServerHealthRegistry` の状態遷移は単純な3値ではなく、`HEALTHY` / `DEGRADED` / `UNAVAILABLE` / `HALF_OPEN` / `UNKNOWN` の5値。UNAVAILABLEになったサーバは既定30秒（`half_open_cooldown_sec`）経過後、`is_unavailable()` 呼び出し時に自動的に`HALF_OPEN`（1回だけ疎通を許可する試行状態）へ遷移する簡易サーキットブレーカーとして動作する（Explicit in code, `shared/mcp_health.py`）。
- `record_degraded()` は現在の状態が`UNAVAILABLE`/`HALF_OPEN`の場合は上書きしない（サーキットブレーカーとトライアル窓を壊さないため）（Explicit in code）。

---

## Related Chapters

| トピック | ファイル |
|---|---|
| プロトコル詳細、HTTP形式 | [04_mcp_02_01_endpoints-and-transport.md](04_mcp_02_01_endpoints-and-transport.md) |
| audit log | [04_mcp_02_03_audit-logging-and-errors.md](04_mcp_02_03_audit-logging-and-errors.md) |
| ルーティング、ライフサイクル、ToolExecutor | [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) |
| サーバ別仕様 | [04_mcp_04_01_web-search-file-read-github.md](04_mcp_04_01_web-search-file-read-github.md) |
| セキュリティおよびセーフティモデル | [04_mcp_05_01_access-control-and-allowlists.md](04_mcp_05_01_access-control-and-allowlists.md) |
| 設定と運用 | [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) |
| 既知の不具合と不整合 | [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) |

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_02_01_endpoints-and-transport.md`
- `04_mcp_02_02_startup-modes-and-health.md`
- `04_mcp_03_01_dispatch-and-routing.md`

## Keywords

mcp
system
overview
architecture
health-registry
half-open
circuit-breaker
