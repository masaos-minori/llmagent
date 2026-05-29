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
scripts/agent/repl.py                      →  /opt/llm/scripts/agent/repl.py
scripts/agent/config.py                    →  /opt/llm/scripts/agent/config.py
scripts/agent/context.py                   →  /opt/llm/scripts/agent/context.py
scripts/agent/session.py                   →  /opt/llm/scripts/agent/session.py
scripts/agent/history.py                   →  /opt/llm/scripts/agent/history.py
scripts/agent/orchestrator.py              →  /opt/llm/scripts/agent/orchestrator.py
scripts/agent/repl_tool_exec.py            →  /opt/llm/scripts/agent/repl_tool_exec.py
scripts/agent/repl_health.py               →  /opt/llm/scripts/agent/repl_health.py
scripts/agent/repl_debug.py                →  /opt/llm/scripts/agent/repl_debug.py
scripts/agent/cli_view.py                  →  /opt/llm/scripts/agent/cli_view.py
scripts/agent/memory/layer.py              →  /opt/llm/scripts/agent/memory/layer.py
scripts/agent/memory/store.py              →  /opt/llm/scripts/agent/memory/store.py
scripts/agent/commands/registry.py        →  /opt/llm/scripts/agent/commands/registry.py
scripts/agent/commands/cmd_session.py      →  /opt/llm/scripts/agent/commands/cmd_session.py
scripts/agent/commands/cmd_mcp.py          →  /opt/llm/scripts/agent/commands/cmd_mcp.py
scripts/agent/commands/cmd_config.py       →  /opt/llm/scripts/agent/commands/cmd_config.py
scripts/agent/commands/cmd_context.py      →  /opt/llm/scripts/agent/commands/cmd_context.py
scripts/agent/commands/cmd_rag.py          →  /opt/llm/scripts/agent/commands/cmd_rag.py
scripts/agent/commands/cmd_ingest.py       →  /opt/llm/scripts/agent/commands/cmd_ingest.py
scripts/mcp/models.py                      →  /opt/llm/scripts/mcp/models.py
scripts/mcp/server.py                      →  /opt/llm/scripts/mcp/server.py
scripts/mcp/installer.py                   →  /opt/llm/scripts/mcp/installer.py
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
scripts/rag/pipeline.py                    →  /opt/llm/scripts/rag/pipeline.py
scripts/rag/types.py                       →  /opt/llm/scripts/rag/types.py
scripts/rag/repository.py                  →  /opt/llm/scripts/rag/repository.py
scripts/rag/llm.py                         →  /opt/llm/scripts/rag/llm.py
scripts/rag/utils.py                       →  /opt/llm/scripts/rag/utils.py
scripts/rag/ingestion/crawler.py           →  /opt/llm/scripts/rag/ingestion/crawler.py
scripts/rag/ingestion/crawler_utils.py     →  /opt/llm/scripts/rag/ingestion/crawler_utils.py
scripts/rag/ingestion/chunk_splitter.py    →  /opt/llm/scripts/rag/ingestion/chunk_splitter.py
scripts/rag/ingestion/chunk_utils.py       →  /opt/llm/scripts/rag/ingestion/chunk_utils.py
scripts/rag/ingestion/chunk_english.py     →  /opt/llm/scripts/rag/ingestion/chunk_english.py
scripts/rag/ingestion/chunk_japanese.py    →  /opt/llm/scripts/rag/ingestion/chunk_japanese.py
scripts/rag/ingestion/ingester.py          →  /opt/llm/scripts/rag/ingestion/ingester.py
scripts/rag/ingestion/pipeline_utils.py    →  /opt/llm/scripts/rag/ingestion/pipeline_utils.py
scripts/db/create_schema.py                →  /opt/llm/scripts/db/create_schema.py
scripts/db/migrate.py                      →  /opt/llm/scripts/db/migrate.py
scripts/db/helper.py                       →  /opt/llm/scripts/db/helper.py
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
  │   └─ shell_mcp_server.toml                # シェル MCP サーバ設定 (許可コマンド・タイムアウト)
  ├─ scripts/
  │   ├─ agent.py                             # CLI エントリポイント (AgentREPL を起動)
  │   ├─ agent/                               # エージェント REPL パッケージ
  │   │   ├─ repl.py                          # AgentREPL: 全コンポーネントを AgentContext に注入し REPL ループを駆動
  │   │   ├─ config.py                        # AgentConfig データクラス・設定ローダー (hot-reload 対応)
  │   │   ├─ context.py                       # AgentContext: per-session mutable state / DI ハブ
  │   │   ├─ session.py                       # AgentSession: セッション CRUD (SQLite 永続化)
  │   │   ├─ history.py                       # 会話履歴バッファ・圧縮フック
  │   │   ├─ orchestrator.py                  # Orchestrator: ターンレベル制御 (RAG → 圧縮 → LLM → ツール)
  │   │   ├─ repl_tool_exec.py                # リスクベースのツール承認・監査ログ
  │   │   ├─ repl_health.py                   # ヘルスチェックサテライト
  │   │   ├─ repl_debug.py                    # デバッグサテライト
  │   │   ├─ cli_view.py                      # CLIView: readline 設定・RAG 進捗表示・マルチライン入力
  │   │   ├─ memory/
  │   │   │   ├─ layer.py                     # MemoryLayer: 4 層メモリ管理ファサード
  │   │   │   └─ store.py                     # MemoryStore: SQLite CRUD + vec0 KNN
  │   │   └─ commands/
  │   │       ├─ registry.py                  # CommandRegistry: スラッシュコマンドディスパッチャ
  │   │       ├─ cmd_session.py               # /session コマンド
  │   │       ├─ cmd_mcp.py                   # /mcp コマンド
  │   │       ├─ cmd_config.py                # /config, /reload コマンド
  │   │       ├─ cmd_context.py               # /context コマンド (git ブランチ情報含む)
  │   │       ├─ cmd_rag.py                   # /rag コマンド
  │   │       └─ cmd_ingest.py                # /ingest コマンド
  │   ├─ mcp/                                 # MCP サーバパッケージ
  │   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
  │   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
  │   │   ├─ installer.py                     # MCP サーバ登録ヘルパー
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
  │   │   │   ├─ models.py / server.py / service.py             # シェル MCP サーバ (:8007)
  │   │   └─ rag_pipeline/
  │   │       ├─ models.py / server.py / service.py             # RAG パイプライン MCP サーバ (:8010)
  │   ├─ rag/                                 # RAG パイプラインパッケージ
  │   │   ├─ pipeline.py                      # RagPipeline: MQE → ベクトル/FTS5 → RRF → 再ランク
  │   │   ├─ types.py                         # RagHit / LLMMessage 共通型 (shared/types.py を再エクスポート)
  │   │   ├─ repository.py                    # chunks_vec / chunks_fts アクセス層
  │   │   ├─ llm.py                           # MQE・再ランク用 LLM 呼び出し
  │   │   ├─ utils.py                         # テキスト正規化・埋込 BLOB 変換ユーティリティ
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
  │   │   ├─ migrate.py                       # rag.sqlite → session.sqlite マイグレーション
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
  │       └─ plugin_registry.py               # プラグイン登録デコレータ (@register_command 等)
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
