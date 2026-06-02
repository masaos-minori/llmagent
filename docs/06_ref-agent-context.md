# agent/context.py

## 1. 機能概要

`AgentREPL` と `CommandRegistry` が共有する per-session mutable state と全コンポーネント参照を一元管理するデータ保持クラス。全フィールド (`history` / `llm_url` / `debug_mode` / `plan_mode` / `system_prompt_name` / `shutdown_requested` / 統計カウンタ / `cfg` / `session` / `tool_result_store` など) は `AgentContext.__init__()` 内で初期値にセットされる。サービス参照 (`services.*`) は `AgentREPL._init_components()` が注入する。

## 2. AgentContext API

```python
from agent.context import AgentContext

ctx = AgentContext()
```

全サービス参照は `ctx.services.<key>` 経由。`AgentContext` に直接サービスフィールドは存在しない。

| フィールド | 型 | 初期値 | 説明 |
|---|---|---|---|
| `services` | `ServiceContainer` | `ServiceContainer()` | 全サービス参照を保持する DI コンテナ |
| `history` | `list[LLMMessage]` | `[]` | 会話履歴 (system / user / assistant / tool ロール) |
| `llm_url` | `str` | `""` | アクティブな LLM エンドポイント URL |
| `debug_mode` | `bool` | `False` | RAG パイプラインデバッグ出力フラグ |
| `plan_mode` | `bool` | `False` | プランモードフラグ。`True` のとき `AgentConfig.plan_blocked_tools` に列挙されたツールを自動ブロック |
| `system_prompt_name` | `str` | `"default"` | アクティブなシステムプロンプトプレセット名 |
| `shutdown_requested` | `bool` | `False` | グレースフルシャットダウン要求フラグ |
| `current_turn_id` | `str \| None` | `None` | `Orchestrator.handle_turn()` 開始時に UUID4 をセット; ターン間は `None` |
| `current_rag_query_id` | `str \| None` | `None` | 予約フィールド。in-process RAG 除去後は常に `None`。将来の RAG トレース用途向けに保持 |
| `stat_turns` | `int` | `0` | ユーザーターン累計 |
| `stat_tool_calls` | `int` | `0` | ツール呼び出し累計 |
| `stat_rag_hits` | `int` | `0` | RAG コンテキスト付加ターン累計 |
| `stat_tool_errors` | `int` | `0` | ツール実行エラー累計 |
| `stat_latency` | `dict[str, list[float]]` | `{}` | ステップ別レイテンシサンプル (秒)。キー: `rag.mqe` / `rag.search` / `rag.rrf` / `rag.rerank` / `llm` |
| `stat_semantic_cache_hits` | `int` | `0` | セマンティックキャッシュヒット回数累計 |
| `stat_input_tokens` | `int \| None` | `None` | LLM 入力トークン累計。`None` = エンドポイントが `usage` を返さなかった |
| `stat_output_tokens` | `int \| None` | `None` | LLM 出力トークン累計。`None` = エンドポイントが `usage` を返さなかった |
| `tool_result_store` | `ToolResultStore` | `ToolResultStore()` | ツール実行結果の永続ストア。`/tool list` / `/tool show` で参照 |
| `cfg` | `AgentConfig` | `build_agent_config()` | ホットリロード対象ランタイム設定。詳細は `docs/06_ref-agent-config.md` 参照 |
| `session` | `AgentSession` | `AgentSession()` | セッション/メッセージ DB 操作。詳細は `docs/06_ref-agent-session.md` 参照 |

## 3. ServiceContainer API

全フィールドは `ServiceContainer.__init__()` 内で初期値にセットされる。`stdio_procs` は空 dict (`{}`) で初期化、それ以外のフィールドは `None` で初期化される。`AgentREPL._init_components()` が各フィールドへ実体を注入する。

| フィールド | 型 | 初期値 | 説明 |
|---|---|---|---|
| `http` | `httpx.AsyncClient \| None` | `None` | 共有 HTTP クライアント |
| `llm` | `LLMClient \| None` | `None` | SSE ストリーミング・リトライ担当 |
| `tools` | `ToolExecutor \| None` | `None` | MCP ルーティング・TTL キャッシュ担当 |
| `hist_mgr` | `HistoryManager \| None` | `None` | 履歴文字数カウント・圧縮担当 |
| `stdio_procs` | `dict[str, StdioTransport]` | `{}` | サーバキー → StdioTransport。stdio トランスポートのプロセスを管理 |
| `lifecycle` | `ServerLifecycleManager \| None` | `None` | ondemand stdio サーバの起動・停止ライフサイクル管理 |
| `audit_logger` | `Logger \| None` | `None` | JSON-lines 形式で `audit.log` にターンイベントを書き込む構造化ロガー |
| `memory` | `MemoryLayer \| None` | `None` | Long-term / Task メモリレイヤー。`AgentConfig.use_memory_layer=False` (デフォルト) のとき `None` のまま。ライフサイクルフック: `on_session_start()` (SessionStart: top semantic entries をシステムプロンプトへ注入) / `on_user_prompt()` (UserPromptSubmit: 関連メモリをターン前に system ロールとして注入) / `on_session_stop()` (Stop: セッション終了時に会話履歴からエントリを抽出して JSONL + SQLite へ永続化) |
