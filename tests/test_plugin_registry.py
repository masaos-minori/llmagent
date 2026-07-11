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
from shared.plugin_conflicts import validate_tool_conflicts
from shared.plugin_result import PluginLoadError

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


# ── @register_tool conflict detection (via validate_tool_conflicts) ─────────


class TestRegisterToolConflict:
    def test_conflict_rejected_by_default(self, caplog):
        # Register a tool that conflicts with a known MCP tool name
        @plugin_registry.register_tool("list_directory")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("list_directory") is not None

        mcp_tools = frozenset({"list_directory"})
        with caplog.at_level(logging.INFO, logger="shared.plugin_conflicts"):
            validate_tool_conflicts(mcp_tools, "reject")

        assert plugin_registry.get_tool("list_directory") is None
        assert any("rejected" in r.message for r in caplog.records)

    def test_conflict_allowed_with_override(self, caplog):
        @plugin_registry.register_tool("list_directory")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("list_directory") is not None

        mcp_tools = frozenset({"list_directory"})
        with caplog.at_level(logging.INFO, logger="shared.plugin_conflicts"):
            validate_tool_conflicts(mcp_tools, "allow")

        assert plugin_registry.get_tool("list_directory") is not None
        assert any("shadows MCP tool" in r.message for r in caplog.records)

    def test_no_conflict_succeeds(self):
        @plugin_registry.register_tool("my_unique_tool")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        mcp_tools = frozenset({"list_directory"})
        validate_tool_conflicts(mcp_tools, "reject")

        assert plugin_registry.get_tool("my_unique_tool") is not None

    def test_no_known_tools_disables_check(self):
        @plugin_registry.register_tool("list_directory")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        validate_tool_conflicts(frozenset(), "reject")
        assert plugin_registry.get_tool("list_directory") is not None


# ── load_plugins conflict detection ──────────────────────────────────────────


class TestLoadPluginsConflict:
    def test_conflicting_plugin_skipped_in_reject_mode(self, tmp_path: Path):
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        (tmp_path / "good_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("my_tool")
                async def t(args) -> tuple[str, bool]:
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
                async def t(args) -> tuple[str, bool]:
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
                async def t(args) -> tuple[str, bool]:
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
                async def t(args) -> tuple[str, bool]:
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
                async def t(args) -> tuple[str, bool]:
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
                async def t(args) -> tuple[str, bool]:
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


class TestRegistryIsolation:
    def test_repeated_load_accumulates_registrations(self, tmp_path: Path) -> None:
        """Sequential load_plugins() calls add to existing registries without clearing."""
        dir_a = tmp_path / "plugins_a"
        dir_a.mkdir()
        (dir_a / "tool_a.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("isolation_tool_a")
                async def t(args: dict) -> tuple[str, bool]:
                    return "", False
            """)
        )
        dir_b = tmp_path / "plugins_b"
        dir_b.mkdir()
        (dir_b / "tool_b.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("isolation_tool_b")
                async def t(args: dict) -> tuple[str, bool]:
                    return "", False
            """)
        )

        plugin_registry.load_plugins(dir_a)
        plugin_registry.load_plugins(dir_b)

        assert plugin_registry.get_tool("isolation_tool_a") is not None
        assert plugin_registry.get_tool("isolation_tool_b") is not None

    def test_reset_between_loads_yields_clean_state(self, tmp_path: Path) -> None:
        """_reset_for_testing() between load_plugins() calls clears earlier registrations."""
        dir_a = tmp_path / "plugins_a"
        dir_a.mkdir()
        (dir_a / "tool_a.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("isolation_reset_tool_a")
                async def t(args: dict) -> tuple[str, bool]:
                    return "", False
            """)
        )
        dir_b = tmp_path / "plugins_b"
        dir_b.mkdir()
        (dir_b / "tool_b.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("isolation_reset_tool_b")
                async def t(args: dict) -> tuple[str, bool]:
                    return "", False
            """)
        )

        plugin_registry.load_plugins(dir_a)
        plugin_registry._reset_for_testing()
        plugin_registry.load_plugins(dir_b)

        assert plugin_registry.get_tool("isolation_reset_tool_a") is None
        assert plugin_registry.get_tool("isolation_reset_tool_b") is not None


