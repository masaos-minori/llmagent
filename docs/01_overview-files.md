# ファイル構成

アーキテクチャ概要 → [`01_overview-arch.md`](01_overview-arch.md)

## 3. ファイル構成

本リポジトリのファイル構成とデプロイ先の対応。

```
(リポジトリ)                          (デプロイ先)
deploy/deploy.sh               →  (リポジトリからの実行のみ: スクリプト・設定を一括コピー)
deploy/init_db.sh              →  (リポジトリからの実行のみ: DB スキーマ初期化)
deploy/setup_services.sh       →  (リポジトリからの実行のみ: OpenRC サービス登録・起動)
scripts/create_schema.py       →  /opt/llm/scripts/create_schema.py
scripts/web_crawler.py             →  /opt/llm/scripts/web_crawler.py
scripts/chunk_splitter.py       →  /opt/llm/scripts/chunk_splitter.py
scripts/rag_ingester.py         →  /opt/llm/scripts/rag_ingester.py
scripts/agent.py               →  /opt/llm/scripts/agent.py
scripts/web_search_mcp_server.py      →  /opt/llm/scripts/web_search_mcp_server.py
scripts/fileop_mcp_server.py         →  /opt/llm/scripts/fileop_mcp_server.py
scripts/github_mcp_server.py         →  /opt/llm/scripts/github_mcp_server.py
scripts/mcp_models.py           →  /opt/llm/scripts/mcp_models.py
scripts/mcp_server.py           →  /opt/llm/scripts/mcp_server.py
scripts/config_loader.py        →  /opt/llm/scripts/config_loader.py
scripts/agent_rag.py           →  /opt/llm/scripts/agent_rag.py
scripts/rag_utils.py           →  /opt/llm/scripts/rag_utils.py
scripts/sqlite_helper.py            →  /opt/llm/scripts/sqlite_helper.py
scripts/logger.py              →  /opt/llm/scripts/logger.py
scripts/agent_session.py       →  /opt/llm/scripts/agent_session.py
scripts/agent_config.py        →  /opt/llm/scripts/agent_config.py
scripts/agent_commands.py      →  /opt/llm/scripts/agent_commands.py
scripts/formatters.py          →  /opt/llm/scripts/formatters.py
scripts/pipeline_utils.py      →  /opt/llm/scripts/pipeline_utils.py
scripts/llm_client.py          →  /opt/llm/scripts/llm_client.py
scripts/tool_executor.py       →  /opt/llm/scripts/tool_executor.py
scripts/history_manager.py     →  /opt/llm/scripts/history_manager.py
scripts/agent_context.py       →  /opt/llm/scripts/agent_context.py
scripts/cli_view.py            →  /opt/llm/scripts/cli_view.py
scripts/agent_repl.py           →  /opt/llm/scripts/agent_repl.py
config/common.json             →  /opt/llm/config/common.json
config/agent.json              →  /opt/llm/config/agent.json
config/rag_pipeline.json        →  /opt/llm/config/rag_pipeline.json
config/web_search_mcp_server.json →  /opt/llm/config/web_search_mcp_server.json
config/fileop_mcp_server.json  →  /opt/llm/config/fileop_mcp_server.json
config/github_mcp_server.json  →  /opt/llm/config/github_mcp_server.json
db/rrf.sql                     →  /opt/llm/db/rrf.sql
init.d/embed-llm               →  /etc/init.d/embed-llm
init.d/llama-chat-llm          →  /etc/init.d/llama-chat-llm
init.d/llama-coding-llm        →  /etc/init.d/llama-coding-llm
init.d/web-search-mcp          →  /etc/init.d/web-search-mcp
init.d/file-mcp                →  /etc/init.d/file-mcp
init.d/github-mcp              →  /etc/init.d/github-mcp
conf.d/web-search-mcp          →  /etc/conf.d/web-search-mcp
conf.d/github-mcp              →  /etc/conf.d/github-mcp
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
  │   ├─ common.json                    # 共通設定 (DB パス・埋込 URL)
  │   ├─ agent.json                     # エージェント設定 (URL・検索パラメータ・システムプロンプト・ツール定義)
  │   ├─ rag_pipeline.json              # クロール・チャンク設定 (対象 URL・チャンクサイズ・ストップワード)
  │   ├─ web_search_mcp_server.json     # Web 検索サーバ設定 (プロバイダ優先順位・API URL)
  │   ├─ fileop_mcp_server.json         # ファイル MCP サーバ設定 (許可ディレクトリ・サイズ上限)
  │   └─ github_mcp_server.json         # GitHub MCP サーバ設定 (取得件数上限)
  ├─ scripts/
  │   ├─ create_schema.py              # SQLite スキーマ初期化 (1 回のみ実行)
  │   ├─ web_crawler.py               # WebCrawler クラス: BFS クローラ → rag-src/*.txt
  │   ├─ chunk_splitter.py            # ChunkSplitter クラス: チャンク分割 → rag-src/chunk/*.txt
  │   ├─ rag_ingester.py              # RagIngester クラス: 埋込生成・DB 投入 → rag-src/registered/
  │   ├─ agent.py                     # CLI REPL エージェントツール (foreground 起動)
  │   ├─ web_search_mcp_server.py     # Web 検索 MCP サーバ (Brave/Bing/DuckDuckGo)
  │   ├─ fileop_mcp_server.py         # ファイルシステム操作 MCP サーバ
  │   ├─ github_mcp_server.py         # GitHub 操作 MCP サーバ
  │   ├─ mcp_models.py                # MCP /v1/call_tool 統合エンドポイント共通 Pydantic モデル
  │   ├─ mcp_server.py                # MCP サーバ HTTP 起動共通基底クラス
  │   ├─ config_loader.py             # 共通設定ローダー (全スクリプト共通)
  │   ├─ agent_rag.py                 # RAG パイプライン (MQE・KNN/FTS5 検索・RRF・Cross-Encoder 再ランク)
  │   ├─ rag_utils.py                 # テキスト正規化・埋込 BLOB 変換ユーティリティ
  │   ├─ sqlite_helper.py             # SQLite 接続・チャンク書込ヘルパー (共通 DB 操作)
  │   ├─ logger.py                    # ロギング共通セットアップ (全スクリプトが import)
  │   ├─ agent_session.py             # AgentSession クラス: セッション/メッセージ DB 永続化
  │   ├─ agent_config.py              # 設定定数共有モジュール (AgentREPL / CommandRegistry 共用)
  │   ├─ agent_commands.py            # CommandRegistry スラッシュコマンドディスパッチャ
  │   ├─ formatters.py                # MCP ツール結果整形・kv ログ文字列生成ユーティリティ
  │   ├─ pipeline_utils.py            # パイプライン共通ユーティリティ (ファイル収集・JSON 読込)
  │   ├─ llm_client.py                # LLMClient: SSE ストリーミング・指数バックオフリトライ
  │   ├─ tool_executor.py             # ToolExecutor: MCP サーバルーティング・TTL キャッシュ
  │   ├─ history_manager.py           # HistoryManager: 会話履歴文字数カウントと LLM ベース圧縮
  │   ├─ agent_context.py             # AgentContext: per-session mutable state 一元管理
  │   ├─ cli_view.py                  # CLIView: readline 設定・RAG 進捗表示・マルチライン入力
  │   └─ agent_repl.py                 # 対話型 REPL エージェント本体 (RAG+MCP)
  └─ logs/                             # 各サービスのログファイル出力先
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
