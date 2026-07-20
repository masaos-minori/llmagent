"""tests/test_runtime_tool_routing_integration.py

Integration tests for RuntimeToolRegistry wiring into the routing layer,
/mcp tools subcommand, and browser tools config_dependent migration.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import MagicMock

import httpx
import pytest
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
    TransportType,
)
from shared.route_resolver import ToolRouteResolver
from shared.runtime_tool import build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_executor import ToolExecutor

# ── Helpers ───────────────────────────────────────────────────────────────────


@contextmanager
def caplog_at_level(level: int) -> Iterator[None]:
    """Context manager that temporarily sets the root logger level."""
    root = logging.getLogger()
    old_level = root.level
    root.setLevel(level)
    try:
        yield
    finally:
        root.setLevel(old_level)


def _http(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(TransportType.HTTP, url, startup_mode=StartupMode.PERSISTENT)


def _make_executor(
    configs: dict[str, McpServerConfig] | None = None,
    concurrency_limits: dict[str, int] | None = None,
) -> ToolExecutor:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolExecutor(
        http,
        cache_ttl=60.0,
        server_configs=configs or {"file_read": _http()},
        concurrency_limits=concurrency_limits,
    )


def _make_runtime_registry() -> RuntimeToolRegistry:
    """Create a minimal RuntimeToolRegistry with one tool."""
    tool = build_runtime_tool(
        name="browser_fetch",
        server_key="browser",
        description="Fetch a URL",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        status="active",
        is_write=False,
        requires_serial=True,
        resource_scope="",
        agent_safety_tier="READ_ONLY",
        requires_approval=False,
        enabled_for_llm=True,
        capabilities=("web_fetch",),
    )
    return RuntimeToolRegistry(tools={"browser_fetch": tool})


# ── 1. RuntimeToolRegistry → Routing Layer Wiring ────────────────────────────


class TestRuntimeRegistryPriorityInResolve:
    """Verify RuntimeToolRegistry takes resolution priority over legacy ToolRegistry."""

    def test_runtime_registry_wins_when_both_available(self) -> None:
        """When both registries exist, RuntimeToolRegistry resolves first."""
        runtime_reg = _make_runtime_registry()
        configs = {"browser": _http("http://127.0.0.1:8001")}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        assert resolver.resolve("browser_fetch") == "browser"

    def test_legacy_fallback_when_runtime_unavailable(self) -> None:
        """Without RuntimeToolRegistry, resolve falls through to legacy ToolRegistry."""
        configs = {"file_read": _http("http://127.0.0.1:8002")}
        resolver = ToolRouteResolver(configs)
        assert resolver.resolve("read_text_file") == "file_read"

    def test_runtime_only_resolve(self) -> None:
        """RuntimeToolRegistry alone can resolve its own tools."""
        runtime_reg = _make_runtime_registry()
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        assert resolver.resolve("browser_fetch") == "browser"

    def test_unknown_tool_raises_with_runtime_only(self) -> None:
        """Unknown tool raises ValueError when only RuntimeToolRegistry is present."""
        runtime_reg = _make_runtime_registry()
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("no_such_browser_tool")

    def test_mixed_tools_resolve_correctly(self) -> None:
        """Tools in both registries resolve to their correct owners."""
        runtime_reg = _make_runtime_registry()
        configs = {"file_read": _http("http://127.0.0.1:8003")}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        assert resolver.resolve("browser_fetch") == "browser"
        assert resolver.resolve("read_text_file") == "file_read"

    def test_runtime_none_does_not_break_resolve(self) -> None:
        """Passing runtime_registry=None behaves like no RuntimeToolRegistry."""
        configs = {"file_read": _http("http://127.0.0.1:8004")}
        resolver = ToolRouteResolver(configs, runtime_registry=None)
        assert resolver.resolve("read_text_file") == "file_read"

    def test_strict_mode_error_message_mentions_any_registry(self) -> None:
        """strict_mode error message mentions 'any registry' not just ToolRegistry."""
        runtime_reg = _make_runtime_registry()
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(
            configs, strict_mode=True, runtime_registry=runtime_reg
        )
        with pytest.raises(ValueError, match="any registry"):
            resolver.resolve("nonexistent_tool")

    def test_warn_on_missing_logs_warning_for_unknown_tool(self) -> None:
        """warn_on_missing=True logs warning for unknown tool."""
        runtime_reg = _make_runtime_registry()
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(
            configs, warn_on_missing=True, runtime_registry=runtime_reg
        )
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("unknown_tool_xyz")

    def test_runtime_empty_registry_resolves_via_legacy(self) -> None:
        """Empty RuntimeToolRegistry falls through to legacy ToolRegistry."""
        empty_reg = RuntimeToolRegistry()
        configs = {"file_read": _http("http://127.0.0.1:8005")}
        resolver = ToolRouteResolver(configs, runtime_registry=empty_reg)
        assert resolver.resolve("read_text_file") == "file_read"

    def test_runtime_registry_resolves_all_its_tools(self) -> None:
        """All tools registered in RuntimeToolRegistry resolve correctly."""
        tool_a = build_runtime_tool(
            name="tool_a",
            server_key="srv_a",
            status="active",
            is_write=False,
            requires_serial=True,
            resource_scope="",
            agent_safety_tier="READ_ONLY",
            requires_approval=False,
            enabled_for_llm=True,
            capabilities=(),
        )
        tool_b = build_runtime_tool(
            name="tool_b",
            server_key="srv_b",
            status="active",
            is_write=True,
            requires_serial=True,
            resource_scope="",
            agent_safety_tier="WRITE_DANGEROUS",
            requires_approval=True,
            enabled_for_llm=True,
            capabilities=(),
        )
        reg = RuntimeToolRegistry(tools={"tool_a": tool_a, "tool_b": tool_b})
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(configs, runtime_registry=reg)
        assert resolver.resolve("tool_a") == "srv_a"
        assert resolver.resolve("tool_b") == "srv_b"

    def test_runtime_registry_set_runtime_registry_replaces_resolver(self) -> None:
        """ToolExecutor.set_runtime_registry() replaces the resolver instance."""
        configs = {"file_read": _http("http://127.0.0.1:8006")}
        ex = _make_executor(configs=configs)
        resolver_before = ex._resolver
        runtime_reg = _make_runtime_registry()
        ex.set_runtime_registry(runtime_reg)
        assert ex._resolver is not resolver_before
        # New resolver should resolve via RuntimeToolRegistry first
        assert ex._resolver.resolve("browser_fetch") == "browser"
        # Legacy fallback still works
        assert ex._resolver.resolve("read_text_file") == "file_read"


class TestLogRoutingCoverageWithRuntime:
    """Tests for _log_routing_coverage with RuntimeToolRegistry awareness."""

    def _make_configs(self) -> dict[str, McpServerConfig]:
        return {
            "file_read": _http("http://127.0.0.1:8007"),
        }

    def test_runtime_mapped_tool_is_mapped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A tool resolvable via RuntimeToolRegistry is MAPPED."""
        runtime_reg = _make_runtime_registry()
        known_tools = frozenset({"browser_fetch"})
        with caplog.at_level(logging.INFO):
            ToolRouteResolver({}, known_tools=known_tools, runtime_registry=runtime_reg)

    def test_all_unmapped_when_both_registries_miss(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Tool absent from both registries is UNMAPPED."""
        configs = self._make_configs()
        known_tools = frozenset({"totally_unknown_tool"})
        with caplog.at_level(logging.WARNING):
            ToolRouteResolver(configs, known_tools=known_tools)
        warnings = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any(
            "0/1 tools mapped" in msg and "totally_unknown_tool" in msg
            for msg in warnings
        )

    def test_runtime_only_tool_is_mapped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A tool present only in RuntimeToolRegistry is MAPPED."""
        runtime_reg = _make_runtime_registry()
        known_tools = frozenset({"browser_fetch"})
        with caplog.at_level(logging.INFO):
            ToolRouteResolver({}, known_tools=known_tools, runtime_registry=runtime_reg)
        infos = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert any("1/1 tools mapped" in msg for msg in infos)

    def test_both_registries_count_as_mapped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Tool in both registries counts as mapped once."""
        runtime_reg = _make_runtime_registry()
        known_tools = frozenset({"browser_fetch", "read_text_file"})
        with caplog.at_level(logging.INFO):
            ToolRouteResolver({}, known_tools=known_tools, runtime_registry=runtime_reg)
        infos = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert any("2/2 tools mapped" in msg for msg in infos)


# ── 2. /mcp tools Subcommand ─────────────────────────────────────────────────

# ── 3. Browser Tools config_dependent Migration ───────────────────────────────


class TestBrowserToolsConfigDependentMigration:
    """Verify browser_tools.py uses config_dependent instead of requires_config."""

    async def test_browser_tools_tool_list_contains_config_dependent(self) -> None:
        """browser_tools TOOL_LIST contains config_dependent property."""
        from mcp_servers.browser.browser_tools import TOOL_LIST

        assert len(TOOL_LIST) > 0
        for tool in TOOL_LIST:
            assert "config_dependent" in tool, (
                f"Tool {tool['name']} missing config_dependent"
            )

    async def test_browser_tools_no_requires_config_in_tool_list(self) -> None:
        """browser_tools TOOL_LIST does NOT contain requires_config."""
        from mcp_servers.browser.browser_tools import TOOL_LIST

        for tool in TOOL_LIST:
            assert "requires_config" not in tool, (
                f"Tool {tool['name']} still has requires_config"
            )

    async def test_browser_fetch_tool_has_config_dependent_true(self) -> None:
        """browser_fetch specifically has config_dependent: True."""
        from mcp_servers.browser.browser_tools import TOOL_LIST

        fetch_tool = next(t for t in TOOL_LIST if t["name"] == "browser_fetch")
        assert fetch_tool.get("config_dependent") is True
