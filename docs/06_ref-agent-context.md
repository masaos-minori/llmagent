# agent_context.py

## 1. 機能概要

`AgentREPL` と `CommandRegistry` が共有する per-session mutable state と全コンポーネント参照を一元管理するデータ保持クラス。`AgentREPL().run()` が各フィールドに依存性を注入。

## 2. API

```python
from agent_context import AgentContext

ctx = AgentContext()
```

| フィールド | 型 | 説明 |
|---|---|---|
| `history` | `list[LLMMessage]` | 会話履歴 (system / user / assistant / tool ロール) |
| `llm_url` | `str` | アクティブな LLM エンドポイント URL |
| `debug_mode` | `bool` | RAG パイプラインデバッグ出力フラグ |
| `plan_mode` | `bool` | プランモードフラグ。`True` のとき `plan_blocked_tools` を自動ブロック |
| `system_prompt_name` | `str` | アクティブなシステムプロンプトプレセット名 |
| `shutdown_requested` | `bool` | グレースフルシャットダウン要求フラグ |
| `stat_turns` | `int` | ユーザーターン累計 |
| `stat_tool_calls` | `int` | ツール呼び出し累計 |
| `stat_rag_hits` | `int` | RAG コンテキスト付加ターン累計 |
| `stat_tool_errors` | `int` | ツール実行エラー累計 |
| `stat_latency` | `dict[str, list[float]]` | ステップ別レイテンシサンプル (秒)。キー: `rag.mqe` / `rag.search` / `rag.rrf` / `rag.rerank` / `llm` |
| `stat_semantic_cache_hits` | `int` | セマンティックキャッシュヒット回数累計 |
| `tool_result_store` | `list[dict]` | 直近 20 件のツール実行結果全文。`/tool list` / `/tool show` で参照。各要素: `{name, args, text, summarized}` |
| `cfg` | `AgentConfig` | ホットリロード対象ランタイム設定 |
| `session` | `AgentSession` | セッション/メッセージ DB 操作 |
| `http` | `httpx.AsyncClient \| None` | 共有 HTTP クライアント |
| `llm` | `LLMClient \| None` | SSE ストリーミング・リトライ担当 |
| `tools` | `ToolExecutor \| None` | MCP ルーティング・TTL キャッシュ担当 |
| `hist_mgr` | `HistoryManager \| None` | 履歴文字数カウント・圧縮担当 |
| `rag` | `RagPipeline \| None` | MQE→検索→RRF→Rerank 担当 |
| `stdio_procs` | `dict[str, StdioTransport]` | サーバキー → StdioTransport。stdio トランスポートのプロセスを管理 |
