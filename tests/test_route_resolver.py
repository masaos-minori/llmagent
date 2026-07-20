"""tests/test_route_resolver.py
Unit tests for shared.route_resolver.ToolRouteResolver.
"""

import logging

import pytest
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.route_resolver import ToolRouteResolver, build_discovery_map
from shared.runtime_tool import build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry


def _http(key: str, url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(TransportType.HTTP, url, startup_mode=StartupMode.PERSISTENT)


def _runtime_registry_for(tool_to_server: dict[str, str]) -> RuntimeToolRegistry:
    """Build a RuntimeToolRegistry covering the given {tool_name: server_key} pairs."""
    tools = {
        name: build_runtime_tool(
            name=name,
            server_key=server_key,
            status="active",
            is_write=False,
            requires_serial=False,
            resource_scope="",
            agent_safety_tier="READ_ONLY",
            requires_approval=False,
            enabled_for_llm=True,
            capabilities=(),
        )
        for name, server_key in tool_to_server.items()
    }
    return RuntimeToolRegistry(tools=tools)


class TestRegistryRouting:
    """All known tool names resolve correctly via an explicit RuntimeToolRegistry."""

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
        self.resolver = ToolRouteResolver(configs, runtime_registry=runtime_registry)

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
        runtime_registry = _runtime_registry_for({"search_web": "web_search"})
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_registry)
        # RuntimeToolRegistry has search_web → web_search; config-driven tool_names is ignored.
        assert resolver.resolve("search_web") == "web_search"

    def test_config_only_tools_do_not_route(self) -> None:
        """Tools listed only in config tool_names do not route — they must be in RuntimeToolRegistry."""
        custom = _http("custom")
        custom.tool_names = ["custom_tool"]
        configs = {
            "custom": custom,
            "file_read": _http("file_read"),
        }
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_registry)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("custom_tool")
        assert resolver.resolve("read_text_file") == "file_read"

    def test_empty_server_configs(self) -> None:
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver({}, runtime_registry=runtime_registry)
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
    """Prove routing works via an explicit RuntimeToolRegistry without config tool_names."""

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
        runtime_registry = _runtime_registry_for(
            {
                "read_text_file": "file_read",
                "write_file": "file_write",
                "shell_run": "shell",
            }
        )
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_registry)
        assert resolver.resolve("read_text_file") == "file_read"
        assert resolver.resolve("write_file") == "file_write"
        assert resolver.resolve("shell_run") == "shell"

    def test_registry_routes_all_tool_constants_tools(self) -> None:
        """Every tool from get_all_mcp_tool_names() resolves given a covering RuntimeToolRegistry."""
        from shared.tool_constants import get_all_mcp_tool_names

        configs = self._make_configs()
        all_tools = get_all_mcp_tool_names()
        runtime_registry = _runtime_registry_for(
            {tool_name: "some_server" for tool_name in all_tools}
        )
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_registry)
        for tool_name in all_tools:
            server_key = resolver.resolve(tool_name)
            assert server_key, f"tool {tool_name!r} resolved to empty string"

    def test_strict_mode_error_message_mentions_runtime_registry(self) -> None:
        """strict_mode ValueError for unknown tool mentions RuntimeToolRegistry explicitly."""
        configs = self._make_configs()
        resolver = ToolRouteResolver(configs, strict_mode=True)
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
    """Tests proving discovery_map does NOT affect routing.

    The discovery_map parameter is retained for backward compatibility with
    integration tests that route synthetic tool names, but it has no effect
    on routing results — RuntimeToolRegistry is the sole routing authority.
    """

    def _make_configs(self) -> dict[str, McpServerConfig]:
        return {
            "file_read": _http("file_read"),
            "web_search": _http("web_search"),
        }

    def test_discovery_map_does_not_override_registry(self) -> None:
        """RuntimeToolRegistry routing wins even when discovery_map maps the tool elsewhere."""
        configs = self._make_configs()
        discovery_map = {"read_text_file": "custom_server"}
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(
            configs, discovery_map=discovery_map, runtime_registry=runtime_registry
        )
        # RuntimeToolRegistry maps read_text_file → file_read; discovery_map must not override it.
        assert resolver.resolve("read_text_file") == "file_read"

    def test_registry_used_when_tool_not_in_discovery_map(self) -> None:
        """RuntimeToolRegistry is used when tool is not in discovery map."""
        configs = self._make_configs()
        discovery_map = {"custom_tool": "custom_server"}
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(
            configs, discovery_map=discovery_map, runtime_registry=runtime_registry
        )
        assert resolver.resolve("read_text_file") == "file_read"

    def test_empty_discovery_map_does_not_affect_registry_routing(self) -> None:
        """Empty discovery map does not affect RuntimeToolRegistry routing."""
        configs = self._make_configs()
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(
            configs, discovery_map={}, runtime_registry=runtime_registry
        )
        assert resolver.resolve("read_text_file") == "file_read"

    def test_unknown_tool_raises_regardless_of_discovery_map(self) -> None:
        """Unknown tool raises ValueError even with a non-empty discovery map."""
        configs = self._make_configs()
        discovery_map = {"custom_tool": "custom_server"}
        resolver = ToolRouteResolver(configs, discovery_map=discovery_map)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("no_such_tool_xyz")

    def test_discovery_map_none_does_not_affect_registry_routing(self) -> None:
        """None discovery map (default) does not affect RuntimeToolRegistry routing."""
        configs = self._make_configs()
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(
            configs, discovery_map=None, runtime_registry=runtime_registry
        )
        assert resolver.resolve("read_text_file") == "file_read"


