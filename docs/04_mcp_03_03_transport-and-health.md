title: "HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys (Part 1 & 2)"
category: mcp
tags:
  - mcp
  - transport
  - health-registry
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
source:
  - 04_mcp_03_03_transport-and-health.md

# HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys (Part 1)

## HttpTransport (`shared/http_transport.py`)

### HttpTransport

**Inconsistency (Record of required fix):** This section header was previously `shared/tool_executor.py`, but the actual implementation of the `HttpTransport` class is defined in `shared/http_transport.py` (Explicit in code). Instantiation and retention are handled by `shared/tool_transport_invoker.py`, while `shared/tool_executor.py` only imports the `TransportError` exception type from the same module. Although the module docstring of `shared/tool_executor.py` states "Provides HttpTransport implementation for POST /v1/call_tool over httpx.", the actual implementation does not exist in that file (Explicit in code).

```python
HttpTransport(http, base_url, server_key, cfg=McpServerConfig)
result = await transport.call("tool_name", {"arg": "val"})
```

- If `cfg.auth_token` is not empty, `Authorization: Bearer <token>` is added.
- All transport-level failures (timeouts, non-2xx HTTP, malformed responses, exhaustion of retries) raise a `TransportError`; it never directly returns `is_error=True`.
- Transport error handlers catch `TransportError` and convert it to `ToolCallResult(error_type="transport")`.
- `set_session_id(session_id)` injects an `X-Session-Id` header into every request (via `ToolTransportInvoker`).
- **Retries:** Retries are performed on HTTP 429/502/503/504. A maximum of 3 attempts are made, with decreasing delays: 4 seconds for attempt 0, 2 seconds for attempt 1, and 1 second for attempt 2 before a final exhaustion error occurs. Formula: $2^{(RETRY\_MAX - attempt - 1)}$. This is not exponential backoff (delays decrease per attempt). Only the final result (success or `TransportError` after all retries exhausted) is recorded in the HealthRegistry. The `TransportError` message (`"[Retry exhausted] ..."`) includes the last caught exception details (type, status code, etc.) at the end.
- **Non-retryable errors:** HTTP timeouts (`httpx.TimeoutException`) and `HTTPStatusError` for status codes other than 429/502/503/504 are propagated immediately without retries.
- **Tool-level vs. Transport-level errors:** Tool-level errors (`error_type == "tool"`) are treated as successful transport calls, triggering `record_success()` and incrementing the `stat_tool_errors` counter. Transport-level errors trigger `record_failure()` and increment the `stat_transport_errors` counter. Both counters are tracked independently.
- **Response Parsing:** The `_handle_call_tool_response()` method uses `parse_http_json(resp)` within `parse_http_json` (defined in `shared/json_utils.py`) to decode JSON data from an `httpx.Response`. Previously, `orjson.loads(resp.content)` was used directly.

---

42. ## McpServerHealthRegistry (`shared/mcp_health.py`)

**Note:** The class implementation is defined in `shared/mcp_health.py`. `shared/mcp_config.py` only re-exports it using `# noqa: F401` (Explicit in code). Since they can both be imported with the same name, there is no practical issue, but the canonical module is `shared/mcp_health.py`.

Created within `_build_tool_executor()` (factory.py), this is a per-server failure tracker shared between `ToolTransportInvoker` (via `set_health_registry()`) and `AppServices.health_registry`. Because they hold the same object, health status recorded by `ToolExecutor` is immediately visible via `AppServices.health_registry`.

**State Transitions:**

``` text
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown 30s elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                         │
                               (failure)─┘ → UNAVAILABLE (cooldown reset)
```

| State | Condition |
|---|---|
| `HEALTHY` | No failures, or after a successful call |
| `DEGRADED` | number of failures < threshold (default 3) |
| `UNAVAILABLE` | number of failures ≥ threshold; dispatch is blocked |
| `HALF_OPEN` | After 30s cooldown; allows one trial dispatch |

