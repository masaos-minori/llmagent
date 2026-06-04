# agent/repl.py / agent/orchestrator.py

## 1. 機能概要

`AgentREPL` (`agent/repl.py`) は全コンポーネントを `AgentContext` へ依存性注入し、REPL ループを駆動する薄いコーディネータ。ターンレベルのロジック (LLM ループ・ツールディスパッチ) は `Orchestrator` (`agent/orchestrator.py`) に委譲。`agent.py` が `AgentREPL().run()` で起動。

実装は 3 つのサテライトモジュールに分割:
- `agent/repl_health.py` — MCP 死活監視・ウォッチドッグループ (→ §5)
- `agent/repl_tool_exec.py` — ツール呼び出し承認・実行 (→ §4)
- `agent/repl_debug.py` — コンテキストダンプ・デバッグユーティリティ (純粋関数)

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
| `_prompt` | `str` | 現在のセッション ID を含む動的 REPL プロンプト文字列 (`"agent[:#<id>]> "` または `"agent> "`) |
| `_n_tools` | `int` | `ctx.cfg.tool_definitions` から算出したツール定義数 |

### メソッド

| メソッド | 説明 |
|---|---|
| `run() -> None` | readline 初期化 → `_init_components()` → stdio サーバ起動 → サービスヘルスチェック → ツール定義検証 → `_print_startup_banner()` → セッション開始 → メモリ SessionStart → ウォッチドッグ起動 → `_repl_loop()` → メモリ Stop → リソースクローズ |
| `_init_components() -> None` | `build_agent_context(ctx, view)` でサービスを注入した後、`_init_command_registry` → `_init_orchestrator` を呼び出す |
| `_init_command_registry(ctx) -> None` | `CommandRegistry(ctx)` を `self._cmds` に代入 |
| `_init_orchestrator(ctx) -> None` | `build_tracer()` で OTel トレーサを生成して `Orchestrator` を `self._orchestrator` に代入 |
| `_print_startup_banner() -> None` | DB チャンク数・ツール数を表示 (`"DB: N chunks | Tools: N"`) |
| `_get_chunk_count() -> str` | DB の `chunks` 行数をカンマ区切り書式で返す。エラー時は `"?"` を返す |
| `_start_subprocess_servers() -> None` | `startup_mode == 'persistent'` の stdio と `startup_mode == 'subprocess'` の HTTP サーバを起動。`ondemand` サーバは `ServerLifecycleManager.ensure_ready()` による初回使用時起動に委ねる |
| `_repl_loop() -> None` | ユーザ入力待機 → `\` 終端で複数行継続入力 → スラッシュコマンドまたは `self._orchestrator.handle_turn()` に委譲 |
| `_close_resources() -> None` | readline 履歴保存 → `lifecycle.shutdown_all()` で stdio サーバ停止 → `AsyncClient` クローズ |

**`_init_components()` 呼び出し順序:**

```
build_agent_context(ctx, view)   ← factory.py が audit_logger/http/llm/tools/lifecycle/hist_mgr/memory を注入
  → _init_command_registry
  → _init_orchestrator
```

## 3. Orchestrator API

```python
from agent.orchestrator import Orchestrator

