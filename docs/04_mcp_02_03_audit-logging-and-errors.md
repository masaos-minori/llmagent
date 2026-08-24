---
title: "MCP Audit Log Format and Common Error Handling"
area: mcp
tags:
  - mcp
  - audit
  - logging
  - errors
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_02_01_endpoints-and-transport.md
  - 04_mcp_02_02_startup-modes-and-health.md
  - 00_security_01_architecture-and-trust-boundaries.md — System architecture / trust boundaries / threat modeling / authentication & authorization / auditing / local vs production / Fail-open/Fail-closed / prompt injection responsibility boundaries
---

# MCP Protocol and Transport: Audit Logs and Error Formats

## Audit Log Format

Each `POST /v1/call_tool` invocation outputs one JSON-lines audit record.

```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/workspace/file.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

| Field | Source | Always Present? | Value if Missing/Empty |
|---|---|---|---|
| `session_id` | `X-Session-Id` request header | Yes | `"-"` |
| `request_id` | `X-Request-Id` (UUID injected by middleware) | Yes | `"-"` |
| `tool` | `req.name` (tool name) | Yes | — |
| `target` | Server-specific: repository slug / first 80 chars of command / first 80 chars of query | Yes | — |
| `outcome` | `"ok"` or `"error"` | Yes | — |
| `detail` | Optional supplementary info | No | Omitted |
| `server_key` | Server identifier (e.g., `"file_read"`, `"cicd"`, `"mdq"`, `"shell"`, `"github"`) | Yes | `""` |
| `error_type` | Error classification for transport failures | Yes | `""` |

**Note:** github-mcp and shell-mcp write to both shared and dedicated audit logs. Only file-delete-mcp uses a dedicated audit log. File read/write MCP servers do not write audit logs. Dedicated audit logs for github-mcp and shell-mcp use ISO8601 timestamps + op=<operation> + path/repo/command. These do not have X-Session-Id or X-Request-Id correlation fields. Correlation between logs should be based on the agent-side audit logs.

Audit log functions are implemented within each server's dispatch handler.

---

## Common Error Formats

| Error Type | HTTP Status | `is_error` |
|---|---|---|
| Tool not found | 200 | `true` |
| Tool validation error | 200 | `true` |
| Authentication failure | 401 | N/A (Transport error) |
| Server error | 500 | N/A (Transport error) |
| Truncated response | 200 | `false` (Content is provided) |

HTTP transport errors (4xx/5xx) are caught by `HttpTransport.call()`, which raises a `TransportError` exception. The transport error handler converts this into `ToolCallResult(output=str(e), is_error=True, error_type="transport")`.

> **Note:** `HttpTransport.call()` does not directly return `is_error=True` for transport failures. Instead, it raises a `TransportError`. The transport error handler catches this and returns `ToolCallResult(error_type="transport")`. See [04_mcp_03 HttpTransport](./04_mcp_03_03_transport-and-health.md#httptransport).

### HealthRegistry Updates

- **Transport Failure** (after all retries exhausted): `HealthRegistry.record_failure(server_key)` — Increments failure count; may transition the server to DEGRADED/UNAVAILABLE.
- **Transport Success** (including tool-level errors from the server): `HealthRegistry.record_success(server_key)` — Resets failure count to 0. Tool-level errors are tracked separately via `stat_tool_errors`.
- **Cache Hit**: No HealthRegistry update — because no live call was made.
- **Rejected by preflight health check**: `record_failure()` is not called — because the attempt itself was not made.
- **Retry Behavior**: Only the final result is recorded in HealthRegistry (Success, or TransportError after all retries exhausted). Intermediate retry attempts are not counted.

### Error Classification Table

| Error Type | HTTP Status | HealthRegistry Action | request_id | is_retryable |
|---|---|---|---|---|
| HTTP 4xx (Non-retryable: 401/403/404) | 4xx | `record_failure()` | `""` | No |
| HTTP 5xx (Server error) | 5xx | `record_failure()` | `""` | Yes (with backoff) |
| Timeout | N/A | `record_failure()` | `""` | Yes (with backoff) |
| Connection Refused | N/A | `record_failure()` | `""` | No |
| DNS/Network Error | N/A | `record_failure()` | `""` | No |
| Malformed Response (not dict, missing 'result') | 200 | `record_failure()` | `""` | No |

For all transport failures, `request_id=""` is set because the request did not complete normally. For tool-level errors (HTTP 200 and `is_error=True`), the actual `request_id` from the server response is used, and `record_success()` is called.

---

## dispatch_tool helper (`scripts/mcp_servers/dispatch.py`)

```python
from mcp_servers.dispatch import ToolArgs, dispatch_tool

result = await dispatch_tool(dispatch_table, name, args)
# Returns DispatchResult(output, is_error)
```

- Empty string/whitespace `name` → `("Tool name must be a non-empty string", True)`
- Unknown `name` → `("Unknown tool: <name>", True)`
- `ValueError` from handler → `("Validation error: <e>", True)`
- Other exceptions are propagated to the caller

**Disabled call handling:** When a tool is disabled, the MCP server returns a response with `is_error=True` and includes the concrete reason in the result field. This follows the standard error response format but specifically indicates the tool is disabled rather than encountering a runtime error.

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_02_01_endpoints-and-transport.md`
- `04_mcp_02_02_startup-modes-and-health.md`
- `00_security_01_architecture-and-trust-boundaries.md` — System architecture / trust boundaries / threat modeling / authentication & authorization / auditing / local vs production / Fail-open/Fail-closed / prompt injection responsibility boundaries

## Keywords

mcp
protocol
transport
audit
error
HealthRegistry
TransportError
dispatch_tool
