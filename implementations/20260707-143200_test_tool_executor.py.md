# Implementation: H-5 — tests for ensure_ready error handling (test_tool_executor.py)

## Goal

Add tests verifying that `ToolExecutor._raw_execute()` converts `ensure_ready()`
failures into `ToolCallResult(is_error=True, error_type="transport")` and calls
`health_registry.record_failure()`, without invoking the transport `execute()` method.

## Scope

**Target**: `tests/test_tool_executor.py` (or the equivalent test file for ToolExecutor)

**Step covered**: Plan H-5 step 2.

**Out of scope**: source changes, other test files.

## Assumptions

1. An existing test file covers `ToolExecutor`; new tests are added there.
2. `ToolExecutor` can be constructed with stub transports and a mock lifecycle.
3. `AsyncMock` is used for `ensure_ready()` to raise exceptions asynchronously.

## Implementation

### Target file

`tests/test_tool_executor.py`

### Procedure

#### Setup helper

```python
def make_executor_with_mock_lifecycle(ensure_ready_side_effect=None):
    """Return a ToolExecutor with a mock lifecycle that raises on ensure_ready."""
    http_mock = AsyncMock()
    executor = ToolExecutor(
        http_mock,
        cache_ttl=0,
        server_configs={},
        cache_max_size=0,
        concurrency_limits={},
    )
    mock_lifecycle = AsyncMock()
    if ensure_ready_side_effect is not None:
        mock_lifecycle.ensure_ready.side_effect = ensure_ready_side_effect
    executor.set_lifecycle(mock_lifecycle)

    mock_registry = MagicMock()
    executor.set_health_registry(mock_registry)

    # Register a fake tool pointing to a mock transport
    mock_transport = AsyncMock()
    executor._transports["test_server"] = mock_transport
    executor._resolver._tool_to_server["test_tool"] = "test_server"

    return executor, mock_lifecycle, mock_registry, mock_transport
```

#### Test 1: RuntimeError from ensure_ready → is_error=True, error_type="transport"

```python
@pytest.mark.asyncio
async def test_raw_execute_lifecycle_runtime_error_returns_transport_error():
    executor, _, _, mock_transport = make_executor_with_mock_lifecycle(
        ensure_ready_side_effect=RuntimeError("startup failed")
    )

    result = await executor._raw_execute("test_tool", {})

    assert result.is_error is True
    assert result.error_type == "transport"
    assert "ensure_ready failed" in result.output
    mock_transport.execute.assert_not_called()
```

#### Test 2: OSError from ensure_ready → is_error=True, error_type="transport"

```python
@pytest.mark.asyncio
async def test_raw_execute_lifecycle_os_error_returns_transport_error():
    executor, _, _, mock_transport = make_executor_with_mock_lifecycle(
        ensure_ready_side_effect=OSError("command not found")
    )

    result = await executor._raw_execute("test_tool", {})

    assert result.is_error is True
    assert result.error_type == "transport"
    mock_transport.execute.assert_not_called()
```

#### Test 3: record_failure() called on ensure_ready failure

```python
@pytest.mark.asyncio
async def test_raw_execute_lifecycle_error_calls_record_failure():
    executor, _, mock_registry, _ = make_executor_with_mock_lifecycle(
        ensure_ready_side_effect=RuntimeError("startup failed")
    )

    await executor._raw_execute("test_tool", {})

    mock_registry.record_failure.assert_called_once_with("test_server")
```

#### Test 4: transport execute() NOT called after lifecycle failure

```python
@pytest.mark.asyncio
async def test_raw_execute_transport_not_called_after_lifecycle_error():
    executor, _, _, mock_transport = make_executor_with_mock_lifecycle(
        ensure_ready_side_effect=RuntimeError("startup failed")
    )

    await executor._raw_execute("test_tool", {})

    mock_transport.execute.assert_not_awaited()
```

#### Test 5: Successful ensure_ready → transport execute() IS called

```python
@pytest.mark.asyncio
async def test_raw_execute_successful_lifecycle_calls_transport():
    executor, _, _, mock_transport = make_executor_with_mock_lifecycle(
        ensure_ready_side_effect=None  # no error
    )
    mock_transport.execute.return_value = ToolCallResult(
        output="ok", is_error=False, request_id="", server_key="test_server"
    )

    result = await executor._raw_execute("test_tool", {})

    assert result.is_error is False
    mock_transport.execute.assert_awaited_once()
```

### Method

- All tests use `_raw_execute()` directly to bypass caching and stampede protection.
- `make_executor_with_mock_lifecycle` wires a fake tool `"test_tool"` → `"test_server"`
  so the resolver returns a known server key.
- `AsyncMock.side_effect` raises the given exception when awaited.

### Details

- The test helper must mock `executor._resolver._tool_to_server` directly, or use
  whatever internal structure `ToolExecutor` uses for tool-to-server mapping. Read
  `tool_executor.py` to confirm the field name before writing.
- `set_health_registry()` and `set_lifecycle()` are confirmed to exist at lines 128 and
  131 of `tool_executor.py`.
- If `record_failure` is not the correct method name, read `shared/mcp_health.py` and
  adjust.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests (targeted) | `uv run pytest tests/ -k "tool_executor" -v` | all pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
