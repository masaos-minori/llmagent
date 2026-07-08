"""tests/test_route_resolver.py
Unit tests for shared.route_resolver.ToolRouteResolver.
"""

import logging

import pytest
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.route_resolver import ToolRouteResolver, build_discovery_map


def _http(key: str, url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(TransportType.HTTP, url, startup_mode=StartupMode.PERSISTENT)


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

    def test_unknown_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown tool"):
            self.resolver.resolve("totally_unknown")

    def test_query_sqlite_no_longer_routable(self) -> None:
        """sqlite-mcp was removed; query_sqlite must not resolve to any server."""
        with pytest.raises(ValueError, match="Unknown tool"):
            self.resolver.resolve("query_sqlite")


class TestConfigDrivenRouting:
    """Config tool_names is NOT a routing input — only drift validation metadata."""

    def test_config_does_not_override_registry(self) -> None:
        my_server = _http("my_server")
        my_server.tool_names = ["search_web"]
        configs = {
            "my_server": my_server,
            "web_search": _http("web_search"),
        }
        resolver = ToolRouteResolver(configs)
        # registry has search_web → web_search; config-driven is lower priority
        assert resolver.resolve("search_web") == "web_search"

    def test_config_only_tools_do_not_route(self) -> None:
        """Tools listed only in config tool_names do not route — they must be in ToolRegistry."""
        custom = _http("custom")
        custom.tool_names = ["custom_tool"]
        configs = {
            "custom": custom,
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
        my_server = _http("my_server")
        my_server.tool_names = ["my_tool"]
        configs = {
            "my_server": my_server,
        }
        resolver = ToolRouteResolver(configs)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("totally_unknown")


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


class TestBuildDiscoveryMap:
    """Tests for build_discovery_map() function."""

    def test_normal_path(self) -> None:
        """Two servers, each with valid tool dicts."""
        route_map, duplicates = build_discovery_map(
            {
                "file_read": [{"name": "read_file", "server_key": "file_read"}],
                "shell": [{"name": "shell_run", "server_key": "shell"}],
            }
        )
        assert route_map == {"read_file": "file_read", "shell_run": "shell"}
        assert duplicates == {}

    def test_outer_key_used_for_routing(self) -> None:
        """Outer server key is used for routing; inner server_key field is ignored."""
        route_map, _ = build_discovery_map(
            {
                "file_read": [{"name": "read_file"}],
            }
        )
        assert route_map == {"read_file": "file_read"}

    def test_empty_tool_name_skipped(self) -> None:
        """Tool dict with empty or None name is skipped."""
        route_map, duplicates = build_discovery_map(
            {
                "file_read": [
                    {"name": "", "server_key": "file_read"},
                    {"name": None, "server_key": "file_read"},
                ],
            }
        )
        assert route_map == {}
        assert duplicates == {}

    def test_duplicate_tool_first_wins(self) -> None:
        """Same tool name in two servers; first occurrence wins."""
        route_map, duplicates = build_discovery_map(
            {
                "server_a": [{"name": "read_file", "server_key": "server_a"}],
                "server_b": [{"name": "read_file", "server_key": "server_b"}],
            }
        )
        assert route_map == {"read_file": "server_a"}
        assert duplicates == {"read_file": ["server_a", "server_b"]}

    def test_single_server_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Single server with one tool; no duplicate warning logged."""
        with caplog.at_level(logging.WARNING):
            route_map, duplicates = build_discovery_map(
                {
                    "server_a": [{"name": "read_file"}],
                }
            )
        assert route_map == {"read_file": "server_a"}
        assert duplicates == {}
        assert not caplog.records

    def test_duplicate_tool_different_key_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Same tool name, different server keys; warning is logged."""
        with caplog.at_level(logging.WARNING):
            route_map, duplicates = build_discovery_map(
                {
                    "server_a": [{"name": "read_file", "server_key": "server_a"}],
                    "server_b": [{"name": "read_file", "server_key": "server_b"}],
                }
            )
        assert route_map == {"read_file": "server_a"}
        assert duplicates == {"read_file": ["server_a", "server_b"]}
        assert any(
            "read_file" in r.message
            for r in caplog.records
            if r.levelno >= logging.WARNING
        )


class TestDiscoveryMapValidationOnly:
    """Tests proving discovery_map does NOT override registry routing.

    The discovery_map parameter is retained for backward compatibility with
    integration tests that route synthetic tool names, but it has no effect
    on routing results — ToolRegistry is the sole routing authority.
    """

    def _make_configs(self) -> dict[str, McpServerConfig]:
        return {
            "file_read": _http("file_read"),
            "web_search": _http("web_search"),
        }

    def test_discovery_map_does_not_override_registry(self) -> None:
        """Registry routing wins even when discovery_map maps the tool to a different server."""
        configs = self._make_configs()
        discovery_map = {"read_text_file": "custom_server"}
        resolver = ToolRouteResolver(configs, discovery_map=discovery_map)
        # Registry maps read_text_file → file_read; discovery_map must not override it.
        assert resolver.resolve("read_text_file") == "file_read"

    def test_registry_fallback_when_tool_not_in_discovery_map(self) -> None:
        """Registry is used when tool is not in discovery map."""
        configs = self._make_configs()
        discovery_map = {"custom_tool": "custom_server"}
        resolver = ToolRouteResolver(configs, discovery_map=discovery_map)
        assert resolver.resolve("read_text_file") == "file_read"

    def test_empty_discovery_map_falls_through_to_registry(self) -> None:
        """Empty discovery map falls through to registry routing."""
        configs = self._make_configs()
        resolver = ToolRouteResolver(configs, discovery_map={})
        assert resolver.resolve("read_text_file") == "file_read"

    def test_unknown_tool_raises_regardless_of_discovery_map(self) -> None:
        """Unknown tool raises ValueError even with a non-empty discovery map."""
        configs = self._make_configs()
        discovery_map = {"custom_tool": "custom_server"}
        resolver = ToolRouteResolver(configs, discovery_map=discovery_map)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("no_such_tool_xyz")

    def test_discovery_map_none_falls_through_to_registry(self) -> None:
        """None discovery map (default) falls through to registry routing."""
        configs = self._make_configs()
        resolver = ToolRouteResolver(configs, discovery_map=None)
        assert resolver.resolve("read_text_file") == "file_read"


class TestRoutingSourceIsolation:
    def test_config_tool_names_do_not_affect_routing(self) -> None:
        """Config tool_names is metadata only — ToolRouteResolver.resolve() ignores it."""
        from shared.mcp_config import McpServerConfig, TransportType

        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost",
            tool_names=["read_text_file"],  # config metadata — not a routing input
        )
        resolver = ToolRouteResolver({"file_read": cfg})
        assert resolver.resolve("read_text_file") == "file_read"

    def test_constants_not_used_directly_by_resolver(self) -> None:
        """ToolRouteResolver does not fall back to tool_constants frozensets."""
        resolver = ToolRouteResolver({})
        with pytest.raises(ValueError, match="[Uu]nknown tool"):
            resolver.resolve("nonexistent_tool_xyz")
