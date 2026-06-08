"""tests/test_route_resolver.py
Unit tests for shared.route_resolver.ToolRouteResolver.
"""

import logging

import pytest
from shared.mcp_config import McpServerConfig
from shared.route_resolver import ToolRouteResolver


def _http(key: str, url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], "")


def _stdio(key: str, tool_names: list[str] | None = None) -> McpServerConfig:
    cfg = McpServerConfig("stdio", "", ["python", "s.py"], "")
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

    def test_unknown_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown tool"):
            self.resolver.resolve("totally_unknown")


class TestConfigDrivenRouting:
    """tool_names in config overrides static fallback for those tools."""

    def test_config_map_takes_priority(self) -> None:
        configs = {
            "my_server": _stdio("my_server", tool_names=["search_web"]),
            "web_search": _http("web_search"),
        }
        resolver = ToolRouteResolver(configs)
        # search_web is explicitly mapped to my_server, not web_search
        assert resolver.resolve("search_web") == "my_server"

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
    def test_fallback_emits_warning_when_enabled(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        resolver = ToolRouteResolver({}, warn_on_fallback=True)
        with caplog.at_level(logging.WARNING, logger="shared.route_resolver"):
            resolver.resolve("search_web")
        assert "static fallback" in caplog.text

    def test_fallback_silent_by_default(self, caplog: pytest.LogCaptureFixture) -> None:
        resolver = ToolRouteResolver({})
        with caplog.at_level(logging.WARNING, logger="shared.route_resolver"):
            resolver.resolve("search_web")
        assert "static fallback" not in caplog.text
