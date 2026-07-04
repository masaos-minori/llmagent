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
