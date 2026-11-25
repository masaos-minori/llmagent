"""
tests/test_agent_mcp_status.py
Unit tests for McpStatusService and _tier_for_server.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from agent.services.config_pending_state import PendingMcpRecord
from agent.services.enums import McpAvailability, McpTier
from agent.services.exceptions import McpProbeError
from agent.services.mcp_status import (
    TIER_LABELS,
    McpPendingRow,
    McpStatusService,
    _tier_for_server,
)
from agent.services.models import McpProbeResult
from shared.mcp_config import McpServerConfig, StartupMode, TransportType


class TestTierForServer:
    """Agentcfg003 REQ-004: _tier_for_server consumes the declared tiers of the
    server's registered tools, not a configuration map."""

    def test_no_tools_returns_read_only(self) -> None:
        assert _tier_for_server([]) == McpTier.READ_ONLY

    def test_read_only_tool_returns_read_only(self) -> None:
        assert _tier_for_server(["READ_ONLY"]) == McpTier.READ_ONLY

    def test_write_safe_tool_returns_write_safe(self) -> None:
        assert _tier_for_server(["WRITE_SAFE"]) == McpTier.WRITE_SAFE

    def test_dangerous_tool_returns_write_dangerous(self) -> None:
        assert _tier_for_server(["WRITE_DANGEROUS"]) == McpTier.WRITE_DANGEROUS

    def test_admin_tool_returns_admin(self) -> None:
        assert _tier_for_server(["ADMIN"]) == McpTier.ADMIN

    def test_highest_tier_wins(self) -> None:
        assert (
            _tier_for_server(["READ_ONLY", "WRITE_DANGEROUS"])
            == McpTier.WRITE_DANGEROUS
        )

    def test_admin_beats_dangerous(self) -> None:
        assert _tier_for_server(["ADMIN", "WRITE_DANGEROUS"]) == McpTier.ADMIN

    def test_unknown_declared_tier_raises_mcp_probe_error(self) -> None:
        with pytest.raises(McpProbeError, match="Unknown declared tier"):
            _tier_for_server(["SUPER_DANGEROUS"])


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
            async def get(self, url: str, timeout: float = 5.0):
                return _FakeResponse()

        (
            avail,
            sandbox,
            _restart_rec,
            _op_action,
            _reason,
        ) = await service._get_http_status(_FakeClient(), "http://localhost:8009")
        assert avail == McpAvailability.OK
        assert sandbox == "firejail"

    @pytest.mark.asyncio
    async def test_returns_empty_when_sandbox_backend_missing_from_details(
        self,
    ) -> None:
        service = McpStatusService.__new__(McpStatusService)

        class _FakeResponse:
            status_code = 200

            def json(self):
                return {
                    "status": "ok",
                    "ready": True,
                    "dependencies": {},
                    "details": {},
                }

        class _FakeClient:
            async def get(self, url: str, timeout: float = 5.0):
                return _FakeResponse()

        (
            avail,
            sandbox,
            _restart_rec,
            _op_action,
            _reason,
        ) = await service._get_http_status(_FakeClient(), "http://localhost:8009")
        assert avail == McpAvailability.OK
        assert sandbox == ""


class TestProbeAllHealthTimeoutZero:
    @pytest.mark.asyncio
    async def test_health_timeout_zero_does_not_cause_near_instant_timeout(
        self,
    ) -> None:
        """REQ-006: health_timeout=0 should not cause near-instant timeout at probe_all()."""
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="test-token",
            health_timeout=0,
        )

        captured_kwargs: dict[str, object] = {}
        captured_headers: list[dict[str, str] | None] = []

        class _FakeAsyncClient:
            def __init__(self, **kwargs: object) -> None:
                captured_kwargs.update(kwargs)

            async def __aenter__(self) -> _FakeAsyncClient:
                return self

            async def __aexit__(self, *args: object) -> None:
                pass

            async def get(
                self,
                url: str,
                timeout: object = None,
                headers: dict[str, str] | None = None,
            ) -> MagicMock:
                captured_headers.append(headers)
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"tools": []}
                return resp

        ctx = MagicMock()
        ctx.cfg.approval.tool_safety_tiers = {}
        ctx.cfg.mcp.mcp_servers = {"test_server": cfg}

        with patch("agent.services.mcp_status.httpx.AsyncClient", _FakeAsyncClient):
            status = McpStatusService(ctx=ctx)
            await status.probe_all()

        # Assert: timeout should be None (no timeout), not 0 (near-instant)
        assert "timeout" in captured_kwargs
        timeout_val = captured_kwargs["timeout"]
        assert isinstance(timeout_val, httpx.Timeout)
        assert timeout_val.read is None
        # The health probe authenticates with the server's configured token
        assert captured_headers == [{"Authorization": "Bearer test-token"}]


