
title: "Shared Infrastructure File Structure: venv/db/ + scripts/db/ (Part 1/2)"
category: overview
tags:
  - shared
  - db
  - sqlite
  - file-structure
related:
  - 01_overview-files-04-shared.md



# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


``` text
/opt/llm/
├─ venv/                              # Python 仮想環境
│   └─ uv.lock                        # Python 依存パッケージ一覧 (uv managed)
├─ db/
│   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
│   ├─ session.sqlite                 # エージェントセッション + メッセージ — see 90_shared_04 §2
│   └─ workflow.sqlite                # タスク追跡 + イベント処理 — see 90_shared_04 §7
│   # 3-DB分割は、書き込み頻度が異なるデータ間でのSQLiteロック競合を回避するために設計されています（RAG: インジェスト時のみ、Session: 毎ターン、Workflow: 各イベント時）。各DBはWALモードで動作します。詳細はコミット `73bd9bb08` / `fa703f346` を参照してください。
├─ scripts/
│   ├─ db/                                  # DB 層パッケージ (詳細なファイル構成はディレクトリを参照)
│   │   ├─ __init__.py                      # モジュール初期化
│   │   ├─ create_schema.py                 # SQLite スキーマ初期化
│   │   ├─ schema_sql.py                    # build_rag_schema_sql / build_session_schema_sql / build_workflow_schema_sql
│   │   ├─ helper.py                        # 接続管理 (WAL / busy_timeout)
│   │   ├─ maintenance.py                   # 運用ポリシー
│   │   ├─ config.py                        # DbConfig データクラス・SQLite パスビルダ
│   │   ├─ models.py                        # WalCheckpointCounts / PurgeCounts / DbHealthMetrics / DocumentRow / SessionRow / MessageRow
│   │   ├─ store.py                         # Protocol 抽象レイヤー
│   │   ├─ store_protocols.py               # VectorStore / DocumentStore / SessionStore Protocol 定義
│   │   ├─ store_impl.py                    # SQLiteVectorStore / SQLiteDocumentStore / SQLiteSessionStore 実装
│   │   ├─ rag_consistency.py               # RAG インデックス整合性チェック
│   │   ├─ rotation.py                      # データベースローテーション
│   │   └─ recovery.py                      # コーrupted DB リカバリ
```

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3a. ファイル構成

デプロイ先のディレクトリ構成:


``` text
/opt/llm/
├─ venv/                              # Python 仮想環境
│   └─ uv.lock                        # Python 依存パッケージ一覧 (uv managed)
├─ db/
│   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
│   ├─ session.sqlite                 # エージェントセッション + メッセージ — see 90_shared_04 §2
│   └─ workflow.sqlite                # タスク追跡 + イベント処理 — see 90_shared_04 §7
│   # 3-DB分割は、書き込み頻度が異なるデータ間でのSQLiteロック競合を回避するために設計されています（RAG: インジェスト時のみ、Session: 毎ターン、Workflow: 各イベント時）。各DBはWALモードで動作します。詳細はコミット `73bd9bb08` / `fa703f346` を参照してください。
├─ scripts/
│   ├─ db/                                  # DB 層パッケージ (詳細なファイル構成はディレクトリを参照)
│   │   ├─ __init__.py                      # モジュール初期化
│   │   ├─ create_schema.py                 # SQLite スキーマ初期化
│   │   ├─ schema_sql.py                    # build_rag_schema_sql / build_session_schema_sql / build_workflow_schema_sql
│   │   ├─ helper.py                        # 接続管理 (WAL / busy_timeout)
│   │   ├─ maintenance.py                   # 運用ポリシー
│   │   ├─ config.py                        # DbConfig データクラス・SQLite パスビルダ
│   │   ├─ models.py                        # WalCheckpointCounts / PurgeCounts / DbHealthMetrics / DocumentRow / SessionRow / MessageRow
│   │   ├─ store.py                         # Protocol 抽象レイヤー
│   │   ├─ store_protocols.py               # VectorStore / DocumentStore / SessionStore Protocol 定義
│   │   ├─ store_impl.py                    # SQLiteVectorStore / SQLiteDocumentStore / SQLiteSessionStore 実装
│   │   ├─ rag_consistency.py               # RAG インデックス整合性チェック
│   │   ├─ rotation.py                      # データベースローテーション
│   │   └─ recovery.py                      # コーrupted DB リカバリ
```

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure




# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3b. ファイル構成

`scripts/shared/` を正とする。以下はテーマ別に緩くグルーピングしたファイル一覧である。

**LLM クライアント/トランスポート**
- `llm_client.py` — LLMClient: SSE ストリーミング・指数バックオフリトライ
- `llm_types.py` — LLMUsage / LLMResponse データクラス
- `llm_exceptions.py` — エラー型定義
- `llm_transport_errors.py` — LlmTransportErrorHandler
- `llm_sse_stream.py` — LlmSseStreamHandler
- `llm_sse_helpers.py` — LlmSseHelpers
- `llm_reconnect.py` — LlmReconnectHandler
- `llm_hot_config.py` — ホットリロード設定フィールド
- `llm_retry.py` — 指数バックオフ リクエストリトライ
- `llm_payload.py` — LlmPayloadHandler
- `sse_parser.py` — RobustSSEParser

