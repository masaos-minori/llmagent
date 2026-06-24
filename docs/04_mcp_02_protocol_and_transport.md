# MCP Protocol and Transport

- System overview → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)

## Purpose

Document the shared MCP protocol: HTTP and stdio formats, common types, authentication,
response truncation, audit logging, and error shapes.

---

## Common Endpoints (All Servers)

| Endpoint | Method | Description |
|---|---|---|
| `/v1/call_tool` | POST | Execute a named tool |
| `/v1/tools` | GET | List available tools and descriptions |
| `/health` | GET | Health check |

All 11 servers expose these endpoints. `/health` response varies by server (see §Server-specific health).

---

## HTTP Transport: `/v1/call_tool`

### Request

```
POST /v1/call_tool
Content-Type: application/json
Authorization: Bearer <token>   (when auth_token is configured)
X-Session-Id: <session_id>      (injected by ToolExecutor)

{"name": "tool_name", "args": {"key": "value"}}
```

`X-Session-Id` is set by `ToolExecutor.set_session_id()` at agent startup and injected by
`HttpTransport.call()` into every POST request.

`X-Request-Id` is injected by the server's auth middleware as a UUID in the response header.

### Response

```json
{"result": "<formatted text>", "is_error": false}
```

`is_error=true` signals a tool-level error. HTTP status is still 200 for tool errors.
HTTP 4xx/5xx signals a transport-level error.

---

## Pydantic Models (`mcp/models.py`)

```python
class CallToolRequest(BaseModel):
    name: str
    args: dict = {}

class CallToolResponse(BaseModel):
    result: str
    is_error: bool
```

Shared across all MCP servers. Ensures consistent request/response structure.

---

## HTTP Tool List: `/v1/tools`

```json
{"tools": [{"name": "read_text_file", "description": "..."}]}
```

Called by `AgentREPL._check_tool_definitions()` at startup to validate that configured
tool names match live server tools. Mismatch → warning log; if `tool_definitions_strict=True` → `RuntimeError`.

---

## stdio Transport

All servers support `--stdio` mode. The agent uses `StdioTransport` to communicate over
the process's stdin/stdout with newline-delimited JSON.

### stdio Request (one line)

```json
{"id": 1, "name": "search_docs", "args": {"query": "watchdog", "limit": 10}}
```

### stdio Response (one line)

```json
{"id": 1, "result": "...", "is_error": false, "truncated": false, "total_bytes": 1234}
```

### Reserved RPC: `__list_tools__`

```json
// Request
{"id": 1, "name": "__list_tools__", "args": {}}
// Response
{"id": 1, "result": "{\"tools\": [\"search_docs\", ...]}", "is_error": false}
```

Used by `healthcheck_mode="ping_tool"` to verify the server is alive.
`__` prefix is reserved — user-defined tools must not use this prefix.

---

## MCPServer Base Class (`mcp/server.py`)

All MCP servers inherit from `MCPServer`.

### Data classes

| Class | Fields | Purpose |
|---|---|---|
| `TruncationResult` | `text: str`, `truncated: bool`, `total_bytes: int` | Return value of `_truncate_with_meta()` |

### Class attributes (declared by subclasses)

| Attribute | Type | Example |
|---|---|---|
| `server_name` | `str` | `"web-search-mcp"` |
| `server_version` | `str` | `"3.0.0"` |
| `http_host` | `str` | `"127.0.0.1"` |
| `http_port` | `int` | `8004` |
| `app_module` | `str` | `"mcp.web_search.server:app"` (most servers); `github-mcp` uses bare `"github_mcp_server:app"` (see `04_mcp_90`) |
| `mcp_tools` | `list[dict]` | Tool definitions list |

### Methods

| Method | Description |
|---|---|---|
| `async dispatch(name, args) -> DispatchResult` | Abstract; must be overridden. Returns `DispatchResult(output, is_error)` |
| `list_tools() -> list[str]` | Tool names from `mcp_tools`. Returns `[]` if not defined |
| `list_tools_with_server_key() -> list[dict[str, object]]` | Tool metadata including `server_key`; used by `/v1/tools` endpoint |
| `health() -> dict[str, object]` | `{"status": "ok", "ready": bool, "dependencies": dict, "details": dict}` by default; overridden per server (e.g. github adds `github_token` to `dependencies`, mdq adds `service` to `details`) |
| `run_http() -> None` | Start uvicorn HTTP server |
| `async run_stdio() -> None` | Handle newline-delimited JSON-RPC on stdin/stdout |

### Entry point pattern (all servers)

```python
if __name__ == "__main__":
    import sys
    server = MyMCPServer()
    if "--stdio" in sys.argv:
        asyncio.run(server.run_stdio())
    else:
        server.run_http()
```

---

## HTTP vs stdio Mode

| Aspect | HTTP mode | stdio mode |
|---|---|---|
| Process management | subprocess only | Agent manages via StdioTransport |
| Request format | POST to `/v1/call_tool` | newline-delimited JSON |
| Concurrency | uvicorn async | per-instance asyncio.Lock (serialized) |
| Session ID header | `X-Session-Id` | not applicable |
| Tool list check | `GET /v1/tools` | `__list_tools__` RPC |
| Health check | `GET /health` | `healthcheck_mode="ping_tool"` or process alive |

---

### stdio Transport: Scalability Limits (Design Note)

**Current behavior:**
Each `StdioTransport` instance serializes concurrent calls using a single `asyncio.Lock`
(see `shared/tool_executor.py`). This means only one request at a time can be in-flight
per stdio server, regardless of how many concurrent tool calls arrive.

