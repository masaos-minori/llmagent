---
title: "Shared Runtime and Execution Infrastructure — LLM and MCP Clients"
area: shared
tags:
  - shared
  - llm-client
  - mcp-client
related:
  - shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
  - shared_03_04_runtime_and_execution-caching-and-reference.md
  - shared_00_document-guide.md
  - agent_08_03_configuration-tools-memory.md
  - mcp_03_01_dispatch-and-routing.md
  - agent_05_llm-and-streaming.md
  - mcp_06_01_configuration-file-inventory.md
  - agent_08_01_configuration-loading-agent-config.md
  - agent_06_01_tool-execution-and-approval-execution.md
---
# Shared Runtime and Execution Infrastructure

- Overview → [shared_00_document-guide.md](shared_00_document-guide.md)

## 9. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**Responsibility:** Core engine for tool dispatching — handles tool → server resolution, concurrency limits, health gating, and transport communication.

**`ToolCallResult` (Result Contract, `shared/transport_dto.py`):** a frozen dataclass carrying the tool output (truncated if > `MCP_MAX_RESPONSE_BYTES`), an error flag, the routing target (`server_key`), the MCP `X-Request-Id` (empty when unavailable), `source` (`mcp` for MCP calls, empty on error paths) and `error_type` (`transport`/`tool`/empty). `error_type` drives the health gate and error counter aggregation: only transport failures count toward server health.

**Execution Flow:** Resolve `tool_name` → `server_key` via `ToolRouteResolver`; `startup_mode=none` gate rejects disabled servers; `McpServerHealthRegistry.is_unavailable()` blocks `UNAVAILABLE` dispatch (`HALF_OPEN` allows one attempt per cooldown); `lifecycle.ensure_ready()` if configured; execute via `HttpTransport.call()` behind a per-server-key semaphore; return `ToolCallResult`.

**Health Gate:** `McpServerHealthRegistry.is_unavailable()` blocks dispatch when `UNAVAILABLE`; consecutive transport failures transition state from `HEALTHY` → `DEGRADED` → `UNAVAILABLE` (once `failure_threshold` reaches `UNAVAILABLE`); a success response resets state to `HEALTHY` and clears the failure count. `HALF_OPEN` is the standard circuit-breaker recovery state: after `half_open_cooldown_sec` in `UNAVAILABLE` state, one dispatch attempt is allowed; a failure during `HALF_OPEN` immediately returns to `UNAVAILABLE`. The registry stores no degraded reason.

**Concurrency Behavior:** `concurrency_limits` maps `server_key` → max concurrent calls; semaphore-based throttling in `ToolTransportInvoker`; tool-call-batch parallel/serial scheduling is unified under a single path — `agent/tool_runner.py::_execute_with_dag()`, which delegates to `agent/tool_scheduler.py::build_execution_groups()`. `ctx.cfg.tool.serial_tool_calls=True` feeds `force_serial=True` into the scheduler instead of selecting a different execution engine.

**Side-Effect Detection:** `build_execution_groups()` reads each call's `is_write` from `PreparedToolCall.spec` (resolved once during `agent/tool_preparation.py::prepare_tool_calls()`, sourced from `RuntimeToolRegistry.tool_spec_for_call()`) — an unregistered tool is rejected fail-closed during preparation and never reaches scheduling. See [agent_08_03_configuration-tools-memory.md](../23_agent/agent_08_03_configuration-tools-memory.md) for the scheduler's grouping rules.

**Routing:** `RuntimeToolRegistry` is the sole routing authority; unknown tools result in an immediate `ValueError` (see `shared_03_02` for the ownership split). `ToolRegistry` is seed data for startup drift validation only, and configuration file `tool_names` is metadata for drift validation only, not runtime routing. For detailed routing info, see [mcp_03_01_dispatch-and-routing.md](../22_mcp/mcp_03_01_dispatch-and-routing.md).

---

## 10. `LLMClient` (`shared/llm_client.py`)

**Responsibility:** An HTTP client for LLM API communication featuring retry logic, SSE streaming, and error handling.

**Primary APIs:** `LLMClient` wraps `AsyncClient` with SSE streaming and error handling; construction parameters cover retry backoff, sampling limits, token/usage callbacks and the SSE tolerance settings.

**Error Behavior:** Transport and stream errors raise `LLMTransportError`, classified by kind (HTTP 429/503 are retryable, other HTTP statuses are fatal; connect, read-timeout, heartbeat-timeout, malformed-frame and premature-EOF kinds are distinguished). SSE heartbeat timeouts trigger retries if enabled; malformed chunks are retried up to `sse_malformed_retry` times before raising `MALFORMED_SSE_FRAME`. Retry exhaustion raises `LLMTransportError` with `partial_text` containing accumulated output.

**Retries:** Exponential backoff starting from `retry_base_delay`; limit `max_retries` for non-streaming requests; streaming reconnection uses a separate counter `sse_reconnect_max`.

**Statistics (Instance-level):** the instance counts reconnects, heartbeat timeouts and parse errors. Partial completions are not accumulated: `LlmReconnectHandler.stream()` returns them but `LLMClient.stream()` discards them.

**Configuration:** `LlmHotConfigHandler` applies hot reloads for sampling limits and retry/SSE tolerance settings (not the endpoint). `None` values leave existing settings unchanged.

**Details:** For details on the streaming protocol and the internal implementation of the SSE parser, see [agent_05_llm-and-streaming.md](../23_agent/agent_05_llm-and-streaming.md).

---

## 11. `McpServerConfig` / `McpServerHealthRegistry`

Both are defined in `shared/mcp_config.py`. For a full field reference, see [mcp_06_01_configuration-file-inventory.md](../22_mcp/mcp_06_01_configuration-file-inventory.md) and [agent_08_01_configuration-loading-agent-config.md](../23_agent/agent_08_01_configuration-loading-agent-config.md).

**Overview:** Per-server transport config validated by `__post_init__` (URL scheme, timeout range, `tool_names` uniqueness, env type). `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE` / `HALF_OPEN` / `UNKNOWN`. `McpServerHealthRegistry` tracks consecutive failures; `UNAVAILABLE` blocks dispatch. The registry stores no degraded reason (see section 9).

> **Note:** `McpServerConfig.transport` uses the `TransportType` enum instead of a plain string. Related enums include `StartupMode` (none/persistent/subprocess) and `SecurityProfile` (a single `production` member; MCP auth enforcement is unconditional).

---

## 12. Summary of Execution Flows

**Configuration Loading:** `build_agent_config()` → `ConfigLoader().load_all()` reads `agent.toml` only (`_BASE_CONFIG_FILES = ("agent.toml",)`). Other configs (`crawler.toml`, `chunk_splitter.toml`, `ingester.toml`, `*_mcp_server.toml`) are loaded separately following process isolation policies.

**Tool Execution:** `ToolExecutor.execute(tool_name, args)` → health gate → raw MCP call.

---

## 13. Import Boundaries and Design Notes

- Import direction: see `shared_01_overview.md`.
- For details on `LLMClient`, see the `LLMClient` section of this document and [agent_05_llm-and-streaming.md](../23_agent/agent_05_llm-and-streaming.md).
- For details on `ToolExecutor`, see the `ToolExecutor` section of this document, [mcp_03_01_dispatch-and-routing.md](../22_mcp/mcp_03_01_dispatch-and-routing.md), and [agent_06_01_tool-execution-and-approval-execution.md](../23_agent/agent_06_01_tool-execution-and-approval-execution.md).

## Keywords

- shared
- llm-client
- mcp-client
