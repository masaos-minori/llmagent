"""
tests/test_plugin_registry.py
Unit tests for plugin_registry: decorators, accessors, and load_plugins().
"""

from __future__ import annotations

import asyncio
import logging
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


# ── @register_tool conflict detection (via _validate_tool_conflicts) ─────────


class TestRegisterToolConflict:
    def test_conflict_rejected_by_default(self, caplog):
        # Register a tool that conflicts with a known MCP tool name
        @plugin_registry.register_tool("list_directory")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("list_directory") is not None

        mcp_tools = frozenset({"list_directory"})
        plugin_registry._validate_tool_conflicts(mcp_tools, "reject")

        assert plugin_registry.get_tool("list_directory") is None
        assert any("rejected" in r.message for r in caplog.records)

    def test_conflict_allowed_with_override(self, caplog):
        @plugin_registry.register_tool("list_directory")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("list_directory") is not None

        mcp_tools = frozenset({"list_directory"})
        with caplog.at_level(logging.WARNING):
            plugin_registry._validate_tool_conflicts(mcp_tools, "allow")

        assert plugin_registry.get_tool("list_directory") is not None
        assert any("shadows MCP tool" in r.message for r in caplog.records)

    def test_no_conflict_succeeds(self):
        @plugin_registry.register_tool("my_unique_tool")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        mcp_tools = frozenset({"list_directory"})
        plugin_registry._validate_tool_conflicts(mcp_tools, "reject")

        assert plugin_registry.get_tool("my_unique_tool") is not None

    def test_no_known_tools_disables_check(self):
        @plugin_registry.register_tool("list_directory")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        plugin_registry._validate_tool_conflicts(frozenset(), "reject")
        assert plugin_registry.get_tool("list_directory") is not None


# ── load_plugins conflict detection ──────────────────────────────────────────


