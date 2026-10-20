---
title: "MCP Health Reasons and Error Kinds"
area: mcp
tags:
  - mcp
  - health-reasons
  - scheduling
related:
  - mcp_00_document-guide.md
  - mcp_06_01_configuration-file-inventory.md
  - agent_08_03_configuration-tools-memory.md
---

# MCP Health Reasons and Error Kinds

## Health Reasons Priority

When probing an HTTP MCP server via `/health`, structured fields are returned that determine both LIFECYCLE actions and display reasons.

`McpProbeResult` carries `restart_recommended` (true if the health endpoint says so, or `lifecycle_state == FAILED`), `operator_action_required` (true only if the health endpoint sets it), and a derived `health_reason`.

Priority for deriving `health_reason`:

| Priority | Condition | Result |
|-----------|-----------|--------|
| 1 | The `/health` body has a `reason` (fallback `message`) string | That string |
| 2 | No body reason and the health endpoint set `operator_action_required` | `"operator_action_required"` |
| 3 | No body reason and `restart_recommended` is true | `"restart_recommended"` |
| - | All other cases | Empty string |

The `restart_recommended` field has two different sources with distinct semantics:

1. **From the `/health` endpoint**: Indicates proactive recommendation from the server itself.
2. **From `LifecycleProtocol.ensure_ready()`**: Set when `lifecycle_state == FAILED` — indicates reactive detection based on transport layer failures.

Both are treated equally at the display level.

#### Degraded Reasons Are Not Stored

The `/health` body reason is used for display only; `record_failure()` takes no reason argument.


`McpServerHealthRegistry` does not store a degraded reason. A server's state changes only through `record_failure()` (`DEGRADED` below the failure threshold, `UNAVAILABLE` at or above it) and `record_success()` (back to `HEALTHY`, clearing the failure count).

---

## Difference Between Tool Errors and Transport Errors

In an MCP server, errors are divided into two categories:

1. **Transport Error**: Failures in communication itself, such as network issues, timeouts, or server unreachability.
2. **Tool Error**: The server is reachable, but a specific tool execution failed (e.g., invalid arguments, upstream API error).

Transport errors affect the MCP server's health state (`McpServerHealthRegistry`). Tool errors do not — the server is operating normally, but a specific tool call failed.

#### Error Counter Tracking

Per-server tool and transport error counters are kept in memory by `ToolTransportInvoker` (inherited by `ToolExecutor`) and drive no automatic warning or threshold. The similarly named `AgentContext.stats.stat_tool_errors` is a separate agent-session aggregate for `/stats`.

#### Audit Log Detail Verification

Each `tool_exec` audit event carries `error_type` of `"tool"`, `"transport"`, or `""` (success); filter with `jq 'select(.error_type == "tool")' <log_dir>/audit.log`.

---

### Tool Scheduling and Serialization

An agent executes tool calls grouped by resource scope through a single DAG scheduler. Serialization is an intentional safety measure against concurrent writes to shared resources, not a configuration error. The triggers (`requires_serial`, `forced_serial`, resource read/write and write/write conflicts, `global_write_scope`) and the `ROUND_SERIALIZATION` log format are defined in [mcp_06_06](mcp_06_06_end-to-end-tool-call-tracing.md#serialization-of-side-effects); `serial_tool_calls` is described in [agent_08_03](../23_agent/agent_08_03_configuration-tools-memory.md).

#### Serialization Statistics via `/mcp status`

Running `/mcp status` allows you to view cumulative session statistics.

``` text
--- Tool Scheduling ---
  Serialization events this session: 5
  Tools affected by serialization:   12
```

These counters are reset upon agent restart. If the number of serialization events is high relative to total tool calls, it may be a candidate for adding `resource_scope_kind`/`resource_scope_keys` annotations or reviewing `requires_serial=False` — however, this should only be decided after analyzing which tools are causing them.

#### Before Optimization

Do not change `requires_serial` or `resource_scope_kind`/`resource_scope_keys` values without reviewing the serialization log data. The observability layer provides the necessary data for safe decision-making.

---

## Keywords

- health-reasons
- scheduling
