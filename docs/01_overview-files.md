# ファイル構成

アーキテクチャ概要 → [`01_overview-arch.md`](01_overview-arch.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

```
/opt/llm/
├─ llama.cpp/                                 # llama.cpp ソース・ビルド成果物
├─ models/
│   ├─ Qwen3.6-Instruct-Q4_K_M.gguf           # チャット/コード生成用 LLM (MQE・再ランク兼用, :8001)
│   └─ multilingual-E5-small.gguf             # 埋込用 LLM (384 次元, :8003)
├─ rag-src/                           # クロール済みテキスト (yyyymmddhhmmss-{slug}.json)
│   ├─ chunk/                         # チャンク分割済みファイル ({stem}-{idx:04d}.json)
│   └─ registered/                    # DB 投入済みファイル (ingester.py が移動)
├─ db/
│   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
│   ├─ session.sqlite                 # エージェントセッション + メッセージ — see 90_shared_04 §2
│   └─ workflow.sqlite                # タスク追跡 + イベント処理 — see 90_shared_04 §7
├─ sqlite-vec/
│   └─ vec0.so                        # SQLite ベクトル検索拡張 (ロード可能拡張モジュール)
├─ venv/                              # Python 仮想環境
│   └─ requirements.txt              # Python 依存パッケージ一覧
├─ config/
│   ├─ common.toml                          # 共通設定 (DB パス・埋込 URL)
│   ├─ rag_pipeline.toml                    # クロール・チャンク設定 (対象 URL・チャンクサイズ・ストップワード)
│   ├─ web_search_mcp_server.toml           # Web 検索 MCP サーバ設定 (:8004)
│   ├─ file_read_mcp_server.toml            # ファイル読込 MCP サーバ設定 (:8005, 許可ディレクトリ)
│   ├─ github_mcp_server.toml               # GitHub MCP サーバ設定 (:8006)
│   ├─ file_write_mcp_server.toml           # ファイル書込 MCP サーバ設定 (:8007)
│   ├─ file_delete_mcp_server.toml          # ファイル削除 MCP サーバ設定 (:8008)
│   ├─ shell_mcp_server.toml                # シェル MCP サーバ設定 (:8009, 許可コマンド)
│   ├─ rag_pipeline_mcp_server.toml         # RAG パイプライン MCP サーバ設定 (:8010)
│   ├─ sqlite_mcp_server.toml               # SQLite MCP サーバ設定 (:8011)
│   ├─ cicd_mcp_server.toml                 # CI/CD MCP サーバ設定 (:8012)
│   ├─ mdq_mcp_server.toml                  # MDQ MCP サーバ設定 (:8013)
│   └─ git_mcp_server.toml                  # Git MCP サーバ設定 (:8014)
├─ scripts/
│   ├─ agent.py                             # CLI エントリポイント (AgentREPL を起動)
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
│   │   │    │    ├─ ServiceWarning: label, url, message
│   │   │    │    ├─ HealthCheckResult: warnings, errors; has_issues (prop), warning_messages(), error_messages()
│   │   │    │    └─ McpHealthProbeResult: reachable, status_code, restart_recommended, operator_action_required, body
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
│   ├─ rag/                                 # RAG パイプラインパッケージ
│   │   ├─ __init__.py                      # RAG パッケージ初期化
│   │   ├─ pipeline.py                      # RagPipeline: MQE → ベクトル/FTS5 → RRF → 再ランク
│   │   ├─ pipeline_refiner.py              # refine_context(): reranked hits → LLM によるキーポイント圧縮
│   │   ├─ pipeline_service.py              # call_rag_service(): RAG サービス HTTP 呼び出し (指数バックオフリトライ)
│   │   ├─ http_augment.py                  # HTTP RAG エージェント外部サービスに委譲
│   │   ├─ repository.py                    # chunks_vec / chunks_fts アクセス層
│   │   ├─ cache.py                         # SemanticCache: 埋め込みベース LRU セマンティックキャッシュ
│   │   ├─ stage.py                         # PipelineStage Protocol / PipelineContext データクラス
│   │   ├─ maintenance.py                   # RagDbMaintenanceService: FTS5 再構築・WAL チェックポイント・VACUUM
│   │   ├─ llm_client.py                    # RagLLM: RAG 専用 LLM クライアント (MQE・再ランク用)
│   │   ├─ llm_prompts.py                   # RAG パイプライン LLM プロンプトテンプレート
│   │   ├─ enums.py                         # RAG 列挙型
│   │   ├─ exceptions.py                    # RAG 例外定義
│   │   ├─ types.py                         # RawHit / MergedHit / RankedHit 等の型定義
│   │   ├─ utils.py                         # RAG ユーティリティ
│   │   ├─ models_audit.py                  # RAG 監査データモデル
│   │   ├─ models_config.py                 # RAG 設定データモデル
│   │   ├─ models_data.py                   # RAG データモデル
│   │   ├─ models_result.py                 # RAG 結果データモデル
│   │   ├─ mcp/                             # RAG MCP サーバモジュール
│   │   │   └─ __init__.py                  # RAG MCP パッケージ初期化
│   │   ├─ ingestion/                       # クロール・チャンク分割・DB 投入
│   │   │   ├─ document_manager.py          # ドキュメントライフサイクル管理 (RagIngester)
│   │   │   ├─ crawler.py                   # クローラー
│   │   │   ├─ crawler_utils.py             # クローラーユーティリティ
│   │   │   ├─ etag_manager.py              # ETag キャッシュ管理 (クロール差分検出)
│   │   │   ├─ chunk_splitter.py            # チャンク分割エントリポイント
│   │   │   ├─ chunk_japanese.py            # 日本語チャンク分割
│   │   │   ├─ chunk_english.py             # 英語チャンク分割
│   │   │   ├─ chunk_utils.py               # チャンク分割ユーティリティ
│   │   │   ├─ pipeline_utils.py            # パイプラインユーティリティ
│   │   │   └─ ingester.py                  # DB 投入 (registered/ へ移動)
│   │   └─ stages/                          # search / fusion / mqe / augment / rerank
│   │       ├─ __init__.py                  # stages パッケージ初期化
│   │       ├─ augment.py                   # 文脈拡張ステージ
│   │       ├─ fusion.py                    # RRF マージステージ
│   │       ├─ mqe.py                       # メタクエリ生成ステージ
│   │       ├─ rerank.py                    # リランクステージ
│   │       └─ search.py                    # ベクトル/FTS5 検索ステージ
│   ├─ db/                                  # DB 層パッケージ
│   │   ├─ __init__.py                      # モジュール初期化
│   │   ├─ create_schema.py                 # SQLite スキーマ初期化
│   │   ├─ schema_sql.py                    # build_rag_schema_sql / build_session_schema_sql / build_workflow_schema_sql
│   │   ├─ helper.py                        # 接続管理 (WAL / busy_timeout)
│   │   ├─ maintenance.py                   # 運用ポリシー
│   │   ├─ config.py                        # DbConfig データクラス・SQLite パスビルダ
│   │   ├─ models.py                        # WalCheckpointCounts / PurgeCounts / ToolResultRow / DbHealthMetrics / DocumentRow / SessionRow / MessageRow
│   │   ├─ store.py                         # Protocol 抽象レイヤー
│   │   ├─ store_protocols.py               # VectorStore / DocumentStore / SessionStore Protocol 定義
│   │   ├─ store_impl.py                    # SQLiteVectorStore / SQLiteDocumentStore / SQLiteSessionStore 実装
│   │   ├─ tool_results.py                  # ツール結果永続化
│   │   ├─ rag_consistency.py               # RAG インデックス整合性チェック
│   │   ├─ rotation.py                      # データベースローテーション
│   │   └─ recovery.py                      # コーrupted DB リカバリ
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
│       ├─ plugin_registry.py               # プラグイン登録デコレータ (@register_command 等)
│       ├─ plugin_registries.py             # プラグインレジストリ一覧
│       ├─ plugin_tool_invoker.py           # PluginToolInvoker: プラグインツール呼び出し (防御的タプル検証)
│       ├─ plugin_auto_discover.py          # load_plugins(): *.py からプラグイン自動発見 + 競合検証
│       ├─ plugin_conflicts.py              # プラグイン競合検出
│       ├─ plugin_result.py                 # PluginFailure / PluginLoadResult データクラス、PluginLoadError 例外
│       ├─ route_resolver.py                # ToolRouteResolver: ツール名 → サーバキーマッピング
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
│   ├─ eventbus/                            # イベントバスパッケージ
│   │   ├─ app.py                           # FastAPI アプリケーション
│   │   ├─ broker.py                        # メッセージブローカー
│   │   ├─ config.py                        # イベントバス設定
│   │   ├─ db.py                            # データベースアクセス層
│   │   ├─ offsets.py                       # オフセット管理
│   │   ├─ dlq.py                           # DLQ (Dead Letter Queue)
│   │   ├─ publish_route.py                 # publish エンドポイント
│   │   ├─ subscribe_route.py               # subscribe エンドポイント
│   │   ├─ ack_route.py                     # ack エンドポイント
│   │   ├─ dlq_route.py                     # DLQ エンドポイント
│   │   ├─ replay_route.py                  # リプレイエンドポイント
│   │   ├─ health_route.py                  # ヘルスチェックエントポイント
│   │   └─ __init__.py                      # イベントバスパッケージ初期化
   └─ logs/                                    # 各サービスのログファイル出力先
/etc/conf.d/
   └─ github-mcp                         # GITHUB_TOKEN (Personal Access Token) 設定
```
