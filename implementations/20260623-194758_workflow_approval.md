# Implementation: Expose Workflow Execution Mode and Approval-Pending State

## Goal

Make approval-pending state visible in terminal output and `/stats`. Two gaps: (1) no terminal message when workflow turn suspends for approval, (2) `/stats` doesn't show `approval_pending`.

## Scope

**In:**
- `scripts/agent/tool_output.py` — add `emit_approval_pending_notice()` function
- `scripts/agent/orchestrator.py` — call `emit_approval_pending_notice()` when approval_pending is set
- `scripts/agent/commands/models.py` — add `approval_pending: bool = False` to `StatsViewModel`
- `scripts/agent/commands/cmd_config_stats.py` — add approval_pending display to `/stats`
- `scripts/agent/commands/cmd_workflow.py` — reset `ctx.workflow.approval_pending` on `/approve` and `/reject`

**Out:**
- Changing REPL prompt format
- Redesigning workflow execution

## Assumptions

1. `orchestrator.py:199` sets `ctx.workflow.approval_pending = True` in the `except WorkflowPendingApprovalError` block
2. `emit_*` functions from `tool_output.py` write to `_DEFAULT_OUT` (the terminal)
3. `ctx.workflow` is a field of `AgentContext` — accessible via `ctx.workflow.approval_pending`

## Implementation

### Target files: see above

### Procedure

1. Add `emit_approval_pending_notice()` to `tool_output.py`
2. Call it in `orchestrator.py` after setting `approval_pending = True`
3. Add `approval_pending` field to `StatsViewModel`
4. Read from `ctx.workflow.approval_pending` in `_collect_stats()`
5. Display conditionally in `_cmd_stats()` when True
6. Reset `approval_pending` on `/approve` and `/reject`

### Method

Direct code additions — new function, new field, conditional display.

### Details

**Change 1: `tool_output.py` — emit function**

Add after existing emit functions:
```python
def emit_approval_pending_notice(
    approval_id: str,
    task_id: str,
    output: OutputPort | None = None,
) -> None:
    """Write a visible terminal notice when a workflow turn is suspended for approval."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(
        f"\n[APPROVAL PENDING] Workflow task '{task_id}' is waiting for approval."
        f" Use /approve [reason] or /reject [reason]. (id: {approval_id})"
    )
```

**Change 2: `orchestrator.py` — call emit function**

In the `except WorkflowPendingApprovalError as exc:` block after `ctx.workflow.approval_pending = True`:
```python
from agent.tool_output import emit_approval_pending_notice
emit_approval_pending_notice(
    approval_id=exc.approval_id,
    task_id=exc.task_id or "unknown",
)
```

**Change 3: `models.py` — StatsViewModel field**

Add after `workflow_mode`:
```python
approval_pending: bool = False
```

**Change 4: `cmd_config_stats.py` — _collect_stats()**

After the `workflow_mode` line:
```python
approval_pending=ctx.workflow.approval_pending if ctx.workflow is not None else False,
```

**Change 5: `cmd_config_stats.py` — _cmd_stats()**

After the workflow_mode display line:
```python
if stats.approval_pending:
    self._out.write("  Approval       : PENDING — use /approve or /reject")
```

**Change 6: `cmd_workflow.py` — reset on approve/reject**

In `_cmd_approve()`:
```python
self._ctx.turn.pending_approval_id = None
self._ctx.workflow.approval_pending = False
```

In `_cmd_reject()`:
```python
self._ctx.turn.pending_approval_id = None
self._ctx.workflow.approval_pending = False
```

## Validation plan

1. `uv run ruff check scripts/agent/orchestrator.py scripts/agent/tool_output.py scripts/agent/commands/` — no lint errors
2. `uv run pytest tests/test_orchestrator.py tests/test_agent_cmd_workflow.py -v` — all pass
3. `uv run pytest tests/test_agent_cmd_config.py -v` — no regression
