# contextvars.ContextVar cross-request leakage risk in MDQ dispatch

## Priority
Medium

## Summary
The MDQ server uses `contextvars.ContextVar` for per-call metadata storage, but the `set()`/`reset()` pattern in `_dispatch_mdq_tool` does not guarantee isolation between concurrent async requests in the same event loop iteration.

## Background
The MDQ server defines `_mdq_metadata_var` at line 188 of `mdq_server.py`:

```python
_mdq_metadata_var: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "mdq_metadata", default={}
)
```

The `_dispatch_mdq_tool` function (lines 297-311) uses the ContextVar pattern:

```python
async def _dispatch_mdq_tool(name, args, idempotency_key=None):
    token = _mdq_metadata_var.set({})
    try:
        result = await dispatch_tool(...)
        metadata = _mdq_metadata_var.get()
    finally:
        _mdq_metadata_var.reset(token)
    return MdqDispatchResult(output=result.output, is_error=result.is_error, metadata=metadata)
```

This pattern is correct for the common case where each request is handled in its own async context. However, there is a subtle race condition: if two concurrent requests arrive in the same event loop tick and both call `_dispatch_mdq_tool`, the `set()` calls can interleave before the `try` block executes, causing one request's metadata to leak into another.

## Problem
The ContextVar pattern relies on the assumption that `set()` and `reset()` are atomic within a single async context. In FastAPI/uvicorn, each HTTP request gets its own async context, so this is generally safe. However, there are edge cases:

1. **Concurrent requests in the same task group**: If a caller invokes multiple tool calls concurrently (e.g., via a batch endpoint), the ContextVar values can cross-contaminate.
2. **Exception during `set()`**: If `_mdq_metadata_var.set({})` raises before the `try` block, the `finally` clause will attempt to `reset()` a token that was never successfully set, potentially corrupting the ContextVar state.
3. **Default mutable dict**: The `default={}` at line 189 creates a shared mutable default. While `ContextVar` copies the default on access, the initial `default={}` is evaluated once at module load time and could theoretically cause issues if the ContextVar implementation changes.

## Reason for Change
While the current pattern works correctly under normal FastAPI request handling, the lack of explicit documentation about the ContextVar's lifecycle and the mutable default value create a maintenance hazard. Future changes to the dispatch path could introduce cross-request leakage.

## Implementation Intent
1. Replace the mutable default `{}` with `None` and use `or {}` in the `get()` call to avoid shared mutable defaults.
2. Add a guard in `_dispatch_mdq_tool` to handle the case where `set()` fails before the `try` block.
3. Document the ContextVar's expected lifecycle in a comment.

## Target Files or Areas
- `scripts/mcp_servers/mdq/mdq_server.py` — `_mdq_metadata_var` (line 188), `_dispatch_mdq_tool` (lines 297-311)

## Required Changes
- Replace `default={}` with `default=None` in `_mdq_metadata_var` definition
- Update `_dispatch_mdq_tool` to handle `None` default: `metadata = _mdq_metadata_var.get() or {}`
- Add a guard in `_dispatch_mdq_tool` to catch exceptions from `set()` before the `try` block
- Add a docstring comment explaining the ContextVar lifecycle

## Constraints
- Must not change the existing metadata propagation semantics
- Must preserve backward compatibility with existing callers

## Acceptance Criteria
- `_mdq_metadata_var` default is `None` instead of a mutable dict
- Metadata is correctly propagated even when `get()` returns `None`
- No cross-request metadata leakage under concurrent load

## Testing Expectations
- Unit test: verify ContextVar isolation under concurrent async requests
- Unit test: verify `get()` returns `{}` when default is `None` and no value is set
- Concurrency test: verify no metadata leakage under high concurrency

## Documentation Impact
Add a comment to `_mdq_metadata_var` explaining its lifecycle and the ContextVar pattern used.

## Out of Scope
- Changes to the ContextVar library itself
- Changes to how metadata is consumed by downstream tools

## Dependencies
N/A: none

## Unresolved Questions
- Does FastAPI guarantee per-request async contexts for all request handlers?
- Are there any batch endpoints that invoke multiple tool calls concurrently?

## AI Implementation Instruction
In `scripts/mcp_servers/mdq/mdq_server.py`, replace `default={}` with `default=None` in `_mdq_metadata_var`, update `_dispatch_mdq_tool` to handle `None` default, and add a guard for `set()` failures. Do not modify any other MCP server's ContextVar usage.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py
