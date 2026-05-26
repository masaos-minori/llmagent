# 概要・アーキテクチャ・ファイル構成

## 1. 概要・目的

CPU 専用のローカル環境 (Intel N100 / 16 GB RAM) に llama.cpp を用いた LLM サーバ群と SQLite ベースのベクトル DB を構築し、日本語・英語双方に対応した高精度 RAG システムを実現。

### 1.1 前提条件

| 項目 | 値 |
|---|---|
| OS | Gentoo Linux + OpenRC |
| CPU | Intel N100 (GPU なし、AVX2 非対応) |
| RAM | 16 GB |
| Python | `/opt/llm/venv/` (venv) |
| 用途 | コーディング補助・日本語チャット |

## 2. アーキテクチャ

### 2.1 プロセス構成

```
ユーザー
    │ 対話入力 (agent[chat]> / agent[code]> プロンプト)
    ▼
┌──────────────────────────────────────────────────────┐
│  agent.py (CLI REPL ツール)                           │
│  入力 → RAG 検索 → LLM 呼出 → MCP ツール実行 → 回答  │
└───────┬─────────────┬──────────────────┬─────────────┘
        │             │                  │
        ▼             ▼                  ▼
:8003 embed-LLM  :8001 code-LLM    MCP サーバ群 (stdio または http)
(RAG 検索時)     :8002 chat-LLM    web_search / fileop / github
```

| OpenRC サービス | ポート | モデル | 役割 |
|---|---|---|---|
| `embed-llm` | 8003 | multilingual-E5-small | テキスト → 384 次元ベクトル変換 |
| `llama-chat-llm` | 8002 | gemma-4-e4b | 日本語チャット・MQE・再ランク |
| `llama-coding-llm` | 8001 | qwen2.5-coder-7b | コード生成 |
| `web-search-mcp` | 8004 | — | Web 検索 MCP サーバ (Brave/Bing/DuckDuckGo) |
| `file-mcp` | 8005 | — | ファイルシステム操作 MCP サーバ |
| `github-mcp` | 8006 | — | GitHub 操作 MCP サーバ |

### 2.2 取込パイプライン

取込処理は 3 スクリプトによるファイルベースのパイプライン構成。

```
【1. web_crawler.py (WebCrawler クラス)】
target_urls → BFS クロール (同一オリジン、max_depth=6、crawl_delay=1.5s)
  → HTML 取得 → BeautifulSoup: <pre> 抽出 + Trafilatura: 本文抽出
  → langdetect: 言語判定 (ja / en のみ採用、100 文字未満除外)
  → rag-src/yyyymmddhhmmss-{slug}.txt (JSON: url, title, lang, fetched_at, content, code_blocks)

【2. chunk_splitter.py (ChunkSplitter クラス)】
rag-src/*.txt
  → テキストチャンク分割:
      JA: NFKC 正規化 → Sudachi SplitMode.C → ストップワード除去 → 40〜500 字
      EN: 段落・文境界分割 → ストップワード除去 → 40〜500 字
  → コードチャンク分割: 空行区切り分割 (言語非依存)
  → rag-src/chunk/{stem}-{idx:04d}.txt (JSON: url, title, lang, source_file, chunk_index, chunk_type, content)

【3. rag_ingester.py (RagIngester クラス)】
rag-src/chunk/*.txt
  → URL ごとにグループ化
  → 埋込: POST http://127.0.0.1:8003/embedding {"content": "passage: <text>"}
  → SQLite 投入: documents / chunks / chunks_vec / chunks_fts
  → rag-src/registered/ に移動
```

### 2.3 クエリパイプライン

