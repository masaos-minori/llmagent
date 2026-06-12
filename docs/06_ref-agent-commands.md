# agent/commands/registry.py (CommandRegistry)

## 1. 機能概要

`AgentContext` を受け取り全スラッシュコマンドをディスパッチする `CommandRegistry` クラス。`AgentREPL` への依存をゼロにした設計。全 `_cmd_*` メソッドは `self._ctx` 経由でのみ状態にアクセス。

コマンドグループはミックスインクラスに分割:

| ミックスイン | ファイル | 担当コマンド |
|---|---|---|
| `_SessionMixin` | `agent/commands/cmd_session.py` | `/session` 系 (委譲先: `agent/services/session_title.py`, `agent/services/session_restore.py`) |
| `_McpMixin` | `agent/commands/cmd_mcp.py` | `/mcp` 系 (委譲先: `agent/services/mcp_status.py`, `agent/services/mcp_install.py`) |
| `_ConfigMixin` | `agent/commands/cmd_config.py` | `/config`, `/stats`, `/set`, `/reload` (委譲先: `agent/services/config_reload.py`) |
| `_ContextMixin` | `agent/commands/cmd_context.py` | `/context`, `/clear`, `/undo`, `/history`, `/system` (委譲先: `agent/services/context_view.py`, `agent/services/undo_service.py`) |
| `_DbMixin` | `agent/commands/cmd_db.py` | `/db` 系 (委譲先: `agent/services/db_maintenance_service.py`) |
| `_ToolingMixin` | `agent/commands/cmd_tooling.py` | `/tool`, `/plan` |
| `_NotesMixin` | `agent/commands/cmd_notes.py` | `/note` |
| `_DebugMixin` | `agent/commands/cmd_debug.py` | `/debug` |
| `_IngestMixin` | `agent/commands/cmd_ingest.py` | `/ingest`, `/export`, `/compact`, `/rag` |
| `_MemoryMixin` | `agent/commands/cmd_memory.py` | `/memory` 系 |

共有ユーティリティ: `agent/commands/utils.py` は `/export` コマンドが使用する `render_history_md(history) -> str` と、複数の mixin から共有される引数解析ヘルパー `parse_flag_int(tokens, flag)` / `parse_flag_str(tokens, flag)` を提供する。

## 2. API

```python
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext

cmds = CommandRegistry(ctx)
matched = await cmds.dispatch("/stats")
```

モジュールレベル関数 (`registry.py` および `cmd_context.py` で定義、`__all__` で再エクスポート):

| 関数 | 定義元 | 説明 |
|---|---|---|
| `budget_breakdown(messages) -> ContextBudget` | `services/context_view.py` | メッセージリストを system / history / tool_results に分類して文字数を集計。`ContextBudget(system, history, tool_results)` を返す |
| `mask_args(args, masked_fields) -> dict` | `registry.py` | `masked_fields` に含まれるキーの値を `"***"` に置換して返す |

## 3. CommandRegistry メソッド一覧

### 3.1 dispatch / プラグイン

| メソッド | 説明 |
|---|---|
| `dispatch(line) -> bool` (async) | スラッシュコマンドをルーティングし、マッチした場合は `True` を返す。`_COMMANDS` リストを順に走査し exact-match / prefix 判定（境界判定: `line == name or line.startswith(name + " ")`）を行う。未マッチ時はプラグインコマンドへフォールバック |
| `_dispatch_plugin(line) -> bool` (async) | `plugin_registry.iter_commands()` を走査し、完全一致・プレフィックス一致のプラグインコマンドにディスパッチ。マッチした場合は `True` を返す |

完全一致 sync コマンド (引数なし): `/help`, `/config`, `/stats`, `/context`, `/plan`, `/undo`, `/reload`

完全一致 async コマンド (引数なし): `/compact`

プレフィックスコマンド (trailing args を渡す): `/mcp`(async), `/session`, `/clear`, `/ingest`(async), `/rag`(async), `/export`, `/history`, `/system`, `/db`, `/note`, `/tool`, `/set`, `/memory`, `/debug`

### 3.2 /help

| メソッド | 説明 |
|---|---|
| `_cmd_help() -> None` | スラッシュコマンド一覧・ツール数・現在の LLM URL・セッション ID を表示 |

