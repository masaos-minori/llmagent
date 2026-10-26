# _validate_pre_snapshot uses blocking os.path calls in async context

## Priority
Low

## Summary
The `_validate_pre_snapshot` function in `git_server.py` uses synchronous `os.path.exists()` and `os.path.access()` calls inside an async HTTP handler, which blocks the event loop during validation.

## Background
The `_validate_pre_snapshot` function at lines 111-132 of `git_server.py`:

```python
def _validate_pre_snapshot(path: str) -> tuple[bool, str]:
    """Validate that *path* is accessible and contains a Git repository before calling snapshot."""
    try:
        import os as _os
        if not _os.path.exists(path):
            return False, "[DENIED] repository path does not exist"
        if not _os.access(path, _os.R_OK):
            return False, "[DENIED] repository path is not readable"
        has_git = _os.path.isdir(_os.path.join(path, ".git"))
        if not has_git:
            has_bare = _os.path.isfile(_os.path.join(path, "HEAD"))
            if not has_bare:
                return False, "[DENIONED] path is not a Git repository"
        return True, ""
    except PermissionError:
        return False, "[DENIED] permission denied accessing repository"
```

This function is called from the `call_tool` endpoint at line 285:

```python
ok, err = _validate_pre_snapshot(resolved)
```

The `call_tool` endpoint is an async FastAPI handler (line 236):

```python
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
```

## Problem
The `os.path.exists()`, `os.path.access()`, `os.path.isdir()`, and `os.path.isfile()` calls are synchronous file system operations. In an async event loop (uvicorn), these calls block the entire event loop while executing, preventing other requests from being processed.

While the impact is typically small (filesystem operations are fast), under high load or on slow filesystems (e.g., NFS mounts), this can cause:
1. Event loop stalls — other requests wait for the blocking call to complete.
2. Increased latency for concurrent requests.
3. Potential timeout issues if the filesystem is unresponsive.

## Reason for Change
Blocking I/O in an async handler degrades the server's responsiveness under load. Using async-compatible file system operations would prevent event loop stalls.

## Implementation Intent
1. Replace synchronous `os.path` calls with `aiofiles` or `anyio` equivalents, or
2. Run the blocking calls in a thread pool executor using `asyncio.to_thread()`, or
3. Accept the current behavior and document it as a known limitation.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` — `_validate_pre_snapshot` (lines 111-132)

## Required Changes
- Replace synchronous `os.path` calls with async-compatible alternatives
- Or wrap the calls in `asyncio.to_thread()` to avoid blocking the event loop
- Document the change in the function's docstring

## Constraints
- Must not change the validation semantics (same checks, same results)
- Must preserve the existing error messages

## Acceptance Criteria
- File system validation does not block the event loop
- Validation results are identical to the synchronous version
- No performance regression under low load

## Testing Expectations
- Unit test: verify validation works correctly with async executor
- Integration test: verify no event loop stall under concurrent load
- Regression test: ensure existing validation behavior is preserved

## Documentation Impact
Update `_validate_pre_snapshot` docstring to document the async execution model.

## Out of Scope
- Changes to the validation logic itself
- Changes to how paths are resolved before validation

## Dependencies
N/A: none

## Unresolved Questions
- Is `aiofiles` available in the project's dependencies?
- Are there other MCP servers with the same pattern?

## AI Implementation Instruction
In `scripts/mcp_servers/git/git_server.py`, replace synchronous `os.path` calls in `_validate_pre_snapshot` with async-compatible alternatives. Do not modify any other MCP server's validation logic.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/git/git_server.py
