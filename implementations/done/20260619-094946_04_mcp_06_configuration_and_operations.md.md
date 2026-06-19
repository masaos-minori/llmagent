# Implementation: Document Transport vs Tool Error Monitoring Fields

## Goal

Add a monitoring section to `docs/04_mcp_06_configuration_and_operations.md` describing the transport/tool error distinction, per-server error counters, and the repeated-failure warning threshold.

## Scope

- `docs/04_mcp_06_configuration_and_operations.md` — new subsection documenting:
  - `error_type=transport` vs `error_type=tool` in log output
  - `stat_tool_errors` per-server counter access
  - `repeated_tool_error_threshold` config parameter
  - How to interpret warning messages

Out of scope:
- Code changes
- External monitoring system integration

## Assumptions

1. The doc already has an operations section covering MCP server health and watchdog (line 281 confirms `mcp_watchdog_max_restarts`); the new subsection extends this.
2. The monitoring fields are added by Steps 1-3 in `tool_executor.py`.
3. Audience: operators running the production agent who need to distinguish "server down" from "tool broken."

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Find the existing server health / watchdog section.
2. Insert a new `### Tool error monitoring` subsection after it.

### Method

New prose subsection with a log example, counter table, and config parameter description.

### Details

**Subsection content outline:**

```
### Tool error monitoring

`ToolExecutor` distinguishes two error categories:

| Category | Log field | Condition |
|----------|-----------|-----------|
| Transport error | `error_type=transport` | Network failure, timeout, server unreachable |
| Tool error | `error_type=tool` | Server reachable; tool execution returned `is_error=true` |

Transport errors affect the MCP server health state and may trigger watchdog restarts.
Tool errors do not — the server is functioning, but the specific tool call failed
(e.g., invalid arguments, upstream API error).

#### Per-server tool error counters

`ToolExecutor.stat_tool_errors` is a `dict[str, int]` (server_key → count) available
for the lifetime of the process. Read it from the agent context:

```python
ctx.services.tool_executor.stat_tool_errors   # {"rag_pipeline": 3, "github": 0}
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
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the new subsection | operator can distinguish transport vs tool errors without reading source |
| Accuracy | Cross-check counter name with `tool_executor.py` `__init__` | `stat_tool_errors` matches |
| Accuracy | Cross-check threshold param name | `repeated_tool_error_threshold` matches |
