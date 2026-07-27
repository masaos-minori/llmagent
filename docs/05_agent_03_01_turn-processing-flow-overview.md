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

## 目的

1回の会話ターンにおける操作の正確なシーケンスを、状態遷移・エラーハンドリングパス・
部分完了時の挙動を含めて文書化する。

---

## 1ターンの処理フロー

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
       │   一時停止中の場合もここでブロックする。下記「バックグラウンドタスク失敗時の
       │   閾値通知と一時停止」参照)
       │
       ① ターン開始処理
       │    → UUID4のcurrent_turn_idを生成
       │    → 監査ログを発行: turn_start
       │    → WorkflowEngine.run(task, plan_fn, execute_fn, verify_fn) を起動
       │         (plan_fnは何もしない; ターン開始処理は既にここで完了済み)
       │
       ② メモリ注入 と モード分類          [WorkflowEngineのexecuteステージ内]
       │    → [use_memory_layer=Trueの場合] MemoryInjectionService.on_user_prompt(query, session_id)
       │    → メモリスニペットを"system"ロールメッセージとして注入
       │          → memory_injectedフラグを設定
       │    → classify_and_inject_mode(line, ctx): クエリをMDQ/RAGに分類し、
       │         ヒントを"_ephemeral"付きsystemメッセージとして注入 (下記参照)
       │
       ③ ユーザーメッセージの追加
        │    → システムプロンプト同期 (下記参照)
        │    → ユーザーメッセージをctx.conv.append_message()経由でctx.conv.historyに追加
        │    → AgentSession.save("user", content)
        │    → (最初のターンのみ) セッションタイトル生成のためasyncio.create_task
        │         (タスクにはon_first_turnコールバックの__name__を明示的にname=として
        │          付与する。下記「バックグラウンドタスク失敗時の閾値通知と一時停止」参照)
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
       │                   → ツール実行結果を"tool"ロールとしてctx.conv.append_message()経由で履歴に追加
       │                        (拒否されたツール呼び出しはctx.conv.extend_messages()経由で追加; 詳細は
       │                         05_agent_06_01_tool-execution-and-approval-execution.md §履歴への結果反映 参照)
       │              → 履歴をLLMに再送信
       │              → ToolLoopGuard: 重複排除/循環/リトライ/連続エラーのガード
       │
       ⑥ ターン終了処理                    [WorkflowEngineのverifyステージ内]
            → 監査ログを発行: turn_end (経過ms、トークン数、再接続回数など)
            → ctx.turn.current_turn_id = None
