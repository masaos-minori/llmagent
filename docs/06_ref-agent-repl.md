# agent_repl.py

## 1. 機能概要

全コンポーネントを `AgentContext` へ依存性注入し、REPL ループを駆動する薄いコーディネータ。スラッシュコマンドは `CommandRegistry`、状態は `AgentContext` に委譲。`agent.py` が `AgentREPL()().run()` で起動。

実装は 3 つのサテライトモジュールに分割:
- `agent_repl_health.py` — MCP 死活監視・ウォッチドッグループ
- `agent_repl_tool_exec.py` — ツール呼び出し承認・実行
- `agent_repl_debug.py` — RAG デバッグプリンタ・コンテキストユーティリティ (純粋関数)

## 2. API

```python
from agent_repl import AgentREPL

await AgentREPL().run()
```

| メソッド | 説明 |
|---|---|
| `run() -> None` | readline 初期化 → `_init_components()` → セッション開始 → REPL ループ → リソースクローズ |
| `_init_components() -> None` | `LLMClient` / `ToolExecutor` / `HistoryManager` / `RagPipeline` / `CommandRegistry` を生成して `AgentContext` に注入 |
| `_print_startup_banner() -> None` | 起動時バナー (DB チャンク数・ツール数・モード) を表示 |
| `_run_turn(llm_url) -> str` | SSE ストリーミングで LLM を呼び出し、tool_calls があれば並列実行後に再送信。最終回答テキストを返す |
| `_handle_user_message(line) -> None` | `ctx.rag.augment()` でコンテキスト付加 → 履歴追記 → 圧縮 → LLM 呼び出し → DB 保存 |
| `_execute_one_tool_call(tc) -> tuple[str, str, dict, str, bool]` | 1 件の `tool_call` を解析して `ToolExecutor.execute()` を呼び `(id, name, args, text, is_error)` を返す |
| `_execute_all_tool_calls(tool_calls, turn) -> None` | `asyncio.gather()` で全 tool_call を並列実行し、結果を順序を保って履歴に追記 |

## 3. 処理フロー

```
AgentREPL.run()
  └─ _view.setup_readline()   — readline 設定・補完・履歴ファイル読み込み
  └─ _init_components()       — 全コンポーネントを AgentContext に注入
  └─ _print_startup_banner()  — DB チャンク数・ツール数・モードを表示
  └─ ctx.session.start()      — sessions テーブルに INSERT
  └─ _repl_loop()
       └─ input()             — ユーザ入力待機
       └─ _handle_user_message()
            └─ ctx.rag.augment()    — MQE → KNN+BM25 → RRF → Rerank
            └─ ctx.session.save()  — messages テーブルに保存
            └─ asyncio.create_task(_cmds._generate_session_title())  ← 第1ターンのみ
            └─ ctx.hist_mgr.compress()   — 履歴圧縮
            └─ _run_turn()       — LLM 呼び出し + ツールループ (最大 MAX_TOOL_TURNS 回)
  └─ _close_resources()       — readline 履歴保存・AsyncClient クローズ
```

## 4. 使用スクリプト

`agent.py` が `asyncio.run(AgentREPL().run())` で呼び出す唯一のエントリポイント。
