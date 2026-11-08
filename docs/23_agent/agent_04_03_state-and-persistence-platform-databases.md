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
  - agent_00_document-guide.md
  - agent_04_01_state-and-persistence-state-model.md
  - agent_04_02_state-and-persistence-history-compression.md
  - agent_02_runtime-architecture.md
  - agent_03_01_turn-processing-flow-overview.md
  - agent_09_01_data-layer-session-db.md
  - db_02_architecture_and_schema-schema-reference.md
  - db_03_07_mcp-dedup-and-execution-snapshot.md
---

# Agent State and Persistence - Platform Databases

- Runtime Architecture → [agent_02_runtime-architecture.md](agent_02_runtime-architecture.md)
- Turn Flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
- Data Layer (Schema) → [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md)

## Purpose

To document the ownership relationships and responsibility boundaries of the four SQLite databases used by the Agent layer.

## Design Intent

### Platform Database Ownership

The Agent layer operates across four SQLite databases (see `DbTarget` in `scripts/db/helper.py`):

| Database | Purpose | Schema reference |
|---|---|---|
| `session.sqlite` | Agent sessions, messages, memory | [db_02](../41_db/db_02_architecture_and_schema-schema-reference.md) section 6 |
| `rag.sqlite` | RAG documents, chunks, embeddings | [db_02](../41_db/db_02_architecture_and_schema-schema-reference.md) section 5 |
| `workflow.sqlite` | Task tracking, event processing | [db_02](../41_db/db_02_architecture_and_schema-schema-reference.md) section 7 |
| `eventbus.sqlite` | Event Bus (out of scope for this document) | — |

DB paths are configured in `agent.toml` (schema: `scripts/db/config.py`). The RAG and session paths have no defaults and startup fails if they are unset; the workflow and eventbus paths have built-in defaults.

**DB Ownership:** `session.sqlite` is owned by `AgentSession` (`agent/session.py`) and, for memory tables, `MemoryStore` (`agent/memory/store.py`); `workflow.sqlite` by `StateStore` (`agent/workflow/state_store.py`); `rag.sqlite` by the RAG MCP server (`scripts/mcp_servers/rag_pipeline/`).

> **Note:** The Memory layer (`MemoryStore` in `agent/memory/store.py`) uses `SQLiteHelper("session")` and persists to `memories`/`memories_fts`/`memories_vec` tables in `session.sqlite`. It is separate from `rag.sqlite` and independent from the RAG document/chunk embedding store. `JsonlMemoryStore` in `agent/memory/jsonl_store.py` separately archives memory to a non-authoritative append-only JSONL file (for backup/audit purposes). `read_all()` returns all entries; no retention filtering is applied at this layer.

**Logical ownership inside `session.sqlite`:** the file is shared physically, but the tables have separate logical owners. `AgentSession` owns `sessions`, `messages`, and `session_diagnostics`; `MemoryStore` owns `memories`, `memories_fts`, `memories_vec`, and `memory_links`. Session operations never write the memory tables, and memory operations never write the session tables. `memories.session_id` is provenance only (no foreign key), so deleting a session leaves its memories in place. There is no session-scoped memory deletion API: memory rows are removed only by `/memory delete` and `/memory prune`.

### Session / RAG Responsibility Boundaries

`AgentSession` does not import any modules or methods from the RAG layer. All RAG document operations (ingestion, search, chunk management) are performed via the RAG MCP path. RAG maintenance operations are performed via `RagMaintenanceService` — they do not go through the session object.

### Service Responsibility Boundaries

Maintenance is split by database: `DbMaintenanceService` (`agent/services/db_maintenance_service.py`) covers `session.sqlite` (stats, health, checkpoint, vacuum, purge, session recovery) and `RagMaintenanceService` (`agent/services/rag_maintenance_service.py`) covers `rag.sqlite` (RAG stats, FTS/vector rebuild, consistency, recovery). Both are thin wrappers over `db/maintenance.py`.

Boundaries:

