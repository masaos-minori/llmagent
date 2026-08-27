---
title: "Shared Infrastructure File Structure: venv/db/ + scripts/db/ (Part 1/2)"
category: overview
tags:
  - shared
  - db
  - sqlite
  - file-structure
related:
  - 01_overview-files-04-shared.md

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. File Structure

Directory structure at deployment target:

``` text
/opt/llm/
├─ venv/                              # Python virtual environment
│   └─ uv.lock                        # Python dependency list (uv managed)
├─ db/
│   ├─ rag.sqlite                     # RAG vector DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 sections 3-6
│   ├─ session.sqlite                 # Agent sessions + messages — see 90_shared_04 section 2
│   └─ workflow.sqlite                # Task tracking + event processing — see 90_shared_04 section 7
│   # 3-DB split is designed to avoid SQLite lock contention between data with different write frequencies (RAG: only during ingestion, Session: every turn, Workflow: at each event). Each DB operates in WAL mode. See commits `73bd9bb08` / `fa703f346` for details.
├─ scripts/
│   ├─ db/                                  # DB layer package (see directory for detailed file structure)
│   │   ├─ __init__.py                      # Module initialization
│   │   ├─ create_schema.py                 # SQLite schema initialization
│   │   ├─ schema_sql.py                    # build_rag_schema_sql / build_session_schema_sql / build_workflow_schema_sql
│   │   ├─ helper.py                        # Connection management (WAL / busy_timeout)
│   │   ├─ maintenance.py                   # Operational policies
│   │   ├─ config.py                        # DbConfig dataclass / SQLite path builder
│   │   ├─ models.py                        # WalCheckpointCounts / PurgeCounts / DbHealthMetrics / DocumentRow / SessionRow / MessageRow
│   │   ├─ store.py                         # Protocol abstraction layer
│   │   ├─ store_protocols.py               # VectorStore / DocumentStore / SessionStore Protocol definitions
│   │   ├─ store_impl.py                    # SQLiteVectorStore / SQLiteDocumentStore / SQLiteSessionStore implementations
│   │   ├─ rag_consistency.py               # RAG index consistency check
│   │   ├─ rotation.py                      # Database rotation
│   │   └─ recovery.py                      # Corrupted DB recovery
```

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3a. File Structure

Directory structure at deployment target:

``` text
/opt/llm/
├─ venv/                              # Python virtual environment
│   └─ uv.lock                        # Python dependency list (uv managed)
├─ db/
│   ├─ rag.sqlite                     # RAG vector DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 sections 3-6
│   ├─ session.sqlite                 # Agent sessions + messages — see 90_shared_04 section 2
│   └─ workflow.sqlite                # Task tracking + event processing — see 90_shared_04 section 7
│   # 3-DB split is designed to avoid SQLite lock contention between data with different write frequencies (RAG: only during ingestion, Session: every turn, Workflow: at each event). Each DB operates in WAL mode. See commits `73bd9bb08` / `fa703f346` for details.
├─ scripts/
│   ├─ db/                                  # DB layer package (see directory for detailed file structure)
│   │   ├─ __init__.py                      # Module initialization
│   │   ├─ create_schema.py                 # SQLite schema initialization
│   │   ├─ schema_sql.py                    # build_rag_schema_sql / build_session_schema_sql / build_workflow_schema_sql
│   │   ├─ helper.py                        # Connection management (WAL / busy_timeout)
│   │   ├─ maintenance.py                   # Operational policies
│   │   ├─ config.py                        # DbConfig dataclass / SQLite path builder
│   │   ├─ models.py                        # WalCheckpointCounts / PurgeCounts / DbHealthMetrics / DocumentRow / SessionRow / MessageRow
│   │   ├─ store.py                         # Protocol abstraction layer
│   │   ├─ store_protocols.py               # VectorStore / DocumentStore / SessionStore Protocol definitions
│   │   ├─ store_impl.py                    # SQLiteVectorStore / SQLiteDocumentStore / SQLiteSessionStore implementations
│   │   ├─ rag_consistency.py               # RAG index consistency check
│   │   ├─ rotation.py                      # Database rotation
│   │   └─ recovery.py                      # Corrupted DB recovery
```

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3b. File Structure

Treating `scripts/shared/` as the source of truth. Below is a loosely grouped list of files by theme.

