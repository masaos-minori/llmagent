---
title: "Agent State and Persistence - State Model"
category: agent
tags:
  - agent
  - state
  - persistence
  - agentcontext
  - session
related:
  - 05_agent_00_document-guide.md
  - 05_agent_04_02_state-and-persistence-history-compression.md
  - 05_agent_04_03_state-and-persistence-platform-databases.md
source:
  - 05_agent_04_01_state-and-persistence-state-model.md
---

# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- データレイヤー (スキーマ) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## 目的

エージェントの状態モデルを定義する: セッションスコープ/ターンスコープ/永続化対象の区分、
履歴圧縮がデータベースとどう相互作用するか、どのデータを誰が所有するか。

---

## AgentContext状態モデル

`AgentContext` (`agent/context.py`) はセッションごとのDIハブである。すべての可変状態はここに存在する。

### ConversationState (`ctx.conv`)

セッションスコープ。REPLのライフタイム中は保持される。

| Field | Type | Initial | Description |
|---|---|---|---|
| `history` | `list[LLMMessage]` | `[]` | アクティブな会話履歴 (system/user/assistant/tool) |
| `llm_url` | `str` | `""` | アクティブなLLMエンドポイントURL |
| `debug_mode` | `bool` | `False` | デバッグ出力フラグ |
| `plan_mode` | `bool` | `False` | プランモード; `plan_blocked_tools`をブロックする |
| `system_prompt_name` | `str` | `"default"` | アクティブなシステムプロンプトプリセット名 |
| `system_prompt_content` | `str` | `""` | システムプロンプトの全文; 各ターンごとに`history[0]`と同期される |
| `shutdown_requested` | `bool` | `False` | グレースフルシャットダウンフラグ |

### TurnState (`ctx.turn`)

ターンスコープ。ターン間でリセットされる。

| Field | Type | Initial | Description |
|---|---|---|---|
| `current_turn_id` | `str\|None` | `None` | ターン開始時にUUID4がセットされる; ターン間は`None` |
| `background_tasks` | `set[asyncio.Task[Any]]` | `set()` | このターン中に生成されたバックグラウンドタスク; クリーンシャットダウンのため追跡される |
| `last_error_kind` | `str\|None` | `None` | 直近のターン失敗時のエラー種別; 直近のターンが成功していれば`None` |
| `pending_approval_id` | `str\|None` | `None` | 直近のワークフローターンが人間の承認待ちで一時停止した際の承認ID |

### WorkflowState (`ctx.workflow`)

セッションスコープのワークフローランタイム状態。一時的なもので、REPL再起動をまたいで永続化されない。
永続的なタスク状態は (`StateStore`経由で) `workflow.sqlite`に存在する。

| Field | Type | Initial | Description |
|---|---|---|---|
| `active` | `bool` | `False` | `WorkflowEngine.run()`実行中は`True` |
| `current_task_id` | `str\|None` | `None` | 実行中のワークフロータスクのタスクID; アイドル時は`None` |
| `workflow_id` | `str\|None` | `None` | このワークフロー実行のUUID4; アイドル時は`None` |
| `current_workflow_version` | `str\|None` | `None` | `WorkflowDef`由来のワークフローバージョン文字列 |
| `approval_pending` | `bool` | `False` | ターンが承認ゲートで一時停止した場合`True` |
| `last_session_id` | `str\|None` | `None` | 直近の`create_task()`呼び出しで使用されたセッションID |

`Orchestrator.handle_turn()`はタスク作成時に`active=True`と`current_task_id`を設定し、
エンジン完了後または`WorkflowHaltError`発生後にいずれもクリアする。
`WorkflowPendingApprovalError`発生時 (ターン一時停止) に`approval_pending=True`が設定される。

### RuntimeStats (`ctx.stats`)

セッション累積のカウンタとレイテンシサンプル。

| Field | Type | Description |
|---|---|---|
| `stat_turns` | `int` | ユーザーターン数 |
| `stat_tool_calls` | `int` | ツール呼び出し数 |
| `stat_tool_errors` | `int` | ツールエラー数 |
| `stat_latency` | `dict[str, list[float]]` | ステップ単位のレイテンシサンプル (秒) |
| `stat_semantic_cache_hits` | `int` | セマンティックキャッシュヒット数 |
| `stat_input_tokens` | `int\|None` | LLM入力トークン数 (エンドポイントが`usage`を省略している場合`None`) |
| `stat_output_tokens` | `int\|None` | LLM出力トークン数 (エンドポイントが`usage`を省略している場合`None`) |
| `stat_serialization_events` | `list[dict]` | DAGツールスケジューラと標準ランナーが記録するラウンドごとのシリアル化イベント。全ターンを通じて累積される。初期値: `[]`。`/mcp`コマンドで表示される。 |
| `stat_serialization_total_overhead_ms` | `float` | 全ターンを通じて累積される合計シリアル化オーバーヘッド (ミリ秒)。初期値: `0.0`。 |
| `stat_memory_consistency_failures` | `int` | このセッションでの`/memory check-consistency`失敗回数。`cmd_memory.py`によりインクリメントされる。初期値: `0`。 |
| `stat_memory_circuit_open` | `bool` | メモリ埋め込みのサーキットブレーカーがオープン状態の場合`True`。表示時に`MemoryServices`から読み取られる — 通常運用中は`ctx.stats`に**書き込まれない**。初期値: `False`。 |
| `stat_memory_fts_fallback_count` | `int` | このセッションでのFTSフォールバック回数 (埋め込みが利用不可の場合にトリガーされる)。`MemoryServices.retriever.fts_fallback_count`をミラーする — 表示時に読み取られ、`ctx.stats`では独立して追跡されない。初期値: `0`。 |