- `AgentSession` accesses only `session.sqlite` and imports nothing from the RAG layer. Diagnostic logs (`session_diagnostics`) are written by `DiagnosticStore`.
- `db/maintenance.py` has no imports from `rag/`; DB rotation is in `db/rotation.py`.
- `/session stats|health|checkpoint|vacuum|purge|recover` target `DbMaintenanceService`; `/session rag-consistency|rag-rebuild-fts|rag-rebuild-vec` target `RagMaintenanceService`.
- `prune_old_memories()` belongs to neither service; it is called from the `/memory` commands.
- `agent/repository_gateway.py` is a tool-call execution gate and is not part of DB responsibility boundaries.

## Responsibility Boundary

### StateStore Responsibility Scope

`StateStore` manages tasks, attempts, artifact references, stage-level idempotency (duplicate-event detection and atomic attempt initiation), and the tool-call lifecycle (the `tool_call_state` table, written through `agent/workflow/tool_call_state_ops.py`) in `workflow.sqlite`, through the operation modules under `agent/workflow/`. Each task row's `task_nonce` (new) is a globally unique identifier (UUID4) generated by `create_task()` and is not derived from the session or turn number. Task identity is `task_id` across a retained database; a duplicate `create_task()` call with identical arguments is a new task — task-request deduplication does not exist — and stage re-execution is prevented by the `processed_events` event key, not by the nonce. Do not conflate the two kinds of keys in this database: the task `task_nonce` (new) is a random task-scoped identifier, while `tool_call_state.idempotency_key` is the content-derived transport dedup key (sha256 of method/tool/args/session uid) with the owning `task_id` appended, so two tasks making an identical call keep separate lifecycle rows; the wire `X-Idempotency-Key` sent to the dispatcher remains the raw content-derived key. See [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md).

### Workflow Lifecycle Tables (toolexec001)

| Table | Responsibility |
|---|---|
| `tool_call_state` | Agent-side lifecycle of each dispatched tool call (`pending` / `completed` / `failed` / `interrupted`), keyed by the composed state key (the transport idempotency key with `task_id` appended), which enforces per-task separation of identical calls; stale `pending` rows past `dedup.pending_timeout_minutes` are transitioned to `interrupted` and surfaced to the next LLM turn as a control message. |

The former `execution_snapshots` table is retired: no code path ever wrote it, fresh databases no longer create it or the `tool_call_state.snapshot_id` foreign key, and a legacy database may still carry the empty table and a NULL column with no effect.

Full column contract, migration path (`workflow.sqlite` ledger `1 -> 2`), and the replay
decision table: [db_03_07](../41_db/db_03_07_mcp-dedup-and-execution-snapshot.md). Producer
wiring on the agent executor path is tracked by follow-up issue
`issues/20261031-175803_toolstate001_tool-call-state-producer.md`.

## Key Constraints

### Prohibition of Direct Cross-DB Operations

Each database must only be accessed by its owner module. Direct access to other databases is prohibited.

### Separation of Memory DB and RAG DB

The Memory layer uses `session.sqlite` and is independent of `rag.sqlite`.

## Operational Notes

- The `/session` maintenance subcommands handle `session.sqlite` maintenance. No slash command exposes `workflow.sqlite` directly for maintenance — workflow states are managed exclusively via `StateStore` through the `WorkflowEngine`.
- A new session against a retained `workflow.sqlite` always receives a fresh `task_id` and a fresh, unique `task_nonce` (new); nothing needs deleting before the new run.
- `begin_stage_if_new` checks the `event_id` and starts an attempt atomically (check and insertion in a single transaction), so a stage is not started twice.
- Startup stale-attempt recovery reconciles task status: after `recover_stale_attempts()` fails lease-expired attempts (and prunes their `processed_events` rows), every task that is still `running` with no remaining live attempt is written to `failed` in the same transaction. `RecoveryReport` counts this as `tasks_reconciled` (new) alongside `recovered` and `still_live`; `halted` and `completed` tasks are never reconciled, and the resume halt-guard semantics are unchanged (recovery narrative: [db_07 section 9.7](../41_db/db_07_api_and_operations-recovery-and-reference.md)).

## Keywords

- platform databases
- StateStore methods
- task/attempt/approval/artifact operations
