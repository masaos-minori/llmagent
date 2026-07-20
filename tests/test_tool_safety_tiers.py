"""
tests/test_tool_safety_tiers.py
Safety-tier coverage tests against the real config/agent.toml [tool_safety_tiers]
table, complementing tests/test_startup_routing_drift.py's synthetic-registry
unit tests for check_tool_safety_tiers()/check_unknown_tool_safety_tiers().

Those existing tests prove the functions' logic is correct in isolation using
hand-built registries/dicts; this module's job is proving the real, currently
deployed config/agent.toml [tool_safety_tiers] table currently satisfies that
logic (no registered tool missing a tier; no tier entry naming an unregistered
tool), plus an explicit check that search_web resolves to "READ_ONLY".
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from shared.tool_routing_validation import (
    check_tool_safety_tiers,
    check_unknown_tool_safety_tiers,
)


def _real_tool_safety_tiers() -> dict[str, str]:
    path = Path(__file__).parent.parent / "config" / "agent.toml"
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    tiers: dict[str, str] = cfg["tool_safety_tiers"]
    return tiers


class TestRealAgentTomlSafetyTiers:
    """Exercise check_tool_safety_tiers()/check_unknown_tool_safety_tiers()
    against the real registry and the real config/agent.toml [tool_safety_tiers]
    table, not a synthetic stub."""

    def test_no_registered_tool_missing_safety_tier(self) -> None:
        msgs = check_tool_safety_tiers(tool_safety_tiers=_real_tool_safety_tiers())
        assert msgs == []

    def test_no_unknown_tool_in_safety_tiers(self) -> None:
        msgs = check_unknown_tool_safety_tiers(
            tool_safety_tiers=_real_tool_safety_tiers()
        )
        assert msgs == []

    def test_search_web_is_read_only(self) -> None:
        assert _real_tool_safety_tiers()["search_web"] == "READ_ONLY"
