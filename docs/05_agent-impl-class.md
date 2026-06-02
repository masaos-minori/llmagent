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
| スラッシュコマンド | `/help` / `/mcp` / `/mcp install` / `/config` / `/stats` / `/context` / `/compact` / `/clear [new]` / `/chat` / `/code` / `/session` / `/db` / `/ingest` / `/debug` / `/note` / `/tool` / `/plan` / `/undo` / `/history` / `/system` / `/set` / `/reload` / `/export` / `/exit` (Ctrl-D も終了) |
| マルチライン入力 | 行末が `\` のとき次行に継続し、空行または `\` のない行で確定。継続プロンプトは `... ` |
| 会話履歴 | セッション中はメッセージリストを保持してマルチターン対話に対応 |
| HTTP クライアント | `httpx.AsyncClient` を起動時生成・終了時クローズ。`AgentContext.http` に保持 |
| DB 接続 | `SQLiteHelper().open(row_factory=True)` を RAG クエリごとにオープン/クローズ (`RagPipeline.augment()`) |
| MCP http 通信 | `ToolExecutor.execute()` が tool 名に応じて MCP サーバ (:8004/:8005/:8006) に HTTP POST。TTL キャッシュ・エラーハンドリングも担当 |
| REPL 本体 | 依存性注入による責務分離: `AgentContext` (共有 mutable state)、`CLIView` (readline・進捗表示)、`LLMClient` (SSE ストリーミング)、`ToolExecutor` (MCP ルーティング)、`HistoryManager` (履歴圧縮)、`CommandRegistry` (スラッシュコマンドディスパッチ)、`AgentConfig` (ホットリロード対象設定)。`AgentREPL` はこれらのコーディネータ。`agent.py` はエントリポイントのみ |
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
| `/debug` | デバッグ出力 (ログレベル切替・audit.log 表示) を ON/OFF |
| `/plan` | プランモードをトグル。ON 時は `plan_blocked_tools` に含まれるツールを自動ブロックし、計画立案に専念させる |
| `/undo` | 直前の user+assistant ターン対をメモリ履歴と DB からロールバック |
| `/history [n]` | 直近 N 件の user/assistant メッセージを先頭 120 文字プレビューで表示 (デフォルト: 5) |
| `/system [name]` | `agent.json` の `system_prompts` で定義したプレセットに切り替え。name 省略時は現在のプレセットと候補一覧を表示 |
| `/set temperature <f>` | LLM 生成温度をランタイムで変更 (0.0–2.0)。`/set` 単体で現在値を表示 |
| `/set max_tokens <n>` | LLM 最大トークン数をランタイムで変更 (≥1) |
| `/reload` | `config/agent.toml` を再読み込みしてランタイムパラメータ (コンテキスト圧縮 / LLM リトライ / ツールキャッシュ / temperature / max_tokens / SSE 設定 / 承認ルール) を即時反映 |
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

`config/common.toml` と `config/agent.toml` を参照。

config/common.toml

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | RAG SQLite データベースのパス |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec 拡張 (.so) のパス |
| `embed_url` | `http://127.0.0.1:8003/embedding` | 埋込 API のエンドポイント (MQE・検索時に使用) |
| `sqlite_timeout` | `30` | `sqlite3.connect()` のタイムアウト秒数。並列書き込み競合時の "database is locked" を防止 |