**ツールルーティング/実行**
- `tool_executor.py` — ToolExecutor: MCP サーバルーティング・TTL キャッシュ
- `tool_executor_helpers.py` — ツール実行ヘルパー関数
- `tool_transport_invoker.py` — ToolTransportInvoker: MCP 呼び出し (ヘルス/ライフサイクル/セマフォ/呼び出し記録)
- `tool_registry.py` — ToolDefinition / ToolRegistry クラス
- `tool_spec.py` — ToolSpec: ツール呼び出し実行メタデータ
- `tool_cache.py` — ToolResultCache: LRU キャッシュ + TTL (※注: 現在 ToolExecutor では未使用のスタンドアロン・ユーティリティ)
- `tool_lifecycle.py` — LifecycleProtocol: MCP サーバライフサイクルプロトコル
- `tool_routing_validation.py` — ドリフト検証関数
- `tool_constants.py` — ツール分類 frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
- `route_resolver.py` — ToolRouteResolver: ツール名 → サーバキーマッピング
- `runtime_tool.py` — RuntimeTool: 正規化されたランタイムツールメタデータの frozen dataclass (name, server_key, description, input_schema, is_write, agent_safety_tier 等) と `build_runtime_tool()` コンストラクタ
- `runtime_tool_registry.py` — RuntimeToolRegistry: `McpToolDiscoveryService.discover_all()` が起動時に構築するインメモリ `{name: RuntimeTool}` レジストリ。`ToolRouteResolver.resolve()` が参照する唯一のルーティング権威 (`tool_registry.ToolRegistry` へのフォールバックなし)

**設定**
- `config_loader.py` — TOML/JSON 共通設定ローダー
- `config_utils.py` — 型付き設定値アクセサ (例: `get_str()`) — TOML/JSON 由来の生 dict から検証済みの値を読み取る
- `config_errors.py` — Configエラー型
- `config_validator.py` — RagConfigValidator
- `production_config_validator.py` — 本番環境固有の設定検証
- `mcp_config.py` — McpServerConfig 等の設定データクラス
- `mcp_health.py` — McpServerHealthState / McpServerHealthRegistry — ディスパッチゲート用ヘルス追跡

**その他ユーティリティ**
- `types.py` — 共通型定義
- `db_maintenance.py` — count_table(): テーブル行数カウント共通ヘルパー
- `action_result.py` — ActionResult データクラス
- `events.py` — ArtifactEvent / RetryEvent TypedDict
- `transport_dto.py` — ToolCallResult / TransportErrorInfo データクラス
- `formatters.py` — MCP 全サーバ共通出力フォーマッタ
- `git_helper.py` — get_repo_info(): GitPython でブランチ・コミット情報取得
- `http_transport.py` — HTTP トランスポート層
- `json_utils.py` — JSON ユーティリティ
- `logger.py` — ロギング設定
- `otel_noop.py` — OpenTelemetry ノップ実装
- `otel_tracer.py` — OpenTelemetry トレース
- `token_counter.py` — トークンカウンター
- `token_estimation.py` — トークン推定
- `__init__.py` — shared パッケージ初期化

**`protocols/`**
- `protocols/__init__.py` — プロトコルパッケージ初期化
- `protocols/shell.py` — ShellPolicy プロトコル

### 設計上の意図と動作仕様

#### キャッシュとヘルスチェックによる制御
`tool_cache.py` の `ToolResultCache` は、TTLベースのキャッシュにより重複したアップストリーム呼び出しを削減しますが、結果の鮮度（staleness）のリスクを伴います。また、`mcp_health.py` を利用したヘルスチェックにより、サーバーの稼働状態（HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN）に基づいたディスパッチ制御が行われます。なお、`ToolResultCache` はスタンドアロンのユーティリティであり、現在は `ToolExecutor` の内部キャッシュには組み込まれていません。

#### ドリフト検証の挙動
ルーティングドリフトの検知挙動は以下の通りです：
- **Configドリフト**: デフォルトでは警告のみですが、`routing_drift_strict` が有効な場合は `RuntimeError` が発生し、起動が停止します。
- **Liveドリフト**: デフォルトでは警告ですが、`tool_definitions_strict` が有効、または `security_profile == PRODUCTION` の場合は `FATAL` となり、起動が停止します。
- **所有権重複**: 複数のサーバが同一のツール名を主張する場合、モードに関わらず常に `FATAL` となります。

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3c. ファイル構成

`scripts/shared/` を正とする。以下はテーマ別に緩くグルーピングしたファイル一覧である。

