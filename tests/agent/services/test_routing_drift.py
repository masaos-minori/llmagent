"""tests/agent/services/test_routing_drift.py

Agentcfg003 REQ-007 (AC-10): tier drift is a report against declared metadata.
check_routing_safety_tiers() compares the reference seed registry with the live
RuntimeToolRegistry, reads no removed configuration map, and its findings never
change a tool decision.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.services.routing_drift import check_routing_safety_tiers
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_registry import get_registry

from tests.shared.runtime_tool_factory import build_fixture_runtime_tool


def _ctx_with_runtime(registry: RuntimeToolRegistry | None) -> MagicMock:
    ctx = MagicMock()
    if registry is None:
        ctx.services = None
    else:
        ctx.services = MagicMock()
        ctx.services.runtime_tools = registry
    return ctx


class TestCheckRoutingSafetyTiersDriftReport:
    def test_no_services_no_findings(self) -> None:
        """Pre-wiring startup point: nothing declared, nothing to compare."""
        assert check_routing_safety_tiers(_ctx_with_runtime(None)) == []

    def test_empty_live_registry_no_findings(self) -> None:
        """Pre-discovery point: an empty live registry declares nothing."""
        registry = RuntimeToolRegistry(tools={}, allowed_servers=frozenset())
        assert check_routing_safety_tiers(_ctx_with_runtime(registry)) == []

    def test_seed_tool_without_live_declaration_is_reported(self) -> None:
        seed_names = sorted(get_registry().get_all_tool_names())
        assert seed_names
        registry = RuntimeToolRegistry(
            tools={
                name: build_fixture_runtime_tool(name, "git") for name in seed_names[1:]
            },
            allowed_servers=frozenset({"git"}),
        )
        msgs = check_routing_safety_tiers(_ctx_with_runtime(registry))
        assert any(seed_names[0] in msg for msg in msgs)
        assert all(name not in msg for name in seed_names[1:] for msg in msgs)

    def test_all_seed_tools_declared_no_findings(self) -> None:
        registry = RuntimeToolRegistry(
            tools={
                name: build_fixture_runtime_tool(name, "git")
                for name in get_registry().get_all_tool_names()
            },
            allowed_servers=frozenset({"git"}),
        )
        assert check_routing_safety_tiers(_ctx_with_runtime(registry)) == []

    def test_removed_config_map_is_not_read(self) -> None:
        """A ctx carrying a stale tool_safety_tiers attribute still reports only
        the live-declaration drift (REQ-011: no compatibility reader)."""
        seed_names = sorted(get_registry().get_all_tool_names())
        assert seed_names
        ctx = _ctx_with_runtime(
            RuntimeToolRegistry(
                tools={
                    name: build_fixture_runtime_tool(name, "git")
                    for name in seed_names[1:]
                },
                allowed_servers=frozenset({"git"}),
            )
        )
        ctx.cfg.approval.tool_safety_tiers = {seed_names[0]: "READ_ONLY"}
        msgs = check_routing_safety_tiers(ctx)
        assert any(seed_names[0] in msg for msg in msgs)
