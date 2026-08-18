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

## Purpose

エージェントレイヤーが使用する4つのSQLiteデータベースの所有関係と責務境界について文書化する。

## Design Intent

### プラットフォームデータベースの所有関係

エージェントレイヤーは4つのSQLiteデータベースにまたがって動作する（`db/helper.py`の`DbTarget` enum: `RAG`, `SESSION`, `WORKFLOW`, `EVENTBUS`）：

| Database | Purpose | Schema reference |
|---|---|---|
| `session.sqlite` | エージェントセッション、メッセージ、メモリ | `90_shared_04` §2 |
| `rag.sqlite` | RAGドキュメント、チャンク、埋め込み | `90_shared_04` §3-§6 |
| `workflow.sqlite` | タスク追跡、イベント処理 | `90_shared_04` §7 |
| `eventbus.sqlite` | イベントバス（本ドキュメントの対象外） | — |

DBパスは`agent.toml`内の`rag_db_path`, `session_db_path`, `workflow_db_path`, `eventbus_db_path`で設定される（`db/config.py`）。`rag_db_path`/`session_db_path`はデフォルト値なし（未設定なら`ValueError`）、`workflow_db_path`/`eventbus_db_path`は`/opt/llm/db/`配下のデフォルトパスを持つ。

**DBの所有関係：**

| Database | Owner module | Key class |
|---|---|---|
| `session.sqlite` | `agent/session.py` | `AgentSession` |
| `session.sqlite`（メモリ） | `agent/memory/store.py` | `MemoryStore` |
| `workflow.sqlite` | `agent/workflow/state_store.py` | `StateStore` |
| `rag.sqlite` | `scripts/mcp_servers/rag_pipeline/` | RAG MCPサーバー |

> **Note:** メモリレイヤー（`agent/memory/store.py`の`MemoryStore`）は`SQLiteHelper("session")`を使い、session.sqliteの`memories`/`memories_fts`/`memories_vec`テーブルに永続化する。rag.sqliteとは別であり、RAGドキュメント/チャンクの埋め込みストアとは独立している。`agent/memory/jsonl_store.py`の`JsonlMemoryStore`はこれとは別に、非正本の追記専用JSONLファイルへメモリをアーカイブする（バックアップ/監査用途）。読み出しは `read_all()` / `read_active()` で可能。

### Session / RAG責務境界

`AgentSession`はRAGレイヤーのインポートやメソッドを一切持たない。すべてのRAGドキュメント操作（取り込み、検索、チャンク管理）はRAG MCPパスを経由する。RAGメンテナンス操作は`RagMaintenanceService`を経由する — セッションオブジェクトを経由することはない。

### サービス責務境界

| Service | Defined in | DB | Methods |
|---|---|---|---|
| `DbMaintenanceService` | `agent/services/db_maintenance_service.py` | session.sqlite | `stats` (sessions/messages), `health`, `checkpoint`, `vacuum`, `purge`, `recover_session` |
| `RagMaintenanceService` | `agent/services/rag_maintenance_service.py` | rag.sqlite | `stats_rag` (docs/chunks), `rebuild_fts`, `consistency`, `recover`, `rebuild_vec`, `reconcile_url` |

両サービスクラスは`db/maintenance.py`の低レベル関数（`checkpoint_wal`, `vacuum_db`, `purge_old_sessions`など）を呼び出すラッパーであり、`db/maintenance.py`自体にはこれらのクラスは定義されていない。CLIサブコマンド名`/db session recover`と実装メソッド名`recover_session`は非対称だが対応関係は一致している。

`AgentSession`は`SQLiteHelper("session")`経由でsession.sqliteのみにアクセスする。

検証済みの境界：

- `agent/session.py`がインポートするのは以下：`agent.diagnostic_store`（`DiagnosticStore`）、`agent.session_message_repo`（`SessionMessageRepository`）、`db.helper`（`SQLiteHelper`）、`shared.types`。診断ログ（`session_diagnostics`）の保存は`DiagnosticStore`が担う
- `db/maintenance.py`にはメンテナンス関数（`vacuum_db`, `checkpoint_wal`, `prune_old_memories`など）が含まれるが、`rag/`モジュールのインポートは一切ない; DBローテーションは`db/rotation.py`にある
- `/db`コマンドはスコープによりサブコマンドをルーティングする：`/db rag <subcmd>`は`RagMaintenanceService`を対象とし、`/db session <subcmd>`は`DbMaintenanceService`を対象とする
- `db/maintenance.py`の`prune_old_memories()`は`DbMaintenanceService`/`RagMaintenanceService`いずれの管轄でもなく、`agent/commands/memory_data_ops.py`から`/memory`系コマンド経由で直接呼び出される
- `agent/repository_gateway.py`はDB永続化とは無関係で、ツール呼び出し（write/delete/API-write）のポリシー審査・実行・監査を行う実行ゲート層である。承認プロンプトは発行しない（`tool_runner.execute_all_tool_calls()`のバッチレベルゲートが呼び出し前に一度だけ強制する）。DB責務境界には関与しない

## Responsibility Boundary

### StateStoreの責任範囲

`StateStore`は`workflow.sqlite`のタスク/試行/承認/成果物の管理を担う。詳細なメソッド一覧は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### タスクCRUD操作

`task_ops.py`はワークフロー状態のCRUD操作を提供する。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### 試行操作

`attempt_ops.py`は試行レコードの管理を提供する。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### 承認操作

`approval_ops.py`は事後実行承認の管理を提供する。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### 成果物操作

`artifact_ops.py`は成果物への参照記録を提供する。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

### 冪等性操作

`idempotency_ops.py`はイベントの処理済みチェックとアトミックな試行開始を提供する。詳細は[05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)を参照。

## Key Constraints

### DB間の直接操作禁止

各データベースは所有モジュールのみがアクセスする必要がある。他のDBへの直接操作は禁止。

### メモリDBとRAG DBの分離

メモリレイヤーはsession.sqliteを使用し、rag.sqliteとは独立している。

## Operational Notes

- `/db session`スコープはsession.sqliteのメンテナンスを扱う。`/db`はworkflow.sqliteを直接メンテナンス対象として公開していない — ワークフロー状態は`WorkflowEngine`経由の`StateStore`のみによって管理される。
- `request_approval`の`workflow_id`引数は`approvals`テーブルに格納され、クエリ結果で返されるが、現在のコードベースではフィルタリングやルーティングには使用されていない（単なる追跡用）。
- `finish_attempt`の`error_kind`/`error_detail`は`attempts`テーブルの追加カラムで、`error_msg`とは別にエラー分類情報を保持する。
- `begin_stage_if_new`はevent_idをアトミックにチェックし、新規であれば試行を開始する。`begin_immediate`でチェックと挿入を単一トランザクションにまとめ、明示的な`commit()`は呼ばない。

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_04_01_state-and-persistence-state-model.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`

## Keywords

platform databases
StateStore methods
task/attempt/approval/artifact operations
session/RAG responsibility boundary
