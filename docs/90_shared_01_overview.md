# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

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
- All modules under `shared/`: `config_loader`, `config_errors`, `config_validator`, `logger`, `types`, `llm_types`, `transport_dto`, `action_result`, `events`, `protocols/shell`, `tool_constants`, `route_resolver`, `mcp_config`, `mcp_health`, `tool_executor`, `http_transport`, `plugin_registry`, `plugin_auto_discover`, `plugin_result`, `otel_tracer`, `otel_noop`, `token_counter`, `token_estimation`, `git_helper`, `formatters`, `json_utils`, `llm_exceptions`, `llm_transport_errors`, `llm_sse_stream`, `llm_sse_helpers`, `llm_reconnect`, `llm_retry`, `llm_payload`, `llm_hot_config`, `sse_parser`, `tool_registry`, `tool_routing_validation`, `tool_transport_invoker`, `tool_lifecycle`, `tool_executor_helpers`, `tool_spec`, `tool_cache`, `plugin_tool_invoker`
- All modules under `db/`: `config.py`, `helper.py`, `create_schema.py`, `models.py`, `schema_sql.py`, `store.py`, `store_impl.py`, `store_protocols.py`, `maintenance.py`, `rotation.py`, `recovery.py`, `rag_consistency.py`
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
| `config_errors.py` | ConfigMissingError, ConfigParseError, ConfigReadError, ConfigPermissionError error classes |
| `config_validator.py` | RagConfigValidator (validate embedding_dim/vec_dim consistency, use_rrf warning, semantic_cache_threshold sanity) |
| `logger.py` | Named logger with FileHandler + StreamHandler |
| `types.py` | `LLMMessage` (TypedDict), `RagConfig` (Protocol) |
| `llm_types.py` | `LLMUsage`, `LLMResponse` frozen dataclasses |
| `transport_dto.py` | `ToolCallResult`, `TransportErrorInfo` dataclasses — MCP tool execution result and transport failure info |
| `action_result.py` | `ActionResult` frozen dataclass — machine decision schema |
| `events.py` | `ArtifactEvent`, `RetryEvent` TypedDicts |
| `protocols/shell.py` | `ShellPolicy` dataclass — shell execution policy |
| `tool_constants.py` | frozenset classification tables: `READ_TOOLS`, `WRITE_TOOLS`, etc. (registry seed only, not a routing input) |
| `route_resolver.py` | `ToolRouteResolver` — tool name → server key |
| `mcp_config.py` | `McpServerConfig`, re-exports McpServerHealthState/McpServerHealthRegistry from mcp_health.py |
| `mcp_health.py` | `McpServerHealthState` enum (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN), `McpServerHealthRegistry` — health tracking for dispatch gating |
| `tool_executor.py` | `ToolExecutor`, `HttpTransport` |
| `http_transport.py` | `TransportError`, `HttpTransport` — HTTP transport layer (calls /v1/call_tool) |
| `plugin_registry.py` | Dynamic plugin loading and tool/command registration |
| `plugin_auto_discover.py` | `load_plugins()` — import all *.py from plugin_dir with conflict validation |
| `plugin_result.py` | `PluginFailure`, `PluginLoadResult` dataclasses, `PluginLoadError` exception |
| `otel_tracer.py` | Private TracerProvider for OpenTelemetry |
| `otel_noop.py` | NoOpTracer and NoOpSpan stubs for disabled tracing |
| `token_counter.py` | Token count via `/tokenize` endpoint or chars//4 fallback |
| `token_estimation.py` | `estimate_tokens_for_text()`, `estimate_tokens_for_assistant_with_tool_calls()`, `estimate_tokens()` — category-aware token estimation |
| `git_helper.py` | Git repository info retrieval |
| `formatters.py` | Text truncation, key=value log strings, size formatting |
| `json_utils.py` | `dumps()` — orjson.dumps().decode() wrapper returning str |
| `llm_exceptions.py` | `LLMErrorKind` literal, `LLMTransportError` with kind/phase/url/status_code/retryable/partial_text/detail fields |
| `llm_transport_errors.py` | `LlmTransportErrorHandler` — raise_http_status_error, translate_stream_error |
| `llm_sse_stream.py` | `LlmSseStreamHandler` — read_next_chunk, stream_once |
| `llm_sse_helpers.py` | `LlmSseHelpers` — merge_tool_call_delta, build_stream_response |
| `llm_reconnect.py` | `LlmReconnectHandler` — resolve_retryable, stream |
| `llm_retry.py` | `LlmRetryHandler` — exponential-backoff retry for LLM HTTP requests |
| `llm_payload.py` | `LlmPayloadHandler` — build_payload, parse_response |
| `llm_hot_config.py` | `LlmHotConfigHandler` — hot-reloadable config fields |
| `sse_parser.py` | `RobustSSEParser` — stateful SSE parser with incremental UTF-8 decoder + heartbeat tracking + malformed frame budget |
| `tool_registry.py` | `ToolDefinition` dataclass, `ToolRegistry` class — central MCP tool registry and drift validation |
| `tool_routing_validation.py` | `validate_routing_against_config()`, `validate_routing_against_live()`, `validate_all_routing()` — drift validation functions |
| `tool_transport_invoker.py` | `ToolTransportInvoker` — transport layer MCP invocation (health, lifecycle, semaphore, call recording) |
| `tool_lifecycle.py` | `LifecycleProtocol` protocol for MCP server lifecycle managers |
| `tool_executor_helpers.py` | `is_side_effect()`, `format_transport_error()`, `tool_hash_key()` helper functions |
| `tool_spec.py` | `ToolSpec` dataclass — execution metadata for a single tool call (resource_scope, requires_serial, is_write) |
| `tool_cache.py` | `CacheEntry` dataclass, `ToolResultCache` — LRU cache with TTL for tool call results |
| `plugin_tool_invoker.py` | `PluginToolInvoker` — plugin tool execution layer |

