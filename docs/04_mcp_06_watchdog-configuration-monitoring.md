---
title: "Watchdog Behavior — Configuration and Monitoring"
category: mcp
tags:
  - mcp
  - watchdog
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration-file-inventory.md
source:
  - 04_mcp_06_configuration-file-inventory.md
---

# Watchdog Behavior — Configuration and Monitoring


## Watchdog Behavior

The watchdog loop (`watchdog_loop()` in `agent/repl_health.py`) periodically probes all MCP
servers and attempts to restart them when they fail. It runs as a background asyncio task.

**Note:** The watchdog's periodic `record_success()`/`record_failure()` calls supplement (but do not replace) the per-call HealthRegistry updates from the tool execution layer. Each tool call increments its own failure count independently of the watchdog.

#### Process snapshot integration in status display

When `_probe_single_server()` executes via McpStatusService.probe_all(), it integrates lifecycle introspection data into each row:

```python
snapshot_fn = getattr(lifecycle, "get_process_snapshot", None)
snapshot = snapshot_fn(key) if snapshot_fn else None

# PID column shows actual process ID if managed by this agent
pid_display = str(snapshot.get("pid")) if snapshot else "-"

# LIFECYCLE column combines two sources:
lifecycle_state = lifecycle.get_transport_state(key).value   # RUNNING/STARTING/etc.
restart_rec_http = probe_result.restart_recommended          # HTTP endpoint flag
restart_recommended = (lifecycle_state == FAILED.value) or restart_rec_http
operator_action_required = op_action_http                    # Only from HTTP endpoint
health_reason = body_reason                                   # Priority-derived reason string
```

This means that even without calling the `/health` endpoint directly, you can determine whether a subprocess-mode server has been marked as FAILED due to prior transport failures during tool dispatch—visible both through the LIFECYCLE state and the derived `restart_recommended` field.



### Configuration

| Setting | LOCAL default | PRODUCTION default | Effect |
|---|---|---|---|
| `mcp_watchdog_interval` | `0` (disabled) | `30.0` | Probe interval in seconds; `0` = disabled |
| `mcp_watchdog_max_restarts` | `3` | `3` | Max restart attempts per server before giving up |



### Disabled state consequences

When `mcp_watchdog_interval = 0`:
- The watchdog loop still starts but logs a warning: `Watchdog: disabled (interval=0) — failed servers will not be auto-restarted`
- Crashed HTTP servers will remain unreachable until the agent process is restarted manually
- Crashed subprocess servers (shell-mcp) will not be restarted automatically



### Recommended values and operational impact

| Profile | `mcp_watchdog_interval` | Rationale |
|---|---|---|
| LOCAL development | `0` (disabled) | Manual restart is acceptable during development; avoids unnecessary log noise |
| PRODUCTION | `30.0` | Balances detection speed against probe overhead; frequent enough to catch crashes within 30s |

**Setting `mcp_watchdog_interval` too low (< 10s):**
- Increased probe overhead across all MCP servers
- More frequent log entries for transient failures
- May cause rapid restart loops for servers with slow recovery

**Setting `mcp_watchdog_interval` too high (> 120s):**
- Delayed detection of server failures
- Longer periods of degraded service before auto-restart
- Extended downtime for critical MCP servers between crash and recovery

**General guidance:** Keep `mcp_watchdog_interval` between 15–60 seconds for production. Values outside this range should only be used with explicit justification.



### Verifying watchdog state

Two places show the current watchdog state:

1. **Startup logs** (`/opt/llm/logs/agent.log`):
   ```
   INFO  Watchdog: enabled (interval=30s, max_restarts=3)
   ```
   or
   ```
   WARNING Watchdog: disabled (interval=0) — failed servers will not be auto-restarted
   ```

2. **`/mcp status` command** (REPL):
   ```
   Watchdog    enabled (interval=30s, max_restarts=3)
   ```
   or
   ```
   Watchdog    disabled (interval=0) — no auto-restart
   ```


## Related Documents

- [04_mcp_06_configuration-file-inventory.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

watchdog
configuration
monitoring
