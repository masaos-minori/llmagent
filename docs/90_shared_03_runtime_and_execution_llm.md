---
title: "Shared Runtime - LLMClient and MCP Health"
category: shared
tags:
  - shared
  - runtime
  - llmclient
  - sse
  - streaming
  - retry
  - reconnect
  - mcp health
  - mcpservers
  - health registry
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_03_runtime_and_execution_infra.md
  - 90_shared_03_runtime_and_execution_executor.md
source:
  - 90_shared_03_runtime_and_execution_infra.md
---

# Shared Runtime - LLMClient and MCP Health

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

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
[04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) and
[05_agent_08_configuration.md](05_agent_08_configuration.md).

**Summary:**
- `McpServerConfig`: per-server transport settings (transport, url, cmd, startup_mode, tool_names, auth_token, etc.) — validated by `__post_init__` (URL scheme, timeout ranges, tool_names uniqueness, env types). The `key` field is set by `_build_single_server()` from the TOML section name and is excluded from `==` comparison.
- `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE`
- `McpServerHealthRegistry`: tracks consecutive failures; `UNAVAILABLE` blocks dispatch; `record_degraded(key, reason)` / `get_degraded_reason(key)` track reachable-but-degraded servers without incrementing failure count

> **Note:** `McpServerConfig.transport` uses `TransportType` enum (not plain `str`).

`build_discovery_map(server_tool_lists)` in `shared/route_resolver.py` now returns `tuple[dict[str, str], dict[str, list[str]]]`: `(route_map, duplicates)` where `duplicates` maps each tool name claimed by more than one server to the full list of claiming server keys.

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_03_runtime_and_execution_infra.md](90_shared_03_runtime_and_execution_infra.md)
- [90_shared_03_runtime_and_execution_executor.md](90_shared_03_runtime_and_execution_executor.md)
- [90_shared_03_runtime_and_execution_other.md](90_shared_03_runtime_and_execution_other.md)

## Keywords

llmclient
sse
streaming
retry
reconnect
mcp health
mcpservers
health registry
