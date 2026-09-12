## Goal

Remove `Depends(require_consumer_identity)` from delegated-to function in `scripts/eventbus/subscribe_route.py` and keep `isinstance(_identity, dict)` guard (REQ-001, REQ-003).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/subscribe_route.py` to remove authorization dependencies and update identity handling
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- Authorization will be handled by the wrapper functions in `app.py` via FastAPI DI
- The `_identity` parameter will receive a dict-like object with a `topics` key containing a set of permitted topics
- The existing `isinstance(_identity, dict)` guard should be preserved to prevent crashes when `_identity` is not a dict

## Design decisions

- Remove the `Depends(require_consumer_identity)` declaration from the `subscribe` function signature
- Keep the `_identity` parameter but change it to accept a regular dict (not a FastAPI dependency)
- Preserve the `isinstance(_identity, dict)` guard to prevent crashes when `_identity` is not a dict

## Alternatives considered

- Keeping the `Depends(...)` declaration and relying on FastAPI DI — would not work because these functions are called as plain functions, not through FastAPI's DI system
- Removing the `_identity` parameter entirely — would break backward compatibility with any code that passes this parameter

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Remove `Depends(require_consumer_identity)` from `subscribe` function signature
2. Update the `_identity` parameter to be a regular parameter (not a FastAPI dependency)
3. Keep the `isinstance(_identity, dict)` guard
4. Update the topic allowlist check to use the new `_identity` format

### Method

For each function:
- Change the `_identity` parameter from `dict = Depends(require_consumer_identity)` to `dict | None = None`
- Keep the `isinstance(_identity, dict)` guard to prevent crashes
- Update the topic allowlist check to handle the new `_identity` format

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

#### Step 2: Update subscribe function

```python
# Before:
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _identity: dict = Depends(require_consumer_identity),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.db import get_consumer_offset  # noqa: PLC0415, RUF100

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    # _identity is never actually resolved by FastAPI's dependency injection
    # here — this function is called as a plain awaited function from
    # app.py's route wrapper, not registered directly as a route, so the
    # Depends(require_consumer_identity) default (or its None return value)
    # is never a real dict at this point. Skip topic-allowlist enforcement
    # rather than reject every request when identity resolution didn't
    # actually run; see
    # issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
    # for the full authorization gap this is a symptom of.
    if isinstance(_identity, dict):
        caller_topics = _identity.get("topics", set())
        for t in topic:
            if t not in caller_topics:
                raise HTTPException(
                    status_code=403, detail=f"Forbidden: topic '{t}' not allowed"
                )

    # ... rest of the function unchanged ...

# After:
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _role: Role | None = None,  # Resolved by FastAPI DI in app.py wrapper
    _identity: dict[str, Any] | None = None,  # Resolved by FastAPI DI in app.py wrapper
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.db import get_consumer_offset  # noqa: PLC0415, RUF100

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    # Topic allowlist enforcement using resolved identity
    if _identity is not None and isinstance(_identity, dict):
        caller_topics = _identity.get("topics", set())
        for t in topic:
            if t not in caller_topics:
                raise HTTPException(
                    status_code=403, detail=f"Forbidden: topic '{t}' not allowed"
                )

    # ... rest of the function unchanged ...
```

## Compatibility considerations

- The `_identity` parameter has been changed from a FastAPI dependency to a regular parameter
- The parameter type has changed from `dict` to `dict[str, Any] | None`
- Existing tests that call this function directly may need updating to pass the `_identity` parameter

## Security considerations

- Authorization is now enforced at the wrapper function level, ensuring all requests are properly authorized
- The `_identity` parameter is set by FastAPI DI and cannot be bypassed by callers
- The topic allowlist check ensures consumers can only access topics they are authorized for

## Rollback considerations

- If the authorization wiring breaks, roll back to the previous state where authorization was bypassed (security regression)
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Integration: verify role-gated access for each endpoint | pytest tests/eventbus/test_eventbus_auth.py | Wrong-role requests get 403 |
| scripts/eventbus/auth.py::require_consumer_identity | Unit: verify return type is dict with topics key | pytest tests/eventbus/test_eventbus_auth.py | No AttributeError on success path |

## Completion criteria

- [ ] `Depends(require_consumer_identity)` removed from `subscribe` function signature
- [ ] `_identity` parameter updated to accept a regular dict (not a FastAPI dependency)
- [ ] `isinstance(_identity, dict)` guard preserved
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
| 1 | Remove Depends declaration from subscribe | Pending | — | — | |
| 2 | Update _identity parameter type | Pending | — | — | |
| 3 | Preserve isinstance guard | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-111042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-144827
- **Related target files**: scripts/eventbus/subscribe_route.py
