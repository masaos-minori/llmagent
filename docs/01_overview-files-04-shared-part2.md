---
title: "Shared Infrastructure File Structure: scripts/shared/ (Part 2/2)"
category: overview
tags:
  - shared
  - db
  - sqlite
  - file-structure
related:
  - 01_overview-files-04-shared-part1.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

``` text
│   ├─ shared/                              # 共有ユーティリティパッケージ (詳細はディレクトリを参照)
│   │   ├─ __init__.py                      # shared パッケージ初期化
│   │   ├─ llm_client.py                    # LLMClient: SSE ストリーミング・指数バックオフリトライ
│   │   ├─ llm_types.py                     # LLMUsage / LLMResponse データクラス
│   │   ├─ llm_exceptions.py                # エラー型定義
│   │   ├─ llm_transport_errors.py          # LlmTransportErrorHandler
│   │   ├─ llm_sse_stream.py               # LlmSseStreamHandler
│   │   ├─ llm_sse_helpers.py              # LlmSseHelpers
│   │   ├─ llm_reconnect.py               # LlmReconnectHandler
│   │   ├─ llm_hot_config.py              # ホットリロード設定フィールド
│   │   ├─ llm_retry.py                   # 指数バックオフ リクエストリトライ
│   │   ├─ llm_payload.py                 # LlmPayloadHandler
│   │   ├─ sse_parser.py                  # RobustSSEParser
│   │   ├─ tool_executor.py               # ToolExecutor: MCP サーバルーティング・TTL キャッシュ
│   │   ├─ tool_executor_helpers.py       # ツール実行ヘルパー関数
│   │   ├─ tool_transport_invoker.py      # ToolTransportInvoker: MCP 呼び出し (ヘルス/ライフサイクル/セマフォ/呼び出し記録)
│   │   ├─ tool_registry.py                # ToolDefinition / ToolRegistry クラス
│   │   ├─ tool_spec.py                   # ToolSpec: ツール呼び出し実行メタデータ
│   │   ├─ tool_cache.py                  # ToolResultCache: LRU キャッシュ + TTL (※注: 現在 ToolExecutor では未使用のスタンドアロン・ユーティリティ)
│   │   ├─ tool_lifecycle.py              # LifecycleProtocol: MCP サーバライフサイクルプロトコル
│   │   ├─ tool_routing_validation.py     # ドリフト検証関数
│   │   ├─ tool_constants.py              # ツール分類 frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
│   │   ├─ types.py                        # 共通型定義
│   │   ├─ mcp_config.py                  # McpServerConfig 等の設定データクラス
│   │   ├─ mcp_health.py                  # McpServerHealthState / McpServerHealthRegistry — ディスパッチゲート用ヘルス追跡
│   │   ├─ config_loader.py               # TOML/JSON 共通設定ローダー
│   │   ├─ config_errors.py               # Configエラー型
│   │   ├─ config_validator.py            # RagConfigValidator
│   │   ├─ production_config_validator.py # 本番環境固有の設定検証
│   │   ├─ route_resolver.py             # ToolRouteResolver: ツール名 → サーバキーマッピング
│   │   ├─ db_maintenance.py              # count_table(): テーブル行数カウント共通ヘルパー
│   │   ├─ action_result.py               # ActionResult データクラス
│   │   ├─ events.py                       # ArtifactEvent / RetryEvent TypedDict
│   │   ├─ transport_dto.py               # ToolCallResult / TransportErrorInfo データクラス
│   │   ├─ formatters.py                  # MCP 全サーバ共通出力フォーマッタ
│   │   ├─ git_helper.py                   # get_repo_info(): GitPython でブランチ・コミット情報取得
│   │   ├─ http_transport.py              # HTTP トランスポート層
│   │   ├─ json_utils.py                  # JSON ユーティリティ
│   │   ├─ logger.py                       # ロギング設定
│   │   ├─ otel_noop.py                      # OpenTelemetry ノップ実装
│   │   ├─ otel_tracer.py                    # OpenTelemetry トレース
│   │   ├─ token_counter.py                 # トークンカウンター
│   │   └─ token_estimation.py              # トークン推定
│   │   ├─ protocols/                       # 共有プロトコル定義
│   │   │   ├─ __init__.py                  # プロトコルパッケージ初期化
│   │   │   └─ shell.py                     # ShellPolicy プロトコル
```

### 設計上の意図と動作仕様

#### キャッシュとヘルスチェックによる制御
`tool_cache.py` の `ToolResultCache` は、TTLベースのキャッシュにより重複したアップストリーム呼び出しを削減しますが、結果の鮮度（staleness）のリスクを伴います。また、`mcp_health.py` を利用したヘルスチェックにより、サーバーの稼働状態（HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN）に基づいたディスパッチ制御が行われます。なお、`ToolResultCache` はスタンドアロンのユーティリティであり、現在は `ToolExecutor` の内部キャッシュには組み込まれていません。

#### ドリフト検証の挙動
ルーティングドリフトの検知挙動は以下の通りです：
- **Configドリフト**: デフォルトでは警告のみですが、`routing_drift_strict` が有効な場合は `RuntimeError` が発生し、起動が停止します。
- **Liveドリフト**: デフォルトでは警告ですが、`tool_definitions_strict` が有効、または `security_profile == PRODUCTION` の場合は `FATAL` となり、起動が停止します。
- **所有権重複**: 複数のサーバが同一のツール名を主張する場合、モードに関わらず常に `FATAL` となります。

## Related Documents

- `01_overview-files-04-shared-part1.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure
