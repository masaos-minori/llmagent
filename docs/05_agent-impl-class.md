# エージェント実装詳細 — クラス API

REPL パイプラインフロー・実装詳細 → [`05_agent-impl-flow.md`](05_agent-impl-flow.md)

## 1. agent.py 実装詳細

### 1.1 機能概要

CLI REPL ツール。`agent[chat]>` / `agent[code]>` プロンプトで対話し、HTTP 経由で MCP サーバと通信。LLM が必要なツールを自律選択・実行し、最終回答をターミナルに表示。セッション中は会話履歴を保持してマルチターン対話に対応。

### 1.2 実装方式

| 機能 | 実装 |
|---|---|
| エントリポイント | `python agent.py` (uvicorn 不要; foreground CLI プロセス) |
| 行編集・補完 | Readline ベース; タブ補完でスラッシュコマンドを補完; 履歴は `~/.agent_history` に保存 |
| スラッシュコマンド | `/help` / `/mcp` / `/mcp install` / `/config` / `/stats` / `/context` / `/compact` / `/clear [new]` / `/chat` / `/code` / `/session` / `/db` / `/ingest` / `/debug` / `/rag` / `/note` / `/tool` / `/plan` / `/undo` / `/history` / `/system` / `/set` / `/reload` / `/export` / `/exit` (Ctrl-D も終了) |
| マルチライン入力 | 行末が `\` のとき次行に継続し、空行または `\` のない行で確定。継続プロンプトは `... ` |
| 会話履歴 | セッション中はメッセージリストを保持してマルチターン対話に対応 |
| HTTP クライアント | `httpx.AsyncClient` を起動時生成・終了時クローズ。`AgentContext.http` に保持 |
| DB 接続 | `SQLiteHelper().open(row_factory=True)` を RAG クエリごとにオープン/クローズ (`RagPipeline.augment()`) |
| MCP http 通信 | `ToolExecutor.execute()` が tool 名に応じて MCP サーバ (:8004/:8005/:8006) に HTTP POST。TTL キャッシュ・エラーハンドリングも担当 |
| REPL 本体 | 依存性注入による責務分離: `AgentContext` (共有 mutable state)、`CLIView` (readline・RAG 進捗表示)、`LLMClient` (SSE ストリーミング)、`ToolExecutor` (MCP ルーティング)、`HistoryManager` (履歴圧縮)、`RagPipeline` (MQE→検索→RRF→Rerank)、`CommandRegistry` (スラッシュコマンドディスパッチ)、`AgentConfig` (ホットリロード対象設定)。`AgentREPL` はこれらのコーディネータ。`agent.py` はエントリポイントのみ |
| 起動ディレクトリ | 任意のディレクトリから起動可能。`agent.py` 先頭の `sys.path.insert(0, str(Path(__file__).parent))` がスクリプトの親ディレクトリを `sys.path` に追加するため、CWD に依存しない |

### 1.3 入出力インタフェース

通常入力

`agent[chat]>` または `agent[code]>` プロンプトに任意のテキストを入力。LLM が応答し、ツール呼び出しがあれば実行後に最終回答を表示。

スラッシュコマンド

| コマンド | 動作 |
|---|---|
| `/help` | 利用可能なスラッシュコマンドの一覧を表示 |
| `/mcp` | MCP サーバの状態・ツール一覧・疎通確認を表示 |
| `/mcp install <name>` | 新規 MCP サーバのテンプレートファイルを生成するウィザード。スクリプト骨格・設定 JSON・OpenRC スクリプト・任意で conf.d テンプレートを生成し、手動対応手順 (agent.json への tool 定義追加、deploy.sh への追記等) を表示 |
| `/config` | 設定ファイルのパスと主要設定値を表示 |
| `/stats` | セッション統計 (ターン数・ツール呼び出し数・RAG コンテキスト付加回数・LLM リトライ回数・ツールエラー回数) を表示 |
| `/context` | ランタイム・コンテキスト状態 (メッセージ数・総文字数・圧縮閾値残余量・圧縮回数・現在のシステムプロンプト名・冒頭) を表示。Budget breakdown として system / rag / history / tool_results のカテゴリ別文字数と割合も表示 |
| `/compact` | `context_char_limit` の閾値に関わらず会話履歴を即時圧縮。ターン数が `context_compress_turns * 2` 以下の場合はメッセージを表示してスキップ |
| `/clear [new]` | 会話履歴をシステムプロンプトのみにリセットし、セッション統計・ツールキャッシュをクリア。`new` を付けると新規 DB セッションも開始 |
| `/chat` | LLM をチャットモードに切り替え (gemma-4-e4b, `:8002`) |
| `/code` | LLM をコード生成モードに切り替え (qwen2.5-coder-7b, `:8001`) |
| `/session list [n]` | 過去のセッション一覧を表示 (デフォルト: 直近 20 件。件数指定可) |
| `/session load <id>` | 過去セッションの会話履歴を復元 |
| `/session rename <title>` | 現在のセッションタイトルを指定した文字列に変更 (50 文字以内) |
| `/session delete <id>` | 指定セッションとそのメッセージを DB から削除。現在のセッション ID を指定した場合は警告を表示 |
| `/db stats` | ドキュメント・チャンク・セッション・メッセージの件数を表示 |
| `/db urls [--lang ja\|en] [--limit N]` | 登録済みドキュメントの URL・タイトル・言語・チャンク数・取込日時を一覧表示 |
| `/db clean <url>` | 指定 URL のドキュメントとチャンクを DB から削除 |
| `/db rebuild-fts` | FTS5 の `chunks_fts` インデックスを再構築 |
| `/ingest <path_or_url> [lang] [--snippets-only]` | URL またはローカルファイルパスをクロール → チャンク分割 → DB 投入まで一括実行。`--snippets-only` で Markdown 見出しベースのスニペットチャンキングを強制 |
| `/debug` | RAG パイプラインのデバッグ出力 (MQE クエリ・RRF スコア・rerank 結果) を ON/OFF |
| `/rag search <query>` | RAG パイプライン (MQE → KNN+BM25 → RRF → Rerank) をドライランし取得チャンクを表示。LLM には送信しない |
| `/plan` | プランモードをトグル。ON 時は `plan_blocked_tools` に含まれるツールを自動ブロックし、計画立案に専念させる |
| `/undo` | 直前の user+assistant ターン対をメモリ履歴と DB からロールバック |
| `/history [n]` | 直近 N 件の user/assistant メッセージを先頭 120 文字プレビューで表示 (デフォルト: 5) |
| `/system [name]` | `agent.json` の `system_prompts` で定義したプレセットに切り替え。name 省略時は現在のプレセットと候補一覧を表示 |
| `/set temperature <f>` | LLM 生成温度をランタイムで変更 (0.0–2.0)。`/set` 単体で現在値を表示 |
| `/set max_tokens <n>` | LLM 最大トークン数をランタイムで変更 (≥1) |
| `/reload` | `config/agent.json` を再読み込みしてランタイムパラメータ (RAG / コンテキスト圧縮 / LLM リトライ / ツールキャッシュ / temperature / max_tokens) を即時反映 |
| `/export [md\|json] [file]` | 会話履歴を Markdown または JSON でエクスポート。ファイル名省略時は stdout に出力 |
| `/exit` | エージェントを終了 (Ctrl-D でも可) |

ログファイル: `/opt/llm/logs/agent.log`

### 1.4 エラーハンドリング

| ケース | 対処 |
|---|---|
| LLM リクエスト失敗 (HTTP 503/429・接続エラー) | `_llm_request_with_retry()` が指数バックオフで最大 `llm_max_retries` 回リトライし、全試行失敗時にエラーをターミナルに表示して REPL を継続 |
| LLM リクエスト失敗 (その他) | エラーメッセージをターミナルに表示して REPL を継続 |
| MCP ツール実行失敗 | エラー内容を tool ロールとして LLM に返し、会話を継続 |
| `MAX_TOOL_TURNS` 超過 | 最後の assistant メッセージを表示して終了 |
| 全体例外 | `run()` の `finally` でリソースをクリーンアップし、未捕捉の例外はイベントループに伝播してスタックトレースを標準エラーに出力 |

### 1.5 ログ出力

- ファイル: `/opt/llm/logs/agent.log` + 標準エラー出力
- フォーマット: `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 起動・終了、ツール呼び出し (ターン数・ツール名・引数)、LLM 応答テキスト (`LLM response: ...`)、LLM モード切り替え |
| `WARNING` | MCP ツール実行失敗、`MAX_TOOL_TURNS` 超過 |
| `ERROR` | 全体例外 (`logger.exception`) |

### 1.6 設定項目

`config/common.json` と `config/agent.json` を参照。

config/common.json

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | RAG SQLite データベースのパス |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec 拡張 (.so) のパス |
| `embed_url` | `http://127.0.0.1:8003/embedding` | 埋込 API のエンドポイント (MQE・検索時に使用) |
| `sqlite_timeout` | `30` | `sqlite3.connect()` のタイムアウト秒数。並列書き込み競合時の "database is locked" を防止 |

config/agent.json

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `chat_url` | `http://127.0.0.1:8002/v1/chat/completions` | チャット LLM (MQE・再ランク・回答生成) のエンドポイント |
| `code_url` | `http://127.0.0.1:8001/v1/chat/completions` | コード生成 LLM のエンドポイント |
| `web_search_url` | `http://127.0.0.1:8004` | web-search-mcp サーバのベース URL |
| `file_server_url` | `http://127.0.0.1:8005` | file-mcp サーバのベース URL (HTTP モード時に使用) |
| `github_server_url` | `http://127.0.0.1:8006` | github-mcp サーバのベース URL (HTTP モード時に使用) |
| `default_mode` | `"chat"` | LLM モードのデフォルト値 (`"chat"` または `"code"`) |
| `context_char_limit` | `8000` | 会話履歴の総文字数上限。超過時に古いターンを要約して圧縮 |
| `context_compress_turns` | `4` | 一度に圧縮する最古ターン数 (user+assistant ペア単位) |
| `tool_cache_ttl` | `300` | ツール結果のメモリキャッシュ有効期間 (秒)。同一ツール名+引数の結果を TTL 内で再利用 |
| `llm_max_retries` | `3` | LLM リクエスト失敗時の最大リトライ回数 (HTTP 503/429・接続エラー対象) |
| `llm_retry_base_delay` | `1.0` | 指数バックオフの基準待機秒数 (delay = base_delay × 2^attempt) |
| `http_timeout` | `120.0` | llama-server への HTTP タイムアウト (秒) |
| `web_search_max_results` | `5` | Web 検索で取得する上位件数 |
| `max_tool_turns` | `5` | ツールコーリング最大ターン数 |
| `system_prompt_tool` | (テキスト) | REPL セッション起動時のデフォルトシステムプロンプト (`system_prompts.default` と同値を推奨) |
| `system_prompts` | (辞書) | `/system <name>` で切り替えられるプレセット辞書。デフォルトキー: `default` / `strict` / `creative` |
| `mqe_prompt_template` | (テキスト) | MQE クエリ言い換えプロンプトのテンプレート。`{n_queries}` と `{query}` をプレースホルダとして使用 |
| `rerank_prompt_template` | (テキスト) | Cross-Encoder 再ランクスコアリングプロンプトのテンプレート。`{query}` と `{items_text}` をプレースホルダとして使用 |
| `rag_top_k` | `5` | LLM コンテキストに追加するチャンク数上限。`agent_config.RAG_TOP_K` として参照 |
| `tool_result_max_llm_chars` | `8000` | ツール実行結果を LLM コンテキストに追加する際の文字数上限。超過分は末尾を切り捨て |
| `tool_definitions` | (リスト) | HTTP モードで LLM に提供するツール定義 (OpenAI function calling 形式) |
| `llm_temperature` | `0.2` | メイン LLM の生成温度 (0.0–2.0)。`/set temperature <f>` でセッション中に変更可能 |
| `llm_max_tokens` | `1024` | メイン LLM の最大生成トークン数 (≥1)。`/set max_tokens <n>` でセッション中に変更可能 |
| `use_refiner` | `false` | RAG Refiner を有効化。Rerank 後のチャンクをクエリ関連の要点に圧縮してから LLM コンテキストに投入。失敗時は原文チャンクにフォールバック |
| `refiner_max_tokens` | `512` | Refiner LLM 呼び出しの最大生成トークン数 |
| `refiner_timeout` | `30.0` | Refiner LLM 呼び出しの HTTP タイムアウト秒数 |
| `refiner_max_chars_per_chunk` | `300` | Refiner に渡す 1 チャンクあたりの最大文字数。超過分は切り捨てトークン爆発を防止 |

