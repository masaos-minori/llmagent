---
title: "Transport Error Tracing and Lifecycle Flow"
area: mcp
tags:
  - mcp
  - tracing
  - lifecycle
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_03_transport-and-health.md
  - 04_mcp_03_03_transport-and-health.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
---

# Transport Error Tracing and Lifecycle Flow

> **Note:** Due to historical reasons, the filename contains the word `watchdog`, but the MCP watchdog (automatic health polling / automatic restart loop) was removed on 2026-07-16. For details, see [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md).

## Example Failure Path (Transport Error)

``` text
1-2. Same as above.

3. MCP server unreachable (timeout / 5xx):
   HttpTransport raises TransportError.

4. Agent:
   Transport error handler records the error for "file_read"
   → stat_transport_errors["file_read"] += 1
   → HealthRegistry.record_failure("file_read") → state: HEALTHY → DEGRADED

5. ToolCallResult:
   (output=str(error), is_error=True, server_key="file_read", error_type="transport")

6. audit_tool_exec():
    audit log (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"","is_error":true,"error_type":"transport","ts":...}
    Note: mcp_request_id="" because no response was received.

7. Next real tool call to "file_read" (internal dispatch):
   ensure_ready() attempts recovery (subprocess mode only), then dispatch proceeds.
   → if the call succeeds: HealthRegistry.record_success("file_read") → HALF_OPEN → HEALTHY
   → if it fails again: HealthRegistry.record_failure("file_read") → DEGRADED → UNAVAILABLE
   No background poller retries this automatically; see
   04_mcp_06_12_watchdog-configuration-monitoring.md for the removed watchdog.
```

---

### Difference between Tool Errors and Transport Errors in Tracing

| Field | Tool Error | Transport Error |
|---|---|---|
| `is_error` | `True` | `True` |
| `error_type` | `"tool"` | `"transport"` |
| `mcp_request_id` | Set (server responded) | `""` (no response received) |
| `HealthRegistry` | `record_success()` (server responded) | `record_failure()` (unable to reach server) |
| `stat_tool_errors` | Incremented | No change |
| `stat_transport_errors` | No change | Incremented |

A tool error means the server processed the request but returned an error. A transport error means the agent never received a response from the server.

For operational tracing procedures, see [04_mcp_06 End-to-End Tool Call Tracing](04_mcp_06_08_end-to-end-tool-call-tracing.md#end-to-end-tool-call-tracing).

---

## Lifecycle Flow

For behavior regarding tool definition startup validation, see `04_mcp_06` Startup Validation Behavior.

``` text
AgentREPL.run()
  → MCP server startup
       → startup_mode="subprocess" (http): start_http_subprocess() + health poll
            stderr → /opt/llm/logs/scripts/mcp_servers/{server_key}.stderr.log (append mode)
       → startup_mode="persistent" (http): no lifecycle action needed
       → startup_mode="none": no subprocess spawn, no health check — server is disabled
    → [REPL loop]
    → tool call → ToolExecutor raw execute
         → startup_mode="none" rejects immediately
              with a "disabled" tool error, before health check or transport
             → ensure_ready(server_key):
                  if _shutting_down: return immediately (shutdown guard)
                  if subprocess-mode and not running: start() [auto-restart on demand]
    → finally: lifecycle.shutdown_all()
             sets _shutting_down=True (blocks further start/restart calls)
           + close stderr log file handles
           + AsyncClient.close()
```

`_ServerLifecycleRouter._shutting_down` protects `ensure_ready()`, `start_http_subprocess()`, `restart()`, and `shutdown_idle()`: once `shutdown_all()` is called, these methods return immediately after logging a line, without delegating to `HttpServerLifecycleManager`.

### Implementation Note (Double SIGINT Guard)

`HttpServerLifecycleManager.shutdown_all()` (`agent/http_lifecycle.py`) temporarily swaps the signal handler to `_absorb_sigint_during_shutdown()` during cleanup, absorbing subsequent SIGINTs as WARNING logs (since calling `signal.signal()` from outside the main thread would raise a `ValueError`, it continues without guards). This is intended to prevent orphan subprocesses if a user presses Ctrl-C twice while waiting for connections to close. The original handler is restored once cleanup is complete. (Explicit in code)

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_03_transport-and-health.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

## Keywords

mcp
tool error
transport error
lifecycle flow
health check
restart
