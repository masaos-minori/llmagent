---
title: "Agent State and Persistence - State Model (Part 1)"
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
  - 05_agent_04_01_state-and-persistence-state-model-part1.md
---

# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)
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

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`
- `05_agent_04_01_state-and-persistence-state-model-part2.md`

## Keywords

AgentContext state model
ConversationState
TurnState
WorkflowState
RuntimeStats
session persistence