orch = Orchestrator(ctx, cmds, on_turn_start=..., on_turn_end=..., on_error=..., tracer=...)
await orch.handle_turn(line)
```

| メソッド | 説明 |
|---|---|
| `handle_turn(line) -> None` | メモリ注入 → `_append_user_message` → 履歴圧縮 → `_run_turn()` → 結果を DB 保存。`LLMTransportError` を捕捉し partial/pre-stream の 2 ブランチで処理 |
| `_run_turn(llm_url) -> str` | SSE ストリーミングで LLM を呼び出し、tool_calls があれば `execute_all_tool_calls()` 後に再送信。最大 `max_tool_turns` 回ループ。`_check_all_tool_guards()` と `_check_consecutive_error_limit()` を適用。最終回答テキストを返す |
| `_warn_budget() -> None` | 会話履歴が `context_char_limit` / `context_token_limit` の `budget_warn_ratio` を超えたときコンテキスト使用量の警告ログを出力 |

**`_run_turn()` 安全ガード**

| ガード | 設定フィールド | 動作 |
|---|---|---|
| ツール呼び出し dedup | `tool_dedup_max_repeats` | 同一 (name, args) が指定回数を超えたら `_DEDUP_HINT` を注入してスキップ |
| 循環プランニング検出 | `tool_cycle_detect_window` | 同一 round fingerprint が `window` 回繰り返されたら `_CYCLE_HINT` を注入してループ脱出 |
| 連続エラーガード | `tool_error_max_consecutive` | 全ツールがエラーになったターンが指定回数連続したらループ脱出 |
| エラー retry 抑制 | `tool_error_retry_max` | 同一 (name, args) がこのターンですでにエラーになっていた場合、retry 制限内で再試行 |

**`handle_turn()` LLM エラー処理**

| 条件 | 対処 |
|---|---|
| `LLMTransportError` (partial_text あり) | `[INCOMPLETE: {kind}]` 付きで assistant メッセージを保存 |
| `LLMTransportError` (partial_text なし, turn==0) | history から user メッセージを pop して整合性を保つ |
| `LLMTransportError` (turn > 0) | synthetic tool error を history に追加して `_run_turn()` から return |

## 4. agent/repl_tool_exec.py API

### 公開関数

| 関数 | 説明 |
|---|---|
| `check_approval(ctx, tool_name, args) -> bool` | プレフライトチェック → リスク分類 → dry_run 実行 → ユーザ確認プロンプト → 承認/拒否を返す |
| `execute_one_tool_call(ctx, tc, turn) -> tuple[str, str, dict, str, bool, str]` | 1 件の tool_call を実行し `(id, name, args, full_text, is_error, llm_text)` を返す。長い結果は LLM 要約 (`llm_text`) |
| `execute_all_tool_calls(ctx, tool_calls, turn, out_failed_keys=None) -> None` | 全 tool_call を `asyncio.gather()` (副作用なし) または直列 (副作用あり / `serial_tool_calls=True`) で実行し、承認・dedup・per-turn 上限チェックを経て履歴に追記。エラーキーを `out_failed_keys` (set) に収集する |

### 内部ヘルパー関数

| 関数 | 説明 |
|---|---|
| `_classify_risk(cfg, tool_name, args) -> str` | ツールのリスクレベルを `"none"` / `"medium"` / `"high"` で返す (→ 下記分類順序) |
| `_check_allowed_root(cfg, tool_name, args) -> bool` | パス引数が `allowed_root` 内に収まるか `Path.resolve()` で検証。`False` = 即時拒否 |
| `_check_allowed_repo(cfg, tool_name, args) -> bool` | GitHub 書き込みツールのリポジトリが `approval_github_allowed_repos` に含まれるか検証。`False` = 即時拒否 (Fail-Closed: 空リスト = 全拒否) |
| `_run_approval_checks(ctx, tool_calls) -> tuple[list[dict], list[str]]` | plan_mode ブロックと `check_approval()` を各 tool_call に順次適用し `(approved_calls, denied_ids)` を返す |
| `_collect_tool_result_msgs(ctx, results, turn, out_failed_keys) -> list[...]` | ツール結果をログ出力・表示・DB 保存・history 追記し、`session.save_many()` 用メッセージリストを返す |
| `_classify_operation_type(tool_name) -> str` | `"write"` / `"delete"` / `"execute"` / `"api_write"` / `"read"` の操作種別を返す |
| `_escalate_for_path(cfg, base, args) -> str \| None` | パス引数が `approval_protected_paths` 配下のとき `"high"` を返す |
| `_escalate_for_github_branch(cfg, tool_name, base, args) -> str \| None` | GitHub ツールのブランチが `approval_high_risk_branches` に含まれるとき `"high"` を返す |
| `_build_preview(tool_name, args) -> str` | 承認プロンプト表示用の人間可読プレビュー文字列を生成する |
| `_audit_approval(ctx, tool_name, risk, args, decision) -> None` | `tool_approval` イベントを audit ログに JSON-lines で書き込む |
| `_audit_tool_exec(ctx, tool_name, args, is_error, mcp_request_id) -> None` | `tool_exec` イベント (mcp_request_id 付き) を audit ログに書き込む |
| `_is_summarized(cfg, text, llm_text, is_error) -> bool` | `llm_text` が要約済み (切り捨てではない) かを判定して返す |

### 4-tier ツール安全性分類

ツールは `agent.toml` の `tool_safety_tiers` で 4 段階に分類する。`approval_risk_rules` が設定されているツールはそちらが優先される。

| tier | `_TIER_TO_RISK` | 説明 |
|---|---|---|
| `READ_ONLY` | `"none"` | 副作用なし読み取り専用 (例: `read_text_file`, `list_directory`, `github_get_file_contents`) |
| `WRITE_SAFE` | `"none"` | 低リスク書き込み (例: `write_file`, `create_directory`) |
| `WRITE_DANGEROUS` | `"medium"` | 破壊的書き込み・削除 (例: `delete_file`, `github_push_files`) |
| `ADMIN` | `"high"` | システム管理・シェル実行 (例: `shell_run`) |

**フォールバック (Fail-Safe):** `approval_risk_rules` にも `tool_safety_tiers` にも未登録のツールは `WRITE_DANGEROUS` とみなし、リスク `"medium"` を返す。

### `_classify_risk()` 分類順序

```
1. cfg.approval_risk_rules[tool_name] — 明示設定が最優先
2. cfg.tool_safety_tiers[tool_name] → _TIER_TO_RISK — ティアフォールバック
   (未登録は WRITE_DANGEROUS として "medium")