```

### Implementation note: ワークフローエンジンは常に経由する (Explicit in code)

`Orchestrator.__init__`は`WorkflowLoader().load()`を呼び、失敗時（`config/workflows/default.json`が
存在しない、または検証エラー）は`RuntimeError`を送出してOrchestratorの構築自体が失敗する。
そのため`handle_turn()`が呼ばれる時点で`self._workflow_def`は非`None`であることが保証されており
（`handle_turn()`側にこれを再チェックするコードは存在しない — 保証はコメントとして明記されている）、
ワークフロー必須であり、直接実行へのフォールバック経路は一切存在しない。
上記フロー図の①〜⑥はすべて`WorkflowEngine.run()`のplan/execute/verify各ステージのコールバックとして
実行される。`plan_fn`自体は意図的に無処理(no-op)であり、①のターン開始処理（`current_turn_id`生成、
`turn_start`監査ログ発行）が計画相当の作業として既に完了しているためである
(根拠: `agent/orchestrator.py`の`_handle_workflow_engine()`内`plan_fn`定義コメント)。
ステージ構成の詳細は
[05_agent_03_03_turn-processing-flow-workflow-engine-part1.md](05_agent_03_03_turn-processing-flow-workflow-engine-part1.md)を参照。

### バックグラウンドタスク失敗時の閾値通知と一時停止 (Explicit in code)

最初のターンでスケジュールされるセッションタイトル生成タスク(`self._on_first_turn`)は、完了時に
`Orchestrator._discard_and_log()`がコールバックとして呼ばれ、連続失敗回数
(`self._consecutive_bg_failures`)を管理する。`asyncio.create_task(..., name=...)`で明示的に
付与されたタスク名(`on_first_turn.__name__`、既定は`_generate_session_title`)は
`task.get_name()`で読み戻され、ログメッセージに含められる。

- 連続失敗回数が`BG_FAILURE_THRESHOLD`(既定5、`agent/orchestrator.py`のモジュール定数)に
  **到達した瞬間**(`==`であり`>=`ではない)、`Orchestrator._notify_bg_failure_threshold()`が
  1回だけ呼ばれる。
- `_notify_bg_failure_threshold()`は`self._on_error`経由でユーザーに通知することを保証する:
  `_on_error`自体が例外を送出した場合は`logger.critical()`にフォールバックし、例外を
  `_discard_and_log()`の外へ伝播させない。
- コンストラクタの新しいオプトインパラメータ`pause_on_critical_failure`(既定`False`)が
  `True`の場合、閾値到達時に該当タスク種別を`self._bg_pause_state[task_name] = True`として
  一時停止済みとマークする。`_bg_pause_state`はタスク種別ごと(`dict[str, bool]`)であり、
  グローバルな一時停止フラグではない。
- `handle_turn()`は`approval_pending`ガードの直後で`self._bg_pause_state`にTrueの
  エントリが1つでもあれば早期リターンし、`_on_error`経由でユーザーに通知する
  (`ctx.workflow.approval_pending`ガードと同じ形の早期リターン)。一時停止状態はプロセス内
  メモリのみで保持され、`/resume`コマンドなど明示的に解除する手段は現状存在しない。
  プロセスを再起動するまで解除されない。
- `pause_on_critical_failure`は既定で`False`のため、既存の`Orchestrator(...)`呼び出し元
  (`startup.py`など)はオプトインしない限りこの一時停止機構の影響を受けない。

---

## メモリ注入の詳細

- `AgentConfig.use_memory_layer=True`の場合、ステップ②でトリガーされる
- `MemoryInjectionService.on_user_prompt()`が関連メモリを取得する (FTS5 + オプションでKNN)
- ターンの先頭に`"system"`ロールメッセージとして注入される
- `/undo`はこれらの注入メッセージ(`_memory_injected`)およびモード分類の`_ephemeral`ヒントメッセージを、
  ユーザー+アシスタントのターンと共に削除する(`agent/services/undo_service.py`)
- `Orchestrator._handle_memory_injection()`は生の`ctx.conv.history.append()`ではなく
  `ctx.conv.append_message(msg, source="memory_injection")`を呼ぶ (`agent/orchestrator.py`)。
  `TRUSTED_SOURCES["memory_injection"]`が`_memory_injected`キーを認可するため、この呼び出しは
  検証を通過して従来通りメッセージを追加する。詳細は
  [05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md)
  §検証付き履歴変更メソッド を参照

---

## MDQ/RAGモード分類の詳細

- `classify_and_inject_mode(line, ctx)` (`agent/mode_classification.py`) がメモリ注入と同じ
  execute ステージ内、ユーザーメッセージ追加より前に実行される (Explicit in code)
- `resolve_mode()` (`agent/mdq_rag_classifier.py`): `ctx.cfg.mdq_rag_mode`が`"auto"`以外の
  設定値であればそれを優先し、`"auto"`または未設定なら`classify_query()`のキーワードヒューリスティクス
  (`heading`, `outline`, `toc`, `.md`, `structure`など) でMDQ/RAGを判定する
- MDQモードと判定されても`search_docs`ツールを持つMCPサーバーが利用不可の場合はRAGにフォールバックする
  (警告ログを出力)
- 判定結果に応じたヒント文字列を`"system"`ロール・`_ephemeral: true`付きメッセージとして、
  生の`ctx.conv.history.append()`ではなく`ctx.conv.append_message(msg, source="cmd_handler")`
  経由で追加する(`agent/mode_classification.py`)。`TRUSTED_SOURCES["cmd_handler"]`が
  `_ephemeral`キーを認可するため、この呼び出しは検証を通過して従来通りメッセージを追加する。
  詳細は
  [05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md)
  §検証付き履歴変更メソッド を参照。`_ephemeral`メッセージ(および`_memory_injected`メッセージ)は
  `_process_turn()`の先頭、メモリ注入・モード分類より前に呼ばれる
  前ターン ephemeral メッセージクリア関数で、**前のターン**分のみが除去される
  (毎ターン再評価される一時的なヒント)。この呼び出し順序により、当該ターンで注入した内容は
  同一ターンのLLM呼び出しに正しく渡り、次ターン開始時にのみ除去される
  (システムプロンプト同期関数はシステムプロンプト本文の同期のみを担当し、この除去処理は行わない)

---

## システムプロンプト同期の詳細

- `Orchestrator._sync_system_prompt()`はステップ③で、ユーザーメッセージ追加より前に呼ばれる
  (`agent/orchestrator.py`)
- `ctx.conv.history[0]`が既に`"system"`ロールの場合は`content`をその場で上書きする
  (キー構成は変わらないため検証は行わない)
- `ctx.conv.history[0]`が存在しないか`"system"`ロールでない場合は、新規に
  `{"role": "system", "content": ...}`を構築し、`agent/message_schema.py::validate_message()`で
  検証してから`ctx.conv.history.insert(0, msg)`する。このメッセージは常にrole/contentのみで
  構成されるため検証は常に成功する設計だが、万一失敗した場合は`error`ログを出力して挿入をスキップする
  (`ConversationState`はappendのみを提供し位置指定挿入を持たないため、この分岐は
  `ConversationState.append_message()`を経由せず`orchestrator.py`内で直接検証する)

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
