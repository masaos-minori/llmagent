# ファイル構成

アーキテクチャ概要 → [`01_overview-arch.md`](01_overview-arch.md)

## 3. ファイル構成

本リポジトリのファイル構成とデプロイ先の対応。

```
(リポジトリ)                                        (デプロイ先)
deploy/deploy.sh                           →  (リポジトリからの実行のみ: スクリプト・設定を一括コピー)
deploy/init_db.sh                          →  (リポジトリからの実行のみ: DB スキーマ初期化)
deploy/setup_services.sh                   →  (リポジトリからの実行のみ: OpenRC サービス登録・起動)
scripts/agent.py                           →  /opt/llm/scripts/agent.py
scripts/agent/                             →  /opt/llm/scripts/agent/
scripts/agent/__main__.py                  →  /opt/llm/scripts/agent/__main__.py
scripts/agent/repl.py                      →  /opt/llm/scripts/agent/repl.py
scripts/agent/config.py                    →  /opt/llm/scripts/agent/config.py
scripts/agent/context.py                   →  /opt/llm/scripts/agent/context.py
scripts/agent/session.py                   →  /opt/llm/scripts/agent/session.py
scripts/agent/history.py                   →  /opt/llm/scripts/agent/history.py
scripts/agent/orchestrator.py              →  /opt/llm/scripts/agent/orchestrator.py
scripts/agent/factory.py                   →  /opt/llm/scripts/agent/factory.py
scripts/agent/repl_health.py               →  /opt/llm/scripts/agent/repl_health.py
scripts/agent/cli_view.py                  →  /opt/llm/scripts/agent/cli_view.py
scripts/agent/lifecycle.py                 →  /opt/llm/scripts/agent/lifecycle.py
scripts/agent/http_lifecycle.py            →  /opt/llm/scripts/agent/http_lifecycle.py
scripts/agent/stdio_lifecycle.py           →  /opt/llm/scripts/agent/stdio_lifecycle.py
scripts/agent/llm_turn_runner.py           →  /opt/llm/scripts/agent/llm_turn_runner.py
scripts/agent/tool_runner.py               →  /opt/llm/scripts/agent/tool_runner.py
scripts/agent/tool_policy.py               →  /opt/llm/scripts/agent/tool_policy.py
scripts/agent/tool_approval.py             →  /opt/llm/scripts/agent/tool_approval.py
scripts/agent/tool_audit.py                →  /opt/llm/scripts/agent/tool_audit.py
scripts/agent/tool_result_formatter.py     →  /opt/llm/scripts/agent/tool_result_formatter.py
scripts/agent/tool_loop_guard.py           →  /opt/llm/scripts/agent/tool_loop_guard.py
scripts/agent/memory/types.py              →  /opt/llm/scripts/agent/memory/types.py
scripts/agent/memory/enums.py              →  /opt/llm/scripts/agent/memory/enums.py
scripts/agent/memory/exceptions.py         →  /opt/llm/scripts/agent/memory/exceptions.py
scripts/agent/memory/models.py             →  /opt/llm/scripts/agent/memory/models.py
scripts/agent/memory/ports.py              →  /opt/llm/scripts/agent/memory/ports.py
scripts/agent/memory/services.py           →  /opt/llm/scripts/agent/memory/services.py
scripts/agent/memory/store.py              →  /opt/llm/scripts/agent/memory/store.py
scripts/agent/memory/retriever.py          →  /opt/llm/scripts/agent/memory/retriever.py
scripts/agent/memory/extract.py            →  /opt/llm/scripts/agent/memory/extract.py
scripts/agent/memory/jsonl_store.py        →  /opt/llm/scripts/agent/memory/jsonl_store.py
scripts/agent/memory/embedding_client.py   →  /opt/llm/scripts/agent/memory/embedding_client.py
scripts/agent/memory/ingestion.py          →  /opt/llm/scripts/agent/memory/ingestion.py
scripts/agent/memory/injection.py          →  /opt/llm/scripts/agent/memory/injection.py
scripts/agent/memory/mapper.py             →  /opt/llm/scripts/agent/memory/mapper.py
scripts/agent/commands/registry.py         →  /opt/llm/scripts/agent/commands/registry.py
scripts/agent/commands/cmd_audit.py        →  /opt/llm/scripts/agent/commands/cmd_audit.py
scripts/agent/commands/cmd_session.py      →  /opt/llm/scripts/agent/commands/cmd_session.py
scripts/agent/commands/cmd_mcp.py          →  /opt/llm/scripts/agent/commands/cmd_mcp.py
scripts/agent/commands/cmd_config.py       →  /opt/llm/scripts/agent/commands/cmd_config.py
scripts/agent/commands/cmd_context.py      →  /opt/llm/scripts/agent/commands/cmd_context.py
scripts/agent/commands/cmd_tooling.py      →  /opt/llm/scripts/agent/commands/cmd_tooling.py
scripts/agent/commands/cmd_notes.py        →  /opt/llm/scripts/agent/commands/cmd_notes.py
scripts/agent/commands/cmd_debug.py        →  /opt/llm/scripts/agent/commands/cmd_debug.py
scripts/agent/commands/cmd_db.py           →  /opt/llm/scripts/agent/commands/cmd_db.py
scripts/agent/commands/cmd_ingest.py       →  /opt/llm/scripts/agent/commands/cmd_ingest.py
scripts/agent/commands/cmd_memory.py       →  /opt/llm/scripts/agent/commands/cmd_memory.py
scripts/agent/commands/enums.py            →  /opt/llm/scripts/agent/commands/enums.py
scripts/agent/commands/exceptions.py       →  /opt/llm/scripts/agent/commands/exceptions.py
scripts/agent/commands/formatter.py        →  /opt/llm/scripts/agent/commands/formatter.py
scripts/agent/commands/models.py           →  /opt/llm/scripts/agent/commands/models.py
scripts/agent/commands/output_port.py      →  /opt/llm/scripts/agent/commands/output_port.py
scripts/agent/document_repo.py             →  /opt/llm/scripts/agent/document_repo.py
scripts/agent/note_repo.py                 →  /opt/llm/scripts/agent/note_repo.py
scripts/agent/session_message_repo.py      →  /opt/llm/scripts/agent/session_message_repo.py
scripts/agent/history_selection_policy.py  →  /opt/llm/scripts/agent/history_selection_policy.py
scripts/agent/error_injection_service.py   →  /opt/llm/scripts/agent/error_injection_service.py
scripts/agent/lifecycle_protocol.py        →  /opt/llm/scripts/agent/lifecycle_protocol.py
scripts/agent/tool_scheduler.py            →  /opt/llm/scripts/agent/tool_scheduler.py
scripts/agent/tool_enums.py                →  /opt/llm/scripts/agent/tool_enums.py
scripts/agent/tool_exceptions.py           →  /opt/llm/scripts/agent/tool_exceptions.py
scripts/agent/tool_models.py               →  /opt/llm/scripts/agent/tool_models.py
scripts/agent/tool_output.py               →  /opt/llm/scripts/agent/tool_output.py
scripts/agent/turn_result.py               →  /opt/llm/scripts/agent/turn_result.py
scripts/agent/shared/enums.py              →  /opt/llm/scripts/agent/shared/enums.py
scripts/agent/shared/exceptions.py        →  /opt/llm/scripts/agent/shared/exceptions.py
scripts/agent/shared/health_models.py     →  /opt/llm/scripts/agent/shared/health_models.py
scripts/agent/shared/models.py            →  /opt/llm/scripts/agent/shared/models.py
scripts/agent/services/conversation_service.py → /opt/llm/scripts/agent/services/conversation_service.py
scripts/agent/services/enums.py            →  /opt/llm/scripts/agent/services/enums.py
scripts/agent/services/exceptions.py       →  /opt/llm/scripts/agent/services/exceptions.py
scripts/agent/services/models.py           →  /opt/llm/scripts/agent/services/models.py
scripts/agent/services/io_ports.py         →  /opt/llm/scripts/agent/services/io_ports.py
scripts/agent/services/config_reload.py    →  /opt/llm/scripts/agent/services/config_reload.py
scripts/agent/services/context_view.py     →  /opt/llm/scripts/agent/services/context_view.py
scripts/agent/services/db_maintenance_service.py → /opt/llm/scripts/agent/services/db_maintenance_service.py
scripts/agent/services/export_formatter.py → /opt/llm/scripts/agent/services/export_formatter.py
scripts/agent/services/ingest_workflow.py  →  /opt/llm/scripts/agent/services/ingest_workflow.py
scripts/agent/services/mcp_install.py      →  /opt/llm/scripts/agent/services/mcp_install.py
scripts/agent/services/mcp_status.py       →  /opt/llm/scripts/agent/services/mcp_status.py
scripts/agent/services/session_restore.py  →  /opt/llm/scripts/agent/services/session_restore.py
scripts/agent/services/session_title.py    →  /opt/llm/scripts/agent/services/session_title.py
scripts/agent/services/undo_service.py     →  /opt/llm/scripts/agent/services/undo_service.py
scripts/mcp/audit.py                       →  /opt/llm/scripts/mcp/audit.py
scripts/mcp/dispatch.py                    →  /opt/llm/scripts/mcp/dispatch.py
scripts/mcp/models.py                      →  /opt/llm/scripts/mcp/models.py
scripts/mcp/server.py                      →  /opt/llm/scripts/mcp/server.py
scripts/mcp/web_search/server.py           →  /opt/llm/scripts/mcp/web_search/server.py
scripts/mcp/file/delete_models.py          →  /opt/llm/scripts/mcp/file/delete_models.py
scripts/mcp/file/delete_server.py          →  /opt/llm/scripts/mcp/file/delete_server.py
scripts/mcp/file/delete_service.py         →  /opt/llm/scripts/mcp/file/delete_service.py
scripts/mcp/file/read_models.py            →  /opt/llm/scripts/mcp/file/read_models.py
scripts/mcp/file/read_server.py            →  /opt/llm/scripts/mcp/file/read_server.py
scripts/mcp/file/read_service.py           →  /opt/llm/scripts/mcp/file/read_service.py
scripts/mcp/file/read_tools.py             →  /opt/llm/scripts/mcp/file/read_tools.py
scripts/mcp/file/write_models.py           →  /opt/llm/scripts/mcp/file/write_models.py
scripts/mcp/file/write_server.py           →  /opt/llm/scripts/mcp/file/write_server.py
scripts/mcp/file/write_service.py          →  /opt/llm/scripts/mcp/file/write_service.py
scripts/mcp/file/common.py                 →  /opt/llm/scripts/mcp/file/common.py
scripts/mcp/github/models.py               →  /opt/llm/scripts/mcp/github/models.py
scripts/mcp/github/server.py               →  /opt/llm/scripts/mcp/github/server.py
scripts/mcp/github/service.py              →  /opt/llm/scripts/mcp/github/service.py
scripts/mcp/github/tools.py                →  /opt/llm/scripts/mcp/github/tools.py
scripts/mcp/shell/models.py                →  /opt/llm/scripts/mcp/shell/models.py
scripts/mcp/shell/server.py                →  /opt/llm/scripts/mcp/shell/server.py
scripts/mcp/shell/service.py               →  /opt/llm/scripts/mcp/shell/service.py
scripts/mcp/rag_pipeline/models.py         →  /opt/llm/scripts/mcp/rag_pipeline/models.py
scripts/mcp/rag_pipeline/server.py         →  /opt/llm/scripts/mcp/rag_pipeline/server.py
scripts/mcp/rag_pipeline/service.py        →  /opt/llm/scripts/mcp/rag_pipeline/service.py
scripts/mcp/sqlite/models.py               →  /opt/llm/scripts/mcp/sqlite/models.py
scripts/mcp/sqlite/server.py               →  /opt/llm/scripts/mcp/sqlite/server.py
scripts/mcp/sqlite/service.py              →  /opt/llm/scripts/mcp/sqlite/service.py
scripts/mcp/cicd/models.py                 →  /opt/llm/scripts/mcp/cicd/models.py
scripts/mcp/cicd/server.py                 →  /opt/llm/scripts/mcp/cicd/server.py
scripts/mcp/cicd/service.py                →  /opt/llm/scripts/mcp/cicd/service.py
scripts/mcp/mdq/models.py                  →  /opt/llm/scripts/mcp/mdq/models.py
scripts/mcp/mdq/server.py                  →  /opt/llm/scripts/mcp/mdq/server.py
scripts/mcp/mdq/service.py                 →  /opt/llm/scripts/mcp/mdq/service.py
scripts/mcp/git/models.py                  →  /opt/llm/scripts/mcp/git/models.py
scripts/mcp/git/server.py                  →  /opt/llm/scripts/mcp/git/server.py
scripts/mcp/git/service.py                 →  /opt/llm/scripts/mcp/git/service.py
scripts/rag/pipeline.py                    →  /opt/llm/scripts/rag/pipeline.py
scripts/rag/types.py                       →  /opt/llm/scripts/rag/types.py
scripts/rag/repository.py                  →  /opt/llm/scripts/rag/repository.py
scripts/rag/llm.py                         →  /opt/llm/scripts/rag/llm.py
scripts/rag/utils.py                       →  /opt/llm/scripts/rag/utils.py
scripts/rag/stage.py                       →  /opt/llm/scripts/rag/stage.py
scripts/rag/stages/search.py               →  /opt/llm/scripts/rag/stages/search.py
scripts/rag/stages/fusion.py               →  /opt/llm/scripts/rag/stages/fusion.py
scripts/rag/stages/mqe.py                  →  /opt/llm/scripts/rag/stages/mqe.py
scripts/rag/stages/augment.py              →  /opt/llm/scripts/rag/stages/augment.py
scripts/rag/stages/rerank.py               →  /opt/llm/scripts/rag/stages/rerank.py
scripts/rag/ingestion/crawler.py           →  /opt/llm/scripts/rag/ingestion/crawler.py
scripts/rag/ingestion/crawler_utils.py     →  /opt/llm/scripts/rag/ingestion/crawler_utils.py
scripts/rag/ingestion/chunk_splitter.py    →  /opt/llm/scripts/rag/ingestion/chunk_splitter.py
scripts/rag/ingestion/chunk_utils.py       →  /opt/llm/scripts/rag/ingestion/chunk_utils.py
scripts/rag/ingestion/chunk_english.py     →  /opt/llm/scripts/rag/ingestion/chunk_english.py
scripts/rag/ingestion/chunk_japanese.py    →  /opt/llm/scripts/rag/ingestion/chunk_japanese.py
scripts/rag/ingestion/ingester.py          →  /opt/llm/scripts/rag/ingestion/ingester.py
scripts/rag/ingestion/pipeline_utils.py    →  /opt/llm/scripts/rag/ingestion/pipeline_utils.py
scripts/db/config.py                       →  /opt/llm/scripts/db/config.py
scripts/db/create_schema.py                →  /opt/llm/scripts/db/create_schema.py
scripts/db/helper.py                       →  /opt/llm/scripts/db/helper.py
scripts/db/models.py                       →  /opt/llm/scripts/db/models.py
scripts/db/maintenance.py                  →  /opt/llm/scripts/db/maintenance.py
scripts/db/store.py                        →  /opt/llm/scripts/db/store.py
scripts/db/tool_results.py                 →  /opt/llm/scripts/db/tool_results.py
scripts/shared/llm_client.py               →  /opt/llm/scripts/shared/llm_client.py
scripts/shared/tool_executor.py            →  /opt/llm/scripts/shared/tool_executor.py
scripts/shared/types.py                    →  /opt/llm/scripts/shared/types.py
scripts/shared/mcp_config.py               →  /opt/llm/scripts/shared/mcp_config.py
scripts/shared/config_loader.py            →  /opt/llm/scripts/shared/config_loader.py
scripts/shared/formatters.py               →  /opt/llm/scripts/shared/formatters.py
scripts/shared/logger.py                   →  /opt/llm/scripts/shared/logger.py
scripts/shared/git_helper.py               →  /opt/llm/scripts/shared/git_helper.py
scripts/shared/otel_tracer.py              →  /opt/llm/scripts/shared/otel_tracer.py
scripts/shared/plugin_registry.py          →  /opt/llm/scripts/shared/plugin_registry.py
scripts/shared/tool_constants.py           →  /opt/llm/scripts/shared/tool_constants.py
scripts/shared/route_resolver.py           →  /opt/llm/scripts/shared/route_resolver.py
scripts/shared/token_counter.py            →  /opt/llm/scripts/shared/token_counter.py
scripts/shared/tool_cache.py               →  /opt/llm/scripts/shared/tool_cache.py
scripts/shared/tool_spec.py                →  /opt/llm/scripts/shared/tool_spec.py
config/common.toml                         →  /opt/llm/config/common.toml
config/agent.toml                          →  /opt/llm/config/agent.toml
config/rag_pipeline.toml                   →  /opt/llm/config/rag_pipeline.toml
config/rag_pipeline_mcp_server.toml        →  /opt/llm/config/rag_pipeline_mcp_server.toml
config/web_search_mcp_server.toml          →  /opt/llm/config/web_search_mcp_server.toml
config/file_read_mcp_server.toml           →  /opt/llm/config/file_read_mcp_server.toml
config/file_write_mcp_server.toml          →  /opt/llm/config/file_write_mcp_server.toml
config/file_delete_mcp_server.toml         →  /opt/llm/config/file_delete_mcp_server.toml
config/github_mcp_server.toml              →  /opt/llm/config/github_mcp_server.toml
config/shell_mcp_server.toml               →  /opt/llm/config/shell_mcp_server.toml
config/sqlite_mcp_server.toml              →  /opt/llm/config/sqlite_mcp_server.toml
config/cicd_mcp_server.toml               →  /opt/llm/config/cicd_mcp_server.toml
config/mdq_mcp_server.toml                →  /opt/llm/config/mdq_mcp_server.toml
config/git_mcp_server.toml                →  /opt/llm/config/git_mcp_server.toml
config/mcp_servers.toml                   →  /opt/llm/config/mcp_servers.toml
db/rrf.sql                                 →  /opt/llm/db/rrf.sql
init.d/embed-llm                           →  /etc/init.d/embed-llm
init.d/llama-chat-llm                      →  /etc/init.d/llama-chat-llm
init.d/llama-coding-llm                    →  /etc/init.d/llama-coding-llm
init.d/web-search-mcp                      →  /etc/init.d/web-search-mcp
init.d/file-mcp                            →  /etc/init.d/file-mcp
init.d/github-mcp                          →  /etc/init.d/github-mcp
conf.d/web-search-mcp                      →  /etc/conf.d/web-search-mcp
conf.d/github-mcp                          →  /etc/conf.d/github-mcp
```

