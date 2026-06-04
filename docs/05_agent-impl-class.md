# エージェント実装詳細 — クラス API

REPL パイプラインフロー・実装詳細 → [`05_agent-impl-flow.md`](05_agent-impl-flow.md)

## 1. agent.py 実装詳細

### 1.1 機能概要

CLI REPL ツール。`agent>` (または `agent[:#N]>`) プロンプトで対話し、HTTP 経由で MCP サーバと通信。LLM が必要なツールを自律選択・実行し、最終回答をターミナルに表示。セッション中は会話履歴を保持してマルチターン対話に対応。

### 1.2 実装方式

| 機能 | 実装 |
|---|---|
| エントリポイント | `python agent.py` (uvicorn 不要; foreground CLI プロセス) |
| 行編集・補完 | Readline ベース; タブ補完でスラッシュコマンドを補完; 履歴は `~/.agent_history` に保存 |
| スラッシュコマンド | `/help` / `/mcp` / `/mcp install` / `/config` / `/stats` / `/context` / `/compact` / `/clear [new]` / `/session` / `/db` / `/ingest` / `/debug` / `/note` / `/tool` / `/plan` / `/undo` / `/history` / `/system` / `/set` / `/reload` / `/memory` / `/export` / `/exit` (Ctrl-D も終了) |
| マルチライン入力 | 行末が `\` のとき次行に継続し、空行または `\` のない行で確定。継続プロンプトは `... ` |
| 会話履歴 | セッション中はメッセージリストを保持してマルチターン対話に対応 |
| HTTP クライアント | `httpx.AsyncClient` を起動時生成・終了時クローズ。`ctx.services.http` に保持 |
| DB 接続 | `SQLiteHelper().open(row_factory=True)` をクエリごとにオープン/クローズ |
| MCP http 通信 | `ToolExecutor.execute()` が tool 名に応じて MCP サーバに HTTP POST。TTL キャッシュ・エラーハンドリングも担当 |
| REPL 本体 | 依存性注入による責務分離: `AgentContext` (共有 mutable state)、`CLIView` (readline・進捗表示)、`LLMClient` (SSE ストリーミング)、`ToolExecutor` (MCP ルーティング)、`HistoryManager` (履歴圧縮)、`CommandRegistry` (スラッシュコマンドディスパッチ)、`AgentConfig` (ホットリロード対象設定)。`AgentREPL` はこれらのコーディネータ。`agent.py` はエントリポイントのみ |
| 起動ディレクトリ | 任意のディレクトリから起動可能。`agent.py` 先頭の `sys.path.insert(0, str(Path(__file__).parent))` がスクリプトの親ディレクトリを `sys.path` に追加するため、CWD に依存しない |

### 1.3 入出力インタフェース

通常入力

`agent>` (または `agent[:#N]>`) プロンプトに任意のテキストを入力。LLM が応答し、ツール呼び出しがあれば実行後に最終回答を表示。

スラッシュコマンド

| コマンド | 動作 |
|---|---|
| `/help` | 利用可能なスラッシュコマンドの一覧を表示 |
| `/mcp` | MCP サーバの状態・ツール一覧・疎通確認を表示 |
| `/mcp install <name>` | 新規 MCP サーバのテンプレートファイルを生成するウィザード。スクリプト骨格・設定 JSON・OpenRC スクリプト・任意で conf.d テンプレートを生成し、手動対応手順 (agent.json への tool 定義追加、deploy.sh への追記等) を表示 |
| `/config` | 設定ファイルのパスと主要設定値を表示 |
| `/stats` | セッション統計 (ターン数・ツール呼び出し数・LLM リトライ回数・ツールエラー回数・入出力トークン数等) を表示 |
| `/context` | ランタイム・コンテキスト状態 (メッセージ数・総文字数・圧縮閾値残余量・圧縮回数・現在のシステムプロンプト名・冒頭) を表示。Budget breakdown として system / history / tool_results のカテゴリ別文字数と割合も表示 |
| `/compact` | `context_char_limit` の閾値に関わらず会話履歴を即時圧縮。ターン数が `context_compress_turns * 2` 以下の場合はメッセージを表示してスキップ |
| `/clear [new]` | 会話履歴をシステムプロンプトのみにリセットし、セッション統計・ツールキャッシュをクリア。`new` を付けると新規 DB セッションも開始 |
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
| `/reload` | 分割設定ファイル群を再読み込みしてランタイムパラメータ (コンテキスト圧縮 / LLM リトライ / ツールキャッシュ / temperature / max_tokens / SSE 設定 / 承認ルール) を即時反映 |
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

詳細は `docs/06_ref-agent-config.md` を参照。設定は複数のファイルに分割されている。

config/common.toml (DB パス・sqlite-vec・embed 等)

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | RAG SQLite データベースのパス |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec 拡張 (.so) のパス |
| `embed_url` | `http://127.0.0.1:8003/embedding` | 埋込 API のエンドポイント |
| `sqlite_timeout` | `30` | `sqlite3.connect()` のタイムアウト秒数 |

分割設定ファイル群 (`config/llm.toml` / `config/tools.toml` / `config/context.toml` 等)

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `llm_url` | `http://127.0.0.1:8002/v1/chat/completions` | LLM エンドポイント (単一 URL) |
| `context_char_limit` | `8000` | 会話履歴の総文字数上限。超過時に古いターンを要約して圧縮 |
| `context_compress_turns` | `4` | 一度に圧縮する最古ターン数 (user+assistant ペア単位) |
| `tool_cache_ttl` | `300` | ツール結果のメモリキャッシュ有効期間 (秒) |
| `llm_max_retries` | `3` | LLM リクエスト失敗時の最大リトライ回数 |
| `http_timeout` | `120.0` | llama-server への HTTP タイムアウト (秒) |
| `max_tool_turns` | `5` | ツールコーリング最大ターン数 |
| `llm_temperature` | `0.2` | メイン LLM の生成温度 (0.0–2.0) |
| `llm_max_tokens` | `1024` | メイン LLM の最大生成トークン数 |
| `title_llm_temperature` | `0.1` | セッションタイトル生成 LLM の生成温度 |
| `title_llm_max_tokens` | `20` | セッションタイトル生成 LLM の最大生成トークン数 |

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
| `_view: CLIView` | readline・進捗表示・マルチライン入力を担うプレゼンテーション層 |
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

ターンレベルのファサード (メモリ注入 → 履歴圧縮 → LLM ループ → DB 保存) を担当。LLM ストリーミングとツールループは `LLMTurnRunner` に委譲し、ループガード管理は `ToolLoopGuard` に委譲する。`AgentREPL._repl_loop()` が `handle_turn()` を呼び出す。

```python
from agent.orchestrator import Orchestrator

orchestrator = Orchestrator(
    ctx,
    on_first_turn=cmds._generate_session_title,
    on_turn_start=view.write_turn_start,
    on_turn_end=view.write_turn_end,
    on_error=view.write_llm_error,
    tracer=tracer,
)
await orchestrator.handle_turn(line)
```

**コンストラクタ引数**

| 引数 | 型 | 説明 |
|---|---|---|
| `ctx` | `AgentContext` | 全コンポーネント参照と per-session mutable state |
| `on_first_turn` | `Callable[[str], Any] \| None` | 第 1 ターン時に非同期タスクとして呼び出すコールバック。セッションタイトル生成に使用 (省略可) |
| `on_turn_start` | `Callable[[], None] \| None` | LLMTurnRunner 内の各ツールループ反復開始時に呼び出されるコールバック (省略可) |
| `on_turn_end` | `Callable[[], None] \| None` | LLM 最終回答テキストが確定したとき呼び出されるコールバック (省略可) |
| `on_error` | `Callable[[Exception], None] \| None` | `_handle_llm_turn()` が LLM エラーを捕捉したとき呼び出されるコールバック (省略可) |
| `tracer` | `Any` | OTel tracer または `None` (`None` の場合スパンが no-op になる) |

**戻り値型**

`TurnResult(success, answer, error_kind)` — `_handle_llm_turn` の戻り値。`success=False` のとき `error_kind` にエラー種別文字列が入る。

**パブリックメソッド**

| メソッド | 説明 |
|---|---|
| `handle_turn(line: str) -> None` | `_handle_turn_start` → `_handle_memory_injection` → `_append_user_message` → `_handle_history_compression` → `_handle_llm_turn` の順で 1 ターン分を実行。`LLMTransportError` は明示的に捕捉して REPL を継続。`finally` で `_handle_turn_end` を必ず呼び出す |

**プライベートメソッド — ターン制御**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `_handle_turn_start` | `(line: str) -> None` | `ctx.turn.current_turn_id` に UUID4 をセットし、audit_logger へ `turn_start` イベント (`task_id` / `worker_id` / `event_id` / `ts`) を JSON-lines 形式で出力 |
| `_handle_memory_injection` | `(line: str) -> None` | `ctx.services.memory` が非 `None` のとき `on_user_prompt()` を呼び出し、返却された関連メモリスニペットを `[Relevant memories]` ブロックとして system ロールで `ctx.conv.history` へ注入 |
| `_append_user_message` | `(line: str) -> None` | ユーザーメッセージを `ctx.conv.history` に追記し `ctx.stats.stat_turns` をインクリメント。第 1 ターン (`stat_turns==1`) のとき `asyncio.create_task` で `on_first_turn` を非同期起動 |
| `_sync_system_prompt` | `() -> None` | `ctx.conv.system_prompt_content` を `ctx.conv.history[0]` へ反映する。`_append_user_message()` が各ターン開始時に呼び出す |
| `_handle_history_compression` | `() -> None` | `ctx.services.hist_mgr.compress()` を呼び出し `ctx.conv.history` を上書き。OTel `compress` スパン内で実行 |
| `_handle_llm_turn` | `(llm_url: str) -> TurnResult` | OTel `llm` スパン内で `_llm_runner.run(llm_url)` を呼び出し最終回答をセッション保存して `TurnResult` を返す。`LLMTransportError` は `_handle_llm_transport_error()` で処理し `on_error` コールバックを呼ぶ。その他の例外は `_handle_general_llm_error()` で処理。いずれもエラー結果の `TurnResult` を返す |
| `_handle_turn_end` | `(line: str, answer: str, turn_started_at: float, error_kind: str \| None) -> None` | audit_logger へ `turn_end` イベント (`elapsed_ms` / `input_tokens` / `output_tokens` / `parse_error_count` / `heartbeat_timeout_count` / `reconnect_count` / `partial_completion` / `error_kind`) を出力し `ctx.turn.current_turn_id` を `None` にクリア |
| `_handle_llm_transport_error` | `(e: LLMTransportError, ctx: AgentContext) -> bool` | `e.partial_text` がある場合は `[INCOMPLETE: ...]` サフィックスを付けて `ctx.conv.history`・session・tool_result_store に保存し `True` を返す。pre-stream 失敗の場合は末尾の user メッセージを pop して `False` を返す |
| `_handle_general_llm_error` | `(e: Exception, ctx: AgentContext) -> None` | 予期しない例外をログ出力し、末尾が user ロールなら `ctx.conv.history` から pop する |

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
| `server_configs` | `dict[str, McpServerConfig]` | `config/mcp_servers.toml` の `[mcp_servers]` エントリ。`transport` / `startup_mode` / `cmd` / `working_dir` / `env` / `idle_timeout_sec` を参照 |
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
| `services` | `AppServices` | 全サービス参照を保持する DI コンテナ。`http` / `llm` / `tools` / `hist_mgr` / `stdio_procs` / `audit_logger` / `memory` / `lifecycle` を含む |
| `history` | `list[LLMMessage]` | 会話履歴 (system / user / assistant / tool ロール) |
| `llm_url` | `str` | アクティブな LLM エンドポイント URL |
| `debug_mode` | `bool` | デバッグ出力フラグ |
| `plan_mode` | `bool` | プランモードフラグ。`True` のとき `plan_blocked_tools` を自動ブロック |
| `system_prompt_name` | `str` | アクティブなシステムプロンプトプレセット名 |
| `system_prompt_content` | `str` | 正規のシステムプロンプト文字列。`Orchestrator._sync_system_prompt()` が各ターン前に `history[0]` へ反映 |
| `shutdown_requested` | `bool` | グレースフルシャットダウン要求フラグ |
| `current_turn_id` | `str \| None` | `Orchestrator.handle_turn()` 開始時に UUID4 をセット; `finally` でクリア |
| `stat_turns` | `int` | ユーザーターン累計 |
| `stat_tool_calls` | `int` | ツール呼び出し累計 |
| `stat_tool_errors` | `int` | ツール実行エラー累計 |
| `stat_latency` | `dict[str, list[float]]` | ステップ別レイテンシサンプル (秒)。キー: `llm` |
| `stat_semantic_cache_hits` | `int` | セマンティックキャッシュヒット回数累計 |
| `stat_input_tokens` | `int \| None` | LLM 入力トークン累計。`None` = エンドポイントが `usage` を返さなかった |
| `stat_output_tokens` | `int \| None` | LLM 出力トークン累計。`None` = エンドポイントが `usage` を返さなかった |
| `tool_result_store` | `ToolResultStore` | ツール実行結果の永続ストア。`/tool list` / `/tool show` で参照 |
| `cfg` | `AgentConfig` | ホットリロード対象ランタイム設定 |
| `session` | `AgentSession` | セッション/メッセージ DB 操作 |

---

#### CLIView (`agent/cli_view.py`)

readline 設定・進捗表示・マルチライン入力を担うプレゼンテーション層。`Orchestrator` / `HistoryManager` / `LLMClient` へコールバックとして渡すことで UI 依存を排除。ライブラリモジュールは `print()` を直接呼ばず、すべて `CLIView` 経由で出力する。詳細は `docs/06_ref-agent-view.md` を参照。

| メソッド | 説明 |
|---|---|
| `setup_readline() -> None` | readline 設定・タブ補完・履歴ファイル読み込み |
| `write_history() -> None` | readline 履歴を `~/.agent_history` に保存 |
| `write_token(token: str) -> None` | SSE ストリーミングトークン 1 件を末尾改行なしで stdout に出力。`LLMClient` の `on_token` コールバックとして渡す |
| `write_compress_notice(n: int) -> None` | 履歴圧縮完了通知を表示。`HistoryManager` の `on_compress` コールバックとして渡す |
| `write_turn_start() -> None` | LLM ストリーミングターン開始前に空行を出力。`Orchestrator` の `on_turn_start` コールバックとして渡す |
| `write_turn_end() -> None` | LLM 最終回答後に空行を出力。`Orchestrator` の `on_turn_end` コールバックとして渡す |
| `write_llm_error(e: Exception) -> None` | LLM リクエスト失敗を通知。`Orchestrator` の `on_error` コールバックとして渡す |
| `write_progress(msg: str) -> None` | `[rag] {msg}` をインプレース表示 (`\r` 上書き)。RAG MCP ツール経由の進捗表示用 |
| `clear_progress() -> None` | 進捗表示行をクリア |
| `read_multiline(loop, first_line) -> str` | 行末 `\` の継続入力を読み込み、全行を結合して返す |

---

#### CommandRegistry (`agent/commands/registry.py`)

`AgentContext` を受け取り全スラッシュコマンドをディスパッチするクラス。`AgentREPL` への依存をゼロにした設計。10 個のミックスイン (`_SessionMixin` / `_McpMixin` / `_ConfigMixin` / `_ContextMixin` / `_DbMixin` / `_ToolingMixin` / `_NotesMixin` / `_DebugMixin` / `_IngestMixin` / `_MemoryMixin`) から構成。サービス層 (`agent/services/`) に重い処理を委譲。詳細は `docs/06_ref-agent-commands.md` を参照。

| メソッド | 説明 |
|---|---|
| `dispatch(line) -> bool` | スラッシュコマンド行を受け取り対応ハンドラを呼び出す。マッチしなければ `False` を返す |
| `_generate_session_title(first_input) -> None` | 非同期。`ctx.cfg.title_llm_temperature` / `ctx.cfg.title_llm_max_tokens` で LLM を呼び出してセッションタイトルを生成。`Orchestrator._append_user_message()` が第1ターン時に `asyncio.create_task()` で起動 |
| `_cmd_session(args) -> None` | `/session list [n]` / `/session load <id>` / `/session rename <title>` / `/session delete <id>` を処理 |
| `_cmd_db(args) -> None` | `/db stats` / `/db urls [--lang] [--limit]` / `/db clean <url>` / `/db rebuild-fts` / `/db health` / `/db checkpoint [MODE]` / `/db vacuum` / `/db purge [--max-sessions N] [--max-age-days N]` / `/db recover [<backup-path>]` を処理 |
| `_cmd_clear(args) -> None` | 会話履歴をシステムプロンプトのみにリセットし、セッション統計・ツールキャッシュをクリア |
| `_cmd_debug(args) -> None` | `ctx.conv.debug_mode` をトグル。`audit` / `verbose` / `normal` サブコマンドもサポート |
| `_cmd_ingest(args) -> None` | Crawler → ChunkSplitter → RagIngester を一括実行して RAG DB に取り込み |
| `_cmd_export(args) -> None` | 会話履歴を Markdown または JSON でエクスポート。`agent/commands/utils.py` の `render_history_md()` を使用 |

