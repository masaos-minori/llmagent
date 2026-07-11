---
title: "Agent Turn Processing Flow - Overview"
category: agent
tags:
  - agent
  - turn
  - processing
  - flow
  - orchestrator
related:
  - 05_agent_00_document-guide.md
  - 05_agent_03_02_turn-processing-flow-llm-tool-loop.md
  - 05_agent_03_03_turn-processing-flow-workflow-engine.md
source:
  - 05_agent_03_01_turn-processing-flow-overview.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## 目的

1回の会話ターンにおける操作の正確なシーケンスを、状態遷移・エラーハンドリングパス・
部分完了時の挙動を含めて文書化する。

---

## 1ターンの処理フロー

```
User input (line)
  │
  ├─ line.startswith("/")
  │    └─ CommandRegistry.dispatch(line)     — スラッシュコマンド、LLM呼び出しなし
  │
  └─ Orchestrator.handle_turn(line)
       │
       ① ターン開始処理
       │    → UUID4のcurrent_turn_idを生成
       │    → 監査ログを発行: turn_start
       │
       ② メモリ注入                       [use_memory_layer=Trueの場合]
       │    → MemoryInjectionService.on_user_prompt(query, session_id)
       │    → メモリスニペットを"system"ロールメッセージとして注入
       │          → memory_injectedフラグを設定
       │
       ③ ユーザーメッセージの追加
        │    → ユーザーメッセージをctx.conv.historyに追加
        │    → AgentSession.save("user", content)
        │    → (最初のターンのみ) セッションタイトル生成のためasyncio.create_task
        │
        ④ 履歴圧縮の処理
       │    → HistoryManager.compress(history)
       │    → 文字数/トークン数の上限を超えた場合、最も古いターンをLLM要約で置換
       │
       ⑤ LLMターン処理
       │    → LLMTurnRunner.run(llm_url)
       │         ├─ LLMClient.stream(url, history, tool_defs)
       │         │    → SSEストリーミング → on_tokenコールバック → CLIView.write_token()
       │         │    → content_parts + tool_calls_mapを収集
       │         │
       │         └─ ツールループ (内部、max_tool_turns=5まで):
       │              → execute_all_tool_calls()
       │                   → 副作用のあるツールが存在しない限り並列実行 (asyncio.gather)
       │                   → ToolExecutor.execute(tool_name, args)
       │                   → ツール実行結果を"tool"ロールとして履歴に追加
       │              → 履歴をLLMに再送信
       │              → ToolLoopGuard: 重複排除/循環/リトライ/連続エラーのガード
       │
       ⑥ ターン終了処理
            → 監査ログを発行: turn_end (経過ms、トークン数、再接続回数など)
            → ctx.turn.current_turn_id = None
```

---

## メモリ注入の詳細

- `AgentConfig.use_memory_layer=True`の場合、ステップ②でトリガーされる
- `MemoryInjectionService.on_user_prompt()`が関連メモリを取得する (FTS5 + オプションでKNN)
- ターンの先頭に`"system"`ロールメッセージとして注入される
- `/undo`はこれらの注入メッセージをユーザー+アシスタントのターンと共に削除する

---

## 履歴圧縮の詳細

- 毎ターン、ステップ④でトリガーされる (閾値未満の場合は何もしない)
- `HistoryManager.compress()`は`context_char_limit` (文字数) と `context_token_limit` (トークン数) の両方をチェックする
- `HistorySelectionPolicy`が重要度スコアとカテゴリに基づき最も古いターンを選択する:
  - `temporary` (toolロール) → 最も保持優先度が低い
  - `temporary_reasoning` (tool_calls付きassistant) → 優先度低
  - `factual` (system) → 保持される
  - `history` (user/assistantのテキスト) → 通常優先度
- 直近の`history_protect_turns` (デフォルト2) ターンペアは常に保護される
- 成功時: `CLIView.write_compress_notice(n)`が圧縮通知を表示する
- 文字数上限超過中にLLM呼び出しが失敗した場合: 重要度の低いメッセージから
  (toolロールを優先し、次に`classify_importance`の昇順でソート) 上限を下回るまで破棄する
- フォールバック回数は`stat_fallback_truncate_count`で追跡され、`/context`で"Fallback trunc"として表示される

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`

## Keywords

one-turn processing flow
memory injection detail
history compression detail