| Method | Description |
|---|---|
| `record_failure(server_key)` | Increments failure count; `HALF_OPEN → UNAVAILABLE` (cooldown reset); if threshold reached → `UNAVAILABLE` |
| `record_success(server_key)` | Resets failure count and unavailable timestamp; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | Current state; returns `HEALTHY` for unknown keys |
| `is_unavailable(server_key)` | Returns `True` if `UNAVAILABLE` and cooldown has not yet elapsed; side effect: transitions to `HALF_OPEN` when cooldown expires |

**Constructor:** `McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=30.0)`
- `half_open_cooldown_sec`: Seconds until trial dispatch is allowed after entering `UNAVAILABLE` (default 30s, fixed value — not exponential backoff).

**Shared Wiring:** This registry is created once and consumed in multiple places — writing side is `ToolTransportInvoker` (`record_failure`/`record_success`), reading side is `/mcp status` (`McpStatusService.probe_all()`, `get_state`). Created during the tool executor build process in `factory.py`, an instance of `McpServerHealthRegistry()` is generated and injected into `ToolTransportInvoker` via `set_health_registry()`, and the same object is also stored in `AppServices.health_registry`. As a result, dispatch gating (`is_unavailable()`) recognizes transport layer failure records without synchronization lag. Note: Replacing or rebuilding the registry object (e.g., if a future refactor creates a second `McpServerHealthRegistry()`) would cause asynchrony between writers and readers, breaking dispatch gating consistency — consider this constraint in future changes.

---

84. ## Related Documents

86. - `04_mcp_00_document-guide.md`
87. - `04_mcp_03_01_dispatch-and-routing.md`
88. - `04_mcp_03_02_tool-registry.md`
89. - `04_mcp_03_03_transport-and-health.md`
90. - `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
91. - `04_mcp_03_05_lifecycle-and-new-server.md`

93. ## Keywords

95. mcp
96. HttpTransport
97. McpServerHealthRegistry
98. health state
99. retry
100. correlation keys

102. # HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys (Part 2)

190. ## End-to-End Tool Call Tracing

192. ### End-to-end tool call tracing

194. ### Correlation Keys

196. | Key | Source | Occurrence |
197. |---|---|---|
198. | `X-Session-Id` | Agent (`ctx.session.session_id`) | HTTP Request Header; MCP Server access logs; Agent audit logs |
199. | `X-Request-Id` | MCP Server (UUID per request) | HTTP Response Header; MCP Server access logs; Agent audit logs (`x_request_id`) |
200. | `server_key` | `McpServerConfig.key` | Agent routing logs; `ToolCallResult.server_key`; health registry; transport error counters |
201. | `tool_name` | LLM tool call | Agent audit logs; MCP server request logs; tool error counters |

203. To trace a single tool call, combine `X-Request-Id` (unique per call) and `X-Session-Id` (spans entire session).

205. ---

207. ### Example Success Path

209. ``` text
210. 1. Agent: LLM emits tool_use for "read_text_file"
211.    → tool_runner.execute_one_tool_call(ctx, name="read_text_file", ...)
212.    → ToolRouteResolver.resolve("read_text_file") → server_key="file_read"
213. 
214. 2. Agent → Server (HTTP):
215.    POST /v1/call_tool
216.    X-Session-Id: 42
217.    body: {"name": "read_text_file", "args": {...}}
218. 
219. 3. MCP server (file-read-mcp):
220.    Server log: INFO [42] read_text_file args=... → OK
221.    Response: X-Request-Id: abc-123, is_error=false, result="..."
222. 
223. 4. Agent receives:
224.    ToolCallResult(output="...", is_error=False, request_id="abc-123", server_key="file_read")
225. 
226. 5. Agent audit_tool_exec():
227.     audit log entry (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"abc-123","is_error":false,"error_type":"","ts":...}
228. 
229. 6. Health registry:
230.    HealthRegistry.record_success("file_read") → state remains HEALTHY
231. ```

233. ---

235. ## Related Documents

237. - `04_mcp_00_document-guide.md`
238. - `04_mcp_03_01_dispatch-and-routing.md`
239. - `04_mcp_03_02_tool-registry.md`
240. - `04_mcp_03_03_transport-and-health.md`
241. - `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
242. - `04_mcp_03_05_lifecycle-and-new-server.md`

244. ## Keywords

246. mcp
247. correlation keys
248. tool call tracing
249. end-to-end tracing