### 3.3 /session 系 (_SessionMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_session(args) -> None` | `/session list [n]` / `/session load <id>` / `/session rename <title>` / `/session delete <id>` をディスパッチ |
| `_generate_session_title(first_input) -> None` (async) | `SessionTitleService.generate()` に委譲。LLM で 8 語以内のタイトルを生成して `ctx.session.set_title()` で保存。失敗時はログに記録のみ（フォールバックなし） |
| `_session_load_safe(arg) -> None` | arg を整数 session_id としてパースし `_load_session()` を呼び出し。不正値はエラーメッセージを表示 |
| `_session_delete(arg) -> None` | arg を整数 session_id としてパースし、現在セッションへの削除を拒否した上で削除を実行 |
| `_load_session(session_id) -> None` | `restore_session(self._ctx, session_id)` に委譲（`agent/services/session_restore.py`）。`SessionRestoreResult.session_id` / `.n_messages` を使用して成功メッセージを表示 |

### 3.4 /mcp 系 (_McpMixin)

`_McpMixin` は薄いディスパッチャ。実処理は `agent/services/` のサービスクラスに委譲:
- `McpStatusService` (`agent/services/mcp_status.py`): `probe_all() -> list[McpProbeResult]` (table formatting moved to `cmd_mcp._format_mcp_table()`)
- `McpInstallService` (`agent/services/mcp_install.py`): `run(server_name, qa) -> ScaffoldResult`, `format_next_steps(result) -> str` (next-steps はサービス内で完結)
- `ScaffoldResult` (dataclass): `server_name`, `module`, `port`, `with_confd`, `created_files`, `tool_snippet`, `agent_toml_snippet`
- `InstallQA` (Protocol) / `CliInstallQA` (CLI 実装): I/O を抽象化。`CliInstallQA(port, role, with_confd)` — 非 None 値はそのまま返し、None は `input()` で問い合わせ

| メソッド | 説明 |
|---|---|
| `_cmd_mcp(args) -> None` (async) | `args` が `"install <name>"` の場合はウィザードを起動、それ以外はサーバ状態テーブルを表示 |
| `_cmd_mcp_status() -> None` (async) | `McpStatusService.probe_all()` で全サーバの状態を取得し `_format_mcp_table()` で表示。HTTP サーバは `/health` エンドポイントへの実際の疎通確認を行う (タイムアウト 5 秒) |
| `_cmd_mcp_install(server_name) -> None` (async) | `CliInstallQA` を生成し `McpInstallService.run()` でテンプレートファイルを生成、`svc.format_next_steps(result)` で次ステップチェックリストを表示 |

### 3.5 /config, /stats, /set, /reload (_ConfigMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_stats() -> None` | ターン数・ツール呼び出し数・ツールエラー数・LLM リトライ/再接続回数・HB タイムアウト・部分完了・パースエラー・キャッシュヒット・圧縮回数・セマンティックキャッシュヒット数・入出力トークン数・デバッグモード状態・ステップ別レイテンシ (mean/max/N samples) を表示 |
| `_cmd_config() -> None` | 設定ファイルパス (分割設定ファイル群) と全設定値を表示。`_print_config_values()` と `_print_rag_config()` に委譲 |
| `_print_config_values() -> None` | エンドポイント/LLM/SSE/実行/セマンティックキャッシュ/MCP/承認設定の各フィールドを表示する内部ヘルパー |
| `_print_rag_config() -> None` | rag.sqlite / session.sqlite パスと検索パラメータ (top_k_search / top_k_rerank / max_chunks_per_doc) を表示する内部ヘルパー |
| `_cmd_set(args) -> None` | `/set temperature <f>` / `/set max_tokens <n>` でランタイム LLM パラメータを変更。引数なしの場合は現在値を表示 |
| `_cmd_reload() -> None` | 分割設定ファイル群 (`config/llm.toml` / `config/tools.toml` 等) を再読み込みし `_apply_config_params()` で即時反映 |
| `_apply_config_params(new_cfg) -> None` | `ctx.cfg` フィールドを更新し各コンポーネントに同期。内部で以下のメソッドに委譲: `_apply_tool_params` / `_reload_approval_settings` / `_apply_mcp_url_reload` / `_apply_llm_prompt_params` / `_apply_sse_reload_params` / `_sync_services_to_cfg` |
| `_apply_tool_params(ctx, new_cfg) -> None` | ツールキャッシュ・LLM リトライ・リファイナー・ウォッチドッグ設定を適用する内部ヘルパー |
| `_apply_mcp_url_reload(ctx, new_cfg) -> None` | HTTP MCP サーバの URL を更新する内部ヘルパー (transport 変更には再起動が必要) |
| `_apply_llm_prompt_params(ctx, new_cfg) -> None` | URL/HTTP/LLM 生成/ツール定義/プロンプト設定を適用する内部ヘルパー |
| `_apply_sse_reload_params(ctx, new_cfg) -> None` | SSE ストリームの耐障害性設定を適用する内部ヘルパー |
| `_reload_approval_settings(ctx, new_cfg) -> None` | 承認関連リスト/辞書フィールドを更新する内部ヘルパー |
| `_sync_services_to_cfg(ctx, new_cfg) -> None` | `ConfigReloadService(ctx).apply_config_dict(new_cfg)` を呼び出す 1 行ラッパー。実処理は `agent/services/config_reload.py` の `ConfigReloadService` に委譲 |

