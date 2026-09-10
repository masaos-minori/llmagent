## Goal

Require operator permission for privileged replay (`/replay`) in `scripts/eventbus/replay_route.py`.

## Scope

- Modify `scripts/eventbus/replay_route.py`:
  - Add authentication dependency to the `replay()` function
  - Require operator role for all replay operations
- No other file modifications beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- `scripts/eventbus/auth.py` will be created (REQ-002) with `require_role(Role.OPERATOR)` dependency.
- The current code has no permission check (confirmed by direct read).
- Privileged replay requires operator permission (resolves UNK-01); all `/replay` calls require operator permission.

## Design decisions

- **Dependency injection**: Use FastAPI's `Depends(require_role(Role.OPERATOR))` to inject the operator permission check into the `replay()` handler.
- **Operator-only access**: All replay operations require operator permission; no distinction between limited/full-history replay permissions.

## Alternatives considered

- Role-per-replay-operation granularity: Would allow consumers to replay their own events; operator-only simpler and consistent with security principle of least privilege.
- Middleware-level operator check: Would apply to all routes; route-level check more precise and necessary for replay-specific authorization.

## Implementation

### Target file

`scripts/eventbus/replay_route.py`

### Procedure

Modify `scripts/eventbus/replay_route.py` to require operator permission for replay operations.

### Method

1. Import the authentication dependency from `scripts/eventbus/auth.py`.
2. Add `Depends(require_role(Role.OPERATOR))` to the `replay()` function signature.
3. Validate operator role before processing replay requests.

### Details

```python
# scripts/eventbus/replay_route.py — changes only

# After existing imports, add:
from fastapi import Depends  # noqa: F401 — used in function signature below
from eventbus.auth import require_role, Role  # noqa: PLC0415 — new module, REQ-004

def _count_events_since(conn: Any, since_seq: int) -> int:
    """Return the total count of events with seq > since_seq."""
    row = conn.execute(
        "SELECT COUNT(*) FROM events WHERE seq > ?", (since_seq,)
    ).fetchone()
    return int(row[0]) if row else 0

async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: str = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    # NEW: Add authentication dependency
    _operator: None = Depends(require_role(Role.OPERATOR)),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Replay events from a given sequence number via SSE or JSON response."""
    db = get_db(request)

    def _fetch() -> list:
        """Fetch events with seq > since_seq within limit/offset bounds."""
        rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
        return rows

    rows = await run_with_db_lock(_fetch)

    if fmt == "json":

        def _count() -> int:
            """Count total events with seq > since_seq for pagination."""
            return _count_events_since(db, since_seq)

        total = await run_with_db_lock(_count)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_row_to_dict(r) for r in rows],
        }

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate SSE stream events from fetched rows."""
        for row in rows:
            data = json_dumps(_row_to_dict(row))
            yield f"data: {data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
```

## Compatibility considerations

- The `Depends(require_role(Role.OPERATOR))` parameter must be added to the function signature but does not affect the existing query parameter behavior.
- The `_operator` variable name is intentionally unused; it serves only to trigger the dependency evaluation.

## Security considerations

- **Operator-only access**: All replay operations require operator permission; no distinction between limited/full-history replay permissions.
- **No secret logging**: Authorization failures logged without recording the token value.

## Rollback considerations

- Rolling back this change means removing the authentication dependency and reverting to unauthenticated replay access.
- The original behavior (any caller can replay any events) would be restored.

## Validation plan

- Integration test: Replay events as non-operator → expect 403.
- Integration test: Replay events as operator → expect success.
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v`.

## Completion criteria

- [ ] Authentication dependency added to `replay()` function signature
- [ ] Operator role validation implemented
- [ ] All auth tests passing (positive/negative cases for replay route)
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Modifying the replay logic itself (SSE streaming, JSON response, pagination, etc.).
- Adding monitoring-specific health/metrics endpoints.
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add authentication dependency to replay() | Pending | — | — | |
| 2 | Implement operator role validation | Pending | — | — | |
| 3 | Add or update tests per Validation plan | Pending | — | — | |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Related target files**: scripts/eventbus/replay_route.py
