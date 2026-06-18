## Goal

Update `docs/05_agent_02_runtime-architecture.md` and `docs/05_agent_04_state-and-persistence.md` to document `WorkflowState` as a session-scoped runtime state component of `AgentContext`.

## Scope

- `05_agent_02_runtime-architecture.md`: add `WorkflowState` to the `AgentContext` component listing
- `05_agent_04_state-and-persistence.md`: add `WorkflowState` table row, update user-facing description of workflow state
- No code changes

## Assumptions

- `WorkflowState` is implemented in `scripts/agent/context.py` (step 1 completed)
- Both doc files already exist and have sections covering `AgentContext` and state persistence

## Implementation

### Target file

`docs/05_agent_02_runtime-architecture.md` and `docs/05_agent_04_state-and-persistence.md`

### Procedure

1. In `05_agent_02_runtime-architecture.md`: locate the `AgentContext` component description and add `ctx.workflow` alongside `ctx.conv`, `ctx.turn`, `ctx.stats`
2. In `05_agent_04_state-and-persistence.md`: add a `WorkflowState` entry to the state table

### Method

Direct edit of both doc files.

### Details

**`05_agent_02_runtime-architecture.md`** — in the `AgentContext` section, add:

```
| `ctx.workflow` | `WorkflowState` | Per-session workflow runtime state: active flag, current task ID, approval pending flag |
```

(Add to the sub-structure table alongside the other `ctx.*` entries.)

**`05_agent_04_state-and-persistence.md`** — add to the canonical state table:

```
| `WorkflowState` | session | `ctx.workflow.*` | No (transient) | `active`, `current_task_id`, `current_workflow_version`, `approval_pending`, `last_session_id` |
```

Also add a brief description:

> `WorkflowState` (`ctx.workflow`) is populated by `Orchestrator.handle_turn()` on each turn.
> `active=True` while a workflow engine run is in progress.
> `approval_pending=True` when the turn was suspended at an approval gate (`WorkflowPendingApprovalError`).
> All fields are transient and reset each session; durable task state lives in `workflow.sqlite`.

## Validation plan

| Check | Action | Expected |
|---|---|---|
| Correctness | Verify field names match `WorkflowState` dataclass in `context.py` | All fields match |
| Completeness | Confirm both doc files reference `WorkflowState` | Both updated |
