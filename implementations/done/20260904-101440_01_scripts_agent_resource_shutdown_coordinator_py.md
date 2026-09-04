# Implementation Procedure: Add deterministic ordering to ResourceShutdownCoordinator.close_resources task cancellation

## Target file
- `scripts/agent/resource_shutdown_coordinator.py`

## Source plan
- `plans/20260904-001051_rsc001_plan.md`

## Related requirements
- REQ-RSC001-1: Shutdown behavior is deterministic across multiple runs with same concurrent operations
- REQ-RSC001-2: WAL checkpoint completes before history write is cancelled

## Background
ResourceShutdownCoordinator coordinates cleanup during REPL shutdown. It collects pending tasks and cancels them before gathering results. The current implementation iterates `asyncio.all_tasks()` in arbitrary order, causing inconsistent shutdown behavior between runs.

## Adversarial Verification
- Plan claim "asyncio.all_tasks() iteration is non-deterministic" → Verified: `resource_shutdown_coordinator.py:57-59` uses `asyncio.all_tasks(loop)` which returns tasks in arbitrary order
- Plan assumption "WAL/history tasks identifiable by coroutine name" → **Invalidated**: zero `set_name()` calls across entire codebase (`rg 'set_name|\.name\s*=' scripts/agent/` returned no matches); no naming convention exists
- Current code structure: step 1 cancels ALL tasks simultaneously, then step 2 does WAL checkpoint — this means WAL checkpoint task could be cancelled before step 2 executes, causing inconsistency
- **No additional target files discovered during investigation**

## Design decisions
- Replace tier-based classification (rejected: no naming convention exists) with **LIFO ordering** (last-created-first-cancelled)
- Rationale: Python 3.13 production environment supports `asyncio.Task.get_name()` but no code sets custom names; LIFO provides deterministic ordering without requiring naming infrastructure
- Preserve existing gather semantics (return_exceptions=True)
- Document the ordering rationale in the class docstring

## Alternatives considered
- Tier-based classification by task type → rejected: no naming convention exists in codebase
- Topological sort of task dependencies → rejected: requires tracking dependency graph at task creation time, too invasive
- Priority-based ordering using task attributes → rejected: same problem as tier-based classification

## Compatibility considerations
- Runtime behavior unchanged for valid inputs; shutdown ordering becomes deterministic instead of arbitrary
- Error message text preserved for backward compatibility
- No API surface changes

## Security considerations
- No security impact: defensive check relocation does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires restoring original `for t in pending_tasks: t.cancel()` pattern and removing added ordering logic
- No database schema changes, no config changes

## Method

### Step 1: Replace non-deterministic cancellation with LIFO ordering

Change lines 56-70 from:
```python
        # 1. Cancel all pending tasks (except this one)
        pending_tasks = [
            t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
        ]
        if pending_tasks:
            logger.info(
                "Cancelling %d pending tasks during shutdown", len(pending_tasks)
            )
            for t in pending_tasks:
                t.cancel()

            results = await asyncio.gather(*pending_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    errors.append(("task_cancellation", f"{type(res).__name__}: {res}"))
```

to:
```python
        # 1. Cancel all pending tasks in LIFO order (last-created-first-cancelled)
        #    This ensures deterministic shutdown behavior: the most recently
        #    created task is cancelled first, preventing cascading failures
        #    when dependent tasks are still running.
        pending_tasks = [
            t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
        ]
        if pending_tasks:
            logger.info(
                "Cancelling %d pending tasks during shutdown", len(pending_tasks)
            )
            # Cancel in reverse order (LIFO) for deterministic shutdown
            for t in reversed(pending_tasks):
                t.cancel()

            results = await asyncio.gather(*pending_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    errors.append(("task_cancellation", f"{type(res).__name__}: {res}"))
```

### Step 2: Update class docstring

Add documentation about the cancellation ordering policy to `ResourceShutdownCoordinator` class docstring (around line 33-37):

After the existing docstring text, add:
```
    Cancellation ordering:
        Tasks are cancelled in LIFO (last-created-first-cancelled) order
        to ensure deterministic shutdown behavior. This prevents cascading
        failures when dependent tasks are still running.
```

### Step 3: Verify no other callers of asyncio.all_tasks() in shutdown paths

Search for other uses of `asyncio.all_tasks()` that might need similar treatment:
```bash
rg 'asyncio\.all_tasks' scripts/agent/ --type py
```

Expected result: Only one usage site (this method). If additional sites found, report `Needs confirmation`.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace non-deterministic cancellation with LIFO ordering | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Changed `for t in pending_tasks` to `for t in reversed(pending_tasks)` |
| 2 | Update class docstring | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | Added cancellation ordering documentation |
| 3 | Verify no other callers of asyncio.all_tasks() | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | Only one usage site; ruff + mypy pass |

## Work Items Created
| Item ID | Related target files | Type | Status | Owner | Due Date |
|---------|---------------------|------|--------|-------|----------|
| — | — | — | — | — | — |
