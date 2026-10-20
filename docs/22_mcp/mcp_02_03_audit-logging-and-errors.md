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

**Note:** github-mcp, shell-mcp, and file-delete-mcp write to both the shared and a dedicated audit log; file-write-mcp writes only the shared audit log. file-read-mcp and rag-pipeline-mcp do not write audit logs. Dedicated audit logs for github-mcp, shell-mcp, and file-delete-mcp use ISO8601 timestamps + op=<operation> + path/repo/command. These do not have X-Session-Id or X-Request-Id correlation fields. Correlation between logs should be based on the agent-side audit logs.

### Approval correlation

The shared `mcp_tool_exec` record correlates with Agent-side audit events through shared keys; no MCP server performs an approval check itself (servers read only `x-session-id`, `x-request-id`, and `x-idempotency-key`, and the Agent sends no approval identifier to the server).

- The Agent writes a `tool_approval` event carrying `session_id` and `task_id`, then a `tool_exec` event carrying the same keys plus `mcp_request_id` (`scripts/agent/tool_audit.py`).
- The server echoes `session_id` and `request_id` into `mcp_tool_exec`; `request_id` equals the Agent-side `tool_exec.mcp_request_id`.
- Joining on `session_id` (plus `task_id`, and `request_id` = `mcp_request_id`) reconstructs `tool_approval` -> `tool_exec` -> `mcp_tool_exec`. A call rejected by a server-side guard joins the same way as an accepted one, because the join does not use `outcome`.
- The dedicated plain-text audit logs carry no correlation fields, so correlating a server-side rejection with the approval that preceded it runs through the shared JSON-lines audit log and the Agent-side records.

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

The HTTP-status and retryability classification per transport failure kind is owned by `McpServerHealthRegistry.record_failure()` and its callers (`scripts/shared/mcp_health.py`). For all transport failures `request_id=""` is set because the request did not complete normally. For tool-level errors (HTTP 200 and `is_error=True`), the actual server `request_id` is used and `record_success()` is called.

---

## dispatch_tool helper (`scripts/mcp_servers/dispatch.py`)

Servers route calls through the shared `dispatch_tool(dispatch_table, name, args)` helper (`scripts/mcp_servers/dispatch.py`), which returns `DispatchResult(output, is_error)`:

- Empty or whitespace `name` -> `"Tool name must be a non-empty string"`, `is_error=True`
- Unknown `name` -> `"Unknown tool: <name>"`, `is_error=True`
- `ValueError` from a handler -> `"Validation error: <e>"`, `is_error=True`
- Other exceptions propagate to the caller

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
