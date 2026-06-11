# agent/repl.py / agent/orchestrator.py

## 1. 機能概要

`AgentREPL` (`agent/repl.py`) は全コンポーネントを `AgentContext` へ依存性注入し、REPL ループを駆動する薄いコーディネータ。ターンレベルのロジック (LLM ループ・ツールディスパッチ) は `Orchestrator` (`agent/orchestrator.py`) に委譲。`agent.py` が `AgentREPL().run()` で起動。

実装は 3 つのサテライトモジュールに分割:
- `agent/repl_health.py` — MCP 死活監視・ウォッチドックグループ (→ §5)
- `agent/repl_debug.py` — コンテキストダンプ・デバッグユーティリティ (純粋関数)

> **注意:** `agent/repl_tool_exec.py` は削除済み。ツール承認・実行のロジックは `shared/tool_executor.py` (`ToolExecutor`) に統合されている。

## 2. AgentREPL API

```python
from agent.repl import AgentREPL

await AgentREPL().run()
```

### クラス変数

| 変数 | 型 | 説明 |
|---|---|---|
| `SLASH_COMMANDS` | `list[str]` | readline 補完対象のスラッシュコマンド名一覧。`CLIView` に渡されて tab 補完に使用される |

### プロパティ

| プロパティ | 戻り値 | 説明 |
|---|---|---|
| `_prompt` | `str` | 固定プロンプト文字列 `"> "` |
| `_n_tools` | `int` | `ctx.cfg.tool.tool_definitions` から算出したツール定義数 |

### メソッド

| メソッド | 説明 |
|---|---|
| `run() -> None` | `_initialize_session()` → `_start_mcp_servers()` → `_check_services()` → `_setup_initial_prompt()` → `_run_repl_loop()` (finally ブロックで memory.on_session_stop, watchdog cancel, _close_resources) |
| `_initialize_session() -> None` | `_view.setup_readline()` → `_init_components()` → `ctx.conv.llm_url` を設定 |
| `_start_mcp_servers() -> None` | `_start_subprocess_servers()` — persistent stdio と HTTP subprocess サーバを起動 |
| `_check_services() -> None` | `_check_service_health()` (LLM/Embed ヘルスプローブ) → `_check_tool_definitions()` (agent.toml ↔ ライブ MCP ツールリスト検証) |
| `_setup_initial_prompt() -> None` | システムプロンプトの初期化 → メモ注入 (`memory.on_session_start`) → `ctx.conv.history` を設定 |
| `_run_repl_loop() -> None` | ユーザ入力待機 → `\` 終端で複数行継続入力 → スラッシュコマンドまたは `self._orchestrator.handle_turn()` に委譲 |
| `_close_resources() -> None` | readline 履歴保存 → `lifecycle.shutdown_all()` → `AsyncClient` クローズ |
| `_init_components() -> None` | `build_agent_context(ctx, view)` でサービスを注入した後、`_init_command_registry` → `_init_orchestrator` を呼び出す |
| `_init_command_registry(ctx) -> None` | `CommandRegistry(ctx)` を `self._cmds` に代入 |
| `_init_orchestrator(ctx) -> None` | `init_tracer()` で OTel トレーサを生成して `Orchestrator` を `self._orchestrator` に代入 |
| `_print_startup_banner() -> None` | DB チャンク数・ツール数を表示 (`CLIView.write_startup_banner()` 経由) |
| `_get_chunk_count() -> str` | DB の `chunks` 行数をカンマ区切り書式で返す。エラー時は `"?"` を返す |
| `_start_subprocess_servers() -> None` | `startup_mode == 'persistent'` の stdio と `startup_mode == 'subprocess'` の HTTP サーバを起動。`ondemand` サーバは `LifecycleProtocol.ensure_ready()` による初回使用時起動に委ねる |
| `_check_service_health() -> None` | `check_service_health(ctx)` を呼び出し、警告メッセージを `_view.write_warning()` で表示 |
| `_check_tool_definitions() -> None` | `check_tool_definitions_runtime(ctx)` を呼び出し、警告メッセージを `_view.write_warning()` で表示 |
| `_watchdog_loop() -> None` | `watchdog_loop(ctx)` を非同期呼び出し |

**`_initialize_session()` 呼び出し順序:**

```
_view.setup_readline()              ← readline 設定・補完・履歴ファイル読み込み
build_agent_context(ctx, view)      ← factory.py が audit_logger/http/llm/tools/lifecycle/hist_mgr/memory を注入
  → _init_command_registry
  → _init_orchestrator