3. base == "none" → 即返却
4. delete_directory + recursive=True → "high" に昇格
5. shell_run: cfg.approval_shell_safe_prefixes に一致するコマンド → "none" に降格、不一致 → "high"
6. _escalate_for_path(): パス引数が protected_paths 配下 → "high" に昇格
7. _escalate_for_github_branch(): ブランチが high_risk_branches に含まれる → "high" に昇格
```

### check_approval() 処理フロー

```
check_approval(ctx, tool_name, args)
  ├─ allowed_tools チェック  — ctx.cfg.allowed_tools が非空かつ tool_name 不在なら即時 denied_allowed_tools
  ├─ _check_allowed_root()  — allowed_root 外なら即時 denied_root_jail (audit ログ + False 返却)
  ├─ _check_allowed_repo()  — allowlist 外 GitHub 書き込みなら即時 denied_repo_allowlist (audit ログ + False 返却)
  ├─ _classify_risk()       — approval_risk_rules → tier fallback → 各種エスカレーション
  ├─ risk == "none"         — 自動承認 (audit: "auto")
  ├─ approval_dry_run_tools — dry_run=True でプレビュー実行、結果を表示
  ├─ risk == "medium"       — [y/N] プロンプト (audit: "approved" / "denied")
  └─ risk == "high"         — [yes/no] プロンプト (audit: "approved" / "denied")
```

### plan_mode ブロック

`ctx.conv.plan_mode == True` かつツールが `cfg.plan_blocked_tools` に含まれる場合、`_run_approval_checks()` 内で `check_approval()` 呼び出し前にブロックされ `denied_ids` に追加される。

## 5. agent/repl_health.py API

AgentREPL からはデリゲートメソッド (`_check_service_health`, `_check_tool_definitions`, `_watchdog_loop`) 経由で呼ばれる。

| 関数 | 説明 |
|---|---|
| `probe_mcp_health(http, base_url) -> bool` | `{base_url}/health` に GET して HTTP 200 なら `True` を返す。エラー時は `False` |
| `check_service_health(ctx) -> None` | LLM / Embed サービスの `/health` をプローブ。失敗は警告のみ (REPL は継続) |
| `check_tool_definitions(ctx) -> None` | `agent.toml` の `tool_definitions` と各 MCP サーバの実ツールリストを比較して警告。`tool_definitions_strict=True` のとき不一致で `RuntimeError` を送出。全サーバ未到達時はスキップ |
| `watchdog_loop(ctx) -> None` | `mcp_watchdog_interval` 秒ごとに HTTP サーバは OpenRC 経由で、stdio サーバはプロセス再起動で復旧。キャンセルされるまで無限ループ。`mcp_watchdog_max_restarts` でリトライ上限を制御 |

**stdio 向け追加チェック:** `McpServerConfig.healthcheck_mode == "ping_tool"` のとき、プロセス生存確認に加えて `__list_tools__` RPC で応答確認を行う。`ondemand` サーバはウォッチドッグ対象外。

## 6. 処理フロー

```
AgentREPL.run()
  └─ _view.setup_readline()        — readline 設定・補完・履歴ファイル読み込み
  └─ _init_components()            — build_agent_context() → CommandRegistry → Orchestrator 注入
  └─ _start_subprocess_servers()   — persistent stdio / HTTP subprocess サーバ起動
  └─ _check_service_health()       — LLM/Embed サービスヘルスプローブ (警告のみ)
  └─ _check_tool_definitions()     — agent.toml ↔ ライブ MCP ツールリスト検証 (警告/例外)
  └─ _print_startup_banner()       — DB チャンク数・ツール数を表示
  └─ ctx.session.start()           — sessions テーブルに INSERT
  └─ memory.on_session_start()     — (use_memory_layer=True のとき) セマンティック記憶をシステムプロンプトに注入
  └─ watchdog_task = create_task(_watchdog_loop())  ← mcp_watchdog_interval > 0 のとき
  └─ _repl_loop()
       └─ input()                  — ユーザ入力待機 (EOF/KeyboardInterrupt で終了)
       └─ 末尾 \ → _view.read_multiline()  — 複数行入力の継続
       └─ Orchestrator.handle_turn(line)
            └─ memory.on_user_prompt()  ← use_memory_layer=True のとき関連メモリを注入
            └─ _append_user_message()  — user メッセージを history に追記・セッション保存
            └─ asyncio.create_task(_cmds._generate_session_title())  ← 第1ターンのみ
            └─ hist_mgr.compress() — 履歴圧縮 (context_char_limit / context_token_limit)
            └─ _run_turn()         — LLM SSE ストリーム + ツールループ (max_tool_turns 回)
                 └─ execute_all_tool_calls()  — 承認・並列/直列実行・結果追記
  └─ memory.on_session_stop()      — (use_memory_layer=True のとき) セッション終了時に記憶を抽出・永続化
  └─ watchdog_task.cancel()
  └─ _close_resources()            — readline 履歴保存・lifecycle.shutdown_all()・AsyncClient クローズ