---

## 6. Responsibilities of `db/`

| Module | Responsibility |
|---|---|
| `config.py` | `DbConfig` dataclass, `build_db_config()` — DB path resolution from config |
| `helper.py` | `SQLiteHelper` — connection lifecycle, WAL/PRAGMA, vec extension |
| `create_schema.py` | Schema DDL creation (idempotent via `IF NOT EXISTS`) |
| `models.py` | DTO dataclasses: `DocumentRow`, `MessageRow`, `SessionRow`, `DbHealthMetrics`, `PurgeCounts`, `RecoveryResult`, `WalCheckpointCounts` |
| `schema_sql.py` | DDL template strings (separation of SQL text from execution) |
| `store.py` | Re-export stub — delegates to `store_protocols.py` + `store_impl.py` |
| `store_protocols.py` | `VectorStore`, `DocumentStore`, `SessionStore`, `MemoryDeleteStore` Protocols + embedding helpers |
| `store_impl.py` | `SQLiteVectorStore`, `SQLiteDocumentStore`, `SQLiteSessionStore`, `SQLiteMemoryDeleteStore` implementations |
| `maintenance.py` | WAL checkpoint, VACUUM, session purge, memory prune |
| `rotation.py` | DB rotation (archive current DB, create new one) — `rotate_all_dbs()` function |
| `recovery.py` | Corruption recovery (integrity check + VACUUM or restore from backup) |
| `rag_consistency.py` | Read-only RAG consistency checks (chunks/FTS/vec row counts + orphan detection) — `check_rag_consistency()`, `is_consistent()`, `summarize_issues()` |

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
| `session.sqlite` | `sessions`, `messages`, `memories`, `memories_fts`, `memories_vec`, `memory_links` | Agent conversation state + memory layer |
| `workflow.sqlite` | `tasks`, `attempts`, `processed_events`, `approvals`, `artifacts` | Workflow engine task tracking |

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
| `agent.toml` | See [90_shared_03](90_shared_03_runtime_and_execution.md) §2a Config Ownership for full ownership table |
| Embedding dimension | `embedding_dims` in `agent.toml` (default 384) |

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
| What types/DTOs are defined in shared/? | [90_shared_02_types_and_protocols.md](90_shared_02_types_and_protocols.md) |
| How does ConfigLoader work? | [90_shared_03_runtime_and_execution.md](90_shared_03_runtime_and_execution.md) |
| What SQLite schemas exist? | [90_shared_04_db_architecture_and_schema.md](90_shared_04_db_architecture_and_schema.md) |
| What is the SQLiteHelper API? | [90_shared_05_db_api_and_operations.md](90_shared_05_db_api_and_operations.md) |
| What bugs or inconsistencies exist? | [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) |