### 1.7 クラス API

#### AgentREPL (`agent_repl.py`)

`AgentContext` へ全コンポーネントを注入し、REPL ループを駆動する薄いコーディネータ。`agent.py` がインスタンス化して `run()` を呼び出す。

```python
from agent_repl import AgentREPL

await AgentREPL().run()
```

| クラス属性 | 値 | 説明 |
|---|---|---|
| `SLASH_COMMANDS` | `["/help", "/mcp", ..., "/export", "/exit"]` | タブ補完対象のスラッシュコマンド一覧 |

| プロパティ | 説明 |
|---|---|
| `_mode -> str` | アクティブな LLM モードを返す。`CODE_URL` 使用中なら `"code"`、それ以外は `"chat"` |
| `_prompt -> str` | 動的 REPL プロンプト文字列を返す。例: `"agent[chat]> "` / `"agent[code]> "` |

| インスタンス変数 | 説明 |
|---|---|
| `_ctx: AgentContext` | 全コンポーネント参照と per-session mutable state を保持するコンテキストオブジェクト |
| `_view: CLIView` | readline・RAG 進捗表示・マルチライン入力を担うプレゼンテーション層 |
| `_cmds: CommandRegistry \| None` | `run()` 内で初期化されるスラッシュコマンドディスパッチャ |

