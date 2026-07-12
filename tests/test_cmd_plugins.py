"""tests/test_cmd_plugins.py
Tests for /plugin command handler in cmd_plugins.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.commands.cmd_plugins import _PluginsMixin
from agent.commands.output_port import CliOutputPort


def _make_mixin() -> _PluginsMixin:
    mixin = _PluginsMixin.__new__(_PluginsMixin)
    mixin._out = MagicMock(spec=CliOutputPort)
    return mixin


class TestCmdPlugin:
    def test_no_result_writes_no_data(self) -> None:
        mixin = _make_mixin()
        with patch(
            "shared.plugin_auto_discover.get_last_load_result", return_value=None
        ):
            mixin._cmd_plugin("status")
        mixin._out.write_no_data.assert_called_once()

    def test_result_writes_table(self) -> None:
        from shared.plugin_registry import PluginLoadResult

        result = PluginLoadResult(
            loaded_count=3,
            failed=(),
            tool_conflicts_shadowed=1,
            tool_conflicts_allowed=0,
        )
        mixin = _make_mixin()
        with patch(
            "shared.plugin_auto_discover.get_last_load_result", return_value=result
        ):
            mixin._cmd_plugin("status")
        mixin._out.write_table.assert_called_once()
        args = mixin._out.write_table.call_args[0]
        headers, rows = args[0], args[1]
        assert "Metric" in headers
        loaded_row = next(r for r in rows if r[0] == "Loaded")
        assert loaded_row[1] == "3"
        shadow_row = next(r for r in rows if r[0] == "Command shadows (rejected)")
        assert shadow_row[1] == "0"  # default value

    def test_failed_plugins_listed(self) -> None:
        from shared.plugin_registry import PluginLoadResult
        from shared.plugin_result import PluginFailure

        result = PluginLoadResult(
            loaded_count=1,
            failed=(PluginFailure(path="plugins/bad.py", error="SyntaxError"),),
        )
        mixin = _make_mixin()
        with patch(
            "shared.plugin_auto_discover.get_last_load_result", return_value=result
        ):
            mixin._cmd_plugin("status")
        writes = [call[0][0] for call in mixin._out.write.call_args_list]
        assert any("bad.py" in w for w in writes)

    def test_no_failures_no_extra_write(self) -> None:
        from shared.plugin_registry import PluginLoadResult

        result = PluginLoadResult(loaded_count=2, failed=())
        mixin = _make_mixin()
        with patch(
            "shared.plugin_auto_discover.get_last_load_result", return_value=result
        ):
            mixin._cmd_plugin("status")
        mixin._out.write.assert_not_called()
