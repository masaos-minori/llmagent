"""tests/test_route_resolver.py
Unit tests for shared.route_resolver.ToolRouteResolver.
"""

import logging

import pytest
from shared.mcp_config import McpServerConfig, StartupMode
from shared.route_resolver import ToolRouteResolver


def _http(key: str, url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], StartupMode.PERSISTENT)


def _stdio(key: str, tool_names: list[str] | None = None) -> McpServerConfig:
    cfg = McpServerConfig("stdio", "", ["python", "s.py"], StartupMode.PERSISTENT)
    if tool_names:
        cfg.tool_names = tool_names
    return cfg


class TestStaticFallbackRouting:
    """All existing tool names resolve correctly via static fallback (tool_names=[])."""

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

    def test_github_prefix(self) -> None:
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
    """tool_names in config is lower priority than registry (source of truth)."""

    def test_config_does_not_override_registry(self) -> None:
        configs = {
            "my_server": _stdio("my_server", tool_names=["search_web"]),
            "web_search": _http("web_search"),
        }
        resolver = ToolRouteResolver(configs)
        # registry has search_web → web_search; config-driven is lower priority
        assert resolver.resolve("search_web") == "web_search"

    def test_config_map_partial_coverage_falls_back(self) -> None:
        configs = {
            "custom": _stdio("custom", tool_names=["custom_tool"]),
            "file_read": _http("file_read"),
        }
        resolver = ToolRouteResolver(configs)
        assert resolver.resolve("custom_tool") == "custom"
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
            McpServerConfig(transport="http", url="http://127.0.0.1:8000", cmd=[], startup_mode="")

    def test_startup_mode_invalid_value_raises(self) -> None:
        """Invalid startup_mode value should raise ValueError."""
        with pytest.raises(ValueError):
            McpServerConfig(transport="http", url="http://127.0.0.1:8000", cmd=[], startup_mode="invalid")

    def test_startup_mode_persistent_is_valid(self) -> None:
        """StartupMode.PERSISTENT is valid for both transports."""
        http_cfg = McpServerConfig(transport="http", url="http://127.0.0.1:8000", cmd=[], startup_mode=StartupMode.PERSISTENT)
        assert http_cfg.startup_mode == StartupMode.PERSISTENT

        stdio_cfg = McpServerConfig(transport="stdio", url="", cmd=["python", "s.py"], startup_mode=StartupMode.PERSISTENT)
        assert stdio_cfg.startup_mode == StartupMode.PERSISTENT

    def test_startup_mode_subprocess_only_valid_for_http(self) -> None:
        """StartupMode.SUBPROCESS is only valid for transport='http'."""
        McpServerConfig(transport="http", url="http://127.0.0.1:8000", cmd=[], startup_mode=StartupMode.SUBPROCESS)

    def test_startup_mode_subprocess_invalid_for_stdio(self) -> None:
        """StartupMode.SUBPROCESS raises ValueError for transport='stdio'."""
        with pytest.raises(ValueError, match="startup_mode='subprocess' is only valid for transport='http'"):
            McpServerConfig(transport="stdio", url="", cmd=["python", "s.py"], startup_mode=StartupMode.SUBPROCESS)

    def test_startup_mode_string_persistent_coerced(self) -> None:
        """String 'persistent' is coerced to StartupMode.PERSISTENT."""
        cfg = McpServerConfig(transport="http", url="http://127.0.0.1:8000", cmd=[], startup_mode="persistent")
        assert cfg.startup_mode == StartupMode.PERSISTENT

    def test_startup_mode_string_subprocess_coerced(self) -> None:
        """String 'subprocess' is coerced to StartupMode.SUBPROCESS."""
        cfg = McpServerConfig(transport="http", url="http://127.0.0.1:8000", cmd=[], startup_mode="subprocess")
        assert cfg.startup_mode == StartupMode.SUBPROCESS
