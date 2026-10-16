"""tests/mcp_servers/test_health_response.py

Tests for scripts/mcp_servers/health_response.py: the payload is unchanged when no posture is
supplied, and the Security Posture contract is published verbatim when one is.
"""

from __future__ import annotations

import json

from fastapi.responses import JSONResponse
from mcp_servers.health_response import (
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_OK,
    make_health_response,
)
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
    """A shell posture whose one check follows the requested verdict."""
    check = SecurityCheckResult(
        check_id="server.command_allowlist",
        status=SecurityCheckStatus.OK if validated else SecurityCheckStatus.FAILED,
        reason_code=REASON_OK if validated else REASON_ALLOWLIST_EMPTY,
        message="command allowlist checked",
    )
    return SecurityPosture(
        contract_version=SECURITY_CONTRACT_VERSION,
        server_key="shell",
        policy_version="1",
        validated=validated,
        ready=validated,
        fingerprint="0" * 64,
        checks=(check,),
    )


class TestPayloadWithoutPosture:
    """A server that passes no posture publishes exactly what it published before."""

    def test_no_posture_publishes_only_the_existing_keys(self) -> None:
        body = _body(make_health_response({}, {"service": "shell-mcp"}))

        assert set(body) == BASE_KEYS
        assert "security" not in body

    def test_no_posture_keeps_a_healthy_server_ready(self) -> None:
        response = make_health_response({}, {"service": "shell-mcp"})

        assert response.status_code == 200
        assert _body(response)["status"] == HEALTH_STATUS_OK
        assert _body(response)["ready"] is True

    def test_no_posture_still_degrades_on_a_dependency_failure(self) -> None:
        response = make_health_response({"db": "unreachable"}, None)
        body = _body(response)

        assert response.status_code == 503
        assert body["status"] == HEALTH_STATUS_DEGRADED
        assert body["ready"] is False
        assert body["operator_action_required"] is True
        assert body["details"] == {}

    def test_the_existing_two_argument_call_form_still_works(self) -> None:
        body = _body(make_health_response({}, {}))

        assert body["dependencies"] == {}
        assert body["details"] == {}


class TestPosturePublication:
    """A server that passes a posture publishes it and lets it decide readiness (REQ-002)."""

    def test_a_validated_posture_adds_the_security_block(self) -> None:
        body = _body(make_health_response({}, {}, security=_posture(validated=True)))

        assert set(body) == BASE_KEYS | {"security"}

    def test_the_security_block_carries_the_contract_field_names(self) -> None:
        body = _body(make_health_response({}, {}, security=_posture(validated=True)))

        assert set(body["security"]) == POSTURE_KEYS

    def test_the_security_block_is_the_posture_published_verbatim(self) -> None:
        posture = _posture(validated=True)
        body = _body(make_health_response({}, {}, security=posture))

        assert body["security"] == posture.to_dict()

    def test_a_failed_posture_makes_the_server_not_ready(self) -> None:
        response = make_health_response({}, {}, security=_posture(validated=False))
        body = _body(response)

        assert response.status_code == 503
        assert body["status"] == HEALTH_STATUS_DEGRADED
        assert body["ready"] is False
        assert body["restart_recommended"] is False

    def test_a_validated_posture_does_not_hide_a_dependency_failure(self) -> None:
        response = make_health_response(
            {"db": "unreachable"},
            {},
            security=_posture(validated=True),
        )

        assert response.status_code == 503
        assert _body(response)["ready"] is False

    def test_the_published_block_carries_no_config_path_or_token(self) -> None:
        body = json.dumps(
            _body(make_health_response({}, {}, security=_posture(validated=True)))
        )

        assert "/opt/llm" not in body
        assert "sk-" not in body
