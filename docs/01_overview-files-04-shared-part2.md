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
  - 01_overview.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


```
│   └─ shared/                              # 共有ユーティリティパッケージ (全層から利用可)
│       ├─ __init__.py                      # shared パッケージ初期化
│       ├─ llm_client.py                    # LLMClient: SSE ストリーミング・指数バックオフリトライ
│       ├─ llm_types.py                     # LLMUsage / LLMResponse データクラス (llm_client と分離してインポート軽量化)
│       ├─ llm_exceptions.py                # LLMErrorKind リテラル、LLMTransportError エラー型 (kind/phase/url/status_code/retryable/partial_text/detail)
│       ├─ llm_transport_errors.py          # LlmTransportErrorHandler: raise_http_status_error / translate_stream_error
│       ├─ llm_sse_stream.py                # LlmSseStreamHandler: read_next_chunk / stream_once
│       ├─ llm_sse_helpers.py               # LlmSseHelpers: merge_tool_call_delta / build_stream_response
│       ├─ llm_reconnect.py                 # LlmReconnectHandler: resolve_retryable / stream
│       ├─ llm_hot_config.py                # LlmHotConfigHandler: ホットリロード設定フィールド
│       ├─ llm_retry.py                     # LlmRetryHandler: 指数バックオフ LLM HTTP リクエストリトライ
│       ├─ llm_payload.py                   # LlmPayloadHandler: build_payload / parse_response
│       ├─ sse_parser.py                    # RobustSSEParser: 状態管理 SSE パーサ (UTF-8 増分デコード + ハートビート追跡 + 不正フレーム予算)
│       ├─ tool_executor.py                 # ToolExecutor: MCP サーバルーティング・TTL キャッシュ
│       ├─ tool_executor_helpers.py         # is_side_effect() / format_transport_error() / tool_hash_key(): ツール実行ヘルパー関数
│       ├─ tool_transport_invoker.py        # ToolTransportInvoker: トランスポート層 MCP 呼び出し (ヘルス/ライフサイクル/セマフォ/呼び出し記録)
│       ├─ tool_registry.py                 # ToolDefinition データクラス、ToolRegistry クラス — MCP ツールレジストリとドリフト検証
│       ├─ tool_spec.py                     # ToolSpec: ツール呼び出し実行メタデータ (call_id / name / args / resource_scope / requires_serial / is_write)
│       ├─ tool_cache.py                    # CacheEntry データクラス、ToolResultCache — LRU キャッシュ + TTL
│       ├─ tool_lifecycle.py                # LifecycleProtocol: MCP サーバライフサイクルプロトコル
│       ├─ tool_routing_validation.py       # validate_routing_against_config() / validate_routing_against_live() / validate_all_routing(): ドリフト検証関数
│       ├─ tool_constants.py                # ツール分類 frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
│       ├─ types.py                         # 共通型定義 (LLMMessage, RagConfig, RagHit/RawHit/MergedHit/RankedHit, LLMUsage, LLMResponse, ActionResult, ArtifactEvent, ShellPolicy, ツール frozenset)
│       ├─ mcp_config.py                    # McpServerConfig データクラス、McpServerHealthState / McpServerHealthRegistry を再エクスポート
│       ├─ mcp_health.py                    # McpServerHealthState (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN) 列挙型、McpServerHealthRegistry — ディスパッチゲート用ヘルス追跡
│       ├─ config_loader.py                 # TOML/JSON 共通設定ローダー
│       ├─ config_errors.py                 # ConfigMissingError / ConfigParseError / ConfigReadError / ConfigPermissionError エラー型
│       ├─ config_validator.py              # RagConfigValidator: embedding_dim/vec_dim 整合性チェック、use_rrf 警告、semantic_cache_threshold 健全性チェック
│       ├─ production_config_validator.py   # ProductionConfigValidator: 本番環境固有の設定検証
│       ├─ plugin_registry.py               # プラグイン登録デコレータ (@register_command 等)
│       ├─ plugin_registries.py             # プラグインレジストリ一覧
│       ├─ plugin_tool_invoker.py           # PluginToolInvoker: プラグインツール呼び出し (防御的タプル検証)
│       ├─ plugin_auto_discover.py          # load_plugins(): *.py からプラグイン自動発見 + 競合検証
│       ├─ plugin_conflicts.py              # プラグイン競合検出
│       ├─ plugin_result.py                 # PluginFailure / PluginLoadResult データクラス、PluginLoadError 例外
│       ├─ route_resolver.py                # ToolRouteResolver: ツール名 → サーバキーマッピング
│       ├─ db_maintenance.py                # count_table(): テーブル行数カウント共通ヘルパー
│       ├─ action_result.py                 # ActionResult データクラス (ActionType リテラル) — 機械判定パス向け汎用アクション/結果スキーマ
│       ├─ events.py                        # ArtifactEvent / RetryEvent TypedDict — ライフサイクル/成果物通知の型定義 (配送機構なし)
│       ├─ transport_dto.py                 # ToolCallResult / TransportErrorInfo データクラス — MCP ツール実行結果とトランスポート失敗情報
│       ├─ formatters.py                    # MCP 全サーバ共通出力フォーマッタ (truncate / fmt_size / fmt_md_link / fmt_kvlog 等)
│       ├─ git_helper.py                    # get_repo_info(): GitPython でブランチ・コミット情報取得 (/context 表示用)
│       ├─ http_transport.py                # HTTP トランスポート層
│       ├─ json_utils.py                    # JSON ユーティリティ
│       ├─ logger.py                        # ロギング設定
│       ├─ otel_noop.py                     # OpenTelemetry ノップ実装
│       ├─ otel_tracer.py                   # OpenTelemetry トレース
│       ├─ token_counter.py                 # トークンカウンター
│       └─ token_estimation.py              # トークン推定
│       ├─ protocols/                       # 共有プロトコル定義
│       │   ├─ __init__.py                  # プロトコルパッケージ初期化
│       │   └─ shell.py                     # ShellPolicy プロトコル
```

## Related Documents

- `01_overview-files-04-shared-part1.md`

## Keywords

shared
db
sqlite
file-structure