config/agent.toml

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
| `tool_result_max_llm_chars` | `8000` | ツール実行結果を LLM コンテキストに追加する際の文字数上限。超過分は末尾を切り捨て |
| `tool_definitions` | (リスト) | HTTP モードで LLM に提供するツール定義 (OpenAI function calling 形式) |
| `llm_temperature` | `0.2` | メイン LLM の生成温度 (0.0–2.0)。`/set temperature <f>` でセッション中に変更可能 |
| `llm_max_tokens` | `1024` | メイン LLM の最大生成トークン数 (≥1)。`/set max_tokens <n>` でセッション中に変更可能 |
| `use_refiner` | `false` | RAG Refiner を有効化。Rerank 後のチャンクをクエリ関連の要点に圧縮してから LLM コンテキストに投入。失敗時は原文チャンクにフォールバック |
| `refiner_max_tokens` | `512` | Refiner LLM 呼び出しの最大生成トークン数 |
| `refiner_timeout` | `30.0` | Refiner LLM 呼び出しの HTTP タイムアウト秒数 |
| `refiner_max_chars_per_chunk` | `300` | Refiner に渡す 1 チャンクあたりの最大文字数。超過分は切り捨てトークン爆発を防止 |

### 1.7 クラス API

#### AgentREPL (`agent/repl.py`)

`AgentContext` へ全コンポーネントを注入し、REPL ループを駆動する薄いコーディネータ。ターンレベルのロジック (メモリ注入 → 圧縮 → LLM → ツール実行) は `Orchestrator` に委譲。DI は `agent/factory.py` の `build_agent_context()` が担う。`agent.py` がインスタンス化して `run()` を呼び出す。

```python
from agent.repl import AgentREPL

await AgentREPL().run()
```

| クラス属性 | 値 | 説明 |
|---|---|---|
| `SLASH_COMMANDS` | `["/help", "/mcp", "/config", "/stats", "/context", "/compact", "/clear", "/session", "/ingest", "/debug", "/export", "/undo", "/history", "/system", "/db", "/set", "/reload", "/exit"]` | タブ補完対象のスラッシュコマンド一覧。`/note` / `/plan` / `/tool` / `/memory` は `CommandRegistry` でディスパッチされるが、このリストには含まれない (タブ補完対象外) |

| プロパティ | 説明 |
|---|---|
| `_prompt -> str` | 動的 REPL プロンプト文字列を返す。例: `"agent[:#1]> "` (セッション ID あり) / `"agent> "` (セッション ID なし) |
| `_n_tools -> int` | `tool_definitions` のツール数を返す |

| インスタンス変数 | 説明 |
|---|---|
| `_ctx: AgentContext` | 全コンポーネント参照と per-session mutable state を保持するコンテキストオブジェクト |
| `_view: CLIView` | readline・RAG 進捗表示・マルチライン入力を担うプレゼンテーション層 |
| `_cmds: CommandRegistry \| None` | `_init_components()` 内で初期化されるスラッシュコマンドディスパッチャ |
| `_orchestrator: Orchestrator \| None` | `_init_components()` 内で初期化されるターンレベルロジック委譲先 |

| メソッド | 説明 |
|---|---|
| `run() -> None` | `_init_components()` でサービスを注入し REPL ループを開始。`finally` でメモリ永続化・ウォッチドッグタスクキャンセル・リソースクリーンアップを実行 |
| `_repl_loop() -> None` | `/exit`・EOF・シャットダウン要求まで入力行を処理するメインループ |
| `_init_components() -> None` | `build_agent_context(ctx, view)` で全サービスを注入した後 `_init_command_registry` → `_init_orchestrator` の順で初期化する DI 処理 |
| `_init_audit_logger(ctx) -> None` | 構造化 JSON-lines 形式の audit ログ (`ctx.services.audit_logger`) を初期化 |
| `_init_llm_client(ctx) -> None` | `httpx.AsyncClient` と `LLMClient` を初期化し `ctx.services.http` / `ctx.services.llm` に注入 |
| `_init_command_registry(ctx) -> None` | `CommandRegistry` を初期化し `self._cmds` に代入 |
| `_init_orchestrator(ctx) -> None` | OTel tracer を生成し `Orchestrator` を初期化。`on_turn_start` / `on_turn_end` / `on_error` コールバックを `CLIView` メソッドにバインドして `self._orchestrator` に代入 |
| `_init_plugin_registry() -> None` | `plugins/` ディレクトリからプラグインファイルをロード |
| `_start_subprocess_servers() -> None` | `startup_mode="persistent"` の stdio と `startup_mode="subprocess"` の HTTP サーバを起動し登録。`ondemand` サーバは初回ツール呼び出し時に起動 |
| `_close_resources() -> None` | readline 履歴保存 → `ServerLifecycleManager.shutdown_all()` で stdio サーバ停止 → `httpx.AsyncClient` クローズ (run() finally ブロックから呼び出し) |
| `_print_startup_banner() -> None` | 起動時バナー (`"DB: {chunk_count} chunks | Tools: {n_tools}"`) を表示 |
| `_check_service_health() -> None` | `agent/repl_health.py` の `check_service_health()` に委譲してサービス疎通確認を実行 |
| `_check_tool_definitions() -> None` | `agent/repl_health.py` の `check_tool_definitions()` に委譲してツール定義を検証 |
| `_watchdog_loop() -> None` | `agent/repl_health.py` の `watchdog_loop()` に委譲して MCP サーバ監視を実行 |

