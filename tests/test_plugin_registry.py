"""
tests/test_plugin_registry.py
Unit tests for plugin_registry: decorators, accessors, and load_plugins().
"""

from __future__ import annotations

import asyncio
import textwrap
from pathlib import Path

import pytest
import shared.plugin_registry as plugin_registry

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_registry():
    """Clear all plugin registries before each test to prevent cross-test pollution."""
    plugin_registry._reset_for_testing()
    yield
    plugin_registry._reset_for_testing()


# ── @register_command ─────────────────────────────────────────────────────────


class TestRegisterCommand:
    def test_sync_command_registered(self):
        @plugin_registry.register_command("/test")
        def cmd(ctx: object, args: str) -> None:
            pass

        entry = plugin_registry.get_command("/test")
        assert entry is not None
        handler, is_prefix = entry
        assert handler is cmd
        assert is_prefix is False

    def test_prefix_command_flag(self):
        @plugin_registry.register_command("/foo", prefix=True)
        async def cmd(ctx: object, args: str) -> None:
            pass

        _, is_prefix = plugin_registry.get_command("/foo")
        assert is_prefix is True

    def test_get_command_unknown_returns_none(self):
        assert plugin_registry.get_command("/nonexistent") is None

    def test_iter_commands_snapshot(self):
        @plugin_registry.register_command("/a")
        def a(ctx: object, args: str) -> None:
            pass

        @plugin_registry.register_command("/b")
        def b(ctx: object, args: str) -> None:
            pass

        snapshot = plugin_registry.iter_commands()
        assert set(snapshot.keys()) == {"/a", "/b"}

    def test_decorator_returns_original_function(self):
        @plugin_registry.register_command("/id")
        async def my_fn(ctx: object, args: str) -> None:
            pass

        assert my_fn.__name__ == "my_fn"


# ── @register_tool ────────────────────────────────────────────────────────────


class TestRegisterTool:
    def test_tool_registered(self):
        @plugin_registry.register_tool("my_tool")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("my_tool") is handler

    def test_get_tool_unknown_returns_none(self):
        assert plugin_registry.get_tool("no_such_tool") is None

    def test_tool_callable(self):
        @plugin_registry.register_tool("echo")
        async def handler(args: dict) -> tuple[str, bool]:
            return str(args.get("text", "")), False

        result, is_error = asyncio.run(handler({"text": "hello"}))
        assert result == "hello"
        assert is_error is False


# ── @register_pipeline_stage ──────────────────────────────────────────────────


class TestRegisterPipelineStage:
    def test_post_stage_registered(self):
        @plugin_registry.register_pipeline_stage(when="post")
        async def stage(hits: list, query: str) -> list:
            return hits

        stages = plugin_registry.get_pipeline_post_stages()
        assert stage in stages

    def test_multiple_stages_ordered(self):
        calls: list[str] = []

        @plugin_registry.register_pipeline_stage(when="post")
        async def first(hits: list, query: str) -> list:
            calls.append("first")
            return hits

        @plugin_registry.register_pipeline_stage(when="post")
        async def second(hits: list, query: str) -> list:
            calls.append("second")
            return hits

        stages = plugin_registry.get_pipeline_post_stages()
        assert stages[0] is first
        assert stages[1] is second

    def test_invalid_when_raises(self):
        with pytest.raises(ValueError, match="post"):
            plugin_registry.register_pipeline_stage(when="pre")

    def test_stage_snapshot_is_copy(self):
        @plugin_registry.register_pipeline_stage(when="post")
        async def s(hits: list, query: str) -> list:
            return hits

        a = plugin_registry.get_pipeline_post_stages()
        b = plugin_registry.get_pipeline_post_stages()
        assert a is not b


# ── load_plugins ──────────────────────────────────────────────────────────────


class TestLoadPlugins:
    def test_missing_dir_returns_zero(self, tmp_path: Path):
        n = plugin_registry.load_plugins(tmp_path / "nonexistent")
        assert n == 0

    def test_empty_dir_returns_zero(self, tmp_path: Path):
        (tmp_path / "plugins").mkdir()
        n = plugin_registry.load_plugins(tmp_path / "plugins")
        assert n == 0

    def test_plugin_file_loaded_and_registers(self, tmp_path: Path):
        plugin_file = tmp_path / "my_plugin.py"
        plugin_file.write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/hello")
                async def cmd(ctx, args):
                    pass
            """)
        )
        n = plugin_registry.load_plugins(tmp_path)
        assert n == 1
        assert plugin_registry.get_command("/hello") is not None

    def test_broken_plugin_skipped(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('boom')")
        (tmp_path / "good.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("good_tool")
                async def t(args):
                    return "", False
            """)
        )
        n = plugin_registry.load_plugins(tmp_path)
        # bad.py fails but good.py succeeds
        assert n == 1
        assert plugin_registry.get_tool("good_tool") is not None

    def test_load_plugins_accepts_string_path(self, tmp_path: Path):
        n = plugin_registry.load_plugins(str(tmp_path))
        assert n == 0


# ── _reset_for_testing ────────────────────────────────────────────────────────


class TestReset:
    def test_reset_clears_all_registries(self):
        @plugin_registry.register_command("/x")
        def c(ctx: object, args: str) -> None:
            pass

        @plugin_registry.register_tool("x")
        async def t(args: dict) -> tuple[str, bool]:
            return "", False

        @plugin_registry.register_pipeline_stage(when="post")
        async def s(hits: list, query: str) -> list:
            return hits

        plugin_registry._reset_for_testing()

        assert plugin_registry.get_command("/x") is None
        assert plugin_registry.get_tool("x") is None
        assert plugin_registry.get_pipeline_post_stages() == []
