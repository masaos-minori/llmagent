## Goal

Update workflow task status in the database when the engine exits (success or failure) to prevent orphaned task records.

## Scope

**In:**
- `scripts/agent/orchestrator.py`: Add task status updates in the `finally` block of `_handle_workflow_engine()`

**Out:**
- Modifying `WorkflowEngine.run()` — the fix should be in the caller, not the engine itself
- Changing the task record lifecycle beyond status updates
- Any other file modifications

## Assumptions

1. `store` is already accessible in the `finally` block since it's defined at method scope.
2. `error_kind` is already accessible in the `finally` block since it's declared at method scope (line 182).
3. `task` may not be defined if an exception occurs before `_init_workflow_task()` returns — need to guard against this.
4. The `StateStore.update_task_status()` method is available and works correctly.

## Design decisions

- Update task status in the `finally` block rather than in each individual exception handler, ensuring consistent behavior regardless of how the engine exits.
- Catch exceptions during status update silently with a warning — a failed status update should not cause the agent to crash.

## Alternatives considered

- Update task status in each individual exception handler: would require duplicating the logic across multiple paths and risk missing some exit points.
- Update task status in `WorkflowEngine.run()`: would mix concerns — the engine shouldn't know about task lifecycle management.
- Defer status updates to a background cleanup job: would leave orphaned records until the next cleanup cycle, defeating the purpose.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Locate `_handle_workflow_engine()` method in `Orchestrator` class (line ~174)
2. Find the existing `finally` block
3. Add task status update logic before `_deactivate_workflow()` call
4. Guard against undefined `task` variable with `'task' in locals()` check

### Method

Inline modification of existing method — no new methods or classes required.

### Details

```python
finally:
    # Update task status before deactivating to prevent orphaned records
    try:
        if 'task' in locals() and task.task_id:
            if error_kind is not None:
                store.update_task_status(task.task_id, "failed")
            else:
                store.update_task_status(task.task_id, "completed")
    except Exception as e:
        logger.warning("Failed to update task status on engine exit: %s", e)
    self._deactivate_workflow(ctx)
    store.close()
```

## Compatibility considerations

N/A — only affects error handling path; no API changes.

## Security considerations

N/A — no security impact; only improves data consistency for workflow tasks.

## Rollback considerations

Simple revert of the task status update addition; no data migration or config changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/orchestrator.py | Lint | `ruff check scripts/agent/orchestrator.py` | 0 errors |
| scripts/agent/orchestrator.py | Type check | `mypy scripts/agent/orchestrator.py` | no new errors |
| scripts/agent/orchestrator.py | Architecture | `lint-imports` | 0 violations |
| scripts/agent/orchestrator.py | Tests | `pytest tests/test_agent/ -k orchestrator` | all pass |
| scripts/agent/orchestrator.py | Manual test | Configure a workflow with multiple stages, trigger a tool execution failure during "execute" stage | Verify the task record shows status="failed" |

## Out of scope

- Modifying `WorkflowEngine.run()` — the fix should be in the caller, not the engine itself
- Changing the task record lifecycle beyond status updates
- Any other file modifications

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-145758_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-171450
- Related target files: scripts/agent/orchestrator.py