---

#### Orchestrator (`agent/orchestrator.py`)

ターンレベルのロジック (メモリ注入 → 履歴圧縮 → LLM ループ → ツール実行 → DB 保存) を担当。`AgentREPL._repl_loop()` が `handle_turn()` を呼び出す。

```python
from agent.orchestrator import Orchestrator

orchestrator = Orchestrator(
    ctx,
    cmds,
    on_turn_start=view.write_turn_start,   # ツールループの各ターン開始時コールバック
    on_turn_end=view.write_turn_end,        # LLM 最終回答確定時コールバック
    on_error=view.write_llm_error,          # LLM エラー通知コールバック
    tracer=tracer,
)
await orchestrator.handle_turn(line)
```

**コンストラクタ引数**

| 引数 | 型 | 説明 |
|---|---|---|
| `ctx` | `AgentContext` | 全コンポーネント参照と per-session mutable state |
| `cmds` | `CommandRegistry` | セッションタイトル生成 (`_generate_session_title`) のために参照 |
| `on_turn_start` | `Callable[[], None] \| None` | `_run_turn()` 内の各ツールループ反復開始時に呼び出されるコールバック (省略可) |
| `on_turn_end` | `Callable[[], None] \| None` | LLM 最終回答テキストが確定したとき (`_finalize_answer()` 内) に呼び出されるコールバック (省略可) |
| `on_error` | `Callable[[Exception], None] \| None` | `_handle_llm_turn()` が LLM エラーを捕捉したとき呼び出されるコールバック (省略可) |
| `tracer` | `Any` | OTel tracer または `None` (`None` の場合 `_NullContextManager` でスパンが no-op になる) |

**パブリックメソッド**

| メソッド | 説明 |
|---|---|
| `handle_turn(line: str) -> None` | `_handle_turn_start` → `_handle_memory_injection` → `_append_user_message` → `_handle_history_compression` → `_handle_llm_turn` の順で 1 ターン分を実行。`LLMTransportError` は `_handle_llm_turn` 内で処理済みのため `handle_turn` では吸収して REPL を継続。`finally` で `_handle_turn_end` を必ず呼び出す |

