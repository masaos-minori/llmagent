# Design: Document new monitoring fields in ops doc

## Goal
Document transport vs tool error distinction, per-server counter format, and repeated failure detection in `docs/04_mcp_06_configuration_and_operations.md`.

## Target File
- `docs/04_mcp_06_configuration_and_operations.md`

## Current State (lines 200-235)
- "Reading Audit Logs" section describes log file paths and grep patterns
- No mention of error_type, per-server counters, or repeated failure detection
- "Settings with High Operational Impact" covers allowlists and safety settings only

## Implementation Steps

### Step 1: Add new section after "Reading Audit Logs" (before line 237)

Insert new subsection under "Reading Audit Logs":

```markdown
### Error Type Distinction in Audit Logs

Tool execution audit events now include an `error_type` field:

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
    ...
}
```

These counters are in-memory (not persisted) and reset on agent restart. They track errors within the current agent process lifetime.

### Repeated Failure Detection

When a tool fails 3+ times within a 5-minute sliding window, a warning is logged:

```
WARNING: Repeated tool failures detected: shell_run failed 3 times in 300s window
```

This helps operators distinguish between transient issues and systemic problems requiring intervention.
```

### Step 2: Add monitoring-related entry to "Settings with High Operational Impact" table (line 240)

Add row after `mcp_watchdog_interval`:
| `error_type` in audit logs | Distinguishes transport failures from tool errors for operator debugging |

### Step 3: Update "Watchdog Behavior" section

Add note about interaction between watchdog and error counters:
> **Note:** The watchdog monitors transport availability (health checks). Tool-level errors (`error_type=tool`) do not trigger watchdog restarts — only transport failures (`error_type=transport`) affect server health state.

## Completion Criteria
- New monitoring fields documented in ops doc
- Error type table explains transport vs tool distinction
- Per-server counter format documented
- Repeated failure detection threshold documented (3 failures / 5 min)