```
agent.py CLI REPL  (RAG + MCP ツールコーリング統合ツール)
  ユーザーが `agent[chat]>` / `agent[code]>` プロンプトに質問を入力する
  [1] RAG 検索: MQE (直近 2 件の過去ユーザー発話を history_context として渡し検索専用で使用) →
               embed query → KNN+BM25 → RRF → Cross-Encoder 再ランク
               → [Refiner] use_refiner=true のとき 1 回の LLM 呼び出しでチャンクをクエリ関連要点に圧縮
                 (失敗時は原文チャンクにフォールバック)
        → 上位チャンクをコンテキストとしてユーザーメッセージに付加する
           "[Reference documents]\n[Source: {title} | {url}]\n{content}\n\nQuestion: {query}"
  [2] 拡張済みメッセージ + ツール定義を llama.cpp OpenAI 互換 API (:8001 または :8002) へ送信する
  [3] LLM が tool_calls を返したら MCP サーバ経由でツールを実行する
  [4] ツール実行結果を tool ロールとして履歴に追加し、LLM に再送信する ([3] へ戻る)
  [5] tool_calls がなくなったら最終回答をターミナルに表示する
  → セッション中は会話履歴を保持しマルチターン対話が可能; セッションと全メッセージを DB に永続化
  → DB 接続は RAG クエリごとにオープン/クローズ; LLM 応答は SSE ストリーミングでトークン逐次表示

  MCP 呼出方式: 各 MCP サーバの /v1/call_tool エンドポイントに直接 HTTP POST する:
              search_web → :8004/v1/call_tool {name, args}
              list_directory / read_text_file ... → :8005/v1/call_tool {name, args}
              github_search_repositories ... → :8006/v1/call_tool {name, args}
            ツール定義は config/agent.json の tool_definitions を使用
```

### 2.4 MCP サーバ呼出の実現方式と仕様

`agent.py` の REPL は MCP サーバ 3 本の `/v1/call_tool` エンドポイントに直接 HTTP POST。

| 項目 | 内容 |
|---|---|
| 通信方式 | HTTP POST `/v1/call_tool` |
| ツール定義の取得 | `config/agent.json` の `tool_definitions` を使用 |
| MCP サーバ | 事前起動必須 (:8004/:8005/:8006) |

HTTP 通信フロー

```
POST :8004/v1/call_tool     {"name": "search_web", "args": {"query": "..."}}
  → {"result": "[1] タイトル\nURL: ...\nProvider: brave\nスニペット", "is_error": false}

POST :8005/v1/call_tool     {"name": "list_directory", "args": {"path": "..."}}
  → {"result": "[DIR] scripts/\n[FILE] agent.py (12 KB)", "is_error": false}

POST :8006/v1/call_tool     {"name": "github_search_repositories", "args": {"query": "..."}}
  → {"result": "...", "is_error": false}
```

### 2.5 実装済み機能