---

## セッション永続化 (`AgentSession`)

`AgentSession` (`agent/session.py`) が`session.sqlite`を管理する。

### ターンごとに永続化される内容

| Event | Table | Content |
|---|---|---|
| セッション開始 | `sessions` | session_id, created_at, title |
| 各メッセージ | `messages` | role, content, tool_calls, tool_call_id, session_id |

### セッションのライフサイクル

```
AgentREPL.run()
  → AgentSession.start()              — sessionsへINSERT; session_idを取得
  → each turn: AgentSession.save()    — messagesへINSERT
  → /session load <id>                — fetch_messages() → ctx.conv.historyを再構築
  → /session delete <id>              — sessions + messagesをDELETE (CASCADE)
```

### セッションタイトル生成

最初のユーザーターンにおいて、`cmd_session.py`内のセッションタイトル生成が`SessionTitleService.generate()`を呼び出し、LLMベースの短いタイトルを生成する。これはasyncioのバックグラウンドタスクとして実行される (`asyncio.create_task()`によるfire-and-forget)。

### セッションタイトル生成失敗時の挙動

| Failure case | Fallback title | Log |
|---|---|---|
| LLM HTTP/リクエストエラー | 長さ > 32の場合`first_input[:29] + "..."`、それ以外は`first_input` | WARNING |
| LLMが空または不正なレスポンスを返す | 上記と同様 | WARNING |
| `first_input`が空 | `"(New Session)"` | WARNING |
| `set_title()`のDB書き込みが失敗 | タイトルは永続化されない; エラーがログに記録される | ERROR |

すべての失敗ケースはノンブロッキングであり、セッションは通常通り継続する。
フォールバック時、監査ログエントリが発行される: `session_title_fallback session_id=<id> fallback=<title> reason=<error>`。
`set_title_pending`は結果にかかわらず`finally`ブロックで`False`にリセットされる。

### メッセージ保存ルール

- `save(role, content)`は有効なロールのみを保存する: `user`, `assistant`, `tool`, `system`
- 無効なロールは警告としてログに記録され、カウントされる (`stat_skipped_invalid_role`)
- `session_id`が欠落している場合は警告としてログに記録され、カウントされる (`stat_skipped_no_session`)
- `strict_mode=True`の場合、両条件ともスキップの代わりに`RuntimeError`を発生させる
- カウンタは`session.skipped_no_session_count`と`session.skipped_invalid_role_count`からアクセス可能
- `save_many(messages)`は複数のメッセージを1つのトランザクションでバッチ処理する; 無効なロールは単一の警告ログと共にスキップされる
- `replace_messages(messages)`は圧縮された履歴のスナップショットをDBに書き戻す; session_idがNoneの場合は黙ってスキップする
- 診断データ (LLMトランスポートエラー、ガードヒント、セッションランタイムサマリー) は`DiagnosticStore` (`agent/diagnostic_store.py`) 経由で`session_diagnostics`テーブルに永続化される — `messages`テーブルとは別。部分完了の永続化モデルについては → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)
- `DiagnosticStore`のメソッド: `save(session_id, kind, content)`, `fetch(session_id)`, `fetch_all(limit=50)`
- `AgentContext.diagnostics`は初期化時にorchestratorの診断ストアに接続される; `Orchestrator`が構築される前は`None`
- 書き込まれる種別: `"mid_turn_error"` (`ErrorInjectionService`, `LLMTurnRunner`, `Orchestrator`からのLLMトランスポートエラー), `"guard_hint"` (`ToolLoopGuard`からの循環/重複排除/リトライイベント)
- ガードヒントとターン中のエラーは診断データにのみ格納される — `ctx.conv.history`には現れない
- 診断データは`DiagnosticStore`経由で`session_diagnostics`テーブルに格納される; `messages`には決して存在せず、したがって`fetch_messages()`からは返されない

> **現在の挙動:** DiagnosticStoreは`session_diagnostics`テーブルにのみ書き込む。診断データは`session_diagnostics`を通じてのみ永続化され、`diagnostics.jsonl`への二重永続化は行われない。

---

## 会話履歴とデータベースの関係

```
ctx.conv.history (in-memory list)
    ↕ synchronized per turn
AgentSession (session.sqlite: sessions + messages)
```

- セッション中はhistoryが正となるソースである
- データベースは永続的なバックアップである
- `/session load <id>`はデータベースから`ctx.conv.history`を再構築する
- `delete_last_turn()`はDBから最後の (最大2件の) 行を削除する
- `undo_last_turn()`は最後の`role='user'`メッセージ以降のすべてを削除する

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`

## Keywords

AgentContext state model
ConversationState
TurnState
WorkflowState
RuntimeStats
session persistence