class TestLoadPluginsConflict:
    def test_conflicting_plugin_skipped_in_reject_mode(self, tmp_path: Path):
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args):
                    return "", False
            """)
        )
        (tmp_path / "good_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("my_tool")
                async def t(args):
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory"})
        result = plugin_registry.load_plugins(
            tmp_path,
            known_tools=mcp_tools,
            override_policy="reject",
        )
        # Both modules load (loaded_count=2), but conflicting tool is removed
        assert result.loaded_count == 2
        assert plugin_registry.get_tool("my_tool") is not None
        assert plugin_registry.get_tool("list_directory") is None

    def test_conflicting_plugin_allowed_in_allow_mode(self, tmp_path: Path):
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args):
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory"})
        result = plugin_registry.load_plugins(
            tmp_path,
            known_tools=mcp_tools,
            override_policy="allow",
        )
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("list_directory") is not None

    def test_non_conflicting_plugin_loads_in_reject_mode(self, tmp_path: Path):
        (tmp_path / "safe_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("my_safe_tool")
                async def t(args):
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory"})
        result = plugin_registry.load_plugins(
            tmp_path,
            known_tools=mcp_tools,
            override_policy="reject",
        )
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("my_safe_tool") is not None

    def test_load_plugins_default_no_conflict_check(self, tmp_path: Path):
        # Default params: no known_tools, so no conflict check
        (tmp_path / "shadow_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args):
                    return "", False
            """)
        )
        result = plugin_registry.load_plugins(tmp_path)
        assert result.loaded_count == 1


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
        result = plugin_registry.load_plugins(tmp_path / "nonexistent")
        assert result.loaded_count == 0

    def test_empty_dir_returns_zero(self, tmp_path: Path):
        (tmp_path / "plugins").mkdir()
        result = plugin_registry.load_plugins(tmp_path / "plugins")
        assert result.loaded_count == 0

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
        result = plugin_registry.load_plugins(tmp_path)
        assert result.loaded_count == 1
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
        result = plugin_registry.load_plugins(tmp_path)
        # bad.py fails but good.py succeeds
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("good_tool") is not None

    def test_load_plugins_accepts_string_path(self, tmp_path: Path):
        result = plugin_registry.load_plugins(str(tmp_path))
        assert result.loaded_count == 0

    def test_failure_details_included(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('boom')")
        result = plugin_registry.load_plugins(tmp_path)
        assert len(result.failed) == 1
        assert result.failed[0].path == "bad.py"
        assert "RuntimeError" in result.failed[0].error
        assert "boom" in result.failed[0].error

    def test_empty_failed_when_all_succeed(self, tmp_path: Path):
        (tmp_path / "good.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("ok_tool")
                async def t(args):
                    return "", False
            """)
        )
        result = plugin_registry.load_plugins(tmp_path)
        assert result.failed == ()


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


# ── Strict plugin loading mode ────────────────────────────────────────────────


class TestLoadPluginsStrictMode:
    def test_strict_mode_all_load_success(self, tmp_path: Path):
        plugin_file = tmp_path / "ok.py"
        plugin_file.write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("strict_tool")
                async def t(args):
                    return "", False
            """)
        )
        result = plugin_registry.load_plugins(tmp_path, strict_mode=True)
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("strict_tool") is not None

    def test_strict_mode_broken_plugin_raises(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('boom')")
        with pytest.raises(RuntimeError, match="boom"):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)

    def test_non_strict_mode_broken_plugin_continues(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('oops')")
        (tmp_path / "good.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("survive_tool")
                async def t(args):
                    return "", False
            """)
        )
        result = plugin_registry.load_plugins(tmp_path, strict_mode=False)
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("survive_tool") is not None

    def test_missing_dir_strict_mode_returns_zero(self, tmp_path: Path):
        result = plugin_registry.load_plugins(
            tmp_path / "nonexistent", strict_mode=True
        )
        assert result.loaded_count == 0

    def test_strict_mode_does_not_collect_failures(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('strict_boom')")
        with pytest.raises(RuntimeError, match="strict_boom"):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)


# ── run_pipeline_stages() error isolation ─────────────────────────────────────


class TestRunPipelineStages:
    """Tests for run_pipeline_stages() hook error isolation."""

    @pytest.mark.asyncio
    async def test_no_hooks_returns_original(self) -> None:
        hits: list = [{"url": "u1"}, {"url": "u2"}]
        result = await plugin_registry.run_pipeline_stages(hits, "test query")
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_modifies_hits(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def add_score(hits: list, query: str) -> list:
            return [{**h, "score": 1.0} for h in hits]

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_async_hook_modifies_hits(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        async def async_tag(hits: list, query: str) -> list:
            return [{**h, "async": True} for h in hits]

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result[0]["async"] is True

    @pytest.mark.asyncio
    async def test_hook_isolation_skips_failed_sync(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def bad_hook(hits: list, query: str) -> list:
            raise RuntimeError("sync failure")

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_isolation_skips_failed_async(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        async def bad_async(hits: list, query: str) -> list:
            raise ValueError("async failure")

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_strict_mode_re_raises(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def strict_fail(hits: list, query: str) -> list:
            raise RuntimeError("strict mode error")

        with pytest.raises(RuntimeError, match="strict mode error"):
            await plugin_registry.run_pipeline_stages([{"url": "u"}], "q", strict=True)

    @pytest.mark.asyncio
    async def test_multiple_hooks_first_fails_second_runs(self) -> None:
        ran: dict[str, bool] = {"second": False}

        @plugin_registry.register_pipeline_stage(when="post")
        def first_fail(hits: list, query: str) -> list:
            raise RuntimeError("first fails")

        @plugin_registry.register_pipeline_stage(when="post")
        def second_ok(hits: list, query: str) -> list:
            ran["second"] = True
            return hits

        hits: list = [{"url": "u"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert ran["second"] is True
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_returning_none_keeps_prior_hits(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def no_return(hits: list, query: str) -> None:
            return None

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result == hits
