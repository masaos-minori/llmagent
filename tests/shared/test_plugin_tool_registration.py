"""tests/shared/test_plugin_tool_registration.py
Tests for plugin registration-time validation via register_tool() and load_plugins().
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shared import plugin_registry


@pytest.fixture(autouse=True)
def reset_registry():  # type: ignore[return]
    plugin_registry._reset_for_testing()
    yield
    plugin_registry._reset_for_testing()


class TestPluginToolRegistration:
    def test_valid_annotation_registers_successfully(self) -> None:
        @plugin_registry.register_tool("valid_tool")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("valid_tool") is not None

    def test_missing_annotation_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="missing return type annotation"):

            @plugin_registry.register_tool("bad_tool")
            async def handler(args):  # noqa: ANN001,ANN201
                return "ok", False

    def test_wrong_annotation_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="expected return type"):

            @plugin_registry.register_tool("wrong_tool")
            async def handler(args: dict) -> str:
                return "x"

    def test_invalid_plugin_not_in_registry(self) -> None:
        try:

            @plugin_registry.register_tool("absent_tool")
            async def handler(args):  # noqa: ANN001,ANN201
                return "ok", False
        except ValueError:
            pass
        assert plugin_registry.get_tool("absent_tool") is None

    def test_non_strict_load_records_failure_and_continues(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "bad.py").write_text(
            "from shared.plugin_registry import register_tool\n"
            "@register_tool('bad')\n"
            "async def h(args): return 'x', False\n"
        )
        (tmp_path / "ok.py").write_text(
            "from shared.plugin_registry import register_tool\n"
            "@register_tool('ok')\n"
            "async def h(args: dict) -> tuple[str, bool]: return 'x', False\n"
        )
        result = plugin_registry.load_plugins(tmp_path)
        assert result.loaded_count == 1
        assert len(result.failed) == 1
        assert "missing return type annotation" in result.failed[0].error

    def test_strict_mode_raises_plugin_load_error(self, tmp_path: Path) -> None:
        (tmp_path / "bad.py").write_text(
            "from shared.plugin_registry import register_tool\n"
            "@register_tool('bad')\n"
            "async def h(args): return 'x', False\n"
        )
        with pytest.raises(plugin_registry.PluginLoadError):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)