| メソッド | 説明 |
|---|---|
| `run() -> None` | 全コンポーネントを `AgentContext` に注入し REPL ループを開始 |
| `_run_turn(llm_url) -> str` | SSE ストリーミングでトークン逐次表示し、tool_calls があれば並列実行→再送信を繰り返す。最終回答テキストを返す |
| `_handle_user_message(line) -> None` | `RagPipeline.augment()` でコンテキスト付加 → 履歴追記 → 履歴圧縮 → `_run_turn()` → DB 保存 |
| `_execute_one_tool_call(tc) -> tuple[str, str, dict, str, bool]` | 1 件の `tool_call` dict を解析して `ToolExecutor.execute()` を呼び `(id, name, args, text, is_error)` を返す |
| `_execute_all_tool_calls(tool_calls, turn) -> None` | `asyncio.gather()` で全 tool_call を並列実行し、結果を順序を保って履歴に追記 |

---

#### AgentContext (`agent_context.py`)

全コンポーネント参照と per-session mutable state を一元管理するデータ保持クラス。`AgentREPL.run()` が各フィールドに依存性を注入。

| フィールド | 型 | 説明 |
|---|---|---|
| `history` | `list[LLMMessage]` | 会話履歴 (system / user / assistant / tool ロール) |
| `llm_url` | `str` | アクティブな LLM エンドポイント URL |
| `debug_mode` | `bool` | RAG パイプラインデバッグ出力フラグ |
| `plan_mode` | `bool` | プランモードフラグ。ON 時は `plan_blocked_tools` を自動ブロック |
| `system_prompt_name` | `str` | アクティブなシステムプロンプトプレセット名 |
| `shutdown_requested` | `bool` | グレースフルシャットダウン要求フラグ |
| `stat_turns` | `int` | セッション開始からのユーザーターン累計 |
| `stat_tool_calls` | `int` | ツール呼び出し累計 |
| `stat_rag_hits` | `int` | RAG コンテキスト付加ターン累計 |
| `stat_tool_errors` | `int` | ツール実行エラー累計 |
| `stat_latency` | `dict[str, list[float]]` | ステップ別レイテンシサンプル (秒)。キー: `rag.mqe` / `rag.search` / `rag.rrf` / `rag.rerank` / `llm` |
| `stat_semantic_cache_hits` | `int` | セマンティックキャッシュヒット回数累計 |
| `tool_result_store` | `list[dict]` | 直近 20 件のツール実行結果全文。各要素: `{name, args, text, summarized}` |
| `cfg` | `AgentConfig` | ホットリロード対象ランタイム設定 |
| `session` | `AgentSession` | sessions / messages テーブルへの全 DB 操作 |
| `http` | `httpx.AsyncClient \| None` | 共有 HTTP クライアント |
| `llm` | `LLMClient \| None` | SSE ストリーミング・リトライ担当 |
| `tools` | `ToolExecutor \| None` | MCP ルーティング・TTL キャッシュ担当 |
| `hist_mgr` | `HistoryManager \| None` | 会話履歴文字数カウント・圧縮担当 |
| `rag` | `RagPipeline \| None` | MQE→検索→RRF→Rerank オーケストレーション担当 |
| `stdio_procs` | `dict[str, StdioTransport]` | サーバキー → StdioTransport。stdio MCP サーバのプロセス管理 |

