---
title: "MCP Health Reasons and Scheduling"
category: mcp
tags:
  - mcp
  - health-reasons
  - scheduling
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
source:
  - 04_mcp_06_13_watchdog-health-reasons-scheduling.md
---

# MCP Health Reasons and Scheduling

## Health Reasons Priority

When probing an HTTP MCP server via `/health`, structured fields are returned that determine both LIFECYCLE actions and display reasons.

```python
# From McpProbeResult model
restart_recommended: bool       # True if health endpoint says so OR lifecycle_state == FAILED
operator_action_required: bool  # True only if health endpoint sets this flag
health_reason: str              # Derived priority: operator_action > restart_recommended
```

Priority for deriving `health_reason`:

| Condition | Result |
|-----------|--------|
| `operator_action_required=true` AND reachable+HTTP_OK | `"operator_action_required"` |
| `restart_recommended=true` AND reachable+HTTP_OK | `"restart_recommended"` |
| Server unreachable/failed | String from body (`details.reason`, fallback to `message`) |
| All other cases | Empty string |

The `restart_recommended` field has two different sources with distinct semantics:

1. **From the `/health` endpoint**: Indicates proactive recommendation from the server itself.
2. **From `LifecycleProtocol.ensure_ready()`**: Set when `lifecycle_state == FAILED` — indicates reactive detection based on transport layer failures.

Both are treated equally at the display level.

### Body Reason Tracking Across Probe Chain

When probing an HTTP MCP server's `/health`, the `body` field propagates as follows:

```python
# Step 1: Probe returns raw body
probe_result.body["reason"] or probe_result.body["message"]

# Step 2: Resolved to endpoint string  
_resolve_endpoint() returns tuple including body_reason

# Step 3: HealthRegistry receives it via record_failure(server_key)
# Note: record_failure() does not take a 'reason' argument.
# Although record_degraded(server_key, reason=None) exists, it is currently dead code.
registry.record_failure(server_key)

# Step 4: Current Status
# Because record_degraded() is not used, get_degraded_reason() always returns None.
# Refer to docs/04_mcp_06_12_watchdog-configuration-monitoring.md for details.
```

#### List of Degraded Reasons

Currently, since `record_degraded()` is not called, `get_degraded_reason()` always returns `None`.

- All degraded reasons are cleared by `record_success()`.

---

### Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_06_02_configuration-file-inventory.md`
- `04_mcp_06_13_watchdog-health-reasons-scheduling.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

### Keywords

health-reasons
scheduling

---

## Difference Between Tool Errors and Transport Errors

In an MCP server, errors are divided into two categories:

1. **Transport Error**: Failures in communication itself, such as network issues, timeouts, or server unreachability.
2. **Tool Error**: The server is reachable, but a specific tool execution failed (e.g., invalid arguments, upstream API error).

Transport errors affect the MCP server's health state (`McpServerHealthRegistry`). Tool errors do not — the server is operating normally, but a specific tool call failed.

#### Error Counter Tracking

`ToolTransportInvoker` maintains both tool error counts (`stat_tool_errors`) and transport error counts (`stat_transport_errors`) in memory per server key. Since `ToolExecutor` inherits from this class, it carries over both counters but does not maintain its own separate ones.

**Note:** Currently, there are no automatic warning logs or threshold checks based on these counters.

**Note (Confusion Prevention):** A similarly named `stat_tool_errors` (`AgentContext.stats.stat_tool_errors`, `scripts/agent/context.py`) exists in the agent session statistics, but this is distinct from the `ToolTransportInvoker` counter described here; it is used for aggregate display at the agent layer, such as in `/stats`.

#### Audit Log Detail Verification

Details regarding tool execution results are outputted in a structured JSON format audit log (`audit_logger`). Each log entry is composed as a `ToolExecEvent` and includes the following fields:

- `"event"`: `"tool_exec"`
- `"error_type"`: `"tool"`, `"transport"`, or `""` (on success)

These logs can be investigated using `jq` or `grep` to search JSON fields.

```bash
# Example of extracting specific error types using jq
cat agent.log | jq 'select(.error_type == "tool")'

# Example of direct JSON string search using grep
grep '"error_type":"tool"' agent.log
```

---

### Tool Scheduling and Serialization

An agent executes tool calls grouped by resource scope (always active DAG scheduling when `serial_tool_calls=False`). While `use_tool_dag` is not present in the codebase (Explicit in code — [05_agent_08_03](05_agent_08_03_configuration-tools-memory.md#toolconfig-cfgtool)), setting `serial_tool_calls=True` switches to the legacy standard execution mode (sequential if any side-effecting tool is present, otherwise parallel). Most tools are executed in parallel, but

serialization is forced within a round under certain conditions:

| Condition | Trigger | Log Reason |
|-----------|---------|------------|
| Tool has `requires_serial=True` | Any tool with this flag | `requires_serial` |
| Overlapping `resource_scopes` (at least one write) | Two or more tool calls with matching or hierarchical filesystem scopes | `resource_scope_conflict` |
| Empty `resource_scopes` for a write tool | Any write tool without scope metadata | `is_write_overlap` |
| Side-effect tool in a round (standard path) | Any side-effecting tool | "Side-effect tool detected" |

Serialization is an intentional safety measure — to prevent corruption of shared resources due to concurrent writes. This is not an indication of a configuration error.

#### Reading Serialization Log Entries

Each serialization event is logged in the following format:

``` text
INFO ROUND_SERIALIZATION: triggered by <tool_name> (<reason>)
     — <N> tools serialized in this round
```

Example:

``` text
INFO ROUND_SERIALIZATION: triggered by write_file (is_write_overlap)
     — 2 tools serialized in this round
```

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

### Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_06_02_configuration-file-inventory.md`
- `04_mcp_06_13_watchdog-health-reasons-scheduling.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

### Keywords

health-reasons
scheduling