ctx.conv.llm_url = ctx.cfg.llm.llm_url
```

## 3. Orchestrator API

```python
from agent.orchestrator import Orchestrator

orch = Orchestrator(ctx, cmds, on_turn_start=..., on_turn_end=..., on_error=..., tracer=...)
await orch.handle_turn(line)
```

| メソッド | 説明 |
|---|---|
| `handle_turn(line) -> None` | `_handle_turn_start()` → `_process_turn()` → `_handle_turn_end()`。メモリ注入・履歴圧縮・LLM 呼び出し・エラー処理を順次実行 |
| `_handle_turn_start(line) -> None` | turn ID 生成、audit ログ (`turn_start` event) を出力 |
| `_handle_memory_injection(line) -> None` | `ctx.services.memory.on_user_prompt(query, session_id)` を非同期呼び出し。メモリスニペットがある場合 system メッセージとして history に追記 (`_memory_injected=True`) |
| `_handle_history_compression() -> None` | `hist_mgr.compress()` で履歴圧縮 (context_char_limit / context_token_limit) |
| `_handle_llm_turn(llm_url) -> TurnResult` | `LLMTurnRunner.run(llm_url)` を呼び出し、LLM 応答を保存。`LLMTransportError` を捕捉し partial/completion の2ブランチで処理 |
| `_process_turn(line, ctx, turn_started_at) -> tuple[str, str | None]` | メモリ注入 → ユーザメッセージ追記 → 履歴圧縮 → `_handle_llm_turn()`。allowed_tools の一時的オーバーライドと restore を行う |
| `_handle_turn_end(line, answer, turn_started_at, error_kind) -> None` | audit ログ (`turn_end` event: elapsed_ms, token counts, reconnect count, etc.) を出力 |

### `_handle_llm_transport_error()` 処理

| 条件 | 対処 |
|---|---|
| `LLMTransportError` (partial_text あり) | `[INCOMPLETE: {kind}]` 付きで assistant メッセージを保存、`tool_result_store.store()` に partial 結果を記録 |
| `LLMTransportError` (partial_text なし, history[-1] が user) | history から user メッセージを pop して整合性を保つ |

**内部委譲先:**

| コンポーネント | 責務 | ファイル |
|---|---|---|
| `LLMTurnRunner` | LLM SSE ストリーミング + tool_call ループ | `agent/llm_turn_runner.py` |
| `ToolLoopGuard` | dedup/cycle/retry/error ガード | `agent/tool_loop_guard.py` |

> **注意:** `_run_turn()`, `_warn_budget()` はこのファイルには存在しない。LLM 呼び出しは `LLMTurnRunner.run()` に委譲。

## 4. ツール実行 (shared/tool_executor.py)

`repl_tool_exec.py` は削除され、ツール実行のロジックは `shared/tool_executor.py` に統合されている。

### ToolExecutor クラス

| メソッド | 説明 |
|---|---|
| `execute(tool_name, args) -> tuple[str, bool, str]` | プラグインツール優先 (`plugin_registry.get_tool()`) → キャッシュヒット → `_raw_execute()` (MCP ルーティング) |
| `_raw_execute(tool_name, args) -> tuple[str, bool, str]` | サーバキー解決 → ヘルスチェック → `LifecycleProtocol.ensure_ready()` → トランスポート呼出 |
| `_execute_with_cache(tool_name, args) -> tuple[str, bool, str]` | TTL キャッシュ (LRU, max_size) のヒット/ミスを処理。成功時のみキャッシュに保存 |

### トランスポート

| クラス | 説明 |
|---|---|
| `HttpTransport` | POST `/v1/call_tool` over httpx。認証トークン・セッション ID ヘッダー付与 |
| `StdioTransport` | JSON-RPC over subprocess stdin/stdout。per-instance Lock で同時実行を直列化 |

### 補助関数

| 関数 | 説明 |
|---|---|
| `is_side_effect(tool_name) -> bool` | 副作用ありツール (`write`/`delete`/`shell_run`) の判定 |
| `tool_call_key(name, args) -> str` | (name, args) の安定した MD5 ハッシュキー (dedup用) |
| `format_transport_error(...) -> dict[str, str]` | トランスポートエラーの要約・詳細文字列生成 |

### プラグインツール戻り値規約

`@register_tool` ハンドラは必ず `tuple[str, bool]` を返す:

```python
# (result_text, is_error)
return "result string", False   # 成功
return "error message", True    # エラー
```

## 5. agent/repl_health.py API

AgentREPL からはデリゲートメソッド (`_check_service_health`, `_check_tool_definitions`, `_watchdog_loop`) 経由で呼ばれる。

| 関数 | 説明 |
|---|---|
| `probe_mcp_health(http, base_url) -> bool` | `{base_url}/health` に GET して HTTP 200 なら `True` を返す。エラー時は `False` |
| `check_service_health(ctx) -> list[str]` | LLM / Embed サービスの `/health` をプローブ。失敗は警告のみ (REPL は継続)。warning 文字列のリストを返す |
| `check_tool_definitions_runtime(ctx) -> list[str]` | `tool_definitions` と各 MCP サーバの実ツールリストを比較して警告。`strict=True` のとき不一致で `RuntimeError` を送出 |
| `watchdog_loop(ctx) -> None` | `mcp_watchdog_interval` 秒ごとに HTTP サーバは lifecycle manager 経由で、stdio サーバはプロセス再起動で復旧。キャンセルされるまで無限ループ。`mcp_watchdog_max_restarts` でリトライ上限を制御 |

**stdio 向け追加チェック:** `McpServerConfig.healthcheck_mode == "ping_tool"` のとき、プロセス生存確認に加えて `__list_tools__` RPC で応答確認を行う。`ondemand` サーバはウォッチドッグ対象外。

## 6. 処理フロー

```
AgentREPL.run()
  └─ _initialize_session()
       └─ _view.setup_readline()        — readline 設定・補完・履歴ファイル読み込み
       └─ _init_components()            — build_agent_context() → CommandRegistry → Orchestrator 注入
       └─ ctx.conv.llm_url = cfg.llm.llm_url
  └─ _start_mcp_servers()              — persistent stdio / HTTP subprocess サーバ起動
  └─ _check_services()
       └─ _check_service_health()       — LLM/Embed サービスヘルスプローブ (警告のみ)
       └─ _check_tool_definitions()     — agent.toml ↔ ライブ MCP ツールリスト検証 (警告/例外)
  └─ _setup_initial_prompt()
       └─ システムプロンプトの初期化       — cfg.tool.system_prompts / auto_inject_notes
       └─ memory.on_session_start()      — セマンティック記憶をシステムプロンプトに注入
       └─ ctx.conv.history = [{"role": "system", "content": ...}]
  └─ _run_repl_loop()
       └─ input(self._prompt)            — ユーザ入力待機 (EOF/KeyboardInterrupt で終了)
       └─ 末尾 \ → _view.read_multiline() — 複数行入力の継続
       └─ line.startswith("/")           — スラッシュコマンド: self._cmds.dispatch(line)
       └─ else → self._orchestrator.handle_turn(line)
            └─ _handle_turn_start()      — turn ID 生成, audit log (turn_start)
            └─ _process_turn()
                 ├─ memory.on_user_prompt() — メモリスニペットを system メッセージとして history に追記
                 ├─ _append_user_message()  — user メッセージを history に追記・セッション保存
                 │     └─ (first turn only) asyncio.create_task(_cmds._generate_session_title())
                 ├─ _handle_history_compression() — hist_mgr.compress()
                 └─ _handle_llm_turn()    — LLMTurnRunner.run(llm_url) → LLM SSE ストリーム + tool ループ
                      └─ LLMTurnRunner 内部: ToolLoopGuard (dedup/cycle/retry/error ガード)
            └─ _handle_turn_end()        — audit log (turn_end: elapsed_ms, tokens, etc.)
  └─ finally ブロック (_run_repl_loop)
       └─ memory.on_session_stop()       — セッション終了時に記憶を抽出・永続化
       └─ watchdog_task.cancel()
       └─ _close_resources()             — readline 履歴保存・lifecycle.shutdown_all()・AsyncClient クローズ