**プライベートメソッド — ターン制御**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `_handle_turn_start` | `(line: str) -> None` | `ctx.current_turn_id` に UUID4 をセットし、audit_logger へ `turn_start` イベント (`task_id` / `worker_id` / `event_id` / `ts`) を JSON-lines 形式で出力 |
| `_handle_memory_injection` | `(line: str) -> None` | `ctx.services.memory` が非 `None` のとき `on_user_prompt()` を呼び出し、返却された関連メモリスニペットを `[Relevant memories]` ブロックとして system ロールで `ctx.history` へ注入 |
| `_append_user_message` | `(line: str) -> None` | ユーザーメッセージを history に追記し `ctx.stat_turns` をインクリメント。第 1 ターン (`stat_turns==1`) のとき `asyncio.create_task` でセッションタイトル生成を非同期起動 |
| `_handle_history_compression` | `() -> None` | `ctx.services.hist_mgr.compress()` を呼び出し `ctx.history` を上書き。OTel `compress` スパン内で実行 |
| `_handle_llm_turn` | `(llm_url: str) -> str` | OTel `llm` スパン内で `_run_turn()` を呼び出し最終回答をセッション保存して返す。`LLMTransportError` は `_handle_llm_transport_error()` で処理し `on_error` コールバックを呼んで再 raise する。その他の例外は `_handle_general_llm_error()` で処理し同様に再 raise |
| `_handle_turn_end` | `(line: str, answer: str) -> None` | audit_logger へ `turn_end` イベント (`elapsed_ms` / `input_tokens` / `output_tokens` / `parse_error_count` / `heartbeat_timeout_count` / `reconnect_count` / `partial_completion`) を出力し `ctx.current_turn_id` を `None` にクリア |
| `_handle_llm_transport_error` | `(e: LLMTransportError, ctx: AgentContext) -> bool` | `e.partial_text` がある場合は `[INCOMPLETE: ...]` サフィックスを付けて history・session・tool_result_store に保存し `True` を返す。pre-stream 失敗の場合は末尾の user メッセージを pop して `False` を返す |
| `_handle_general_llm_error` | `(e: Exception, ctx: AgentContext) -> None` | 予期しない例外をログ出力し、末尾が user ロールなら history から pop する |

**プライベートメソッド — LLM ループ**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `_run_turn` | `(llm_url: str) -> str` | SSE ストリーミングでトークンを逐次表示し `tool_calls` があれば `execute_all_tool_calls()` で実行 → 再送信を繰り返す。ループ上限は `ctx.cfg.max_tool_turns`。`_check_all_tool_guards()` で dedup / cycle / retry ガードをまとめて適用し、`_check_consecutive_error_limit()` で連続エラーガードを適用。turn==0 のとき `_warn_budget()` と `_record_llm_latency()` を実行。最終回答テキストを返す |
| `_finalize_answer` | `(message: LLMMessage) -> str` | done-turn メッセージを history に追記し `on_turn_end` を呼び出して回答テキストを返す |
| `_warn_budget` | `() -> None` | `context_char_limit > 0` のとき文字数予算、`context_token_limit > 0` のときトークン数予算を確認し、`budget_warn_ratio` 超過時に内訳付き `logger.warning` を出力。`_run_turn()` の `turn==0` のときのみ呼び出される |
| `_inject_mid_turn_error` | `(e: LLMTransportError, turn: int) -> str` | ツールループの 2 ターン目以降に発生した `LLMTransportError` に対して合成 `tool` ロールメッセージを history と tool_result_store に注入し、エラー要約文字列を返す |
| `_span_ctx` | `(name: str) -> Any` | `self._tracer` が非 `None` のとき `tracer.start_as_current_span(name)` を返す。`None` のとき `_NullContextManager` を返す |

**プライベートメソッド — ガード**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `_check_all_tool_guards` | `(seen_calls, round_fingerprints, failed_calls, message) -> str \| None` | cycle → dedup → retry の順でガードを実行し、最初にヒットした終了メッセージを返す。全ガード未検出の場合は `None` |
| `_check_dedup_guard` | `(seen_calls: dict[str, int], message: LLMMessage) -> str \| None` | 同一 (tool_name:args_json) の MD5 キーが `tool_dedup_max_repeats` 回以上出現した場合に `_DEDUP_HINT` を history へ注入し終了メッセージを返す。未検出の場合は `None` |
| `_check_cycle_guard` | `(round_fingerprints: list[str], message: LLMMessage) -> str \| None` | ラウンド単位のツール呼び出しセット MD5 指紋が `tool_cycle_detect_window` 回以上繰り返された場合に `_CYCLE_HINT` を history へ注入し終了メッセージを返す。`tool_cycle_detect_window <= 0` のとき無効。未検出の場合は `None` |
| `_check_retry_guard` | `(failed_calls: set[str], message: LLMMessage) -> str \| None` | 既にエラーになった (tool_name, args) キーへの再試行を検出した場合に `_DEDUP_HINT` を注入し終了メッセージを返す。`tool_error_retry_max <= 0` のとき無効。未検出の場合は `None` |

