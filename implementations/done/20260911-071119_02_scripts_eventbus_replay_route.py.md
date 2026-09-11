## Goal

Combine the `_fetch()` and `_count()` calls into a single `run_with_db_lock()`-wrapped closure so each JSON response's `total` and `items` represent one internally consistent database snapshot. Also add `Literal["sse", "json"]` constraint to the route handler signature.

## Scope

Modify `scripts/eventbus/replay_route.py`:
- Combine `_fetch()`/_count() into single locked closure (REQ-003; `scripts/eventbus/replay_route.py`).
- Add `Literal["sse", "json"]` constraint to route handler signature (REQ-001; `scripts/eventbus/replay_route.py`).
- Verify `ORDER BY seq` is preserved after refactoring (REQ-005; `scripts/eventbus/replay_route.py`).

## Assumptions

- Combining `_fetch()`/`_count()` into a single closure means the DB connection must remain open for the duration of both queries — this is safe since SQLite supports concurrent readers.
- The default `format` value should remain `"sse"` — changing the default would break existing clients.
- No other callers beyond the FastAPI routing layer use the `fmt` parameter directly.

## Design decisions

1. **Snapshot consistency (REQ-003)**: Combine `_fetch()` and `_count()` into a single closure that executes both queries inside the same `run_with_db_lock()` call. This ensures the lock is held across both reads, preventing interleaving with `/publish`.

2. **Format validation approach (REQ-001)**: Use `Literal["sse", "json"]` type annotation on the `fmt` query parameter in both `app.py` and `replay_route.py`. If FastAPI doesn't support Literal on query params, fall back to a custom `Enum` class.

3. **Precedence of defaults**: Keep `default="sse"` for backward compatibility. If a client sends `?format=json`, they get a JSON response; otherwise, SSE streaming.

4. **Validation mechanism**: Rely on FastAPI's built-in validation — no manual validation needed. Unsupported values will be rejected with HTTP 422 automatically.

5. **OpenAPI exposure**: FastAPI will automatically document the `Literal` type in the OpenAPI schema, listing only `sse` and `json` as valid values.

## Alternatives considered

- Using a custom `Enum` class instead of `Literal`: more verbose but guaranteed to work with all FastAPI versions.
- Adding manual validation logic: unnecessary complexity when FastAPI provides automatic validation.
- Accepting any string value and validating downstream: defeats the purpose of strict API contract enforcement.

## Implementation
### Target file
`scripts/eventbus/replay_route.py`

### Procedure
1. Phase 1: Preparation — Add format validation to the replay route handler
2. Phase 2: Core Logic — Combine _fetch()/_count() into single locked closure

### Method
#### Phase 1: Preparation
- [ ] Add `Literal["sse", "json"]` constraint to `fmt` query parameter in `replay_route.py` (REQ-001; `scripts/eventbus/replay_route.py`)
- [ ] If Literal doesn't work with FastAPI query params, define `class ReplayFormat(str, Enum): sse = "sse"; json = "json"` and use `ReplayFormat` as the type (REQ-001; `scripts/eventbus/replay_route.py`)

#### Phase 2: Core Logic
- [ ] Create `combined_fetch_and_count(conn, db, since_seq, limit, offset)` function that runs both queries inside one closure (REQ-003; `scripts/eventbus/replay_route.py`)
- [ ] Replace the two separate `run_with_db_lock()` calls with a single call to the combined function (REQ-003; `scripts/eventbus/replay_route.py`)
- [ ] Verify `ORDER BY seq` is preserved in the SQL queries within the combined function (REQ-005; `scripts/eventbus/replay_route.py`)

### Details

**Phase 1: Preparation**

Add `Literal["sse", "json"]` type annotation to the `fmt` query parameter in the `/replay` route handler in `replay_route.py`:

```python
from typing import Literal

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

If FastAPI doesn't support `Literal` on query params, replace with a custom `Enum`:

```python
from enum import Enum

class ReplayFormat(str, Enum):
    sse = "sse"
    json = "json"

