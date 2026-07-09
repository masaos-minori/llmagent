"""tests/test_plugin_contract.py
Plugin contract validation tests: registration-time and runtime.
"""

from __future__ import annotations

import pytest

# ── registration-time checks ──────────────────────────────────────────────────


def test_missing_return_annotation_rejected() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool

    _reset_for_testing()
    with pytest.raises(ValueError, match="missing return type annotation"):

        @register_tool("bad_tool")
        async def bad(args: dict):  # type: ignore[return]
            return "ok", False


def test_wrong_return_annotation_rejected() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool

    _reset_for_testing()
    with pytest.raises(ValueError, match="expected return type"):

        @register_tool("bad_tool")
        async def bad(args: dict) -> str:  # type: ignore[return]
            return "ok"  # type: ignore[return-value]


def test_non_async_handler_rejected() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool

    _reset_for_testing()
    with pytest.raises(ValueError, match="must be an async function"):

        @register_tool("bad_tool")
        def bad(args: dict) -> tuple[str, bool]:  # type: ignore[return]
            return "ok", False


def test_valid_plugin_registers() -> None:
    from shared.plugin_registry import _reset_for_testing, get_tool, register_tool

    _reset_for_testing()

    @register_tool("good_tool")
    async def good(args: dict) -> tuple[str, bool]:
        return "ok", False

    assert get_tool("good_tool") is good


# ── runtime contract checks ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_runtime_not_tuple() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("rt_tool")
    async def bad_rt(args: dict) -> tuple[str, bool]:  # type: ignore[return]
        return "not a tuple"  # type: ignore[return-value]

    result = await PluginToolInvoker().try_execute("rt_tool", {})
    assert result is not None
    assert result.is_error is True
    assert "tuple" in result.output.lower()


@pytest.mark.asyncio
async def test_runtime_tuple_wrong_length() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("rt_tool2")
    async def bad_rt(args: dict) -> tuple[str, bool]:  # type: ignore[return]
        return ("a", False, "extra")  # type: ignore[return-value]

    result = await PluginToolInvoker().try_execute("rt_tool2", {})
    assert result is not None
    assert result.is_error is True


@pytest.mark.asyncio
async def test_runtime_first_not_str() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("rt_tool3")
    async def bad_rt(args: dict) -> tuple[str, bool]:  # type: ignore[return]
        return (123, False)  # type: ignore[return-value]

    result = await PluginToolInvoker().try_execute("rt_tool3", {})
    assert result is not None
    assert result.is_error is True
    assert "str" in result.output.lower()


@pytest.mark.asyncio
async def test_runtime_second_not_bool() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("rt_tool4")
    async def bad_rt(args: dict) -> tuple[str, bool]:  # type: ignore[return]
        return ("ok", "not_bool")  # type: ignore[return-value]

    result = await PluginToolInvoker().try_execute("rt_tool4", {})
    assert result is not None
    assert result.is_error is True
    assert "bool" in result.output.lower()


@pytest.mark.asyncio
async def test_runtime_valid_returns_result() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("rt_good")
    async def good_rt(args: dict) -> tuple[str, bool]:
        return "hello", False

    result = await PluginToolInvoker().try_execute("rt_good", {})
    assert result is not None
    assert result.is_error is False
    assert result.output == "hello"


# ── strict vs non-strict mode ─────────────────────────────────────────────────


def test_strict_mode_raises_on_invalid_plugin(tmp_path) -> None:  # type: ignore[type-arg]
    from shared.plugin_registry import PluginLoadError, _reset_for_testing, load_plugins

    plugin_code = (
        "from shared.plugin_registry import register_tool\n"
        "@register_tool('bad')\n"
        "def not_async(args): return 'x', False\n"
    )
    (tmp_path / "bad_plugin.py").write_text(plugin_code)
    _reset_for_testing()
    with pytest.raises(PluginLoadError):
        load_plugins(tmp_path, strict_mode=True)


def test_non_strict_mode_continues_after_invalid(tmp_path) -> None:  # type: ignore[type-arg]
    from shared.plugin_registry import _reset_for_testing, get_tool, load_plugins

    bad_plugin = (
        "from shared.plugin_registry import register_tool\n"
        "@register_tool('bad')\n"
        "def not_async(args): return 'x', False\n"
    )
    good_plugin = (
        "from shared.plugin_registry import register_tool\n"
        "@register_tool('good')\n"
        "async def g(args: dict) -> tuple[str, bool]: return 'ok', False\n"
    )
    (tmp_path / "bad_plugin.py").write_text(bad_plugin)
    (tmp_path / "good_plugin.py").write_text(good_plugin)
    _reset_for_testing()
    result = load_plugins(tmp_path, strict_mode=False)
    assert result.loaded_count == 1
    assert len(result.failed) == 1
    assert get_tool("good") is not None
    assert get_tool("bad") is None


# ── Plugin audit source field tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_plugin_result_has_source_plugin_on_success() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("src_test_ok")
    async def ok_rt(args: dict) -> tuple[str, bool]:
        return "ok", False

    result = await PluginToolInvoker().try_execute("src_test_ok", {})
    assert result is not None
    assert result.source == "plugin"
    assert result.is_error is False
    assert result.output == "ok"


@pytest.mark.asyncio
async def test_plugin_result_has_source_plugin_on_error() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("src_test_err")
    async def err_rt(args: dict) -> tuple[str, bool]:
        raise RuntimeError("boom")

    result = await PluginToolInvoker().try_execute("src_test_err", {})
    assert result is not None
    assert result.source == "plugin"
    assert result.is_error is True
    assert "[plugin error]" in result.output


@pytest.mark.asyncio
async def test_plugin_result_has_source_plugin_on_contract_violation() -> None:
    from shared.plugin_registry import _reset_for_testing, register_tool
    from shared.plugin_tool_invoker import PluginToolInvoker

    _reset_for_testing()

    @register_tool("src_test_contract")
    async def bad_rt(args: dict) -> tuple[str, bool]:  # type: ignore[return]
        return ("a", False, "extra")  # type: ignore[return-value]

    result = await PluginToolInvoker().try_execute("src_test_contract", {})
    assert result is not None
    assert result.source == "plugin"
    assert result.is_error is True
    assert "contract violation" in result.output.lower()
