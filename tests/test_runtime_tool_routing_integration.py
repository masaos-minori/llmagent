"""tests/test_runtime_tool_routing_integration.py

Integration tests for RuntimeToolRegistry wiring into the routing layer,
/mcp tools subcommand, and web_search_tools.py's browser_fetch entry's
config_dependent migration.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
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


def _make_runtime_registry(
    *, extra: dict[str, str] | None = None
) -> RuntimeToolRegistry:
    """Create a minimal RuntimeToolRegistry with browser_fetch, plus any extra tools.

    `extra` maps additional tool_name -> server_key pairs to register alongside
    browser_fetch, for tests that need more than one routable tool.
    """
    tool = build_runtime_tool(
        name="browser_fetch",
        server_key="web_search",
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
    tools = {"browser_fetch": tool}
    for name, server_key in (extra or {}).items():
        tools[name] = build_runtime_tool(
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
    return RuntimeToolRegistry(tools=tools)


# ── 1. RuntimeToolRegistry → Routing Layer Wiring ────────────────────────────


class TestRuntimeRegistryPriorityInResolve:
    """Verify RuntimeToolRegistry is the sole routing authority."""

    def test_runtime_registry_wins_when_both_available(self) -> None:
        """RuntimeToolRegistry resolves tools it registers."""
        runtime_reg = _make_runtime_registry()
        configs = {"web_search": _http("http://127.0.0.1:8001")}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        assert resolver.resolve("browser_fetch") == "web_search"

    def test_runtime_only_resolve(self) -> None:
        """RuntimeToolRegistry alone can resolve its own tools."""
        runtime_reg = _make_runtime_registry()
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        assert resolver.resolve("browser_fetch") == "web_search"

    def test_unknown_tool_raises_with_runtime_only(self) -> None:
        """Unknown tool raises ValueError when only RuntimeToolRegistry is present."""
        runtime_reg = _make_runtime_registry()
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("no_such_browser_tool")

    def test_mixed_tools_resolve_correctly(self) -> None:
        """Tools registered in RuntimeToolRegistry resolve to their correct owners."""
        runtime_reg = _make_runtime_registry(extra={"read_text_file": "file_read"})
        configs = {"file_read": _http("http://127.0.0.1:8003")}
        resolver = ToolRouteResolver(configs, runtime_registry=runtime_reg)
        assert resolver.resolve("browser_fetch") == "web_search"
        assert resolver.resolve("read_text_file") == "file_read"

    def test_runtime_none_raises_for_all_tools(self) -> None:
        """Passing runtime_registry=None means no tool can resolve."""
        configs = {"file_read": _http("http://127.0.0.1:8004")}
        resolver = ToolRouteResolver(configs, runtime_registry=None)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("read_text_file")

    def test_strict_mode_error_message_mentions_runtime_registry(self) -> None:
        """strict_mode error message mentions RuntimeToolRegistry explicitly."""
        runtime_reg = _make_runtime_registry()
        configs: dict[str, McpServerConfig] = {}
        resolver = ToolRouteResolver(
            configs, strict_mode=True, runtime_registry=runtime_reg
        )
        with pytest.raises(ValueError, match="RuntimeToolRegistry"):
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

    def test_empty_runtime_registry_raises_for_all_tools(self) -> None:
        """Empty RuntimeToolRegistry means no tool can resolve."""
        empty_reg = RuntimeToolRegistry()
        configs = {"file_read": _http("http://127.0.0.1:8005")}
        resolver = ToolRouteResolver(configs, runtime_registry=empty_reg)
        with pytest.raises(ValueError, match="Unknown tool"):
            resolver.resolve("read_text_file")

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

    def test_set_runtime_registry_preserves_resolver_identity(self) -> None:
        """ToolExecutor.set_runtime_registry() mutates the existing resolver, not replaces it."""
        configs = {"file_read": _http("http://127.0.0.1:8006")}
        ex = _make_executor(configs=configs)
        resolver_before = ex._resolver
        runtime_reg = _make_runtime_registry()
        ex.set_runtime_registry(runtime_reg)
        assert ex._resolver is resolver_before
        # The mutated resolver now resolves via the newly-wired RuntimeToolRegistry.
        assert ex._resolver.resolve("browser_fetch") == "web_search"
        # No fallback: a tool not registered in the new RuntimeToolRegistry no longer resolves.
        with pytest.raises(ValueError, match="Unknown tool"):
            ex._resolver.resolve("read_text_file")


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
        """Tool absent from RuntimeToolRegistry is UNMAPPED."""
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

    def test_runtime_registry_mapped_tools_count_correctly(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Multiple tools registered in RuntimeToolRegistry all count as mapped."""
        runtime_reg = _make_runtime_registry(extra={"read_text_file": "file_read"})
        known_tools = frozenset({"browser_fetch", "read_text_file"})
        with caplog.at_level(logging.INFO):
            ToolRouteResolver({}, known_tools=known_tools, runtime_registry=runtime_reg)
        infos = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert any("2/2 tools mapped" in msg for msg in infos)


