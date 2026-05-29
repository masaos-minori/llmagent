# agent/context.py

## 1. 機能概要

`AgentREPL` と `CommandRegistry` が共有する per-session mutable state と全コンポーネント参照を一元管理するデータ保持クラス。`AgentREPL().run()` が各フィールドに依存性を注入。

## 2. AgentContext API

```python
from agent.context import AgentContext

ctx = AgentContext()
```

全サービス参照は `ctx.services.<key>` 経由。`AgentContext` に直接サービスフィールドは存在しない。

| フィールド | 型 | 説明 |
|---|---|---|
| `services` | `ServiceContainer` | 全サービス参照を保持する DI コンテナ |
| `history` | `list[LLMMessage]` | 会話履歴 (system / user / assistant / tool ロール) |
| `llm_url` | `str` | アクティブな LLM エンドポイント URL |
| `debug_mode` | `bool` | RAG パイプラインデバッグ出力フラグ |
| `plan_mode` | `bool` | プランモードフラグ。`True` のとき `plan_blocked_tools` を自動ブロック |
| `system_prompt_name` | `str` | アクティブなシステムプロンプトプレセット名 |
| `shutdown_requested` | `bool` | グレースフルシャットダウン要求フラグ |
| `current_turn_id` | `str \| None` | `Orchestrator.handle_turn()` 開始時に UUID4 をセット; `finally` でクリア |
| `current_rag_query_id` | `str \| None` | `Orchestrator._augment_with_rag()` 開始時にセット; RAG スキップ時は `None` |
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

## 3. ServiceContainer API

`AgentREPL._init_components()` が各フィールドを注入する。それ以前は全フィールドが `None`。

| フィールド | 型 | 説明 |
|---|---|---|
| `http` | `httpx.AsyncClient \| None` | 共有 HTTP クライアント |
| `llm` | `LLMClient \| None` | SSE ストリーミング・リトライ担当 |
| `tools` | `ToolExecutor \| None` | MCP ルーティング・TTL キャッシュ担当 |
| `hist_mgr` | `HistoryManager \| None` | 履歴文字数カウント・圧縮担当 |
| `rag` | `RagPipeline \| None` | MQE→検索→RRF→Rerank 担当 |
| `stdio_procs` | `dict[str, StdioTransport]` | サーバキー → StdioTransport。stdio トランスポートのプロセスを管理 |
| `audit_logger` | `Logger \| None` | JSON-lines 形式で `audit.log` にターンイベントを書き込む構造化ロガー |
| `memory` | `MemoryLayer \| None` | Long-term / Task メモリレイヤー。`use_memory_layer=False` (デフォルト) のとき `None` |
