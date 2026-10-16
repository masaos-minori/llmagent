"""tests/shared/test_security_result_dto.py

Tests for scripts/shared/security/result_dto.py: the REQ-001 result DTO, the
reason-code vocabulary, and the non-secret enforcement point in __post_init__.
"""

from __future__ import annotations

import pytest
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_AUTH_TOKEN_MISSING,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    REASON_SERVER_KEY_MISMATCH,
    SECURITY_REASON_CODES,
    SecurityCheckResult,
    SecurityCheckStatus,
    assert_non_secret,
)

VALID_FINGERPRINT = "0" * 64

# A reason code that fits each status: WARNING and FAILED must name a reason.
_STATUS_REASONS = {
    SecurityCheckStatus.OK: REASON_OK,
    SecurityCheckStatus.WARNING: REASON_ALLOWLIST_EMPTY,
    SecurityCheckStatus.FAILED: REASON_ALLOWLIST_EMPTY,
    SecurityCheckStatus.NOT_APPLICABLE: REASON_NOT_APPLICABLE,
}


def _result(
    status: SecurityCheckStatus,
    reason_code: str = REASON_OK,
    message: str = "shell command allowlist present",
    check_id: str = "shell.allowlist_non_empty",
) -> SecurityCheckResult:
    """Build one check result with the posture-level fields left at their defaults."""
    return SecurityCheckResult(
        check_id=check_id,
        status=status,
        reason_code=reason_code,
        message=message,
    )


class TestRoundTrip:
    """to_dict()/from_dict() preserve a check result for every status."""

    @pytest.mark.parametrize("status", list(SecurityCheckStatus))
    def test_from_dict_to_dict_round_trips(self, status: SecurityCheckStatus) -> None:
        result = _result(status, _STATUS_REASONS[status])
        restored = SecurityCheckResult.from_dict(result.to_dict())

        assert restored == result

    def test_to_dict_emits_only_the_check_fields(self) -> None:
        payload = _result(SecurityCheckStatus.OK).to_dict()

        assert payload == {
            "id": "shell.allowlist_non_empty",
            "status": "ok",
            "reason_code": "ok",
            "message": "shell command allowlist present",
        }

    def test_from_dict_rejects_a_payload_missing_a_key(self) -> None:
        payload = _result(SecurityCheckStatus.OK).to_dict()
        payload.pop("reason_code")

        with pytest.raises(ValueError, match="missing keys"):
            SecurityCheckResult.from_dict(payload)


class TestReasonCodeVocabulary:
    """Every code a server can emit is enumerated, and an unknown one fails closed."""

    def test_vocabulary_size_matches_the_declared_codes(self) -> None:
        assert len(SECURITY_REASON_CODES) == 30

    @pytest.mark.parametrize(
        "reason_code",
        [
            REASON_OK,
            REASON_ALLOWLIST_EMPTY,
            REASON_AUTH_TOKEN_MISSING,
            REASON_NOT_APPLICABLE,
            REASON_SERVER_KEY_MISMATCH,
        ],
    )
    def test_emitted_codes_are_in_the_vocabulary(self, reason_code: str) -> None:
        assert reason_code in SECURITY_REASON_CODES
        status = (
            SecurityCheckStatus.OK
            if reason_code == REASON_OK
            else SecurityCheckStatus.FAILED
        )
        assert _result(status, reason_code).reason_code == reason_code

    def test_unknown_reason_code_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown reason_code"):
            _result(SecurityCheckStatus.FAILED, "alllowlist_empty")


