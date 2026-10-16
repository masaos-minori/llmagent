"""tests/mcp_servers/file/test_file_health_posture.py

Tests for scripts/mcp_servers/file/common.py: _health() publishes a Security Posture through the
shared response builder, keeps the payload unchanged when no posture is supplied, and never folds
posture data into details.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.responses import JSONResponse
from mcp_servers.file.common import _health
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

BASE_KEYS = {
    "status",
    "ready",
    "liveness",
    "restart_recommended",
    "operator_action_required",
    "dependencies",
    "details",
}
POSTURE_KEYS = {
    "contract_version",
    "server_key",
    "policy_version",
    "validated",
    "ready",
    "fingerprint",
    "checks",
}


def _body(response: JSONResponse) -> dict[str, object]:
    """The decoded /health payload."""
    return json.loads(response.body)


def _posture(*, validated: bool) -> SecurityPosture:
    """A file_read posture whose one check follows the requested verdict."""
    check = SecurityCheckResult(
        check_id="server.allowed_dirs_configured",
        status=SecurityCheckStatus.OK if validated else SecurityCheckStatus.FAILED,
        reason_code=REASON_OK if validated else REASON_ALLOWLIST_EMPTY,
        message="allowed_dirs checked",
    )
    return SecurityPosture(
        contract_version=SECURITY_CONTRACT_VERSION,
        server_key="file_read",
        policy_version="1",
        validated=validated,
        ready=validated,
        fingerprint="0" * 64,
        checks=(check,),
    )


class TestHealthWithoutPosture:
    """A file server that passes no posture publishes exactly what it published before."""

    @pytest.mark.asyncio
    async def test_no_posture_publishes_only_the_existing_keys(
        self, tmp_path: Path
    ) -> None:
        response = await _health([str(tmp_path)])

        assert set(_body(response)) == BASE_KEYS
        assert "security" not in _body(response)

    @pytest.mark.asyncio
    async def test_no_posture_keeps_the_existing_status_codes(
        self, tmp_path: Path
    ) -> None:
        healthy = await _health([str(tmp_path)])
        degraded = await _health([str(tmp_path / "missing")])

        assert healthy.status_code == 200
        assert degraded.status_code == 503


class TestHealthWithPosture:
    """The posture is published verbatim and gates ready independently of deps."""

    @pytest.mark.asyncio
    async def test_validated_posture_publishes_the_security_block(
        self, tmp_path: Path
    ) -> None:
        response = await _health([str(tmp_path)], _posture(validated=True))
        body = _body(response)

        assert set(body) == BASE_KEYS | {"security"}
        security = body["security"]
        assert isinstance(security, dict)
        assert set(security) == POSTURE_KEYS
        assert body["status"] == "ok"
        assert body["ready"] is True
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_published_block_carries_the_server_key(self, tmp_path: Path) -> None:
        response = await _health([str(tmp_path)], _posture(validated=True))
        security = _body(response)["security"]

        assert isinstance(security, dict)
        assert security["server_key"] == "file_read"
        assert security["contract_version"] == SECURITY_CONTRACT_VERSION
        assert security["validated"] is True

    @pytest.mark.asyncio
    async def test_unvalidated_posture_makes_an_available_server_not_ready(
        self, tmp_path: Path
    ) -> None:
        response = await _health([str(tmp_path)], _posture(validated=False))
        body = _body(response)

        assert body["dependencies"] == {}
        assert body["ready"] is False
        assert body["status"] == "degraded"
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_missing_directory_still_degrades_a_validated_server(
        self, tmp_path: Path
    ) -> None:
        response = await _health([str(tmp_path / "missing")], _posture(validated=True))
        body = _body(response)

        assert body["dependencies"] != {}
        assert body["ready"] is False
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_posture_data_is_not_folded_into_details(
        self, tmp_path: Path
    ) -> None:
        response = await _health([str(tmp_path)], _posture(validated=True))
        body = _body(response)

        assert body["details"] == {}
