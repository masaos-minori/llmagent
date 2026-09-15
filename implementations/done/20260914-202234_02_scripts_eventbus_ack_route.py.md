# Implementation Procedure: Remove consumer-less fallback; add principal ownership validation; add consumer_id requirement

## Goal

Update `scripts/eventbus/ack_route.py` to remove the consumer-less fallback path, add principal ownership validation, and make consumer_id mandatory for both ACK and NACK endpoints.

## Scope

- Replace the consumer-less fallback in `_do_ack()` with a mandatory consumer_id check.
- Add principal ownership validation to both ACK and NACK endpoints.
- Add event delivery verification before accepting ACK/NACK.
- Update function signatures to accept `Principal` instead of `Role`.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The current `_do_ack()` function has a consumer-less fallback path that needs to be removed.
- D: The current `nack()` function does not validate consumer_id or principal ownership.

## Design decisions

- **Mandatory consumer_id**: Replace the consumer-less fallback with a check that raises HTTP 400 if consumer_id is empty.
- **Principal ownership validation**: Validate that the requested consumer ID belongs to the principal using `principal.allowed_consumer_ids`.
- **Event delivery verification**: Verify the event was delivered to the consumer before accepting ACK/NACK.
- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.

## Alternatives considered

- **Keep consumer-less fallback temporarily**: Have it log a deprecation warning before removing. This adds complexity without security benefit.
- **Separate admin ACK endpoint**: Create a separate operator-only endpoint for administrative ACK. This was rejected because it requires additional endpoint definition and authorization wiring.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_do_ack()` consumer-less fallback logic.
- The revert is mechanical — no semantic changes beyond restoring original function signatures.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

#### Step 1: Update imports (REQ-001)

Replace the current import statement (lines 9-11):

Current code:
```python
from eventbus.auth import (
    Role,
)
```

New code:
```python
from eventbus.auth import (
    Principal,
    Role,
)
```

#### Step 2: Update _do_ack() to require consumer_id and validate principal ownership (REQ-002, REQ-003, REQ-004, REQ-005)

Replace the current `_do_ack()` function (lines 29-75):

Current code:
```python
async def _do_ack(
    db: Any,
    cfg: Any,
    event_id: str,
    consumer_id: str = "",
    _role: Role | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Common ack logic shared by /ack and /events/{event_id}/ack."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    def _ack_and_offset() -> tuple[bool, bool, int | None]:
        """Acknowledge an event atomically (delivery + offset in one transaction).

        ack_event_for_consumer() requires a non-empty consumer_id (it tracks
        a per-consumer offset); fall back to the plain, consumer-less
        ack_event() when the caller didn't supply one, matching this
        endpoint's own consumer_id: str = Query(default="") contract.
        """
        from eventbus.db import ack_event as _ack_event_plain  # noqa: PLC0415
        from eventbus.db import ack_event_for_consumer  # noqa: PLC0415

        now = now_iso()
        if consumer_id:
            found, newly_acked, seq = ack_event_for_consumer(
                db, event_id, consumer_id, now
            )
            return (found, newly_acked, seq)
        found, newly_acked = _ack_event_plain(db, event_id, now)
        return (found, newly_acked, None)

    found, newly_acked, seq = await run_with_db_lock(_ack_and_offset)
    # Check found first: ack_event_for_consumer()'s INSERT OR IGNORE into
    # consumer_delivery has no FK enforcement against events, so
    # newly_acked can be True even for a nonexistent event_id (found=False,
    # seq=None in that case) — found is the authoritative existence check.
    if not found:
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    resp: dict[str, Any] = {"event_id": event_id, "acked": True}
    if newly_acked:
        logger.info("event acked event_id=%s", event_id)
        resp["seq"] = seq
        return resp
    logger.debug("event already acked event_id=%s", event_id)
    resp["already_acked"] = True
    return resp
```

New code:
```python
async def _do_ack(
    db: Any,
    cfg: Any,
    event_id: str,
    consumer_id: str,  # Required — no default (REQ-004)
    _principal: Principal | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Common ack logic shared by /ack and /events/{event_id}/ack."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)
    
    # REQ-004: consumer_id is mandatory for consumer ACK
    if not consumer_id:
        raise HTTPException(status_code=400, detail="consumer_id is required for consumer ACK")
    
    # REQ-002: Validate principal owns the consumer_id
    if _principal and _principal.allowed_consumer_ids and consumer_id not in _principal.allowed_consumer_ids:
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )
    
    # REQ-003: Verify event was delivered to this consumer before accepting ACK
    try:
        row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
                (consumer_id, event_id),
            ).fetchone()
        )
        if row is None:
            # Event not delivered to this consumer — reject
            raise HTTPException(status_code=409, detail="Event not delivered to this consumer")
    except Exception:
        # If we can't verify delivery state, fail closed
        raise HTTPException(status_code=409, detail="Event not delivered to this consumer")

    def _ack_and_offset() -> tuple[bool, bool, int | None]:
        """Acknowledge an event atomically (delivery + offset in one transaction).

        ack_event_for_consumer() requires a non-empty consumer_id (it tracks
        a per-consumer offset). The consumer-less ack_event() path has been
        removed — all consumer-scoped operations must be attributable.
        """
        from eventbus.db import ack_event_for_consumer  # noqa: PLC0415

        now = now_iso()
        found, newly_acked, seq = ack_event_for_consumer(
            db, event_id, consumer_id, now
        )
        return (found, newly_acked, seq)

    found, newly_acked, seq = await run_with_db_lock(_ack_and_offset)
    # Check found first: ack_event_for_consumer()'s INSERT OR IGNORE into
    # consumer_delivery has no FK enforcement against events, so
    # newly_acked can be True even for a nonexistent event_id (found=False,
    # seq=None in that case) — found is the authoritative existence check.
    if not found:
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    resp: dict[str, Any] = {"event_id": event_id, "acked": True}
    if newly_acked:
        logger.info("event acked event_id=%s", event_id)
        resp["seq"] = seq
        return resp
    logger.debug("event already acked event_id=%s", event_id)
    resp["already_acked"] = True
    return resp
