---
title: "Watchdog Behavior — Health Reasons and Scheduling"
category: mcp
tags:
  - mcp
  - watchdog
  - health-reasons
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Watchdog Behavior — Health Reasons and Scheduling


### Health reason priority order

When probing an HTTP MCP server via `/health`, the probe returns structured fields that determine both LIFECYCLE actions and display reasons:

```python
# From McpProbeResult model
restart_recommended: bool       # True if health endpoint says so OR lifecycle_state == FAILED
operator_action_required: bool  # True only if health endpoint sets this flag
health_reason: str              # Derived priority: operator_action > restart_recommended
```

Priority order for `health_reason` derivation:

| Condition | Result |
|-----------|--------|
| `operator_action_required=true` AND reachable+HTTP_OK | `"operator_action_required"` |
| `restart_recommended=true` AND reachable+HTTP_OK | `"restart_recommended"` |
| Server unreachable/failing | Body-provided reason string (from `details.reason` or fallback `message`) |
| All other cases | Empty string |

The `restart_recommended` field has two sources with different semantics:

1. **From `/health` endpoint**: Indicates proactive recommendation by the server itself
2. **From LifecycleProtocol.ensure_ready()**: Set when `lifecycle_state == FAILED` — indicates reactive detection based on transport-level failures

Both are treated equivalently at the display level.

#### Body reason tracking through probe chain

When probing an HTTP MCP server's `/health`, the body field propagates as follows:

```python
# Step 1: Probe returns raw body
probe_result.body["reason"] or probe_result.body["message"]

# Step 2: Resolved to endpoint string  
_resolve_endpoint() returns tuple including body_reason

# Step 3: HealthRegistry receives it via record_failure(record_success())
registry.record_failure(reason=str(body_reason))

# Step 4: Displayed at two levels
# - Per-server degraded reason: registry.get_degraded_reason(key)
# - Global table column: McpProbeResult.health_reason derived below
```

#### Watchdog logging behavior

When the watchdog detects issues via `_watchdog_check_http()`:

```python
# In _probe_mcp_health_detail():
if not probe.reachable or probe.status_code != HTTPStatus.OK:
    # Unreachable/degraded: no restart attempt; log WARNING with details
elif probe.restart_recommended:
    # Proactive restart recommended: proceed with subprocess shutdown/startup
else:
    # No issue detected: normal operation continues
```

For servers where `reachable=True` but `status_code=503` (degraded), the watchdog does NOT automatically restart because `restart_recommended=false`. Instead, it logs a warning containing the body-reason from `probe.body["reason"]` or `probe.body["message"]`. If `operator_action_required=true`, the same logic applies—no automatic restart, just a WARNING about what requires manual attention.

---



### Tool error monitoring

`ToolExecutor` distinguishes two error categories:

| Category | Log field | Condition |
|----------|-----------|-----------|
| Transport error | `error_type=transport` | Network failure, timeout, server unreachable |
| Tool error | `error_type=tool` | Server reachable; tool execution returned `is_error=true` |

Transport errors affect the MCP server health state and may trigger watchdog restarts.
Tool errors do not — the server is functioning, but the specific tool call failed
(e.g., invalid arguments, upstream API error).

Transport errors are raised by `HttpTransport` as `TransportError` and caught by
the transport error handler, which increments `stat_transport_errors`
and calls `HealthRegistry.record_failure()`.

#### Per-server tool error counters

`ToolExecutor.stat_tool_errors` is a `dict[str, int]` (server_key → count) available
for the lifetime of the process. Read it from the agent context:

```python
ctx.services.tools.stat_tool_errors   # {"rag_pipeline": 3, "github": 0}
```

#### Repeated-failure warnings

When the per-server tool error count reaches a multiple of
`repeated_tool_error_threshold` (default: 3), a warning is logged:

```
WARNING repeated tool errors from 'rag_pipeline': 3 failures (error_type=tool)
```

The threshold is configurable at `ToolExecutor` construction time. Counters reset
on process restart. There is no automatic server restart on tool errors (only
transport failures trigger the watchdog).

#### Grep patterns for monitoring

```bash
# Find tool errors for a specific server
grep "error_type=tool" agent.log | grep "rag_pipeline"

# Find repeated-failure warnings
grep "repeated tool errors" agent.log

# Find transport failures
grep "error_type=transport" agent.log
```

---



### Tool scheduling and serialization

The agent executes tool calls in resource-scoped groups (DAG scheduling, active when `use_tool_dag=true`). Setting `use_tool_dag=false` reverts to the legacy non-production mode (all WRITE_TOOLS before READ_TOOLS within a round, without resource-scoped parallelism). Most tools run in parallel,
but certain conditions force serial execution within a round:

| Condition | Trigger | Log reason |
|-----------|---------|------------|
| Tool has `requires_serial=True` | Any tool with this flag | `requires_serial` |
| Multiple write tools share a `resource_scope` | Two+ write tools with same scope | `resource_scope_conflict` |
| Write tools without a `resource_scope` | Any write tool lacking scope metadata | `is_write_overlap` |
| Side-effect tool in round (standard execution path) | Any side-effect tool | logged as "Side-effect tool detected" |

Serialization is intentional safety behavior — it prevents concurrent writes from corrupting
shared resources. It does not indicate a configuration error.

#### Reading serialization log entries

Each serialization event logs:

```
INFO ROUND_SERIALIZATION: triggered by <tool_name> (<reason>)
     — <N> tools serialized in this round
```

Example:

```
INFO ROUND_SERIALIZATION: triggered by write_file (is_write_overlap)
     — 2 tools serialized in this round
```

#### Serialization stats in /mcp status

Run `/mcp status` to see cumulative session stats:

```
--- Tool Scheduling ---
  Serialization events this session: 5
  Tools affected by serialization:   12
```

These counters reset on agent restart. A high serialization count relative to
total tool calls may indicate candidates for `resource_scope` annotation or
`requires_serial=False` review — but only after analyzing which tools are
triggering it.

#### Before optimizing

Do not change `requires_serial` or `resource_scope` values without reviewing
the serialization log data. The observability layer provides the data needed
to make safe decisions.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

watchdog
health-reasons
scheduling
