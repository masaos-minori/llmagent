## Goal

Remove `Depends(require_role(Role.OPERATOR))` from delegated-to function in `scripts/eventbus/replay_route.py` since authorization moves to app.py wrappers (REQ-001).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/replay_route.py` to remove authorization dependencies
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- Authorization will be handled by the wrapper functions in `app.py` via FastAPI DI
- The `_operator` parameter is no longer needed as a FastAPI dependency
- The existing database operations remain unchanged

## Design decisions

- Remove the `Depends(require_role(Role.OPERATOR))` declaration from the `replay` function signature
- Keep the `_operator` parameter name for backward compatibility but change it to a regular parameter (not a FastAPI dependency)
- The authorization check will be performed by the wrapper function before calling these delegated-to functions

## Alternatives considered

- Keeping the `Depends(...)` declaration and relying on FastAPI DI — would not work because these functions are called as plain functions, not through FastAPI's DI system
- Removing the `_operator` parameter entirely — would break backward compatibility with any code that passes this parameter

## Implementation

### Target file

`scripts/eventbus/replay_route.py`

### Procedure

1. Remove `Depends(require_role(Role.OPERATOR))` from `replay` function signature
2. Update the `_operator` parameter to be a regular parameter (not a FastAPI dependency)
3. Remove the import of `require_role` if no longer needed

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

#### Step 2: Update replay function

```python
# Before:
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Replay events from a given sequence number via SSE or JSON response."""
    db = get_db(request)

    def _fetch_and_count(since_seq: int, limit: int, offset: int):
        """Fetch events and count total under one lock acquisition."""
        rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
        total = _count_events_since(db, since_seq)
        return rows, total

    rows, total = await run_with_db_lock(
        lambda: _fetch_and_count(since_seq, limit, offset)
    )

    if fmt == "json":
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_row_to_dict(r) for r in rows],
        }

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate SSE stream events from fetched rows."""
        for row in rows:
            seq = row[0]
            data = json_dumps(_row_to_dict(row))
            yield f"id:{seq}\ndata:{data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")

# After:
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # Resolved by FastAPI DI in app.py wrapper
) -> Any:
    """Replay events from a given sequence number via SSE or JSON response."""
    db = get_db(request)

    def _fetch_and_count(since_seq: int, limit: int, offset: int):
        """Fetch events and count total under one lock acquisition."""
        rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
        total = _count_events_since(db, since_seq)
        return rows, total

    rows, total = await run_with_db_lock(
        lambda: _fetch_and_count(since_seq, limit, offset)
    )

    if fmt == "json":
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_row_to_dict(r) for r in rows],
        }

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate SSE stream events from fetched rows."""
        for row in rows:
            seq = row[0]
            data = json_dumps(_row_to_dict(row))
            yield f"id:{seq}\ndata:{data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
```

## Compatibility considerations

- The `_operator` parameter has been renamed to `_role` to better reflect its purpose
- The parameter type has changed from `Annotated[None, Depends(...)]` to `Role | None`
- Existing tests that call this function directly may need updating to pass the `_role` parameter

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

- [ ] `Depends(require_role(Role.OPERATOR))` removed from `replay` function signature
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
| 1 | Remove Depends declaration from replay | Pending | — | — | |
| 2 | Update parameter names and types | Pending | — | — | |
| 3 | Run validation tests | Pending | — | — | |

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
- **Related target files**: scripts/eventbus/replay_route.py
