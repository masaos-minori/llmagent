## Goal

Remove `Depends(require_role(Role.OPERATOR))` from delegated-to functions in `scripts/eventbus/dlq_route.py` since authorization moves to app.py wrappers (REQ-001).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/dlq_route.py` to remove authorization dependencies
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- Authorization will be handled by the wrapper functions in `app.py` via FastAPI DI
- The `_operator` parameter is no longer needed as a FastAPI dependency
- The existing database operations remain unchanged

## Design decisions

- Remove the `Depends(require_role(Role.OPERATOR))` declaration from both `dlq_list` and `dlq_requeue` functions
- Keep the `_operator` parameter name for backward compatibility but change it to a regular parameter (not a FastAPI dependency)
- The authorization check will be performed by the wrapper function before calling these delegated-to functions

## Alternatives considered

- Keeping the `Depends(...)` declaration and relying on FastAPI DI — would not work because these functions are called as plain functions, not through FastAPI's DI system
- Removing the `_operator` parameter entirely — would break backward compatibility with any code that passes this parameter

## Implementation

### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

1. Remove `Depends(require_role(Role.OPERATOR))` from `dlq_list` function signature
2. Remove `Depends(require_role(Role.OPERATOR))` from `dlq_requeue` function signature
3. Update the `_operator` parameter to be a regular parameter (not a FastAPI dependency)
4. Remove the import of `require_role` if no longer needed

### Method

For each function:
- Change the `_operator` parameter from `Annotated[None, Depends(require_role(Role.OPERATOR))]` to a simple `Any` type hint
- Keep the parameter name for backward compatibility

### Details

#### Step 1: Update imports

```python
# Before:
from eventbus.auth import Role, require_role  # noqa: PLC0415 — new module, REQ-004

# After:
from eventbus.auth import Role  # noqa: PLC0415 — new module, REQ-004
```

#### Step 2: Update dlq_list function

```python
# Before:
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """List dead-letter queue entries with pagination support."""
    db = get_db(request)

    def _dlq_count() -> int:
        """Count total events in the dead letter queue."""
        count: int = count_dlq(db)
        return count

    def _dlq_fetch() -> list:
        """Fetch paginated events from the dead letter queue."""
        rows: list = fetch_dlq(db, limit=limit, offset=offset)
        return rows

    total = await run_with_db_lock(_dlq_count)
    rows = await run_with_db_lock(_dlq_fetch)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(r) for r in rows],
    }

# After:
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # Resolved by FastAPI DI in app.py wrapper
) -> dict[str, Any]:
    """List dead-letter queue entries with pagination support."""
    db = get_db(request)

    def _dlq_count() -> int:
        """Count total events in the dead letter queue."""
        count: int = count_dlq(db)
        return count

    def _dlq_fetch() -> list:
        """Fetch paginated events from the dead letter queue."""
        rows: list = fetch_dlq(db, limit=limit, offset=offset)
        return rows

    total = await run_with_db_lock(_dlq_count)
    rows = await run_with_db_lock(_dlq_fetch)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(r) for r in rows],
    }
```

#### Step 3: Update dlq_requeue function

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
    _role: Role | None = None,  # Resolved by FastAPI DI in app.py wrapper
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
```

## Compatibility considerations

- The `_operator` parameter has been renamed to `_role` to better reflect its purpose
- The parameter type has changed from `Annotated[None, Depends(...)]` to `Role | None`
- Existing tests that call these functions directly may need updating to pass the `_role` parameter

## Security considerations

- Authorization is now enforced at the wrapper function level, ensuring all requests are properly authorized
- The `_role` parameter is set by FastAPI DI and cannot be bypassed by callers

## Rollback considerations

- If the authorization wiring breaks, roll back to the previous state where authorization was bypassed (security regression)
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Integration: verify role-gated access for each endpoint | pytest tests/eventbus/test_eventbus_auth.py | Wrong-role requests get 403 |
| scripts/eventbus/auth.py::require_role | Unit: verify token→role mapping logic | pytest tests/eventbus/test_eventbus_auth.py | All auth tests pass with per-role tokens |

## Completion criteria

- [ ] `Depends(require_role(Role.OPERATOR))` removed from `dlq_list` function signature
- [ ] `Depends(require_role(Role.OPERATOR))` removed from `dlq_requeue` function signature
- [ ] `_operator` parameter renamed to `_role` with appropriate type hint
- [ ] Import of `require_role` removed (if no longer needed)
- [ ] Tests pass with the new authorization model

## Out of scope

- Changes to `scripts/eventbus/app.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/auth.py` (handled in separate procedure document)
- Changes to test files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove Depends declarations from dlq_list | Pending | — | — | |
| 2 | Remove Depends declarations from dlq_requeue | Pending | — | — | |
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
- **Related target files**: scripts/eventbus/dlq_route.py
