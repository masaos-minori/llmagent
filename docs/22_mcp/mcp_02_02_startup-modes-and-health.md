---
title: "MCP Protocol and Transport: Startup Modes, Authentication, and Health Checks"
area: mcp
tags:
  - mcp
  - startup-modes
  - health-checks
related:
  - mcp_00_document-guide.md
  - mcp_03_03_transport-and-health.md
  - mcp_06_07_mcp-failure-diagnosis.md
  - mcp_05_05_mdq-enforcement-and-lockdown.md
---
# MCP Protocol and Transport: Startup Modes, Authentication, and Health Checks

## HTTP Startup Modes

Both modes use the same wire contract (POST `/v1/call_tool`, `X-Session-Id` header, `GET /v1/tools` for the tool list check, `GET /health`). They differ only in process ownership: `persistent` connects to an externally managed server, while `subprocess` makes the agent start uvicorn and poll `/health` until ready at startup.

---

### Standard `/health` Response Semantics

All MCP server `/health` endpoints follow consistent semantics for response fields.

**`status`**: `"ok"` if fully healthy, `"degraded"` if dependency failures are detected.

**`ready`**: `true` if there are no dependency failures, `false` otherwise.

**`liveness`**: Defaults to `true` (base class); subclasses can override it to indicate critical internal states where the process cannot accept requests.

**`restart_recommended`**: Setting this to `true` indicates that restarting the process may resolve the issue; `false` means a restart will not help. No live consumer acts on this field today; it is surfaced read-only via `/mcp status`.

No health implementation returns `restart_recommended=True` (base class and all 10 servers, `scripts/mcp_servers/health_response.py::make_health_response()` included), so no automatic restart occurs regardless of this field.

**`operator_action_required`**: `true` if human intervention is required (e.g., missing credentials, missing binaries). This field is surfaced via `/mcp status`; no automated action is taken.

The `make_health_response()` helper sets `operator_action_required = not ready`, so any dependency failure that makes a server not ready is also reported as operator action required. The base `MCPServer.health()` fixes it at `False`.

**`dependencies`**: A dictionary mapping dependency names to error messages. Empty if healthy.

**`details`**: Server-specific supplementary information (e.g., `sandbox_backend`, `service`). Empty dict if not applicable.

**`security`**: Security Posture block. Every MCP server validates its own security settings at startup and publishes the result here, so the key is present in all 10 server responses. `ready` requires `security.validated` in addition to an empty `dependencies` dict. The block carries exactly these keys:

| Key | Meaning |
|---|---|
| `contract_version` | Version of the posture contract the block conforms to |
| `server_key` | Server key the posture belongs to; matches the `[mcp_servers.<key>]` section |
| `policy_version` | Version of that server's own check policy |
| `validated` | `true` when no check reported `failed` |
| `ready` | Mirrors `validated`; a posture is never ready without validation |
| `fingerprint` | 64-character lowercase hex digest over the server's non-secret security settings (scalars and counts only) |
| `checks` | Ordered list of that server's checks; each entry carries `id`, `status`, `reason_code`, `message` |

`status` is one of `ok`, `warning`, `failed`, `not_applicable`. Only `failed` blocks `validated`. `warning` is reported and the server still binds. `not_applicable` means the check does not apply to that server and is never treated as a failure. Check messages carry setting names and counts, never secrets, allowlist entries, or absolute paths.

The Agent reads this block during startup readiness and MCP tool discovery. A `failed` check blocks Agent startup regardless of the server's `required` classification; see [ADR-004](../10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md). A server whose posture is not validated refuses to bind its HTTP port.

**HTTP Status Codes**:
- `200` if `status="ok"` and `ready=true` (fully healthy)
- `503` if `status="degraded"` or `ready=false` (dependency failure, or a security posture that did not validate)

**Dependency Values**: Any non-empty dependency value (`"not configured"`, `"unreachable"`, `"not_set"`, `"check failed"`, etc.) constitutes a degraded state — a server is not healthy until all dependencies are satisfied. These values are not just informational; they always indicate an actual missing or failed dependency. `"unreachable"` (used by `rag-pipeline-mcp` for `dependencies.embed_url`) means the endpoint is configured but the reachability probe could not confirm it; it carries the same degraded response shape (HTTP 503, `ready:false`, `liveness:true`) as the other values.

