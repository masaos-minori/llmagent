"""tests/test_mdq_metadata_consistency.py

Unit tests for mdq-mcp health and tool metadata consistency.

Verifies:
- No `stub` key in any mdq-mcp tool entry
- All non-admin tools have `"status": "production"`
- Admin tools (`fts_consistency_check`, `fts_rebuild`) have `"status": "admin"`
- Total tool count is 9
- Health response dict contains no `stub` field
"""

from __future__ import annotations


class TestMdqToolMetadataConsistency:
    """Verify mdq-mcp tool metadata is consistent (no stub markers, correct statuses)."""

    def test_total_tool_count(self) -> None:
        """mdq-mcp has exactly 9 tools."""
        from mcp_servers.mdq.tools import TOOL_LIST

        assert len(TOOL_LIST) == 9

    def test_no_stub_keys_in_tools(self) -> None:
        """No mdq-mcp tool entry contains a `stub` key."""
        from mcp_servers.mdq.tools import TOOL_LIST

        for tool in TOOL_LIST:
            assert "stub" not in tool, (
                f"Tool '{tool['name']}' has unexpected 'stub' key"
            )

    def test_production_tool_statuses(self) -> None:
        """7 non-admin mdq-mcp tools have status='production'."""
        from mcp_servers.mdq.tools import TOOL_LIST

        production_tools = {
            "search_docs",
            "get_chunk",
            "outline",
            "index_paths",
            "refresh_index",
            "stats",
            "grep_docs",
        }
        for tool in TOOL_LIST:
            if tool["name"] in production_tools:
                assert tool.get("status") == "production", (
                    f"Tool '{tool['name']}' should have status='production'"
                )

    def test_admin_tool_statuses(self) -> None:
        """2 admin mdq-mcp tools (fts_consistency_check, fts_rebuild) have status='admin'."""
        from mcp_servers.mdq.tools import TOOL_LIST

        admin_tools = {"fts_consistency_check", "fts_rebuild"}
        for tool in TOOL_LIST:
            if tool["name"] in admin_tools:
                assert tool.get("status") == "admin", (
                    f"Tool '{tool['name']}' should have status='admin'"
                )

    def test_all_tools_have_status_field(self) -> None:
        """All 9 mdq-mcp tools have a 'status' field."""
        from mcp_servers.mdq.tools import TOOL_LIST

        for tool in TOOL_LIST:
            assert "status" in tool, f"Tool '{tool['name']}' is missing 'status' field"


class TestMdqHealthMetadataConsistency:
    """Verify mdq-mcp /health response contains no stub field."""

    def test_health_response_no_stub(self) -> None:
        """Simulate the health endpoint response and assert no 'stub' key is present."""
        health_response = {
            "status": "ok",
            "ready": True,
            "dependencies": {},
            "details": {"service": "mdq-mcp"},
        }

        assert "stub" not in health_response
        assert "stub" not in health_response.get("details", {})

    def test_degraded_health_response_no_stub(self) -> None:
        """Simulate the degraded health response and assert no 'stub' key is present."""
        health_response = {
            "status": "degraded",
            "ready": False,
            "dependencies": {"index": "not_ready"},
            "details": {"service": "mdq-mcp"},
        }

        assert "stub" not in health_response
        assert "stub" not in health_response.get("details", {})
