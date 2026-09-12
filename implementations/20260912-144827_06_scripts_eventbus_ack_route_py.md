## Goal

Remove `Depends(require_consumer_identity)` from delegated-to functions in `scripts/eventbus/ack_route.py` since authorization moves to app.py wrappers (REQ-001).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/ack_route.py` to remove authorization dependencies
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- Authorization will be handled by the wrapper functions in `app.py` via FastAPI DI
- The `_identity` parameter is no longer needed as a FastAPI dependency
- The existing database operations remain unchanged

## Design decisions

- Remove the `Depends(require_consumer_identity)` declaration from both `ack_event` and `nack` functions
- Keep the `_identity` parameter name for backward compatibility but change it to a regular parameter (not a FastAPI dependency)
- The authorization check will be performed by the wrapper function before calling these delegated-to functions

## Alternatives considered

- Keeping the `Depends(...)` declaration and relying on FastAPI DI — would not work because these functions are called as plain functions, not through FastAPI's DI system
- Removing the `_identity` parameter entirely — would break backward compatibility with any code that passes this parameter

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. Remove `Depends(require_consumer_identity)` from `ack_event` function signature
2. Remove `Depends(require_consumer_identity)` from `nack` function signature
3. Update the `_identity` parameter to be a regular parameter (not a FastAPI dependency)
4. Remove the import of `require_consumer_identity` if no longer needed

### Method

For each function:
- Change the `_identity` parameter from `Annotated[dict, Depends(require_consumer_identity)] = {}` to a simple `dict | None = None` type hint
- Keep the parameter name for backward compatibility

### Details

#### Step 1: Update imports

```python
# Before:
from eventbus.auth import (
    require_consumer_identity,  # noqa: PLC0415 — new module, REQ-003
)

# After:
# (require_consumer_identity import removed — no longer needed here)
```

#### Step 2: Update ack_event function

```python
# Before:
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
    _identity: Annotated[dict, Depends(require_consumer_identity)] = {},  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    db = get_db(request)
    cfg = get_config(request)
    return await _do_ack(db, cfg, event_id, consumer_id)

# After:
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
    _role: Role | None = None,  # Resolved by FastAPI DI in app.py wrapper
    _identity: dict[str, Any] | None = None,  # Resolved by FastAPI DI in app.py wrapper
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    db = get_db(request)
    cfg = get_config(request)
    return await _do_ack(db, cfg, event_id, consumer_id)
```

#### Step 3: Update nack function

```python
# Before:
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    _identity: Annotated[dict, Depends(require_consumer_identity)] = {},  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    db = get_db(request)
    cfg = get_config(request)

    def _nack_and_promote() -> tuple[int, bool]:
        """Nack an event and promote to DLQ if max retries exceeded.

        DLQ promotion is gated on delivery_failure_count (the lifetime
        failure counter), not cycle_failure_count (which resets per
        requeue/redeliver cycle) — see
        tests/eventbus/test_eventbus_dlq_promotion.py for the intended
        semantics.
        """
        failure_count, _cycle_count = _nack_event(db, event_id)
        if failure_count == -1:
            return (-1, False)
        promoted = False
        if failure_count >= cfg.max_retry:
            from eventbus.dlq import promote_single  # noqa: PLC0415

            promoted = promote_single(db, cfg.deadletter_dir, event_id)
        return (failure_count, promoted)

    failure_count, promoted = await run_with_db_lock(_nack_and_promote)
    if failure_count == -1:
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    if failure_count == -2:
        # Invalid transition: event is already ACKed or DLQ'd
        # Determine which state by checking the event directly
        row = await run_with_db_lock(lambda: db.execute(
            "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone())
        if row and row["acked_at"] is not None:
            raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
        elif row and row["dlq_at"] is not None:
            raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
        else:
            raise HTTPException(status_code=409, detail="invalid NACK transition")
    logger.info(
        "event nacked event_id=%s delivery_failure_count=%d", event_id, failure_count
    )
    result: dict[str, Any] = {
        "event_id": event_id,
        "delivery_failure_count": failure_count,
    }
    if promoted:
        result["dlq_promoted"] = True
    return result

# After:
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    _role: Role | None = None,  # Resolved by FastAPI DI in app.py wrapper
    _identity: dict[str, Any] | None = None,  # Resolved by FastAPI DI in app.py wrapper
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    db = get_db(request)
    cfg = get_config(request)

    def _nack_and_promote() -> tuple[int, bool]:
        """Nack an event and promote to DLQ if max retries exceeded.

        DLQ promotion is gated on delivery_failure_count (the lifetime
        failure counter), not cycle_failure_count (which resets per
        requeue/redeliver cycle) — see
        tests/eventbus/test_eventbus_dlq_promotion.py for the intended
        semantics.
        """
        failure_count, _cycle_count = _nack_event(db, event_id)
        if failure_count == -1:
            return (-1, False)
        promoted = False
        if failure_count >= cfg.max_retry:
            from eventbus.dlq import promote_single  # noqa: PLC0415

            promoted = promote_single(db, cfg.deadletter_dir, event_id)
        return (failure_count, promoted)

    failure_count, promoted = await run_with_db_lock(_nack_and_promote)
    if failure_count == -1:
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    if failure_count == -2:
        # Invalid transition: event is already ACKed or DLQ'd
        # Determine which state by checking the event directly
        row = await run_with_db_lock(lambda: db.execute(
            "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone())
        if row and row["acked_at"] is not None:
            raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
        elif row and row["dlq_at"] is not None:
            raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
        else:
            raise HTTPException(status_code=409, detail="invalid NACK transition")
    logger.info(
        "event nacked event_id=%s delivery_failure_count=%d", event_id, failure_count
    )
    result: dict[str, Any] = {
        "event_id": event_id,
        "delivery_failure_count": failure_count,
    }
    if promoted:
        result["dlq_promoted"] = True
    return result
```

## Compatibility considerations

- The `_identity` parameter has been changed from a FastAPI dependency to a regular parameter
- The parameter type has changed from `Annotated[dict, Depends(...)] = {}` to `dict[str, Any] | None = None`
- Existing tests that call these functions directly may need updating to pass the `_identity` parameter

## Security considerations

- Authorization is now enforced at the wrapper function level, ensuring all requests are properly authorized
- The `_identity` parameter is set by FastAPI DI and cannot be bypassed by callers

## Rollback considerations

- If the authorization wiring breaks, roll back to the previous state where authorization was bypassed (security regression)
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Integration: verify role-gated access for each endpoint | pytest tests/eventbus/test_eventbus_auth.py | Wrong-role requests get 403 |
| scripts/eventbus/auth.py::require_consumer_identity | Unit: verify return type is dict with topics key | pytest tests/eventbus/test_eventbus_auth.py | No AttributeError on success path |

## Completion criteria

- [ ] `Depends(require_consumer_identity)` removed from `ack_event` function signature
- [ ] `Depends(require_consumer_identity)` removed from `nack` function signature
- [ ] `_identity` parameter updated to accept a regular dict (not a FastAPI dependency)
- [ ] Import of `require_consumer_identity` removed (if no longer needed)
- [ ] Tests pass with the new authorization model

## Out of scope

- Changes to `scripts/eventbus/app.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/auth.py` (handled in separate procedure document)
- Changes to test files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove Depends declaration from ack_event | Pending | — | — | |
| 2 | Remove Depends declaration from nack | Pending | — | — | |
| 3 | Update parameter names and types | Pending | — | — | |
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
- **Source issue**: issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-111042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-144827
- **Related target files**: scripts/eventbus/ack_route.py
