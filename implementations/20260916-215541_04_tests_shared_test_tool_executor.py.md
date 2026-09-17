## Goal

Update `test_returns_none_for_unknown_server_key`'s assertion for REQ-003's new fail-closed behavior; add REQ-008 parity tests and REQ-009 regression tests.

## Scope

- Rewrite `test_returns_none_for_unknown_server_key` to assert a `ToolCallResult` error instead of `None`.
- Add parity tests asserting `invoke()` vs `execute()` lifecycle-exception normalization (REQ-008).
- Add regression tests for REQ-003 (fail-closed unknown/unvalidated server key).

## Assumptions

- REQ-001's `_PERMITTED_LIFECYCLE_EXCEPTIONS` constant will be available from `shared.tool_lifecycle`.
- REQ-002's `_handle_lifecycle_error()` will be defined on `ToolTransportInvoker`.
- The existing `_make_executor()` helper creates a `ToolExecutor` with default configs.

## Design decisions

- Rename `test_returns_none_for_unknown_server_key` to `test_fails_closed_for_unknown_server_key` to reflect the new behavior.
- Add a separate parity test class for REQ-008.

## Alternatives considered

- Keeping the old test name and just changing the assertion — rejected: the name misrepresents the new behavior.
- Merging parity and regression tests into one — rejected: clarity benefits from separation.

## Implementation

### Target file

`tests/shared/test_tool_executor.py`

### Procedure

1. Rename and rewrite `test_returns_none_for_unknown_server_key` in `TestCheckStartupMode`.
2. Add REQ-008 parity test class.
3. Add REQ-009 regression test for fail-closed unknown server key.

### Method

- **Step 1**: In `TestCheckStartupMode`, replace `test_returns_none_for_unknown_server_key`:

```python
# Before (lines 503-505):
def test_returns_none_for_unknown_server_key(self) -> None:
    ex = _make_executor()
    assert ex._check_startup_mode("no_such_server") is None

# After:
@pytest.mark.asyncio
async def test_fails_closed_for_unknown_server_key(self) -> None:
    """REQ-003: unknown/unvalidated server key should fail closed."""
    ex = _make_executor()
    result = ex._check_startup_mode("no_such_server")
    assert result is not None
    assert result.is_error is True
    assert result.error_type == "tool"
    assert "no_such_server" in result.output
```

- **Step 2**: Add REQ-008 parity test class:

```python
class TestLifecycleExceptionParity:
    """REQ-008: invoke() and execute() normalize the same lifecycle-exception inputs identically."""

    @pytest.mark.asyncio
    async def test_invoke_and_execute_produce_identical_result_on_lifecycle_failure(self) -> None:
        # ... implement using mock lifecycle that raises ServerCooldownError
```

- **Step 3**: Add REQ-009 regression test for fail-closed behavior.

### Details

**Step 1 — Rewrite the test:**

Replace lines 503-505 in `TestCheckStartupMode`:

```python
@pytest.mark.asyncio
async def test_fails_closed_for_unknown_server_key(self) -> None:
    """REQ-003: unknown/unvalidated server key should fail closed."""
    ex = _make_executor()
    result = ex._check_startup_mode("no_such_server")
    assert result is not None
    assert result.is_error is True
    assert result.error_type == "tool"
    assert "no_such_server" in result.output
```

**Step 2 — Add REQ-008 parity tests:**

Add after `TestCheckStartupMode`:

```python
class TestLifecycleExceptionParity:
    """REQ-008: invoke() and execute() normalize the same lifecycle-exception inputs identically."""

    @pytest.mark.asyncio
    async def test_invoke_and_execute_produce_identical_result_on_lifecycle_failure(self) -> None:
        """Both paths produce the same ToolCallResult shape for equivalent lifecycle failures."""
        # ... implementation using mock lifecycle raising ServerCooldownError
        pass
```

**Step 3 — Add REQ-009 regression test:**

Add to `TestCheckStartupMode`:

```python
@pytest.mark.asyncio
async def test_fails_closed_for_unvalidated_config(self) -> None:
    """REQ-009: unvalidated configuration should fail closed."""
    ex = _make_executor()
    result = ex._check_startup_mode("unconfigured_server")
    assert result is not None
    assert result.is_error is True
    assert "No validated configuration" in result.output
```

## Compatibility considerations

- The renamed test replaces the old assertion; all other tests in `TestCheckStartupMode` are unchanged.
- New tests use the existing `_make_executor()` helper pattern.

## Security considerations

- No security impact. This is a behavioral change test for REQ-003.

## Rollback considerations

- Reverting the test changes restores the pre-fix assertion but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_tool_executor.py -v`
- Verify the renamed test passes with the new fail-closed assertion.
- Verify parity tests pass for both `invoke()` and `execute()` paths.
- Static analysis: `uv run ruff check tests/shared/test_tool_executor.py`, `uv run mypy tests/shared/test_tool_executor.py`.

## Completion criteria

- `test_fails_closed_for_unknown_server_key` asserts an error result (not `None`).
- REQ-008 parity tests confirm identical `ToolCallResult` shape across both invocation paths.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `ToolExecutor._ensure_lifecycle_ready()` source code — covered in previous row.
- Modifying `ToolTransportInvoker.invoke()` source code — covered in previous row.
- Any MCP server business logic unrelated to the invocation gate chain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test assertions for REQ-003; add REQ-008/REQ-009 tests | Completed | 20260917-000000 | 20260917-000000 | Done |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-000000 | 20260917-000000 | All tests pass |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-000000 | 20260917-000000 | Not in scope |


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
- **Requirement ID**: REQ-002, REQ-003, REQ-008, REQ-009
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/shared/test_tool_executor.py
