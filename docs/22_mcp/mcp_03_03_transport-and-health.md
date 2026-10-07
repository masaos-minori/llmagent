---
title: "HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys"
area: mcp
tags:
  - mcp
  - transport
  - health-registry
related:
  - mcp_00_document-guide.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_03_02_tool-registry.md
  - mcp_03_04_tool-call-tracing-and-lifecycle.md
  - mcp_03_05_lifecycle-and-new-server.md
---

# HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys

## HttpTransport (`shared/http_transport.py`)

### HttpTransport

`HttpTransport` provides POST `/v1/call_tool` over httpx. Its instantiation and retention are handled by `ToolTransportInvoker`, while `ToolExecutor` only imports the `TransportError` exception type from the same module as `HttpTransport`.

```python
HttpTransport(http, base_url, server_key, cfg=McpServerConfig)
result = await transport.call("tool_name", {"arg": "val"})
```

- If `cfg.auth_token` is not empty, `Authorization: Bearer <token>` is added.
- All transport-level failures (timeouts, non-2xx HTTP, malformed responses, exhaustion of retries) raise a `TransportError`; it never directly returns `is_error=True`.
- Transport error handlers catch `TransportError` and convert it to `ToolCallResult(error_type="transport")`.
- `set_session_id(session_id)` injects an `X-Session-Id` header into every request (via `ToolTransportInvoker`).
- **Retries:** Retries are performed on HTTP 429/502/503/504 and on non-timeout `httpx.RequestError` (e.g. connection errors). The number of attempts is bounded by `HttpTransport._RETRY_MAX`. The delay between attempts for retryable HTTP statuses increases exponentially (`2**attempt` seconds); no sleep follows the last attempt. Only the final result (success or `TransportError` after all retries exhausted) is recorded in the HealthRegistry. The `TransportError` message (`"[Retry exhausted] ..."`) includes the tool name, the last retryable HTTP status (if any), and the attempt count; raw response bodies are not included.
- **Non-retryable errors:** HTTP timeouts (`httpx.TimeoutException`) and `HTTPStatusError` for status codes other than 429/502/503/504 are propagated immediately without retries.
- **Tool-level vs. Transport-level errors:** Tool-level errors (`error_type == "tool"`) are treated as successful transport calls, triggering `record_success()` and incrementing the `stat_tool_errors` counter. Transport-level errors trigger `record_failure()` and increment the `stat_transport_errors` counter. Both counters are tracked independently.
- **Response Parsing:** `HttpTransport._parse_http_response()` uses `parse_http_json(resp)` (defined in `shared/json_utils.py`) to decode JSON data from an `httpx.Response`.

---

## McpServerHealthRegistry (`shared/mcp_health.py`)

**Note:** The class implementation is defined in `shared/mcp_health.py`. `shared/mcp_config.py` only re-exports it using `# noqa: F401` (Explicit in code). Since they can both be imported with the same name, there is no practical issue, but the canonical module is `shared/mcp_health.py`.

Created within `_build_tool_executor()` (factory.py), this is a per-server failure tracker shared between `ToolTransportInvoker` (via `set_health_registry()`) and `AppServices.health_registry`. Because they hold the same object, health status recorded by `ToolExecutor` is immediately visible via `AppServices.health_registry`.

**State Transitions:**

``` text
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                         │
                               (failure)─┘ → UNAVAILABLE (cooldown reset)
```

| State | Condition |
|---|---|
| `HEALTHY` | No failures, or after a successful call |
| `DEGRADED` | number of failures < threshold |
| `UNAVAILABLE` | number of failures ≥ threshold; dispatch is blocked |
| `HALF_OPEN` | After the cooldown; allows one trial dispatch |

| Method | Description |
|---|---|
| `record_failure(server_key)` | Increments failure count; `HALF_OPEN → UNAVAILABLE` (cooldown reset); if threshold reached → `UNAVAILABLE` |
| `record_success(server_key)` | Resets failure count and unavailable timestamp; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | Current state; returns `HEALTHY` for unknown keys |
| `is_unavailable(server_key)` | Returns `True` if `UNAVAILABLE` and cooldown has not yet elapsed; side effect: transitions to `HALF_OPEN` when cooldown expires |

**Constructor:** `McpServerHealthRegistry(failure_threshold, half_open_cooldown_sec)` (defaults in `shared/mcp_health.py`)
- `half_open_cooldown_sec`: Seconds until trial dispatch is allowed after entering `UNAVAILABLE` (fixed value — not exponential backoff).

**Shared Wiring:** This registry is created once and consumed in multiple places — writing side is `ToolTransportInvoker` (`record_failure`/`record_success`), reading side is `/mcp status` (`McpStatusService.probe_all()`, `get_state`). Created during the tool executor build process in `factory.py`, an instance of `McpServerHealthRegistry()` is generated and injected into `ToolTransportInvoker` via `set_health_registry()`, and the same object is also stored in `AppServices.health_registry`. As a result, dispatch gating (`is_unavailable()`) recognizes transport layer failure records without synchronization lag. Note: Replacing or rebuilding the registry object (e.g., if a future refactor creates a second `McpServerHealthRegistry()`) would cause asynchrony between writers and readers, breaking dispatch gating consistency — consider this constraint in future changes.

---

## End-to-End Tool Call Tracing

### End-to-end tool call tracing

### Correlation Keys

| Key | Source | Occurrence |
|---|---|---|
| `X-Session-Id` | Agent (`ctx.session.session_id`) | HTTP Request Header; MCP Server access logs; Agent audit logs |
| `X-Request-Id` | MCP Server (UUID per request) | HTTP Response Header; MCP Server access logs; Agent audit logs (`x_request_id`) |
| `server_key` | `McpServerConfig.key` | Agent routing logs; `ToolCallResult.server_key`; health registry; transport error counters |
| `tool_name` | LLM tool call | Agent audit logs; MCP server request logs; tool error counters |

To trace a single tool call, combine `X-Request-Id` (unique per call) and `X-Session-Id` (spans entire session).

---

### Example Success Path

``` text
1. Agent: LLM emits tool_use for "read_text_file"
   → tool_runner.execute_one_tool_call(ctx, name="read_text_file", ...)
   → ToolRouteResolver.resolve("read_text_file") → server_key="file_read"

2. Agent → Server (HTTP):
   POST /v1/call_tool
   X-Session-Id: 42
   body: {"name": "read_text_file", "args": {...}}

3. MCP server (file-read-mcp):
   Server log: INFO [42] read_text_file args=... → OK
   Response: X-Request-Id: abc-123, is_error=false, result="..."

4. Agent receives:
   ToolCallResult(output="...", is_error=False, request_id="abc-123", server_key="file_read")

5. Agent audit_tool_exec():
    audit log entry (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"abc-123","is_error":false,"error_type":"","ts":...}

6. Health registry:
   McpServerHealthRegistry.record_success("file_read") → state remains HEALTHY
```

## Keywords

- mcp
- HttpTransport
- McpServerHealthRegistry
- health state
- retry
- correlation keys
- tool call tracing
- end-to-end tracing
- transport
- health-registry
