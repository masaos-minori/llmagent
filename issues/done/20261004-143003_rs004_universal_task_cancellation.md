# ResourceShutdownCoordinator: Cancels ALL pending tasks including those needing completion

## Background

`ResourceShutdownCoordinator.close_resources()` in `scripts/agent/resource_shutdown_coordinator.py` coordinates resource shutdown during REPL exit. It cancels pending tasks after WAL checkpoint completes.

## Problem

The method uses `asyncio.all_tasks(loop)` to get all pending tasks and cancels them all indiscriminately. This includes tasks that may be critical for data integrity, such as history-write tasks that are mid-operation.

## Evidence

- File: `scripts/agent/resource_shutdown_coordinator.py`
- Lines 113-127:

```python
pending_tasks = [
    t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
]
if pending_tasks:
    logger.info(...)
    for t in reversed(pending_tasks):
        t.cancel()
    results = await asyncio.gather(*pending_tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            errors.append(("task_cancellation", f"{type(res).__name__}: {res}"))
```

## Impact

- History write operations may be cancelled mid-flight, losing data
- Any task spawned during the turn loop could be affected
- The LIFO ordering claim ("last-created-first-cancelled") provides no guarantee of correctness — it's arbitrary based on task creation order

## Recommended action

1. Track which tasks are safe to cancel vs. which must complete (e.g., via a `turn.background_tasks` set as documented in `TurnState`).
2. Only cancel tasks from `turn.background_tasks`.
3. Await completion of non-cancellable tasks (like WAL checkpoint, which is already done before this point).

```python
# Cancel only background tasks tracked by Orchestrator
pending_tasks = list(self._ctx.turn.background_tasks)
self._ctx.turn.background_tasks.clear()
for t in pending_tasks:
    t.cancel()
results = await asyncio.gather(*pending_tasks, return_exceptions=True)
...
```

## Acceptance criteria

- [ ] Only tracked background tasks are cancelled
- [ ] Critical operations (WAL checkpoint, history flush) are not cancelled
- [ ] Test verifies no data loss during shutdown with active history writes
- [ ] Test verifies cancellation of background-only tasks

## Out of scope

- Changes to WAL checkpoint logic (already correctly placed before cancellation)
- Changes to the shutdown sequence ordering
