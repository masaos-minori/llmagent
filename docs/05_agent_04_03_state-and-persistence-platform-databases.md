---
title: "Agent State and Persistence - Platform Databases"
area: agent
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

# Agent State and Persistence - Platform Databases

- Runtime Architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- Turn Flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- Data Layer (Schema) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## Purpose

To document the ownership relationships and responsibility boundaries of the four SQLite databases used by the Agent layer.

## Design Intent

### Platform Database Ownership

The Agent layer operates across four SQLite databases (`DbTarget` enum in `db/helper.py`: `RAG`, `SESSION`, `WORKFLOW`, `EVENTBUS`):

| Database | Purpose | Schema reference |
|---|---|---|
| `session.sqlite` | Agent sessions, messages, memory | `90_shared_04` section 2 |
| `rag.sqlite` | RAG documents, chunks, embeddings | `90_shared_04` sections 3-6 |
| `workflow.sqlite` | Task tracking, event processing | `90_shared_04` section 7 |
| `eventbus.sqlite` | Event Bus (out of scope for this document) | — |

DB paths are configured in `agent.toml` via `rag_db_path`, `session_db_path`, `workflow_db_path`, and `eventbus_db_path` (`db/config.py`). `rag_db_path`/`session_db_path` have no default values (raises `ValueError` if not set), while `workflow_db_path`/`eventbus_db_path` have default paths under `/opt/llm/db/`.

**DB Ownership:**

| Database | Owner module | Key class |
|---|---|---|
| `session.sqlite` | `agent/session.py` | `AgentSession` |
| `session.sqlite` (Memory) | `agent/memory/store.py` | `MemoryStore` |
| `workflow.sqlite` | `agent/workflow/state_store.py` | `StateStore` |
| `rag.sqlite` | `scripts/mcp_servers/rag_pipeline/` | RAG MCP Server |

> **Note:** The Memory layer (`MemoryStore` in `agent/memory/store.py`) uses `SQLiteHelper("session")` and persists to `memories`/`memories_fts`/`memories_vec` tables in `session.sqlite`. It is separate from `rag.sqlite` and independent from the RAG document/chunk embedding store. `JsonlMemoryStore` in `agent/memory/jsonl_store.py` separately archives memory to a non-authoritative append-only JSONL file (for backup/audit purposes). `read_all()` returns all entries regardless of retention policy; `read_active()` filters by retention policy.

### Session / RAG Responsibility Boundaries

`AgentSession` does not import any modules or methods from the RAG layer. All RAG document operations (ingestion, search, chunk management) are performed via the RAG MCP path. RAG maintenance operations are performed via `RagMaintenanceService` — they do not go through the session object.

### Service Responsibility Boundaries

| Service | Defined in | DB | Methods |
|---|---|---|---|
| `DbMaintenanceService` | `agent/services/db_maintenance_service.py` | session.sqlite | `stats` (sessions/messages), `health`, `checkpoint`, `vacuum`, `purge`, `recover_session` |
| `RagMaintenanceService` | `agent/services/rag_maintenance_service.py` | rag.sqlite | `stats_rag` (docs/chunks), `rebuild_fts`, `consistency`, `recover`, `rebuild_vec`, `reconcile_url` |

Both service classes are wrappers that call low-level functions in `db/maintenance.py` (`checkpoint_wal`, `vacuum_db`, `purge_old_sessions`, etc.), but these classes themselves are not defined in `db/maintenance.py`. While CLI subcommand names like `/db session recover` and implementation method names like `recover_session` are asymmetrical, they correspond correctly.

`AgentSession` accesses only `session.sqlite` via `SQLiteHelper("session")`.

Verified Boundaries:

- `agent/session.py` imports: `agent.diagnostic_store` (`DiagnosticStore`), `agent.session_message_repo` (`SessionMessageRepository`), `db.helper` (`SQLiteHelper`), and `shared.types`. Diagnostic logs (`session_diagnostics`) are handled by `DiagnosticStore`.
- `db/maintenance.py` contains maintenance functions (`vacuum_db`, `checkpoint_wal`, `prune_old_memories`, etc.) but has no imports from `rag/`; DB rotation is located in `db/rotation.py`.
- The `/db` command routes subcommands based on scope: `/db rag <subcmd>` targets `RagMaintenanceService`, while `/db session <subcmd>` targets `DbMaintenanceService`.
- `db/maintenance.py`'s `prune_old_memories()` is not under the jurisdiction of either `DbMaintenanceService` or `RagMaintenanceService`; it is called directly from `agent/commands/memory_data_ops.py` via `/memory` type commands.
- `agent/repository_gateway.py` is unrelated to DB persistence; it acts as an execution gate for policy review, execution, and auditing of tool calls (it does not issue approval prompts; the batch-level gate in `tool_runner.execute_all_tool_calls()` is enforced once before invocation). It is not involved in DB responsibility boundaries.

## Responsibility Boundary

### StateStore Responsibility Scope

`StateStore` manages tasks/attempts/approvals/artifacts in `workflow.sqlite`. See [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) for detailed method lists.

### Task CRUD Operations

`task_ops.py` provides CRUD operations for workflow states. See [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) for details.

### Attempt Operations

`attempt_ops.py` provides management for attempt records. See [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) for details.

### Approval Operations

`approval_ops.py` provides management for post-execution approvals. See [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) for details.

### Artifact Operations

`artifact_ops.py` provides recording of artifact references. See [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) for details.

### Idempotency Operations

`idempotency_ops.py` provides duplicate detection and atomic attempt initiation. See [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) for details.

## Key Constraints

### Prohibition of Direct Cross-DB Operations

Each database must only be accessed by its owner module. Direct access to other databases is prohibited.

### Separation of Memory DB and RAG DB

The Memory layer uses `session.sqlite` and is independent of `rag.sqlite`.

## Operational Notes

- The `/db session` scope handles `session.sqlite` maintenance. The `/db` command does not expose `workflow.sqlite` directly for maintenance — workflow states are managed exclusively via `StateStore` through the `WorkflowEngine`.
- The `request_approval` `workflow_id` argument is stored in the `approvals` table and returned in query results, but currently, it is not used for filtering or routing in the codebase.
- `finish_attempt`'s `error_kind`/`error_detail` are additional columns in the `attempts` table, providing error classification separate from `error_msg`.
- `begin_stage_if_new` checks the `event_id` atomically and starts an attempt if new. `begin_immediate` wraps check and insertion in a single transaction without calling `commit()` explicitly.

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_04_01_state-and-persistence-state-model.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`

## Keywords

platform databases
StateStore methods
task/attempt/approval/artifact operations