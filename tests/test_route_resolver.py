"""tests/test_route_resolver.py
Unit tests for shared.route_resolver.ToolRouteResolver.
"""

import logging
from unittest.mock import MagicMock

import pytest
from shared.mcp_config import McpServerConfig, StartupMode
from shared.route_resolver import ToolRouteResolver


def _http(key: str, url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], startup_mode=StartupMode.PERSISTENT)


def _stdio(key: str, tool_names: list[str] | None = None) -> McpServerConfig:
    cfg = McpServerConfig("stdio", "", ["python", "s.py"], startup_mode=StartupMode.PERSISTENT)
    if tool_names:
        cfg.tool_names = tool_names
    return cfg


class TestRegistryRouting:
    """All existing tool names resolve correctly via registry (tool_names=[])."""

    def setup_method(self) -> None:
        configs = {
            "file_read": _http("file_read"),
            "file_write": _http("file_write"),
            "file_delete": _http("file_delete"),
            "shell": _http("shell"),
            "web_search": _http("web_search"),
            "github": _http("github"),
            "rag_pipeline": _http("rag_pipeline"),
            "cicd": _http("cicd"),
            "sqlite": _http("sqlite"),
        }
        self.resolver = ToolRouteResolver(configs)

    def test_read_tools(self) -> None:
        for name in [
            "list_directory",
            "list_directory_with_sizes",
            "directory_tree",
            "read_text_file",
            "read_media_file",
            "read_multiple_files",
            "search_files",
            "grep_files",
            "get_file_info",
        ]:
            assert self.resolver.resolve(name) == "file_read", name

    def test_write_tools(self) -> None:
        for name in ["write_file", "edit_file", "create_directory", "move_file"]:
            assert self.resolver.resolve(name) == "file_write", name

    def test_delete_tools(self) -> None:
        for name in ["delete_file", "delete_directory"]:
            assert self.resolver.resolve(name) == "file_delete", name

    def test_shell_run(self) -> None:
        assert self.resolver.resolve("shell_run") == "shell"

    def test_search_web(self) -> None:
        assert self.resolver.resolve("search_web") == "web_search"

    def test_github_tools(self) -> None:
        for name in ["github_search_repositories", "github_get_file_contents"]:
            assert self.resolver.resolve(name) == "github", name

    def test_rag_tools(self) -> None:
        for name in ["rag_run_pipeline", "rag_debug_pipeline"]:
            assert self.resolver.resolve(name) == "rag_pipeline", name

    def test_cicd_tools(self) -> None:
        for name in [
            "trigger_workflow",
            "get_workflow_runs",
            "get_workflow_status",
            "get_workflow_logs",
        ]:
            assert self.resolver.resolve(name) == "cicd", name

    def test_sqlite_tools(self) -> None:
        for name in ["query_sqlite"]:
            assert self.resolver.resolve(name) == "sqlite", name

    def test_unknown_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown tool"):
            self.resolver.resolve("totally_unknown")


class TestConfigDrivenRouting:
    """Config tool_names is NOT a routing input — only drift validation metadata."""

    def test_config_does_not_override_registry(self) -> None:
        configs = {
            "my_server": _stdio("my_server", tool_names=["search_web"]),
            "web_search": _http("web_search"),
        }
        resolver = ToolRouteResolver(configs)
        # registry has search_web → web_search; config-driven is lower priority
        assert resolver.resolve("search_web") == "web_search"

    def test_config_only_tools_do_not_route(self) -> None:
        """Tools listed only in config tool_names do not route — they must be in ToolRegistry."""
        configs = {
            "custom": _stdio("custom", tool_names=["custom_tool"]),
            "file_read": _http("file_read"),
        }
        resolver = ToolRouteResolver(configs)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("custom_tool")
        assert resolver.resolve("read_text_file") == "file_read"

    def test_empty_server_configs(self) -> None:
        resolver = ToolRouteResolver({})
        assert resolver.resolve("read_text_file") == "file_read"

    def test_unknown_tool_with_partial_config_raises(self) -> None:
        configs = {
            "my_server": _stdio("my_server", tool_names=["my_tool"]),
        }
        resolver = ToolRouteResolver(configs)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("totally_unknown")


class TestWarnOnFallback:
    def test_registry_lookup_no_fallback_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        resolver = ToolRouteResolver({}, warn_on_fallback=True)
        with caplog.at_level(logging.WARNING, logger="shared.route_resolver"):
            resolver.resolve("search_web")
        assert "static fallback" not in caplog.text

    def test_silent_by_default_no_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        resolver = ToolRouteResolver({})
        with caplog.at_level(logging.WARNING, logger="shared.route_resolver"):
            resolver.resolve("search_web")
        assert "static fallback" not in caplog.text