```

## 7. プラグインアーキテクチャ (shared/plugin_registry.py)

プラグインファイルは `plugins/*.py` に配置する。`AgentREPL._init_plugin_registry()` が起動時に `plugin_registry.load_plugins(plugin_dir)` を呼び出し、各ファイルをインポートする。`plugin_dir` は `scripts/` の 2 親階層上の `plugins/` ディレクトリ。`@register_*` デコレータはインポート時に実行され、グローバルレジストリに登録される。

### デコレータ一覧

| デコレータ | シグネチャ | 説明 |
|---|---|---|
| `@register_command(name, *, prefix=False)` | `handler(ctx, args: str) -> None` (sync or async) | スラッシュコマンドを登録。`name` は先頭 `/` を含む文字列。`prefix=True` で末尾引数を受け付ける |
| `@register_tool(name)` | `async handler(args: dict) -> tuple[str, bool]` | ローカル Python 関数をツールハンドラとして登録。MCP ルーティングをバイパスして `ToolExecutor` から直接呼ばれる |

### API (アクセサ関数)

| 関数 | 説明 |
|---|---|
| `get_command(name) -> tuple[Callable, bool] \| None` | 登録済みコマンドの `(handler, is_prefix)` を返す。未登録は `None` |
| `iter_commands() -> dict[str, tuple[Callable, bool]]` | 全登録コマンドのスナップショット (`dict` のコピー) を返す |
| `get_tool(name) -> Callable \| None` | 登録済みローカルツールハンドラを返す。未登録は `None` |
| `load_plugins(plugin_dir) -> int` | `plugin_dir` の `*.py` をアルファベット順にインポートしてロード数を返す。エラーはログ記録してスキップ (fail-open)。ディレクトリ不在時は `0` を返す |
| `_reset_for_testing() -> None` | 全レジストリをクリア。テスト用途のみ |

### ディスパッチ順序

`CommandRegistry.dispatch()` はビルトインコマンドのマッチング後に `_dispatch_plugin()` でプラグインコマンドを照合する。プラグインはビルトインより低優先度。`@register_tool` で登録した関数は `ToolExecutor.execute()` 内でキャッシュ・MCPルーティングよりも先に照合される。

### ツールハンドラ戻り値規約

`@register_tool` ハンドラは必ず `tuple[str, bool]` を返す:

```python
# (result_text, is_error)
return "result string", False   # 成功
return "error message", True    # エラー
```

### プラグイン例

```python
# plugins/my_plugin.py
from shared.plugin_registry import register_command, register_tool

@register_command("/ping")
async def cmd_ping(ctx, args: str) -> None:
    print("pong")

@register_tool("echo")
async def tool_echo(args: dict) -> tuple[str, bool]:
    return str(args.get("text", "")), False
```

## 8. 使用スクリプト

`agent.py` が `asyncio.run(AgentREPL().run())` で呼び出す唯一のエントリポイント。
