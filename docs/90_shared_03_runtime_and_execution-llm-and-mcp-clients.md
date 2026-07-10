---
title: "Shared Runtime and Execution - LLM and MCP Clients"
category: shared
tags:
  - shared
  - runtime
  - llm-client
  - mcp-server-config
  - execution-flow
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_runtime_and_execution-config-and-logging.md
  - 90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md
  - 90_shared_03_runtime_and_execution-caching-and-reference.md
source:
  - 90_shared_03_runtime_and_execution-config-and-logging.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)

## 9. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**Responsibility:** Core tool dispatch engine — resolves tool → server, handles caching, concurrency limits, health gating, and transport communication.

**`ToolCallResult` dataclass (result contract):**
```python
@dataclass
class ToolCallResult:
    output: str          # Tool output string (truncated if > MCP_MAX_RESPONSE_BYTES)
    is_error: bool       # True if the tool call failed
    request_id: str      # X-Request-Id from the MCP server response
    server_key: str      # Server key used for routing (e.g. "file_read", "shell")
```

**Execution flow:**
```
ToolExecutor.execute(tool_name, args) -> ToolCallResult
  1. plugin_registry.get_tool(tool_name) → plugin takes priority
  2. ToolRouteResolver.resolve(tool_name) → server_key
  3. McpServerHealthRegistry.is_unavailable(server_key) → block if UNAVAILABLE
  4. TTL + LRU cache check (is_error=False results only)
  5. Execute tool call (tool_name, args)
       → Semaphore acquire (if concurrency_limits set for server_key)
       → HttpTransport.call()
  6. Cache store (is_error=False only; TTL from config)
  7. Return ToolCallResult
```

**Cache behavior:**
- Only `is_error=False` results are cached
- TTL + LRU eviction (configurable via `tool_cache_ttl_sec`, `tool_cache_maxsize`)
- Cache key: `(tool_name, serialized_args)`
- Side-effect tools bypass cache entirely

**Health gate:**
- `McpServerHealthRegistry.is_unavailable(server_key)` blocks dispatch when UNAVAILABLE
- Consecutive transport failures → DEGRADED → UNAVAILABLE state transitions
- Successful response → resets to HEALTHY

**Concurrency behavior:**
- `concurrency_limits` dict maps server_key → max concurrent calls
- Semaphore-based throttling in the tool execution layer
- When `execute_all_tool_calls()` detects any side-effect tool, all calls in that round are serialized

**Side-effect detection:**
```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

When `execute_all_tool_calls()` detects any side-effect tool, all calls in that round
are serialized regardless of `serial_tool_calls` setting.

**Routing:** Two-layer cascade — (1) live `/v1/tools` discovery, (2) `ToolRegistry` from `tool_constants.py`. Unknown tools fail immediately with `ValueError`. See [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) for full routing details.

---

## 10. `LLMClient` (`shared/llm_client.py`)

**Responsibility:** HTTP client for LLM API communication with retry logic, SSE streaming, and error handling.

**Main API:**
```python
class LLMClient:
    def __init__(
        http: AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
    )

    async def call(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse      # Non-streaming
    async def stream(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse  # Streaming
    def build_payload(history: list[LLMMessage], tool_defs: list[dict[str, Any]], stream: bool = False) -> dict[str, Any]  # Payload construction
```

**Error behavior:**
- HTTP errors → `LLMTransportError` with `LLMErrorKind` classification
- SSE heartbeat timeout → retry (configurable via `llm_stream_retry_on_heartbeat_timeout`)
- SSE malformed chunk → retry (configurable via `llm_stream_retry_on_malformed_chunk`)
- Max retries exhausted → raises `LLMTransportError`

**Retry:** Exponential backoff starting at `retry_base_delay`, capped at `max_retries`.

**Statistics (instance-level):** `stat_retries`, `stat_reconnects`, `stat_heartbeat_timeouts`, `stat_partial_completions`, `stat_parse_errors`

**Configuration:** `apply_config()` hot-reloads temperature, max_tokens, and other fields from config dict.

**Full details:** See [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) for streaming protocol details and SSE parser internals.

---

## 11. `McpServerConfig` / `McpServerHealthRegistry`

Both defined in `shared/mcp_config.py`. Full field reference in
[04_mcp_06_configuration-file-inventory.md](04_mcp_06_configuration-file-inventory.md) and
[05_agent_08_configuration-loading-agent-config.md](05_agent_08_configuration-loading-agent-config.md).

**Summary:**
- `McpServerConfig`: per-server transport settings (transport, url, cmd, startup_mode, tool_names, auth_token, etc.) — validated by `__post_init__` (URL scheme, timeout ranges, tool_names uniqueness, env types). The `key` field is set by `_build_single_server()` from the TOML section name and is excluded from `==` comparison.
- `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE`
- `McpServerHealthRegistry`: tracks consecutive failures; `UNAVAILABLE` blocks dispatch; `record_degraded(key, reason)` / `get_degraded_reason(key)` track reachable-but-degraded servers without incrementing failure count

> **Note:** `McpServerConfig.transport` uses `TransportType` enum (not plain `str`).

`build_discovery_map(server_tool_lists)` in `shared/route_resolver.py` now returns `tuple[dict[str, str], dict[str, list[str]]]`: `(route_map, duplicates)` where `duplicates` maps each tool name claimed by more than one server to the full list of claiming server keys.

---

## 12. Execution Flow Summary

**Config loading:**
```
build_agent_config()
  → ConfigLoader().load_all()     [12 files incl. agent.toml — see §2a Config Ownership for full table]
```

**Plugin loading:**
```
Plugin registry initialization
  → plugin_registry.load_plugins(plugin_dir)
  → imports plugins/*.py alphabetically
  → @register_* decorators populate global registry
```

**Tool execution:**
```
ToolExecutor.execute(tool_name, args)
  → plugin priority → health gate → cache → raw MCP call
```

---

## 13. Import Boundaries and Design Notes

- `shared/` must NOT import from `agent/`, `mcp/`, `rag/`, `db/`
- `LLMClient` details are in this document (§10) and [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md)
- `ToolExecutor` details are in this document (§9), [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md), and [05_agent_06_tool-execution-and-approval-execution.md](05_agent_06_tool-execution-and-approval-execution.md)

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_runtime_and_execution-config-and-logging.md`
- `90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md`
- `90_shared_03_runtime_and_execution-caching-and-reference.md`

## Keywords

LLMClient
McpServerConfig
McpServerHealthRegistry
execution flow summary
import boundaries
