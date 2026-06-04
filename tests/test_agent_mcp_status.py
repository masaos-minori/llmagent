"""
tests/test_agent_mcp_status.py
Unit tests for McpStatusService and _tier_label_for_server.
"""

from __future__ import annotations

from agent.services.mcp_status import _tier_label_for_server


class TestTierLabelForServer:
    def test_no_tools_returns_no(self) -> None:
        assert _tier_label_for_server([], {}) == "no"

    def test_read_only_tool_returns_no(self) -> None:
        tiers = {"read_file": "READ_ONLY"}
        assert _tier_label_for_server(["read_file"], tiers) == "no"

    def test_write_safe_tool_returns_write_safe(self) -> None:
        tiers = {"write_file": "WRITE_SAFE"}
        assert _tier_label_for_server(["write_file"], tiers) == "write-safe"

    def test_dangerous_tool_returns_dangerous(self) -> None:
        tiers = {"delete_file": "WRITE_DANGEROUS"}
        assert _tier_label_for_server(["delete_file"], tiers) == "dangerous"

    def test_admin_tool_returns_admin(self) -> None:
        tiers = {"shell_run": "ADMIN"}
        assert _tier_label_for_server(["shell_run"], tiers) == "admin"

    def test_highest_tier_wins(self) -> None:
        tiers = {"read_file": "READ_ONLY", "delete_file": "WRITE_DANGEROUS"}
        assert (
            _tier_label_for_server(["read_file", "delete_file"], tiers) == "dangerous"
        )

    def test_admin_beats_dangerous(self) -> None:
        tiers = {"shell_run": "ADMIN", "delete_file": "WRITE_DANGEROUS"}
        assert _tier_label_for_server(["shell_run", "delete_file"], tiers) == "admin"

    def test_unclassified_tool_treated_as_read_only(self) -> None:
        tiers = {}
        assert _tier_label_for_server(["unknown_tool"], tiers) == "no"

    def test_empty_tiers_returns_no(self) -> None:
        assert _tier_label_for_server(["write_file", "delete_file"], {}) == "no"
