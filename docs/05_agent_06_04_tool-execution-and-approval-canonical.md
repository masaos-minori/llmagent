---
title: "Agent Tool Execution and Approval - Canonical Approval Model"
area: agent
tags:
  - agent
  - tool-execution
  - adr-001
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 05_agent_06_03_tool-execution-and-approval-concurrency-safety.md

source:
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
---

# Agent Tool Execution and Approval

- Turn Flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## Purpose

Documents the Canonical Approval Model (ADR-001) and the persistence of partial completion.

## Design Intent

### Canonical Approval Model (ADR-001)

**Date:** 2026-06-26
**Status:** Accepted

#### Context

There are two approval layers in the agent: tool-level and workflow-level. They must coexist without conflict.

**Terminology Clarification:**
- **Automatic Execution**: Operations that do not require human approval (planning phase, verification phase, low-risk tool operations).
- **Pre-execution Approval**: A tool-level approval gate triggered before tool execution (real-time risk assessment).
- **Post-execution Approval**: A workflow-level approval gate triggered after the `execute` stage is complete (batch result verification).

#### Decision

Both layers are canonical; boundaries and responsibilities are explicit rather than mutually exclusive.

#### Boundary Table

| Axis | Pre-execution Approval (tool-level) | Post-execution Approval (workflow-level) |
|------|---------------------------------------|---------------------------------------------|
| Implementation | `agent/tool_approval.py` | `agent/workflow/workflow_engine.py` |
| Granularity | Per tool call | Per task (between `execute` $\rightarrow$ `verify`) |
| State | Ephemeral (in memory) | Persistent in DB (`approvals`) |
| Resolution | Interactive via stdin | `/approve` / `/reject` |
| Currently active | Always active | Inactive (default workflow definitions have `require_approval=false`) |
| Risk classification | `approval_risk_rules` per tool | `require_approval` flag on workflow definition |

**Design judgment**: The requirement for a "single canonical approval object" means clearly defining the boundaries and responsibilities of each layer. It does not mean excluding one of the layers. Both layers solve different problems:

- Pre-execution Approval: Real-time risk gate per tool (before execution)
- Post-execution Approval: Human approval for the entire results of the `execute` stage (after execution)
- Automatic Execution: Operations that do not require human approval (planning phase, verification phase, low-risk tool calls)

#### Coexistence Rules

When `require_approval=True`:

1. During the `execute` stage: Pre-execution approval (tool-level) triggers for every tool call (only for MEDIUM/HIGH risk tools)
2. After the `execute` stage: Post-execution approval (workflow-level) pauses the workflow; user executes `/approve` or `/reject`
3. Both trigger independently. This is intentional, as they operate at different granularities.
4. Automatic execution (planning phase, verification phase, low-risk tool calls) does not require human approval.

### Persistence of Partial Completion

If a workflow fails after some steps are completed, the workflow engine records the final task status via `StateStore.update_task_status()`:

- `"failed"` — Workflow step raised an unhandled exception
- `"halted"` — Workflow was explicitly stopped by `WorkflowHaltError`

**Design judgment**: Completed steps are not persisted individually. Partial completion is **not** automatically resumed — the user must either resubmit the request or use `/reject` to dismiss pending gates.

## Responsibility Boundary

- **Canonical Source**: `agent/tool_approval.py` (tool-level), `agent/workflow/workflow_engine.py` (workflow-level)
- **Workflow Approval DB**: `workflow.sqlite`

## Key Constraints

- Both approval layers are canonical and not mutually exclusive
- Pre-execution approval (tool-level) is always active
- Post-execution approval (workflow-level) does not fire by default
- Partial completion is not automatically resumed
- Automatic execution (planning/verification phases, low-risk tools) does not require human approval

## Operational Notes

- Automatic execution (planning phase, verification phase, low-risk tool calls) does not require human approval
- Pre-execution approval (tool-level) configures risk classification via `ApprovalConfig.approval_risk_rules`
- Post-execution approval (workflow-level) is enabled via the `WorkflowDef.require_approval` flag

## Known Limitations

- Post-execution approval (workflow-level) is disabled by default — requires explicit configuration change
- Pre-execution approval (tool-level) can be configured individually via `approval_risk_rules`, but unset tools require approval as "MEDIUM" risk
- Partial completion is not automatically resumed — manual user intervention is required

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`

## Keywords

canonical approval model
ADR-001
partial completion persistence
