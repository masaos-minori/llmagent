## Goal

Restrict the `/replay` endpoint's `format` query parameter to the closed set `sse`/`json` so that unsupported values return a validation error (HTTP 422) and OpenAPI documents only the supported values.

## Scope

Modify `scripts/eventbus/app.py`:
- Add `Literal["sse", "json"]` constraint to `fmt` query parameter in `app.py` (REQ-001; `scripts/eventbus/app.py`).
- Ensure FastAPI rejects unsupported values with HTTP 422 automatically (REQ-002; `scripts/eventbus/app.py`).
- Verify OpenAPI schema lists only `sse` and `json` as valid values (REQ-002; `scripts/eventbus/app.py`).

## Assumptions

- FastAPI supports `Literal["sse", "json"]` type annotations on query parameters — if not, fall back to a custom `Enum` class.
- The default `format` value should remain `"sse"` — changing the default would break existing clients.
- No other callers beyond the FastAPI routing layer use the `fmt` parameter directly.

## Design decisions

1. **Format validation approach (REQ-001)**: Use `Literal["sse", "json"]` type annotation on the `fmt` query parameter in both `app.py` and `replay_route.py`. If FastAPI doesn't support Literal on query params, fall back to a custom `Enum` class.

2. **Precedence of defaults**: Keep `default="sse"` for backward compatibility. If a client sends `?format=json`, they get a JSON response; otherwise, SSE streaming.

3. **Validation mechanism**: Rely on FastAPI's built-in validation — no manual validation needed. Unsupported values will be rejected with HTTP 422 automatically.

4. **OpenAPI exposure**: FastAPI will automatically document the `Literal` type in the OpenAPI schema, listing only `sse` and `json` as valid values.

## Alternatives considered

- Using a custom `Enum` class instead of `Literal`: more verbose but guaranteed to work with all FastAPI versions.
- Adding manual validation logic: unnecessary complexity when FastAPI provides automatic validation.
- Accepting any string value and validating downstream: defeats the purpose of strict API contract enforcement.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Phase 1: Preparation — Add format validation to the replay route handler

### Method
#### Phase 1: Preparation
- [ ] Add `Literal["sse", "json"]` constraint to `fmt` query parameter in `app.py` (REQ-001; `scripts/eventbus/app.py`)
- [ ] If Literal doesn't work with FastAPI query params, define `class ReplayFormat(str, Enum): sse = "sse"; json = "json"` and use `ReplayFormat` as the type (REQ-001; `scripts/eventbus/replay_route.py`)

### Details

**Phase 1: Preparation**

Add `Literal["sse", "json"]` type annotation to the `fmt` query parameter in the `/replay` route handler in `app.py`:

```python
from typing import Literal

@app.get("/replay")
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
    """Replay events from a given sequence number via SSE or JSON."""
    return await replay_route(
        request,
        since_seq=since_seq,
        fmt=fmt,
        limit=limit,
        offset=offset,
    )
```

If FastAPI doesn't support `Literal` on query params, replace with a custom `Enum`:

```python
from enum import Enum

class ReplayFormat(str, Enum):
    sse = "sse"
    json = "json"

@app.get("/replay")
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: ReplayFormat = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
    """Replay events from a given sequence number via SSE or JSON."""
    return await replay_route(
        request,
        since_seq=since_seq,
        fmt=fmt,
        limit=limit,
        offset=offset,
    )
```

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
| `scripts/eventbus/*.py` | Lint | `uv run ruff check scripts/eventbus/app.py scripts/eventbus/replay_route.py` | Clean |
| `scripts/eventbus/*.py` | Type check | `uv run mypy scripts/eventbus/app.py scripts/eventbus/replay_route.py` | Pass |

## Completion criteria

- `Literal["sse", "json"]` added to `fmt` query parameter in `app.py` — REQ-001
- Unsupported format values return HTTP 422 — REQ-002
- OpenAPI schema lists only `sse` and `json` as valid values — REQ-002

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
| 2 | If Literal doesn't work, define ReplayFormat Enum class | Pending | — | — | |
| 3 | Add or update tests per Validation plan | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260907-125042_eb_m04_replay_pagination_snapshot_consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-073144_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-071119
- **Related target files**: scripts/eventbus/app.py
