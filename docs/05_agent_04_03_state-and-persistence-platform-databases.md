---
title: "Agent State and Persistence - Platform Databases"
category: agent
tags:
  - agent
  - state
  - persistence
  - platform-databases
  - workflow-sqlite
related:
  - 05_agent_00_document-guide.md
  - 05_agent_04_01_state-and-persistence-state-model.md
  - 05_agent_04_02_state-and-persistence-history-compression.md
source:
  - 05_agent_04_01_state-and-persistence-state-model.md
---

# エージェントの状態と永続化

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- データレイヤー (スキーマ) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## プラットフォームデータベース

エージェントレイヤーは3つのSQLiteデータベースにまたがって動作する:

| Database | Purpose | Schema reference |
|---|---|---|
| `session.sqlite` | エージェントセッション、メッセージ | `90_shared_04` §2 |
| `rag.sqlite` | RAGドキュメント、チャンク、埋め込み | `90_shared_04` §3-§6 |
| `workflow.sqlite` | タスク追跡、イベント処理 | `90_shared_04` §7 |

DBパスは`agent.toml`内の`rag_db_path`, `session_db_path`, `workflow_db_path`で設定される。スキーマの詳細全体: `90_shared_04_db_architecture_and_schema.md`。

**DBの所有関係:**

| Database | Owner module | Key class |
|---|---|---|
| `session.sqlite` | `agent/session.py` | `AgentSession` |
| `workflow.sqlite` | `agent/workflow/state_store.py` | `StateStore` |
| `rag.sqlite` | `scripts/mcp/rag_pipeline/` | RAG MCPサーバー |

> **Note:** `/db session`スコープはsession.sqliteのメンテナンスを扱う。`/db`はworkflow.sqliteを直接メンテナンス対象として公開していない — ワークフロー状態は`WorkflowEngine`経由の`StateStore`のみによって管理される。

### StateStoreのメソッド (`agent/workflow/state_store.py`)

| Method | Description |
|---|---|
| `create_task(session_id, turn_number, workflow_version, workflow_id)` | 新規タスクレコードを作成; `TaskRecord`を返す |
| `update_task_status(task_id, status)` | タスクステータスを更新 (pending/running/pending_approval/completed/failed/halted) |
| `get_task_by_id(task_id)` | 指定したtask_idのタスクレコードを返す。存在しなければNone |
| `get_task_by_idempotency_key(key)` | 指定した冪等性キーのタスクレコードを返す。なければNone |
| `get_task_by_session(session_id)` | セッションに属する全タスクをcreated_at昇順で返す |
| `get_latest_task(session_id)` | セッションで最も新しく作成されたタスクを返す |
| `list_tasks(limit=50)` | created_at降順で最大`limit`件のタスクを返す |
| `start_attempt(task_id, stage_id)` | 新規試行レコードを開始; `AttemptRecord`を返す |
| `finish_attempt(attempt_id, status, error_msg)` | 試行をステータスと任意のエラーメッセージで完了させる |
| `count_attempts(task_id, stage_id)` | タスク+ステージの組み合わせの試行回数を返す |

### タスクCRUD操作 (`agent/workflow/task_ops.py`)

| Function | Description |
|---|---|
| `create_task(db, session_id, turn_number, workflow_version, workflow_id)` | 新規タスクレコードを作成; `TaskRecord`を返す |
| `update_task_status(db, task_id, status)` | タスクステータスを更新 (pending/running/pending_approval/completed/failed/halted) |
| `get_task_by_id(db, task_id)` | 指定したtask_idのタスクレコードを返す。存在しなければNone |
| `get_task_by_idempotency_key(db, key)` | 指定した冪等性キーのタスクレコードを返す。なければNone |
| `get_task_by_session(db, session_id)` | セッションに属する全タスクをcreated_at昇順で返す |
| `get_latest_task(db, session_id)` | セッションで最も新しく作成されたタスクを返す |
| `list_tasks(db, limit=50)` | created_at降順で最大`limit`件のタスクを返す |

### 試行操作 (`agent/workflow/attempt_ops.py`)

| Function | Description |
|---|---|
| `start_attempt(db, task_id, stage_id)` | 新規試行レコードを開始; `AttemptRecord`を返す |
| `finish_attempt(db, attempt_id, status, error_msg)` | 試行をステータスと任意のエラーメッセージで完了させる |
| `count_attempts(db, task_id, stage_id)` | タスク+ステージの組み合わせの試行回数を返す |

### 承認操作 (`agent/workflow/approval_ops.py`)

| Function | Description |
|---|---|
| `request_approval(db, task_id, stage_id)` | タスク (または特定のステージ) に対する承認待ちゲートを挿入; `ApprovalRecord`を返す |
| `resolve_approval(db, approval_id, status, reason)` | 承認ステータスを'approved'または'rejected'に設定する |
| `get_pending_approval(db, task_id)` | タスクの最新の承認レコードを返す。存在しなければNone |
| `find_pending_approval_by_session(db, session_id)` | このセッション内で最も新しい承認待ちタスクの(task_id, approval)を返す。なければNone |
| `find_latest_pending_approval(db)` | グローバルで最も新しい承認待ちの(task_id, approval)を返す。なければNone |

### 成果物操作 (`agent/workflow/artifact_ops.py`)

| Function | Description |
|---|---|
| `record_artifact(db, task_id, stage_id, uri)` | 成果物への参照を記録する; `ArtifactRef`を返す |

### 冪等性操作 (`agent/workflow/idempotency_ops.py`)

| Function | Description |
|---|---|
| `is_event_processed(db, event_id)` | イベントが既に処理済みかをチェックする (冪等性ガード) |
| `begin_stage_if_new(db, event_id, task_id, stage_id)` | event_idをアトミックにチェックし、新規であれば試行を開始する; ステージを実行すべき場合は`AttemptRecord`を、既に処理済みの場合はNoneを返す |



---

## Session / RAG責務境界

`AgentSession` (`agent/session.py`) はRAGレイヤーのインポートやメソッドを一切持たない。
すべてのRAGドキュメント操作 (取り込み、検索、チャンク管理) はRAG MCPパスを経由する;
RAGメンテナンス操作は`RagMaintenanceService`を経由する —
セッションオブジェクトを経由することはない。

### サービス責務境界

| Service | DB | Methods |
|---|---|---|
| `DbMaintenanceService` | session.sqlite | `stats` (sessions/messages), `health`, `checkpoint`, `vacuum`, `purge`, `recover_session` |
| `RagMaintenanceService` | rag.sqlite | `stats_rag` (docs/chunks), `rebuild_fts`, `consistency`, `recover`, `rebuild_vec`, `reconcile_url` |

`AgentSession`は`SQLiteHelper("session")`経由でsession.sqliteのみにアクセスする。

検証済みの境界:
- `agent/session.py`がインポートするのは以下のみ: `db.helper`, `shared.types`, `agent.session_message_repo`
- `db/maintenance.py`にはメンテナンス関数 (`vacuum_db`, `checkpoint_wal`など) が含まれるが、`rag/`モジュールのインポートは一切ない; DBローテーションは`db/rotation.py`にある
- `/db`コマンドはスコープによりサブコマンドをルーティングする: `/db rag <subcmd>`は`RagMaintenanceService`を対象とし、`/db session <subcmd>`は`DbMaintenanceService`を対象とする

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_04_01_state-and-persistence-state-model.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`

## Keywords

platform databases
StateStore methods
task/attempt/approval/artifact operations
session/RAG responsibility boundary
