# Implementation Procedure Output Template (Canonical)

## Goal

Wire the `x-idempotency-key` header through the `call_tool` endpoint in `rag_pipeline_server.py` to enable end-to-end duplicate detection for side-effecting tool calls.

## Scope

- Add `request: Request` parameter to the `call_tool` function signature (currently missing).
- Import `extract_request_context` from `mcp_servers.server`.
- Call `extract_request_context(request)` inside `call_tool`, capture the third return value as `idempotency_key`.
- Pass `idempotency_key` to `_dispatch_rag_tool()` via keyword argument.
- Update `_dispatch_rag_tool()` helper signature to accept `idempotency_key: str | None = None` and forward it to `dispatch_tool()`.

## Assumptions

- FastAPI explicitly supports injecting `Request` objects into route handler parameters — this is the standard pattern used by Group A handlers.
- `idempotency_key` being `None` should not trigger duplicate detection per `dispatch.py:116`.
- No other mechanism exists in `rag_pipeline_server.py` for tracking request context.

## Design decisions

- Add `request: Request` as a positional parameter after `req: CallToolRequest` in the `call_tool` signature — consistent with Group A handlers.
- Use keyword argument (`idempotency_key=idempotency_key`) when calling `_dispatch_rag_tool()` to make the wiring explicit and avoid positional confusion.
- Default `idempotency_key=None` in `_dispatch_rag_tool()` to maintain backward compatibility with existing callers (e.g., the `MCPServer.dispatch()` method).

## Alternatives considered

- Adding `request: Request` before `req: CallToolRequest` — rejected because FastAPI would bind the first positional parameter to the wrong model.
- Using a dependency injection approach via `Depends(extract_request_context)` — rejected because it changes the function signature semantics and requires additional setup.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Add `from fastapi import Request` to imports (add alongside existing FastAPI imports on line 28).
2. Add `from mcp_servers.server import extract_request_context` to imports (add alongside existing `mcp_servers.server` imports on line 47).
3. Modify `call_tool` function signature: add `request: Request` parameter after `req: CallToolRequest`.
4. Inside `call_tool`, after the availability check succeeds, call `_, _, idempotency_key = extract_request_context(request)` (first two values unused, consistent with Group A pattern where only the key is needed downstream).
5. Change the `_dispatch_rag_tool` call to pass `idempotency_key`: `r = await _dispatch_rag_tool(req.name, req.args, idempotency_key=idempotency_key)`.
6. Update `_dispatch_rag_tool` signature: change `async def _dispatch_rag_tool(name: str, args: ToolArgs)` to `async def _dispatch_rag_tool(name: str, args: ToolArgs, idempotency_key: str | None = None)`.
7. Update the `dispatch_tool` call inside `_dispatch_rag_tool` to forward the key: `return await dispatch_tool(_service.get_dispatch_table(), name, args, idempotency_key=idempotency_key)`.

### Method
Code modification — add parameter, extraction call, and propagation.

### Details
```python
# Before (imports):
from fastapi import FastAPI
...
from mcp_servers.server import MCPServer, ToolArgs, build_tools_response

# After (imports):
from fastapi import FastAPI, Request
...
from mcp_servers.server import MCPServer, ToolArgs, build_tools_response, extract_request_context

# Before (call_tool signature):
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:

# After (call_tool signature):
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:

# Before (call_tool body):
    enabled, reason = _rag_pipeline_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    r = await _dispatch_rag_tool(req.name, req.args)
    return _to_call_tool_response(r)

# After (call_tool body):
    enabled, reason = _rag_pipeline_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    _, _, idempotency_key = extract_request_context(request)
    r = await _dispatch_rag_tool(req.name, req.args, idempotency_key=idempotency_key)
    return _to_call_tool_response(r)

# Before (_dispatch_rag_tool):
async def _dispatch_rag_tool(name: str, args: ToolArgs) -> DispatchResult:
    """Route RAG pipeline tool calls through the service's dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)

# After (_dispatch_rag_tool):
async def _dispatch_rag_tool(name: str, args: ToolArgs, idempotency_key: str | None = None) -> DispatchResult:
    """Route RAG pipeline tool calls through the service's dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args, idempotency_key=idempotency_key)
```

## Compatibility considerations

- Backward compatible: `_dispatch_rag_tool` gains an optional trailing parameter with default `None`. Existing callers within the same file (e.g., `MCPServer.dispatch()`) already pass positional arguments `(name, args)` — adding an optional trailing parameter does not break them.
- `dispatch_tool()` already has `idempotency_key: str | None = None` as an optional parameter.
- When `idempotency_key` is `None`, `dispatch.py:116` skips duplicate detection entirely — no behavioral change for current callers.

## Security considerations

- No new secrets or credentials are introduced.
- The `Request` object is injected by FastAPI's dependency injection system — no manual parsing required.

## Rollback considerations

- Revert the four code blocks above to their original state.
- If `extract_request_context` import causes circular import issues, remove the import and restore the original `call_tool` signature.

## Validation plan

- Code review: confirm `call_tool` has `request: Request` parameter and calls `extract_request_context(request)`.
- Code review: confirm `_dispatch_rag_tool` signature includes `idempotency_key: str | None = None` and forwards it.
- Regression test: `uv run pytest tests/mcp_servers/test_rag_pipeline_server.py -q` passes.
- Type check: `uv run mypy scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` is clean.

## Completion criteria

- [ ] `call_tool` function signature includes `request: Request` parameter.
- [ ] `extract_request_context` is imported from `mcp_servers.server`.
- [ ] `call_tool` body calls `extract_request_context(request)` and captures `idempotency_key`.
- [ ] `_dispatch_rag_tool` call site passes `idempotency_key=idempotency_key`.
- [ ] `_dispatch_rag_tool` signature accepts `idempotency_key: str | None = None`.
- [ ] `_dispatch_rag_tool` forwards `idempotency_key` to `dispatch_tool()`.
- [ ] All validation checks pass (tests, type check).

## Out of scope

- Modifying `dispatch.py`'s duplicate-detection logic itself.
- Adding the `x-idempotency-key` header to outgoing HTTP requests.
- Idempotency support for non-side-effecting tool calls beyond what `dispatch.py` already handles via `_is_side_effecting()`.
- Changing audit logging semantics or FastAPI route registration/response model contracts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260918-213709 | 20260918-213709 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260918-213709 | 20260918-213709 |  |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260918-213710 | 20260918-213710 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260918-213710 | 20260918-213710 |  |

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
- **Requirement ID**: REQ-002; AC-2
- **Source issue**: N/A: not found at expected path
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260918-075225_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-163828
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py