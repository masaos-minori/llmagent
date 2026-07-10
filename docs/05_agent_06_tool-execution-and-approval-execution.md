---
title: "Agent Tool Execution and Approval"
category: agent
tags:
  - agent
  - agent
  - tool
  - execution
  - approval
  - safety
related:
  - 05_agent_00_document-guide.md
---

# Agent Tool Execution and Approval

or.py`)

`execute(tool_name, args) -> ToolCallResult` dispatch priority:

```
1. Plugin tool (@register_tool)        — local Python function, bypasses MCP
2. TTL cache                           — returns cached result if not expired
3. MCP server dispatch via internal method
     → ToolRouteResolver.resolve()     — tool_name → server_key (routing authority; see 04_mcp_03 §Routing Source of Truth)
     → McpServerHealthRegistry check  — skip UNAVAILABLE servers
     → LifecycleProtocol.ensure_ready() — start ondemand servers if needed
     → HttpTransport — send to MCP server
```

`ToolCallResult` is a frozen dataclass: `(output: str, is_error: bool, request_id: str, server_key: str)`

---

## Parallel vs Sequential Execution



`execute_all_tool_calls()` dispatches based on config flags. Config reference → [05_agent_08 §ToolConfig `use_tool_dag`](05_agent_08_configuration-loading-agent-config.md).

| Condition | Execution |
|---|---|
| `use_tool_dag=True` and `serial_tool_calls=False` | DAG scheduling |
| `serial_tool_calls=True` | Sequential (all tools) |
| `use_tool_dag=False`, any side-effect tool | Sequential (serialized for safety) |
| `use_tool_dag=False`, no side-effect tools | Parallel (`asyncio.gather()`) |

**Production note:** Setting `use_tool_dag=false` is considered legacy (non-production) behavior. In production mode, this setting is flagged as an error during startup validation via `ProductionConfigValidator.validate()`. The DAG scheduler provides resource-scoped parallelism for independent reads while serializing writes per resource scope.

---

## DAG Tool Scheduler (`agent/tool_s

cheduler.py`)

`build_execution_groups(tool_calls, tool_meta)` groups tool calls into ordered batches.

### Rules (applied in priority order)

1. **`requires_serial=True`** — tool forms a single-element serial barrier; runs alone before all other tools
2. **Same `resource_scope` + `is_write=True`** — tools sharing a scope are serialized within that scope's group
3. **`is_write=True` without `resource_scope`** — goes into a `write_first` group (conservative; runs before reads)
4. **All others** — parallel group at the end

### `concurrent_groups` structure

`metadata.concurrent_groups: list[list[list[dict]]]` — list of batches:
- Each **batch** runs sequentially relative to other batches
- Groups **within** a batch run concurrently via `asyncio.gather()`
- `serial_barrier` tools: one batch each (solo)
- `write_first` group: own sequential batch
- All `resource_scope` groups + parallel group: shared concurrent batch

Example: `[write_file(scope=file), github_push(scope=github), read_text_file]` →
one concurrent batch with three groups, all running simultaneously.

### `scheduling_mode` audit field

`"dag_concurrent"` — at least one batch had multiple groups running concurrently.
`"dag_sequential"` — all batches ran with a single group (no intra-batch concurrency).

### `execute_one_tool_call(ctx, tc, turn)`

Parses, executes, and optionally summarizes one tool_call dict. Returns `(tc_id, name, args, full_text, is_error, llm_text)`.

- Parses `arguments` JSON; raises `ToolArgumentsDecodeError` on malformed JSON
- Raises `ToolExecutorUnavailableError` when `ctx.services_required.tools` is None
- If transport error: saves failure to `ctx.diagnostics`
- If summarization enabled and result > threshold: calls `summarize_tool_result()` → `llm_text`
- Otherwise: truncates to `tool_result_max_llm_chars` + "\n... (truncated)"

### Serialization statistics

Serialization stats track serialization impact across rounds:

| Counter | Description |
|---|---|
| `total_events` | Cumulative serialization events across all rounds |
| `total_tools_affected` | Cumulative tools affected by serialization |
| `tools_affected_last_round` | Tools affected in the most recent round (reset to 0 when no serialization) |

### Display threshold

Results longer than 500 chars are shown as line/char counts instead of full text in logs.

---

### Serialization Event Schema

Every round emits a `round_exec` audit event:

| Field | Type | Description |
|---|---|---|
| `round_id` | string | UUIDv4 identifying this round |
| `tool_count` | int | Number of tool calls in the round |
| `mode` | string | `"parallel"` or `"serial"` |
| `has_side_effect` | bool | True if any serialization event was triggered |
| `trigger_tool` | string or null | First tool that triggered serialization |
| `elapsed_ms` | float | Wall-clock time for the full round in milliseconds |
| `scheduling_mode` | string or null | DAG mode: `"dag_concurrent"` or `"dag_sequential"`; null in standard mode |

Use `elapsed_ms` to identify serialization overhead. A round with
`has_side_effect=true` and a high `elapsed_ms` compared to equivalent parallel rounds
is a candidate for optimization.

Query the audit log:
```
grep round_exec /path/to/audit.log
```

---

## Approval Flow

`check_approval()`

## Related Documents

- `agent`
- `tool`
- `execution`

## Keywords

agent
tool
execution
approval
safety
