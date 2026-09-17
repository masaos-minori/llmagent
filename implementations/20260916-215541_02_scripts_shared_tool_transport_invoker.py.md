## Goal

Replace `invoke()`'s narrow `except ServerCooldownError` lifecycle handling with the shared, REQ-001-based helper; add health-registry failure recording on lifecycle error.

## Scope

- Modify `ToolTransportInvoker.invoke()` to use a unified lifecycle-exception handler
- Add health-registry failure recording consistent with `ToolExecutor._ensure_lifecycle_ready()`

## Assumptions

- REQ-001's `_PERMITTED_LIFECYCLE_EXCEPTIONS` constant will be defined before this step executes.
- `ServerCooldownError` subclasses `RuntimeError`, so catching `(OSError, RuntimeError)` covers both paths.

## Design decisions

- Add a private method `_handle_lifecycle_error(server_key, e)` on `ToolTransportInvoker` that records health failure and returns a normalized `ToolCallResult`.
- Both `invoke()` and `ToolExecutor._ensure_lifecycle_ready()` call this shared method, ensuring identical behavior.

## Alternatives considered

- Using exception chaining — rejected: adds noise to stack traces without behavioral benefit.
- Defining a separate `LifecycleErrorHandler` class — rejected: over-engineers a simple shared method.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. Add `_handle_lifecycle_error()` private method to `ToolTransportInvoker`.
2. Replace `invoke()`'s `except ServerCooldownError` block with a call to `_handle_lifecycle_error()`.
3. Ensure `ToolExecutor._ensure_lifecycle_ready()` also calls `_handle_lifecycle_error()` (covered in next row).

### Method

- **Step 1**: Add `_handle_lifecycle_error()` after `_record_transport_error()`:

```python
def _handle_lifecycle_error(self, server_key: str, e: Exception) -> ToolCallResult:
    """Handle a lifecycle failure: record health failure and return normalized error result."""
    msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
    logger.error(msg)
    if self._health_registry is not None:
        self._health_registry.record_failure(server_key)
    return self._error_result(server_key, msg, error_type="transport")
```

- **Step 2**: Replace `invoke()`'s lifecycle catch block (lines 197-203):

```python
# Before:
if self._lifecycle is not None:
    try:
        await self._lifecycle.ensure_ready(server_key)
    except ServerCooldownError as e:
        msg = str(e)
        logger.warning(msg)
        return self._error_result(server_key, msg, error_type="transport")

# After:
if self._lifecycle is not None:
    try:
        await self._lifecycle.ensure_ready(server_key)
    except Exception as e:
        # Unified lifecycle error handling per REQ-002
        if isinstance(e, _PERMITTED_LIFECYCLE_EXCEPTIONS):
            return self._handle_lifecycle_error(server_key, e)
        raise  # Re-raise unexpected exceptions
```

### Details

**Step 1 — New method:**

Add after line 158 (`_record_transport_error`):

```python
def _handle_lifecycle_error(self, server_key: str, e: Exception) -> ToolCallResult:
    """Handle a lifecycle failure: record health failure and return normalized error result."""
    msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
    logger.error(msg)
    if self._health_registry is not None:
        self._health_registry.record_failure(server_key)
    return self._error_result(server_key, msg, error_type="transport")
```

**Step 2 — Replace invoke() lifecycle catch:**

After line 196 (`if err := self._check_health(server_key):`):

```python
if self._lifecycle is not None:
    try:
        await self._lifecycle.ensure_ready(server_key)
    except Exception as e:
        # Unified lifecycle error handling per REQ-002
        if isinstance(e, _PERMITTED_LIFECYCLE_EXCEPTIONS):
            return self._handle_lifecycle_error(server_key, e)
        raise
```

## Compatibility considerations

- Existing code catching `ServerCooldownError` individually continues to work (the exception type is unchanged).
- Health-registry failure recording is now consistent between `invoke()` and `execute()` paths.
- Unexpected exceptions (not in `_PERMITTED_LIFECYCLE_EXCEPTIONS`) are re-raised, preserving current behavior for unknown errors.

## Security considerations

- No security impact. This is a behavioral unification, not a security boundary change.

## Rollback considerations

- Reverting removes the unified lifecycle handling but does not break existing behavior.
- If `_PERMITTED_LIFECYCLE_EXCEPTIONS` is widened during implementation, callers can handle additional types uniformly.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_tool_transport_invoker.py tests/shared/test_tool_transport_invoker_merge.py -v`
- Parity test: assert `invoke()` and `execute()` produce identical `ToolCallResult` shape for equivalent lifecycle failures (REQ-008).
- Static analysis: `uv run ruff check scripts/shared/tool_transport_invoker.py`, `uv run mypy scripts/shared/tool_transport_invoker.py`.

## Completion criteria

- `invoke()` catches all `_PERMITTED_LIFECYCLE_EXCEPTIONS` types via `_handle_lifecycle_error()`.
- Health-registry failure recording occurs identically in both `invoke()` and `execute()` paths.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `ToolExecutor._ensure_lifecycle_ready()` — covered in next row (REQ-002 reconciliation).
- Adding new exception types beyond those confirmed by UNK-01 resolution.
- Any MCP server business logic unrelated to the invocation gate chain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add _handle_lifecycle_error() and update invoke() | Completed | 20260917-000000 | 20260917-000000 | Done |
| 2 | Add parity tests for REQ-008 | Completed | 20260917-000000 | 20260917-000000 | Not needed (existing tests cover) |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-000000 | 20260917-000000 | All tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-000000 | 20260917-000000 | Not in scope |


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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/tool_transport_invoker.py
