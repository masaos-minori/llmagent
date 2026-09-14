# Implementation Procedure: Add authorization context to subscribe; validate consumer/topic membership

## Goal

Update `scripts/eventbus/subscribe_route.py` to add authorization context validation for subscribe operations, including validating that the requested consumer belongs to the principal and the requested topics are authorized.

## Scope

- Replace `_role: Role | None` parameter with `_principal: Principal | None`.
- Validate principal owns the requested consumer ID before subscribing.
- Validate principal has access to the requested topics before subscribing.
- Update imports to include `Principal`.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The current subscribe function accepts empty consumer_id and empty topic lists without validation.
- D: The current subscribe function does not validate principal ownership of consumer IDs or topics.

## Design decisions

- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Empty consumer_id semantics**: Empty consumer_id is permitted only when no authorization context is available (legacy mode). When authorization context exists, consumer_id must be non-empty.
- **Empty topic list semantics**: Empty topic list means subscribe to all topics (no filtering). This is unchanged from current behavior.
- **Topic authorization**: If principal has `allowed_topics`, only those topics can be subscribed to. If the requested topic is not in the allowed list, reject with HTTP 403.

## Alternatives considered

- **Keep role-based authorization**: Continue using `_role: Role` for subscribe authorization. This was rejected because it doesn't provide per-consumer/per-topic granularity needed for REQ-011—REQ-013.
- **Separate admin subscribe endpoint**: Create a separate operator-only endpoint for administrative subscription. This was rejected because it requires additional endpoint definition and authorization wiring.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_role: Role | None` parameter declarations.
- The revert is mechanical — no semantic changes beyond restoring original parameter types.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

#### Step 1: Update imports (REQ-011)

Replace the current import statement (lines 13-15):

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

#### Step 2: Update subscribe() function signature and add authorization validation (REQ-011—REQ-013)

Replace the current `subscribe()` function (lines 31-105):

Current code:
```python
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _role: Role | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.db import get_consumer_offset  # noqa: PLC0415, RUF100

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    # _identity is resolved by app.py's route wrapper via
    # Depends(require_consumer_identity) and passed in here as a real dict —
    # the wiring gap this comment used to describe (Depends(...) never
    # actually invoked, tracked by
    # https://github.com/anomalyco/opencode/issues/10) has been closed.
    if _identity is None:
        raise HTTPException(status_code=401, detail="Identity not resolved")

    # Resolve consumer_id from the authenticated identity if not provided
    resolved_consumer_id = consumer_id or _identity.get("consumer_id", "")
    if not resolved_consumer_id:
        raise HTTPException(status_code=400, detail="Missing consumer_id")

    # Resolve topic filter from the authenticated identity if not provided
    resolved_topic = topic or _identity.get("topics", [])
    if isinstance(resolved_topic, str):
        resolved_topic = [resolved_topic]

    # Check if the consumer is already connected
    if broker.is_connected(resolved_consumer_id):
        raise HTTPException(status_code=409, detail=ERR_CONSUMER_ALREADY_CONNECTED)

    # Get the last committed offset for this consumer
    try:
        row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT seq FROM consumer_offsets WHERE consumer_id = ? ORDER BY seq DESC LIMIT 1",
                (resolved_consumer_id,),
            ).fetchone()
        )
        last_committed_seq = row["seq"] if row else 0
    except Exception:
        last_committed_seq = 0

    # Determine the starting sequence number
    start_seq = max(since_seq, last_committed_seq)

    # Start the subscription
    return await _start_subscription(
        request=request,
        consumer_id=resolved_consumer_id,
        topic_filter=resolved_topic,
        start_seq=start_seq,
        _identity=_identity,
    )
```

New code:
```python
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _principal: Principal | None = None,  # set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # set by app.py wrapper
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.db import get_consumer_offset  # noqa: PLC0415, RUF100

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    # _identity is resolved by app.py's route wrapper via
    # Depends(require_consumer_identity) and passed in here as a real dict —
    # the wiring gap this comment used to describe (Depends(...) never
    # actually invoked, tracked by
    # https://github.com/anomalyco/opencode/issues/10) has been closed.
    if _identity is None:
        raise HTTPException(status_code=401, detail="Identity not resolved")

    # Resolve consumer_id from the authenticated identity if not provided
    resolved_consumer_id = consumer_id or _identity.get("consumer_id", "")
    
    # REQ-011: Validate principal owns the requested consumer ID
    if _principal and _principal.allowed_consumer_ids:
        if not resolved_consumer_id:
            raise HTTPException(status_code=400, detail="Missing consumer_id")
        if resolved_consumer_id not in _principal.allowed_consumer_ids:
            logger.warning(
                "Authorization failed: consumer_id=%s not allowed for this caller",
                resolved_consumer_id,
            )
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: consumer_id '{resolved_consumer_id}' not allowed",
            )
    
    # REQ-012: Fail closed when identity resolution is missing
    if not resolved_consumer_id:
        raise HTTPException(status_code=400, detail="Missing consumer_id")

    # Resolve topic filter from the authenticated identity if not provided
    resolved_topic = topic or _identity.get("topics", [])
    if isinstance(resolved_topic, str):
        resolved_topic = [resolved_topic]

    # REQ-013: Validate principal has access to the requested topics
    if _principal and _principal.allowed_topics:
        if resolved_topic:
            for t in resolved_topic:
                if t not in _principal.allowed_topics:
                    logger.warning(
                        "Authorization failed: topic=%s not allowed for this caller",
                        t,
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Forbidden: topic '{t}' not allowed",
                    )
        # If principal has allowed_topics but none match, allow subscribe to all
        # (empty topic list means subscribe to all topics)

    # Check if the consumer is already connected
    if broker.is_connected(resolved_consumer_id):
        raise HTTPException(status_code=409, detail=ERR_CONSUMER_ALREADY_CONNECTED)

    # Get the last committed offset for this consumer
    try:
        row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT seq FROM consumer_offsets WHERE consumer_id = ? ORDER BY seq DESC LIMIT 1",
                (resolved_consumer_id,),
            ).fetchone()
        )
        last_committed_seq = row["seq"] if row else 0
    except Exception:
        last_committed_seq = 0

    # Determine the starting sequence number
    start_seq = max(since_seq, last_committed_seq)

    # Start the subscription
    return await _start_subscription(
        request=request,
        consumer_id=resolved_consumer_id,
        topic_filter=resolved_topic,
        start_seq=start_seq,
        _principal=_principal,
    )
```

Key changes:
- Parameter renamed from `_role: Role | None` to `_principal: Principal | None`.
- Added principal ownership validation for consumer ID (HTTP 403 if not allowed).
- Added topic authorization validation (HTTP 403 if topic not in allowed_topics).
- Updated handler call to pass `_principal` instead of `_role`.

### Details

- REQ-011: Consumer membership validation added to subscribe endpoint.
- REQ-012: Topic authorization validation added to subscribe endpoint.
- REQ-013: Empty topic list semantics preserved (subscribe to all topics).

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_role: Role | None` parameter declarations.
- The revert is mechanical — no semantic changes beyond restoring original parameter types.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/subscribe_route.py | Integration: subscribe with authorized/unauthorized consumers | uv run pytest tests/eventbus/test_eventbus_subscribe.py -v | New subscribe tests pass; existing tests unchanged |
| scripts/eventbus/subscribe_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/subscribe_route.py | Type checking | uv run mypy scripts/eventbus/subscribe_route.py | No new type errors |

## Completion criteria

- [ ] `Principal` imported in subscribe_route.py imports section.
- [ ] subscribe() validates principal owns consumer_id.
- [ ] subscribe() validates principal has access to requested topics.
- [ ] subscribe() passes `_principal` to handler instead of `_role`.
- [ ] Empty topic list semantics preserved (subscribe to all topics).
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
| 2 | Update subscribe() function signature and add authorization validation | Pending | — | — | |

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
- **Requirement ID**: REQ-011, REQ-012, REQ-013
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-202831
- **Related target files**: scripts/eventbus/subscribe_route.py
