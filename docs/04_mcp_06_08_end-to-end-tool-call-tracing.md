---
title: "End-to-End Tool Call Tracing"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# End-to-End Tool Call Tracing

## End-to-End Tool Call Tracing

To trace a failed tool call across agent, transport, and server logs:

1. Find the `mcp_request_id` in the agent-side audit log:
    ```bash
    jq 'select(.mcp_request_id == "<id>")' /opt/llm/logs/audit.log
    ```
2. Search MCP server audit log for the same `request_id` field (JSON-lines format):
    ```bash
    jq 'select(.request_id == "<id>")' /opt/llm/logs/audit.log
    ```
3. Search per-server log for the `X-Request-Id` response header:
    ```bash
    grep "<id>" /opt/llm/logs/github-mcp.log  # or relevant server log
    ```
4. Check health state for `server_key` at that timestamp in `/opt/llm/logs/agent.log`.
5. If health changed: check watchdog actions log for restart/failover.

---

### Error Type Distinction in Audit Logs (Agent-Side)

Agent-side audit events include an `error_type` field:

| error_type | Meaning | Example cause |
|---|---|---|
| `transport` | MCP server unreachable (network failure, timeout, crash) | Server process died, port not listening, HTTP 5xx |
| `tool` | MCP server reachable but tool returned is_error=true | Tool validation failed, database constraint violation |
| _(empty)_ | Successful execution | — |

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

### Per-Server Error Counters

`ToolExecutor` maintains per-server error counters accessible via `ToolExecutor.get_error_counters()`:

```python
{
    "shell-mcp": {"transport": 2, "tool": 5},
    "github-mcp": {"transport": 0, "tool": 1},
}
```

These counters are in-memory (not persisted) and reset on agent restart.

### Repeated Failure Detection

When a tool fails 3+ times within a 5-minute sliding window, a warning is logged:

```
WARNING: Repeated tool failures detected: shell_run failed 3 times in 300s window
```

> **Note:** The watchdog monitors transport availability (health checks). Tool-level errors (`error_type=tool`) do not trigger watchdog restarts — only transport failures (`error_type=transport`) affect server health state.

---

### Side-Effect Serialization

When a round contains side-effect tools (write operations), the scheduler groups them to prevent concurrent modifications. This is intentional for safety but reduces parallelism.

**Serialization triggers:**

| Trigger | Condition | Effect |
|---|---|---|
| `requires_serial` | Tool metadata has `requires_serial=true` | Tool runs alone in its own single-element group |
| `resource_scope_conflict` | Multiple writes to same resource scope | All tools in that scope run serially |
| `is_write_overlap` | Multiple writes without specific scope | All write tools grouped together (write-first) |

**Log format:**
```
ROUND_SERIALIZATION: triggered by shell_run (requires_serial) — 1 tools serialized in this round
Serialization impact: 3 tools grouped serially (normally would run in parallel)
```

**Viewing stats:**
Run `/mcp` to see serialization statistics at the bottom of the MCP status output.

**Why this matters:**
Serialization reduces parallelism but prevents race conditions on shared resources. Before attempting to optimize parallelism, review serialization logs to understand which tools and scopes trigger grouping most frequently.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
