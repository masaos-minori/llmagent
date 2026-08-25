"""tests/test_route_resolver.py
Unit tests for shared.route_resolver.ToolRouteResolver.
"""

import logging

import pytest
from shared.route_resolver import ToolRouteResolver, build_discovery_map
from shared.runtime_tool import build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry


def _runtime_registry_for(tool_to_server: dict[str, str]) -> RuntimeToolRegistry:
    """Build a RuntimeToolRegistry covering the given {tool_name: server_key} pairs."""
    tools = {
        name: build_runtime_tool(
            name=name,
            server_key=server_key,
            status="active",
            is_write=False,
            requires_serial=False,
            resource_scope_kind="",
            resource_scope_keys=(),
            agent_safety_tier="READ_ONLY",
            enabled_for_llm=True,
            capabilities=(),
        )
        for name, server_key in tool_to_server.items()
    }
    return RuntimeToolRegistry(tools=tools)


class TestRegistryRouting:
    """All known tool names resolve correctly via an explicit RuntimeToolRegistry."""

    def setup_method(self) -> None:
        runtime_registry = _runtime_registry_for(
            {
                "list_directory": "file_read",
                "list_directory_with_sizes": "file_read",
                "directory_tree": "file_read",
                "read_text_file": "file_read",
                "read_media_file": "file_read",
                "read_multiple_files": "file_read",
                "search_files": "file_read",
                "grep_files": "file_read",
                "get_file_info": "file_read",
                "write_file": "file_write",
                "edit_file": "file_write",
                "create_directory": "file_write",
                "move_file": "file_write",
                "delete_file": "file_delete",
                "delete_directory": "file_delete",
                "shell_run": "shell",
                "search_web": "web_search",
                "github_search_repositories": "github",
                "github_get_file_contents": "github",
                "rag_run_pipeline": "rag_pipeline",
                "rag_debug_pipeline": "rag_pipeline",
                "trigger_workflow": "cicd",
                "get_workflow_runs": "cicd",
                "get_workflow_status": "cicd",
                "get_workflow_logs": "cicd",
            }
        )
        self.resolver = ToolRouteResolver(runtime_registry=runtime_registry)

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


class TestConfigToolNamesNotRoutingInput:
    """Config tool_names is NOT a routing input — ToolRouteResolver has no server_configs
    parameter at all, so RuntimeToolRegistry is the only possible routing source."""

    def test_registry_resolves_without_any_config(self) -> None:
        runtime_registry = _runtime_registry_for({"search_web": "web_search"})
        resolver = ToolRouteResolver(runtime_registry=runtime_registry)
        assert resolver.resolve("search_web") == "web_search"

    def test_tool_absent_from_registry_does_not_route(self) -> None:
        """A tool absent from RuntimeToolRegistry does not route, regardless of naming."""
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(runtime_registry=runtime_registry)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("custom_tool")
        assert resolver.resolve("read_text_file") == "file_read"

    def test_no_runtime_registry_raises_for_any_tool(self) -> None:
        resolver = ToolRouteResolver()
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("totally_unknown")


class TestRegistryWithoutConfig:
    """Prove routing works via an explicit RuntimeToolRegistry without config tool_names."""

    def test_registry_routes_without_config_tool_names(self) -> None:
        """Known tools resolve correctly given only a RuntimeToolRegistry."""
        runtime_registry = _runtime_registry_for(
            {
                "read_text_file": "file_read",
                "write_file": "file_write",
                "shell_run": "shell",
            }
        )
        resolver = ToolRouteResolver(runtime_registry=runtime_registry)
        assert resolver.resolve("read_text_file") == "file_read"
        assert resolver.resolve("write_file") == "file_write"
        assert resolver.resolve("shell_run") == "shell"

    def test_registry_routes_all_tool_constants_tools(self) -> None:
        """Every tool from get_all_mcp_tool_names() resolves given a covering RuntimeToolRegistry."""
        from shared.tool_constants import get_all_mcp_tool_names

        all_tools = get_all_mcp_tool_names()
        runtime_registry = _runtime_registry_for(
            {tool_name: "some_server" for tool_name in all_tools}
        )
        resolver = ToolRouteResolver(runtime_registry=runtime_registry)
        for tool_name in all_tools:
            server_key = resolver.resolve(tool_name)
            assert server_key, f"tool {tool_name!r} resolved to empty string"

    def test_strict_mode_error_message_mentions_runtime_registry(self) -> None:
        """strict_mode ValueError for unknown tool mentions RuntimeToolRegistry explicitly."""
        resolver = ToolRouteResolver(strict_mode=True)
        with pytest.raises(ValueError, match="RuntimeToolRegistry"):
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
                    {"name": None, "server_key": "file_read"},  # type: ignore[typeddict-item]  # deliberately malformed input — exercises the defensive skip path
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


class TestRoutingSourceIsolation:
    def test_config_tool_names_do_not_affect_routing(self) -> None:
        """ToolRouteResolver has no server_configs parameter — config tool_names cannot
        be passed to it at all, so RuntimeToolRegistry is necessarily the sole source."""
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(runtime_registry=runtime_registry)
        assert resolver.resolve("read_text_file") == "file_read"

    def test_constants_not_used_directly_by_resolver(self) -> None:
        """ToolRouteResolver does not fall back to tool_constants frozensets."""
        resolver = ToolRouteResolver()
        with pytest.raises(ValueError, match="[Uu]nknown tool"):
            resolver.resolve("nonexistent_tool_xyz")


class TestDuplicateToolRegistration:
    """Tests confirming ToolRegistry.register() rejects duplicate registrations."""

    def test_duplicate_registration_raises_value_error(self) -> None:
        """Registering the same tool name to two different servers raises ValueError."""
        from shared.tool_registry import ToolDefinition, ToolRegistry

        registry = ToolRegistry()
        registry.register(ToolDefinition(name="read_text_file", server_key="server_a"))
        with pytest.raises(
            ValueError,
            match=r"already registered to server 'server_a'; cannot reassign to 'server_b'",
        ):
            registry.register(
                ToolDefinition(name="read_text_file", server_key="server_b")
            )