| 機能 | 実装場所 | 説明 |
|---|---|---|
| RAG 検索 | `agent_rag.py` | MQE + KNN + BM25 + RRF + Cross-Encoder |
| MCP ツールコーリング | `agent_repl.py` | HTTP 専用 (ポート 8004/8005/8006) |
| セッション永続化 | `agent_session.py` | sessions / messages テーブルへの SQLite 保存 |
| セッション復元 | `agent_commands._cmd_session` | `/session load <id>` で過去会話を復元 |
| コンテキスト圧縮 | `history_manager.HistoryManager.compress` | 履歴が `context_char_limit` 超で LLM 要約 |
| ツール結果 TTL キャッシュ | `tool_executor.ToolExecutor.execute` | 同一ツール+引数を `tool_cache_ttl` 秒再利用 |
| SSE ストリーミング | `llm_client.LLMClient.stream` | SSE 経由でトークンを逐次表示する (全ターン共通) |
| LLM 指数バックオフリトライ | `llm_client.LLMClient` | HTTP 429/503・接続エラーで最大 3 回リトライ |
| `/undo` コマンド | `agent_commands._cmd_undo` | 直前 user+assistant ターンを履歴・DB から削除 |
| `/ingest` コマンド | `agent_commands._cmd_ingest` | URL / ローカルファイルを REPL 内から即時クロール→DB 投入 |
| `/export` コマンド | `agent_commands._cmd_export` | 会話を Markdown/JSON でエクスポート |
| `/rag search` | `agent_commands._cmd_rag` | RAG ドライラン (LLM 送信なし) |
| デバッグ出力 | `agent_context.AgentContext.debug_mode` | `/debug` で MQE/RRF/Rerank の中間結果を表示 |
| `/history [n]` コマンド | `agent_commands._cmd_history` | 直近 N 件の user/assistant メッセージを 120 文字プレビューで表示 (デフォルト: 5) |
| マルチライン入力 | `cli_view.CLIView.read_multiline` | 行末 `\` で継続入力、空行/終端行で確定。継続プロンプトは `... ` |
| システムプロンプト切り替え | `agent_commands._cmd_system` | `/system <name>` で `agent.json` の `system_prompts` プレセットをセッション中に切り替え |
| DB 管理コマンド | `agent_commands._cmd_db`, `agent_session` | `/db stats` / `/db urls [--lang] [--limit]` / `/db clean <url>` / `/db rebuild-fts` で DB 管理操作を提供 |
| 埋込並列化 | `RagIngester._ingest_chunk_files` | `ThreadPoolExecutor` で `embed_workers` 件の埋込 HTTP 呼び出しを並列実行 |
| クロールタイムアウト設定化 | `Crawler._fetch_html` | `fetch_timeout` を `rag_pipeline.json` から読み込み、ハードコード値を解消 |
| `/session list [n]` | `agent_commands._cmd_session`, `AgentSession.list_sessions` | 表示件数を引数で指定可能に (デフォルト: 20) |
| 並列ツール実行 | `AgentREPL._execute_all_tool_calls` | `asyncio.gather()` で全 tool_calls を並列実行。結果は元の順序を維持 |
| 並列 BFS クロール | `Crawler.crawl_site` | `httpx.AsyncClient` + `asyncio.Semaphore(crawl_concurrency)` で非同期並列クロール |
| ストリーミング全ターン対応 | `AgentREPL._run_turn` | 全ターンで `LLMClient.stream()` を使用。ツール実行後の継続ターンもトークンを逐次出力する |
| エラー統計の追跡 | `LLMClient.stat_retries`, `AgentContext.stat_tool_errors` | LLM リトライ回数・ツールエラー回数を計測し `/stats` に表示 |
| ツール結果の LLM コンテキストトランケーション | `AgentREPL._execute_all_tool_calls` | `tool_result_max_llm_chars` を超えるツール結果を切り詰めてから `_history` に追加 |
| MQE クエリ埋込の並列化 | `agent_rag.RagPipeline` | `asyncio.gather(return_exceptions=True)` で全クエリの埋込を並列取得 |
| クロール最大ページ数制限 | `Crawler.crawl_site` | `rag_pipeline.json` の `max_pages` で BFS 総ページ数に上限を設ける |
| `RAG_TOP_K` の `agent.json` 設定対応 | `agent_config.RAG_TOP_K` | `agent.json` の `rag_top_k` から読み込むモジュールレベル定数 (デフォルト: 5) |
| SQLiteHelper connect() timeout | `SQLiteHelper.open()` | `common.json` の `sqlite_timeout` を `sqlite3.connect(timeout=)` に渡す |
| `/config` 表示漏れ解消 | `agent_commands._cmd_config` | `tool_cache_ttl` / `llm_max_retries` / `llm_retry_base_delay` を表示 |
| 会話履歴を考慮した RAG クエリ | `AgentREPL._handle_user_message`, `agent_rag.RagPipeline.augment` | 直近 2 件の過去ユーザー発話 (RAG プレフィックスを除去した生クエリ) を `history_context` として MQE に渡す。LLM 最終回答プロンプトには含めない |
| RAG コンテキストへのドキュメントタイトル表示 | `agent_rag.RagPipeline.augment` | ソースブロック形式を `[Source: {title} \| {url}]` に変更。title が空の場合は URL にフォールバックする |
| 並列ツール実行の直列化オプション | `AgentREPL._execute_all_tool_calls`, `agent_config.AgentConfig` | `serial_tool_calls=true` のとき `asyncio.gather()` を直列ループに切り替える。write→read 等の依存関係がある tool_calls で順序保証が必要な場合に有効化する |
| ステップ別レイテンシ計測 | `agent_rag.RagPipeline.run`, `AgentREPL._run_turn`, `agent_context.AgentContext.stat_latency` | RAG 各ステップ (MQE/Search/RRF/Rerank) と LLM 初回呼び出しの所要秒数をセッションごとに蓄積し `/stats` で平均・最大を表示する |
| RAG ステップのランタイムトグル | `agent_commands.CommandRegistry._cmd_rag` | `/rag on\|off` / `/rag mqe on\|off` / `/rag rerank on\|off` で `AgentConfig` の `use_*` フラグを再起動なしに変更する。`/rag` 単体で現在のステータスを表示 |
| セッション横断ノート (`/note`) | `agent_commands._cmd_note`, `agent_session.AgentSession` | `/note add\|list\|delete` で `notes` テーブルに軽量メモを永続化。`auto_inject_notes=true` で起動時にシステムプロンプト末尾へ自動付加する |
| ツール結果の要約・構造化 | `AgentREPL._execute_all_tool_calls`, `agent_rag.RagLLM.summarize_tool_result` | `use_tool_summarize=true` かつ結果が `tool_summarize_threshold` 超のとき LLM で要約してから履歴追加。全文は `ctx.tool_result_store` に保持し `/tool show` で参照可能 |
| セマンティックキャッシュ | `agent_rag.SemanticCache`, `AgentREPL._handle_user_message` | クエリ埋め込みのコサイン類似度が `semantic_cache_threshold` 以上のとき RAG パイプラインをスキップし前回コンテキストを再利用する。`/stats` でヒット数・キャッシュサイズを表示 |
| RAG コンテキスト Refiner | `agent_rag.RagLLM.refine_context`, `agent_rag.RagPipeline.augment` | `use_refiner=true` のとき Rerank 後チャンクを 1 回の LLM 呼び出しでクエリ関連要点に圧縮して投入する。トークン削減と情報密度向上が目的。空出力・例外時は原文チャンクにフォールバックする |
| コンテキスト予算管理 | `agent_commands._budget_breakdown`, `agent_commands.CommandRegistry._cmd_context`, `AgentREPL._run_turn` | `/context` でカテゴリ別（system / rag / history / tool_results）文字数と割合を表示。毎ターン `context_char_limit` の 80% 超過時に `logger.warning` で内訳付き警告を出力 |
| `/context` システムプロンプト名表示 | `agent_commands._cmd_context` | 現在のプレセット名を表示行に追加 |
| `/session rename` / `/session delete` | `agent_commands._cmd_session` | タイトル変更・セッション削除 |
| `/clear new` | `agent_commands._cmd_clear` | 引数 `new` でリセットと同時に新セッションを開始 |
| スライディングウィンドウチャンキング | `chunk_splitter.py` | `chunk_overlap` (デフォルト: 50) 文字分の前チャンク末尾を次チャンク先頭に付加 |
| ローカルファイル取込対応 | `Crawler.crawl_file`, `agent_commands._cmd_ingest` | `/ingest /path/to/file` でローカルファイルを直接 RAG DB に取込む |
| ドキュメント更新検知・再取込 | `Crawler._fetch_html_async`, `RagIngester._get_or_create_document` | ETag / Last-Modified で 304 Not Modified をスキップし、変更時のみ再取込 |
| `/reload` コマンド | `agent_commands._cmd_reload` | `agent.json` を再読込し、ランタイム変更可能なパラメータを即時反映 |
| グレースフルシャットダウン | `agent.py`, `AgentREPL._repl_loop` | `SIGTERM` で `SystemExit(0)` を送出し `run()` の `finally` でリソースを確実にクローズ |
| Logger ログ出力先の分離 | `logger.py` | `logging.basicConfig`（root ロガー一括設定）を廃し、名前付きロガーへ FileHandler を個別付与する方式に変更。`propagate=False` で重複出力を防止 |
| agent.py CWD 非依存起動 | `agent.py` | `sys.path.insert(0, str(Path(__file__).parent))` を追加。`/opt/llm/scripts/` 以外のディレクトリからの起動でも import が成功する |
| HTTP ツールエラーの詳細化 | `tool_executor.ToolExecutor.execute` | エラーメッセージに `status_code` / `url` / `tool_name` を含めるよう変更。トラブル時の原因切り分けを改善 |
| FTS5 クエリの空トークン除去 | `agent_rag._build_fts_query` | トークン sanitize 後に空文字になった要素を除去し、全トークン消失時は `'""'` にフォールバック。FTS5 構文エラーのログに元クエリを追加 |
| Rerank スコアしきい値フィルタ | `agent_rag.RagLLM.cross_encoder_rerank` | `rag_min_score` (0–10) 未満のチャンクを rerank 後に除外。デフォルト 0.0 でフィルタなし。`AgentConfig` 経由でホットリロード対応 |
| 同一ドキュメント重複排除 | `agent_rag.deduplicate_chunks` | URL をドキュメント識別子として使用し、同一ドキュメントのチャンクを `max_chunks_per_doc` (デフォルト: 2) 件に絞る。`rerank_candidates()` がフィルタ後に呼び出す |
| クロール済み URL 一覧 | `agent_commands._cmd_db`, `agent_session.AgentSession.list_documents` | `/db urls [--lang ja\|en] [--limit N]` で登録済み URL・タイトル・言語・チャンク数・取込日時を表示 |
| Markdown スニペットチャンキング | `ChunkSplitter._chunk_markdown_by_heading`, `agent_commands._cmd_ingest` | `/ingest --snippets-only` で Markdown を見出し (`# / ## / ###`) 単位のスニペットに分割して投入する。`md_index_enable=true` でグローバル有効化可能 |
| 二段階ドキュメント取得 | `AgentREPL._run_turn`, `agent_rag.fetch_full_document` | `use_two_stage_fetch=true` のとき LLM が追加コンテキスト要求を示した応答を検出し、`fetch_full_document()` でトップ hits の周辺チャンク (window=±2) を展開して LLM に再送信する |

