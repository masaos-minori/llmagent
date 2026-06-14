# agent/context.py

## 1. 機能概要

`AgentREPL` と `CommandRegistry` が共有する per-session mutable state と全コンポーネント参照を一元管理するデータ保持クラス。
状態は4つのサブ構造体に分割されており、各コンポーネントは `ctx.conv.*` / `ctx.turn.*` / `ctx.stats.*` / `ctx.services.*` 経由でアクセスする。

## 2. AgentContext API

```python
from agent.context import AgentContext

ctx = AgentContext()
# 会話状態
ctx.conv.history        # list[LLMMessage]
ctx.conv.llm_url        # str
# ターン状態
ctx.turn.current_turn_id  # str | None
# 統計
ctx.stats.stat_turns    # int
# サービス参照 (factory.build_agent_context() 後に有効)
ctx.services.llm        # LLMClient
```

| フィールド | 型 | 説明 |
|---|---|---|
| `conv` | `ConversationState` | per-session 会話フィールド。詳細は下記 |
| `turn` | `TurnState` | per-turn 一時フィールド。詳細は下記 |
| `stats` | `RuntimeStats` | セッション累計統計。詳細は下記 |
| `cfg` | `AgentConfig` | ホットリロード対象ランタイム設定。詳細は `docs/06_ref-agent-config.md` |
| `session` | `AgentSession` | セッション/メッセージ DB 操作。詳細は `docs/06_ref-agent-session.md` |
| `services` | `AppServices` | 全サービス参照。`factory.build_agent_context()` 完了後に有効 |
| `tool_result_store` | `ToolResultStore` | ツール実行結果の永続ストア。`/tool list` / `/tool show` で参照 |

## 3. ConversationState (ctx.conv.*)

per-session 会話フィールド。`AgentContext.__init__()` 内でデフォルト値がセットされる。

| フィールド | 型 | 初期値 | 説明 |
|---|---|---|---|
| `history` | `list[LLMMessage]` | `[]` | 会話履歴 (system / user / assistant / tool ロール) |
| `llm_url` | `str` | `""` | アクティブな LLM エンドポイント URL |
| `debug_mode` | `bool` | `False` | デバッグ出力フラグ |
| `plan_mode` | `bool` | `False` | プランモードフラグ。`True` のとき `AgentConfig.plan_blocked_tools` に列挙されたツールを自動ブロック |
| `system_prompt_name` | `str` | `"default"` | アクティブなシステムプロンプトプレセット名 |
| `system_prompt_content` | `str` | `""` | 正規のシステムプロンプト文字列。`Orchestrator._sync_system_prompt()` が各ターン開始時に `history[0]` へ反映する |
| `shutdown_requested` | `bool` | `False` | グレースフルシャットダウン要求フラグ |

## 4. TurnState (ctx.turn.*)

per-turn 一時フィールド。`Orchestrator.handle_turn()` が各ターンで管理する。

| フィールド | 型 | 初期値 | 説明 |
|---|---|---|---|
| `current_turn_id` | `str \| None` | `None` | `Orchestrator.handle_turn()` 開始時に UUID4 をセット; ターン間は `None` |

## 5. RuntimeStats (ctx.stats.*)

セッション累計統計フィールド。

| フィールド | 型 | 初期値 | 説明 |
|---|---|---|---|
| `stat_turns` | `int` | `0` | ユーザーターン累計 |
| `stat_tool_calls` | `int` | `0` | ツール呼び出し累計 |
| `stat_tool_errors` | `int` | `0` | ツール実行エラー累計 |
| `stat_latency` | `dict[str, list[float]]` | `{}` | ステップ別レイテンシサンプル (秒) |
| `stat_semantic_cache_hits` | `int` | `0` | セマンティックキャッシュヒット回数累計 |
| `stat_input_tokens` | `int \| None` | `None` | LLM 入力トークン累計。`None` = エンドポイントが `usage` を返さなかった |
| `stat_output_tokens` | `int \| None` | `None` | LLM 出力トークン累計。`None` = エンドポイントが `usage` を返さなかった |

## 6. AppServices (ctx.services.*)

`factory.build_agent_context()` が各フィールドへ実体を注入する。`stdio_procs` は空 dict (`{}`) で初期化、それ以外は `None` で初期化される。

| フィールド | 型 | 初期値 | 説明 |
|---|---|---|---|
| `http` | `httpx.AsyncClient` | — | 共有 HTTP クライアント |
| `llm` | `LLMClient` | — | SSE ストリーミング・リトライ担当 |
| `tools` | `ToolExecutor` | — | MCP ルーティング・TTL キャッシュ担当 |
| `hist_mgr` | `HistoryManager` | — | 履歴文字数カウント・圧縮担当 |
| `lifecycle` | `_ServerLifecycleRouter` / `LifecycleProtocol` | — | stdio サーバの lifecycle 管理 (`factory.py` の `_ServerLifecycleRouter` が routing を担当)。`agent/lifecycle.py` の `restart_stdio()` は残存 |
| `audit_logger` | `Logger` | — | JSON-lines 形式で `audit.log` にターンイベントを書き込む構造化ロガー |
| `memory` | `MemoryServices \| None` | `None` | memory サブサービスコンテナ。`AgentConfig.use_memory_layer=False` (デフォルト) のとき `None`。`mem.injection` / `mem.ingestion` / `mem.store` / `mem.retriever` で各サービスに直接アクセス。`EmbeddingClient` は `injection._embed_client` 経由で参照 |
| `stdio_procs` | `dict[str, StdioTransport]` | `{}` | サーバキー → StdioTransport。stdio トランスポートのプロセスを管理 |