---

#### CLIView (`cli_view.py`)

readline 設定・RAG 進捗表示・マルチライン入力を担うプレゼンテーション層。`RagPipeline` へ `on_status` / `on_clear` コールバックとして渡すことで UI 依存を排除。

| メソッド | 説明 |
|---|---|
| `setup_readline() -> None` | readline 設定・タブ補完・履歴ファイル読み込み |
| `write_history() -> None` | readline 履歴を `~/.agent_history` に保存 |
| `rag_status(msg: str) -> None` | `[rag] {msg}` をインプレース表示 (`\r` 上書き) |
| `rag_clear() -> None` | RAG 進捗表示行をクリア |
| `read_multiline(loop, first_line) -> str` | 行末 `\` の継続入力を読み込み、全行を結合して返す |

---

#### CommandRegistry (`agent_commands.py`)

`AgentContext` を受け取り全スラッシュコマンドをディスパッチするクラス。`_REPLCommandsMixin` ミックスイン方式を廃止し、`AgentREPL` への依存をゼロにした設計。詳細は `docs/06_common.md` section 11 を参照。

| メソッド | 説明 |
|---|---|
| `dispatch(line) -> bool` | スラッシュコマンド行を受け取り対応ハンドラを呼び出す。マッチしなければ `False` を返す |
| `_generate_session_title(first_input) -> None` | 非同期。チャットモデルに max_tokens=20 で1文要約を要求しセッションタイトルを生成。`_handle_user_message()` が第1ターン時に `asyncio.create_task()` で起動 |
| `_cmd_session(args) -> None` | `/session list [n]` / `/session load <id>` / `/session rename <title>` / `/session delete <id>` を処理 |
| `_cmd_db(args) -> None` | `/db stats` / `/db urls [--lang] [--limit]` / `/db clean <url>` / `/db rebuild-fts` を処理 |
| `_cmd_clear(args) -> None` | 会話履歴をシステムプロンプトのみにリセットし、セッション統計・ツールキャッシュをクリア |
| `_cmd_debug() -> None` | `ctx.debug_mode` を ON/OFF トグル |
| `_cmd_rag(args) -> None` | RAG パイプラインをドライランしチャンク・スコア・URL を表示。LLM には送信しない |
| `_cmd_ingest(args) -> None` | Crawler → ChunkSplitter → RagIngester を一括実行して RAG DB に取り込み |
| `_cmd_export(args) -> None` | 会話履歴を Markdown または JSON でエクスポート |

---

#### RagPipeline (`agent_rag.py`)

MQE → KNN+BM25 検索 → RRF → Cross-Encoder Rerank を実行するパイプラインクラス。UI に依存せず、進捗表示は `on_status` / `on_clear` コールバックに委譲。

| メソッド | 説明 |
|---|---|
| `augment(query, debug_fn=None) -> str` | DB をオープン/クローズしてパイプライン全体を実行し、上位チャンクを `[Reference documents]` ブロックとして返す。`use_refiner=true` のとき Rerank 後チャンクを `RagLLM.refine_context()` で圧縮してから返す。失敗時は原文チャンクにフォールバック |
| `run(query, db) -> tuple[list[str], list[list[RagHit]], list[RagHit], list[RagHit]]` | DB 接続を受け取り MQE→検索→RRF→Rerank を実行して `(queries, all_results, merged, reranked)` を返す。finally で `on_clear()` を呼ぶ |
| `expand_queries_safe(query) -> list[str]` | MQE LLM にクエリ言い換えを要求。失敗時は元クエリ 1 件を返す |
| `search_queries(queries, db) -> list[list[RagHit]]` | 各クエリで KNN + BM25 検索を実行し結果リストのリストを返す |
| `rerank_candidates(query, merged) -> list[RagHit]` | Cross-Encoder プロンプトで候補をスコアリングし `rag_min_score` フィルタと `deduplicate_chunks()` を適用して返す |
