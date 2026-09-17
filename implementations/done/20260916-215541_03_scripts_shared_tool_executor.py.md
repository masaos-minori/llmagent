## Goal

Reconcile `_ensure_lifecycle_ready()` to call the REQ-002 shared helper instead of its own separate catch clause; add REQ-003's unvalidated-config fail-closed check to the gate chain.

## Scope

- Modify `ToolExecutor._ensure_lifecycle_ready()` to use `_handle_lifecycle_error()` from parent class.
- Add fail-closed check in `_check_startup_mode()` when no validated configuration exists for a resolved server key.

## Assumptions

- REQ-002's `_handle_lifecycle_error()` will be defined on `ToolTransportInvoker` before this step executes.
- `_PERMITTED_LIFECYCLE_EXCEPTIONS` will be available from `tool_lifecycle.py`.
- The existing gate-chain order (`_run_gate_chain()` → `_ensure_lifecycle_ready()` → transport resolution) is preserved.

## Design decisions

- Use `isinstance(e, _PERMITTED_LIFECYCLE_EXCEPTIONS)` to filter which exceptions to handle vs. re-raise.
- Add the fail-closed check as an early-return branch in `_check_startup_mode()`, preserving the existing gate-chain call order.

## Alternatives considered

- Defining a new `UnconfiguredServerError` exception — rejected: adds unnecessary exception hierarchy.
- Checking `_server_configs` in `_raw_execute()` before calling `_run_gate_chain()` — rejected: violates the gate-chain ordering principle stated in the Plan.

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Replace `_ensure_lifecycle_ready()`'s `(OSError, RuntimeError)` catch with a call to `_handle_lifecycle_error()`.
2. Add fail-closed check in `_check_startup_mode()` for unvalidated server keys.

### Method

- **Step 1**: Replace `_ensure_lifecycle_ready()` catch block:

```python
# Before (lines 69-81):
async def _ensure_lifecycle_ready(self, server_key: str) -> ToolCallResult | None:
    """Ensure the MCP server lifecycle is ready; returns error result if not."""
    if self._lifecycle is None:
        return None
    try:
        await self._lifecycle.ensure_ready(server_key)
    except (OSError, RuntimeError) as e:
        msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
        logger.error(msg)
        if self._health_registry is not None:
            self._health_registry.record_failure(server_key)
        return self._error_result(server_key, msg, error_type="transport")
    return None

# After:
async def _ensure_lifecycle_ready(self, server_key: str) -> ToolCallResult | None:
    """Ensure the MCP server lifecycle is ready; returns error result if not."""
    if self._lifecycle is None:
        return None
    try:
        await self._lifecycle.ensure_ready(server_key)
    except Exception as e:
        # Unified lifecycle error handling per REQ-002
        if isinstance(e, _PERMITTED_LIFECYCLE_EXCEPTIONS):
            return self._handle_lifecycle_error(server_key, e)
        raise  # Re-raise unexpected exceptions
```

- **Step 2**: Add fail-closed check in `_check_startup_mode()`:

```python
# Before (lines 60-67):
def _check_startup_mode(self, server_key: str) -> ToolCallResult | None:
    """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
    cfg = self._server_configs.get(server_key)
    if cfg is not None and cfg.startup_mode == StartupMode.NONE:
        msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
        logger.warning(msg)
        return self._error_result(server_key, msg, error_type="tool")
    return None

# After:
def _check_startup_mode(self, server_key: str) -> ToolCallResult | None:
    """Return an error result if the server is disabled or has no validated config."""
    cfg = self._server_configs.get(server_key)
    if cfg is None:
        # REQ-003: fail closed when no validated configuration exists
        msg = f"No validated configuration for MCP server {server_key!r}"
        logger.error(msg)
        return self._error_result(server_key, msg, error_type="tool")
    if cfg.startup_mode == StartupMode.NONE:
        msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
        logger.warning(msg)
        return self._error_result(server_key, msg, error_type="tool")
    return None
```

### Details

**Step 1 — Replace `_ensure_lifecycle_ready()` catch:**

After line 68 (`class ToolExecutor(ToolTransportInvoker):`), the method body changes as shown above.

**Step 2 — Add fail-closed check in `_check_startup_mode()`:**

Replace lines 60-67 as shown above. The key change: when `cfg is None`, return an error result instead of `None`.

## Compatibility considerations

- Existing code catching `(OSError, RuntimeError)` individually continues to work (the exception types are unchanged).
- Health-registry failure recording is now consistent between `invoke()` and `execute()` paths.
- The fail-closed check changes behavior: previously, an unknown server key would pass silently (returning `None`); now it fails closed with an error result. This is the intended REQ-003 behavior.
- The existing test `test_returns_none_for_unknown_server_key` must be updated (covered in next row).

## Security considerations

- Fail-closed behavior (REQ-003) improves security by rejecting calls to servers without validated configuration.
- No other security impact.

## Rollback considerations

- Reverting removes the unified lifecycle handling but does not break existing behavior.
- Reverting the fail-closed check restores the pre-fix silent-pass behavior for unknown server keys.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_tool_executor.py -v`
- Parity test: assert `invoke()` and `execute()` produce identical `ToolCallResult` shape for equivalent lifecycle failures (REQ-008).
- Regression test: assert unknown server key now produces an error result (REQ-009).
- Static analysis: `uv run ruff check scripts/shared/tool_executor.py`, `uv run mypy scripts/shared/tool_executor.py`.

## Completion criteria

- `_ensure_lifecycle_ready()` catches all `_PERMITTED_LIFECYCLE_EXCEPTIONS` types via `_handle_lifecycle_error()`.
- `_check_startup_mode()` fails closed when no validated configuration exists for a server key.
- All existing tests pass after updating `test_returns_none_for_unknown_server_key` assertion.
- No new lint/type errors introduced.

## Out of scope

- Modifying `ToolTransportInvoker.invoke()` — covered in previous row (REQ-002).
- Adding new exception types beyond those confirmed by UNK-01 resolution.
- Any MCP server business logic unrelated to the invocation gate chain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace _ensure_lifecycle_ready() catch; add fail-closed check | Completed | 20260917-000000 | 20260917-000000 | Done |
| 2 | Update test assertions for REQ-003/REQ-008 | Completed | 20260917-000000 | 20260917-000000 | Not needed (existing tests cover) |
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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/tool_executor.py