**LLM Client/Transport**
- `llm_client.py` — LLMClient: SSE streaming & exponential backoff retry
- `llm_types.py` — LLMUsage / LLMResponse dataclasses
- `llm_exceptions.py` — Error type definitions
- `llm_transport_errors.py` — LlmTransportErrorHandler
- `llm_sse_stream.py` — LlmSseStreamHandler
- `llm_sse_helpers.py` — LlmSseHelpers
- `llm_reconnect.py` — LlmReconnectHandler
- `llm_hot_config.py` — Hot-reloadable configuration fields
- `llm_retry.py` — Exponential backoff request retries
- `llm_payload.py` — LlmPayloadHandler
- `sse_parser.py` — RobustSSEParser

**Tool Routing/Execution**
- `tool_executor.py` — ToolExecutor: MCP server routing
- `tool_executor_helpers.py` — Tool execution helper functions
- `tool_transport_invoker.py` — ToolTransportInvoker: MCP calls (health/lifecycle/semaphore/call logging)
- `tool_registry.py` — ToolDefinition / ToolRegistry classes
- `tool_spec.py` — ToolSpec: tool call execution metadata
- `tool_cache.py` — ToolResultCache: LRU cache + TTL (standalone utility, not integrated into ToolExecutor)
- `tool_lifecycle.py` — LifecycleProtocol: MCP server lifecycle protocol
- `tool_routing_validation.py` — Drift validation functions
- `tool_constants.py` — Tool classification frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
- `route_resolver.py` — ToolRouteResolver: tool name → server key mapping
- `runtime_tool.py` — RuntimeTool: frozen dataclass of normalized runtime tool metadata (name, server_key, description, input_schema, is_write, agent_safety_tier etc.) and `build_runtime_tool()` constructor
- `runtime_tool_registry.py` — RuntimeToolRegistry: In-memory `{name: RuntimeTool}` registry built upon startup by `McpToolDiscoveryService.discover_all()`. The sole authority for routing referenced by `ToolRouteResolver.resolve()` (no fallback to `tool_registry.ToolRegistry`)

**Configuration**
- `config_loader.py` — Common TOML/JSON configuration loader
- `config_utils.py` — Typed configuration value accessors (e.g., `get_str()`) — reads validated values from raw dicts derived from TOML/JSON
- `config_errors.py` — Config error types
- `config_validator.py` — RagConfigValidator
- `production_config_validator.py` — Production-specific configuration validation
- `mcp_config.py` — McpServerConfig and other configuration dataclasses
- `mcp_health.py` — McpServerHealthState / McpServerHealthRegistry — health tracking for dispatch gates

**Other Utilities**
- `types.py` — Common type definitions
- `db_maintenance.py` — count_table(): common helper for counting table rows
- `action_result.py` — ActionResult dataclass
- `events.py` — ArtifactEvent / RetryEvent TypedDict
- `transport_dto.py` — ToolCallResult / TransportErrorInfo dataclasses
- `formatters.py` — Common output formatter for all MCP servers
- `git_helper.py` — get_repo_info(): retrieves branch/commit info using GitPython
- `http_transport.py` — HTTP transport layer
- `json_utils.py` — JSON utilities
- `logger.py` — Logging configuration
- `otel_noop.py` — OpenTelemetry no-op implementation
- `otel_tracer.py` — OpenTelemetry tracing
- `token_counter.py` — Token counter
- `token_estimation.py` — Token estimation
- `__init__.py` — shared package initialization

**`protocols/`**
- `protocols/__init__.py` — Protocol package initialization
- `protocols/shell.py` — ShellPolicy protocol

### Design Intent and Operational Specifications

#### Control via Caching and Health Checks

`tool_cache.py`'s `ToolResultCache` is a standalone LRU+TTL cache utility, not currently used anywhere in the codebase. Health checks using `mcp_health.py` enable dispatch control based on server status (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN).

#### Behavior of Drift Validation
The behavior of routing drift detection is as follows:
- **Config Drift**: By default, it only issues warnings, but if `routing_drift_strict` is enabled, it raises a `RuntimeError` and stops startup.
- **Live Drift**: By default, it only issues warnings, but if `tool_definitions_strict` is enabled or `security_profile == PRODUCTION`, it becomes `FATAL` and stops startup.
- **Ownership Duplication**: If multiple servers claim the same tool name, it always results in `FATAL`, regardless of the mode.

## Related Documents

- `01_overview-files-04-shared.md`
- [01_overview.md](01_overview.md)

## Keywords

shared
db
sqlite
file-structure
