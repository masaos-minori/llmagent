# Implementation Procedure: Add privileged-action audit logging for replay operations

## Goal

Update `scripts/eventbus/replay_route.py` to add privileged-action audit logging for replay operations.

## Scope

- Add audit logging for replay operations using the existing `log_privileged_action()` helper.

## Assumptions

- A: The existing `scripts/eventbus/audit.py` module provides the infrastructure for structured audit logging — confirmed by `audit.py:45-145`.
- B: The `log_auth_failure()` and `log_privileged_action()` functions already exist with the correct signature — confirmed by `audit.py:94-145`.
- C: The `_build_audit_record()` function accepts `consumer_id`, `route`, `target`, `outcome`, `error_type`, and optional `detail` — confirmed by `audit.py:59-91`.
- D: The `X-Request-Id` header is already injected by the auth middleware — confirmed by `auth.py:276-281`.
- E: CI-005 has already been resolved and removed from the active inventory — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:313-315`.

## Design decisions

- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for healthy subscription states.

## Alternatives considered

- **Keep single-token design**: Continue using only `auth_token` and per-role tokens. This was rejected because it doesn't provide the granularity needed for REQ-007—REQ-009.
- **Separate authorization config file**: Have a separate YAML/TOML file for authorization rules. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`scripts/eventbus/replay_route.py`

### Procedure

#### Step 1: Import audit helpers (REQ-002, REQ-003)

Add import statements at the top of the file after existing imports:

New code:
```python
from scripts.eventbus.audit import log_privileged_action
```

Key changes:
- Added import for `log_privileged_action` from the audit module.

#### Step 2: Add privileged-action audit logging to replay endpoint (REQ-002, REQ-003)

Replace the current `replay()` function (lines 27-63):

Current code:
```python
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # set by app.py wrapper
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

New code:
```python
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # set by app.py wrapper
) -> Any:
    """Replay events from a given sequence number via SSE or JSON response."""
    db = get_db(request)
    
    # NEW: Emit privileged-action audit record
    log_privileged_action(
        consumer_id=consumer_id_from_request(request),
        route="/replay",
        target=f"seq:{since_seq}",
        detail=f"request_id={request.state.request_id} fmt={fmt} limit={limit}",
    )

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

Key changes:
- Added audit logging for replay operations.
- Used `request.state.request_id` as the request identity.

### Details

- REQ-002: Privileged-action audit logging added to replay endpoint.
- REQ-003: Request ID included in audit records; raw tokens never exposed.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/replay_route.py | Integration: privileged-action audit record emission | uv run pytest tests/eventbus/test_eventbus_auth.py -v | Replay audit test passes |
| scripts/eventbus/replay_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/replay_route.py | Type checking | uv run mypy scripts/eventbus/replay_route.py | No new type errors |

## Completion criteria

- [ ] Audit logging integrated into replay endpoint.
- [ ] Request ID included in audit records.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import audit helpers | Pending | — | — | |
| 2 | Add privileged-action audit logging to replay endpoint | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260914-102405_eventbus05_structured-auth-audit-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173340_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-225158
- **Related target files**: scripts/eventbus/replay_route.py