class _FakeAsyncClient:
    """Minimal async httpx.AsyncClient stand-in returning empty tools."""

    def __init__(self, **kwargs: object) -> None:
        pass

    async def __aenter__(self) -> _FakeAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def get(self, *args: object, **kwargs: object) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"tools": []}
        return resp


class TestProbeAllTierDerivation:
    """REQ-003: probe_all derives each server's tier from the RuntimeToolRegistry
    (the ADR-003 sole tool authority), not the removed cfg.tool_names field."""

    @pytest.mark.asyncio
    async def test_probe_all_falls_back_to_read_only_when_registry_absent(
        self,
    ) -> None:
        """A server absent from the runtime registry degrades to READ_ONLY when
        the registry itself is None (no static-catalog fallback remains)."""
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="test-token",
        )
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {"srv": cfg}
        ctx.services_required.runtime_tools = None

        with patch("agent.services.mcp_status.httpx.AsyncClient", _FakeAsyncClient):
            status = McpStatusService(ctx=ctx)
            results = await status.probe_all()

        assert results[0].tier == McpTier.READ_ONLY

    @pytest.mark.asyncio
    async def test_probe_all_uses_registry_tier_for_populated_server(
        self,
    ) -> None:
        """A server whose tools live in the runtime registry takes the highest
        risk tier among those tools (READ_ONLY when unclassified)."""
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="test-token",
        )
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {"srv": cfg}
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.all_tools.return_value = [
            SimpleNamespace(
                name="write_file", server_key="srv", agent_safety_tier="WRITE_SAFE"
            ),
        ]

        with patch("agent.services.mcp_status.httpx.AsyncClient", _FakeAsyncClient):
            status = McpStatusService(ctx=ctx)
            results = await status.probe_all()

        assert results[0].tier == McpTier.WRITE_SAFE


class TestPendingRows:
    """REQ-008, AC-4: pending rows are a separate model, built from records only."""

    @staticmethod
    def _record(
        server_key: str, change: str, field_paths: tuple[str, ...]
    ) -> PendingMcpRecord:
        return PendingMcpRecord(
            server_key=server_key, change=change, field_paths=field_paths
        )

    def test_one_record_becomes_one_row(self) -> None:
        rows = McpStatusService.pending_rows(
            (self._record("svc", "added", ("mcp_servers/svc",)),)
        )

        assert rows == [
            McpPendingRow(
                server_key="svc", change="added", field_paths=("mcp_servers/svc",)
            )
        ]

    def test_a_pending_row_is_not_a_probe_result(self) -> None:
        """The two row types are distinct, so a pending definition cannot be rendered live."""
        rows = McpStatusService.pending_rows(
            (self._record("svc", "changed", ("mcp_servers/svc.url",)),)
        )

        assert not isinstance(rows[0], McpProbeResult)

    def test_no_records_means_no_rows(self) -> None:
        assert McpStatusService.pending_rows(()) == []

    def test_the_row_names_field_paths_and_no_value(self) -> None:
        rows = McpStatusService.pending_rows(
            (self._record("svc", "changed", ("mcp_servers/svc.auth_token",)),)
        )

        assert rows[0].field_paths == ("mcp_servers/svc.auth_token",)
        assert "secret-value" not in repr(rows[0])

    def test_building_rows_reads_no_lifecycle_or_probe_state(self) -> None:
        """`pending_rows` is a static mapping: it reaches no ctx, probe, or registry."""
        ctx = MagicMock()
        service = McpStatusService(ctx=ctx)

        rows = service.pending_rows(
            (self._record("svc", "removed", ("mcp_servers/svc",)),)
        )

        assert rows[0].change == "removed"
        assert ctx.method_calls == []
