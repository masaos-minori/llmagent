# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

## 9. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**Responsibility:** Core engine for tool dispatching — handles tool $\rightarrow$ server resolution, caching, concurrency limits, health gating, and transport communication.

**`ToolCallResult` Data Class (Result Contract, `shared/transport_dto.py`, frozen dataclass):** A frozen dataclass containing `output` (truncated if $> \text{MCP\_MAX\_RESPONSE\_BYTES}$), `is_error`, `request_id` (X-Request-Id from MCP server, empty for cache hits), `server_key` (routing target), `source` ('mcp'/'cache'/empty), and `error_type` ('transport'/'tool'/empty). `error_type` is used by the health gate and error counter aggregation.

**Execution Flow:** Resolve `tool_name` $\rightarrow$ `server_key` via `ToolRouteResolver`; `startup_mode=none` gate rejects disabled servers; `McpServerHealthRegistry.is_unavailable()` blocks `UNAVAILABLE` dispatch (`HALF_OPEN` allows one attempt per cooldown); `lifecycle.ensure_ready()` if configured; execute via `HttpTransport.call()` behind a per-server-key semaphore; return `ToolCallResult`.

**Caching Behavior:** Removed (see REQ-002).

**Health Gate:** `McpServerHealthRegistry.is_unavailable()` blocks dispatch when `UNAVAILABLE`; consecutive transport failures transition state from `HEALTHY` $\rightarrow$ `DEGRADED` $\rightarrow$ `UNAVAILABLE` (once `failure_threshold` reaches `UNAVAILABLE`); a success response resets state to `HEALTHY` (clears failure count/degraded reason). `HALF_OPEN` exists as an experimental circuit-breaker recovery mechanism: after `half_open_cooldown_sec` in `UNAVAILABLE` state, one dispatch attempt is allowed; a failure during `HALF_OPEN` immediately returns to `UNAVAILABLE`; `record_degraded()` does not override `UNAVAILABLE`/`HALF_OPEN` states.

**Concurrency Behavior:** `concurrency_limits` maps `server_key` $\rightarrow$ max concurrent calls; semaphore-based throttling in `ToolTransportInvoker`; tool-call-batch parallel/serial scheduling is unified under a single path — `agent/tool_runner.py::_execute_with_dag()`, which delegates to `agent/tool_scheduler.py::build_execution_groups()`. The former non-DAG path (`_execute_standard()`) has been removed; `ctx.cfg.tool.serial_tool_calls=True` now feeds `force_serial=True` into the scheduler instead of selecting a different execution engine.

**Side-Effect Detection:** `build_execution_groups()` reads each call's `is_write` from `PreparedToolCall.spec` (resolved once during `agent/tool_preparation.py::prepare_tool_calls()`, sourced from `RuntimeToolRegistry.tool_spec_for_call()`) — an unregistered tool is rejected fail-closed during preparation and never reaches scheduling, so no conservative "assume True" fallback remains. `_SIDE_EFFECT_TOOLS`/`is_side_effect()` (`tool_executor_helpers.py`) is deprecated (no longer used after TTL cache removal). See [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md) for the scheduler's grouping rules.

**Routing (Explicit in code):** `shared/runtime_tool_registry.py`'s `RuntimeToolRegistry` is the sole routing authority. `ToolRouteResolver.resolve()` (`shared/route_resolver.py`) refers only to `RuntimeToolRegistry.resolve()`, and unknown tools result in an immediate `ValueError`. `shared/tool_registry.py`'s `ToolRegistry` is no longer used for routing decisions; it has been downgraded to seed data for startup drift validation (`shared/tool_routing_validation.py`). Configuration file `tool_names` is metadata for drift validation only and is not used for runtime routing decisions. The old "two-stage cascade" method (live discovery $\rightarrow$ registry resolution) no longer exists in the current codebase. For detailed routing info, see [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md).

---

## 10. `LLMClient` (`shared/llm_client.py`)

**Responsibility:** An HTTP client for LLM API communication featuring retry logic, SSE streaming, and error handling.

