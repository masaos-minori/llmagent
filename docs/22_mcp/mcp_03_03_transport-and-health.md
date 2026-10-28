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

`HttpTransport` provides POST `/v1/call_tool` over httpx. `ToolTransportInvoker` instantiates and retains it; `ToolExecutor` only imports the `TransportError` type.

- If `cfg.auth_token` is not empty, `Authorization: Bearer <token>` is added.
- All transport-level failures (timeouts, non-2xx HTTP, malformed responses, exhaustion of retries) raise a `TransportError`; it never directly returns `is_error=True`.
- Transport error handlers catch `TransportError` and convert it to `ToolCallResult(error_type="transport")`.
- `set_session_id(session_id)` injects an `X-Session-Id` header into every request (via `ToolTransportInvoker`).
- **Retries:** Retries are performed on HTTP 429/502/503/504 and on non-timeout `httpx.RequestError` (e.g. connection errors). The number of attempts is bounded, the delay between attempts for retryable HTTP statuses increases exponentially, and no sleep follows the last attempt. Only the final result (success or `TransportError` after all retries exhausted) is recorded in the McpServerHealthRegistry. The `TransportError` message (`"[Retry exhausted] ..."`) includes the tool name, the last retryable HTTP status (if any), the last request-error cause (if any), and the attempt count; raw response bodies are not included.
- **Non-retryable errors:** HTTP timeouts (`httpx.TimeoutException`) and `HTTPStatusError` for status codes other than 429/502/503/504 are propagated immediately without retries.
- **Tool-level vs. Transport-level errors:** Tool-level errors (`error_type == "tool"`) are treated as successful transport calls, triggering `record_success()` and incrementing the `stat_tool_errors` counter. Transport-level errors trigger `record_failure()` and increment the `stat_transport_errors` counter. Both counters are tracked independently.
---

## McpServerHealthRegistry (`shared/mcp_health.py`)

The canonical module is `shared/mcp_health.py`; `shared/mcp_config.py` only re-exports the class.

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

Semantics: `record_failure` increments the failure count (`HALF_OPEN` goes straight back to `UNAVAILABLE` with the cooldown reset); `record_success` resets the failure count and unavailable timestamp (`HALF_OPEN` goes to `HEALTHY`); `get_state` returns `HEALTHY` for unknown keys; `is_unavailable` returns `True` only while `UNAVAILABLE` and the cooldown has not elapsed, and transitions to `HALF_OPEN` as a side effect when the cooldown expires. Constructor parameters are `failure_threshold` and `half_open_cooldown_sec`; the cooldown is a fixed value, not exponential backoff.

**Shared Wiring (invariant):** one registry instance is created while the tool executor is built (`factory.py`) and shared by the writer (`ToolTransportInvoker` via `set_health_registry()`: `record_failure`/`record_success`) and the readers (`AppServices.health_registry`, used by `McpStatusService.probe_all()` and dispatch gating through `is_unavailable()`). Because they hold the same object, transport failures are visible to dispatch gating and `/mcp status` without synchronization lag. Replacing or rebuilding the registry object (for example creating a second `McpServerHealthRegistry()`) would desynchronize writers and readers and break dispatch gating, so changes must keep a single shared instance.

---

## End-to-End Tool Call Tracing

Correlation keys (`X-Session-Id`, `X-Request-Id`, `server_key`, `tool_name`) are defined in [mcp_02_01](mcp_02_01_endpoints-and-transport.md#correlation-keys). To trace a single tool call, combine `X-Request-Id` (unique per call) and `X-Session-Id` (spans the entire session). The Agent audit record stores the server request id as `mcp_request_id`.

### Example Success Path

1. The LLM emits a tool call; `ToolRouteResolver` resolves `server_key` (for example `file_read`).
2. The Agent POSTs `/v1/call_tool` with `X-Session-Id`.
3. The server answers with an `X-Request-Id` and `is_error=false`.
4. The Agent builds `ToolCallResult(output, is_error=False, request_id, server_key)`.
5. `audit_tool_exec()` writes a `tool_exec` JSON-lines entry carrying `mcp_request_id`.
6. `McpServerHealthRegistry.record_success(server_key)` keeps the state `HEALTHY`.

The failure path is in [mcp_03_04](mcp_03_04_tool-call-tracing-and-lifecycle.md).

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