**Why this is acceptable today:**
All production servers use `transport = "http"` (see `config/mcp_servers.toml`).
stdio mode is available but currently unused in production. With one or two stdio servers
handling low-concurrency workloads, the lock contention is negligible.

**When this becomes a bottleneck:**
If stdio-based servers become common, or if a single stdio server receives high
concurrent load (e.g., embedded local tools called across many parallel tool rounds),
the serialized lock will create a queue of waiting coroutines. Threshold TBD — dependent
on round concurrency and per-call latency.

**Future scaling options (planning note — no current commitment):**

1. **Worker pool per stdio server**: Spawn N subprocess workers and distribute calls
   across them using a semaphore-guarded pool. Cost: N × memory overhead per worker.

2. **Multiplexed stdio protocol**: Extend the JSON-RPC framing to support concurrent
   in-flight requests with response matching by `id`. Requires server-side support and
   a response demultiplexer in `StdioTransport`.

3. **Migrate to HTTP transport**: Convert high-traffic stdio servers to persistent HTTP
   servers. Aligns with the existing `HttpTransport` path which has no per-instance
   serialization constraint. This is the lowest-risk migration path.

See `04_mcp_01_system_overview.md` for the transport overview and
`shared/tool_executor.py` (`StdioTransport` class) for the lock implementation.

---

## Bearer Authentication

When `McpServerConfig.auth_token` is non-empty:
- Server: `attach_auth_middleware(app, token)` registers middleware that validates
  `Authorization: Bearer <token>`. Mismatched requests receive HTTP 401.
- Client: `HttpTransport` injects `Authorization: Bearer <token>` into every POST.
- Empty `auth_token`: auth check skipped; only `X-Request-Id` injection is active.

---

## Response Truncation

When result exceeds 512 KB:
```
[TRUNCATED: {total:,} bytes total, showing {max_bytes:,} bytes]
```

- `total_bytes` = original byte count (before truncation)
- `showing` = `MCP_MAX_RESPONSE_BYTES` (512 KB) — the display limit
- Implemented by `_truncate_with_meta()` in `mcp/server.py`

**Note:** The suffix says "showing 524,288 bytes" (the limit), not the actual truncated bytes.

---

## Server-Specific Health Response Fields

| Server | `/health` overrides |
|---|---|---|
| web-search-mcp | No overrides (returns `{"status":"ok","ready":true}`) |
| github-mcp | `dependencies.github_token` (`"set"`/`"not_set"`) |
| mdq-mcp | root-level `"stub": true` (marks experimental status); `details.service: "mdq-mcp"` |
| shell-mcp | `dependencies.shell` (`"sh not found in PATH"`/`"check failed"`); `details.sandbox_backend` (`"firejail"` or `"none"`) |
| file-read-mcp | `dependencies.filesystem` (`"/workspace not found"`/`"check failed"`) |
| file-write-mcp | `dependencies.filesystem` (`"/workspace not found"`/`"check failed"`) |
| file-delete-mcp | `dependencies.filesystem` (`"/workspace not found"`/`"check failed"`) |
| rag-pipeline-mcp | `dependencies.embed_url` (`"not configured"`/`"check failed"`) |
| sqlite-mcp | `dependencies.<db_name>` (`"file not found: <path>"`/`"check failed"`) per registered DB |
| git-mcp | `dependencies.git` (`"git not found in PATH"`/`"check failed"`) |

---

## Audit Log Format

Every `POST /v1/call_tool` emits one audit log line:

```
AUDIT session=<session_id> request=<x_request_id> action=<tool_name> target=<primary_arg> outcome=<ok|error> detail=<supplementary>
```

| Field | Source | Missing value |
|---|---|---|
| `session` | `X-Session-Id` request header | `"-"` |
| `request` | `X-Request-Id` (middleware-injected UUID) | `"-"` |
| `action` | `req.name` (tool name) | — |
| `target` | Server-specific: repo slug / command first 80 chars / query 80 chars | — |
| `outcome` | `"ok"` or `"error"` | — |
| `detail` | Optional supplementary info | `""` |

Implemented via `mcp.audit._audit_log()` called from each server's dispatch handler.

---

## Common Error Shape

| Error type | HTTP status | `is_error` |
|---|---|---|
| Tool not found | 200 | `true` |
| Tool validation error | 200 | `true` |
| Auth failure | 401 | N/A (transport error) |
| Server error | 500 | N/A (transport error) |
| Response truncated | 200 | `false` (content provided) |

HTTP transport errors (4xx/5xx) are caught by `HttpTransport.call()` and returned as
`ToolCallResult(output=error_message, is_error=True)`.

---

## dispatch_tool Helper (`mcp/dispatch.py`)

```python
from mcp.dispatch import ToolArgs, dispatch_tool

result = await dispatch_tool(dispatch_table, name, args)
# Returns DispatchResult(output, is_error)
```

- Empty/whitespace `name` → `("Tool name must be a non-empty string", True)`
- Unknown `name` → `("Unknown tool: <name>", True)`
- `ValueError` from handler → `("Validation error: <e>", True)`
- Other exceptions propagate to caller

**Note:** For HTTP transport, `CallToolRequest.name_must_not_be_blank()` validator in `mcp/models.py` catches empty names before `dispatch_tool()` is reached. The `dispatch_tool()` empty-name check is redundant for HTTP but relevant for stdio mode.