**Primary APIs:** `LLMClient` wraps `AsyncClient` with retry logic, SSE streaming, and error handling. Constructor accepts http client, `max_retries`, `retry_base_delay`, `temperature`, `max_tokens`, optional callbacks (`on_token`/`on_usage`), and SSE parameters (`sse_heartbeat_timeout=30`, `sse_malformed_retry=2`, `sse_reconnect_max=1`, `llm_stream_retry_on_heartbeat_timeout=True`, `llm_stream_retry_on_malformed_chunk=False`). `call()`/`stream()` accept `url`/`history`/`tool_defs`; `build_payload` constructs the request dict.

**Error Behavior:** HTTP errors $\rightarrow$ `LLMTransportError` classified by kind: `HTTP_STATUS_RETRYABLE` (429/503), `HTTP_STATUS_FATAL` (others), `CONNECT_ERROR`, `READ_TIMEOUT`, `HEARTBEAT_TIMEOUT`, `MALFORMED_SSE_FRAME`, `UTF8_PARTIAL_DECODE_ERROR`, `PREMATURE_EOF`, `UNKNOWN_STREAM_ERROR`. SSE heartbeat timeouts trigger retries if enabled; malformed chunks are retried up to `sse_malformed_retry` times before raising `MALFORMED_SSE_FRAME`. Retry exhaustion raises `LLMTransportError` with `partial_text` containing accumulated output.

**Retries:** Exponential backoff starting from `retry_base_delay`; limit `max_retries` for non-streaming requests; streaming reconnection uses a separate counter `sse_reconnect_max`.

**Statistics (Instance-level):** Instance-level stats include `stat_retries`, `stat_reconnects`, `stat_heartbeat_timeouts`, and `stat_parse_errors`. Note: `stat_partial_completions` does not exist; `LlmReconnectHandler.stream()` returns `partial_completions` as a tuple element, but `LLMClient.stream()` discards it without accumulation.

**Configuration:** `LlmHotConfigHandler` applies hot reloads for: `temperature`, `max_tokens`, `max_retries`, `retry_base_delay`, `sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`, `stream_retry_on_heartbeat_timeout`, and `stream_retry_on_malformed_chunk`. `None` values leave existing settings unchanged.

**Details:** For details on the streaming protocol and the internal implementation of the SSE parser, see [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md).

---

## 11. `McpServerConfig` / `McpServerHealthRegistry`

Both are defined in `shared/mcp_config.py`. For a full field reference, see [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) and [05_agent_08_01_configuration-loading-agent-config.md](05_agent_08_01_configuration-loading-agent-config.md).

**Overview:** Per-server transport config (transport, url, cmd, startup_mode, tool_names, auth_token, env) validated by `__post_init__` (URL scheme, timeout range, `tool_names` uniqueness, env type). Key field set from TOML section name, excluded from `==` comparison. `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE`. `McpServerHealthRegistry` tracks consecutive failures; `UNAVAILABLE` blocks dispatch; `record_degraded(key, reason)` / `get_degraded_reason(key)` track "reachable but degraded" servers without incrementing the failure count.

> **Note:** `McpServerConfig.transport` uses the `TransportType` enum instead of a plain string. Related enums include `StartupMode` (none/persistent/subprocess) and `SecurityProfile` (local/production controls MCP auth enforcement). The `HealthcheckMode` enum was deleted on 2026-07-17 — HTTP was the only transport.

`shared/route_resolver.py`'s `build_discovery_map(server_tool_lists)` currently returns a `tuple[dict[str, str], dict[str, list[str]]]`: `(route_map, duplicates)`, where `duplicates` maps tool names requested from multiple servers to their respective source server keys.

---

## 12. Summary of Execution Flows

**Configuration Loading:** `build_agent_config()` $\rightarrow$ `ConfigLoader().load_all()` reads `agent.toml` only (`_BASE_CONFIG_FILES = ("agent.toml",)`). Other configs (`crawler.toml`, `chunk_splitter.toml`, `ingester.toml`, `*_mcp_server.toml`) are loaded separately following process isolation policies.

**Tool Execution:** `ToolExecutor.execute(tool_name, args)` $\rightarrow$ health gate $\rightarrow$ raw MCP call.

---

## 13. Import Boundaries and Design Notes

- `shared/` must NOT import from `agent/`, `mcp_servers/`, `rag/`, or `db/`.
- For details on `LLMClient`, see this document (section 10) and [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md).
- For details on `ToolExecutor`, see this document (section 9), [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md), and [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md).