class TestStatusReasonContract:
    """WARNING is non-fatal but must name why it warns; OK may not carry a finding."""

    def test_warning_round_trips_with_a_reason(self) -> None:
        result = _result(SecurityCheckStatus.WARNING, REASON_ALLOWLIST_EMPTY)

        assert SecurityCheckResult.from_dict(result.to_dict()) == result

    def test_warning_without_a_reason_raises(self) -> None:
        with pytest.raises(ValueError, match="WARNING must name a reason"):
            _result(SecurityCheckStatus.WARNING, REASON_OK)

    def test_ok_with_a_finding_reason_raises(self) -> None:
        with pytest.raises(ValueError, match="status OK requires reason ok"):
            _result(SecurityCheckStatus.OK, REASON_ALLOWLIST_EMPTY)

    def test_failed_and_not_applicable_are_accepted(self) -> None:
        assert (
            _result(SecurityCheckStatus.FAILED, REASON_ALLOWLIST_EMPTY).status
            == "failed"
        )
        assert _result(
            SecurityCheckStatus.NOT_APPLICABLE, REASON_NOT_APPLICABLE
        ).status == ("not_applicable")


class TestNonSecretEnforcement:
    """A DTO holding a Secret, a sensitive path, or a config body cannot be built."""

    @pytest.mark.parametrize(
        "message",
        [
            "auth_token = sk-abcdefghijklmnop",
            "token: hunter2hunter2hunter2",
            "config path /opt/llm/config/shell_mcp_server.toml is invalid",
            "[mcp_servers.shell]\nallowlist = []",
            "Authorization: Bearer abcdefghijklmnop",
        ],
    )
    def test_rejected_message_raises(self, message: str) -> None:
        with pytest.raises(ValueError):
            _result(SecurityCheckStatus.FAILED, REASON_ALLOWLIST_EMPTY, message=message)

    def test_rejected_value_is_not_echoed(self) -> None:
        secret = "sk-abcdefghijklmnop"
        with pytest.raises(ValueError) as excinfo:
            _result(
                SecurityCheckStatus.FAILED,
                REASON_ALLOWLIST_EMPTY,
                f"auth_token = {secret}",
            )

        assert secret not in str(excinfo.value)

    def test_overlong_message_is_rejected_as_a_config_body(self) -> None:
        with pytest.raises(ValueError, match="longer than a non-secret summary"):
            _result(
                SecurityCheckStatus.FAILED, REASON_ALLOWLIST_EMPTY, message="x" * 121
            )

    def test_reason_code_names_are_not_secrets(self) -> None:
        # REASON_AUTH_TOKEN_MISSING names a field; a message naming the same field is legal.
        result = _result(
            SecurityCheckStatus.WARNING,
            REASON_AUTH_TOKEN_MISSING,
            message="auth token is not configured for this server",
        )

        assert result.reason_code == REASON_AUTH_TOKEN_MISSING

    def test_assert_non_secret_accepts_a_plain_summary(self) -> None:
        assert_non_secret("sandbox backend firejail present", "message") is None

    def test_check_id_is_validated_too(self) -> None:
        with pytest.raises(ValueError, match="check_id contains an absolute path"):
            _result(
                SecurityCheckStatus.FAILED,
                REASON_ALLOWLIST_EMPTY,
                check_id="/opt/llm/x",
            )

    def test_empty_check_id_raises(self) -> None:
        with pytest.raises(ValueError, match="check_id must not be empty"):
            _result(SecurityCheckStatus.FAILED, REASON_ALLOWLIST_EMPTY, check_id="")


class TestFingerprintShape:
    """The DTO stores and shape-checks a fingerprint; it never computes one."""

    def test_valid_fingerprint_is_accepted(self) -> None:
        result = SecurityCheckResult(
            check_id="shell.allowlist_non_empty",
            status=SecurityCheckStatus.OK,
            reason_code=REASON_OK,
            message="shell command allowlist present",
            fingerprint=VALID_FINGERPRINT,
        )

        assert result.fingerprint == VALID_FINGERPRINT

    @pytest.mark.parametrize("fingerprint", ["0" * 63, "0" * 65, "Z" * 64, "deadbeef"])
    def test_malformed_fingerprint_raises(self, fingerprint: str) -> None:
        with pytest.raises(ValueError, match="64 lowercase hex"):
            SecurityCheckResult(
                check_id="shell.allowlist_non_empty",
                status=SecurityCheckStatus.OK,
                reason_code=REASON_OK,
                message="shell command allowlist present",
                fingerprint=fingerprint,
            )
