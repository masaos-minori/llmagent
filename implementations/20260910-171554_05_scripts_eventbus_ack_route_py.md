## Goal

Bind authenticated identity to allowed `consumer_id` before allowing ack/nack operations in `scripts/eventbus/ack_route.py`.

## Scope

- Modify `scripts/eventbus/ack_route.py`:
  - Add authentication dependency to `ack_event()` and `nack()` functions
  - Validate caller's consumer identity against allowed `consumer_id`s
- No other file modifications beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- `scripts/eventbus/auth.py` will be created (REQ-002) with `require_consumer_identity()` dependency.
- Consumer identity binding uses a config-driven allowlist: each `consumer_id` maps to permitted topics.
- The current code accepts an unauthenticated `consumer_id` query parameter (lines 64, 74) with no identity check.

## Design decisions

- **Dependency injection**: Use FastAPI's `Depends(require_consumer_identity())` to inject the permission check into both `ack_event()` and `nack()` handlers.
- **Consumer identity validation**: A caller cannot ack/nack on behalf of another consumer; the authenticated identity determines which `consumer_id` they may use.

## Alternatives considered

- Middleware-level consumer identity validation: Would apply to all routes; route-level validation more precise and necessary for consumer-specific checks.
- Config-driven role-per-consumer mapping: Would require complex ACL; fixed role-to-route mapping sufficient for loopback-only deployment.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

Modify `scripts/eventbus/ack_route.py` to bind authenticated identity to allowed `consumer_id` for ack/nack operations.

### Method

1. Import the authentication dependency from `scripts/eventbus/auth.py`.
2. Add `Depends(require_consumer_identity())` to both `ack_event()` and `nack()` function signatures.
3. Remove the existing unauthenticated `consumer_id` parameter handling.
4. Validate caller's consumer identity before processing ack/nack.

### Details

```python
# scripts/eventbus/ack_route.py — changes only

# After existing imports, add:
from fastapi import Depends, HTTPException  # noqa: F401 — used in function signatures below
from eventbus.auth import require_consumer_identity  # noqa: PLC0415 — new module, REQ-003

async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
    # NEW: Add authentication dependency
    _identity: dict = Depends(require_consumer_identity),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    db = get_db(request)
    cfg = get_config(request)
    return await _do_ack(db, cfg, event_id, consumer_id)

async def nack(
    request: Request,
    event_id: str = Query(default=""),
    # NEW: Add authentication dependency
    _identity: dict = Depends(require_consumer_identity),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    db = get_db(request)
    cfg = get_config(request)

    def _nack_and_promote() -> tuple[int, bool]:
        """Nack an event and promote to DLQ if max retries exceeded."""
        failure_count = _nack_event(db, event_id)
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

- The `Depends(require_consumer_identity())` parameter must be added to both function signatures but does not affect the existing `consumer_id` query parameter behavior.
- The `_identity` dict structure must be consistent with how `require_consumer_identity()` returns data.

## Security considerations

- **Identity binding**: A caller cannot ack/nack on behalf of another consumer; the authenticated identity determines which `consumer_id` they may use.
- **No secret logging**: Authorization failures logged without recording the token value.

## Rollback considerations

- Rolling back this change means removing the authentication dependency and reverting to unauthenticated `consumer_id` acceptance.
- The original behavior (any caller can ack/nack on behalf of any `consumer_id`) would be restored.

## Validation plan

- Integration test: Ack event as consumer_A when consumer_B owns it → expect 403.
- Integration test: Nack event as consumer_A when consumer_B owns it → expect 403.
- Integration test: Ack/nack as authorized consumer → expect success.
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v`.

## Completion criteria

- [ ] Authentication dependency added to `ack_event()` and `nack()` function signatures
- [ ] Consumer identity validation implemented
- [ ] All auth tests passing (positive/negative cases for ack/nack routes)
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Modifying the ack/nack logic itself (offset writing, DLQ promotion, etc.).
- Adding monitoring-specific health/metrics endpoints.
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add authentication dependency to ack_event() | Pending | — | — | |
| 2 | Add authentication dependency to nack() | Pending | — | — | |
| 3 | Implement consumer identity validation | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: scripts/eventbus/ack_route.py
