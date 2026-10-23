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
  - overview_02_files.md
  - agent_07_01_cli-and-commands-cli-reference.md
  - agent_10_01_operations-and-observability-startup-and-health.md
---

# Overview & Architecture

File Structure → [`overview_02_files.md`](overview_02_files.md)

## 2.4 Agent Features & Commands List

Details → [`agent_07_01_cli-and-commands-cli-reference.md`](../23_agent/agent_07_01_cli-and-commands-cli-reference.md)

## 2.5 Implemented Features Summary

- RAG Search (MQE + KNN + BM25 + RRF + Rerank + Refiner)
- MCP Tool Calling (HTTP)
- Memory Layer (semantic/episodic): long-term knowledge reused across sessions, independent of session lifecycle
- Session Persistence & Restoration: conversation history only; does not include memory
- Context Compression (LLM Summarization)
- SSE Streaming
- Slash Commands
- Tool Loop Guard (dedup/cycle/retry/error limits)
- Workflow Engine (plan/execute/verify)
- MDQ/RAG Query Routing
- Dependency Injection Hub (AgentContext)
- Diagnostic Store (turn/session statistics)

Refer to `overview_02_files.md` for the file structure.

### Implementation Notes

**Shared State and Dependency Injection**

`AgentContext` (`agent/context.py`) functions as the dependency injection hub for all services. Its state components are shared by the same instance across `AgentREPL`, `Orchestrator`, and each command handler. (Explicit in code — `agent/context.py`)

**Memory Layer Operating Modes**

`MemoryServices.get_activation_mode()` returns one of the following modes based on the startup state: `disabled` (disabled in config), `fts-only` (embedding disabled by `memory_embed_enabled=false`, or no embedding client exists), `degraded` (embedding circuit breaker open), or `hybrid` (normal operation). An individual retrieval whose embedding call fails falls back to FTS for that retrieval without being treated as an error. An unreachable embedding service at startup is not a mode: the startup readiness check fails with a FATAL error (see `agent_10_01_operations-and-observability-startup-and-health.md`). (Explicit in code — `agent/memory/services.py`)

**Tool Routing**

`RuntimeToolRegistry` (`shared/runtime_tool_registry.py`) holds sole routing authority. It is built from the live `/v1/tools` discovery at startup. The static registry (`tool_registry.py`) and the `tool_names` setting are used only for drift validation, never for routing. (Explicit in code — `shared/runtime_tool_registry.py`)

**Scope of sqlite-vec Extension Application**

`SQLiteHelper` in `db/helper.py` loads the `sqlite-vec` extension (`vec0.so`) by default only for the databases that own a vec0 table: `rag` (`chunks_vec`) and `session` (`memories_vec`). It is NOT applied to `workflow` or `eventbus` databases, and an explicit `load_vec` argument overrides the default. This intentional separation restricts vector operations to the two databases that own vector tables. (Explicit in code — `db/helper.py`)

**Diagnostic Storage upon Session Termination**

On every REPL exit path (normal exit, startup failure, startup interrupt, and input-loop error), session diagnostics and memory are persisted (`AgentREPL._persist_session_state`) and then the resource shutdown sequence runs (`ResourceShutdownCoordinator.close_resources`), persist first because it reads clients that shutdown releases. Persistence is gated on a session existing: when no session was started (for example on a startup failure) the persist step runs and writes nothing, by design. The following actions are performed:

1. **Save Session Diagnostics** — Saves turn count, tool call count, latency, and workflow statistics to `DiagnosticStore`; no row is written when no session was started.
2. **Persist Session Memory** — Extracts and persists memory from session history using rule-based logic; nothing is extracted or persisted when no session was started.
3. **WAL Checkpoint** — Executes a WAL checkpoint on `session.sqlite` before closing the connection: a PASSIVE checkpoint first, falling back to TRUNCATE (up to 3 attempts) when PASSIVE raises. A PASSIVE checkpoint that copies no frames over a non-empty WAL (a reader is holding it) and a TRUNCATE that stays blocked are recorded as shutdown errors. When the checkpoint does not succeed, a defensive backup of the WAL file via `WalCheckpointManager.backup_sync` is attempted; no exception is raised and the process terminates normally. Since SQLite will read existing WAL files upon the next startup, no data loss occurs. Note that if failures persist, attention should be paid to WAL file growth. (Explicit in code — `agent/wal_checkpoint_manager.py`, `agent/repl.py`)

Current-session counters can be viewed with the `/stats` command; the saved record is stored in the `session_diagnostics` table. (Explicit in code — `agent/repl.py`)

---

## Keywords

- feature-architecture
- implemented-features
- agent-context
- memory-layer
- tool-routing
- sqlite-vec
- diagnostic-store