**プライベートメソッド — ループ制御ヘルパー**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `_update_consecutive_errors` | `(consecutive_errors: int, n_errors: int, n_tool_calls: int) -> int` | 全ツールがエラーの場合に `consecutive_errors + 1` を返し、1 本でも成功があれば `0` にリセットして返す |
| `_check_consecutive_error_limit` | `(consecutive_errors: int) -> str \| None` | `consecutive_errors >= tool_error_max_consecutive` のとき警告ログ出力後に終了メッセージを返す。`tool_error_max_consecutive <= 0` のとき無効 |
| `_record_llm_latency` | `(t0_llm: float, turn: int) -> None` | `turn == 0` のときのみ `ctx.stat_latency["llm"]` にレイテンシサンプル (秒) を追記 |

---

#### ServerLifecycleManager (`agent/lifecycle.py`)

MCP サーバサブプロセスの起動・停止・アイドルタイムアウト管理を担当。`LifecycleProtocol` (`shared/tool_executor.py`) を実装し、`ToolExecutor.set_lifecycle()` 経由で注入される。`AgentREPL._init_tool_executor()` で生成され `ctx.services.lifecycle` に格納。

```python
from agent.lifecycle import ServerLifecycleManager

lifecycle = ServerLifecycleManager(
    server_configs=ctx.cfg.mcp_servers,
    tool_executor=ctx.services.tools,
    stdio_procs=ctx.services.stdio_procs,
)
await lifecycle.ensure_ready("my_server")
await lifecycle.shutdown_all()
```

**コンストラクタ引数**

| 引数 | 型 | 説明 |
|---|---|---|
| `server_configs` | `dict[str, McpServerConfig]` | `config/agent.toml` の `[mcp_servers]` エントリ。`transport` / `startup_mode` / `cmd` / `working_dir` / `env` / `idle_timeout_sec` を参照 |
| `tool_executor` | `ToolExecutor` | ondemand 起動後に `set_transport()` で新トランスポートを登録するために参照 |
| `stdio_procs` | `dict[str, StdioTransport]` | `ctx.services.stdio_procs` を共有参照。persistent サーバが既に登録済みのため、ondemand サーバはここに追記する |

**メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `ensure_ready` | `(server_key: str) -> None` | `http+subprocess` の場合は `_verify_http_subprocess()` を呼んで no-op 終了。`persistent` の場合は no-op。`ondemand` の場合は `_ensure_ondemand_stdio()` で起動を試みる |
| `shutdown_all` | `() -> None` | `stdio_procs` に登録されている全トランスポートに対して `stop()` を呼び出す。エラーは `logger.warning` で記録し続行 |
| `shutdown_idle` | `() -> None` | `startup_mode="ondemand"` かつ `idle_timeout_sec > 0` のサーバで `_last_called` からの経過秒数が閾値を超えているものを `stop()` する。ウォッチドッグ (`_watchdog_loop`) から定期呼び出し |
| `_verify_http_subprocess` | `(server_key: str) -> None` | HTTP subprocess サーバが `_http_procs` に存在しないか既に停止していれば `logger.warning` を出力 (起動は行わない) |
| `_ensure_ondemand_stdio` | `(server_key: str) -> None` | ロックなし fast-path で生存確認し、未起動または停止中の場合は per-server `asyncio.Lock` で二重起動を防ぎながら `_start_ondemand_server()` を呼び出す |
| `_start_ondemand_server` | `(server_key: str) -> None` | `StdioTransport` を生成・起動し `ToolExecutor.set_transport()` → `stdio_procs` 登録を実行。`start()` 失敗時は `logger.error` で記録し続行 |

