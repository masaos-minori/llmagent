# Implementation: tests/test_plugin_contract.py — Plugin contract validation tests

## Goal

Test all registration-time and runtime contract violation cases, plus strict vs non-strict mode behavior.

## Scope

**In**: Tests for `register_tool()` and `PluginToolInvoker.try_execute()` contract validation.

**Out**: Source file changes.

## Assumptions

1. Tests call `_reset_for_testing()` before each test that registers tools.
2. Runtime tests call `PluginToolInvoker().try_execute()` directly.
3. Non-strict plugin load tests use `load_plugins()` with a temp plugin dir.

## Implementation

### Target file
`tests/test_plugin_contract.py`

### Procedure
Write parameterized pytest tests for each contract violation case.

### Method

```python
import asyncio
from shared.plugin_registry import register_tool, _reset_for_testing
from shared.plugin_tool_invoker import PluginToolInvoker

# Registration-time tests

def test_missing_return_annotation_rejected():
    _reset_for_testing()
    with pytest.raises(ValueError, match="missing return type annotation"):
        @register_tool("bad_tool")
        async def bad(args: dict):
            return "ok", False

def test_wrong_return_annotation_rejected():
    _reset_for_testing()
    with pytest.raises(ValueError, match="expected return type"):
        @register_tool("bad_tool")
        async def bad(args: dict) -> str:
            return "ok"

def test_non_async_handler_rejected():
    _reset_for_testing()
    with pytest.raises(ValueError, match="must be an async function"):
        @register_tool("bad_tool")
        def bad(args: dict) -> tuple[str, bool]:
            return "ok", False

def test_valid_plugin_registers():
    _reset_for_testing()
    @register_tool("good_tool")
    async def good(args: dict) -> tuple[str, bool]:
        return "ok", False
    from shared.plugin_registry import get_tool
    assert get_tool("good_tool") is good

# Runtime tests

@pytest.mark.asyncio
async def test_runtime_not_tuple():
    _reset_for_testing()
    @register_tool("rt_tool")
    async def bad_rt(args: dict) -> tuple[str, bool]:
        return "not a tuple"  # type: ignore
    invoker = PluginToolInvoker()
    result = await invoker.try_execute("rt_tool", {})
    assert result is not None
    assert result.is_error is True
    assert "tuple" in result.output.lower()

@pytest.mark.asyncio
async def test_runtime_tuple_wrong_length():
    _reset_for_testing()
    @register_tool("rt_tool2")
    async def bad_rt(args: dict) -> tuple[str, bool]:
        return ("a", False, "extra")  # type: ignore
    invoker = PluginToolInvoker()
    result = await invoker.try_execute("rt_tool2", {})
    assert result.is_error is True

@pytest.mark.asyncio
async def test_runtime_first_not_str():
    _reset_for_testing()
    @register_tool("rt_tool3")
    async def bad_rt(args: dict) -> tuple[str, bool]:
        return (123, False)  # type: ignore
    invoker = PluginToolInvoker()
    result = await invoker.try_execute("rt_tool3", {})
    assert result.is_error is True
    assert "str" in result.output.lower()

@pytest.mark.asyncio
async def test_runtime_second_not_bool():
    _reset_for_testing()
    @register_tool("rt_tool4")
    async def bad_rt(args: dict) -> tuple[str, bool]:
        return ("ok", "not_bool")  # type: ignore
    invoker = PluginToolInvoker()
    result = await invoker.try_execute("rt_tool4", {})
    assert result.is_error is True
    assert "bool" in result.output.lower()

# Strict mode tests

def test_strict_mode_raises_on_invalid_plugin(tmp_path):
    plugin_code = "from shared.plugin_registry import register_tool\n@register_tool('bad')\ndef not_async(args): return 'x', False\n"
    (tmp_path / "bad_plugin.py").write_text(plugin_code)
    from shared.plugin_registry import load_plugins, _reset_for_testing
    _reset_for_testing()
    from shared.plugin_result import PluginLoadError
    with pytest.raises(PluginLoadError):
        load_plugins(tmp_path, strict_mode=True)

def test_non_strict_mode_continues_after_invalid(tmp_path):
    bad_plugin = "from shared.plugin_registry import register_tool\n@register_tool('bad')\ndef not_async(args): return 'x', False\n"
    good_plugin = "from shared.plugin_registry import register_tool\n@register_tool('good')\nasync def g(args: dict) -> tuple[str, bool]: return 'ok', False\n"
    (tmp_path / "bad_plugin.py").write_text(bad_plugin)
    (tmp_path / "good_plugin.py").write_text(good_plugin)
    from shared.plugin_registry import load_plugins, _reset_for_testing, get_tool
    _reset_for_testing()
    result = load_plugins(tmp_path, strict_mode=False)
    assert result.loaded_count == 1  # good_plugin loaded
    assert len(result.failed) == 1   # bad_plugin failed
    assert get_tool("good") is not None
    assert get_tool("bad") is None
```

## Validation plan

- `uv run pytest tests/test_plugin_contract.py -v` — all pass.
- `ruff check tests/test_plugin_contract.py` — 0 errors.