async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: ReplayFormat = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Replay events from a given sequence number via SSE or JSON response."""
    db = get_db(request)

    def _fetch() -> list:
        """Fetch events with seq > since_seq within limit/offset bounds."""
        rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
        return rows

    rows = await run_with_db_lock(_fetch)

    if fmt == ReplayFormat.json:

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

**Phase 2: Core Logic**

Create a combined function that executes both queries inside the same `run_with_db_lock()` call:

```python
def _fetch_and_count(conn, db, since_seq, limit, offset):
    """Fetch events and count total under one lock acquisition."""
    rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
    total = _count_events_since(db, since_seq)
    return rows, total

# In the replay function, replace the two separate run_with_db_lock calls:
rows, total = await run_with_db_lock(lambda: _fetch_and_count(db, since_seq, limit, offset))
return {
    "total": total,
    "limit": limit,
    "offset": offset,
    "items": [_row_to_dict(r) for r in rows],
}
```

Verify `ORDER BY seq` is preserved in the SQL queries within the combined function by checking `db.py` line 215 (`fetch_events_since()`).

## Compatibility considerations

- Existing clients sending unsupported format values will now receive HTTP 422 errors instead of silent SSE fallback. Document this breaking change clearly.
- No changes needed to callers — `EventBusConfig` construction remains the same.

## Security considerations

- Adding `Literal["sse", "json"]` prevents injection of arbitrary format strings into the replay endpoint.
- Invalid combinations fail startup with actionable errors rather than silently producing misleading health status.

## Rollback considerations

- Reverting the format validation requires reverting the type annotation and ensuring no downstream dependencies rely on the new behavior.
- If reverted during runtime, the dataclass defaults ensure behavior reverts to original hardcoded values.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/app.py` | Unit — format validation | `uv run pytest tests/eventbus/test_eventbus_replay_pagination.py -k "invalid_format" -v` | 422 returned for unsupported formats |
| `scripts/eventbus/app.py` | Integration — OpenAPI schema | `uv run pytest tests/eventbus/test_eventbus_replay_pagination.py -k "enum" -v` | OpenAPI lists only `sse` and `json` |
| `scripts/eventbus/replay_route.py` | Integration — snapshot consistency | `uv run pytest tests/eventbus/test_eventbus_replay_pagination.py -k "snapshot" -v` | total/items consistent during concurrent publish |
| `scripts/eventbus/replay_route.py` | Integration — ordering | `uv run pytest tests/eventbus/test_eventbus_replay_pagination.py -k "order" -v` | Pagination ordered by seq |
| `scripts/eventbus/*.py` | Lint | `uv run ruff check scripts/eventbus/app.py scripts/eventbus/replay_route.py` | Clean |
| `scripts/eventbus/*.py` | Type check | `uv run mypy scripts/eventbus/app.py scripts/eventbus/replay_route.py` | Pass |

## Completion criteria

- `Literal["sse", "json"]` added to `fmt` query parameter in `replay_route.py` — REQ-001
- `_fetch()`/_count() combined into single locked closure — REQ-003
- Unsupported format values return HTTP 422 — REQ-002
- OpenAPI schema lists only `sse` and `json` as valid values — REQ-002
- `ORDER BY seq` preserved after refactoring — REQ-005

## Out of scope

- Deriving threshold values from load-test measurement (EB-M05).
- Backpressure disconnect behavior itself (EB-H02).
- Changing the DLQ sweep interval (`_DLQ_INTERVAL = 60.0` in `app.py`).
- Updating broker.py, health_route.py, or documentation (covered by other implementation procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Literal["sse", "json"] to fmt query parameter | Pending | — | — | |
| 2 | Combine _fetch()/_count() into single locked closure | Pending | — | — | |
| 3 | If Literal doesn't work, define ReplayFormat Enum class | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Source issue**: issues/20260907-125042_eb_m04_replay_pagination_snapshot_consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-073144_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-071119
- **Related target files**: scripts/eventbus/replay_route.py