class TestLogRoutingCoverage:
    """Tests for ToolRouteResolver._log_routing_coverage() RuntimeToolRegistry classification.

    "Mapped" must mean resolvable via RuntimeToolRegistry (the same authority resolve() uses),
    not merely present in discovery_map — discovery_map is validation-only metadata.
    """

    def _make_configs(self) -> dict[str, McpServerConfig]:
        return {
            "file_read": _http("file_read"),
        }

    def test_discovery_map_only_tool_is_unmapped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A tool present only in discovery_map (absent from RuntimeToolRegistry) is UNMAPPED.

        This is the core regression check: resolve() would raise ValueError for this
        tool, so _log_routing_coverage() must not count it as mapped just because it
        appears in discovery_map.
        """
        configs = self._make_configs()
        discovery_map = {"discovery_only_tool": "some_server"}
        known_tools = frozenset({"discovery_only_tool", "read_text_file"})
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        with caplog.at_level(logging.WARNING):
            ToolRouteResolver(
                configs,
                discovery_map=discovery_map,
                known_tools=known_tools,
                runtime_registry=runtime_registry,
            )
        warnings = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any(
            "1/2 tools mapped" in msg and "discovery_only_tool" in msg
            for msg in warnings
        )

    def test_registry_mapped_tool_is_mapped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A tool resolvable via RuntimeToolRegistry is MAPPED, regardless of discovery_map."""
        configs = self._make_configs()
        known_tools = frozenset({"read_text_file"})
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        with caplog.at_level(logging.INFO):
            ToolRouteResolver(
                configs, known_tools=known_tools, runtime_registry=runtime_registry
            )
        infos = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert any("1/1 tools mapped" in msg for msg in infos)

    def test_all_unmapped_when_registry_and_discovery_map_both_miss(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Tool absent from RuntimeToolRegistry and discovery_map is UNMAPPED."""
        configs = self._make_configs()
        known_tools = frozenset({"totally_unknown_tool"})
        with caplog.at_level(logging.WARNING):
            ToolRouteResolver(configs, known_tools=known_tools)
        warnings = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any(
            "0/1 tools mapped" in msg and "totally_unknown_tool" in msg
            for msg in warnings
        )


class TestRoutingSourceIsolation:
    def test_config_tool_names_do_not_affect_routing(self) -> None:
        """Config tool_names is metadata only — ToolRouteResolver.resolve() ignores it."""
        from shared.mcp_config import McpServerConfig, TransportType

        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost",
            tool_names=["read_text_file"],  # config metadata — not a routing input
        )
        runtime_registry = _runtime_registry_for({"read_text_file": "file_read"})
        resolver = ToolRouteResolver(
            {"file_read": cfg}, runtime_registry=runtime_registry
        )
        assert resolver.resolve("read_text_file") == "file_read"

    def test_constants_not_used_directly_by_resolver(self) -> None:
        """ToolRouteResolver does not fall back to tool_constants frozensets."""
        resolver = ToolRouteResolver({})
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
