## Goal

Only cancel tracked background tasks during shutdown instead of all pending tasks, preventing data loss from mid-flight critical operations.

## Implementation outcome

Deviation from procedure: no code change was performed. Origin/master already ships
this fix in commit `10308ed7` — `close_resources()` already cancels only
`turn.background_tasks` in LIFO order, snapshotting the set before clearing it to
prevent double-cancellation (lines 108-127). This matches the intent of the
Details "After" block and is ordered correctly (snapshot before clear). Existing
regression tests (`tests/agent/test_resource_shutdown_coordinator.py`,
`TestSelectiveTaskCancellation`) use the real API and pass (5 passed total).

Accepting the upstream implementation and closing the workflow.

## Scope

- Modify `scripts/agent/resource_shutdown_coordinator.py`: replace `asyncio.all_tasks()` with `turn.background_tasks` for task cancellation
- Clear the `background_tasks` set before iterating to prevent double-cancellation

## Assumptions

- `self._ctx.turn.background_tasks` is accessible from within `close_resources()`
- The `TurnState.background_tasks` set is properly maintained by the Orchestrator
- WAL checkpoint has already completed before `close_resources()` is called (confirmed by issue statement)

## Design decisions

- Replace `asyncio.all_tasks(loop)` with `list(self._ctx.turn.background_tasks)` — only explicitly-tracked tasks are cancelled
- Clear the set before iterating to prevent double-cancellation of tasks added during iteration
- Keep the LIFO ordering logic for remaining tasks

## Alternatives considered

- Adding a separate "critical task" exclusion list — fragile, requires constant updates
- Using task names/prefixes to identify critical tasks — over-engineering, hard to maintain

## Implementation
### Target file
`scripts/agent/resource_shutdown_coordinator.py`

### Procedure
Replace the `asyncio.all_tasks()` iteration with the `turn.background_tasks` set tracked by the Orchestrator. Clear the set before cancelling to prevent double-cancellation.

### Method
1. Locate lines 113-127 in `scripts/agent/resource_shutdown_coordinator.py` (task cancellation loop)
2. Change `asyncio.all_tasks(loop)` to `list(self._ctx.turn.background_tasks)`
3. Add `self._ctx.turn.background_tasks.clear()` before the iteration to prevent double-cancellation
4. Update the comment above the cancellation block to reflect the new behavior

### Details
```python
# Before (lines 113-127):
# Cancel all pending tasks except the current one
loop = asyncio.get_event_loop()
pending_tasks = [
    t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
]
for task in reversed(pending_tasks):
    task.cancel()

# After:
# Cancel only tracked background tasks (not critical operations like WAL checkpoint)
if hasattr(self._ctx, 'turn') and hasattr(self._ctx.turn, 'background_tasks'):
    # Clear the set before iterating to prevent double-cancellation
    self._ctx.turn.background_tasks.clear()
    for task in reversed(list(self._ctx.turn.background_tasks)):
        task.cancel()
```

The key change is replacing `asyncio.all_tasks(loop)` with `list(self._ctx.turn.background_tasks)` and clearing the set before iterating. This ensures only explicitly-tracked background tasks are cancelled, while critical operations like history writes remain untouched.

## Compatibility considerations

This change is backward-compatible — it cancels fewer tasks than before. No existing behavior is lost for tracked tasks. However, any code that relied on universal task cancellation may need updates.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to `asyncio.all_tasks(loop)` if callers depend on universal task cancellation. This would restore the previous behavior but reintroduce data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/resource_shutdown_coordinator.py | Unit test — verify selective task cancellation | uv run pytest tests/agent/test_resource_shutdown_coordinator.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Only tracked background tasks are cancelled (REQ-001)
- [ ] Critical operations (WAL checkpoint, history flush) are not cancelled (REQ-002)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to WAL checkpoint logic (already correctly placed before cancellation)
- Changes to the shutdown sequence ordering
- Creating new test file (handled in separate document)

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261004-143003_rs004_universal_task_cancellation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182811_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194648
- **Related target files**: scripts/agent/resource_shutdown_coordinator.py
