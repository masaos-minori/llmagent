# End-to-End Tool Call Tracing

To trace a failed tool call through agent, transport, and server logs, follow these steps:

1. Find the `mcp_request_id` in the agent-side audit log:
    ```bash
    jq 'select(.mcp_request_id == "<id>")' /opt/llm/logs/audit.log
    ```
2. Search for the same `request_id` field in the MCP server's audit log (JSON-lines format):
    ```bash
    jq 'select(.request_id == "<id>")' /opt/llm/logs/audit.log
    ```
3. Search for the `X-Request-Id` response header in the specific server logs:
    ```bash
    grep "<id>" /opt/llm/logs/github-mcp.log  # or relevant server log
    ```
4. Check the health status of the `server_key` at that time in `/opt/llm/logs/agent.log`.
5. If the health status has changed: check the current DEGRADED/UNAVAILABLE state and `health_reason` via `/mcp status`. Note that automatic restarts are not performed (for subprocess-mode servers, `ensure_ready()` will only attempt a restart during the next tool dispatch).

---

## Error Type Distinction in Audit Logs (Agent Side)

**Regarding cross-layer correlation:** Per-server audit logs (`github_audit.log`, `shell_audit.log`, `delete_audit.log`) do not contain correlation fields like `X-Session-Id` or `X-Request-Id`. Correlation between these logs must be established using the agent-side audit log as the reference.

The agent-side audit event includes an `error_type` field:

| error_type | Meaning | Example Cause |
|---|---|---|
| `transport` | Unable to reach MCP server (network failure, timeout, crash) | Server process stopped, port not listening, HTTP 5xx |
| `tool` | Reachable, but tool returned `is_error=true` | Tool validation failed, database constraint violation |
| _(empty)_ | Execution successful | — |

Example audit log line:
```json
{"event":"tool_exec","tool":"shell_run","is_error":true,"error_type":"transport",...}
```

Filter by error type:
```bash
# Transport failures (server issues)
grep '"error_type":"transport"' /opt/llm/logs/audit.log

# Tool-level failures (business logic errors)
grep '"error_type":"tool"' /opt/llm/logs/audit.log
```

## Per-Server Error Counters

`ToolExecutor` maintains per-server error counters, which can be inspected via `ToolExecutor.get_error_counters()`:

```python
{
    "shell-mcp": {"transport": 2, "tool": 5},
    "github-mcp": {"transport": 0, "tool": 1},
}
```

These counters are kept in memory only (not persisted) and are reset upon agent restart.

## Detecting Repeated Failures

If a tool fails 3 or more times within a 5-minute sliding window, a warning is logged:

``` text
WARNING: Repeated tool failures detected: shell_run failed 3 times in 300s window
```

> **Note:** `McpServerHealthRegistry` (`shared/mcp_health.py`) only tracks transport availability. Tool-layer errors (`error_type=tool`) do not affect the HealthRegistry state — only transport failures (`error_type=transport`) affect the server's health state.

---

## Serialization of Side Effects

When a round contains tools with side effects (write operations), the scheduler groups them together to prevent concurrent modifications. This is intentional behavior for safety, though it reduces concurrency.

**Serialization Triggers:**

| Trigger | Condition | Effect |
|---|---|---|
| `requires_serial` | `requires_serial=true` is set in tool metadata | The tool is executed alone as a single-element group |
| `resource_scope_conflict` | Multiple tool calls have overlapping `resource_scopes` (exact match, or filesystem scope ancestor/descendant relationship) | All tool calls with overlapping scopes are executed serially |
| `is_write_overlap` | Multiple writes without a specific scope | All write-type tools are grouped together (write-first) |

**Log Format:**
``` yaml
ROUND_SERIALIZATION: triggered by shell_run (requires_serial) — 1 tools serialized in this round
Serialization impact: 3 tools grouped serially (normally would run in parallel)
```

**How to check statistics:**
Running `/mcp` displays serialization statistics at the end of the MCP status output.

**Why this information is important:**
While serialization reduces concurrency, it prevents race conditions on shared resources. Before attempting to optimize concurrency, check the serialization logs to identify which tools and scopes are most frequently causing grouping.

---



## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
