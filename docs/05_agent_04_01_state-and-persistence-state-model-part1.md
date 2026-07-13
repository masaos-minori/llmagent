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
| `is_processing` | `bool` | `False` | `handle_turn()`実行中は`True` |

### TurnState (`ctx.turn`)

ターンスコープ。ターン間でリセットされる。

| Field | Type | Initial | Description |
|---|---|---|---|
| `current_turn_id` | `str\|None` | `None` | ターン開始時にUUID4がセットされる; ターン間は`None` |
| `background_tasks` | `set[asyncio.Task[Any]]` | `set()` | このターン中に生成されたバックグラウンドタスク; クリーンシャットダウンのため追跡される |
| `last_error_kind` | `str\|None` | `None` | 直近のターン失敗時のエラー種別; 直近のターンが成功していれば`None` |
| `pending_approval_id` | `str\|None` | `None` | 直近のワークフローターンが人間の承認待ちで一時停止した際の承認ID |
| `pending_approval_task_id` | `str\|None` | `None` | `/approve`実行後に再開すべきタスクID; `/approve`コマンドがセットし、`Orchestrator.handle_turn()`がクリアする |

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
| `stat_partial_completions` | `int` | LLMの部分応答 (途中切断されたストリーミング応答) を受理した回数。初期値: `0`。 |

---

## AppServices (`ctx.services`)

`factory.build_agent_context()`が構築する、完全初期化済みのサービス参照の集合体。フィールドは`http`, `llm`, `tools`, `lifecycle`, `hist_mgr`, `audit_logger`, `memory`, `health_registry`, `gateway`。
`memory`は`use_memory_layer=False`の場合のみ意図的に`None`(未初期化ではなく明示的な不在)。
`gateway` (`RepositoryGateway`) は`factory.py`が構築してから注入されるまでの間は`None`。

`AppServices`はさらに以下のランタイム集計フィールドを持つ (`ctx.stats`とは別枠):

| Field | Type | Description |
|---|---|---|
| `serialization_events` | `int` | DAGツール実行のシリアル化イベント発生回数 |
| `serialization_tools_affected` | `int` | シリアル化の影響を受けたツール呼び出し数 |

### RepositoryGateway (`agent/repository_gateway.py`)

すべてのリポジトリ書込み/削除/API書込み操作の単一の強制境界。読み取り専用ツール呼び出しはノーチェックで`ToolExecutor`に直接転送される。書込み系操作は次の順で通過する: (1) ポリシー事前チェック (`tool_policy.check_preflight`)、(2) 承認プロンプト (`tool_approval.run_approval_checks`)、(3) `ToolExecutor`による実行、(4) 監査ログ出力。
ポリシー違反時は`PolicyViolationError`を捕捉し `is_error=True, error_type="denied"`の`ToolCallResult`を返す (例外を上位に伝播させない)。承認が拒否された場合も同様に`denied`扱いの結果を返す。

*(根拠分類: Explicit in code — `agent/repository_gateway.py`, `agent/context.py`)*

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
AppServices
RepositoryGateway
session persistence
