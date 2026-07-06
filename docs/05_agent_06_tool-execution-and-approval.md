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
     → ToolRouteResolver.resolve()     — tool_name → server_key (routing authority; see 04_mcp_03 §Routing Source of Truth)
     → McpServerHealthRegistry check  — skip UNAVAILABLE servers
     → LifecycleProtocol.ensure_ready() — start ondemand servers if needed
     → HttpTransport — send to MCP server
```

`ToolCallResult` is a frozen dataclass: `(output: str, is_error: bool, request_id: str, server_key: str)`

---

## Parallel vs Sequential Execution

`execute_all_tool_calls()` dispatches based on config flags. Config reference → [05_agent_08 §ToolConfig `use_tool_dag`](05_agent_08_configuration.md).

| Condition | Execution |
|---|---|
| `use_tool_dag=True` and `serial_tool_calls=False` | DAG scheduling |
| `serial_tool_calls=True` | Sequential (all tools) |
| `use_tool_dag=False`, any side-effect tool | Sequential (serialized for safety) |
| `use_tool_dag=False`, no side-effect tools | Parallel (`asyncio.gather()`) |

---

## DAG Tool Scheduler (`agent/tool_scheduler.py`)

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

`_serialization_stats` tracks serialization impact across rounds:

| Counter | Description |
|---|---|
| `total_events` | Cumulative serialization events across all rounds |
| `total_tools_affected` | Cumulative tools affected by serialization |
| `tools_affected_last_round` | Tools affected in the most recent round (reset to 0 when no serialization) |

### `_TOOL_RESULT_MAX_CHARS`

Display threshold: results longer than 500 chars are shown as line/char counts instead of full text in logs.

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

`check_approval()` runs before each tool execution:

### Pre-flight checks (instant deny)

1. **`allowed_tools` whitelist:** if list is non-empty and tool not in list → denied
2. **`allowed_root` root jail:** if path arg is outside `cfg.allowed_root` → denied
3. **GitHub repo allowlist:** if write op on repo not in `approval_github_allowed_repos` → denied (fail-closed)

#### `check_allowed_root(cfg, tool_name, args)`

Returns `False` when any path argument is outside `cfg.approval.allowed_root`. Returns `True` when:
- `allowed_root` is not set (no restriction)
- All path arguments resolve to paths within the allowed root

#### `check_allowed_repo(cfg, tool_name, args)`

Returns `False` when a GitHub write tool targets a repo not in the allowlist. Only applies to `_API_WRITE_TOOLS` (github_* tools). Returns:
- `True` for non-GitHub write tools
- `False` when `allowed_repos` is empty (fail-closed)
- Result of `"owner/repo" in allowed_repos` check

### Operation type classification

`classify_operation_type(tool_name)` returns one of: `READ`, `WRITE`, `DELETE`, `EXECUTE`, `API_WRITE`.

Classification priority (first match wins):
1. `WRITE_TOOLS` → `OperationType.WRITE`
2. `DELETE_TOOLS` → `OperationType.DELETE`
3. `_EXEC_TOOLS` (`shell_run`) → `OperationType.EXECUTE`
4. `_API_WRITE_TOOLS` (github_* tools) → `OperationType.API_WRITE`
5. Default → `OperationType.READ`

### Risk classification

Priority: `approval_risk_rules` table → `tool_safety_tiers` mapping

#### Tier-to-risk mapping

| Tier | Risk level |
|---|---|
| `READ_ONLY` | `none` |
| `WRITE_SAFE` | `none` |
| `WRITE_DANGEROUS` | `medium` |
| `ADMIN` | `high` |

Tools absent from `tool_safety_tiers` default to `WRITE_DANGEROUS` (fail-safe).

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

#### `_GITHUB_WRITE_TOOLS`

Internal constant: `frozenset` of 7 GitHub write tools used for `gitops_push_blocked` check:

| Tool | Purpose |
|---|---|
| `github_push_files` | Push multiple files |
| `github_create_or_update_file` | Create or update a single file |
| `github_delete_file` | Delete a file |
| `github_merge_pull_request` | Merge a PR |
| `github_create_pull_request` | Create a PR |
| `github_update_pull_request` | Update a PR |
| `github_create_branch` | Create a branch |

When `gitops_push_blocked=True`, any of these tools are denied without prompt.

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

### `is_summarized(cfg, text, llm_text, is_error)`

Returns `True` when `llm_text` represents a summarized (not truncated) form of `text`.

Conditions for returning `False`:
- `use_tool_summarize` is disabled or `is_error` is True
- `text` length ≤ `tool_summarize_threshold`
- `llm_text == text` (identical — means truncation, not summarization)

Returns `True` when all above conditions are False and `llm_text != truncated_version`.

### `build_preview(tool_name, args)`

Builds a human-readable operation preview shown before approval prompts.

| Tool category | Preview format |
|---|---|
| `write_file`, `edit_file` | `{path}\n    content: {content[:200]}` |
| `delete_file`, `delete_directory`, `create_directory` | `{path or directory_path}` |
| `move_file` | `{source} → {destination}` |
| `shell_run` | `{command}` |
| `github_*` | `{owner}/{repo} {extra args JSON[:200]}` |
| Other tools | `json.dumps(args)[:300]` |

### `TURN_LIMIT_HINT`

Hint appended to history when a tool result is dropped due to the per-turn limit. Format:

```
[Result omitted: per-turn tool result limit reached. Use /tool show <id> to retrieve the full output.]
```

Applied by `_apply_turn_char_limit()` when `turn_chars + len(llm_text) > tool_results_turn_max_chars`.

---

## Tool Result Cache

`ToolExecutor` maintains a TTL + LRU cache:

- Cache key: JSON-serialized tool name + args (plain string, no MD5)
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
| Dedup | `tool_dedup_max_repeats` (default 3) | Same (name, args) repeated ≥ N times → terminate loop; hint stored in `session_diagnostics` |
| Cycle detection | `tool_cycle_detect_window` (default 2) | Same tool-call fingerprint repeated in last N rounds → terminate loop; hint stored in `session_diagnostics` |
| Retry cap | `tool_error_retry_max` (default 1) | Errored (name, args) called again → terminate loop; hint stored in `session_diagnostics` |
| Consecutive error | `tool_error_max_consecutive` (default 3) | All tools in round error N times → terminate loop |

> **Note:** Guard hints are stored for offline diagnostics only. They are **not** injected into `ctx.conv.history`.

---

## Concurrency Limits

`tool_concurrency_limits: dict[str, int]` (in `ToolConfig`) maps server key to max
concurrent calls. Implemented as `asyncio.Semaphore` lazily created in `_raw_execute()`.

If a server key appears in the limit dict, calls are bounded. Missing keys: no limit.
Unknown server key warning logged but does not error.

---

## Fail-Closed Execution Policy

The orchestrator does NOT fall back to direct (unapproved) execution when a workflow
cannot be created. If workflow creation fails, a `WorkflowCreationError` is raised and
the task is rejected with a clear error message.

**Before (removed):** the orchestrator would execute tool calls directly, bypassing
workflow-level approval checks, when no workflow plan was available.

**After:** `WorkflowCreationError` is raised. The user must fix the underlying cause
(missing plan, invalid config) and retry.

This is a fail-closed policy: safety is preferred over availability.
See [Agent Startup and Recovery](05_agent_07_cli-and-commands.md#startup-recovery) for the startup recovery model.

---

## Workflow Approval Recovery (Cross-Session)

Workflow-level approval state is persisted in the `approvals` table of `workflow.sqlite`.
When a workflow task is suspended for approval (user must run `/approve` or `/reject`),
the approval record survives agent restart:

- **Startup recovery:** On startup, `_recover_pending_approvals()` queries the `approvals` table
  for any pending approval. If found, it sets `ctx.workflow.approval_pending = True` and
  `ctx.turn.pending_approval_id`, then displays a warning with task ID and approval ID.

- **Resolution after restart:** `/approve` and `/reject` resolve the latest pending approval
  from the workflow database — in-memory `pending_approval_id` is NOT required for resolution.
  This means even if the in-memory state is lost, the user can still approve/reject via the CLI.

- **Warning message includes IDs:** The startup warning shows `task=<id> approval=<id> reason=<reason>`
  so operators can correlate with logs and know which task to act on.

---

## Canonical Approval Model (ADR-001)

**Date:** 2026-06-26
**Status:** Accepted

### Context

Two approval layers exist in the agent: tool-level and workflow-level. They must coexist without conflict.

### Decision

Both layers are canonical; boundaries and responsibilities are explicit, not exclusive.

### Boundary Table

| Axis | Tool-level Approval | Workflow-level Approval |
|------|---------------------|------------------------|
| Implementation | `agent/tool_approval.py` | `agent/workflow/workflow_engine.py` |
| Granularity | per tool call | per task (execute→verify gap) |
| State | ephemeral (in-memory) | DB-persisted (`approvals`) |
| Resolution | stdin interactive | `/approve` / `/reject` |
| Currently active | always enabled | disabled (`require_approval=False`) |

The workflow-level approval gate is controlled by `AgentConfig.workflow_require_approval`
(default `False`). Set `workflow_require_approval = true` in the agent config to enable it.
See [AgentConfig Structure](05_agent_08_configuration.md#agentconfig-structure) for the field
reference and startup-only classification.

### Coexistence Rules

When `require_approval=True`:

1. During execute stage: `run_approval_checks` fires per tool call (MEDIUM/HIGH risk tools only).
2. After execute stage: the approval gate suspends the workflow; user runs `/approve` or `/reject`.
3. Both fire independently. This is intentional: they operate at different granularities.

### Architecture Diagram

```
User prompt
  └─► Orchestrator
        └─► WorkflowEngine (plan → execute → [approval gate] → verify)
              └─► repository_gateway.py (tool-call batch)
                    └─► run_approval_checks (per-tool, MEDIUM/HIGH risk)
                          └─► stdin prompt → approved/denied
              └─► Approval gate [when require_approval=True]
                    └─► WorkflowPendingApprovalError
                          └─► /approve or /reject command
```

### ADR Rationale

The requirement "one canonical approval object" means: define clear boundaries and responsibilities for each layer. It does not mean eliminate one layer. Both layers solve different problems:

- Tool-level: real-time per-tool risk gate (before execution).
- Workflow-level: human sign-off on the full execute stage result (after execution).

---

## Partial Completion Persistence

When a workflow fails after some steps have completed, the workflow engine records the
final task status via `StateStore.update_task_status()`:

- `"failed"` — workflow step raised an unhandled exception
- `"halted"` — workflow was explicitly halted via `WorkflowHaltError`

Completed steps are not separately persisted (the workflow engine does not track
individual step progress in the DB). The user must inspect the audit log to determine
which steps succeeded before the failure.

Partial completions are **not** automatically resumed — the user must re-issue the
request or use `/reject` to dismiss a pending approval gate.
