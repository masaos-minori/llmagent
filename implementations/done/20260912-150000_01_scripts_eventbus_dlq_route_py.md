## Goal

Wire `dlq_requeue()` to `redeliver_event()` in `scripts/eventbus/dlq_route.py` using the lineage model (REQ-001).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/dlq_route.py` to use `redeliver_event()` instead of `requeue_event()`
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The lineage model is chosen as the single truth for `/dlq/{event_id}/requeue`
- Each DLQ requeue creates a new event row with `redelivered_from` pointing to the original
- The original row's `dlq_at` is intentionally left set so only one redeliver succeeds per original event
- A `redelivered_from`-existence check is needed for full concurrency protection

## Design decisions

- Wire `dlq_requeue()` to call `redeliver_event()` instead of `requeue_event()`
- Update the response shape to include `new_event_id` and `new_seq` fields
- Preserve existing error handling for events not in DLQ

## Alternatives considered

- Keeping the in-place model: would leave `redeliver_event()` and the `redelivered_from`/`cycle_failure_count` schema columns unused, representing wasted engineering effort
- Adding a config flag to switch between models: adds complexity without clear benefit; the design decision should be made once and committed

## Implementation

### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

1. Update imports to include `redeliver_event` from db module
2. Replace `requeue_event()` call with `redeliver_event()` call
3. Update response shape to include `new_event_id` and `new_seq` fields
4. Remove the dead code path for events not in DLQ

### Method

For the function update:
- Change the `_requeue()` inner function to call `redeliver_event()` instead of `requeue_event()`
- Update the response logic to handle the new return type `(success, new_event_id)`
- Add `new_event_id` and `new_seq` fields to the response when successful

### Details

#### Step 1: Update imports

```python
# Before:
from eventbus.db import count_dlq, fetch_dlq, requeue_event

# After:
from eventbus.db import count_dlq, fetch_dlq, redeliver_event
```

#### Step 2: Update dlq_requeue function

```python
# Before:
async def dlq_requeue(
    request: Request,
    event_id: str,
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue."""
    db = get_db(request)
    cfg = get_config(request)

    def _requeue() -> tuple[bool, int | None]:
        """Requeue a single event from the dead letter queue and return its failure count."""
        found = requeue_event(db, event_id)
        if not found:
            return False, None
        row = db.execute(
            "SELECT delivery_failure_count FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return True, int(row[0]) if row else None

    requeued, failure_count = await run_with_db_lock(_requeue)
    if requeued:
        logger.info("dlq requeued event_id=%s", event_id)
        resp: dict[str, Any] = {"event_id": event_id, "requeued": True}
        if failure_count is not None and failure_count >= cfg.max_retry:
            resp["dlq_imminent"] = True
        return resp
    # Event exists but is not currently in DLQ — dlq_at IS NULL means event was already requeued or acked
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
    raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)

# After:
async def dlq_requeue(
    request: Request,
    event_id: str,
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue.

    Uses the lineage model: each requeue creates a new event row with
    redelivered_from pointing to the original event_id. The original row's
    dlq_at is intentionally left set so only one redeliver succeeds per
    original event.
    """
    db = get_db(request)
    cfg = get_config(request)

    def _redeliver() -> tuple[bool, str | None]:
        """Redeliver a single event from the dead letter queue using the lineage model."""
        success, new_event_id = redeliver_event(db, event_id)
        return (success, new_event_id)

    success, new_event_id = await run_with_db_lock(_redeliver)
    if success:
        logger.info("dlq redelivered event_id=%s -> %s", event_id, new_event_id)
        resp: dict[str, Any] = {
            "event_id": event_id,
            "requeued": True,
            "new_event_id": new_event_id,
        }
        # Include new_seq by fetching the seq of the newly inserted row
        row = db.execute(
            "SELECT seq FROM events WHERE event_id = ?",
            (new_event_id,),
        ).fetchone()
        if row is not None:
            resp["new_seq"] = int(row[0])
        return resp
    # Event exists but is not currently in DLQ — dlq_at IS NULL means event was already redelivered or acked
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
    raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
```

## Compatibility considerations

- The response shape changes to include `new_event_id` and `new_seq` fields
- Existing callers expecting the same `event_id` back will need updating
- The `dlq_imminent` field is no longer included since the original event's `delivery_failure_count` is no longer relevant after redelivery

## Security considerations

- The lineage model provides better auditability — each delivery attempt is a distinct row with `redelivered_from` pointing to the original
- This improves security by preventing indefinite resource consumption from abandoned subscriptions

## Rollback considerations

- If the lineage model causes issues in production, roll back to the previous state where `requeue_event()` was used
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/dlq_route.py::dlq_requeue | Integration: verify response shape matches lineage model | pytest tests/eventbus/test_eventbus_dlq.py::test_dlq_requeue | Test completes without assertion errors |
| scripts/eventbus/db.py::redeliver_event | Integration: verify concurrent requeue operations don't cause data corruption | pytest tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue | Test completes without assertion errors |

## Completion criteria

- [ ] Import updated to include `redeliver_event` from db module
- [ ] `_requeue()` replaced with `_redeliver()` calling `redeliver_event()`
- [ ] Response shape includes `new_event_id` and `new_seq` fields
- [ ] Tests pass with the new requeue model

## Out of scope

- Changes to `scripts/eventbus/db.py` (handled in separate procedure document)
- Changes to test files (handled in separate procedure documents)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update imports to include redeliver_event | Pending | — | — | |
| 2 | Replace requeue_event with redeliver_event | Pending | — | — | |
| 3 | Update response shape | Pending | — | — | |
| 4 | Run validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260911-142700_ebdlq01_requeue-model-in-place-vs-lineage-conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-115455_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-150000
- **Related target files**: scripts/eventbus/dlq_route.py
