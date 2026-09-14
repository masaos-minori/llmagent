# Implementation Procedure: Wire principal through ACK/NACK endpoints and update dependency declarations

## Goal

Update `scripts/eventbus/app.py` endpoint dependencies for ACK/NACK routes to pass `Principal` objects instead of raw `Role` values, and make `consumer_id` mandatory for both ACK and NACK endpoints.

## Scope

- Replace `_role: Role = Depends(require_role(...))` with `_principal: Principal = Depends(require_role(...))` for ACK/NACK endpoints.
- Change `consumer_id: str = Query(default="")` to `consumer_id: str = Query(...)` (required) for both ACK and NACK endpoints.
- Update imports to include `Principal`.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The existing route function signatures remain compatible — only the parameter type changes.
- D: REQ-004/REQ-007 require consumer_id to be mandatory for ACK/NACK endpoints.

## Design decisions

- **Parameter name preservation**: Keep `_role` parameter names where possible to minimize downstream changes. If the handler already accepts `_role`, rename to `_principal` only if the handler uses it as a role value (not just passes it through).
- **Import order**: Add `Principal` to the existing `from eventbus.auth import` statement.
- **Mandatory consumer_id**: Use `Query(...)` without default to enforce consumer_id presence.

## Alternatives considered

- **Remove `_role` parameter entirely**: Have handlers derive role information from `Principal.roles` internally. This was rejected because it requires changing every handler's logic — too invasive for a single pass.
- **Keep both parameters temporarily**: Accept both `_role: Role` AND `_principal: Principal` during transition. This adds complexity without security benefit.

## Compatibility considerations

- Route handler functions (`ack_event_route`, `nack_route`) must be updated to accept `Principal` instead of `Role`.
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

#### Step 1: Update imports (REQ-001)

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

#### Step 2: Update /events/{event_id}/ack endpoint dependencies (REQ-001, REQ-004)

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
    """Acknowledge an event as successfully processed by a consumer."""
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
    consumer_id: str = Query(...),  # Required — no default (REQ-004)
    _principal: Principal = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    result: dict[str, Any] = await ack_event_route(
        request,
        event_id=event_id,
        consumer_id=consumer_id,
        _principal=_principal,
        _identity=_identity,
    )
    return result
```

Key changes:
- Parameter renamed from `_role: Role` to `_principal: Principal`.
- `consumer_id` changed from optional (`default=""`) to required (`Query(...)`).
- Handler call updated to pass `_principal` instead of `_role`.

#### Step 3: Update /nack endpoint dependencies (REQ-001, REQ-007)

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
    """Negatively acknowledge an event, triggering retry logic."""
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
    consumer_id: str = Query(...),  # Required — no default (REQ-007)
    _principal: Principal = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    result: dict[str, Any] = await nack_route(
        request, event_id=event_id, _principal=_principal, _identity=_identity
    )
    return result
```

Key changes:
- Parameter renamed from `_role: Role` to `_principal: Principal`.
- `consumer_id` changed from optional (`default=""`) to required (`Query(...)`).
- Handler call updated to pass `_principal` instead of `_role`.

### Details

- REQ-001: `Principal` imported and wired through ACK/NACK endpoint dependencies.
- REQ-004: `consumer_id` made mandatory for ACK endpoint via `Query(...)`.
- REQ-007: `consumer_id` made mandatory for NACK endpoint via `Query(...)`.

## Compatibility considerations

- Route handler functions (`ack_event_route`, `nack_route`) must be updated to accept `Principal` instead of `Role`.
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
| scripts/eventbus/app.py | Integration: all endpoints respond with correct auth status | uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -v | All endpoint tests pass |
| scripts/eventbus/app.py | Static analysis: no type errors | uv run mypy scripts/eventbus/app.py | No new type errors |
| scripts/eventbus/app.py | Lint check | uv run ruff check scripts/eventbus/app.py | No lint errors |

## Completion criteria

- [ ] `Principal` imported in app.py imports section.
- [ ] ACK endpoint uses `_principal: Principal = Depends(require_role(...))`.
- [ ] NACK endpoint uses `_principal: Principal = Depends(require_role(...))`.
- [ ] ACK endpoint `consumer_id` is required (`Query(...)`).
- [ ] NACK endpoint `consumer_id` is required (`Query(...)`).
- [ ] All route handler calls pass `_principal` instead of `_role`.
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
| 2 | Update /events/{event_id}/ack endpoint dependency | Pending | — | — | |
| 3 | Update /nack endpoint dependency | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-004, REQ-007
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-202125
- **Related target files**: scripts/eventbus/app.py
