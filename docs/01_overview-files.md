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
  ├─ rag-src/                           # クロール済みテキスト (yyyymmddhhmmss-{slug}.txt)
  │   ├─ chunk/                         # チャンク分割済みファイル ({stem}-{idx:04d}.txt)
  │   └─ registered/                    # DB 投入済みファイル (ingester.py が移動)
  ├─ db/
  │   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
  │   ├─ session.sqlite                 # エージェントセッション + メッセージ — see 90_shared_04 §2
  │   ├─ workflow.sqlite                # タスク追跡 + イベント処理 — see 90_shared_04 §7
  │   └─ rrf.sql                        # SQL クエリ参照定義 (KNN・BM25・RRF の説明コメント付き)
  ├─ sqlite-vec/
  │   └─ vec0.so                        # SQLite ベクトル検索拡張 (ロード可能拡張モジュール)
  ├─ venv/                              # Python 仮想環境
  │   └─ requirements.txt              # Python 依存パッケージ一覧
  ├─ config/
  │   ├─ common.toml                          # 共通設定 (DB パス・埋込 URL)
  │   ├─ agent.toml                           # エージェント設定 (URL・検索パラメータ・システムプロンプト・ツール定義)
  │   ├─ rag_pipeline.toml                    # クロール・チャンク設定 (対象 URL・チャンクサイズ・ストップワード)
  │   ├─ rag_pipeline_mcp_server.toml         # RAG パイプライン MCP サーバ設定 (:8010)
  │   ├─ web_search_mcp_server.toml           # Web 検索サーバ設定 (DuckDuckGoのみ)
  │   ├─ file_read_mcp_server.toml            # ファイル読込 MCP サーバ設定 (許可ディレクトリ)
  │   ├─ file_write_mcp_server.toml           # ファイル書込 MCP サーバ設定 (許可ディレクトリ・サイズ上限)
  │   ├─ file_delete_mcp_server.toml          # ファイル削除 MCP サーバ設定 (許可ディレクトリ)
  │   ├─ github_mcp_server.toml               # GitHub MCP サーバ設定 (取得件数上限)
  │   ├─ shell_mcp_server.toml                # シェル MCP サーバ設定 (許可コマンド・タイムアウト)
  │   ├─ sqlite_mcp_server.toml               # SQLite MCP サーバ設定 (db_allowlist / max_rows)
  │   ├─ cicd_mcp_server.toml                 # CI/CD MCP サーバ設定 (repo_allowlist / workflow_allowlist)
  │   ├─ mdq_mcp_server.toml                  # MDQ MCP サーバ設定 (:8013)
  │   ├─ mcp_servers.toml                     # MCP サーバ一覧設定 (transport / url / tool_names)
  │   └─ git_mcp_server.toml                  # ローカル git MCP サーバ設定 (:8014)
  ├─ scripts/
  │   ├─ agent.py                             # CLI エントリポイント (AgentREPL を起動)
  │   ├─ agent/                               # エージェント REPL パッケージ
  │   │   ├─ __main__.py                      # python -m agent エントリポイント
  │   │   ├─ repl.py                          # AgentREPL: 全コンポーネントを AgentContext に注入し REPL ループを駆動
  │   │   ├─ startup.py                       # StartupOrchestrator: 起動シーケンス
  │   │   ├─ config.py                        # AgentConfig データクラス・設定ローダー (hot-reload 対応)
  │   │   ├─ config_builders.py               # 設定ビルダ群
  │   │   ├─ config_dataclasses.py            # 設定データクラス
  │   │   ├─ context.py                       # AgentContext: per-session mutable state / DI ハブ
  │   │   ├─ session.py                       # AgentSession: セッション CRUD (SQLite 永続化)
  │   │   ├─ session_message_repo.py          # セッションメッセージリポジトリ
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
  │   │   ├─ turn_result.py                   # ターン結果データクラス
  │   │   ├─ diagnostic_store.py              # 部分完了診断情報保存
  │   │   ├─ error_injection_service.py       # エラー注入サービス
  │   │   ├─ note_repo.py                     # ノートリポジトリ
  │   │   ├─ mdq_rag_classifier.py            # MDQ RAG 分類エンジン
  │   │   ├─ lifecycle_protocol.py            # ライフサイクルプロトコル
  │   │   ├─ lifecycle.py                     # restart_stdio(): 残存関数 (routing は factory.py の _ServerLifecycleRouter が担当)
  │   │   ├─ http_lifecycle.py                # HTTP ライフサイクル管理
  │   │   ├─ stdio_lifecycle.py               # Stdio ライフサイクル管理
  │   │   ├─ repl_health.py                   # ヘルスチェックサテライト
  │   │   ├─ cli_view.py                      # CLIView: readline 設定・RAG 進捗表示・マルチライン入力
  │   │   ├─ factory.py                       # AgentFactory: エージェントコンポーネント構築
  │   │   ├─ memory/
  │   │   │   ├─ types.py                     # MemoryEntry / MemoryQuery / MemoryHit / EmbeddingResult データクラス
  │   │   │   ├─ services.py                  # MemoryServices: memory サブサービスコンテナ (AppServices.memory の型)
  │   │   │   ├─ store.py                     # MemoryStore: SQLite CRUD (`memories` / `memories_fts` / `memories_vec`)
  │   │   │   ├─ retriever.py                 # FtsRetriever / VectorRetriever / HybridRetriever: FTS5 + KNN RRF 検索
  │   │   │   ├─ extract.py                   # extract_memories(): ルールベース履歴抽出
  │   │   │   ├─ jsonl_store.py               # JsonlMemoryStore: 追記専用 JSONL ソース (write() 1 本)
  │   │   │   ├─ embedding_client.py          # 埋め込みクライアント
  │   │   │   ├─ ingestion.py                 # メモリ取り込み
  │   │   │   ├─ injection.py                 # メモリ注入
  │   │   │   └─ mapper.py                    # メモリマッパー
  │   │   ├─ commands/
  │   │   │   ├─ registry.py                  # CommandRegistry: スラッシュコマンドディスパッチャ (12 mixins)
  │   │   │   ├─ cmd_session.py               # /session コマンド (_SessionMixin)
  │   │   │   ├─ cmd_mcp.py                   # /mcp コマンド (_McpMixin)
  │   │   │   ├─ cmd_config.py                # /config, /reload コマンド (_ConfigMixin)
  │   │   │   ├─ cmd_config_display.py        # /config 表示 (_ConfigMixin)
  │   │   │   ├─ cmd_config_set.py            # /set コマンド (_ConfigMixin)
  │   │   │   ├─ cmd_config_stats.py          # /stats コマンド (_ConfigMixin)
  │   │   │   ├─ cmd_context.py               # /context, /clear, /undo, /history, /system コマンド (_ContextMixin)
  │   │   │   ├─ cmd_db.py                    # /db コマンド (_DbMixin)
  │   │   │   ├─ cmd_tooling.py               # /tool, /plan コマンド (_ToolingMixin)
  │   │   │   ├─ cmd_notes.py                 # /note コマンド (_NotesMixin)
  │   │   │   ├─ cmd_debug.py                 # /debug コマンド (_DebugMixin)
  │   │   │   ├─ cmd_audit.py                 # /audit コマンド (_AuditMixin)
  │   │   │   ├─ cmd_ingest.py                # /ingest, /export, /compact, /rag コマンド (_IngestMixin)
  │   │   │   ├─ cmd_memory.py               # /memory コマンド (_MemoryMixin)
  │   │   │   └─ cmd_workflow.py             # /approve, /reject コマンド (_WorkflowMixin)
  │   │   ├─ services/                      # サービスレイヤー
  │   │   ├─ config_reload.py           # 設定リロード
  │   │   ├─ context_view.py            # コンテキストビュー
  │   │   ├─ conversation_service.py    # 会話サービス
  │   │   ├─ db_maintenance_service.py  # DB 保守サービス
  │   │   ├─ export_formatter.py        # エクスポートフォーマット
  │   │   ├─ ingest_workflow.py         # 取り込みワークフロー
  │   │   ├─ io_ports.py                # I/O ポート管理
  │   │   ├─ mcp_install.py             # MCP サーバインストール
  │   │   ├─ mcp_status.py              # MCP サーバステータス
  │   │   ├─ rag_maintenance_service.py # RAG 保守サービス
  │   │   ├─ session_restore.py         # セッション復元
  │   │   ├─ session_title.py           # セッションタイトル生成
  │   │   ├─ undo_service.py            # アンドゥサービス
  │   │   └─ workflow/                      # ワークフローエンジン
  │   │       ├─ models.py                  # ワークフローデータモデル
  │   │       ├─ state_store.py             # ワークフロー状態ストア
  │   │       ├─ workflow_engine.py         # WorkflowEngine: ターン実行エンジン
  │   │       └─ workflow_loader.py         # ワークフローローダー
  │   ├─ shared/                      # エージェント共有層
  │   │    ├─ enums.py                   # エージェント列挙型
  │   │    ├─ exceptions.py              # エージェント例外定義
  │   │    ├─ health_models.py           # ヘルスチェックモデル
  │   │    └─ models.py                  # エージェント共通データモデル
 │   ├─ mcp/                                 # MCP サーバパッケージ
   │   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
   │   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
   │   │   ├─ web_search/server.py             # Web 検索 MCP サーバ (DuckDuckGo, :8004)
  │   │   ├─ file/                            # ファイル MCP サーバ群 (:8005/:8007/:8008)
  │   │   ├─ github/                          # GitHub MCP サーバ (:8006)
  │   │   ├─ shell/                           # シェル MCP サーバ (:8009)
  │   │   ├─ rag_pipeline/                    # RAG パイプライン MCP サーバ (:8010)
  │   │   ├─ sqlite/                          # SQLite 読み取り専用クエリ MCP サーバ (:8011)
  │   │   ├─ cicd/                            # GitHub Actions CI/CD MCP サーバ (:8012)
  │   │   ├─ mdq/                             # Markdown Context Compression Engine MCP サーバ (:8013)
  │   │   └─ git/                             # ローカル git 操作 MCP サーバ (:8014)
  │   ├─ rag/                                 # RAG パイプラインパッケージ
  │   │   ├─ pipeline.py                      # RagPipeline: MQE → ベクトル/FTS5 → RRF → 再ランク
  │   │   ├─ repository.py                    # chunks_vec / chunks_fts アクセス層
  │   │   ├─ ingestion/                       # crawler.py / chunk_splitter.py / ingester.py
  │   │   └─ stages/                          # search / fusion / mqe / augment / rerank
  │   ├─ db/                                  # DB 層パッケージ
  │   │   ├─ create_schema.py                 # SQLite スキーマ初期化
  │   │   ├─ helper.py                        # 接続管理 (WAL / busy_timeout)
  │   │   ├─ maintenance.py                   # 運用ポリシー
  │   │   ├─ store.py                         # Protocol 抽象レイヤー
  │   │   └─ tool_results.py                  # ツール結果永続化
  │   └─ shared/                              # 共有ユーティリティパッケージ
  │       ├─ llm_client.py                    # LLMClient: SSE ストリーミング・指数バックオフリトライ
  │       ├─ tool_executor.py                 # ToolExecutor: MCP サーバルーティング・TTL キャッシュ
  │       ├─ types.py                         # 共通型定義 (LLMMessage 等)
  │       ├─ mcp_config.py                    # McpServerConfig データクラス
  │       ├─ config_loader.py                 # TOML/JSON 共通設定ローダー
  │       ├─ plugin_registry.py               # プラグイン登録デコレータ (@register_command 等)
  │       ├─ tool_constants.py                # ツール分類 frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
  │       └─ route_resolver.py                # ToolRouteResolver: ツール名 → サーバキーマッピング
  └─ logs/                                    # 各サービスのログファイル出力先
/etc/conf.d/
   └─ github-mcp                         # GITHUB_TOKEN (Personal Access Token) 設定
```

---
