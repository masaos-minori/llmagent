---
title: "Agent State and Persistence"
category: agent
tags:
  - agent
  - agent
  - state
  - persistence
  - session
  - history
related:
  - 05_agent_00_document-guide.md
---

# Agent State and Persistence

nt layer operates across three SQLite databases:

| Database | Purpose | Schema reference |
|---|---|---|
| `session.sqlite` | Agent sessions, messages | `90_shared_04` §2 |
| `rag.sqlite` | RAG documents, chunks, embeddings | `90_shared_04` §3-§6 |
| `workflow.sqlite` | Task tracking, event processing | `90_shared_04` §7 |

DB paths are configured via `rag_db_path`, `session_db_path`, `workflow_db_path` in `agent.toml`. Full schema details: `90_shared_04_db_architecture_and_schema.md`.

**DB ownership:**

| Database | Owner module | Key class |
|---|---|---|
| `session.sqlite` | `agent/session.py` | `AgentSession` |
| `workflow.sqlite` | `agent/workflow/state_store.py` | `StateStore` |
| `rag.sqlite` | `scripts/mcp/rag_pipeline/` | RAG MCP server |

> **Note:** The `/db session` scope covers session.sqlite maintenance. `/db` does not expose workflow.sqlite for direct maintenance — workflow state is managed exclusively by `StateStore` via `WorkflowEngine`.

### StateStore methods (`agent/workflow/state_store.py`)

| Method | Description |
|---|---|
| `create_task(session_id, turn_number, workflow_version, workflow_id)` | Create a new task record; returns `TaskRecord` |
| `update_task_status(task_id, status)` | Update task status (pending/running/pending_approval/completed/failed/halted) |
| `get_task_by_id(task_id)` | Return the task record for the given task_id, or None if absent |
| `get_task_by_idempotency_key(key)` | Return the task record for the given idempotency key, or None |
| `get_task_by_session(session_id)` | Return all tasks for a session ordered by created_at ascending |
| `get_latest_task(session_id)` | Return the most recently created task for a session |
| `list_tasks(limit=50)` | Return up to `limit` tasks ordered by created_at descending |
| `start_attempt(task_id, stage_id)` | Start a new attempt record; returns `AttemptRecord` |
| `finish_attempt(attempt_id, status, error_msg)` | Complete an attempt with status and optional error message |
| `count_attempts(task_id, stage_id)` | Return count of attempts for a task+stage combination |

### Task CRUD operations (`agent/workflow/task_ops.py`)

| Function | Description |
|---|---|
| `create_task(db, session_id, turn_number, workflow_version, workflow_id)` | Create a new task record; returns `TaskRecord` |
| `update_task_status(db, task_id, status)` | Update task status (pending/running/pending_approval/completed/failed/halted) |
| `get_task_by_id(db, task_id)` | Return the task record for the given task_id, or None if absent |
| `get_task_by_idempotency_key(db, key)` | Return the task record for the given idempotency key, or None |
| `get_task_by_session(db, session_id)` | Return all tasks for a session ordered by created_at ascending |
| `get_latest_task(db, session_id)` | Return the most recently created task for a session |
| `list_tasks(db, limit=50)` | Return up to `limit` tasks ordered by created_at descending |

### Attempt operations (`agent/workflow/attempt_ops.py`)

| Function | Description |
|---|---|
| `start_attempt(db, task_id, stage_id)` | Start a new attempt record; returns `AttemptRecord` |
| `finish_attempt(db, attempt_id, status, error_msg)` | Complete an attempt with status and optional error message |
| `count_attempts(db, task_id, stage_id)` | Return count of attempts for a task+stage combination |

### Approval operations (`agent/workflow/approval_ops.py`)

| Function | Description |
|---|---|
| `request_approval(db, task_id, stage_id)` | Insert a pending approval gate for a task (or specific stage); returns `ApprovalRecord` |
| `resolve_approval(db, approval_id, status, reason)` | Set approval status to 'approved' or 'rejected' |
| `get_pending_approval(db, task_id)` | Return the most recent approval record for a task, or None if absent |
| `find_pending_approval_by_session(db, session_id)` | Return (task_id, approval) for the most recent pending-approval task in this session, or None |
| `find_latest_pending_approval(db)` | Return (task_id, approval) for the most recent globally pending approval, or None |

### Artifact operations (`agent/workflow/artifact_ops.py`)

| Function | Description |
|---|---|
| `record_artifact(db, task_id, stage_id, uri)` | Record an artifact reference; returns `ArtifactRef` |

### Idempotency operations (`agent/workflow/idempotency_ops.py`)

| Function | Description |
|---|---|
| `is_event_processed(db, event_id)` | Check if an event has already been processed (idempotency guard) |
| `begin_stage_if_new(db, event_id, task_id, stage_id)` | Atomically check event_id and start attempt if new; returns `AttemptRecord` if the stage should run, None if already processed |



---

## Session / RAG Responsibilit

y Boundary

`AgentSession` (`agent/session.py`) has zero RAG-layer imports or methods.
All RAG document operations (ingest, search, chunk management) go through the
RAG MCP path; RAG maintenance operations go through `RagMaintenanceService` —
never through the session object.

### Service responsibility boundary

| Service | DB | Methods |
|---|---|---|
| `DbMaintenanceService` | session.sqlite | `stats` (sessions/messages), `health`, `checkpoint`, `vacuum`, `purge`, `recover_session` |
| `RagMaintenanceService` | rag.sqlite | `stats_rag` (docs/chunks), `rebuild_fts`, `consistency`, `recover`, `rebuild_vec`, `reconcile_url` |

`AgentSession` accesses only session.sqlite via `SQLiteHelper("session")`.

Verified boundaries:
- `agent/session.py` imports only: `db.helper`, `shared.types`, `agent.session_message_repo`
- `db/maintenance.py` contains maintenance functions (`vacuum_db`, `checkpoint_wal`, etc.) but has zero `rag/` module imports; DB rotation is in `db/rotation.py`
- `/db` command routes subcommands by scope: `/db rag <subcmd>` targets `RagMaintenanceService`; `/db session <subcmd>` targets `DbMaintenanceService`

## Related Documents

- `agent`
- `state`
- `persistence`

## Keywords

agent
state
persistence
session
history