# ── Strict plugin loading mode ────────────────────────────────────────────────


class TestLoadPluginsStrictMode:
    def test_strict_mode_all_load_success(self, tmp_path: Path):
        plugin_file = tmp_path / "ok.py"
        plugin_file.write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("strict_tool")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        result = plugin_registry.load_plugins(tmp_path, strict_mode=True)
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("strict_tool") is not None

    def test_strict_mode_broken_plugin_raises(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('boom')")
        with pytest.raises(PluginLoadError, match="boom"):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)

    def test_non_strict_mode_broken_plugin_continues(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('oops')")
        (tmp_path / "good.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("survive_tool")
                async def t(args) -> tuple[str, bool]:
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

    def test_strict_mode_raises_plugin_load_error(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('strict_boom')")
        with pytest.raises(PluginLoadError, match="strict_boom"):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)


# ── run_pipeline_stages() error isolation ─────────────────────────────────────


class TestRunPipelineStages:
    """Tests for run_pipeline_stages() hook error isolation."""

    @pytest.mark.asyncio
    async def test_no_hooks_returns_original(self) -> None:
        hits: list = [{"url": "u1"}, {"url": "u2"}]
        result = await plugin_registry.run_pipeline_stages([], hits, "test query")
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_modifies_hits(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def add_score(hits: list, query: str) -> list:
            return [{**h, "score": 1.0} for h in hits]

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(
            plugin_registry.get_pipeline_post_stages(), hits, "q"
        )
        assert result[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_async_hook_modifies_hits(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        async def async_tag(hits: list, query: str) -> list:
            return [{**h, "async": True} for h in hits]

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(
            plugin_registry.get_pipeline_post_stages(), hits, "q"
        )
        assert result[0]["async"] is True

    @pytest.mark.asyncio
    async def test_hook_isolation_skips_failed_sync(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def bad_hook(hits: list, query: str) -> list:
            raise RuntimeError("sync failure")

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(
            plugin_registry.get_pipeline_post_stages(), hits, "q"
        )
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_isolation_skips_failed_async(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        async def bad_async(hits: list, query: str) -> list:
            raise ValueError("async failure")

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(
            plugin_registry.get_pipeline_post_stages(), hits, "q"
        )
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_strict_mode_re_raises(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def strict_fail(hits: list, query: str) -> list:
            raise RuntimeError("strict mode error")

        with pytest.raises(RuntimeError, match="strict mode error"):
            await plugin_registry.run_pipeline_stages(
                plugin_registry.get_pipeline_post_stages(),
                [{"url": "u"}],
                "q",
                strict=True,
            )

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
        result = await plugin_registry.run_pipeline_stages(
            plugin_registry.get_pipeline_post_stages(), hits, "q"
        )
        assert ran["second"] is True
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_returning_none_keeps_prior_hits(self) -> None:
        @plugin_registry.register_pipeline_stage(when="post")
        def no_return(hits: list, query: str) -> None:
            return None

        hits: list = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(
            plugin_registry.get_pipeline_post_stages(), hits, "q"
        )
        assert result == hits


# ── New behaviors (Steps 1-4) ─────────────────────────────────────────────────


class TestPluginLoadError:
    def test_is_runtime_error_subclass(self):
        assert issubclass(PluginLoadError, RuntimeError)

    def test_aggregated_error_strict_mode(self, tmp_path: Path):
        (tmp_path / "bad1.py").write_text("raise RuntimeError('first_fail')")
        (tmp_path / "bad2.py").write_text("raise RuntimeError('second_fail')")
        with pytest.raises(PluginLoadError) as exc_info:
            plugin_registry.load_plugins(tmp_path, strict_mode=True)
        msg = str(exc_info.value)
        assert "first_fail" in msg
        assert "second_fail" in msg

    def test_aggregated_error_contains_all_module_names(self, tmp_path: Path):
        (tmp_path / "alpha.py").write_text("raise ImportError('no_module')")
        (tmp_path / "beta.py").write_text("raise RuntimeError('bad_runtime')")
        with pytest.raises(PluginLoadError) as exc_info:
            plugin_registry.load_plugins(tmp_path, strict_mode=True)
        msg = str(exc_info.value)
        assert "alpha.py" in msg
        assert "beta.py" in msg


class TestConflictLogging:
    def test_conflict_log_has_plugin_prefix(self, caplog):
        @plugin_registry.register_tool("search_web")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        with caplog.at_level(logging.INFO, logger="shared.plugin_conflicts"):
            validate_tool_conflicts(frozenset({"search_web"}), "reject")

        assert any("[plugin] conflict:" in r.message for r in caplog.records)

    def test_conflict_log_contains_module_name(self, caplog, tmp_path: Path):
        (tmp_path / "mymod.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("conflict_tool")
                async def t(args: dict) -> tuple[str, bool]:
                    return "", False
            """)
        )
        with caplog.at_level(logging.INFO, logger="shared.plugin_auto_discover"):
            plugin_registry.load_plugins(
                tmp_path,
                known_tools=frozenset({"conflict_tool"}),
                override_policy="reject",
            )
        assert any("mymod" in r.message for r in caplog.records)


class TestSignatureWarning:
    def test_missing_return_annotation_raises(self):
        with pytest.raises(ValueError, match="missing return type annotation"):

            @plugin_registry.register_tool("no_return_type")
            async def handler(args: dict):
                return "ok", False

    def test_wrong_return_annotation_raises(self):
        with pytest.raises(ValueError, match="expected return type"):

            @plugin_registry.register_tool("wrong_return")
            async def handler(args: dict) -> str:
                return "ok"

    def test_correct_return_annotation_succeeds(self):
        @plugin_registry.register_tool("correct_return")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("correct_return") is handler


class TestCommandShadowLogging:
    def test_command_shadow_always_logged_at_info(self, caplog, tmp_path: Path):
        plugin_registry.register_builtin_commands(frozenset({"/debug", "/help"}))
        try:
            (tmp_path / "shadow_cmd.py").write_text(
                textwrap.dedent("""\
                    from shared.plugin_registry import register_command

                    @register_command("/debug")
                    async def cmd(ctx, args):
                        pass
                """)
            )
            with caplog.at_level(logging.INFO):
                plugin_registry.load_plugins(tmp_path, strict_mode=False)

            info_records = [r for r in caplog.records if r.levelno == logging.INFO]
            assert any("command shadow rejected" in r.message for r in info_records)
            assert plugin_registry.get_command("/debug") is None
        finally:
            plugin_registry._builtin_command_names[0] = frozenset()


class TestCommandShadowRejection:
    def test_shadow_command_removed_from_registry(self, tmp_path: Path) -> None:
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "shadow_help.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/help")
                async def cmd(ctx, args):
                    pass
            """)
        )
        plugin_registry.load_plugins(tmp_path, strict_mode=False)
        assert plugin_registry.get_command("/help") is None

    def test_non_shadow_command_not_removed(self, tmp_path: Path) -> None:
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "custom_cmd.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/my_custom")
                async def cmd(ctx, args):
                    pass
            """)
        )
        plugin_registry.load_plugins(tmp_path, strict_mode=False)
        assert plugin_registry.get_command("/my_custom") is not None

    def test_shadow_strict_mode_raises_plugin_load_error(self, tmp_path: Path) -> None:
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "shadow_help.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/help")
                async def cmd(ctx, args):
                    pass
            """)
        )
        with pytest.raises(PluginLoadError, match="Command builtin conflicts rejected"):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)

    def test_shadow_strict_mode_message_contains_command_name(
        self, tmp_path: Path
    ) -> None:
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "shadow_help.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/help")
                async def cmd(ctx, args):
                    pass
            """)
        )
        with pytest.raises(PluginLoadError) as exc_info:
            plugin_registry.load_plugins(tmp_path, strict_mode=True)
        assert "/help" in str(exc_info.value)


class TestStrictModeToolConflict:
    def test_strict_mode_tool_conflict_raises(self, tmp_path: Path):
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory"})
        with pytest.raises(PluginLoadError, match="Tool MCP conflicts rejected"):
            plugin_registry.load_plugins(
                tmp_path,
                known_tools=mcp_tools,
                override_policy="reject",
                strict_mode=True,
            )

    def test_strict_mode_tool_conflict_includes_tool_names(self, tmp_path: Path):
        (tmp_path / "conflict1.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        (tmp_path / "conflict2.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("read_file")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory", "read_file"})
        with pytest.raises(PluginLoadError) as exc_info:
            plugin_registry.load_plugins(
                tmp_path,
                known_tools=mcp_tools,
                override_policy="reject",
                strict_mode=True,
            )
        msg = str(exc_info.value)
        assert "list_directory" in msg
        assert "read_file" in msg

    def test_strict_mode_no_conflict_does_not_raise(self, tmp_path: Path):
        (tmp_path / "safe_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("my_safe_tool")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory"})
        result = plugin_registry.load_plugins(
            tmp_path,
            known_tools=mcp_tools,
            override_policy="reject",
            strict_mode=True,
        )
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("my_safe_tool") is not None

    def test_strict_mode_allows_conflict_with_allow_override(self, tmp_path: Path):
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory"})
        result = plugin_registry.load_plugins(
            tmp_path,
            known_tools=mcp_tools,
            override_policy="allow",
            strict_mode=True,
        )
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("list_directory") is not None

    def test_strict_mode_combined_import_and_conflict_errors(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("raise RuntimeError('import_fail')")
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        mcp_tools = frozenset({"list_directory"})
        with pytest.raises(PluginLoadError) as exc_info:
            plugin_registry.load_plugins(
                tmp_path,
                known_tools=mcp_tools,
                override_policy="reject",
                strict_mode=True,
            )
        msg = str(exc_info.value)
        assert "import_fail" in msg
        assert "Tool MCP conflicts rejected" in msg

    def test_strict_mode_tool_conflict_does_not_raise_without_known_tools(
        self, tmp_path: Path
    ):
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        result = plugin_registry.load_plugins(
            tmp_path,
            known_tools=frozenset(),
            override_policy="reject",
            strict_mode=True,
        )
        assert result.loaded_count == 1
        assert plugin_registry.get_tool("list_directory") is not None


# ── Structured load result regression tests ────────────────────────────────────


class TestStructuredLoadResultRegression:
    """Regression tests for PluginLoadResult structured return value."""

    def test_missing_dir_returns_empty_result(self, tmp_path: Path):
        result = plugin_registry.load_plugins(tmp_path / "nonexistent")
        assert result.loaded_count == 0
        assert result.failed == ()
        assert result.tool_conflicts_shadowed == 0
        assert result.tool_conflicts_allowed == 0
        assert result.command_shadows_rejected == 0

    def test_syntax_error_plugin_in_failed(self, tmp_path: Path):
        (tmp_path / "bad.py").write_text("def f(\n")
        result = plugin_registry.load_plugins(tmp_path)
        assert result.loaded_count == 0
        assert len(result.failed) == 1
        assert result.failed[0].path == "bad.py"
        assert "SyntaxError" in result.failed[0].error

    def test_reject_policy_increments_conflict_counters(self, tmp_path: Path):
        (tmp_path / "conflict_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("list_directory")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        result = plugin_registry.load_plugins(
            tmp_path,
            known_tools=frozenset(["list_directory"]),
            override_policy="reject",
        )
        assert result.loaded_count == 1
        assert result.tool_conflicts_shadowed > 0
        assert result.tool_conflicts_allowed == 0

    def test_command_shadow_count_reported(self, tmp_path: Path):
        plugin_registry.register_builtin_commands(frozenset(["/help"]))
        (tmp_path / "shadow_plugin.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/help")
                def cmd():
                    pass
            """)
        )
        result = plugin_registry.load_plugins(tmp_path)
        assert result.command_shadows_rejected > 0

    def test_get_last_load_result_returns_most_recent(self, tmp_path: Path):
        (tmp_path / "plugin_a.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("get_weather")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        result1 = plugin_registry.load_plugins(tmp_path)
        assert plugin_registry.get_last_load_result() is result1

        (tmp_path / "plugin_b.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_tool

                @register_tool("get_weather")
                async def t(args) -> tuple[str, bool]:
                    return "", False
            """)
        )
        result2 = plugin_registry.load_plugins(tmp_path)
        assert plugin_registry.get_last_load_result() is result2
        assert result1 is not result2
