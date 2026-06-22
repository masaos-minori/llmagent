# Shared and DB Layer Overview

- Document guide → [06_shared_00_document-guide.md](06_shared_00_document-guide.md)

## 1. Purpose

This document provides the high-level overview of the `shared/` and `db/` layers:
their purpose, scope, dependency relationships, import constraints, and the overall
picture of persistent data.

**Key points:**
- `shared/` provides cross-cutting infrastructure: config loading, logging, types, tool routing, plugins, OTel, and DTOs
- `db/` provides persistent storage: SQLite connection management, schema creation, store protocols, and maintenance
- Both are bottom-layer dependencies used by all other layers (`agent/`, `mcp/`, `rag/`)

---

## 2. Scope

**In scope:**
- All modules under `shared/`: `config_loader`, `logger`, `types`, `llm_types`, `tool_constants`, `route_resolver`, `mcp_config`, `tool_executor`, `plugin_registry`, `otel_tracer`, `token_counter`, `git_helper`, `formatters`, `action_result`, `events`, `protocols/shell`
- All modules under `db/`: `config.py`, `helper.py`, `create_schema.py`, `models.py`, `schema_sql.py`, `store.py`, `store_impl.py`, `store_protocols.py`, `maintenance.py`, `tool_results.py`, `workflow_schema.py`
- DB files: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`

**Out of scope:**
- MCP server implementations (`mcp/`)
- RAG pipeline logic (`rag/`)
- Agent REPL (`agent/`)
- LLM and embedding servers (external processes)

---

## 3. Out of Scope

- Distributed or replicated SQLite configurations
- External vector databases (only in-process sqlite-vec)
- LLM communication protocol details (covered in `05_agent_05_llm-and-streaming.md`)

---

## 4. Overall Layer Structure

```
External Libraries
        ↑
   shared/          ← bottom layer; all other layers depend on this
        ↑
       db/           ← depends on shared/ only
        ↑
  rag/ | mcp/        ← depend on db/ and shared/
        ↑
    agent/           ← depends on all layers
