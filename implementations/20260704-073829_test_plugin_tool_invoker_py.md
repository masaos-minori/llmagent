# Implementation: Create `tests/shared/test_plugin_tool_invoker.py`

## Goal

Create a new test file `tests/shared/test_plugin_tool_invoker.py` with 6 async tests for
`PluginToolInvoker.try_execute()`, covering the no-plugin, success, exception, and validation
failure paths.

## Scope

- In-Scope: New file `tests/shared/test_plugin_tool_invoker.py` with `TestPluginToolInvoker` class
  (6 test methods).
- Out-of-Scope: No changes to `tests/conftest.py` or any other file. `tests/shared/__init__.py`
  must already exist (prerequisite).

## Assumptions

1. `tests/shared/__init__.py` already exists (see `implementations/20260704-073815_tests_shared_init_py.md`).
2. `scripts/shared/plugin_tool_invoker.py` already exists (see `implementations/20260704-073719_plugin_tool_invoker_py.md`).
3. `plugin_registry._tools` is a plain dict and can be injected directly in tests, consistent with
   the pattern in `tests/test_tool_executor.py` (`plugin_registry._tools["test_tool"] = ...`).
4. `plugin_registry._reset_for_testing()` clears `_tools` between tests.
5. `uv run pytest` is the test runner; `asyncio_mode = "auto"` is set in `pyproject.toml`.

## Implementation

### Target file

`tests/shared/test_plugin_tool_invoker.py` (new file)

### Procedure

1. Create `tests/shared/test_plugin_tool_invoker.py` with the content below.
2. Run `uv run ruff format tests/shared/test_plugin_tool_invoker.py`.
3. Run `uv run ruff check tests/shared/test_plugin_tool_invoker.py` — expect 0 errors.
4. Run `uv run pytest tests/shared/test_plugin_tool_invoker.py -v` — expect 6 passed.

### Method

```python
"""tests/shared/test_plugin_tool_invoker.py
Unit tests for PluginToolInvoker.try_execute().
"""

from __future__ import annotations

from typing import Any

import pytest
from shared import plugin_registry
from shared.plugin_tool_invoker import PluginToolInvoker


class TestPluginToolInvoker:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        plugin_registry._reset_for_testing()
        yield
        plugin_registry._reset_for_testing()

    @pytest.mark.asyncio
    async def test_no_plugin_returns_none(self) -> None:
        invoker = PluginToolInvoker()
        result = await invoker.try_execute("nonexistent_tool", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_plugin_returns_result(self) -> None:
        async def _fn(args: dict) -> Any:
            return ("ok", False)

        plugin_registry._tools["my_tool"] = (_fn, "my_tool")
        invoker = PluginToolInvoker()
        result = await invoker.try_execute("my_tool", {})
        assert result is not None
        assert result.output == "ok"
        assert result.is_error is False
        assert result.error_type == ""

    @pytest.mark.asyncio
    async def test_plugin_exception_returns_error_result(self) -> None:
        async def _fn(args: dict) -> Any:
            raise RuntimeError("boom")

        plugin_registry._tools["fail_tool"] = (_fn, "fail_tool")
        invoker = PluginToolInvoker()
        result = await invoker.try_execute("fail_tool", {})
        assert result is not None
        assert result.is_error is True
        assert result.error_type == "tool"
        assert "boom" in result.output

    @pytest.mark.asyncio
    async def test_invalid_tuple_length_raises_value_error(self) -> None:
        async def _fn(args: dict) -> Any:
            return ("ok",)

        plugin_registry._tools["bad_len"] = (_fn, "bad_len")
        invoker = PluginToolInvoker()
        with pytest.raises(ValueError, match="must return exactly"):
            await invoker.try_execute("bad_len", {})

    @pytest.mark.asyncio
    async def test_wrong_output_type_raises_type_error(self) -> None:
        async def _fn(args: dict) -> Any:
            return (123, False)

        plugin_registry._tools["bad_output"] = (_fn, "bad_output")
        invoker = PluginToolInvoker()
        with pytest.raises(TypeError, match="output must be str"):
            await invoker.try_execute("bad_output", {})

    @pytest.mark.asyncio
    async def test_wrong_is_error_type_raises_type_error(self) -> None:
        async def _fn(args: dict) -> Any:
            return ("ok", "no")

        plugin_registry._tools["bad_bool"] = (_fn, "bad_bool")
        invoker = PluginToolInvoker()
        with pytest.raises(TypeError, match="is_error must be bool"):
            await invoker.try_execute("bad_bool", {})
```

### Details

- `plugin_registry._tools["my_tool"] = (_fn, "my_tool")` — the tuple stores `(fn, server_key)`.
  Check the actual `_tools` dict structure in `shared/plugin_registries.py` before implementing.
- `plugin_registry.get_tool(tool_name)` returns `fn` only (not the tuple) — verify by reading
  `get_tool()` in `plugin_registry.py`.
- `autouse=True` on `_reset` ensures a clean registry for every test.
- The `yield` in `_reset` makes it both a setup and teardown fixture.

## Validation plan

```bash
# Lint
uv run ruff check tests/shared/test_plugin_tool_invoker.py
# Expected: 0 errors

# Run all 6 tests
uv run pytest tests/shared/test_plugin_tool_invoker.py -v
# Expected: 6 passed

# Confirm no regression in tool_executor tests
uv run pytest tests/test_tool_executor.py -q
# Expected: all pass
```