```

## 7. プラグインアーキテクチャ (shared/plugin_registry.py)

プラグインファイルは `plugins/*.py` に配置する。`AgentREPL._init_plugin_registry()` が起動時に `plugin_registry.load_plugins(plugin_dir)` を呼び出し、各ファイルをインポートする。`plugin_dir` は `scripts/` の 2 親階層上の `plugins/` ディレクトリ。`@register_*` デコレータはインポート時に実行され、グローバルレジストリに登録される。

### デコレータ一覧

| デコレータ | シグネチャ | 説明 |
|---|---|---|
| `@register_command(name, *, prefix=False)` | `handler(ctx, args: str) -> None` (sync or async) | スラッシュコマンドを登録。`name` は先頭 `/` を含む文字列。`prefix=True` で末尾引数を受け付ける |
| `@register_tool(name)` | `async handler(args: dict) -> tuple[str, bool]` | ローカル Python 関数をツールハンドラとして登録。MCP ルーティングをバイパスして `ToolExecutor` から直接呼ばれる |
| `@register_pipeline_stage(when="post")` | `handler(hits, query) -> list[dict]` | RAG パイプラインのクロスエンコーダ rerank 後にフック。戻り値は (変更ありの) hits リスト |

### API (アクセサ関数)

| 関数 | 説明 |
|---|---|
| `get_command(name) -> tuple[Callable, bool] | None` | 登録済みコマンドの `(handler, is_prefix)` を返す。未登録は `None` |
| `iter_commands() -> dict[str, tuple[Callable, bool]]` | 全登録コマンドのスナップショット (`dict` のコピー) を返す |
| `get_tool(name) -> Callable | None` | 登録済みローカルツールハンドラを返す。未登録は `None` |
| `get_pipeline_post_stages() -> list[Callable]` | 全登録 post-rerank パイプラインステージフックのスナップショットを返す |
| `load_plugins(plugin_dir) -> int` | `plugin_dir` の `*.py` をアルファベット順にインポートしてロード数を返す。エラーはログ記録してスキップ (fail-open)。ディレクトリ不在時は `0` を返す |
| `_reset_for_testing() -> None` | 全レジストリをクリア。テスト用途のみ |

### ディスパッチ順序

`CommandRegistry.dispatch()` はビルトインコマンドのマッチング後に `_dispatch_plugin()` でプラグインコマンドを照合する。プラグインはビルトインより低優先度。`@register_tool` で登録した関数は `ToolExecutor.execute()` 内でキャッシュ・MCPルーティングよりも先に照合される。

### プラグイン例

```python
# plugins/my_plugin.py
from shared.plugin_registry import register_command, register_tool, register_pipeline_stage

@register_command("/ping")
async def cmd_ping(ctx, args: str) -> None:
    print("pong")

@register_tool("echo")
async def tool_echo(args: dict) -> tuple[str, bool]:
    return str(args.get("text", "")), False
```

## 8. 使用スクリプト

`agent.py` が `asyncio.run(AgentREPL().run())` で呼び出す唯一のエントリポイント。