class TestStartupModeValidation:
    def test_startup_mode_empty_string_raises(self) -> None:
        """Empty string for startup_mode should raise ValueError."""
        with pytest.raises(ValueError):
            McpServerConfig(
                transport="http", url="http://127.0.0.1:8000", cmd=[], startup_mode=""
            )

    def test_startup_mode_invalid_value_raises(self) -> None:
        """Invalid startup_mode value should raise ValueError."""
        with pytest.raises(ValueError):
            McpServerConfig(
                transport="http",
                url="http://127.0.0.1:8000",
                cmd=[],
                startup_mode="invalid",
            )

    def test_startup_mode_persistent_is_valid(self) -> None:
        """StartupMode.PERSISTENT is valid for both transports."""
        http_cfg = McpServerConfig(
            transport="http",
            url="http://127.0.0.1:8000",
            cmd=[],
            startup_mode=StartupMode.PERSISTENT,
        )
        assert http_cfg.startup_mode == StartupMode.PERSISTENT

        stdio_cfg = McpServerConfig(
            transport="stdio",
            url="",
            cmd=["python", "s.py"],
            startup_mode=StartupMode.PERSISTENT,
        )
        assert stdio_cfg.startup_mode == StartupMode.PERSISTENT

    def test_startup_mode_subprocess_only_valid_for_http(self) -> None:
        """StartupMode.SUBPROCESS is only valid for transport='http'."""
        McpServerConfig(
            transport="http",
            url="http://127.0.0.1:8000",
            cmd=[],
            startup_mode=StartupMode.SUBPROCESS,
        )

    def test_startup_mode_subprocess_invalid_for_stdio(self) -> None:
        """StartupMode.SUBPROCESS raises ValueError for transport='stdio'."""
        with pytest.raises(
            ValueError,
            match="startup_mode='subprocess' is only valid for transport='http'",
        ):
            McpServerConfig(
                transport="stdio",
                url="",
                cmd=["python", "s.py"],
                startup_mode=StartupMode.SUBPROCESS,
            )


class TestValidateRoutingDrift:
    def test_no_drift_when_config_matches_registry(self) -> None:
        """validate_routing_against_config returns {} when config tool_names are in the registry."""
        from shared.tool_registry import (
            ToolDefinition,
            ToolRegistry,
            validate_routing_against_config,
        )

        registry = ToolRegistry()
        registry.register(ToolDefinition(name="read_text_file", server_key="file_read"))
        registry.register(ToolDefinition(name="list_directory", server_key="file_read"))

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = ["read_text_file", "list_directory"]
        server_configs = {"file_read": cfg}

        result = validate_routing_against_config(
            registry=registry, server_configs=server_configs
        )
        assert result == {}

    def test_drift_detected_when_config_has_unregistered_tool(self) -> None:
        """validate_routing_against_config returns mismatch when config lists a tool not in registry."""
        from shared.tool_registry import (
            ToolDefinition,
            ToolRegistry,
            validate_routing_against_config,
        )

        registry = ToolRegistry()
        registry.register(ToolDefinition(name="read_text_file", server_key="file_read"))

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = ["read_text_file", "missing_tool"]
        server_configs = {"file_read": cfg}

        result = validate_routing_against_config(
            registry=registry, server_configs=server_configs
        )
        assert "file_read" in result
        assert any("missing_tool" in msg for msg in result["file_read"])

    def test_no_drift_when_config_tool_names_empty(self) -> None:
        """validate_routing_against_config skips servers with empty tool_names."""
        from shared.tool_registry import validate_routing_against_config

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = []
        server_configs = {"some_server": cfg}

        result = validate_routing_against_config(server_configs=server_configs)
        assert result == {}


class TestRegistryWithoutConfig:
    """Prove routing works via registry (priority 2) without config tool_names."""

    def _make_configs(self) -> dict[str, McpServerConfig]:
        return {
            "file_read": _http("file_read"),
            "file_write": _http("file_write"),
            "file_delete": _http("file_delete"),
            "shell": _http("shell"),
            "web_search": _http("web_search"),
            "github": _http("github"),
            "rag_pipeline": _http("rag_pipeline"),
            "cicd": _http("cicd"),
            "sqlite": _http("sqlite"),
            "mdq": _http("mdq"),
            "git": _http("git"),
        }

    def test_registry_routes_without_config_tool_names(self) -> None:
        """Known tools resolve correctly when all server configs have empty tool_names."""
        configs = self._make_configs()
        resolver = ToolRouteResolver(configs)
        assert resolver.resolve("read_text_file") == "file_read"
        assert resolver.resolve("write_file") == "file_write"
        assert resolver.resolve("shell_run") == "shell"

    def test_registry_routes_all_tool_constants_tools(self) -> None:
        """Every tool from get_all_mcp_tool_names() resolves without config tool_names."""
        from shared.tool_constants import get_all_mcp_tool_names

        configs = self._make_configs()
        resolver = ToolRouteResolver(configs)
        for tool_name in get_all_mcp_tool_names():
            server_key = resolver.resolve(tool_name)
            assert server_key, f"tool {tool_name!r} resolved to empty string"

    def test_strict_mode_error_message_points_to_tool_registry(self) -> None:
        """strict_mode ValueError for unknown tool mentions ToolRegistry, not mcp_servers config."""
        configs = self._make_configs()
        resolver = ToolRouteResolver(configs, strict_mode=True)
        with pytest.raises(ValueError, match="ToolRegistry"):
            resolver.resolve("no_such_tool_xyz")