# ── 2. /mcp tools Subcommand ─────────────────────────────────────────────────

# ── 3. Browser Tools config_dependent Migration ───────────────────────────────
# browser_fetch's TOOL_LIST entry now lives in mcp_servers.web_search.web_search_tools
# (merged from the retired standalone mcp_servers.browser package). TOOL_LIST is no
# longer browser-exclusive — it also contains search_web, which has no
# config_dependent key at all — so the first two tests below assert on the
# browser_fetch entry specifically rather than iterating the whole list.


class TestBrowserToolsConfigDependentMigration:
    """Verify web_search_tools.py's browser_fetch entry uses config_dependent instead of requires_config."""

    async def test_browser_tools_tool_list_contains_config_dependent(self) -> None:
        """browser_fetch's TOOL_LIST entry contains config_dependent property."""
        from mcp_servers.web_search.web_search_tools import TOOL_LIST

        fetch_tool = next(t for t in TOOL_LIST if t["name"] == "browser_fetch")
        assert "config_dependent" in fetch_tool, (
            f"Tool {fetch_tool['name']} missing config_dependent"
        )

    async def test_browser_tools_no_requires_config_in_tool_list(self) -> None:
        """browser_fetch's TOOL_LIST entry does NOT contain requires_config."""
        from mcp_servers.web_search.web_search_tools import TOOL_LIST

        fetch_tool = next(t for t in TOOL_LIST if t["name"] == "browser_fetch")
        assert "requires_config" not in fetch_tool, (
            f"Tool {fetch_tool['name']} still has requires_config"
        )

    async def test_browser_fetch_tool_has_config_dependent_true(self) -> None:
        """browser_fetch specifically has config_dependent: True."""
        from mcp_servers.web_search.web_search_tools import TOOL_LIST

        fetch_tool = next(t for t in TOOL_LIST if t["name"] == "browser_fetch")
        assert fetch_tool.get("config_dependent") is True


# ── 4. Discovery → RuntimeToolRegistry → LLM Payload Visibility (end-to-end) ──
# Exercises the real McpToolDiscoveryService.discover_all() call site (mocked
# HTTP transport only) through to RuntimeToolRegistry.llm_tool_definitions(),
# proving `enabled_for_llm` is correctly derived from a live discovery
# response rather than a hand-built RuntimeTool fixture (see
# `_make_runtime_registry()` above, which always passes `enabled_for_llm=True`
# explicitly and therefore cannot catch a regression in the discovery→registry
# wiring itself).


class TestDiscoveryToLlmVisibilityEndToEnd:
    """End-to-end regression guard for `enabled_for_llm` discovery wiring."""

    @staticmethod
    def _http_with_tools() -> AsyncMock:
        """Build a mocked httpx.AsyncClient returning one visible and one disabled tool."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "tools": [
                {
                    "name": "visible_tool",
                    "description": "stays visible",
                    "inputSchema": {"type": "object"},
                },
                {
                    "name": "hidden_tool",
                    "description": "explicitly disabled",
                    "inputSchema": {"type": "object"},
                    "enabled": False,
                    "disabled_reason": "config-gated",
                },
            ]
        }
        http.get = AsyncMock(return_value=resp)
        return http

    async def test_disabled_discovered_tool_excluded_from_llm_payload(self) -> None:
        """A discovered tool with `enabled: false` is hidden from the LLM payload."""
        http = self._http_with_tools()
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {
            "srv": McpServerConfig(TransportType.HTTP, "http://127.0.0.1:9100")
        }
        ctx.services_required.http = http

        result = await McpToolDiscoveryService(ctx).discover_all()

        names = {d["name"] for d in result.registry.llm_tool_definitions()}
        assert "visible_tool" in names
        assert "hidden_tool" not in names
        # Confirms the value came from the real _dedupe_and_build()/
        # build_runtime_tool() path, not a hand-built fixture.
        assert result.registry.get("hidden_tool").enabled_for_llm is False
