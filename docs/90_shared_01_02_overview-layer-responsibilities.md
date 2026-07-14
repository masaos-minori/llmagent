---
title: "Shared and DB Layer Overview - Layer Responsibilities"
category: shared
tags:
  - shared
  - db
  - layer-structure
  - responsibilities
  - architecture
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_01_overview-purpose-and-scope.md
  - 90_shared_01_03_overview-constraints-and-reference.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 4. レイヤー構造全体

```
External Libraries
        ↑
   shared/          ← 最下層。他の全レイヤーがこれに依存する
        ↑
       db/           ← shared/ のみに依存
        ↑
  rag/ | mcp_servers/   ← db/ と shared/ に依存
        ↑
    agent/           ← 全レイヤーに依存
```

インポート方向は `.importlinter` で強制される。違反すると `lint-imports` が失敗する。

---

## 5. `shared/` の責務

| モジュール | 責務 |
|---|---|
| `config_loader.py` | TOML/JSON ファイルの読み込みとマージ |
| `config_errors.py` | ConfigMissingError, ConfigParseError, ConfigReadError, ConfigPermissionError エラークラス |
| `config_validator.py` | RagConfigValidator(embedding_dim/vec_dimの整合性検証、use_rrf警告、semantic_cache_thresholdの妥当性チェック） |
| `logger.py` | FileHandler + StreamHandler を持つ名前付きロガー |
| `types.py` | `LLMMessage`(TypedDict）、`RagConfig`（Protocol） |
| `llm_types.py` | `LLMUsage`、`LLMResponse` frozenデータクラス |
| `transport_dto.py` | `ToolCallResult`、`TransportErrorInfo` データクラス — MCPツール実行結果とトランスポート失敗情報 |
| `action_result.py` | `ActionResult` frozenデータクラス — マシン判定スキーマ |
| `events.py` | `ArtifactEvent`、`RetryEvent` TypedDict |
| `protocols/shell.py` | `ShellPolicy` データクラス — シェル実行ポリシー |
| `tool_constants.py` | frozensetの分類テーブル: `READ_TOOLS`、`WRITE_TOOLS` 等（レジストリのシードのみで、ルーティング入力ではない） |
| `route_resolver.py` | `ToolRouteResolver` — ツール名 → サーバキー |
| `mcp_config.py` | `McpServerConfig`、`TransportType`/`StartupMode`/`HealthcheckMode`/`SecurityProfile` enum、mcp_health.py の McpServerHealthState/McpServerHealthRegistry を再エクスポート |
| `mcp_health.py` | `McpServerHealthState` enum（HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN）、`McpServerHealthRegistry` — ディスパッチ判定用のヘルス追跡 |
| `tool_executor.py` | `ToolExecutor` |
| `http_transport.py` | `TransportError`、`HttpTransport` — HTTPトランスポート層（/v1/call_toolを呼ぶ） |
| `llm_client.py` | `LLMClient` — HTTPリトライ、ペイロード構築、再接続対応SSEストリーミングを束ねるLLM通信層。`build_llm_url()`/`build_embed_url()` ヘルパー |
| `plugin_registry.py` | 動的プラグイン読込とツール/コマンド登録 |
| `plugin_registries.py` | プラグインのコマンド/ツール/パイプラインフックの内部レジストリ（`_commands`/`_tools`/`_pipeline_post`）。`plugin_registry.py`・`plugin_conflicts.py` から共有される状態 |
| `plugin_conflicts.py` | `validate_tool_conflicts()`、`validate_command_conflicts()` — プラグインのツール/コマンド名がMCPツールまたは組み込みコマンドと衝突する場合の検証・排除 |
| `plugin_auto_discover.py` | `load_plugins()` — plugin_dir配下の全*.pyを競合検証しつつインポート |
| `plugin_result.py` | `PluginFailure`、`PluginLoadResult` データクラス、`PluginLoadError` 例外 |
| `production_config_validator.py` | `ProductionConfigValidator`、`ConfigValidationResult` — 本番セキュリティプロファイルでの strict キー未設定・`tool_safety_tiers` の過不足・`allowed_tools=[]` を検証 |
| `otel_tracer.py` | OpenTelemetry用のプライベートTracerProvider |
| `otel_noop.py` | トレーシング無効時のNoOpTracer/NoOpSpanスタブ |
| `token_counter.py` | `/tokenize` エンドポイント経由、またはchars//4フォールバックによるトークン数カウント |
| `token_estimation.py` | `estimate_tokens_for_text()`、`estimate_tokens_for_assistant_with_tool_calls()`、`estimate_tokens()` — カテゴリ別トークン推定 |
| `git_helper.py` | Gitリポジトリ情報の取得 |
| `formatters.py` | テキスト切り詰め、key=value形式のログ文字列、サイズのフォーマット |
| `json_utils.py` | `dumps()` — orjson.dumps().decode() をラップしstrを返す |
| `llm_exceptions.py` | `LLMErrorKind` リテラル、kind/phase/url/status_code/retryable/partial_text/detail フィールドを持つ `LLMTransportError` |
| `llm_transport_errors.py` | `LlmTransportErrorHandler` — raise_http_status_error、translate_stream_error |
| `llm_sse_stream.py` | `LlmSseStreamHandler` — read_next_chunk、stream_once |
| `llm_sse_helpers.py` | `LlmSseHelpers` — merge_tool_call_delta、build_stream_response |
| `llm_reconnect.py` | `LlmReconnectHandler` — resolve_retryable、stream |
| `llm_retry.py` | `LlmRetryHandler` — LLM HTTPリクエストの指数バックオフリトライ |
| `llm_payload.py` | `LlmPayloadHandler` — build_payload、parse_response |
| `llm_hot_config.py` | `LlmHotConfigHandler` — ホットリロード可能な設定フィールド |
| `sse_parser.py` | `RobustSSEParser` — インクリメンタルUTF-8デコーダ・ハートビート追跡・不正フレーム許容量を備えたステートフルSSEパーサ |
| `tool_registry.py` | `ToolDefinition` データクラス、`ToolRegistry` クラス — 中央MCPツールレジストリとドリフト検証 |
| `tool_routing_validation.py` | `validate_routing_against_config()`、`validate_routing_against_live()`、`validate_all_routing()` — ドリフト検証関数群 |
| `tool_transport_invoker.py` | `ToolTransportInvoker` — トランスポート層のMCP呼び出し（ヘルス、ライフサイクル、セマフォ、呼び出し記録） |
| `tool_lifecycle.py` | MCPサーバのライフサイクルマネージャ向け `LifecycleProtocol` プロトコル |
| `tool_executor_helpers.py` | `is_side_effect()`、`format_transport_error()`、`tool_hash_key()` ヘルパー関数群 |
| `tool_spec.py` | `ToolSpec` データクラス — 単一ツール呼び出しの実行メタデータ（resource_scope、requires_serial、is_write） |
| `tool_cache.py` | `CacheEntry` データクラス、`ToolResultCache` — TTL付きLRUキャッシュ(ツール呼び出し結果用) |
| `plugin_tool_invoker.py` | `PluginToolInvoker` — プラグインツール実行層 |
| `db_maintenance.py` | `count_table()` — テーブル行数を取得する薄いヘルパー（`db/maintenance.py` とは別モジュール。テーブル名は必ずハードコードされた識別子であることが前提） |

---

## 6. `db/` の責務

| モジュール | 責務 |
|---|---|
| `config.py` | `DbConfig` データクラス、`build_db_config()` — 設定からのDBパス解決 |
| `helper.py` | `SQLiteHelper` — 接続ライフサイクル、WAL/PRAGMA、vec拡張 |
| `create_schema.py` | スキーマDDL作成（`IF NOT EXISTS` による冪等性） |
| `models.py` | DTOデータクラス: `DocumentRow`、`MessageRow`、`SessionRow`、`DbHealthMetrics`、`PurgeCounts`、`RecoveryResult`、`WalCheckpointCounts` |
| `schema_sql.py` | DDLテンプレート文字列（SQLテキストと実行の分離） |
| `store.py` | 再エクスポート用のスタブ — `store_protocols.py` + `store_impl.py` に委譲 |
| `store_protocols.py` | `VectorStore`、`DocumentStore`、`SessionStore`、`MemoryDeleteStore` プロトコル + 埋め込みヘルパー |
| `store_impl.py` | `SQLiteVectorStore`、`SQLiteDocumentStore`、`SQLiteSessionStore`、`SQLiteMemoryDeleteStore` の実装 |
| `maintenance.py` | WALチェックポイント、VACUUM、セッションパージ、メモリのプルーニング |
| `rotation.py` | DBローテーション（現行DBをアーカイブし新規作成） — `rotate_all_dbs()` 関数 |
| `recovery.py` | 破損リカバリ（整合性チェック + VACUUM、またはバックアップからの復元） |
| `rag_consistency.py` | 読み取り専用のRAG整合性チェック（chunks/FTS/vecの行数比較・孤立データ検出） — `check_rag_consistency()`、`is_consistent()`、`summarize_issues()` |

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_01_01_overview-purpose-and-scope.md`
- `90_shared_01_03_overview-constraints-and-reference.md`

## Keywords

shared
db
layer structure
responsibilities
architecture