---

#### AgentContext (`agent/context.py`)

全コンポーネント参照と per-session mutable state を一元管理するデータ保持クラス。`AgentREPL._init_components()` が各フィールドに依存性を注入。全サービス参照は `ctx.services.<key>` 経由でアクセスする (`AgentContext` に直接サービスフィールドは存在しない)。詳細は `docs/06_ref-agent-context.md` を参照。

| フィールド | 型 | 説明 |
|---|---|---|
| `services` | `ServiceContainer` | 全サービス参照を保持する DI コンテナ。`http` / `llm` / `tools` / `hist_mgr` / `stdio_procs` / `audit_logger` / `memory` / `lifecycle` を含む |
| `history` | `list[LLMMessage]` | 会話履歴 (system / user / assistant / tool ロール) |
| `llm_url` | `str` | アクティブな LLM エンドポイント URL |
| `debug_mode` | `bool` | RAG パイプラインデバッグ出力フラグ |
| `plan_mode` | `bool` | プランモードフラグ。`True` のとき `plan_blocked_tools` を自動ブロック |
| `system_prompt_name` | `str` | アクティブなシステムプロンプトプレセット名 |
| `shutdown_requested` | `bool` | グレースフルシャットダウン要求フラグ |
| `current_turn_id` | `str \| None` | `Orchestrator.handle_turn()` 開始時に UUID4 をセット; `finally` でクリア |
| `current_rag_query_id` | `str \| None` | 予約フィールド。in-process RAG 除去後は常に `None` |
| `stat_turns` | `int` | ユーザーターン累計 |
| `stat_tool_calls` | `int` | ツール呼び出し累計 |
| `stat_rag_hits` | `int` | RAG コンテキスト付加ターン累計 |
| `stat_tool_errors` | `int` | ツール実行エラー累計 |
| `stat_latency` | `dict[str, list[float]]` | ステップ別レイテンシサンプル (秒)。キー: `rag.mqe` / `rag.search` / `rag.rrf` / `rag.rerank` / `llm` |
| `stat_semantic_cache_hits` | `int` | セマンティックキャッシュヒット回数累計 |
| `stat_input_tokens` | `int \| None` | LLM 入力トークン累計。`None` = エンドポイントが `usage` を返さなかった |
| `stat_output_tokens` | `int \| None` | LLM 出力トークン累計。`None` = エンドポイントが `usage` を返さなかった |
| `tool_result_store` | `ToolResultStore` | ツール実行結果の永続ストア。`/tool list` / `/tool show` で参照 |
| `cfg` | `AgentConfig` | ホットリロード対象ランタイム設定 |
| `session` | `AgentSession` | セッション/メッセージ DB 操作 |

---

#### CLIView (`agent/cli_view.py`)

readline 設定・RAG 進捗表示・マルチライン入力を担うプレゼンテーション層。`RagPipeline` へ `on_status` / `on_clear` コールバックとして渡すことで UI 依存を排除。`Orchestrator` には `on_turn_start` / `on_turn_end` / `on_error` コールバックとして渡す。ライブラリモジュールは `print()` を直接呼ばず、すべて `CLIView` 経由で出力する。

