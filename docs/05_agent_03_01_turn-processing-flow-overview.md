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
  - 05_agent_03_03_turn-processing-flow-workflow-engine-part1.md
  - 05_agent_04_01_state-and-persistence-state-model-part1.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
source:
  - 05_agent_03_01_turn-processing-flow-overview.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)

## Purpose

1回の会話ターンにおける操作の正確なシーケンスを、状態遷移・エラーハンドリングパス・
部分完了時の挙動を含めて文書化する。

## Design Intent

ワークフローエンジン経由での実行は必須である。ワークフロー定義のロード失敗は起動時に
`RuntimeError`として検知され、ダイレクト実行へのフォールバック経路は一切存在しない。
この設計により、すべての副作用を伴う操作を追跡可能にし、承認状態をプロセス境界を越えて存続させる。

## Responsibility Boundary

### 1ターンの処理フロー

``` text
User input (line)
   │
   ├─ line.startswith("/")
   │    └─ CommandRegistry.dispatch(line)     — スラッシュコマンド、LLM呼び出しなし
   │
   └─ Orchestrator.handle_turn(line)
        │  (workflow.approval_pendingの場合はここでブロックし、
        │   /approve または /reject を促すエラーを返して処理を終了する)
        │  (続けて、いずれかのバックグラウンドタスク種別が_bg_pause_stateで
        │   一時停止中の場合もここでブロックする)
        │
        ① ターン開始処理
        │    → current_turn_idを生成
        │    → 監査ログを発行: turn_start
        │    → WorkflowEngine.run(task, plan_fn, execute_fn, verify_fn) を起動
        │         (plan_fnは何もしない; ターン開始処理は既にここで完了済み)
        │
        ② メモリ注入 と モード分類          [WorkflowEngineのexecuteステージ内]
        │    → MemoryInjectionService.on_user_prompt() が関連メモリを取得する
        │    → メモリスニペットを"system"ロールメッセージとして注入
        │    → classify_and_inject_mode(): クエリをMDQ/RAGに分類し、
        │         ヒントを"_ephemeral"付きsystemメッセージとして注入
        │
        ③ ユーザーメッセージの追加
         │    → システムプロンプト同期
         │    → ユーザーメッセージを履歴に追加
         │    → AgentSession.save("user", content)
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
        │                   → 副作用のあるツールが存在しない限り並列実行
        │                   → ToolExecutor.execute(tool_name, args)
        │                   → ツール実行結果を"tool"ロールとして履歴に追加
        │                        (拒否されたツール呼び出しはextend_messages()経由で追加)
        │              → 履歴をLLMに再送信
        │              → ToolLoopGuard: 重複排除/循環/リトライ/連続エラーのガード
        │
        ⑥ ターン終了処理                    [WorkflowEngineのverifyステージ内]
             → 監査ログを発行: turn_end (経過ms、トークン数、再接続回数など)
             → current_turn_id = None
```

### Implementation note: ワークフローエンジンは常に経由する

`Orchestrator.__init__`は`WorkflowLoader().load()`を呼び、失敗時は
`RuntimeError`を送出してOrchestratorの構築自体が失敗する。そのため
`handle_turn()`が呼ばれる時点でワークフロー定義は非Noneであり、
ワークフロー必須であり、直接実行へのフォールバック経路は一切存在しない。
上記フロー図の①〜⑥はすべて`WorkflowEngine.run()`のplan/execute/verify各ステージのコールバックとして
実行される。`plan_fn`自体は意図的に無処理(no-op)であり、①のターン開始処理が計画相当の作業として
既に完了しているためである。ステージ構成の詳細は
[05_agent_03_03_turn-processing-flow-workflow-engine-part1.md](05_agent_03_03_turn-processing-flow-workflow-engine-part1.md)を参照。

### バックグラウンドタスク失敗時の閾値通知と一時停止

最初のターンでスケジュールされるセッションタイトル生成タスクは、完了時に
連続失敗回数を管理する。

- 連続失敗回数が閾値に到達した瞬間、`_notify_bg_failure_threshold()`が1回だけ呼ばれる。
- `_notify_bg_failure_threshold()`はユーザーに通知を保証する。例外が発生した場合は
  `logger.critical()`にフォールバックし、例外を伝播させない。
- コンストラクタのオプトインパラメータ`pause_on_critical_failure`が
  `True`の場合、閾値到達時に該当タスク種別を一時停止済みとマークする。
  グローバルな一時停止フラグではなくタスク種別ごとの制御である。
- `handle_turn()`は`approval_pending`ガードの直後で`_bg_pause_state`にTrueの
  エントリが1つでもあれば早期リターンし、ユーザーに通知する。
  一時停止状態はプロセス内メモリのみで保持され、プロセス再起動まで解除されない。
- `pause_on_critical_failure`は既定で`False`のため、既存の呼び出し元は
  オプトインしない限りこの一時停止機構の影響を受けない。

## Key Constraints

### メモリ注入

- `AgentConfig.use_memory_layer=True`の場合、ステップ②でトリガーされる
- `/undo`はこれらの注入メッセージおよびモード分類のヒントメッセージを削除する
- メモリ注入は検証付きの`append_message(msg, source="memory_injection")`経由で追加される

### MDQ/RAGモード分類

- `classify_and_inject_mode()` がメモリ注入と同じexecuteステージ内、ユーザーメッセージ追加より前に実行される
- `ctx.cfg.mdq_rag_mode`が`"auto"`以外の設定値であればそれを優先し、`"auto"`または未設定なら
  キーワードヒューリスティクスでMDQ/RAGを判定する
- MDQモードと判定されても`search_docs`ツールを持つMCPサーバーが利用不可の場合はRAGにフォールバックする
- 判定結果に応じたヒント文字列を`"system"`ロール・`_ephemeral: true`付きメッセージとして追加する

### システムプロンプト同期

- `Orchestrator._sync_system_prompt()`はステップ③で、ユーザーメッセージ追加より前に呼ばれる
- `ctx.conv.history[0]`が既に`"system"`ロールの場合は`content`を上書きする
- 新規にシステムメッセージを構築する場合は検証してから挿入する

### 履歴圧縮

- 毎ターン、ステップ④でトリガーされる（閾値未満の場合は何もしない）
- 重要度スコアに基づき最も古いターンを選択する
- 直近の`history_protect_turns`ターンペアは保護される
- 成功時: 圧縮通知を表示する
- 文字数上限超過中にLLM呼び出しが失敗した場合: 重要度の低いメッセージから破棄する

## Operational Notes

- バックグラウンドタスクの失敗閾値到達時通知と一時停止機構はオプトイン（既定無効）。
- 部分的なコンテンツは通常の会話履歴から分離され、以降のLLMコンテキストを汚染しない。

## Known Limitations

- バックグラウンドタスクの失敗閾値到達時通知と一時停止機構はオプトイン（既定無効）。
  プロセス再起動まで一時停止状態は解除されない。

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`
- `05_agent_04_01_state-and-persistence-state-model-part1.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`

## Keywords

one-turn processing flow
memory injection detail
mdq/rag mode classification
system prompt sync detail
validated history append/insert
validated tool result/denied-message append
workflow engine mandatory execution path
history compression detail
