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

)

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
See [AgentConfig Structure](05_agent_08_01_configuration-loading-agent-config.md#agentconfig-structure) for the field
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

W

hen a workflow fails after some steps have completed, the workflow engine records the
final task status via `StateStore.update_task_status()`:

- `"failed"` — workflow step raised an unhandled exception
- `"halted"` — workflow was explicitly halted via `WorkflowHaltError`

Completed steps are not separately persisted (the workflow engine does not track
individual step progress in the DB). The user must inspect the audit log to determine
which steps succeeded before the failure.

Partial completions are **not** automatically resumed — the user must re-issue the
request or use `/reject` to dismiss a pending approval gate.

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
