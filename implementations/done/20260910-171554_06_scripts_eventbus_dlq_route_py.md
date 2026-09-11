## Goal

Require operator permission for DLQ administration (`dlq_list`, `dlq_requeue`) in `scripts/eventbus/dlq_route.py`.

## Scope

- Modify `scripts/eventbus/dlq_route.py`:
  - Add authentication dependency to `dlq_list()` and `dlq_requeue()` functions
  - Require operator role for all DLQ operations
- No other file modifications beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- `scripts/eventbus/auth.py` will be created (REQ-002) with `require_role(Role.OPERATOR)` dependency.
- The current code has no permission check (confirmed by direct read).
- DLQ administration is privileged; only operators should access DLQ entries.

## Design decisions

- **Dependency injection**: Use FastAPI's `Depends(require_role(Role.OPERATOR))` to inject the operator permission check into both `dlq_list()` and `dlq_requeue()` handlers.
- **Operator-only access**: All DLQ operations require operator permission; no distinction between list/requeue permissions.

## Alternatives considered

- Role-per-DLQ-operation granularity: Would allow consumers to list their own DLQ entries; operator-only simpler and consistent with security principle of least privilege.
- Middleware-level operator check: Would apply to all routes; route-level check more precise and necessary for DLQ-specific authorization.

## Implementation

### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

Modify `scripts/eventbus/dlq_route.py` to require operator permission for DLQ list and requeue operations.

### Method

1. Import the authentication dependency from `scripts/eventbus/auth.py`.
2. Add `Depends(require_role(Role.OPERATOR))` to both `dlq_list()` and `dlq_requeue()` function signatures.
3. Validate operator role before processing DLQ requests.

### Details

```python
# scripts/eventbus/dlq_route.py — changes only

# After existing imports, add:
from fastapi import Depends  # noqa: F401 — used in function signatures below
from eventbus.auth import require_role, Role  # noqa: PLC0415 — new module, REQ-004

async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    # NEW: Add authentication dependency
    _operator: None = Depends(require_role(Role.OPERATOR)),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
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

async def dlq_requeue(request: Request, event_id: str) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue."""
    db = get_db(request)
    cfg = get_config(request)

    # NEW: Add authentication dependency
    _operator: None = Depends(require_role(Role.OPERATOR))  # noqa: ANN001,ANN202 — FastAPI dependency protocol

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

- The `Depends(require_role(Role.OPERATOR))` parameter must be added to both function signatures but does not affect the existing query parameter behavior.
- The `_operator` variable name is intentionally unused; it serves only to trigger the dependency evaluation.

## Security considerations

- **Operator-only access**: All DLQ operations require operator permission; no distinction between list/requeue permissions.
- **No secret logging**: Authorization failures logged without recording the token value.

## Rollback considerations

- Rolling back this change means removing the authentication dependency and reverting to unauthenticated DLQ access.
- The original behavior (any caller can administer the DLQ) would be restored.

## Validation plan

- Integration test: List DLQ as non-operator → expect 403.
- Integration test: Requeue DLQ entry as non-operator → expect 403.
- Integration test: List/requeue as operator → expect success.
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v`.

## Completion criteria

- [ ] Authentication dependency added to `dlq_list()` and `dlq_requeue()` function signatures
- [ ] Operator role validation implemented
- [ ] All auth tests passing (positive/negative cases for DLQ routes)
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Modifying the DLQ list/requeue logic itself (pagination, offset recovery, etc.).
- Adding monitoring-specific health/metrics endpoints.
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add authentication dependency to dlq_list() | Completed | — | — | |
| 2 | Add authentication dependency to dlq_requeue() | Completed | — | — | |
| 3 | Implement operator role validation | Completed | — | — | |
| 4 | Add or update tests per Validation plan | Completed | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Completed | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: scripts/eventbus/dlq_route.py
