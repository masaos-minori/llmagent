---
title: "MCP Protocol and Transport: Startup Modes, Authentication, and Health Checks"
area: mcp
tags:
  - mcp
  - startup-modes
  - health-checks
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_03_transport-and-health.md
---
# MCP Protocol and Transport: Startup Modes, Authentication, and Health Checks

## HTTP Startup Modes

| Aspect | `persistent` Mode | `subprocess` Mode |
|---|---|---|
| Process Management | Managed externally (existing process) | Starts uvicorn when the agent starts |
| Request Format | POST to `/v1/call_tool` | POST to `/v1/call_tool` |
| Concurrency | uvicorn async | uvicorn async |
| Session ID Header | `X-Session-Id` | `X-Session-Id` |
| Tool List Check | `GET /v1/tools` | `GET /v1/tools` |
| Health Check | `GET /health` | Polls `/health` at startup |

---

### Standard `/health` Response Semantics

All MCP server `/health` endpoints follow consistent semantics for response fields.

**`status`**: `"ok"` if fully healthy, `"degraded"` if dependency failures are detected.

**`ready`**: `true` if there are no dependency failures, `false` otherwise.

**`liveness`**: Defaults to `true` (base class); subclasses can override it to indicate critical internal states where the process cannot accept requests.

**`restart_recommended`**: Setting this to `true` indicates that restarting the process may resolve the issue; `false` means a restart will not help. No live consumer acts on this field today — the MCP watchdog that once did was removed 2026-07-16; the field is surfaced read-only via `/mcp status`.

**Note (Current Implementation):** In the current codebase, all 10 MCP server `/health` implementations (those using `scripts/mcp_servers/health_response.py::make_health_response()` and custom implementations for `mdq`/`file-read`/`write-delete`) always return `False` for `restart_recommended`. The base implementation of `MCPServer.health()` also has a fixed `False`. There is no code path that returns `restart_recommended=True` (Explicit in code). Therefore, currently, no automatic restart occurs regardless of this field's value today, while all current implementations return `False` for `restart_recommended` (Explicit in code).

**`operator_action_required`**: `true` if human intervention is required (e.g., missing credentials, missing binaries). This field is surfaced via `/mcp status`; no automated action is taken.

**Note:** The `make_health_response()` helper mechanically sets `operator_action_required = not ready` (it is always `True` if `deps` is non-empty). Thus, for servers using this helper, any dependency failure resulting in `ready=False` is treated as `operator_action_required=True`, making them effectively linked (Explicit in code). Conversely, the base implementation of `MCPServer.health()` has `operator_action_required` fixed at `False`.

**`dependencies`**: A dictionary mapping dependency names to error messages. Empty if healthy.

**`details`**: Server-specific supplementary information (e.g., `sandbox_backend`, `service`). Empty dict if not applicable.

**HTTP Status Codes**:
- `200` if `status="ok"` and `ready=true` (fully healthy)
- `503` if `status="degraded"` or `ready=false` (dependency failure)

**Dependency Values**: Any non-empty dependency value (`"not configured"`, `"not_set"`, `"check failed"`, etc.) constitutes a degraded state — a server is not healthy until all dependencies are satisfied. These values are not just informational; they always indicate an actual missing or failed dependency.

**Interpretation in `/mcp status`**: `McpStatusService.probe_all()` (`agent/services/mcp_status.py`) reads the HTTP status code and the `restart_recommended`/`operator_action_required` fields from the body and reflects them in the `health_reason` column of `/mcp status`. This is a display-only operation and does not trigger automatic restarts or change server states (Explicit in code).
- Reflected in `health_reason` if `reachable=False` (no HTTP response) or `restart_recommended=true`.
- Reflected in `health_reason` as `operator_action_required` if `operator_action_required=true`.
- `HealthRegistry.record_degraded(server_key, reason=...)` in the tool execution layer is called via a different path (`dispatch` result in `shared/tool_executor.py`) (currently a no-op for `UNAVAILABLE`/`HALF_OPEN` cases)

Automatic restarts (formerly MCP watchdog) were removed on 2026-07-16. For details and manual recovery procedures, see [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md).

**Healthy Response Example**:
```json
{
  "status": "ok",
  "ready": true,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": false,
  "dependencies": {},
  "details": {}
}
```

**Degraded Response Example** (`operator_action_required=true` — missing credentials, no restart):
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {
    "github_token": "not_set"
  },
  "details": {}
}
```

---

## Bearer Authentication

If `McpServerConfig.auth_token` is not empty:
- **Server-side**: `attach_auth_middleware(app, token)` registers middleware and validates `Authorization: Bearer <token>`. Mismatched requests receive an HTTP 401.
- **Client-side**: `HttpTransport` injects `Authorization: Bearer <token>` into all POST requests.
- If `auth_token` is empty: Authentication checks are skipped; only `X-Request-Id` injection is active.

---

## Response Truncation

If the result exceeds 512 KB:
``` text
[TRUNCATED: {total:,} bytes total, showing {actual_visible:,} bytes]
```

- `total_bytes` = original byte count (before truncation)
- `actual_visible_bytes` = bytes actually displayed (may be less than 512 KB if a multi-byte UTF-8 character falls on the truncation boundary)
- Implemented via the metadata-aware truncation method in `mcp_servers/server.py`

**Note:** The suffix shows the `actual_visible_bytes`, not the set limit. For ASCII text, this is exactly 512 KB (524,288 bytes). For UTF-8 text containing multi-byte characters at the boundary, it may be slightly less.

**Important:** The `total_bytes` and `actual_visible_bytes` fields in the HTTP response metadata represent the size of the *original* dispatch output, not the truncated text itself. This allows clients to distinguish between short responses that do not require truncation and long responses that have been truncated.

---

## Server-Specific Health Response Fields

| Server | `/health` Override |
|---|---|
| web-search-mcp | No overrides (returns `{"status":"ok","ready":true}`) |
| github-mcp | `dependencies.github_token` (`"not_set"`) |
| mdq-mcp | `details.service: "mdq-mcp"`, `details.document_count`, `details.chunk_count`, `details.fts_row_count`, `details.last_indexed`, `details.stale_document_count`; checks `documents`, `chunks`, `chunks_fts` tables and triggers `chunks_ai/ad/au`; stale detection via `documents.mtime_ns` (nanoseconds) |
| shell-mcp | `dependencies.shell` (`"sh not found in PATH"`/`"check failed"`); `details.sandbox_backend` (`"firejail"` or `"none"`) |
| file-read-mcp | `dependencies.filesystem` (`"/workspace is not a directory"`/`"check failed: <error>"`) |
| file-write-mcp | `dependencies.filesystem` (`"/workspace is not a directory"`/`"check failed: <error>"`) |
| file-delete-mcp | `dependencies.filesystem` (`"/workspace is not a directory"`/`"check failed: <error>"`) |
| rag-pipeline-mcp | `dependencies` (`embed_url: "not configured"` / `config: "check failed"`) |
| git-mcp | `dependencies.git` (`"git not found in PATH"`/`"check failed"`) |
| cicd-mcp | `dependencies` (`github_token: "not_set"` / `config: "check failed"`) |

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_02_01_endpoints-and-transport.md`
- `04_mcp_02_03_audit-logging-and-errors.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

## Keywords

mcp
protocol
transport
auth
bearer
health
truncation
repl_health