| メソッド | 説明 |
|---|---|
| `setup_readline() -> None` | readline 設定・タブ補完・履歴ファイル読み込み |
| `write_history() -> None` | readline 履歴を `~/.agent_history` に保存 |
| `write_token(token: str) -> None` | SSE ストリーミングトークン 1 件を末尾改行なしで stdout に出力。`LLMClient` の `on_token` コールバックとして渡す |
| `write_compress_notice(n: int) -> None` | 履歴圧縮完了通知 (`[context] history compressed (n messages summarized)`) を表示。`HistoryManager` の `on_compress` コールバックとして渡す |
| `write_turn_start() -> None` | LLM ストリーミングターン開始前に空行を出力。`Orchestrator` の `on_turn_start` コールバックとして渡す |
| `write_turn_end() -> None` | LLM 最終回答後に空行を出力。`Orchestrator` の `on_turn_end` コールバックとして渡す |
| `write_llm_error(e: Exception) -> None` | LLM リクエスト失敗を `\nError: {e}\n` の形式でユーザに通知。`Orchestrator` の `on_error` コールバックとして渡す |
| `rag_status(msg: str) -> None` | `[rag] {msg}` をインプレース表示 (`\r` 上書き) |
| `rag_clear() -> None` | RAG 進捗表示行をクリア |
| `read_multiline(loop, first_line) -> str` | 行末 `\` の継続入力を読み込み、全行を結合して返す |

---

#### CommandRegistry (`agent/commands/registry.py`)

`AgentContext` を受け取り全スラッシュコマンドをディスパッチするクラス。`_REPLCommandsMixin` ミックスイン方式を廃止し、`AgentREPL` への依存をゼロにした設計。詳細は `docs/06_common.md` section 11 を参照。

| メソッド | 説明 |
|---|---|
| `dispatch(line) -> bool` | スラッシュコマンド行を受け取り対応ハンドラを呼び出す。マッチしなければ `False` を返す |
| `_generate_session_title(first_input) -> None` | 非同期。チャットモデルに max_tokens=20 で1文要約を要求しセッションタイトルを生成。`Orchestrator._append_user_message()` が第1ターン時に `asyncio.create_task()` で起動 |
| `_cmd_session(args) -> None` | `/session list [n]` / `/session load <id>` / `/session rename <title>` / `/session delete <id>` を処理 |
| `_cmd_db(args) -> None` | `/db stats` / `/db urls [--lang] [--limit]` / `/db clean <url>` / `/db rebuild-fts` / `/db health` / `/db checkpoint [MODE]` / `/db vacuum` / `/db purge [--max-sessions N] [--max-age-days N]` / `/db recover [<backup-path>]` を処理 |
| `_cmd_clear(args) -> None` | 会話履歴をシステムプロンプトのみにリセットし、セッション統計・ツールキャッシュをクリア |
| `_cmd_debug() -> None` | `ctx.debug_mode` を ON/OFF トグル |
| `_cmd_ingest(args) -> None` | Crawler → ChunkSplitter → RagIngester を一括実行して RAG DB に取り込み |
| `_cmd_export(args) -> None` | 会話履歴を Markdown または JSON でエクスポート |

---

#### RagPipeline (`rag/pipeline.py`)

MQE → KNN+BM25 検索 → RRF → Cross-Encoder Rerank を実行するパイプラインクラス。UI に依存せず、進捗表示は `on_status` / `on_clear` コールバックに委譲。

| メソッド | 説明 |
|---|---|
| `augment(query, debug_fn=None) -> str` | DB をオープン/クローズしてパイプライン全体を実行し、上位チャンクを `[Reference documents]` ブロックとして返す。`use_refiner=true` のとき Rerank 後チャンクを `RagLLM.refine_context()` で圧縮してから返す。失敗時は原文チャンクにフォールバック |
| `run(query, db) -> tuple[list[str], list[list[RagHit]], list[RagHit], list[RagHit]]` | DB 接続を受け取り MQE→検索→RRF→Rerank を実行して `(queries, all_results, merged, reranked)` を返す。finally で `on_clear()` を呼ぶ |
| `expand_queries_safe(query) -> list[str]` | MQE LLM にクエリ言い換えを要求。失敗時は元クエリ 1 件を返す |
| `search_queries(queries, db) -> list[list[RagHit]]` | 各クエリで KNN + BM25 検索を実行し結果リストのリストを返す |
| `rerank_candidates(query, merged) -> list[RagHit]` | Cross-Encoder プロンプトで候補をスコアリングし `rag_min_score` フィルタと `deduplicate_chunks()` を適用して返す |
