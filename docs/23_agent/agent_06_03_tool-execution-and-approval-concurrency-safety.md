---
title: "Agent Tool Execution and Approval - Concurrency and Safety"
area: agent
tags:
  - agent
  - tool-execution
  - concurrency-limits
  - fail-closed
related:
  - agent_00_document-guide.md
  - agent_06_01_tool-execution-and-approval-execution.md
  - agent_06_02_tool-execution-and-approval-approval.md
  - agent_06_04_tool-execution-and-approval-canonical.md
---

# Agent Tool Execution and Approval

- Turn Flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [mcp_03_01_dispatch-and-routing.md](../22_mcp/mcp_03_01_dispatch-and-routing.md)

## Purpose

Documents responsibility separation for safety controls, design decisions for `ToolLoopGuard`, and the fail-closed policy.

## Design Intent

### Summary of Safety Controls

| Control | Config field | Behavior |
|---|---|---|
| `allowed_tools` | `cfg.tool.allowed_tools` | Whitelist; at runtime (`check_preflight()`) an empty list performs no whitelist check, so all tools are allowed. Separately, `ProductionConfigValidator` records `allowed_tools=[]` as a validation error in production (startup exits on validator errors) (Explicit in code — `scripts/agent/tool_policy.py`, `scripts/shared/production_config_validator.py`) |
| `allowed_root` | `cfg.approval.allowed_root` | Path jail; if empty, disabled |
| `approval_github_allowed_repos` | `cfg.approval.*` | GitHub write allowlist; if empty, all are rejected (**Fail-closed**) |
| `plan_blocked_tools` | `cfg.tool.plan_blocked_tools` | Automatic rejection in plan mode |
| `approval_protected_paths` | `cfg.approval.*` | Escalation to `high` via path prefixes |
| `approval_high_risk_branches` | `cfg.approval.*` | Escalation to `high` via branch names |
| `gitops_push_blocked` | `cfg.approval.*` | Globally block all writes to GitHub |

### ToolLoopGuard Design Decisions

Controls the internal tool loop within `LlmTurnExecutor`:

| Guard | Config field | Behavior |
|---|---|---|
| Deduplication | `tool_dedup_max_repeats` | If the same (name, args) is repeated N or more times → terminate loop |
| Cycle Detection | `tool_cycle_detect_window` | If the same tool call fingerprint is repeated within the last N rounds → terminate loop |
| Retry Limit | `tool_error_retry_max` | If an erroring (name, args) is called again → terminate loop |
| Consecutive Errors | `tool_error_max_consecutive` | If all tools in a round error N times → terminate loop |
| Empty Result Repeat | `tool_empty_result_max_repeats` (disabled when 0) | If a tool returns empty results N or more times within a turn → terminate loop |

**Distinction from WorkflowEngine retry**: `tool_error_retry_max` is ToolLoopGuard's own in-memory per-turn block — it suppresses retries of the same `(tool, args)` pair within a single turn. It is NOT the same as `WorkflowEngine.retry_policy.max_attempts`, which governs stage-level retries across turns. These are two independent mechanisms at different granularities: ToolLoopGuard operates within a single LLM turn's tool loop, while WorkflowEngine operates across turns at the workflow stage level.

**Design judgment**: Guard hints are stored for offline diagnostics only. They are **not injected** into `ctx.conv.history`.

### Concurrency Limits

`tool_concurrency_limits: dict[str, int]` in `ToolConfig` maps server keys to maximum concurrent calls. It is implemented as an `asyncio.Semaphore` created on-demand during tool execution.

- If the server key exists in the limit dictionary, calls are limited
- If the key does not exist: No limit
- Unknown server keys log a warning but do not cause errors

### Fail-Closed Execution Policy

The Orchestrator never falls back directly to unapproved execution if it cannot create a workflow. If workflow definitions fail to load, `WorkflowLoader().load()` raises a `RuntimeError` during `Orchestrator.__init__()`, and construction of the Orchestrator fails at startup.

**Design judgment**: This is a fail-closed policy — safety is prioritized over availability.

### Workflow Approval Recovery

Workflow-level approval states are persisted in the `approvals` table of `workflow.sqlite`:

- **Startup Recovery**: At startup, searches the `approvals` table to check for pending approvals
- **Post-restart Resolution**: `/approve` and `/reject` require an explicit `approval_id` and resolve that record in the workflow database only if it is still pending; they never pick a pending approval automatically
- **IDs in Warning Messages**: Operators can match logs to identify which tasks need attention

## Responsibility Boundary

- **Canonical Source**: `shared/tool_executor.py` (ToolExecutor), `agent/tool_loop_guard.py` (ToolLoopGuard)
- **Workflow Approval DB**: `workflow.sqlite`

## Key Constraints

- Fail-closed: `approval_github_allowed_repos=[]`, workflow creation failure. `allowed_tools=[]` is not fail-closed at runtime (all tools allowed); only the production startup validator rejects it
- Fail-safe: tools missing from `tool_safety_tiers` are rejected at startup; at classification time a tool absent from the registry is `high`
- ToolLoopGuard guard hints are not injected into history

## Known Limitations

See Known Limitations in [agent_06_02_tool-execution-and-approval-approval.md](agent_06_02_tool-execution-and-approval-approval.md) (the dry-run path for GitHub tools is currently dormant).

## Keywords

safety controls summary
ToolLoopGuard
concurrency limits
fail-closed execution policy
workflow approval recovery
