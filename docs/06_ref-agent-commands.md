# agent/commands/registry.py (CommandRegistry)

## 1. 機能概要

`AgentContext` を受け取り全スラッシュコマンドをディスパッチする `CommandRegistry` クラス。旧 `_REPLCommandsMixin` ミックスイン方式を廃止し、`AgentREPL` への依存をゼロにした設計。全 `_cmd_*` メソッドは `self._ctx` 経由でのみ状態にアクセス。

コマンドグループはミックスインクラスに分割:

| ミックスイン | ファイル | 担当コマンド |
|---|---|---|
| `_SessionMixin` | `agent/commands/cmd_session.py` | `/session` 系 |
| `_McpMixin` | `agent/commands/cmd_mcp.py` | `/mcp` 系 |
| `_ConfigMixin` | `agent/commands/cmd_config.py` | `/config`, `/stats`, `/set`, `/reload` |
| `_ContextMixin` | `agent/commands/cmd_context.py` | `/context`, `/clear`, `/undo`, `/history`, `/system`, `/db` |
| `_RagMixin` | `agent/commands/cmd_rag.py` | `/rag`, `/tool`, `/note`, `/plan`, `/debug` |
| `_IngestMixin` | `agent/commands/cmd_ingest.py` | `/ingest`, `/export`, `/compact` |

## 2. API

```python
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext

cmds = CommandRegistry(ctx)
matched = await cmds.dispatch("/stats")
```

モジュールレベル関数:

| 関数 | 説明 |
|---|---|
| `_budget_breakdown(messages) -> dict[str, int]` | メッセージリストを system / rag / history / tool_results に分類して文字数を集計 |
| `mask_args(args, masked_fields) -> dict` | `masked_fields` に含まれるキーの値を `"***"` に置換して返す |

`CommandRegistry` メソッド:

| メソッド | 説明 |
|---|---|
| `dispatch(line) -> bool` | スラッシュコマンドをルーティングし、マッチした場合は `True` を返す |
| `_generate_session_title(first_input) -> None` | 非同期。チャットモデルに 8 語以内のセッションタイトルを生成させ保存 |
| `_session_load_safe(arg) -> None` | arg を整数 session_id としてパースし `_load_session()` を呼び出し |
| `_session_delete(arg) -> None` | arg を整数 session_id としてパースし current session ガード後に削除 |
| `_cmd_session(args) -> None` | `/session list [n]` / `/session load <id>` / `/session rename <title>` / `/session delete <id>` をディスパッチ |
| `_load_session(session_id) -> None` | `ctx.session.fetch_messages()` でメッセージを取得し `ctx.history` に統合 |
| `_cmd_help() -> None` | ヘルプ・ツール数・現在 LLM URL を表示 |
| `_cmd_mcp(args) -> None` | サーバ状態表示・ウィザード起動。`args=""` で全サーバ表示、`args="install <name>"` でウィザード起動 |
| `_cmd_mcp_status() -> None` | 全サーバの transport / startup_mode / 状態 (OK/RUNNING/STOPPED 等) をテーブル表示 |
| `_cmd_mcp_install(server_name) -> None` | 新規 MCP サーバのスクリプト骨格・設定 JSON・OpenRC スクリプトを生成するウィザード |
| `_cmd_stats() -> None` | ターン数・ツール呼び出し数・LLM リトライ回数・圧縮回数・セマンティックキャッシュヒット数を表示 |
| `_cmd_config() -> None` | 設定ファイルパスと全設定値を表示 |
| `_cmd_context() -> None` | 会話履歴の文字数・圧縮閾値残余・圧縮回数・現在のシステムプロンプト名・予算内訳を表示 |
| `_cmd_clear(args) -> None` | 会話履歴をシステムプロンプトのみにリセットし統計・キャッシュをクリア。`args="new"` のとき新規 DB セッションも開始 |
| `_cmd_undo() -> None` | 直前の user+assistant ターンをメモリ履歴と DB からロールバック |
| `_cmd_history(args) -> None` | 直近 N 件の会話メッセージを先頭 120 文字プレビューで表示 |
| `_cmd_system(args) -> None` | `SYSTEM_PROMPTS` の指定プレセットに切り替え |
| `_cmd_db(args) -> None` | `/db stats` / `/db urls [--lang] [--limit]` / `/db clean <url>` / `/db rebuild-fts` を振り分け |
| `_cmd_note(args) -> None` | `/note add <text>` / `/note list` / `/note delete <id>` を処理 |
| `_cmd_tool(args) -> None` | `/tool list` / `/tool show <idx>` でツール結果ストアを表示 |
| `_cmd_plan() -> None` | `ctx.plan_mode` をトグル。ON 時は `plan_blocked_tools` に含まれるツールを自動ブロック |
| `_cmd_set(args) -> None` | `/set temperature <f>` / `/set max_tokens <n>` でランタイム LLM パラメータを変更 |
| `_cmd_debug() -> None` | `ctx.debug_mode` をトグルして RAG デバッグ出力を切り替え |
| `_print_rag_results(query, queries, reranked) -> None` | `/rag search` 結果を表示する内部ヘルパー |
| `_cmd_rag(args) -> None` | RAG パイプラインをドライランしチャンクのスコア・URL・プレビューを表示 |
| `_render_history_md(history) -> str` | 会話履歴を Markdown 形式に変換して返す |
| `_cmd_export(args) -> None` | 会話履歴を Markdown または JSON でエクスポート |
| `_run_split_and_ingest(loop) -> None` | ChunkSplitter と RagIngester をスレッドエグゼキュータで順次実行 |
| `_cmd_ingest(args) -> None` | URL またはローカルファイルパスをクロール→チャンク分割→DB 投入まで一括実行 |
| `_cmd_compact() -> None` | 閾値に関わらず会話履歴を即時圧縮 |
| `_apply_config_params(new_cfg) -> None` | `ctx.cfg` フィールドを更新し各コンポーネントに同期 |
| `_cmd_reload() -> None` | `config/agent.toml` を再読み込みし `_apply_config_params()` で即時反映 |

## 3. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `self._cmds = CommandRegistry(ctx)` を `run()` で生成し、`_repl_loop()` が `await self._cmds.dispatch(line)` を呼ぶ |
