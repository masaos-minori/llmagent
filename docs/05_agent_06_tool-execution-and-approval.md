# Agent Tool Execution and Approval

- Turn flow → [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md)
- MCP routing → [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md)

## Purpose

Document `ToolExecutor` behavior, parallel vs sequential execution, the approval flow,
plan mode, tool result summarization, caching, safety controls, and `allowed_tools`.

---

## ToolExecutor (`shared/tool_executor.py`)

`execute(tool_name, args) -> ToolCallResult` dispatch priority:

```
1. Plugin tool (@register_tool)        — local Python function, bypasses MCP
2. TTL cache                           — returns cached result if not expired
3. _raw_execute()                      — MCP server dispatch
     → ToolRouteResolver.resolve()     — tool_name → server_key
     → McpServerHealthRegistry check  — skip UNAVAILABLE servers
     → LifecycleProtocol.ensure_ready() — start ondemand servers if needed
     → HttpTransport or StdioTransport — send to MCP server
```

`ToolCallResult` is a frozen dataclass: `(output: str, is_error: bool, request_id: str, server_key: str)`

---

## Parallel vs Sequential Execution

`execute_all_tool_calls()` decides based on tool contents:

| Condition | Execution |
|---|---|
| `serial_tool_calls=True` (config) | Sequential (all tools) |
| Any tool in `_SIDE_EFFECT_TOOLS` present | Sequential (serialized for safety) |
| Neither | Parallel (`asyncio.gather()`) |

`_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})`

Side-effect detection: `is_side_effect(tool_name: str) -> bool`

---

## Approval Flow

`check_approval()` runs before each tool execution:

### Pre-flight checks (instant deny)

1. **`allowed_tools` whitelist:** if list is non-empty and tool not in list → denied
2. **`allowed_root` root jail:** if path arg is outside `cfg.allowed_root` → denied
3. **GitHub repo allowlist:** if write op on repo not in `approval_github_allowed_repos` → denied (fail-closed)

### Risk classification

Priority: `approval_risk_rules` table → `tool_safety_tiers` → `_TIER_TO_RISK` mapping

| Risk level | Behavior |
|---|---|
| `none` | Auto-approved (no prompt) |
| `medium` | Preview + `y/N` prompt |
| `high` | Preview + full `yes` input required |

### Risk escalation conditions

- Path in `approval_protected_paths` → escalate to `high`
- GitHub branch in `approval_high_risk_branches` (default: main, master) → escalate to `high`
- `gitops_force_push_blocked=True` and `force=True` arg → deny
- `gitops_push_blocked=True` → deny all GitHub write ops

### Dry-run preview

Tools in `approval_dry_run_tools` (default: write_file, edit_file, delete_file, delete_directory,
move_file) are pre-executed with `dry_run=True` before the approval prompt. Result appended to preview.

### Denial handling

Denied tools receive `"Tool execution denied by user."` as tool result (returned to LLM as a
tool role message, so conversation continues naturally).

---

## Plan Mode

`/plan` toggles `ctx.conv.plan_mode`.

- When `True`: tools in `cfg.tool.plan_blocked_tools` are auto-denied (without prompt)
- Default blocked: `write_file`, `create_directory`, `delete_file`, `delete_directory`
- Purpose: allow LLM to reason and plan without executing destructive operations

---

## Tool Result Summarization

When `use_tool_summarize=True` and result length > `tool_summarize_threshold` (default 3000 chars):

1. `summarize_tool_result(text, tool_name, args)` calls the LLM with a summarization prompt
2. Summarized result is stored in `ctx.conv.history` (LLM context)
3. Full result is stored in `ctx.tool_result_store`
4. Accessible via `/tool list` / `/tool show <id>`

---

## Tool Result Cache

`ToolExecutor` maintains a TTL + LRU cache:

- Cache key: `MD5(tool_name + orjson_sorted(args))`
- Only successful results (`is_error=False`) are cached
- TTL: `tool_cache_ttl` seconds (default 300)
- LRU eviction when `tool_cache_max_size > 0` (default 200)
- Cache hit: `request_id=""` in result
- `/clear` clears the cache
- Cache stats: visible in `/stats` as `Cache hits`

---

## Safety Controls Summary

| Control | Config field | Behavior |
|---|---|---|
| `allowed_tools` | `cfg.tool.allowed_tools` | Whitelist; empty = allow all |
| `allowed_root` | `cfg.approval.allowed_root` | Path jail; empty = disabled |
| `approval_github_allowed_repos` | `cfg.approval.*` | GitHub write allowlist; empty = deny all (fail-closed) |
| `plan_blocked_tools` | `cfg.tool.plan_blocked_tools` | Auto-deny in plan mode |
| `approval_protected_paths` | `cfg.approval.*` | Path prefix escalation to `high` |
| `approval_high_risk_branches` | `cfg.approval.*` | Branch name escalation to `high` |
| `gitops_push_blocked` | `cfg.approval.*` | Block all GitHub writes globally |
| `gitops_force_push_blocked` | `cfg.approval.*` | Block force push (default: `True`) |
| `gitops_protected_branches` | `cfg.approval.*` | Protected branches (default: main, master) |

---

## ToolLoopGuard

Controls the inner tool loop in `LLMTurnRunner`:

| Guard | Config field | Behavior |
|---|---|---|
| Dedup | `tool_dedup_max_repeats` (default 3) | Same (name, args) repeated N times → inject hint to LLM |
| Cycle detection | `tool_cycle_detect_window` (default 2) | Same tool sequence in N rounds → warn |
| Retry cap | `tool_error_retry_max` (default 1) | Errored (name, args) called again > N → block |
| Consecutive error | `tool_error_max_consecutive` (default 3) | All tools in round error N times → break loop |

---

## Concurrency Limits

`tool_concurrency_limits: dict[str, int]` (in `ToolConfig`) maps server key to max
concurrent calls. Implemented as `asyncio.Semaphore` lazily created in `_raw_execute()`.

If a server key appears in the limit dict, calls are bounded. Missing keys: no limit.
Unknown server key warning logged but does not error.
