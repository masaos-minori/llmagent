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
  - agent_03_01_turn-processing-flow-overview.md
  - mcp_03_01_dispatch-and-routing.md
---

# Agent Tool Execution and Approval

- Turn Flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [mcp_03_01_dispatch-and-routing.md](../22_mcp/mcp_03_01_dispatch-and-routing.md)

## Purpose

Documents responsibility separation for safety controls, design decisions for `ToolLoopGuard`, and the fail-closed policy.

## Design Intent

### Summary of Safety Controls

| Control | Behavior |
|---|---|
| `allowed_tools` (`cfg.tool`) | Whitelist; at runtime (`check_preflight()`) an empty list performs no whitelist check, so all tools are allowed. Separately, `ProductionConfigValidator` records `allowed_tools=[]` as a validation error in production (startup exits on validator errors) (Explicit in code — `scripts/agent/tool_policy.py`, `scripts/agent/production_config_validator.py`) |
| `allowed_root` (`cfg.approval`) | Path jail; if empty, disabled |
| `approval_github_allowed_repos` (`cfg.approval`) | GitHub write allowlist; if empty, all are rejected (**Fail-closed**) |

The remaining controls (`plan_blocked_tools`, `approval_protected_paths`, `approval_high_risk_branches`, `gitops_push_blocked`) are described in [agent_06_02](agent_06_02_tool-execution-and-approval-approval.md).

### ToolLoopGuard Design Decisions

Controls the internal tool loop within `LlmTurnExecutor`. The guards (deduplication, cycle detection, retry limit, consecutive errors, empty result repeat), their thresholds (config fields: [agent_08](agent_08_03_configuration-tools-memory.md)), and the distinction from `WorkflowEngine` stage-level retry are canonical in [agent_03_02](agent_03_02_turn-processing-flow-llm-tool-loop.md). Every guard terminates the loop when triggered; `tool_empty_result_max_repeats=0` disables the empty-result guard.

**Design judgment**: Guard hints are stored for offline diagnostics only. They are **not injected** into `ctx.conv.history`.

### Concurrency Limits

`tool_concurrency_limits: dict[str, int]` in `ToolConfig` maps server keys to maximum concurrent calls. It is implemented as an `asyncio.Semaphore` created on-demand during tool execution; a server with no entry is capped at the process-wide default concurrency ceiling.

- If the server key exists in the limit dictionary, calls are limited to that value
- If the key does not exist: calls fall back to the process-wide default concurrency ceiling
- A configured `0` or negative limit opts out and stays unlimited (no semaphore)
- Unknown server keys log a warning but do not cause errors

### Fail-Closed Execution Policy

The Orchestrator never falls back directly to unapproved execution if it cannot create a workflow. If workflow definitions fail to load, `WorkflowLoader().load()` raises a `RuntimeError` during `Orchestrator.__init__()`, and construction of the Orchestrator fails at startup.

**Design judgment**: This is a fail-closed policy — safety is prioritized over availability.

## Responsibility Boundary

- **Canonical Source**: `shared/tool_executor.py` (ToolExecutor), `agent/tool_loop_guard.py` (ToolLoopGuard)

## Key Constraints

- Fail-closed: `approval_github_allowed_repos=[]`, workflow creation failure. `allowed_tools=[]` is not fail-closed at runtime (all tools allowed); only the production startup validator rejects it
- Fail-safe: tools missing from `tool_safety_tiers` are rejected at startup; at classification time a tool absent from the registry is `high`
- ToolLoopGuard guard hints are not injected into history

## Known Limitations

See Known Limitations in [agent_06_02_tool-execution-and-approval-approval.md](agent_06_02_tool-execution-and-approval-approval.md) (the dry-run path for GitHub tools is currently dormant).

## Keywords

- safety controls summary
- ToolLoopGuard
- concurrency limits
- fail-closed execution policy
