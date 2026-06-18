# ファイル構成

アーキテクチャ概要 → [`01_overview-arch.md`](01_overview-arch.md)

## 3. ファイル構成

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
  │   └─ registered/                    # DB 投入済みファイル (ingester.py が移動)
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
  │   │   ├─ lifecycle.py                     # restart_stdio(): 残存関数 (routing は factory.py の _ServerLifecycleRouter が担当)
  │   │   ├─ http_lifecycle.py                # HTTP ライフサイクル管理
  │   │   ├─ stdio_lifecycle.py               # Stdio ライフサイクル管理
  │   │   ├─ llm_turn_runner.py               # LLM ターン実行
  │   │   ├─ tool_runner.py                   # ツール実行
  │   │   ├─ tool_policy.py                   # ツールポリシー
  │   │   ├─ tool_approval.py                 # ツール承認
  │   │   ├─ tool_audit.py                    # ツール監査
  │   │   ├─ tool_result_formatter.py         # ツール結果整形
  │   │   ├─ tool_loop_guard.py               # ループガード
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
  │   │       └─ cmd_memory.py               # /memory コマンド
  │   ├─ mcp/                                 # MCP サーバパッケージ
  │   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
  │   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
  │   │   ├─ web_search/server.py             # Web 検索 MCP サーバ (Brave/Bing/DuckDuckGo, :8004)
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
