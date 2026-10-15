---
title: "Agent Tool Execution and Approval - Tool-Level Approval and Partial Completion"
area: agent
tags:
  - agent
  - tool-execution
  - adr-001
related:
  - agent_00_document-guide.md
  - agent_06_01_tool-execution-and-approval-execution.md
  - agent_06_02_tool-execution-and-approval-approval.md
  - agent_06_03_tool-execution-and-approval-concurrency-safety.md
  - agent_03_01_turn-processing-flow-overview.md
  - mcp_03_01_dispatch-and-routing.md
---

# Agent Tool Execution and Approval

- Turn Flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [mcp_03_01_dispatch-and-routing.md](../22_mcp/mcp_03_01_dispatch-and-routing.md)

## Purpose

Documents where human approval is decided (tool-level only) and the persistence of partial completion. ADR-001 defines the Workflow Engine foundation and excludes redesign of the tool-level approval policy.

## Design Intent

### Tool-Level Approval

Human approval is decided before a Tool executes, by the tool-level approval in `agent/tool_approval.py`, inside the `execute` stage. The workflow has no approval stage.

#### Terminology

- **Automatic Execution**: Operations that do not require human approval (planning phase, verification phase, low-risk tool operations).
- **Tool-level Approval**: An approval gate triggered before tool execution (real-time risk assessment, interactive via stdin).

#### Behavior

- Risk classification uses `approval_risk_rules` per tool; a tool without a rule falls back to its safety-tier default.
- The gate applies per tool call, for MEDIUM and HIGH risk tools only.
- Every decision, approved or denied, is written to the audit log as a `tool_approval` event that carries the `workflow_id` and the turn ID in its `task_id` field; no separate approval table is kept.
- A workflow definition that contains the `require_approval` key is rejected at load time.

### Persistence of Partial Completion

If a workflow fails after some steps are completed, the workflow engine records the final task status via `StateStore.update_task_status()`:

- `"failed"` — Workflow step raised an unhandled exception
- `"halted"` — Workflow was stopped by `WorkflowHaltError` (retry exhaustion) or `WorkflowTimeoutError`

**Design judgment**: Completed steps are not persisted individually. Partial completion is **not** automatically resumed — the user must resubmit the request.

## Responsibility Boundary

- **Canonical Source**: `agent/tool_approval.py` (tool-level approval)

## Key Constraints

- Tool-level approval is the only human approval and is always active
- The workflow has no approval stage
- Partial completion is not automatically resumed
- Automatic execution (planning/verification phases, low-risk tools) does not require human approval

## Operational Notes

- Tool-level approval configures risk classification via `ApprovalConfig.approval_risk_rules`

## Known Limitations

- Tool-level approval can be configured individually via `approval_risk_rules`, but a tool without a rule falls back to its safety-tier default (`READ_ONLY`/`WRITE_SAFE` → `none`, `WRITE_DANGEROUS` → `medium`, `ADMIN` → `high`)
- Partial completion is not automatically resumed — manual user intervention is required

## Keywords

- tool-level approval model
- ADR-001
- partial completion persistence