### 3.6 /context, /clear, /undo, /history, /system (_ContextMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_context() -> None` | 会話履歴のメッセージ数・文字数・圧縮閾値残余・圧縮回数・現在のシステムプロンプト名/プレビュー・トークン推定値・トークン上限 (`context_token_limit`, 0 で無効)・メモリ層ステータス・git ブランチ/コミット情報・カテゴリ別文字数内訳 (system / history / tool_results) を表示 |
| `_cmd_clear(args) -> None` | 会話履歴をシステムプロンプトのみにリセット。ターン数・ツール呼び出し数・ツールエラー数・レイテンシ統計・セマンティックキャッシュヒット数・LLM リトライ数をゼロにリセット。`args` に `"new"` を含む場合は新規 DB セッションも開始 |
| `_cmd_undo() -> None` | 直前の user+assistant ターンをメモリ履歴と DB からロールバック。直前ユーザメッセージの前に挿入されたメモリ注入メッセージ (`_memory_injected=True`) も一括除去 |
| `_cmd_history(args) -> None` | 直近 N 件の user/assistant メッセージを先頭 120 文字プレビューで表示 (デフォルト N=5) |
| `_cmd_system(args) -> None` | `ctx.conv.system_prompt_content` / `system_prompt_name` を更新し、`history[0]` を即時書き換えてシステムプロンプトをそのターンから有効化する。`args=""` で現在のプレセット名と利用可能な一覧を表示 |

### 3.7 /db 系 (_DbMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_db(args) -> None` | `/db stats` / `/db urls [--lang ja\|en] [--limit N]` / `/db clean <url>` / `/db rebuild-fts` / `/db health` / `/db checkpoint [MODE]` / `/db vacuum` / `/db purge [--max-sessions N] [--max-age-days N]` / `/db recover [<backup-path>]` を振り分け |
| `_db_stats() -> None` | documents/chunks (rag.sqlite) と sessions/messages (session.sqlite) の件数を表示する内部ヘルパー |
| `_db_list_urls(rest) -> None` | `--lang` / `--limit` オプションをパースして `ctx.session.list_documents()` に委譲する内部ヘルパー |
| `_db_clean(rest) -> None` | URL を指定してドキュメントとそのチャンクを DB から削除する内部ヘルパー |
| `_db_rebuild_fts() -> None` | rag.sqlite の FTS5 インデックス (`chunks_fts`) を再構築する内部ヘルパー |
| `_db_health() -> None` | session.sqlite の journal_mode/integrity/page stats を表示する内部ヘルパー |
| `_db_checkpoint(mode) -> None` | WAL チェックポイントを実行する内部ヘルパー (mode: PASSIVE/FULL/RESTART/TRUNCATE) |
| `_db_vacuum() -> None` | VACUUM を実行してフリーページを回収する内部ヘルパー |
| `_db_purge(rest) -> None` | 古いセッションを削除する内部ヘルパー (`--max-sessions N` / `--max-age-days N`) |
| `_db_recover(backup_path) -> None` | 整合性チェックを実行し、破損時にバックアップから復元する内部ヘルパー |

### 3.8 /tool, /plan (_ToolingMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_tool(args) -> None` | `/tool list` / `/tool show <id>` でツール結果ストアを表示 |
| `_tool_list() -> None` | 現在セッションの保存済みツール結果一覧 (id/tool_name/size/summarized) を表示する内部ヘルパー |
| `_tool_show(arg) -> None` | id 指定でツール結果の全文・引数・サイズ・サマリを表示する内部ヘルパー |
| `_cmd_plan() -> None` | `ctx.conv.plan_mode` をトグル。ON 時は `plan_blocked_tools` に含まれるツールを自動ブロックし、ブロック対象ツール一覧を表示 |

### 3.9 /note (_NotesMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_note(args) -> None` | `/note add <text>` / `/note list` / `/note delete <id>` を処理 |
| `_note_add(text) -> None` | ノート追加の内部ヘルパー |
| `_note_list() -> None` | ノート一覧表示の内部ヘルパー |
| `_note_delete(arg) -> None` | ノート削除の内部ヘルパー |

