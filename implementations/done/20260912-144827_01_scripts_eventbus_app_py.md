## Goal

Move `Depends(require_role(...))` and `Depends(require_consumer_identity)` declarations from delegated-to route functions to the `@app.get/post`-registered wrapper functions in `scripts/eventbus/app.py`, so that FastAPI's dependency injection system resolves them correctly (REQ-001).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/app.py` to add authorization dependencies to wrapper functions
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The `require_role` and `require_consumer_identity` functions will be available in `app.py` scope after being imported from `eventbus.auth`
- The existing `Request` parameter in each wrapper function will continue to provide access to the Bearer token via `request.headers.get("Authorization")`
- The delegated-to route functions will receive resolved role/consumer-identity values as regular parameters instead of relying on FastAPI DI

## Design decisions

- Approach A (declare dependencies on wrapper functions) is preferred over Approach B (explicit invocation within wrappers) because it aligns with FastAPI's idiomatic usage pattern and keeps authorization logic declarative
- Each wrapper function will declare its required role/identity as a `Depends()` default parameter, allowing FastAPI to resolve it during request processing

## Alternatives considered

- Approach B: Explicitly calling `require_role()` / `require_consumer_identity()` as plain awaited functions within each wrapper before delegating — would require duplicating authorization logic in each wrapper function

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Add imports for `Depends`, `require_role`, and `require_consumer_identity` from `fastapi` and `eventbus.auth`
2. Modify each `@app.get/post`-registered wrapper function to include `Depends(require_role(...))` or `Depends(require_consumer_identity)` as a default parameter
3. Pass the resolved role/identity value to the delegated-to route function as a regular parameter
4. Update delegated-to route functions to accept the resolved value as a parameter instead of relying on FastAPI DI

### Method

For each wrapper function:
- Add `Depends(require_role(Role.XXX))` or `Depends(require_consumer_identity)` as a parameter with a default value
- Extract the resolved value from the dependency injection result
- Pass the resolved value to the delegated-to route function

### Details

#### `/publish` endpoint (Role.PUBLISHER)

```python
from fastapi import Depends
from eventbus.auth import require_role, require_consumer_identity
from eventbus.auth import Role

@app.post("/publish")
async def publish(
    request: Request,
    _role: Role = Depends(require_role(Role.PUBLISHER)),
) -> dict[str, Any]:
    """Publish a new event to the event bus."""
    result: dict[str, Any] = await publish_route(request, _role=_role)
    return result
```

#### `/replay` endpoint (Role.OPERATOR)

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
    """Replay events from a given sequence number via SSE or JSON."""
    return await replay_route(
        request, since_seq=since_seq, fmt=fmt, limit=limit, offset=offset, _role=_role
    )
```

#### `/subscribe` endpoint (Role.CONSUMER + consumer identity)

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
    """Subscribe to events matching the specified topics via SSE."""
    return await subscribe_route(
        request, topic=topic, since_seq=since_seq, consumer_id=consumer_id,
        _role=_role, _identity=_identity
    )
```

#### `/dlq` endpoint (Role.OPERATOR)

```python
@app.get("/dlq")
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    """List dead-letter queue entries with pagination support."""
    result: dict[str, Any] = await dlq_list_route(request, limit=limit, offset=offset, _role=_role)
    return result
```

#### `/dlq/{event_id}/requeue` endpoint (Role.OPERATOR)

```python
@app.post("/dlq/{event_id}/requeue")
async def dlq_requeue(
    request: Request,
    event_id: str,
    _role: Role = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active queue."""
    result: dict[str, Any] = await dlq_requeue_route(request, event_id, _role=_role)
    return result
```

#### `/events/{event_id}/ack` endpoint (Role.CONSUMER + consumer identity)

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
        request, event_id=event_id, consumer_id=consumer_id,
        _role=_role, _identity=_identity
    )
    return result
```

#### `/nack` endpoint (Role.CONSUMER + consumer identity)

```python
@app.post("/nack")
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    _role: Role = Depends(require_role(Role.CONSUMER)),
    _identity: dict[str, Any] = Depends(require_consumer_identity),
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    result: dict[str, Any] = await nack_route(request, event_id=event_id, _role=_role, _identity=_identity)
    return result
```

## Compatibility considerations

- The delegated-to route functions (`dlq_route.py`, `subscribe_route.py`, `ack_route.py`, `replay_route.py`) must be updated to accept `_role` and/or `_identity` as regular parameters instead of relying on FastAPI DI
- Existing tests that create local route handlers without going through `app.py`'s wrappers may break and need updating
- The single-shared-token deployment model must not break unless a migration path is designed (REQ-005)

## Security considerations

- Moving authorization to the correct layer ensures all requests are properly authorized
- The `require_role` function must map the caller's Bearer token to a Role using configuration (REQ-002)
- The `require_consumer_identity` function must return a proper dict with a `topics` key (REQ-003)

## Rollback considerations

- If the authorization wiring breaks, roll back to the previous state where authorization was bypassed (security regression)
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Integration: verify role-gated access for each endpoint | pytest tests/eventbus/test_eventbus_auth.py | Wrong-role requests get 403 |
| scripts/eventbus/auth.py::require_role | Unit: verify token→role mapping logic | pytest tests/eventbus/test_eventbus_auth.py | All auth tests pass with per-role tokens |
| scripts/eventbus/auth.py::require_consumer_identity | Unit: verify return type is dict with topics key | pytest tests/eventbus/test_eventbus_auth.py | No AttributeError on success path |

## Completion criteria

- [ ] All `@app.get/post`-registered wrapper functions declare `Depends(require_role(...))` or `Depends(require_consumer_identity)` as appropriate
- [ ] Delegated-to route functions receive resolved role/identity values as regular parameters
- [ ] Authorization checks execute for every request (no bypass)
- [ ] Tests pass with the new authorization model

## Out of scope

- Changes to `scripts/eventbus/auth.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/config.py` (handled in separate procedure document)
- Changes to `config/eventbus.toml` (handled in separate procedure document)
- Changes to test files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move Depends declarations to wrapper functions | Completed | — | — | |
| 2 | Update delegated-to route functions to accept resolved values | Completed | — | — | |
| 3 | Run validation tests | Completed | — | — | |

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
- **Related target files**: scripts/eventbus/app.py
