"""
tests/test_agent_mcp_status.py
Unit tests for McpStatusService and _tier_for_server.
"""

from __future__ import annotations

import pytest
from agent.services.enums import McpTier
from agent.services.exceptions import McpProbeError
from agent.services.mcp_status import TIER_LABELS, _tier_for_server


class TestTierForServer:
    def test_no_tools_returns_read_only(self) -> None:
        assert _tier_for_server([], {}) == McpTier.READ_ONLY

    def test_read_only_tool_returns_read_only(self) -> None:
        tiers = {"read_file": "READ_ONLY"}
        assert _tier_for_server(["read_file"], tiers) == McpTier.READ_ONLY

    def test_write_safe_tool_returns_write_safe(self) -> None:
        tiers = {"write_file": "WRITE_SAFE"}
        assert _tier_for_server(["write_file"], tiers) == McpTier.WRITE_SAFE

    def test_dangerous_tool_returns_write_dangerous(self) -> None:
        tiers = {"delete_file": "WRITE_DANGEROUS"}
        assert _tier_for_server(["delete_file"], tiers) == McpTier.WRITE_DANGEROUS

    def test_admin_tool_returns_admin(self) -> None:
        tiers = {"shell_run": "ADMIN"}
        assert _tier_for_server(["shell_run"], tiers) == McpTier.ADMIN

    def test_highest_tier_wins(self) -> None:
        tiers = {"read_file": "READ_ONLY", "delete_file": "WRITE_DANGEROUS"}
        assert (
            _tier_for_server(["read_file", "delete_file"], tiers)
            == McpTier.WRITE_DANGEROUS
        )

    def test_admin_beats_dangerous(self) -> None:
        tiers = {"shell_run": "ADMIN", "delete_file": "WRITE_DANGEROUS"}
        assert _tier_for_server(["shell_run", "delete_file"], tiers) == McpTier.ADMIN

    def test_unclassified_tool_treated_as_read_only(self) -> None:
        tiers = {}
        assert _tier_for_server(["unknown_tool"], tiers) == McpTier.READ_ONLY

    def test_empty_tiers_returns_read_only(self) -> None:
        assert _tier_for_server(["write_file", "delete_file"], {}) == McpTier.READ_ONLY

    def test_unknown_tier_string_raises_mcp_probe_error(self) -> None:
        tiers = {"my_tool": "SUPER_DANGEROUS"}
        with pytest.raises(McpProbeError, match="Unknown tier"):
            _tier_for_server(["my_tool"], tiers)


class TestTierLabels:
    def test_tier_labels_cover_all_tiers(self) -> None:
        for tier in McpTier:
            assert tier in TIER_LABELS

    def test_read_only_label_is_no(self) -> None:
        assert TIER_LABELS[McpTier.READ_ONLY] == "no"

    def test_write_safe_label(self) -> None:
        assert TIER_LABELS[McpTier.WRITE_SAFE] == "write-safe"

    def test_write_dangerous_label(self) -> None:
        assert TIER_LABELS[McpTier.WRITE_DANGEROUS] == "dangerous"

    def test_admin_label(self) -> None:
        assert TIER_LABELS[McpTier.ADMIN] == "admin"


class TestGetHttpStatusSandboxBackend:
    @pytest.mark.asyncio
    async def test_reads_sandbox_backend_from_details(self) -> None:
        """_get_http_status reads sandbox_backend from details dict."""
        service = McpStatusService.__new__(McpStatusService)

        class _FakeResponse:
            status_code = 200
            def json(self):
                return {
                    "status": "ok",
                    "ready": True,
                    "dependencies": {},
                    "details": {"sandbox_backend": "firejail"},
                }

        class _FakeClient:
            async def get(self, url: str):
                return _FakeResponse()

        avail, sandbox = await service._get_http_status(_FakeClient(), "http://localhost:8009")
        assert avail == McpAvailability.OK
        assert sandbox == "firejail"

    @pytest.mark.asyncio
    async def test_returns_empty_when_sandbox_backend_missing_from_details(self) -> None:
        service = McpStatusService.__new__(McpStatusService)

        class _FakeResponse:
            status_code = 200
            def json(self):
                return {"status": "ok", "ready": True, "dependencies": {}, "details": {}}

        class _FakeClient:
            async def get(self, url: str):
                return _FakeResponse()

        avail, sandbox = await service._get_http_status(_FakeClient(), "http://localhost:8009")
        assert avail == McpAvailability.OK
        assert sandbox == ""