デプロイ先のディレクトリ構成:

```
/opt/llm/
  ├─ llama.cpp/                                 # llama.cpp ソース・ビルド成果物
  ├─ models/
  │   ├─ gemma-4-e4b-it-Q4_K_M.gguf             # チャット用 LLM (MQE・再ランク兼用, :8002)
  │   ├─ qwen2.5-coder-7b-instruct-q4_k_m.gguf  # コード生成用 LLM (:8001)
  │   └─ multilingual-E5-small.gguf             # 埋込用 LLM (384 次元, :8003)
  ├─ rag-src/                           # クロール済みテキスト (yyyymmddhhmmss-{slug}.txt)
  │   ├─ chunk/                         # チャンク分割済みファイル ({stem}-{idx:04d}.txt)
  │   └─ registered/                    # DB 投入済みファイル (rag_ingester.py が移動)
  ├─ db/
  │   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts)
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
  │   ├─ web_search_mcp_server.toml           # Web 検索サーバ設定 (プロバイダ優先順位・API URL)
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
│   │   ├─ config.py                        # AgentConfig データクラス・設定ローダー (hot-reload 対応)
│   │   ├─ context.py                       # AgentContext: per-session mutable state / DI ハブ
│   │   ├─ session.py                       # AgentSession: セッション CRUD (SQLite 永続化)
│   │   ├─ history.py                       # 会話履歴バッファ・圧縮フック
│   │   ├─ orchestrator.py                  # Orchestrator: ターンレベル制御 (RAG → 圧縮 → LLM → ツール)
│   │   ├─ factory.py                       # AgentFactory: エージェントコンポーネント構築
│   │   ├─ repl_health.py                   # ヘルスチェックサテライト
│   │   ├─ cli_view.py                      # CLIView: readline 設定・RAG 進捗表示・マルチライン入力
│   │   ├─ lifecycle.py                      # restart_stdio(): 残存関数 (routing は factory.py の _ServerLifecycleRouter が担当)
│   │   ├─ http_lifecycle.py                 # HTTP ライフサイクル管理
│   │   ├─ stdio_lifecycle.py                # Stdio ライフサイクル管理
│   │   ├─ llm_turn_runner.py                # LLM ターン実行
│   │   ├─ tool_runner.py                    # ツール実行
│   │   ├─ tool_policy.py                    # ツールポリシー
│   │   ├─ tool_approval.py                  # ツール承認
│   │   ├─ tool_audit.py                     # ツール監査
│   │   ├─ tool_result_formatter.py          # ツール結果整形
│   │   ├─ tool_loop_guard.py                # ループガード
│   │   ├─ document_repo.py                  # ドキュメントリポジトリ
│   │   ├─ note_repo.py                      # ノートリポジトリ
│   │   ├─ session_message_repo.py           # セッションメッセージリポジトリ
│   │   ├─ history_selection_policy.py       # 履歴選択ポリシー
│   │   ├─ error_injection_service.py        # エラー注入サービス
│   │   ├─ lifecycle_protocol.py             # ライフサイクルプロトコル
│   │   ├─ tool_scheduler.py                 # ツールスケジューラ
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
  │   │   └─ commands/
  │   │       ├─ registry.py                  # CommandRegistry: スラッシュコマンドディスパッチャ
  │   │       ├─ cmd_session.py               # /session コマンド
  │   │       ├─ cmd_mcp.py                   # /mcp コマンド
  │   │       ├─ cmd_config.py                # /config, /reload コマンド
  │   │       ├─ cmd_context.py               # /context, /clear, /undo, /history, /system コマンド
  │   │       ├─ cmd_db.py                    # /db コマンド (_DbMixin)
  │   │       ├─ cmd_tooling.py               # /tool, /plan コマンド (_ToolingMixin)
  │   │       ├─ cmd_notes.py                 # /note コマンド (_NotesMixin)
  │   │       ├─ cmd_debug.py                 # /debug コマンド (_DebugMixin)
  │   │       ├─ cmd_ingest.py                # /ingest, /export, /compact コマンド
  │   │       ├─ cmd_memory.py                # /memory コマンド
  │   │       ├─ mixin_base.py                # コマンドミキシングベースクラス
  │   │       └─ utils.py                     # render_history_md() 共有ユーティリティ
  │   │   └─ services/
  │   │       ├─ config_reload.py             # 設定リロードサービス
  │   │       ├─ context_view.py              # コンテキスト表示サービス
  │   │       ├─ db_maintenance_service.py    # DB メンテナンスサービス
  │   │       ├─ export_formatter.py          # エクスポートフォーマッタ
  │   │       ├─ ingest_workflow.py           # インジェストワークフロー
  │   │       ├─ mcp_install.py               # MCP インストール
  │   │       ├─ mcp_status.py                # MCP ステータス
  │   │       ├─ session_restore.py           # セッション復元
  │   │       ├─ session_title.py             # セッションタイトル
  │   │       └─ undo_service.py              # Undo サービス
  │   ├─ mcp/                                 # MCP サーバパッケージ
  │   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
  │   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
  │   │   ├─ web_search/
  │   │   │   └─ server.py                    # Web 検索 MCP サーバ (Brave/Bing/DuckDuckGo, :8004)
  │   │   ├─ file/
  │   │   │   ├─ common.py                    # ファイル MCP 共通バリデーション
  │   │   │   ├─ read_models.py / read_server.py / read_service.py / read_tools.py
  │   │   │   ├─ write_models.py / write_server.py / write_service.py
  │   │   │   └─ delete_models.py / delete_server.py / delete_service.py
  │   │   ├─ github/
  │   │   │   ├─ models.py / server.py / service.py / tools.py  # GitHub MCP サーバ (:8006)
  │   │   ├─ shell/
  │   │   │   ├─ models.py / server.py / service.py             # シェル MCP サーバ (:8009)
  │   │   ├─ rag_pipeline/
  │   │   │   ├─ models.py / server.py / service.py             # RAG パイプライン MCP サーバ (:8010)
  │   │   ├─ sqlite/
  │   │   │   ├─ models.py / server.py / service.py             # SQLite 読み取り専用クエリ MCP サーバ (:8011)
  │   │   ├─ cicd/
  │   │   │   ├─ models.py / server.py / service.py             # GitHub Actions CI/CD MCP サーバ (:8012)
  │   │   ├─ mdq/
  │   │   │   ├─ models.py / server.py / service.py             # Markdown Context Compression Engine MCP サーバ (:8013)
  │   │   └─ git/
  │   │       ├─ models.py / server.py / service.py             # ローカル git 操作 MCP サーバ (:8014)
  │   ├─ rag/                                 # RAG パイプラインパッケージ
  │   │   ├─ pipeline.py                      # RagPipeline: MQE → ベクトル/FTS5 → RRF → 再ランク
  │   │   ├─ types.py                         # RagHit / LLMMessage 共通型 (shared/types.py を再エクスポート)
  │   │   ├─ repository.py                    # chunks_vec / chunks_fts アクセス層
  │   │   ├─ llm.py                           # MQE・再ランク用 LLM 呼び出し
  │   │   ├─ utils.py                         # テキスト正規化・埋込 BLOB 変換ユーティリティ
  │   │   ├─ stage.py                         # RAG ステージ基底クラス
  │   │   ├─ stages/                          # RAG ステージモジュール
  │   │   │   ├─ search.py                    # 検索ステージ (KNN + FTS5)
  │   │   │   ├─ fusion.py                    # 統合ステージ (RRF 統合)
  │   │   │   ├─ mqe.py                       # MQE ステージ (クエリ展開)
  │   │   │   ├─ augment.py                   # 拡張ステージ (メタデータ付加)
  │   │   │   └─ rerank.py                    # 再ランクステージ (LLM 再ランク)
  │   │   └─ ingestion/
  │   │       ├─ crawler.py                   # WebCrawler: BFS クローラ → rag-src/*.txt
  │   │       ├─ crawler_utils.py             # クローラユーティリティ
  │   │       ├─ chunk_splitter.py            # ChunkSplitter: チャンク分割 → rag-src/chunk/*.txt
  │   │       ├─ chunk_utils.py               # チャンク共通ユーティリティ
  │   │       ├─ chunk_english.py             # 英語チャンク分割
  │   │       ├─ chunk_japanese.py            # 日本語チャンク分割
  │   │       ├─ ingester.py                  # RagIngester: 埋込生成・DB 投入 → rag-src/registered/
  │   │       └─ pipeline_utils.py            # パイプライン共通 I/O ユーティリティ
  │   ├─ db/                                  # DB 層パッケージ
  │   │   ├─ create_schema.py                 # SQLite スキーマ初期化 (1 回のみ実行)
  │   │   ├─ helper.py                        # 接続管理 (WAL / busy_timeout)
  │   │   ├─ maintenance.py                   # 運用ポリシー (/db コマンド)
  │   │   ├─ store.py                         # Protocol 抽象レイヤー
  │   │   └─ tool_results.py                  # ツール結果永続化 (/tool show <id>)
  │   └─ shared/                              # 共有ユーティリティパッケージ
  │       ├─ llm_client.py                    # LLMClient: SSE ストリーミング・指数バックオフリトライ
  │       ├─ tool_executor.py                 # ToolExecutor: MCP サーバルーティング・TTL キャッシュ
  │       ├─ types.py                         # 共通型定義 (LLMMessage 等)
  │       ├─ mcp_config.py                    # McpServerConfig データクラス
  │       ├─ config_loader.py                 # TOML/JSON 共通設定ローダー
  │       ├─ formatters.py                    # MCP ツール結果整形・kv ログ文字列生成ユーティリティ
  │       ├─ logger.py                        # ロギング共通セットアップ (エントリポイントのみが import)
  │       ├─ git_helper.py                    # GitPython ラッパー (ブランチ/コミット情報取得)
  │       ├─ otel_tracer.py                   # OTel トレーサー構築 (build_tracer)
  │       ├─ plugin_registry.py               # プラグイン登録デコレータ (@register_command 等)
  │       ├─ tool_constants.py                # ツール分類 frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
  │       ├─ route_resolver.py                # ToolRouteResolver: ツール名 → サーバキーマッピング
  │       └─ token_counter.py                 # トークン推定ユーティリティ
  └─ logs/                                    # 各サービスのログファイル出力先
/etc/init.d/
  ├─ embed-llm                          # OpenRC: multilingual-E5-small 起動スクリプト (:8003)
  ├─ llama-chat-llm                     # OpenRC: gemma-4-e4b 起動スクリプト (:8002)
  ├─ llama-coding-llm                   # OpenRC: qwen2.5-coder-7b 起動スクリプト (:8001)
  ├─ web-search-mcp                     # OpenRC: Web 検索 MCP サーバ起動スクリプト (:8004)
  ├─ file-mcp                           # OpenRC: ファイルシステム MCP サーバ起動スクリプト (:8005)
  └─ github-mcp                         # OpenRC: GitHub MCP サーバ起動スクリプト (:8006)
/etc/conf.d/
  ├─ web-search-mcp                     # BRAVE_API_KEY / BING_API_KEY 環境変数設定
  └─ github-mcp                         # GITHUB_TOKEN (Personal Access Token) 設定
```

---