**LLM クライアント/トランスポート**
- `llm_client.py` — LLMClient: SSE ストリーミング・指数バックオフリトライ
- `llm_types.py` — LLMUsage / LLMResponse データクラス
- `llm_exceptions.py` — エラー型定義
- `llm_transport_errors.py` — LlmTransportErrorHandler
- `llm_sse_stream.py` — LlmSseStreamHandler
- `llm_sse_helpers.py` — LlmSseHelpers
- `llm_reconnect.py` — LlmReconnectHandler
- `llm_hot_config.py` — ホットリロード設定フィールド
- `llm_retry.py` — 指数バックオフ リクエストリトライ
- `llm_payload.py` — LlmPayloadHandler
- `sse_parser.py` — RobustSSEParser

**ツールルーティング/実行**
- `tool_executor.py` — ToolExecutor: MCP サーバルーティング・TTL キャッシュ
- `tool_executor_helpers.py` — ツール実行ヘルパー関数
- `tool_transport_invoker.py` — ToolTransportInvoker: MCP 呼び出し (ヘルス/ライフサイクル/セマフォ/呼び出し記録)
- `tool_registry.py` — ToolDefinition / ToolRegistry クラス
- `tool_spec.py` — ToolSpec: ツール呼び出し実行メタデータ
- `tool_cache.py` — ToolResultCache: LRU キャッシュ + TTL (※注: 現在 ToolExecutor では未使用のスタンドアロン・ユーティリティ)
- `tool_lifecycle.py` — LifecycleProtocol: MCP サーバライフサイクルプロトコル
- `tool_routing_validation.py` — ドリフト検証関数
- `tool_constants.py` — ツール分類 frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
- `route_resolver.py` — ToolRouteResolver: ツール名 → サーバキーマッピング
- `runtime_tool.py` — RuntimeTool: 正規化されたランタイムツールメタデータの frozen dataclass (name, server_key, description, input_schema, is_write, agent_safety_tier 等) と `build_runtime_tool()` コンストラクタ
- `runtime_tool_registry.py` — RuntimeToolRegistry: `McpToolDiscoveryService.discover_all()` が起動時に構築するインメモリ `{name: RuntimeTool}` レジストリ。`ToolRouteResolver.resolve()` が参照する唯一のルーティング権威 (`tool_registry.ToolRegistry` へのフォールバックなし)

**設定**
- `config_loader.py` — TOML/JSON 共通設定ローダー
- `config_utils.py` — 型付き設定値アクセサ (例: `get_str()`) — TOML/JSON 由来の生 dict から検証済みの値を読み取る
- `config_errors.py` — Configエラー型
- `config_validator.py` — RagConfigValidator
- `production_config_validator.py` — 本番環境固有の設定検証
- `mcp_config.py` — McpServerConfig 等の設定データクラス
- `mcp_health.py` — McpServerHealthState / McpServerHealthRegistry — ディスパッチゲート用ヘルス追跡

**その他ユーティリティ**
- `types.py` — 共通型定義
- `db_maintenance.py` — count_table(): テーブル行数カウント共通ヘルパー
- `action_result.py` — ActionResult データクラス
- `events.py` — ArtifactEvent / RetryEvent TypedDict
- `transport_dto.py` — ToolCallResult / TransportErrorInfo データクラス
- `formatters.py` — MCP 全サーバ共通出力フォーマッタ
- `git_helper.py` — get_repo_info(): GitPython でブランチ・コミット情報取得
- `http_transport.py` — HTTP トランスポート層
- `json_utils.py` — JSON ユーティリティ
- `logger.py` — ロギング設定
- `otel_noop.py` — OpenTelemetry ノップ実装
- `otel_tracer.py` — OpenTelemetry トレース
- `token_counter.py` — トークンカウンター
- `token_estimation.py` — トークン推定
- `__init__.py` — shared パッケージ初期化

**`protocols/`**
- `protocols/__init__.py` — プロトコルパッケージ初期化
- `protocols/shell.py` — ShellPolicy プロトコル

### 設計上の意図と動作仕様

#### キャッシュとヘルスチェックによる制御
`tool_cache.py` の `ToolResultCache` は、TTLベースのキャッシュにより重複したアップストリーム呼び出しを削減しますが、結果の鮮度（staleness）のリスクを伴います。また、`mcp_health.py` を利用したヘルスチェックにより、サーバーの稼働状態（HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN）に基づいたディスパッチ制御が行われます。なお、`ToolResultCache` はスタンドアロンのユーティリティであり、現在は `ToolExecutor` の内部キャッシュには組み込まれていません。

#### ドリフト検証の挙動
ルーティングドリフトの検知挙動は以下の通りです：
- **Configドリフト**: デフォルトでは警告のみですが、`routing_drift_strict` が有効な場合は `RuntimeError` が発生し、起動が停止します。
- **Liveドリフト**: デフォルトでは警告ですが、`tool_definitions_strict` が有効、または `security_profile == PRODUCTION` の場合は `FATAL` となり、起動が停止します。
- **所有権重複**: 複数のサーバが同一のツール名を主張する場合、モードに関わらず常に `FATAL` となります。

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure

