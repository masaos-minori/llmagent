# Implementation Procedure: Wire principal through FastAPI endpoint dependencies

## Goal

Update `scripts/eventbus/app.py` endpoint dependencies to accept `Principal` objects returned by `resolve_principal()` instead of raw `Role` values returned by `require_role(Role.XXX)`.

## Scope

- Replace `_role: Role = Depends(require_role(...))` with `_principal: Principal = Depends(require_role(...))`.
- Pass `_principal` to route handler functions instead of `_role`.
- Update imports to include `Principal`.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The route handler functions (`publish_route`, `subscribe_route`, etc.) accept `_role: Role` parameter — after this change, they must accept `_principal: Principal` instead.
- C: The existing route function signatures remain compatible — only the parameter type changes.

## Design decisions

- **Parameter name preservation**: Keep `_role` parameter names where possible to minimize downstream changes. If the handler already accepts `_role`, rename to `_principal` only if the handler uses it as a role value (not just passes it through).
- **Import order**: Add `Principal` to the existing `from eventbus.auth import` statement.

## Alternatives considered

- **Remove `_role` parameter entirely**: Have handlers derive role information from `Principal.roles` internally. This was rejected because it requires changing every handler's logic — too invasive for a single pass.
- **Keep both parameters temporarily**: Accept `_role: Role` AND `_principal: Principal` during transition. This adds complexity without security benefit.

## Compatibility considerations

- Route handler functions (`publish_route`, `subscribe_route`, `ack_event_route`, `nack_route`, `dlq_list_route`, `dlq_requeue_route`, `replay_route`) must be updated to accept `Principal` instead of `Role`.
- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.

## Security considerations

- No new security concerns introduced — the principal model is more restrictive than the previous split design.

## Rollback considerations

- Revert requires restoring original `_role: Role = Depends(require_role(...))` declarations.
- The revert is mechanical — no semantic changes beyond restoring original parameter types.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

#### Step 1: Update imports (REQ-002)

Replace the current import statement (lines 19-25):

Current code:
```python
from eventbus.auth import (
    Role,
    _populate_token_maps,  # noqa: PLC0415 — new module, REQ-004
    attach_auth_middleware,  # noqa: PLC0415 — new module, REQ-002
    require_consumer_identity,
    require_role,
)
```

New code:
```python
from eventbus.auth import (
    Principal,
    Role,
    _populate_token_maps,  # noqa: PLC0415 — new module, REQ-004
    attach_auth_middleware,  # noqa: PLC0415 — new module, REQ-002
    require_consumer_identity,
    require_role,
)
```

#### Step 2: Update /publish endpoint dependency (REQ-003)

Replace the current endpoint definition (lines 154-161):

Current code:
```python
@app.post("/publish")
async def publish(
    request: Request,
    _role: Role = Depends(require_role(Role.PUBLISHER)),
) -> dict[str, Any]:
    result: dict[str, Any] = await publish_route(request, _role=_role)
    return result
```

New code:
```python
@app.post("/publish")
async def publish(
    request: Request,
    _principal: Principal = Depends(require_role(Role.PUBLISHER)),
) -> dict[str, Any]:
    result: dict[str, Any] = await publish_route(request, _principal=_principal)
    return result
```

Key changes:
- Parameter renamed from `_role: Role` to `_principal: Principal`.
- Handler call updated to pass `_principal` instead of `_role`.

#### Step 3: Update /replay endpoint dependency (REQ-003)

Replace the current endpoint definition (lines 164-176):

Current code:
```python
@app.get("/replay")
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role = Depends(require_role(Role.OPERATOR)),
) -> Any:
    return await replay_route(
        request, since_seq=since_seq, fmt=fmt, limit=limit, offset=offset, _role=_role
    )
```

New code:
```python
@app.get("/replay")
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _principal: Principal = Depends(require_role(Role.OPERATOR)),
) -> Any:
    return await replay_route(
        request, since_seq=since_seq, fmt=fmt, limit=limit, offset=offset, _principal=_principal
    )
```

#### Step 4: Update /subscribe endpoint dependencies (REQ-003)

Replace the current endpoint definition (lines 179-196):

Current code:
```python
@app.get("/subscribe")
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _role: Role = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> Any:
    return await subscribe_route(
        request,
        topic=topic,
        since_seq=since_seq,
        consumer_id=consumer_id,
        _role=_role,
        _identity=_identity,
    )
```

New code:
```python
@app.get("/subscribe")
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _principal: Principal = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> Any:
    return await subscribe_route(
        request,
        topic=topic,
        since_seq=since_seq,
        consumer_id=consumer_id,
        _principal=_principal,
        _identity=_identity,
    )
```

#### Step 5: Update /dlq endpoint dependency (REQ-003)

Replace the current endpoint definition (lines 199-210):

Current code:
```python
@app.get("/dlq")
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    result: dict[str, Any] = await dlq_list_route(
        request, limit=limit, offset=offset, _role=_role
    )
    return result
```

New code:
```python
@app.get("/dlq")
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _principal: Principal = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    result: dict[str, Any] = await dlq_list_route(
        request, limit=limit, offset=offset, _principal=_principal
    )
    return result
```

#### Step 6: Update /dlq/{event_id}/requeue endpoint dependency (REQ-003)

Replace the current endpoint definition (lines 213-221):

Current code:
```python
@app.post("/dlq/{event_id}/requeue")
async def dlq_requeue(
    request: Request,
    event_id: str,
    _role: Role = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    result: dict[str, Any] = await dlq_requeue_route(request, event_id, _role=_role)
    return result
```

New code:
```python
@app.post("/dlq/{event_id}/requeue")
async def dlq_requeue(
    request: Request,
    event_id: str,
    _principal: Principal = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    result: dict[str, Any] = await dlq_requeue_route(request, event_id, _principal=_principal)
    return result
```

#### Step 7: Update /events/{event_id}/ack endpoint dependencies (REQ-003)

Replace the current endpoint definition (lines 224-240):

Current code:
```python
@app.post("/events/{event_id}/ack")
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
    _role: Role = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> dict[str, Any]:
    result: dict[str, Any] = await ack_event_route(
        request,
        event_id=event_id,
        consumer_id=consumer_id,
        _role=_role,
        _identity=_identity,
    )
    return result
```

New code:
```python
@app.post("/events/{event_id}/ack")
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
    _principal: Principal = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> dict[str, Any]:
    result: dict[str, Any] = await ack_event_route(
        request,
        event_id=event_id,
        consumer_id=consumer_id,
        _principal=_principal,
        _identity=_identity,
    )
    return result
```

#### Step 8: Update /nack endpoint dependencies (REQ-003)

Replace the current endpoint definition (lines 243-255):

Current code:
```python
@app.post("/nack")
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    consumer_id: str = Query(default=""),
    _role: Role = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> dict[str, Any]:
    result: dict[str, Any] = await nack_route(
        request, event_id=event_id, _role=_role, _identity=_identity
    )
    return result
```

New code:
```python
@app.post("/nack")
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    consumer_id: str = Query(default=""),
    _principal: Principal = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> dict[str, Any]:
    result: dict[str, Any] = await nack_route(
        request, event_id=event_id, _principal=_principal, _identity=_identity
    )
    return result
```

### Details

- REQ-002: `Principal` imported and wired through all endpoint dependencies.
- REQ-003: All endpoint dependencies use `Depends(require_role(...))` returning `Principal`, not `Role`.
- REQ-005: Endpoint dependencies are the sole authentication authority — middleware delegates.

## Compatibility considerations

- Route handler functions (`publish_route`, `subscribe_route`, `ack_event_route`, `nack_route`, `dlq_list_route`, `dlq_requeue_route`, `replay_route`) must be updated to accept `Principal` instead of `Role`.
- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.

## Security considerations

- No new security concerns introduced — the principal model is more restrictive than the previous split design.

## Rollback considerations

- Revert requires restoring original `_role: Role = Depends(require_role(...))` declarations.
- The revert is mechanical — no semantic changes beyond restoring original parameter types.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Integration: all endpoints respond with correct auth status | uv run pytest tests/eventbus/test_eventbus_auth.py -v | All endpoint tests pass |
| scripts/eventbus/app.py | Static analysis: no type errors | uv run mypy scripts/eventbus/app.py | No new type errors |
| scripts/eventbus/app.py | Lint check | uv run ruff check scripts/eventbus/app.py | No lint errors |

## Completion criteria

- [ ] `Principal` imported in app.py imports section.
- [ ] All endpoint dependencies use `_principal: Principal = Depends(require_role(...))`.
- [ ] All route handler calls pass `_principal` instead of `_role`.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update imports to include Principal | Pending | — | — | |
| 2 | Update /publish endpoint dependency | Pending | — | — | |
| 3 | Update /replay endpoint dependency | Pending | — | — | |
| 4 | Update /subscribe endpoint dependencies | Pending | — | — | |
| 5 | Update /dlq endpoint dependency | Pending | — | — | |
| 6 | Update /dlq/{event_id}/requeue endpoint dependency | Pending | — | — | |
| 7 | Update /events/{event_id}/ack endpoint dependencies | Pending | — | — | |
| 8 | Update /nack endpoint dependencies | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-005
- **Source issue**: issues/20260914-102249_eventbus02_principal-based-authentication-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-171329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-195601
- **Related target files**: scripts/eventbus/app.py

## Execution Status

| REQ ID | Description | Status |
|--------|-------------|--------|
| REQ-001 | Import Principal and resolve_principal in app.py | ✅ Implemented |
| REQ-002 | Update publish_route dependency | ✅ Implemented |
| REQ-003 | Update subscribe_route dependency | ✅ Implemented |
| REQ-004 | Update dlq_list_route dependency | ✅ Implemented |
| REQ-005 | Update dlq_requeue_route dependency | ✅ Implemented |
| REQ-006 | Update replay_route dependency | ✅ Implemented |
| REQ-007 | Update ack_event_route dependency | ✅ Implemented |
| REQ-008 | Update nack_route dependency | ✅ Implemented |
| REQ-009 | Update route handler parameters (_role → _principal) | ✅ Implemented |