### 2.6 スラッシュコマンド一覧

| コマンド | 説明 |
|---|---|
| `/help` | ヘルプ表示 |
| `/mcp` | MCP サーバー状態・ツール一覧・疎通確認 |
| `/config` | 設定値と設定ファイルパス表示 |
| `/stats` | セッション統計 (ターン数・ツール呼び出し数・ツールエラー数・LLM リトライ数・RAG ヒット数) |
| `/context` | 履歴文字数・圧縮閾値残余・圧縮回数・システムプロンプト名表示 |
| `/clear [new]` | 履歴をシステムプロンプトのみにリセット (DB 保持)。`new` 指定で新セッション開始 |
| `/chat` / `/code` | LLM モード切り替え |
| `/session list [n]` | 過去セッション一覧 (件数指定可、デフォルト: 20 件) |
| `/session load <id>` | 過去セッション復元 |
| `/session rename <title>` | 現在のセッションタイトルを変更 |
| `/session delete <id>` | 指定セッションと messages を削除 |
| `/db stats` | documents / chunks / sessions / messages の件数を表示 |
| `/db urls [--lang ja\|en] [--limit N]` | 登録済み URL・タイトル・言語・チャンク数・取込日時を一覧表示 |
| `/db clean <url>` | 指定 URL のドキュメントとチャンクを削除 |
| `/db rebuild-fts` | FTS5 インデックスを再構築 |
| `/ingest <url\|path> [lang]` | URL またはローカルファイルを即時取込 |
| `/debug` | RAG デバッグ出力 ON/OFF |
| `/rag search <q>` | RAG ドライラン |
| `/undo` | 直前ターンをロールバック |
| `/history [n]` | 直近 N 件の user/assistant メッセージをプレビュー表示 (デフォルト: 5) |
| `/system [name]` | システムプロンプトのプレセット切り替え |
| `/note add <text>` | セッション横断ノートを追加 |
| `/note list` | ノート一覧を表示 |
| `/note delete <id>` | ノートを削除 |
| `/tool list` | ツール実行結果ストアの一覧を表示 |
| `/tool show <idx>` | ツール実行結果の全文を表示 |
| `/plan` | プランモードをトグル。ON 時は `plan_blocked_tools` のツールをブロック |
| `/set temperature <f>` | LLM 生成温度をランタイムで変更 (0.0–2.0) |
| `/set max_tokens <n>` | LLM 最大トークン数をランタイムで変更 |
| `/compact` | 会話履歴を即時圧縮 |
| `/export [md\|json] [file]` | 会話履歴エクスポート |
| `/reload` | `config/agent.json` を再読込し、ランタイム変更可能なパラメータを即時反映 |
| `/exit` | 終了 (Ctrl-D も可) |

---

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
