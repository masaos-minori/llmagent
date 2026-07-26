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

#### 検証付き履歴変更メソッド

`ConversationState`は`history`への生の`list.append()`/`list.extend()`/直接代入の代わりに、
`agent/message_schema.py::validate_message()`経由で検証を強制する3つのメソッドを持つ
(`agent/context.py`):

| Method | Description |
|---|---|
| `append_message(msg, *, source="")` | `msg`を検証してから`history`へ追加する。検証失敗時は`ROLE_KEY_WHITELIST`/`TRUSTED_SOURCES`に基づき不正なキーを除去 (`warning`ログ) してから追加する。除去後に`role`または`content`が欠落する場合はメッセージ全体を破棄する (`error`ログ、`history`には追加しない) |
| `extend_messages(msgs, *, source="")` | `msgs`の各メッセージに対して`append_message()`を個別に呼び出す。1件の不正なメッセージが他の正常なメッセージに影響することはない |
| `replace_history(msgs, *, source="")` | `history`を空にしてから`extend_messages(msgs, source=source)`を呼ぶ |

`source`は検証時にのみ使用されるメタデータで、信頼済みソース (`TRUSTED_SOURCES`: `cmd_handler`,
`memory_injection`, `skill_mixin`) からのエフェメラルキー (`_ephemeral`, `_memory_injected`,
`_skill_ephemeral`) を許可するために検証用の一時的なコピーにのみ付与される。`source`自体が
`history`に保存されたメッセージやLLMへのペイロードに含まれることはない。

呼び出し元の例: `Orchestrator._handle_memory_injection()`は`source="memory_injection"`付きで
`append_message()`を、`Orchestrator._append_user_message()`は`source`なしで`append_message()`を
それぞれ呼ぶ (`agent/orchestrator.py`)。`Orchestrator._sync_system_prompt()`の
`history.insert(0, ...)`分岐は位置指定挿入のため`append_message()`は使わず、同じ
`validate_message()`を直接呼んで検証してから挿入する。詳細は
[05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
を参照。`LLMTurnRunner.run()`のツール呼び出し分岐と`_finalize_answer_text()`も、どちらも`source`
なしで`append_message()`を呼ぶ (`agent/llm_turn_runner.py`)。詳細は
[05_agent_03_02_turn-processing-flow-llm-tool-loop.md](05_agent_03_02_turn-processing-flow-llm-tool-loop.md)
§履歴への追加 を参照。

`replace_history()`は`history`全体の一括置き換えを行う2箇所の呼び出し元でも使われる:
`StartupOrchestrator._setup_prompt()`は起動時の初期`history`(システムプロンプト1件のみ)を
`source`なしで`replace_history([...])`により構築し (`agent/startup.py`)、
`session_restore.restore_session()`はセッション復元時に`ctx.session.fetch_messages()`が返した
永続化済みメッセージ列を、同じく`source`なしで`replace_history(...)`により`history`へ反映する
(`agent/services/session_restore.py`)。いずれも通常運用下では既存の`ROLE_KEY_WHITELIST`を
満たす整形済みメッセージのみを扱うため検証は常に成功し保存内容は変化しないが、
`restore_session()`側は改ざん・破損したDB行が予約済みエフェメラルキーを持ち込むケースに対する
多層防御として`replace_history()`を経由する。当該行はサニタイズまたは破棄されるため
`SessionRestoreResult.n_messages`(元の取得件数)が実際の保存件数をわずかに上回りうる
(まれなケースであり許容されている)。

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

すべてのリポジトリ書込み/削除/API書込み操作の単一の強制境界。読み取り専用ツール呼び出しはノーチェックで`ToolExecutor`に直接転送される。書込み系操作は次の順で通過する: (1) ポリシー事前チェック (`tool_policy.check_preflight`)、(2) `ToolExecutor`による実行、(3) 監査ログ出力。
承認プロンプトは`RepositoryGateway`自身では発行しない — `tool_runner.execute_all_tool_calls()`のバッチレベルゲート (`_run_approval_gate()`、内部で`tool_approval.run_approval_checks`を呼ぶ) が、書込み/リスクのあるツール呼び出しを`RepositoryGateway.execute()`に到達させる前に一度だけ承認を強制する、という前提(precondition)の上に成り立つ。この前提を経由しない直接呼び出しは、非対話的な`check_preflight()`以外の承認チェックを受けない。
ポリシー違反時は`PolicyViolationError`を捕捉し `is_error=True, error_type="denied"`の`ToolCallResult`を返す (例外を上位に伝播させない)。承認が拒否された場合の`denied`扱いの結果は、上流の`tool_runner`バッチゲートが返す。

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
append_message
extend_messages
replace_history
validate_message
TurnState
WorkflowState
RuntimeStats
AppServices
RepositoryGateway
session persistence
StartupOrchestrator._setup_prompt
session_restore.restore_session
bulk history replacement defense-in-depth
