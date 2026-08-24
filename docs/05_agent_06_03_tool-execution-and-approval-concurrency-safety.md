---
title: "Agent Tool Execution and Approval - Concurrency and Safety"
area: agent
tags:
  - agent
  - tool-execution
  - concurrency-limits
  - fail-closed
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
source:
  - 05_agent_06_03_tool-execution-and-approval-concurrency-safety.md
---

# Agent Tool Execution and Approval

- Turn Flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## Purpose

Documents responsibility separation for safety controls, design decisions for `ToolLoopGuard`, and the fail-closed policy.

## Design Intent

### Summary of Safety Controls

| Control | Config field | Behavior |
|---|---|---|
| `allowed_tools` | `cfg.tool.allowed_tools` | Whitelist; if empty, all are allowed. In production, `allowed_tools=[]` is treated as a configuration error |
| `allowed_root` | `cfg.approval.allowed_root` | Path jail; if empty, disabled |
| `approval_github_allowed_repos` | `cfg.approval.*` | GitHub write allowlist; if empty, all are rejected (**Fail-closed**) |
| `plan_blocked_tools` | `cfg.tool.plan_blocked_tools` | Automatic rejection in plan mode |
| `approval_protected_paths` | `cfg.approval.*` | Escalation to `high` via path prefixes |
| `approval_high_risk_branches` | `cfg.approval.*` | Escalation to `high` via branch names |
| `gitops_push_blocked` | `cfg.approval.*` | Globally block all writes to GitHub |

### ToolLoopGuard Design Decisions

Controls the internal tool loop within `LLMTurnRunner`:

| Guard | Config field | Behavior |
|---|---|---|
| Deduplication | `tool_dedup_max_repeats` (default 3) | If the same (name, args) is repeated N or more times → terminate loop |
| Cycle Detection | `tool_cycle_detect_window` (default 2) | If the same tool call fingerprint is repeated within the last N rounds → terminate loop |
| Retry Limit | `tool_error_retry_max` (default 1) | If an erroring (name, args) is called again → terminate loop |
| Consecutive Errors | `tool_error_max_consecutive` (default 3) | If all tools in a round error N times → terminate loop |

**Design judgment**: Guard hints are stored for offline diagnostics only. They are **not injected** into `ctx.conv.history`.

### Concurrency Limits

`tool_concurrency_limits: dict[str, int]` in `ToolConfig` maps server keys to maximum concurrent calls. It is implemented as an `asyncio.Semaphore` created on-demand during tool execution.

- If the server key exists in the limit dictionary, calls are limited
- If the key does not exist: No limit
- Unknown server keys log a warning but do not cause errors

### Fail-Closed Execution Policy

The Orchestrator never falls back directly to unapproved execution if it cannot create a workflow. If workflow creation fails, a `WorkflowCreationError` is raised, and the task is rejected with a clear error message.

**Design judgment**: This is a fail-closed policy — safety is prioritized over availability.

### Workflow Approval Recovery

Workflow-level approval states are persisted in the `approvals` table of `workflow.sqlite`:

- **Startup Recovery**: At startup, searches the `approvals` table to check for pending approvals
- **Post-restart Resolution**: `/approve` and `/reject` resolve the latest pending approvals from the workflow database
- **IDs in Warning Messages**: Operators can match logs to identify which tasks need attention

## Responsibility Boundary

- **Canonical Source**: `shared/tool_executor.py` (ToolExecutor), `agent/tool_loop_guard.py` (ToolLoopGuard)
- **Workflow Approval DB**: `workflow.sqlite`

## Key Constraints

- Fail-closed: `allowed_tools=[]` (production), `approval_github_allowed_repos=[]`, workflow creation failure
- Fail-safe: Undefined tools in `tool_safety_tiers` default to `WRITE_DANGEROUS`
- ToolLoopGuard guard hints are not injected into history

## Operational Notes

- Unknown

## Known Limitations

- Since GitHub tools are not included in `approval_dry_run_tools` by default, this path is currently dormant.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`

## Keywords

safety controls summary
ToolLoopGuard
concurrency limits
fail-closed execution policy
workflow approval recovery
