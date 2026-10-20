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

`StateStore` manages tasks, attempts, artifact references, and idempotency (duplicate detection and atomic attempt initiation) in `workflow.sqlite`, through the operation modules under `agent/workflow/`. See [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md).

## Key Constraints

### Prohibition of Direct Cross-DB Operations

Each database must only be accessed by its owner module. Direct access to other databases is prohibited.

### Separation of Memory DB and RAG DB

The Memory layer uses `session.sqlite` and is independent of `rag.sqlite`.

## Operational Notes

- The `/session` maintenance subcommands handle `session.sqlite` maintenance. No slash command exposes `workflow.sqlite` directly for maintenance — workflow states are managed exclusively via `StateStore` through the `WorkflowEngine`.
- `begin_stage_if_new` checks the `event_id` and starts an attempt atomically (check and insertion in a single transaction), so a stage is not started twice.

## Keywords

- platform databases
- StateStore methods
- task/attempt/approval/artifact operations
