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
  - 01_overview-arch-01-process.md
  - 01_overview-arch-02-pipelines.md
  - [01_overview.md](01_overview.md)
---

# Overview & Architecture

File Structure → [`01_overview-files-01-build.md`](01_overview-files-01-build.md), [`01_overview-files-02-rag.md`](01_overview-files-02-rag.md), [`01_overview-files-03-scripts.md`](01_overview-files-03-scripts.md), [`01_overview-files-04-shared.md`](01_overview-files-04-shared.md), [`01_overview-files-05-config.md`](01_overview-files-05-config.md), [`01_overview-files-06-misc.md`](01_overview-files-06-misc.md)

## 2.4 Agent Features & Commands List

Details → [`05_agent_07_01_cli-and-commands-cli-reference.md`](05_agent_07_01_cli-and-commands-cli-reference.md)

## 2.5 Implemented Features Summary

| Feature | Implementation Location |
|---|---|
| RAG Search (MQE + KNN + BM25 + RRF + Rerank + Refiner) | `scripts/rag/` |
| MCP Tool Calling (HTTP, 11 servers) | `scripts/agent/`, `scripts/shared/` |
| Memory Layer (semantic/episodic) | `scripts/agent/memory/` |
| Session Persistence & Restoration | `scripts/agent/`, `scripts/db/` |
| Context Compression (LLM Summarization) | `scripts/agent/` |
| Tool Result Cache (standalone, not used by ToolExecutor) | `scripts/shared/` |
| SSE Streaming | `scripts/shared/` |
| Slash Commands | `scripts/agent/commands/` |
| Tool Loop Guard (dedup/cycle/retry/error limits) | `scripts/agent/` |
| Workflow Engine (plan/execute/approval/verify) | `scripts/agent/workflow/` |
| MDQ/RAG Query Routing | `scripts/agent/` |
| Dependency Injection Hub (AgentContext) | `scripts/agent/` |
| Diagnostic Store (turn/session statistics) | `scripts/agent/` |

Refer to the `01_overview-files-03-scripts-part*.md` series for detailed file structure.

### Implementation Notes

**Shared State and Dependency Injection**

`AgentContext` (`agent/context.py`) functions as the dependency injection hub for all services. It composes `ConversationState`, `TurnState`, `RuntimeStats`, `WorkflowState`, and `AppServices`, which are all referenced by the same instance across `AgentREPL`, `Orchestrator`, and each command handler. (Source: `agent/context.py`)

**Memory Layer Operating Modes**

`MemoryServices.get_activation_mode()` returns one of four modes based on the startup state: `disabled` (disabled in config), `fts-only` (embedding server unavailable), `degraded` (embedding circuit breaker open), or `hybrid` (normal operation). If semantic search is unavailable, it falls back to FTS only without treating it as an error. (Source: `agent/memory/services.py`)

**Tool Routing**

`RuntimeToolRegistry` (`shared/route_resolver.py`) holds sole routing authority. The live discovery map from `/v1/tools` at startup is used exclusively for validation and not for routing. Additionally, the static registry (`tool_registry.py`) is currently not used for routing. The `tool_names` setting is used only for drift validation. (Source: `shared/route_resolver.py`)

**Scope of sqlite-vec Extension Application**

`SQLiteHelper` in `db/helper.py` loads the `sqlite-vec` extension (`vec0.so`) only when `target="rag"`. It is NOT applied to `session`, `workflow`, or `eventbus` databases. This intentional separation restricts vector operations to the RAG database. (Source: `db/helper.py`)

**Diagnostic Storage upon Session Termination**

In the `finally` block of the REPL loop, the following actions are performed:

1. **Save Session Diagnostics** — Saves turn count, tool call count, latency, and workflow statistics to `DiagnosticStore`.
2. **Persist Session Memory** — Extracts and persists memory from session history using rule-based logic.
3. **WAL Truncate Checkpoint** — Executes a WAL TRUNCATE checkpoint on `session.sqlite` before closing the connection. If the checkpoint fails, a defensive backup of the WAL file via `_wal_backup_sync` is attempted; however, no exception is raised and the process terminates normally. Since SQLite will read existing WAL files upon the next startup, no data loss occurs. Note that if failures persist, attention should be paid to WAL file growth. (Source: `agent/repl.py`)

Diagnostics can be viewed using the `/db` command. (Source: `agent/repl.py`)

---

## Related Documents

- `01_overview-arch-01-process.md`
- `01_overview-arch-02-pipelines.md`
- [01_overview.md](01_overview.md)

## Keywords

feature-architecture
implemented-features
agent-context
memory-layer
tool-routing
sqlite-vec
diagnostic-store