### 3.10 /debug (_DebugMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_debug(args) -> None` | 引数なしで `ctx.conv.debug_mode` をトグル。`args="audit"` で audit.log 末尾 20 行を表示、`args="verbose"` / `"normal"` でログレベルを切り替え |

### 3.11 /ingest, /export, /compact, /rag (_IngestMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_ingest(args) -> None` (async) | URL またはローカルファイルパスをクロール→チャンク分割→DB 投入まで一括実行。引数: `<url\|path> [ja\|en] [--snippets-only]` |
| `_run_split_and_ingest(loop, snippets_only=False) -> None` (async) | ChunkSplitter と RagIngester をスレッドエグゼキュータで順次実行。`snippets_only=True` のとき `md_index_enable=True` を強制してヘディングベースのスニペット分割を使用 |
| `_cmd_export(args) -> None` | 会話履歴を Markdown または JSON でエクスポート。引数: `[md\|json] [filename]`。filename 省略時は標準出力 |
| `_cmd_compact() -> None` (async) | 閾値に関わらず会話履歴を即時圧縮。`hist_mgr.force_compress(history)` を使用 — `_char_limit` への直書きを廃止 |
| `_cmd_rag(args) -> None` (async) | インプロセス RAG パイプラインで検索を実行。引数: `search <query> [--debug]`。`--debug` 指定時はステージ別 latency を表示。`rag.toml` の `use_search=false` 時は無効メッセージを返す |

### 3.12 /memory 系 (_MemoryMixin)

| メソッド | 説明 |
|---|---|
| `_cmd_memory(args) -> None` | `/memory help\|list\|search\|show\|pin\|unpin\|delete\|prune` をディスパッチ。引数なしまたは `help` でヘルプテキストを表示。`use_memory_layer=false` 時は `help` のみ通過し他は無効メッセージを返す |
| `_memory_list(mem, args) -> None` | `[semantic\|episodic] [limit]` を受け取り、MemoryStore からエントリを取得してテーブル表示する内部ヘルパー。フィルタなし時は両タイプを pinned 優先・importance 降順で表示 |
| `_memory_search(mem, args) -> None` | FTS5 検索を実行して結果 (スコア/タイプ/id/サマリ) を表示する内部ヘルパー |
| `_memory_show(mem, args) -> None` | `<id>` で 1 件のエントリの全フィールドを表示する内部ヘルパー |
| `_memory_pin(mem, args, pin) -> None` | `<id>` で 1 件をピン留め/解除する内部ヘルパー |
| `_memory_delete(mem, args) -> None` | `<id>` で 1 件を削除する内部ヘルパー |
| `_memory_prune(mem, ctx, args) -> None` | `[days]` を受け取り、指定日数より古いエントリを削除する内部ヘルパー。days 省略時は `ctx.cfg.memory_retention_days` を使用 |

## 4. 内部型 (foundation files)

コマンド層共通の型・例外・プロトコルは以下のファイルで定義:

| ファイル | 定義内容 |
|---|---|
| `agent/commands/enums.py` | `CommandKind`, `MemoryAction`, `DbAction`, `McpAction`, `SessionAction` (StrEnum) |
| `agent/commands/exceptions.py` | `CommandParseError`, `CommandValidationError`, `CommandDispatchError`, `CommandRenderingError`, `UnknownSubcommandError`, `UnknownPresetError`, `UnknownTierError` |
| `agent/commands/models.py` | `StatsViewModel`, `ToolResultView`, `McpInstallRequest`, `McpInstallRenderModel` (frozen dataclass) |
| `agent/commands/output_port.py` | `OutputPort` (Protocol), `CliOutputPort` (stdout 実装) |
| `agent/commands/formatter.py` | `print_success`, `print_error`, `print_no_data`, `print_validation_error`, `print_table`, `print_kv_list` — `CliOutputPort` への薄いシム |
| `agent/commands/mixin_base.py` | `MixinBase` — `_ctx: AgentContext` と `_out: OutputPort` を提供する基底クラス |

`OutputPort` の設計方針: `CommandRegistry.__init__` が `out: OutputPort | None = None` を受け取り、`None` の場合は `CliOutputPort()` を使用。テストでは代替 `OutputPort` 実装を注入可能。

## 5. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `self._cmds = CommandRegistry(ctx)` を `run()` で生成し、`_repl_loop()` が `await self._cmds.dispatch(line)` を呼ぶ |
