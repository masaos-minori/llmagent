## 1. Goal
- Fix `server.py` so that MDQ domain exceptions (Validation, Authorization, NotFound, etc.) are returned as `CallToolResponse(is_error=True)` from the `call_tool` endpoint, clearly distinguishing tool-level errors from transport errors.

## 2. Scope
- **In-Scope**:
  - Catch MDQ domain exceptions in `call_tool` endpoint and return `is_error=True`
  - Maintain HTTP 5xx mapping for `MdqDatabaseError`, `MdqIndexNotReadyError`, `MdqConsistencyError` (transport errors)
  - Add `call_tool` level `is_error=True` verification tests to `tests/test_mdq_error_taxonomy.py`
- **Out-of-Scope**:
  - Exception class definition changes in `models.py` (already implemented)
  - Removing FastAPI exception handler (keep for transport errors)
  - DB schema changes

## 3. Requirements
### Functional
- Tool-level errors (`MdqValidationError`, `MdqAuthorizationError`, `MdqNotFoundError`, `MdqIndexNotReadyError`) → `CallToolResponse(is_error=True)` with HTTP 200
- Infrastructure errors (`MdqDatabaseError`, `MdqConsistencyError`) → re-raise for HTTP 5xx (transport error)
- Exception type recorded in audit log `error_kind`

### Non-functional
- MCP spec compliant: tool errors = `is_error=True`, transport errors = HTTP 5xx
- No double-application of exception handler (FastAPI handler only catches exceptions raised outside route handlers)

## 4. Architecture
### Concurrency Model
- No changes to concurrency model; same as existing `call_tool` flow

### Component Boundaries
```
scripts/mcp/mdq/server.py (call_tool endpoint)
  ├── _dispatch_mdq_tool(req.name, req.args) → try/except wrapper
  │     ├── MdqValidationError → CallToolResponse(is_error=True, result=str(exc))
  │     ├── MdqAuthorizationError → CallToolResponse(is_error=True, result=str(exc))
  │     ├── MdqNotFoundError → CallToolResponse(is_error=True, result=str(exc))
  │     ├── MdqIndexNotReadyError → CallToolResponse(is_error=True, result=str(exc))
  │     └── MdqDatabaseError, MdqConsistencyError → re-raise (HTTP 5xx)
  ├── FastAPI exception handler → catches re-raised transport errors
  └── _audit_log() → error_kind recorded per exception type
```

## 5. Module Design
No changes to dependency direction. All changes within `server.py` — no new module imports needed (exception classes already imported from `models.py`).

## 6. Interface Design
### Modified Methods

```python
# server.py
async def call_tool(self, req: CallToolRequest) -> tuple[dict[str, object], int]:
    req_id = req.id or "unknown"
    name = req.name
    args = req.arguments or {}
    req_start = time.monotonic()

    try:
        r = await self._dispatch_mdq_tool(name, args)
        # ... existing success path (unchanged)
    except (MdqValidationError, MdqAuthorizationError, MdqNotFoundError, MdqIndexNotReadyError) as exc:
        # Tool-level error → is_error=True, HTTP 200
        duration_ms = int((time.monotonic() - req_start) * 1000)
        error_kind = type(exc).__name__
        detail_parts = [f"duration_ms={duration_ms}", f"error_kind={error_kind}"]
        self._audit_log(req_id, name, "error", detail_parts)
        return (
            {"is_error": True, "content": [{"type": "text", "text": str(exc)}]},
            200,  # HTTP 200 — MCP spec: tool errors use is_error flag, not HTTP status
        )
    except (MdqDatabaseError, MdqConsistencyError) as exc:
        # Infrastructure error → re-raise for HTTP 5xx
        duration_ms = int((time.monotonic() - req_start) * 1000)
        self._audit_log(req_id, name, "error", [f"duration_ms={duration_ms}", f"error_kind=transport_error"])
        raise
    except Exception as exc:
        # Catch-all for unexpected errors
        duration_ms = int((time.monotonic() - req_start) * 1000)
        self._audit_log(req_id, name, "error", [f"duration_ms={duration_ms}", f"error_kind=unexpected"])
        raise
```

## 7. Data Model & Serialization
No changes to data models. Exception classes already defined in `models.py`; only their handling is changed.

## 8. Error Handling & Resource Lifecycle
### Failure Modes
- `is_error=True` + HTTP 200 may differ from existing client expectations → **Mitigation**: Document MCP spec compliance in code comments (tool errors = `is_error`, transport errors = HTTP 5xx)
- Exception handler double-application → **Mitigation**: FastAPI handler only catches exceptions raised outside route handlers; try/except inside the handler prevents the handler from being called

### Resource Lifecycle
- No connection pooling changes; each operation opens and closes its own connection (unchanged)

## 9. Configuration
No config changes needed. Audit log format unchanged — backward compatible.

## 10. Test Strategy
### Unit Tests
- `test_call_tool_returns_is_error_for_validation_exception`: Mock `MdqValidationError` raised from `_dispatch_mdq_tool`; assert `is_error=True`, HTTP 200, and error content in response
- `test_call_tool_returns_is_error_for_not_found_exception`: Same for `MdqNotFoundError`
- `test_call_tool_returns_http_503_for_database_error`: Mock `MdqDatabaseError` raised from `_dispatch_mdq_tool`; assert HTTP 503 (via FastAPI exception handler)

### Regression Tests
- Full mdq regression: `uv run pytest tests/test_mdq_error_taxonomy.py -x -q`

## 11. Implementation Plan
### Phase 1: call_tool Endpoint Fix
- Wrap `_dispatch_mdq_tool(req.name, req.args)` call in try/except
- Catch tool-level errors and return `CallToolResponse(is_error=True, result=str(exc))` with HTTP 200
- Record exception type in audit log `error_kind`
- Re-raise infrastructure errors for HTTP 5xx (FastAPI exception handler)

### Phase 2: Test Addition
- Add HTTP client-level tests to `tests/test_mdq_error_taxonomy.py`
- Verify `MdqValidationError` → `is_error=True`, HTTP 200
- Verify `MdqNotFoundError` → `is_error=True`, HTTP 200
- Verify `MdqDatabaseError` → HTTP 503 (transport error, not is_error)

### Phase 3: Verification
- Run `uv run pytest tests/test_mdq_error_taxonomy.py -x -q`
- Run lint/type check: `uv run ruff check scripts/mcp/mdq/server.py && uv run mypy scripts/mcp/mdq/server.py`

## 12. Risks / Open Questions
- **UNK-01**: Priority between FastAPI exception handler and try/except inside `call_tool` handler → **Resolution**: FastAPI exception handler only catches exceptions raised outside route handlers; try/except inside the handler prevents the handler from being called. Confirmed by analysis.
- **Risk**: `is_error=True` + HTTP 200 may differ from existing client expectations → **Mitigation**: Document MCP spec compliance in code comments (tool errors = `is_error`, transport errors = HTTP 5xx).
