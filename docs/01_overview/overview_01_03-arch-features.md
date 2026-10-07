---
title: "Feature Architecture"
area: overview
tags:
  - feature-architecture
  - implemented-features
  - agent-context
  - memory-layer
  - tool-routing
  - sqlite-vec
  - diagnostic-store
related:
  - overview_01_01-arch-process.md
  - overview_01_02-arch-pipelines.md
---

# Overview & Architecture

File Structure → [`overview_02_files.md`](overview_02_files.md)

## 2.4 Agent Features & Commands List

Details → [`agent_07_01_cli-and-commands-cli-reference.md`](../23_agent/agent_07_01_cli-and-commands-cli-reference.md)

## 2.5 Implemented Features Summary

- RAG Search (MQE + KNN + BM25 + RRF + Rerank + Refiner)
- MCP Tool Calling (HTTP)
- Memory Layer (semantic/episodic)
- Session Persistence & Restoration
- Context Compression (LLM Summarization)
- Tool Result Cache (standalone, not used by ToolExecutor)
- SSE Streaming
- Slash Commands
- Tool Loop Guard (dedup/cycle/retry/error limits)
- Workflow Engine (plan/execute/approval/verify)
- MDQ/RAG Query Routing
- Dependency Injection Hub (AgentContext)
- Diagnostic Store (turn/session statistics)

Refer to `overview_02_files.md` for the file structure.

### Implementation Notes

**Shared State and Dependency Injection**

`AgentContext` (`agent/context.py`) functions as the dependency injection hub for all services. It composes `ConversationState`, `TurnState`, `RuntimeStats`, `WorkflowState`, and `AppServices`, which are all referenced by the same instance across `AgentREPL`, `Orchestrator`, and each command handler. (Source: `agent/context.py`)

**Memory Layer Operating Modes**

`MemoryServices.get_activation_mode()` returns one of the following modes based on the startup state: `disabled` (disabled in config), `fts-only` (embedding server unavailable), `degraded` (embedding circuit breaker open), or `hybrid` (normal operation). If semantic search is unavailable, it falls back to FTS only without treating it as an error. (Source: `agent/memory/services.py`)

**Tool Routing**

`RuntimeToolRegistry` (`shared/runtime_tool_registry.py`) holds sole routing authority. It is built from the live `/v1/tools` discovery at startup. The static registry (`tool_registry.py`) and the `tool_names` setting are used only for drift validation, never for routing. (Source: `shared/runtime_tool_registry.py`)

**Scope of sqlite-vec Extension Application**

`SQLiteHelper` in `db/helper.py` loads the `sqlite-vec` extension (`vec0.so`) only when `target="rag"`. It is NOT applied to `session`, `workflow`, or `eventbus` databases. This intentional separation restricts vector operations to the RAG database. (Source: `db/helper.py`)

**Diagnostic Storage upon Session Termination**

After the REPL input loop ends, session diagnostics and memory are persisted (`AgentREPL._persist_after_loop`) and then the resource shutdown sequence runs (`ResourceShutdownCoordinator.close_resources`). The following actions are performed:

1. **Save Session Diagnostics** — Saves turn count, tool call count, latency, and workflow statistics to `DiagnosticStore`.
2. **Persist Session Memory** — Extracts and persists memory from session history using rule-based logic.
3. **WAL Truncate Checkpoint** — Executes a WAL TRUNCATE checkpoint on `session.sqlite` before closing the connection. If the checkpoint fails, a defensive backup of the WAL file via `WalCheckpointManager.backup_sync` is attempted; however, no exception is raised and the process terminates normally. Since SQLite will read existing WAL files upon the next startup, no data loss occurs. Note that if failures persist, attention should be paid to WAL file growth. (Source: `agent/wal_checkpoint_manager.py`, `agent/repl.py`)

Current-session counters can be viewed with the `/stats` command; the saved record is stored in the `session_diagnostics` table. (Source: `agent/repl.py`)

---

## Keywords

feature-architecture
implemented-features
agent-context
memory-layer
tool-routing
sqlite-vec
diagnostic-store