```

Key changes:
- Removed consumer-less fallback (`_ack_event_plain`) — all consumer-scoped operations must be attributable.
- Added mandatory consumer_id check (HTTP 400 if empty).
- Added principal ownership validation (HTTP 403 if consumer_id not in principal.allowed_consumer_ids).
- Added event delivery verification before accepting ACK (HTTP 409 if event not delivered to consumer).
- Parameter renamed from `_role: Role | None` to `_principal: Principal | None`.

#### Step 3: Update ack_event() function signature (REQ-001)

Replace the current `ack_event()` function (lines 78-88):

Current code:
```python
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
    _role: Role | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    db = get_db(request)
    cfg = get_config(request)
    return await _do_ack(db, cfg, event_id, consumer_id)
```

New code:
```python
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(...),  # Required — no default (REQ-004)
    _principal: Principal | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    db = get_db(request)
    cfg = get_config(request)
    return await _do_ack(db, cfg, event_id, consumer_id, _principal=_principal)
```

Key changes:
- `consumer_id` changed from optional (`default=""`) to required (`Query(...)`).
- Parameter renamed from `_role: Role | None` to `_principal: Principal | None`.
- Handler call updated to pass `_principal` instead of `_role`.

#### Step 4: Update nack() function to require consumer_id and validate principal ownership (REQ-007, REQ-008, REQ-009)

Replace the current `nack()` function (lines 91-149):

Current code:
```python
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    _role: Role | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
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
        row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
        )
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

New code:
```python
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    consumer_id: str = Query(...),  # Required — no default (REQ-007)
    _principal: Principal | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)
    
    # REQ-007: consumer_id is mandatory for NACK
    if not consumer_id:
        raise HTTPException(status_code=400, detail="consumer_id is required for NACK")
    
    # REQ-008: Validate principal owns the consumer_id
    if _principal and _principal.allowed_consumer_ids and consumer_id not in _principal.allowed_consumer_ids:
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )
    
    # REQ-009: Verify event was delivered to this consumer before accepting NACK
    try:
        row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
                (consumer_id, event_id),
            ).fetchone()
        )
        if row is None:
            # Event not delivered to this consumer — reject
            raise HTTPException(status_code=409, detail="Event not delivered to this consumer")
    except Exception:
        # If we can't verify delivery state, fail closed
        raise HTTPException(status_code=409, detail="Event not delivered to this consumer")

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
        row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
        )
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

Key changes:
- Added mandatory consumer_id check (HTTP 400 if empty).
- Added principal ownership validation (HTTP 403 if consumer_id not in principal.allowed_consumer_ids).
- Added event delivery verification before accepting NACK (HTTP 409 if event not delivered to consumer).
- Parameter renamed from `_role: Role | None` to `_principal: Principal | None`.

### Details

- REQ-001: `Principal` imported and wired through ACK/NACK endpoint dependencies.
- REQ-002: Principal ownership validation added to ACK endpoint.
- REQ-003: Event delivery verification added to ACK endpoint.
- REQ-004: `consumer_id` made mandatory for ACK endpoint via `Query(...)`.
- REQ-005: Consumer-less fallback removed from ACK endpoint.
- REQ-006: Administrative override handled separately (not implemented here).
- REQ-007: `consumer_id` made mandatory for NACK endpoint via `Query(...)`.
- REQ-008: Principal ownership validation added to NACK endpoint.
- REQ-009: Event delivery verification added to NACK endpoint.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_do_ack()` consumer-less fallback logic.
- The revert is mechanical — no semantic changes beyond restoring original function signatures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/ack_route.py | Unit: ownership validation contract; Integration: consumer mismatch scenarios | uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -v | All new tests pass; existing tests unchanged |
| scripts/eventbus/ack_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/ack_route.py | Type checking | uv run mypy scripts/eventbus/ack_route.py | No new type errors |

## Completion criteria

- [ ] `Principal` imported in ack_route.py imports section.
- [ ] `_do_ack()` removes consumer-less fallback path.
- [ ] `_do_ack()` validates principal owns consumer_id.
- [ ] `_do_ack()` verifies event delivered to consumer before accepting ACK.
- [ ] `ack_event()` requires consumer_id (`Query(...)`).
- [ ] `nack()` requires consumer_id (`Query(...)`).
- [ ] `nack()` validates principal owns consumer_id.
- [ ] `nack()` verifies event delivered to consumer before accepting NACK.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update imports to include Principal | Pending | — | — | |
| 2 | Update _do_ack() to require consumer_id and validate principal ownership | Pending | — | — | |
| 3 | Update ack_event() function signature | Pending | — | — | |
| 4 | Update nack() function to require consumer_id and validate principal ownership | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-007, REQ-008, REQ-009
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-202234
- **Related target files**: scripts/eventbus/ack_route.py
