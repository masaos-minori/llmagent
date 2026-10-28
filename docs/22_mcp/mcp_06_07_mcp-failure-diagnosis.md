---
title: "MCP Failure Diagnosis"
area: mcp
tags:
  - mcp
  - diagnostics
  - troubleshooting
related:
  - mcp_06_01_configuration-file-inventory.md
  - mcp_03_03_transport-and-health.md
  - mcp_06_13_pre-production-fail-open-checklist.md
  - mcp_06_10_health-reasons-and-error-kinds.md
  - mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md
---
# MCP Failure Diagnosis

To track failed or unexpected MCP tool calls, use the following flow:

``` text
1. Was the request delivered to the server?
   NO  → Transport failure (error_type="transport" in agent-side audit log). See Error Type Distinction.
   YES → continue

2. Did the tool return an error response (is_error=true)?
   YES → Tool-level error (error_type="tool" in agent-side audit log). See Error Type Distinction.
   NO (timeout or silent fail) → continue

3. Has server health status changed?
   YES → Check `/mcp status` for the current DEGRADED/UNAVAILABLE state and health_reason.
   NO  → continue

4. Has the circuit breaker tripped (UNAVAILABLE)?
   YES → No automatic restart will happen. Manual recovery required —
          either wait for the next tool call to trigger `ensure_ready()`, or restart the
          server/agent process manually.
   NO  → Check serialization. See Serialization in Tool Execution.
```

For correlation analysis across agent, transport, and server logs, see [mcp_03 End-to-End Tool Call Tracing](./mcp_03_03_transport-and-health.md#end-to-end-tool-call-tracing).

## `ensure_ready` behavior during tool dispatch

When a tool call arrives via the internal dispatch path:

`ensure_ready()` returns immediately during shutdown and for non-subprocess servers. For a subprocess-mode server that is not running, it sets `STARTING`, spawns the subprocess and polls `/health`, then sets `RUNNING`; any startup failure sets `FAILED` and propagates to the caller.

In other words, even if a server repeatedly crashes, individual tool calls that have not yet reached their own circuit-break threshold can attempt recovery through `ensure_ready()`. This is currently the only automatic recovery path; there is no periodic polling or automatic restart loop.

Persistent-mode (non-HTTP-subprocess) MCP servers receive **no** automatic recovery of any kind — `ensure_ready()` returns immediately for them (`cfg.transport != TransportType.HTTP or cfg.startup_mode != StartupMode.SUBPROCESS`) — so recovery for a crashed persistent-mode server depends entirely on external process supervision (see [mcp_06_13_pre-production-fail-open-checklist.md](./mcp_06_13_pre-production-fail-open-checklist.md)'s restart-policy requirement). This explicitly contrasts with subprocess-mode's reactive-on-next-dispatch recovery described above.

**Enforcement point (Explicit in code):** `agent/lifecycle_router.py::_ServerLifecycleRouter.ensure_ready()`; `ToolExecutor` only calls it through `LifecycleProtocol`.

---

**Appropriate cases for restart:** When health status transitions to `FAILED` + repeated transport errors within the threshold, or after successful `ensure_ready()` following a subprocess crash.

**Inappropriate cases for restart:** Single tool errors, one-off timeouts, or delays caused by serialization.

## Circuit Breaker in Tool Execution Layer (`McpServerHealthRegistry`)

`McpServerHealthRegistry` in `shared/mcp_health.py` is an independent circuit breaker that tracks consecutive failures per server and gates dispatching.

- `record_failure()` increments the failure count; when it reaches `failure_threshold`, the state becomes `UNAVAILABLE`.
- `is_unavailable()` is not just a simple getter. After transitioning to `UNAVAILABLE`, once `half_open_cooldown_sec` has passed, it transitions to `HALF_OPEN` without notifying the caller, allowing exactly one trial call (which returns `False`).
- A failure during `HALF_OPEN` immediately reverts the state to `UNAVAILABLE` and resets the cooldown.
- `record_success()` restores the state to `HEALTHY` and clears the failure count. The registry does not store a degraded reason (see `mcp_06_10_health-reasons-and-error-kinds.md`).

The `[mcp_servers.*].tool_names` does not affect the circuit breaker state or routing — it is merely reference information and not an input for routing (consistent with [mcp_06_02](mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md)).

Health checks within the `ToolExecutor` execution process act as a gate before dispatching. (Explicit in code — `shared/mcp_health.py`)

## LLM sees a tool but execution fails with "Unknown tool"

**Possible causes:**
- RuntimeToolRegistry is missing or incomplete
- Discovery was FATAL, WARNING, or SKIPPED
- Duplicate tool name detection excluded the tool
- ToolExecutor.set_runtime_registry() was not called

**Result form:** `ToolExecutor.execute()` returns a `ToolCallResult` whose output begins with `routing:<kind>:`. The `<kind>` points at the cause: `not_ready` — `set_runtime_registry()` was not called or discovery did not populate the registry; `posture_excluded` — the Security Posture gate dropped the tool; `server_unavailable` — the owning server is unavailable or the tool is disabled; `unknown_tool` — the name is missing from `RuntimeToolRegistry` or was dropped by duplicate-name detection.

**Diagnosis steps** (if `RuntimeToolRegistry` is missing or incomplete, restart the agent to re-initialize it, and investigate MCP connection issues if persistent):
1. Check startup output for `mcp_tool_discovery` outcomes
2. Check whether discovery was FATAL, WARNING, or SKIPPED
3. Check whether the owning server's `/v1/tools` response includes the tool
4. Check whether duplicate tool name detection excluded the tool
5. Check whether ctx.services_required.runtime_tools was populated
6. Check whether ToolExecutor.set_runtime_registry() was called (an unwired registry yields the `not_ready` kind)
7. Check whether the tool exists in RuntimeToolRegistry
8. Do not rely only on config/agent.toml tool_definitions

**Root cause:**
`ToolRouteResolver.resolve()` raises `ToolRoutingError` (a `ValueError` subclass) whenever a tool name is not found in `RuntimeToolRegistry`. `ToolExecutor.execute()` catches that error and converts it into the `routing` result described above (`is_error=True`, `error_type="routing"`, output `routing:<kind>:`). This can happen even when the LLM sees the tool via `/v1/tools`, because `RuntimeToolRegistry` may be incomplete due to discovery failures.

## Keywords

- configuration
