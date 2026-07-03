## Goal

Add a `TestPluginReturnValidation` test class to `tests/test_tool_executor.py` covering all six acceptance criteria for strict two-element tuple validation in `ToolExecutor.execute()`.

## Scope

- In-Scope:
  - Append `TestPluginReturnValidation` class with 6 async test methods to `tests/test_tool_executor.py`
  - Import `plugin_registry` inside the test class (or at module level if not already imported)
- Out-of-Scope:
  - Modifying existing test classes (`TestCacheStampede`, `TestHttpTransportRetry`)
  - Adding fixtures to `conftest.py`
  - Testing `@register_tool` registration-time validation (covered by `test_plugin_registry.py`)

## Assumptions

1. `plugin_registry._tools` is a `dict[str, tuple[Callable[..., Any], str]]` (handler, module_name); tests can inject a bad-return function by writing directly to `_tools["test_tool"] = (fn, "test")`.
2. `plugin_registry._reset_for_testing()` is the correct teardown; each test should call it via a `pytest.fixture` with `autouse` or explicit setup/teardown within the class.
3. `ToolExecutor` can be instantiated minimally for plugin-path tests (the plugin branch in `execute()` does not use `_cache` or `_inflight`); the existing pattern of `ToolExecutor.__new__(ToolExecutor)` with minimal attribute assignment is acceptable, but since `execute()` calls `plugin_registry.get_tool()` directly, a full constructor call may be simpler — check constructor signature.
4. The `TypeError` raised for wrong `output` type and wrong `is_error` type comes from the existing code on lines 577-583 (already present, not gated on the length check).
5. `pytest-asyncio` is already configured (existing tests use `@pytest.mark.asyncio`).

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_tool_executor.py`

### Procedure

1. Read the end of `tests/test_tool_executor.py` to find the correct insertion point (after the last test class).
2. Add import for `plugin_registry` from `shared` at the top of the file (after existing imports), e.g.:
   ```python
   from shared import plugin_registry
   ```
3. Append the `TestPluginReturnValidation` class. Each test method must:
   a. Register a dummy tool by directly writing to `plugin_registry._tools`:
      ```python
      plugin_registry._tools["test_tool"] = (bad_fn, "test")
      ```
   b. Build a minimal `ToolExecutor` — check if a no-arg or minimal constructor exists; if not, use `__new__` with `_cache`, `_inflight`, `_cache_ttl`, `_cache_max_size`, `stat_cache_hits` attributes set (same pattern as `TestCacheStampede`).
   c. Call `await executor.execute("test_tool", {})` and assert the expected exception.
   d. Clean up with `plugin_registry._reset_for_testing()` in teardown.
4. Use a `@pytest.fixture(autouse=True)` at class level or a `setup_method`/`teardown_method` pair to call `plugin_registry._reset_for_testing()` before and after each test.

### Method

Test helper pattern (reuse from existing tests):
```python
executor = ToolExecutor.__new__(ToolExecutor)
executor._cache = {}
executor._cache_ttl = 60.0
executor._cache_max_size = 100
executor._inflight = {}
executor.stat_cache_hits = 0
```

Plugin injection pattern:
```python
async def _bad_fn(args: dict) -> Any:
    return <bad_value>
Plugin_registry._tools["test_tool"] = (_bad_fn, "test")
```

Six test methods:
```python
@pytest.mark.asyncio
async def test_non_tuple_return_raises(self) -> None:
    """Plugin returns str → ValueError."""
    async def _fn(args: dict) -> Any:
        return "not_a_tuple"
    plugin_registry._tools["test_tool"] = (_fn, "test")
    with pytest.raises(ValueError, match="must return exactly"):
        await self._make_executor().execute("test_tool", {})

@pytest.mark.asyncio
async def test_one_element_tuple_raises(self) -> None:
    """Plugin returns ('ok',) → ValueError."""
    async def _fn(args: dict) -> Any:
        return ("ok",)
    plugin_registry._tools["test_tool"] = (_fn, "test")
    with pytest.raises(ValueError, match="must return exactly"):
        await self._make_executor().execute("test_tool", {})

@pytest.mark.asyncio
async def test_valid_two_element_tuple(self) -> None:
    """Plugin returns ('ok', False) → ToolCallResult with output='ok', is_error=False."""
    async def _fn(args: dict) -> Any:
        return ("ok", False)
    plugin_registry._tools["test_tool"] = (_fn, "test")
    result = await self._make_executor().execute("test_tool", {})
    assert result.output == "ok"
    assert result.is_error is False

@pytest.mark.asyncio
async def test_three_element_tuple_raises(self) -> None:
    """Plugin returns ('ok', False, 'extra') → ValueError (new strict behavior)."""
    async def _fn(args: dict) -> Any:
        return ("ok", False, "extra")
    plugin_registry._tools["test_tool"] = (_fn, "test")
    with pytest.raises(ValueError, match="must return exactly"):
        await self._make_executor().execute("test_tool", {})

@pytest.mark.asyncio
async def test_wrong_output_type_raises(self) -> None:
    """Plugin returns (123, False) → TypeError."""
    async def _fn(args: dict) -> Any:
        return (123, False)
    plugin_registry._tools["test_tool"] = (_fn, "test")
    with pytest.raises(TypeError, match="output must be str"):
        await self._make_executor().execute("test_tool", {})

@pytest.mark.asyncio
async def test_wrong_is_error_type_raises(self) -> None:
    """Plugin returns ('ok', 'no') → TypeError."""
    async def _fn(args: dict) -> Any:
        return ("ok", "no")
    plugin_registry._tools["test_tool"] = (_fn, "test")
    with pytest.raises(TypeError, match="is_error must be bool"):
        await self._make_executor().execute("test_tool", {})
```

### Details

- Use a private `_make_executor(self) -> ToolExecutor` helper method in the class to avoid repeating the `__new__` setup.
- The `_tools` dict stores `(fn, module_name)` tuples; use `"test"` as the module name string.
- `match=` argument in `pytest.raises` uses regex; `"must return exactly"` matches the updated error message from Step 1.
- `match="output must be str"` and `match="is_error must be bool"` match the existing error messages on lines 579 and 582 of `tool_executor.py`.
- Do NOT use `@register_tool` decorator to inject bad return values — it validates the annotation at registration time and would reject functions that don't annotate `-> tuple[str, bool]`.

## Validation plan

1. Run the new test class:
   ```
   uv run pytest tests/test_tool_executor.py::TestPluginReturnValidation -v
   ```
   Expected: all 6 tests green.
2. Run the full test_tool_executor suite:
   ```
   uv run pytest tests/test_tool_executor.py -v
   ```
   Expected: no regressions in `TestCacheStampede` or `TestHttpTransportRetry`.
3. Run the plugin registry test suite:
   ```
   uv run pytest tests/test_plugin_registry.py -v
   ```
   Expected: all pass.
4. Full suite:
   ```
   uv run pytest
   ```
   Expected: all green.