```

Import direction is enforced by `.importlinter`. Violations fail `lint-imports`.

---

## 5. Responsibilities of `shared/`

| Module | Responsibility |
|---|---|
| `config_loader.py` | TOML/JSON file loading and merging |
| `logger.py` | Named logger with FileHandler + StreamHandler |
| `types.py` | `LLMMessage` (TypedDict), `RagConfig` (Protocol) |
| `llm_types.py` | `LLMUsage`, `LLMResponse` frozen dataclasses |
| `action_result.py` | `ActionResult` frozen dataclass — machine decision schema |
| `events.py` | `ArtifactEvent` TypedDict — repository artifact notifications |
| `protocols/shell.py` | `ShellPolicy` dataclass — shell execution policy |
| `tool_constants.py` | frozenset routing tables: `READ_TOOLS`, `WRITE_TOOLS`, etc. |
| `route_resolver.py` | `ToolRouteResolver` — tool name → server key |
| `mcp_config.py` | `McpServerConfig`, `McpServerHealthRegistry` |
| `tool_executor.py` | `ToolExecutor`, `HttpTransport`, `StdioTransport` |
| `plugin_registry.py` | Dynamic plugin loading and tool/command registration |
| `otel_tracer.py` | Private TracerProvider for OpenTelemetry |
| `token_counter.py` | Token count via `/tokenize` endpoint or chars//4 fallback |
| `git_helper.py` | Git repository info retrieval |
| `formatters.py` | Text truncation, key=value log strings, size formatting |

---

## 6. Responsibilities of `db/`

| Module | Responsibility |
|---|---|
| `config.py` | `DbConfig` dataclass, `build_db_config()` — DB path resolution from config |
| `helper.py` | `SQLiteHelper` — connection lifecycle, WAL/PRAGMA, vec extension |
| `create_schema.py` | Schema DDL creation (idempotent via `IF NOT EXISTS`) |
| `models.py` | DTO dataclasses: `DocumentRow`, `MessageRow`, `SessionRow`, `ToolResultRow`, `DbHealthMetrics`, `PurgeCounts`, `RecoveryResult`, `WalCheckpointCounts` |
| `schema_sql.py` | DDL template strings (separation of SQL text from execution) |
| `store.py` | Re-export stub — delegates to `store_protocols.py` + `store_impl.py` |
| `store_protocols.py` | `VectorStore`, `DocumentStore`, `SessionStore`, `MemoryDeleteStore` Protocols + embedding helpers |
| `store_impl.py` | `SQLiteVectorStore`, `SQLiteDocumentStore`, `SQLiteSessionStore`, `SQLiteMemoryDeleteStore` implementations |
| `maintenance.py` | WAL checkpoint, VACUUM, session purge, memory prune, DB rotate, corruption recovery |
| `tool_results.py` | `ToolResultStore` — full tool result text storage |
| `workflow_schema.py` | `workflow.sqlite` DDL initialization |

---

## 7. Import Direction Constraints

**Rule:** `shared/` → external libraries only. Import from `agent/`, `mcp/`, `rag/`, `db/` is **prohibited**.

**Rule:** `db/` → `shared/` only. Import from `agent/`, `mcp/`, `rag/` is **prohibited**.

Enforced by `.importlinter` (fails `PYTHONPATH=scripts uv run lint-imports`).

Key constraint: `orjson.dumps()` returns `bytes`, not `str`. Always call `.decode()` when a `str` is required. Use `httpx.AsyncClient` (not `requests`) for async HTTP.

---

## 8. Overall Picture of Persistent Data

| DB File | Tables | Purpose |
|---|---|---|
| `rag.sqlite` | `documents`, `chunks`, `chunks_fts`, `chunks_vec` | RAG document index + vector + FTS search |
| `session.sqlite` | `sessions`, `messages`, `notes`, `tool_results`, `memories`, `memories_fts`, `memories_vec`, `memory_links` | Agent conversation state + memory layer |
| `workflow.sqlite` | `tasks`, `attempts`, `processed_events`, `artifacts` | Workflow engine task tracking |

All three DBs use WAL mode and `busy_timeout`. sqlite-vec is loaded only for `rag.sqlite` (target=`"rag"`).

---

## 9. Major Constraints

| Constraint | Value |
|---|---|
| Import direction | `shared/` → external only; `db/` → `shared/` only |
| JSON library | `orjson` (not stdlib `json`); `orjson.dumps()` returns `bytes` |
| HTTP client | `httpx` (not `requests`); `httpx.AsyncClient` for async |
| Config format | TOML / JSON in `/opt/llm/config/`; `_`-prefixed keys are excluded |
| Log messages | English only (no Japanese in code comments or logs) |
| SQLite WAL | All connections use `PRAGMA journal_mode=WAL` |
| `common.toml` | See [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership for full ownership table |
| Embedding dimension | `embedding_dims` in `common.toml` (default 384) |

---

## 10. Executive Summary

`shared/` is the lowest dependency layer. It provides config, logging, types, routing,
plugin support, and DTOs. No code in `shared/` may import from upper layers.

`db/` provides typed, WAL-enabled SQLite access with FTS5 and sqlite-vec integration.
It is the canonical source for schema definitions. `db/` depends on `shared/` only.

All persistent data lives in three SQLite files: `rag.sqlite` (RAG index), `session.sqlite`
(conversation + memory), and `workflow.sqlite` (task tracking).

---

## 11. AI Reference Guide

| Question | Look in |
|---|---|
| What types/DTOs are defined in shared/? | [06_shared_02_types_and_protocols.md](06_shared_02_types_and_protocols.md) |
| How does ConfigLoader work? | [06_shared_03_runtime_and_execution.md](06_shared_03_runtime_and_execution.md) |
| What SQLite schemas exist? | [06_shared_04_db_architecture_and_schema.md](06_shared_04_db_architecture_and_schema.md) |
| What is the SQLiteHelper API? | [06_shared_05_db_api_and_operations.md](06_shared_05_db_api_and_operations.md) |
| What bugs or inconsistencies exist? | [06_shared_90_inconsistencies_and_known_issues.md](06_shared_90_inconsistencies_and_known_issues.md) |
