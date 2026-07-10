---
title: "Scripts File Structure"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - rag-pipeline
  - file-structure
  - source-code
related:
  - 01_overview-files-01-build.md
  - 01_overview-files-02-rag.md
  - 01_overview-files-04-shared.md
  - 01_overview-files-05-config.md
  - 01_overview-files-06-misc.md
  - 01_overview.md
source:
  - 01_overview-files.md
---

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

```
/opt/llm/
├─ scripts/
│   ├─ agent/                               # エージェント REPL パッケージ
│   │   ├─ __init__.py                      # agent パッケージ初期化
│   │   ├─ __main__.py                      # python -m agent エントリポイント
│   │   ├─ repl.py                          # AgentREPL: 全コンポーネントを AgentContext に注入し REPL ループを駆動
│   │   ├─ startup.py                       # StartupOrchestrator: 起動シーケンス
│   │   ├─ config_builders.py               # 設定ビルダ群
│   │   ├─ config_dataclasses.py            # 設定データクラス
│   │   ├─ context.py                       # AgentContext: per-session mutable state / DI ハブ
│   │   ├─ session.py                       # AgentSession: セッション CRUD (SQLite 永続化)
│   │   ├─ session_message_repo.py          # セッションメッセージリポジトリ
│   │   ├─ security_audit_config.py         # セキュリティ監査用 MCP サーバ設定モデル narrow API
│   │   ├─ history.py                       # 会話履歴バッファ・圧縮フック
│   │   ├─ history_selection_policy.py      # 履歴圧縮選択ポリシー
│   │   ├─ orchestrator.py                  # Orchestrator: ターンレベル制御 (RAG → 圧縮 → LLM → ツール)
│   │   ├─ llm_turn_runner.py               # LLMTurnRunner: SSE ストリーミング + ツールループ
│   │   ├─ tool_loop_guard.py               # ToolLoopGuard: dedup/cycle/retry/error ガード
│   │   ├─ tool_runner.py                   # ツール実行
│   │   ├─ tool_scheduler.py                # ツールスケジューラ (並列/直列)
│   │   ├─ tool_policy.py                   # ツールポリシー
│   │   ├─ tool_approval.py                 # ツール承認
│   │   ├─ tool_audit.py                    # ツール監査
│   │   ├─ tool_enums.py                    # ツール列挙型
│   │   ├─ tool_exceptions.py               # ツール例外定義
│   │   ├─ tool_models.py                   # ツールデータモデル
│   │   ├─ tool_output.py                   # ツール出力フォーマット
│   │   ├─ tool_result_formatter.py         # ツール結果整形
│   │   ├─ repository_gateway.py            # RepositoryGateway: 書込/削除/API-write の単一強制境界 (policy → approval → exec → audit)
│   │   ├─ turn_result.py                   # ターン結果データクラス
│   │   ├─ diagnostic_store.py              # 部分完了診断情報保存
│   │   ├─ error_injection_service.py       # エラー注入サービス
│   │   ├─ mdq_rag_classifier.py            # MDQ RAG 分類エンジン
│   │   ├─ mode_classification.py           # MDQ/RAG モード分類 + システムプロンプト注入
│   │   ├─ lifecycle_protocol.py            # ライフサイクルプロトコル
│   │   ├─ llm_transport_errors.py          # LLM トランスポートエラー処理
│   │   ├─ lifecycle.py                     # LifecycleState enum
│   │   ├─ http_lifecycle.py                # HTTP ライフサイクル管理
│   │   ├─ repl_health.py                   # ヘルスチェックサテライト
│   │   ├─ cli_view.py                      # CLIView: readline 設定・RAG 進捗表示・マルチライン入力
│   │   ├─ factory.py                       # AgentFactory: エージェントコンポーネント構築
│   │   ├─ memory/
│   │   │   └─ __init__.py                  # memory パッケージ初期化
│   │   │   ├─ types.py                     # MemoryEntry / MemoryQuery / MemoryHit / EmbeddingResult データクラス
│   │   │   ├─ services.py                  # MemoryServices: memory サブサービスコンテナ (AppServices.memory の型)
│   │   │   ├─ store.py                     # MemoryStore: SQLite CRUD (`memories` / `memories_fts` / `memories_vec`)
│   │   │   ├─ retriever.py                 # FtsRetriever / VectorRetriever / HybridRetriever: FTS5 + KNN RRF 検索
│   │   │   ├─ extract.py                   # extract_memories(): ルールベース履歴抽出
│   │   │   ├─ jsonl_store.py               # JsonlMemoryStore: 追記専用 JSONL ソース (write() 1 本)
│   │   │   ├─ embedding_client.py          # 埋め込みクライアント
│   │   │   ├─ ingestion.py                 # メモリ取り込み
│   │   │   ├─ injection.py                 # メモリ注入
│   │   │   ├─ mapper.py                    # メモリマッパー
│   │   │   ├─ enums.py                     # メモリ列挙型
│   │   │   ├─ exceptions.py                # メモリ例外定義
│   │   │   ├─ models.py                    # HistoryMessage / JsonlRecord / ConsistencyReport / MemorySnippet データクラス
│   │   │   ├─ count_ops.py                 # memories テーブルの行数カウント (type/source_type 別)
│   │   │   ├─ write_ops.py                 # メモリ書き込み操作
│   │   │   ├─ pin_ops.py                   # メモリピン留め操作
│   │   │   ├─ import_ops.py                # メモリインポート操作
│   │   │   ├─ rebuild_ops.py               # メモリ再構築操作
│   │   │   ├─ fts_query.py                 # FTS クエリヘルパー
│   │   │   ├─ scoring.py                   # メモリスコアリング
│   │   │   ├─ rrf.py                       # RRF (Reciprocal Rank Fusion) マージ
│   │   │   └─ sql_constants.py             # SQL定数
│   │   ├─ commands/
│   │   │   └─ __init__.py                  # commands パッケージ初期化
│   │   │   ├─ registry.py                  # CommandRegistry: スラッシュコマンドディスパッチャ (13 mixins)
│   │   │   ├─ command_defs.py              # CommandDef / SubcommandSpec データクラス (データクラス定義のみ; _COMMANDS は持たない)
│   │   │   ├─ command_defs_list.py         # _COMMANDS: 全組み込みスラッシュコマンドの単一ソース (コマンド追加はここへ)
│   │   │   ├─ mixin_base.py                # MixinBase: 全 mixin の共通基底クラス
│   │   │   ├─ output_port.py               # OutputPort / CliOutputPort: コマンド出力インタフェース
│   │   │   ├─ enums.py                     # コマンド列挙型
│   │   │   ├─ exceptions.py                # コマンド例外定義
│   │   │   ├─ models.py                    # コマンドデータモデル
│   │   │   ├─ utils.py                     # コマンドユーティリティ
│   │   │   ├─ cmd_session.py               # /session コマンド (_SessionMixin)
│   │   │   ├─ cmd_mcp.py                   # /mcp コマンド (_McpMixin)
│   │   │   ├─ cmd_config.py                # /config, /reload コマンド (_ConfigMixin)
│   │   │   ├─ cmd_config_display.py        # /config 表示 (_ConfigMixin)
│   │   │   ├─ cmd_config_set.py            # /set コマンド (_ConfigMixin)
│   │   │   ├─ cmd_config_stats.py          # /stats コマンド (_ConfigMixin)
│   │   │   ├─ cmd_context.py               # /context, /clear, /undo, /history, /system コマンド (_ContextMixin)
│   │   │   ├─ cmd_db.py                    # /db コマンド (_DbMixin)
│   │   │   ├─ cmd_tooling.py               # /tool, /plan コマンド (_ToolingMixin)
│   │   │   ├─ cmd_debug.py                 # /debug コマンド (_DebugMixin)
│   │   │   ├─ cmd_audit.py                 # /audit コマンド (_AuditMixin)
│   │   │   ├─ cmd_rag_export.py            # /rag, /export, /compact コマンド (_RagExportMixin)
│   │   │   ├─ cmd_memory.py                # /memory コマンド (_MemoryMixin)
│   │   │   ├─ cmd_mdq.py                   # /mdq コマンド (_MdqMixin): status/index/refresh/search/outline/get/grep
│   │   │   ├─ cmd_plugins.py               # /plugin コマンド (_PluginsMixin): プラグインロード状態表示
│   │   │   ├─ cmd_workflow.py              # /approve, /reject コマンド (_WorkflowMixin)
│   │   │   ├─ db_help_display.py           # DB ヘルプ表示
│   │   │   ├─ db_session_ops.py            # セッション DB 操作
│   │   │   ├─ db_stats_display.py          # DB ステータス表示
│   │   │   ├─ db_rag_ops.py                # RAG DB 操作ハンドラ (clean, list_urls, rebuild_fts, vec_rebuild, reconcile_url, recover, consistency)
│   │   │   ├─ memory_data_ops.py           # メモリデータ操作 (list, search, show, pin, delete, prune)
│   │   │   ├─ memory_rebuild_ops.py        # メモリ再構築操作 (rebuild, rebuild-fts, rebuild-vec, check-consistency)
│   │   │   ├─ memory_status.py             # メモリレイヤー状態表示ロジック (MemoryStatus dataclass)
│   │   │   ├─ session_title.py             # セッションタイトル生成ロジック (LLM-based with fallback)
│   │   │   └─ token_display.py             # トークンカウント表示ロジック (TokenDisplay mixin)
│   │   ├─ services/                        # サービスレイヤー (agent/services/ ディレクトリ内)
│   │   │   └─ __init__.py                  # services パッケージ初期化
│   │   │   ├─ enums.py                     # McpTier / McpAvailability / ConversationActionType / ExportFormat
│   │   │   ├─ exceptions.py                # McpProbeError / SessionTitleGenerationError / ConfigReloadValidationError 等
│   │   │   ├─ models.py                    # SessionTitleResult / McpProbeResult / SessionRestoreResult / DbStats 等
│   │   │   ├─ config_reload.py             # 設定リロード
│   │   │   ├─ context_view.py              # コンテキストビュー
│   │   │   ├─ conversation_service.py      # 会話サービス
│   │   │   ├─ db_maintenance_service.py    # DB 保守サービス
│   │   │   ├─ export_formatter.py          # エクスポートフォーマット
│   │   │   ├─ io_ports.py                  # I/O ポート管理
│   │   │   ├─ mcp_status.py                # MCP サーバステータス
│   │   │   ├─ rag_maintenance_service.py   # RAG 保守サービス
│   │   │   ├─ session_restore.py           # セッション復元
│   │   │   ├─ session_title.py             # セッションタイトル生成
│   │   │   ├─ typed_validators.py          # 設定リロード用型境界抽出ヘルパー
│   │   │   └─ undo_service.py              # アンドゥサービス
│   │   ├─ shared/                          # agent パッケージ内共有型 (agent 層専用)
│   │   │    ├─ __init__.py                 # shared パッケージ初期化
│   │   │    ├─ enums.py                    # 空ファイル: カナonicalな列挙型は agent.memory.enums / agent.tool_enums
│   │   │    ├─ exceptions.py               # 空ファイル: カナonicalな例外は agent.commands/agent.services/agent.memory/agent.tool_exceptions
│   │   │    ├─ health_models.py            # ヘルスチェックモデル
│   │   │   │    ├─ ServiceWarning: label, url, message
│   │   │   │    ├─ HealthCheckResult: warnings, errors; has_issues (prop), warning_messages(), error_messages()
│   │   │   │    └─ McpHealthProbeResult: reachable, status_code, restart_recommended, operator_action_required, body
│   │   │    └─ models.py                   # エージェント共通データモデル
│   │   │       ├─ ToolApprovalEvent: event, task_id, tool, operation_type, resource_scope, risk, decision, args_preview, ts, workflow_id, session_id
│   │   │       ├─ ApprovalDecisionEvent: event, task_id, tool, risk_level, decision, escalation_reason, ts, workflow_id, session_id
│   │   │       └─ ToolExecEvent: event, task_id, tool, operation_type, resource_scope, mcp_request_id, is_error, args_preview, ts, source, error_type, workflow_id, session_id, artifact_uri
│   │   └─ workflow/                        # ワークフローエンジン
│   │       ├─ models.py                    # ワークフローデータモデル
│   │       ├─ state_store.py               # ワークフロー状態ストア
│   │       ├─ workflow_engine.py           # WorkflowEngine: ターン実行エンジン
│   │       ├─ workflow_loader.py           # ワークフローローダー
│   │       ├─ approval_ops.py              # 承認操作 (request, resolve, get_pending)
│   │       ├─ artifact_ops.py              # 成果物操作 (record_artifact)
│   │       ├─ attempt_ops.py               # アテンプト操作 (start, finish, count)
│   │       ├─ idempotency_ops.py           # 冪等性操作 (is_event_processed, begin_stage_if_new)
│   │       ├─ task_ops.py                  # タスク CRUD (create, update_status, get_by_id, list_pending)
│   │       └─ __init__.py                  # workflow パッケージ初期化
│   ├─ mcp/                                 # MCP サーバパッケージ
│   │   └─ __init__.py                      # MCP パッケージ初期化
│   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
│   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
│   │   ├─ audit.py                         # MCP ツール実行監査ログ (JSON-lines 1 行/実行)
│   │   ├─ dispatch.py                      # dispatch_tool(): DispatchResult を返すツールルーティングヘルパー
│   │   ├─ health_response.py               # make_health_response(): /health エンドポイント共通レスポンス生成
│   │   ├─ tool_validators.py               # @register_validator: git_commit / git_push / trigger_workflow / shell_run 等の入力バリデータ
│   │   ├─ web_search/                      # Web 検索 MCP サーバ (DuckDuckGo, :8004)
│   │   │   ├─ server.py                    # Web 検索 MCP サーバ
│   │   │   ├─ tools.py                     # Web 検索ツール
│   │   │   ├─ models.py                    # Web 検索データモデル
│   │   │   ├─ search_provider.py           # Web 検索プロバイダ
│   │   │   ├─ formatters.py                # Web 検索フォーマッタ
│   │   │   └─ __init__.py                  # Web 検索パッケージ初期化
│   │   ├─ file/                            # ファイル MCP サーバ群 (:8005/:8007/:8008)
│   │   │   ├─ read_server.py               # ファイル読込 MCP サーバ (:8005)
│   │   │   ├─ write_server.py              # ファイル書込 MCP サーバ (:8007)
│   │   │   ├─ delete_server.py             # ファイル削除 MCP サーバ (:8008)
│   │   │   ├─ read_service.py              # ファイル読込サービス
│   │   │   ├─ write_service.py             # ファイル書込サービス
│   │   │   ├─ delete_service.py            # ファイル削除サービス
│   │   │   ├─ read_tools.py                # ファイル読込ツール
│   │   │   ├─ write_tools.py               # ファイル書込ツール
│   │   │   ├─ delete_tools.py              # ファイル削除ツール
│   │   │   ├─ read_business.py             # ファイル読込ビジネスロジック
│   │   │   ├─ read_security.py             # ファイル読込セキュリティ
│   │   │   ├─ read_static_helpers.py       # ファイル読込静的ヘルパー
│   │   │   ├─ read_models.py               # ファイル読込データモデル
│   │   │   ├─ write_models.py              # ファイル書込データモデル
│   │   │   ├─ delete_models.py             # ファイル削除データモデル
│   │   │   ├─ write_formatter.py           # ファイル書込フォーマッタ
│   │   │   ├─ delete_formatter.py          # ファイル削除フォーマッタ
│   │   │   ├─ common.py                    # ファイル共通ユーティリティ
│   │   │   └─ __init__.py                  # ファイル MCP パッケージ初期化
│   │   ├─ github/                          # GitHub MCP サーバ (:8006)
│   │   │   ├─ server.py                    # GitHub MCP サーバ
│   │   │   ├─ server_common.py             # GitHub MCP サーバ共通
│   │   │   ├─ server_file.py               # GitHub ファイル操作
│   │   │   ├─ server_issues.py             # GitHub イシュー操作
│   │   │   ├─ server_pull_requests.py      # GitHub PR 操作
│   │   │   ├─ server_repository.py         # GitHub リポジトリ操作
│   │   │   ├─ service_business.py          # GitHub ビジネスロジックサービス
│   │   │   ├─ service_dispatch.py          # GitHub サービスディスパッチ
│   │   │   ├─ service_file.py              # GitHub ファイルサービス
│   │   │   ├─ service_issues.py            # GitHub イシューサービス
│   │   │   ├─ service_pull_requests.py     # GitHub PR サービス
│   │   │   ├─ service_repository.py        # GitHub リポジトリサービス
│   │   │   ├─ service_init.py              # GitHub サービス初期化
│   │   │   ├─ service_security.py          # GitHub セキュリティサービス
│   │   │   ├─ tools.py                     # GitHub ツール
│   │   │   ├─ tools_file.py                # GitHub ファイルツール
│   │   │   ├─ tools_issues.py              # GitHub イシューツール
│   │   │   ├─ tools_pull_requests.py       # GitHub PR ツール
│   │   │   ├─ tools_repository.py          # GitHub リポジトリツール
│   │   │   ├─ models.py                    # GitHub データモデル
│   │   │   ├─ models_base.py               # GitHub 基本データモデル
│   │   │   ├─ models_config.py             # GitHub 設定データモデル
│   │   │   ├─ models_file.py               # GitHub ファイルデータモデル
│   │   │   ├─ models_issues.py             # GitHub イシューデータモデル
│   │   │   ├─ models_pull_requests.py      # GitHub PR データモデル
│   │   │   ├─ models_repository.py         # GitHub リポジトリデータモデル
│   │   │   ├─ formatter.py                 # GitHub フォーマッタ
│   │   │   ├─ mapper.py                    # GitHub マッパー
│   │   │   ├─ exception_handlers.py        # GitHub 例外ハンドラ
│   │   │   └─ __init__.py                  # GitHub MCP パッケージ初期化
│   │   ├─ shell/                           # シェル MCP サーバ (:8009)
│   │   │   ├─ server.py                    # シェル MCP サーバ
│   │   │   ├─ service.py                   # シェルサービス
│   │   │   ├─ tools.py                     # シェルツール
│   │   │   ├─ subprocess_runner.py         # シェルサブプロセスランナー
│   │   │   ├─ service_static_helpers.py    # シェル静的ヘルパー
│   │   │   ├─ models.py                    # シェルデータモデル
│   │   │   └─ __init__.py                  # シェル MCP パッケージ初期化
│   │   ├─ rag_pipeline/                    # RAG パイプライン MCP サーバ (:8010)
│   │   │   ├─ server.py                    # RAG MCP サーバ
│   │   │   ├─ service.py                   # RAG サービス
│   │   │   ├─ tools.py                     # RAG ツール
│   │   │   ├─ models.py                    # RAG データモデル
│   │   │   ├─ document_manager.py          # RAG ドキュメントマネージャ
│   │   │   └─ __init__.py                  # RAG MCP パッケージ初期化
│   │   ├─ cicd/                            # GitHub Actions CI/CD MCP サーバ (:8012)
│   │   │   ├─ server.py                    # CI/CD MCP サーバ
│   │   │   ├─ service.py                   # CI/CD サービス
│   │   │   ├─ tools.py                     # CI/CD ツール
│   │   │   ├─ models.py                    # CI/CD データモデル
│   │   │   ├─ service_init.py              # CI/CD サービス初期化
│   │   │   ├─ service_business.py          # CI/CD ビジネスロジックサービス
│   │   │   ├─ service_defs.py              # CI/CD サービス定義
│   │   │   ├─ service_guards.py            # CI/CD セキュリティガード
│   │   │   ├─ service_github_actions.py    # CI/CD GitHub Actions サービス
│   │   │   ├─ service_github_actions_composite.py  # CI/CD GitHub Actions コンポジットサービス
│   │   │   ├─ service_github_actions_job.py        # CI/CD GitHub Actions ジョブサービス
│   │   │   ├─ exception_handlers.py        # CI/CD 例外ハンドラ
│   │   │   └─ __init__.py                  # CI/CD MCP パッケージ初期化
│   │   ├─ mdq/                             # Markdown Context Compression Engine MCP サーバ (:8013)
│   │   │   ├─ server.py                    # MDQ MCP サーバ
│   │   │   ├─ service.py                   # MDQ サービス
│   │   │   ├─ tools.py                     # MDQ ツール
│   │   │   ├─ models.py                    # MDQ データモデル
│   │   │   ├─ indexer.py                   # MDQ インデクサ
│   │   │   ├─ search.py                    # MDQ 検索
│   │   │   ├─ parser.py                    # MDQ パーザ
│   │   │   ├─ audit_target.py              # MDQ 監査ターゲット
│   │   │   ├─ auth.py                      # MDQ 認証
│   │   │   ├─ db_schema.py                 # MDQ データベーススキーマ
│   │   │   ├─ db_fts.py                    # MDQ FTS データベース
│   │   │   ├─ db_grep.py                   # MDQ grep データベース
│   │   │   ├─ health_check.py              # MDQ ヘルスチェック
│   │   │   ├─ index_delete.py              # MDQ インデックス削除
│   │   │   ├─ __main__.py                  # MDQ CLI エントリポイント
│   │   │   └─ __init__.py                  # MDQ MCP パッケージ初期化
│   │   └─ git/                             # ローカル git 操作 MCP サーバ (:8014)
│   │       ├─ server.py                    # Git MCP サーバ
│   │       ├─ service.py                   # Git サービス
│   │       ├─ tools.py                     # Git ツール
│   │       ├─ models.py                    # Git データモデル
│   │       ├─ git_security.py              # Git セキュリティ
│   │       ├─ format_output.py             # Git 出力フォーマット
│   │       └─ __init__.py                  # Git MCP パッケージ初期化
```

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`

## Keywords

scripts
agent
mcp-server
rag-pipeline
file-structure
source-code
