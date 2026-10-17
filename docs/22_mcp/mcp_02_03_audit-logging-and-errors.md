---
title: "MCP Audit Log Format and Common Error Handling"
area: mcp
tags:
  - mcp
  - audit
  - logging
  - errors
related:
  - mcp_00_document-guide.md
  - mcp_02_01_endpoints-and-transport.md
  - mcp_02_02_startup-modes-and-health.md
  - security_01_architecture-and-trust-boundaries.md
  - mcp_06_05_reading-audit-logs.md
  - mcp_03_03_transport-and-health.md
---

# MCP Protocol and Transport: Audit Logs and Error Formats

## Audit Log Format

Each `POST /v1/call_tool` invocation on a server that writes the shared audit log outputs one JSON-lines audit record. Those servers are web-search-mcp, github-mcp, shell-mcp, cicd-mcp, mdq-mcp, git-mcp, file-write-mcp, and file-delete-mcp. file-read-mcp and rag-pipeline-mcp write no audit log (see the Note below and `mcp_06_05_reading-audit-logs.md`).

```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"search_web","target":"example query","outcome":"ok","server_key":"web_search","error_type":""}
```

| Field | Source | Always Present? | Value if Missing/Empty |
|---|---|---|---|
| `session_id` | `X-Session-Id` request header | Yes | `"-"` |
| `request_id` | `X-Request-Id` (UUID injected by middleware) | Yes | `"-"` |
| `tool` | `req.name` (tool name) | Yes | — |
| `target` | Server-specific: repository slug / truncated command / truncated query / requested file path (truncation length defined per server, e.g. `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/mdq/audit_target.py`). file-write-mcp and file-delete-mcp record the caller-supplied path truncated to 80 characters rather than a resolved canonical path. | Yes | — |
| `outcome` | `"ok"`, `"error"`, or `"rejected"` (the call was rejected by a policy guard before or instead of execution; emitted by git-mcp, file-write-mcp, and file-delete-mcp) | Yes | — |
| `detail` | Optional supplementary info | No | Omitted |
| `server_key` | Server identifier (e.g., `"web_search"`, `"cicd"`, `"mdq"`, `"shell"`, `"github"`) | Yes | `""` |
| `error_type` | Error classification for transport failures | Yes | `""` |
| `requested_target` | Caller-supplied resource path as received, before resolution, redacted by the caller; emitted by git-mcp only | No | Omitted |
| `canonical_target` | Resolved canonical repository path; emitted by git-mcp only | No | Omitted |
| `pre_condition` | Serialized repository state before the operation; emitted by git-mcp only | No | Omitted |
| `post_condition` | Serialized repository state after the operation; emitted by git-mcp only | No | Omitted |
| `requested_target` | Redacted caller-supplied target captured before canonical path resolution; emitted only when the caller supplies it, mirroring the `canonical_target` pattern | No | Omitted |

**Note:** github-mcp, shell-mcp, and file-delete-mcp write to both the shared and a dedicated audit log; file-write-mcp writes only the shared audit log. file-read-mcp and rag-pipeline-mcp do not write audit logs. Dedicated audit logs for github-mcp, shell-mcp, and file-delete-mcp use ISO8601 timestamps + op=<operation> + path/repo/command. These do not have X-Session-Id or X-Request-Id correlation fields. Correlation between logs should be based on the agent-side audit logs.

### Approval correlation

The shared `mcp_tool_exec` record correlates with the Agent-side audit events through shared keys rather than a server-side approval check. The Agent writes a `tool_approval` event (`scripts/agent/tool_audit.py`) carrying `session_id` and `task_id`, then a `tool_exec` event carrying the same `session_id`/`task_id` plus `mcp_request_id`. The server echoes `session_id` and `request_id` into the `mcp_tool_exec` record, where `request_id` equals the Agent-side `tool_exec.mcp_request_id`. Joining on `session_id` (plus `task_id`, and `request_id` = `mcp_request_id`) reconstructs the `tool_approval` -> `tool_exec` -> `mcp_tool_exec` path end to end. No MCP server performs an approval check itself: the servers read only `x-session-id`, `x-request-id`, and `x-idempotency-key`, and the Agent sends no approval identifier server-side (see `scripts/mcp_servers/server.py`). Correlation across the dedicated (non-shared) audit logs therefore relies on these agent-side keys.

Audit log functions are implemented within each server's dispatch handler.

### Approval correlation

`session_id` and `request_id` are the join keys from a shared `mcp_tool_exec` record to the agent-side `tool_exec` record: the agent writes the server's request id into `tool_exec.mcp_request_id` (`scripts/agent/tool_audit.py`), and both records carry the same `session_id`. A call rejected by a server-side guard is joined the same way as an accepted one, because the join uses those keys and not `outcome`. The agent-side `tool_approval` record joins to `tool_exec` on `session_id` and `task_id`. The dedicated plain-text logs carry no correlation fields, so correlating a server-side rejection with the approval that preceded it runs through the shared JSON-lines audit log and the agent-side `tool_exec` / `tool_approval` records.

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

> **Note:** `HttpTransport.call()` does not directly return `is_error=True` for transport failures. Instead, it raises a `TransportError`. The transport error handler catches this and returns `ToolCallResult(error_type="transport")`. See [mcp_03 HttpTransport](./mcp_03_03_transport-and-health.md#httptransport).

### McpServerHealthRegistry Updates

- **Transport Failure** (after all retries exhausted): `McpServerHealthRegistry.record_failure(server_key)` — Increments failure count; may transition the server to DEGRADED/UNAVAILABLE.
- **Transport Success** (including tool-level errors from the server): `McpServerHealthRegistry.record_success(server_key)` — Resets failure count to 0. Tool-level errors are tracked separately via `stat_tool_errors`.
- **Rejected by preflight health check**: `record_failure()` is not called — because the attempt itself was not made.
- **Retry Behavior**: Only the final result is recorded in McpServerHealthRegistry (Success, or TransportError after all retries exhausted). Intermediate retry attempts are not counted.

### Error Classification Table

The exact HTTP-status/retryability classification for each transport failure kind is
determined by `scripts/shared/mcp_health.py::McpServerHealthRegistry.record_failure()` and its
callers in the transport-error-handling path — see that module for the current
mapping.

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

## Keywords

- mcp
- protocol
- transport
- audit
- error
- McpServerHealthRegistry
- TransportError
- dispatch_tool