**Interpretation in `/mcp status`**: `McpStatusService.probe_all()` (`agent/services/mcp_status.py`) reads the HTTP status code and the `restart_recommended`/`operator_action_required` fields from the body and reflects them in the `health_reason` column of `/mcp status`. This is display-only and does not trigger automatic restarts or change server states.
- Reflected in `health_reason` as the body `reason` (fallback `message`) string when present, or as `restart_recommended` when `restart_recommended=true` and no body reason exists.
- Reflected in `health_reason` as `operator_action_required` if `operator_action_required=true` and no body reason exists.
- `McpServerHealthRegistry` (`shared/mcp_health.py`) is updated by the tool execution layer through a different path (`record_failure()`/`record_success()` from `ToolTransportInvoker`); it does not store a degraded reason.

There is no automatic restart of MCP servers. For manual recovery procedures, see [mcp_06_07_mcp-failure-diagnosis.md](mcp_06_07_mcp-failure-diagnosis.md).

A healthy response has `status="ok"`, `ready=true`, empty `dependencies`, and a validated `security` block. A degraded response (for example github-mcp with `dependencies.github_token="not_set"`) has `status="degraded"`, `ready=false`, and `operator_action_required=true`, with no restart recommended.

---

## Bearer Authentication

Every HTTP MCP server MUST have a non-empty `McpServerConfig.auth_token`; Agent startup rejects an enabled HTTP server whose `auth_token` is empty. This also applies to mdq-mcp, whose server verifies the Bearer token like every other HTTP MCP server (see `mcp_05_05_mdq-enforcement-and-lockdown.md`). With a non-empty token:
- **Server-side**: `attach_auth_middleware(app, token)` registers middleware and validates `Authorization: Bearer <token>`. Mismatched requests receive an HTTP 401.
  - Every HTTP MCP server registers this middleware and enforces the configured Bearer token (see `mcp_06_14_mcp-authentication-setup.md`).
- **Client-side**: `HttpTransport` injects `Authorization: Bearer <token>` into all POST requests.
- Empty server-side token (a standalone test run only): `attach_auth_middleware()` skips the authentication check and only injects `X-Request-Id`; the shell, github, file, and mdq servers refuse to start with an empty token.

---

## Response Truncation

If the result exceeds the response size limit (`MCP_MAX_RESPONSE_BYTES`):
``` text
[TRUNCATED: {total:,} bytes total, showing {actual_visible:,} bytes]
```

- `total_bytes` = original byte count (before truncation)
- `actual_visible_bytes` = bytes actually displayed (may be less than the limit if a multi-byte UTF-8 character falls on the truncation boundary)
- The suffix shows `actual_visible_bytes`, not the configured limit; the two differ only when a multi-byte UTF-8 character straddles the boundary.
- `total_bytes` and `actual_visible_bytes` in the HTTP response metadata describe the *original* dispatch output, not the truncated text. This allows clients to distinguish between short responses that do not require truncation and long responses that have been truncated.

---

## Server-Specific Health Response Fields

Every server reports unmet prerequisites through `dependencies` (a non-empty value means degraded). Server-specific content:

| Server | `/health` content |
|---|---|
| web-search-mcp | `details.provider`, `details.browser_provider`; `browser_fetch` state is reported separately from `search_web` |
| github-mcp, cicd-mcp | `dependencies.github_token` when the token is missing |
| mdq-mcp | `details` with document, chunk, and FTS row counts, last indexed time, and stale document count (stale detection via `documents.mtime_ns`); verifies the `documents`, `chunks`, `chunks_fts` tables and their sync triggers |
| shell-mcp | `dependencies.shell` when `sh` is not found; `details.sandbox_backend` (`firejail` or `none`) |
| file-read/write/delete-mcp | `dependencies.filesystem` when the workspace root is not a directory |
| rag-pipeline-mcp | `dependencies.embed_url` is `"not configured"` (embedding URL unset), `"unreachable"` (embedding URL configured but the reachability probe fails), or `dependencies.config` is `"check failed"` (failed config check) |
| git-mcp | `dependencies.git` when `git` is not found |

---

## Keywords

- mcp
- protocol
- transport
- auth
- bearer
- health
- truncation
- repl_health
