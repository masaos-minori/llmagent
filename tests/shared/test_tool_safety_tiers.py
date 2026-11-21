"""
tests/test_tool_safety_tiers.py
Safety-tier coverage tests against the real producer-declared tool metadata,
complementing tests/test_startup_routing_drift.py's synthetic-registry
unit tests for check_tool_safety_tiers()/check_unknown_tool_safety_tiers().

Those existing tests prove the functions' logic is correct in isolation using
hand-built registries; this module's job is proving the real, currently
deployed producer TOOL_LIST declarations satisfy that logic (no seed tool
without a declared tier; no declared tool absent from the seed registry), plus
an explicit check that search_web declares "READ_ONLY".

agentcfg003: the removed config/agent.toml [tool_safety_tiers] table is gone —
tiers are declared values carried by each producer entry.
"""

from __future__ import annotations

from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_routing_validation import (
    check_tool_safety_tiers,
    check_unknown_tool_safety_tiers,
)

from tests.agent._producer_registry import make_producer_registry


class TestRealProducerSafetyTiers:
    """Exercise check_tool_safety_tiers()/check_unknown_tool_safety_tiers()
    against the real seed registry and the real producer-declared tiers, not a
    synthetic stub."""

    def test_no_registered_tool_missing_safety_tier(self) -> None:
        msgs = check_tool_safety_tiers(runtime_registry=make_producer_registry())
        assert msgs == []

    def test_no_unknown_tool_in_declared_tiers(self) -> None:
        msgs = check_unknown_tool_safety_tiers(
            runtime_registry=make_producer_registry()
        )
        assert msgs == []

    def test_search_web_is_read_only(self) -> None:
        assert (
            make_producer_registry().get("search_web").agent_safety_tier == "READ_ONLY"
        )


class TestUnknownToolSafetyTiersEarlyReturn:
    """check_unknown_tool_safety_tiers() must return no findings on an empty or
    absent runtime registry without touching the seed registry."""

    def test_returns_empty_when_runtime_registry_none(self) -> None:
        assert check_unknown_tool_safety_tiers(runtime_registry=None) == []

    def test_returns_empty_when_runtime_registry_has_no_tools(self) -> None:
        empty = RuntimeToolRegistry({}, allowed_servers=frozenset())
        assert check_unknown_tool_safety_tiers(runtime_registry=empty) == []
