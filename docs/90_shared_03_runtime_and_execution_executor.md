---
title: "Shared Runtime - Formatters and ToolExecutor"
category: shared
tags:
  - shared
  - runtime
  - formatter
  - tool executor
  - side effect
  - health gate
  - concurrency
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_03_runtime_and_execution_infra.md
source:
  - 90_shared_03_runtime_and_execution_infra.md
---

# Shared Runtime - Formatters and ToolExecutor

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

---

## 8. `formatters` (`shared/formatters.py`)

```python
def truncate(text: str, max_chars: int) -> str
def fmt_kvlog(op: str, **kwargs) -> str   # key=value log string; first param named "op"
def fmt_size(size: int) -> str           # "1.5 KB", "2.3 MB", etc.
def fmt_md_link(text: str, url: str) -> str   # "[text](url)"
MAX_SNIPPET_CHARS: int                   # max chars for snippet display
```

---

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

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_03_runtime_and_execution_infra.md](90_shared_03_runtime_and_execution_infra.md)
- [90_shared_03_runtime_and_execution_llm.md](90_shared_03_runtime_and_execution_llm.md)
- [90_shared_03_runtime_and_execution_other.md](90_shared_03_runtime_and_execution_other.md)

## Keywords

formatter
tool executor
side effect
health gate
concurrency
