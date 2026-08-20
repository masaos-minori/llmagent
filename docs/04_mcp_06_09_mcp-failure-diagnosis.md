# MCP Failure Diagnosis

To track failed or unexpected MCP tool calls, use the following flow:

``` text
1. Was the request delivered to the server?
   NO  → Transport failure (error_type="transport" in agent-side audit log). See §Error Type Distinction.
   YES → continue

2. Did the tool return an error response (is_error=true)?
   YES → Tool-level error (error_type="tool" in agent-side audit log). See §Error Type Distinction.
   NO (timeout or silent fail) → continue

3. Has server health status changed?
   YES → Check `/mcp status` for the current DEGRADED/UNAVAILABLE state and health_reason.
   NO  → continue

4. Has the circuit breaker tripped (UNAVAILABLE)?
   YES → No automatic restart will happen (the MCP watchdog was removed on 2026-07-16;
          see [04_mcp_06_12_watchdog-configuration-monitoring.md](./04_mcp_06_12_watchdog-configuration-monitoring.md)). Manual recovery required —
          either wait for the next tool call to trigger `ensure_ready()`, or restart the
          server/agent process manually.
   NO  → Check serialization. See §Serialization in Tool Execution.
```

For correlation analysis across agent, transport, and server logs, see [04_mcp_03 §End-to-End Tool Call Tracing](./04_mcp_03_03_transport-and-health.md#end-to-end-tool-call-tracing).

## Failure mode: LLM sees tool but execution fails

**Symptoms:**
- LLM proposes a valid tool call using a known tool name
- Execution fails with "Unknown tool" error despite the tool name being valid

**Root cause:**
- `RuntimeToolRegistry` is missing entirely during runtime
- Tools may exist in MCP server catalogs but are not registered in the runtime registry
- This creates a mismatch: LLM knows about the tool (from discovery), but the router cannot find it

**Diagnostic steps:**
1. Check if `RuntimeToolRegistry` was initialized successfully at startup
2. Verify no errors during tool registration phase
3. Confirm all expected MCP servers have completed their tool discovery
4. Review startup logs for any tool registration failures

**Resolution:**
- Restart the agent process to re-initialize `RuntimeToolRegistry`
- If persistent, investigate MCP server connection issues that may prevent tool registration

See also: Two-stage tool resolution (LLM visibility vs runtime routability)

## `ensure_ready` behavior during tool dispatch

When a tool call arrives via the internal dispatch path:

```python
# In agent/factory.py _ServerLifecycleRouter.ensure_ready():
if _shutting_down: return immediately          # shutdown guard
cfg.transport != HTTP or cfg.startup_mode != SUBPROCESS: return immediately  # non-subprocess servers skip this check
not http_mgr.verify_running(server_key):      # subprocess-mode, not running -> start!
    set_state(LifecycleState.STARTING)         # optimistic state before starting
    await http_mgr.start(server_key, cfg)       # spawn subprocess, poll /health
    set_state(LifecycleState.RUNNING)           # success
except Exception:                               # any startup failure
    set_state(LifecycleState.FAILED)           # mark as failed for subsequent attempts
    raise                                       # propagate up so caller sees the failure
```

In other words, even if a server repeatedly crashes, individual tool calls that have not yet reached their own circuit-break threshold can attempt recovery through `ensure_ready()`. This is currently the only automatic recovery path (periodic polling + automatic restart by the old MCP watchdog was removed on 2026-07-16. See [04_mcp_06_12_watchdog-configuration-monitoring.md](./04_mcp_06_12_watchdog-configuration-monitoring.md)).

**Implementation Note (Explicit in code):** `ensure_ready()` is not in `shared/tool_executor.py`; it is implemented in the `_ServerLifecycleRouter` class in `agent/factory.py`. Actual subprocess startup/shutdown is delegated to `HttpServerLifecycleManager` in `agent/http_lifecycle.py`. `ToolExecutor` only calls this router via `LifecycleProtocol` (`shared/tool_lifecycle.py`) and does not hold the startup logic itself.

---

**Appropriate cases for restart:** When health status transitions to `FAILED` + repeated transport errors within the threshold, or after successful `ensure_ready()` following a subprocess crash.

**Inappropriate cases for restart:** Single tool errors, one-off timeouts, or delays caused by serialization.

## Circuit Breaker in Tool Execution Layer (`McpServerHealthRegistry`)

`McpServerHealthRegistry` in `shared/mcp_health.py` is an independent circuit breaker that tracks consecutive failures per server and gates dispatching.

- `record_failure()` increments the failure count; when it reaches `failure_threshold` (default 3), the state becomes `UNAVAILABLE`.
- `is_unavailable()` is not just a simple getter. After transitioning to `UNAVAILABLE`, once `half_open_cooldown_sec` (default 30 seconds) has passed, it transitions to `HALF_OPEN` without notifying the caller, allowing exactly one trial call (which returns `False`).
- A failure during `HALF_OPEN` immediately reverts the state to `UNAVAILABLE` and resets the cooldown.
- `record_success()` restores the state to `HEALTHY` and clears the failure count and degraded reason.

The `[mcp_servers.*].tool_names` does not affect the circuit breaker state or routing — it is merely reference information and not an input for routing (consistent with [04_mcp_06_03](./04_mcp_06_03_tool_schema_export_policy.md)).

Basis: Explicit in code (`shared/mcp_health.py`). Health checks within the `ToolExecutor` execution process act as a gate before dispatching.

### LLM called a tool, but execution failed with Unknown tool

**Possible causes:**
- RuntimeToolRegistry is missing or incomplete
- Discovery was FATAL, WARNING, or SKIPPED
- Duplicate tool name detection excluded the tool
- ToolExecutor.set_runtime_registry() was not called

**Diagnosis steps:**
1. Check startup output for `mcp_tool_discovery` outcomes
2. Check whether discovery was FATAL, WARNING, or SKIPPED
3. Check whether the owning server's `/v1/tools` response includes the tool
4. Check whether duplicate tool name detection excluded the tool
5. Check whether ctx.services_required.runtime_tools was populated
6. Check whether ToolExecutor.set_runtime_registry() was called
7. Check whether the tool exists in RuntimeToolRegistry
8. Do not rely only on config/agent.toml tool_definitions

**Root cause explanation:**
The "Unknown tool" error originates from `ToolRouteResolver.resolve()` which raises `ValueError` when a tool name is not found in `RuntimeToolRegistry`. This can happen even when the LLM sees the tool via `/v1/tools` because `RuntimeToolRegistry` may be incomplete due to discovery failures.

## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)

## Keywords

configuration
