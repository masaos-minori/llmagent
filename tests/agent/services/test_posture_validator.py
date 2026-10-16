"""tests/agent/services/test_posture_validator.py

Tests for scripts/agent/services/posture_validator.py: parse_posture() reads the security block a
server published, validate_posture() rejects a posture that answers for another server key, carries a
different contract version, omits a required check, or states an impossible shape, compare_fingerprint()
reports fingerprint drift for a server key, and no server-supplied text reaches a rejection message.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import agent.services.posture_validator as posture_validator
from agent.services.posture_validator import (
    SECURITY_BODY_KEY,
    compare_fingerprint,
    parse_posture,
    reset_fingerprint_state,
    validate_posture,
)
from shared.security.posture_contract import (
    COMMON_CHECK_IDS,
    REQUIRED_CHECK_IDS,
    SECURITY_CONTRACT_VERSION,
    SecurityPosture,
)
from shared.security.result_dto import (
    REASON_CHECK_SET_MISMATCH,
    REASON_CONFIG_INVALID,
    REASON_CONTRACT_VERSION_MISMATCH,
    REASON_FINGERPRINT_MISMATCH,
    REASON_OK,
    REASON_POSTURE_MISSING,
    REASON_SERVER_KEY_MISMATCH,
)

SERVER_KEY = "mdq"
FINGERPRINT = "a" * 64
SECRET_TEXT = "/opt/llm/secret/token-value"


def _checks(server_key: str = SERVER_KEY) -> list[dict[str, str]]:
    """One OK entry for every check the contract requires of this server."""
    return [
        {"id": check_id, "status": "ok", "reason_code": "ok", "message": "check passed"}
        for check_id in REQUIRED_CHECK_IDS[server_key]
    ]


def _posture_dict(
    server_key: str = SERVER_KEY, **overrides: object
) -> dict[str, object]:
    """A `security` block exactly as a server publishes it."""
    data: dict[str, object] = {
        "contract_version": SECURITY_CONTRACT_VERSION,
        "server_key": server_key,
        "policy_version": "1",
        "validated": True,
        "ready": True,
        "fingerprint": FINGERPRINT,
        "checks": _checks(server_key),
    }
    data.update(overrides)
    return data


def _body(posture: dict[str, object] | None = None) -> dict[str, object]:
    """A /health body, with or without the security block."""
    body: dict[str, object] = {
        "service": "mdq-mcp",
        "ready": True,
        "dependencies": {},
        "details": {},
    }
    if posture is not None:
        body[SECURITY_BODY_KEY] = posture
    return body


def _posture(**overrides: object) -> SecurityPosture:
    return SecurityPosture.from_dict(_posture_dict(**overrides))


class TestParsePosture:
    """The Agent reads a posture out of a probe body and never trusts an unreadable one."""

    def test_conforming_posture_is_accepted(self) -> None:
        result = parse_posture(_body(_posture_dict()), SERVER_KEY)
        assert result.accepted is True
        assert result.reason_code == REASON_OK
        assert result.server_key == SERVER_KEY

    def test_accepted_result_carries_the_parsed_posture(self) -> None:
        posture = parse_posture(_body(_posture_dict()), SERVER_KEY).posture
        assert posture is not None
        assert posture.server_key == SERVER_KEY
        assert len(posture.checks) == len(REQUIRED_CHECK_IDS[SERVER_KEY])

    def test_missing_security_block_is_rejected(self) -> None:
        result = parse_posture(_body(), SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_POSTURE_MISSING
        assert result.posture is None

    def test_non_mapping_security_block_is_rejected(self) -> None:
        result = parse_posture(_body("not-a-posture"), SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_missing_contract_key_is_rejected(self) -> None:
        posture = _posture_dict()
        del posture["fingerprint"]
        result = parse_posture(_body(posture), SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_malformed_check_entry_is_rejected_not_raised(self) -> None:
        posture = _posture_dict(checks=[{"id": "server.db_path_valid"}])
        result = parse_posture(_body(posture), SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_unknown_status_string_is_rejected(self) -> None:
        checks = _checks()
        checks[0]["status"] = "PASSED"
        result = parse_posture(_body(_posture_dict(checks=checks)), SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_extra_keys_are_ignored_not_stored(self) -> None:
        posture = _posture_dict(surprise=SECRET_TEXT)
        result = parse_posture(_body(posture), SERVER_KEY)
        assert result.accepted is True
        assert result.posture is not None
        assert SECRET_TEXT not in str(result.posture.to_dict())

    def test_a_rejection_never_echoes_server_text(self) -> None:
        checks = _checks()
        checks[0]["status"] = "PASSED"
        checks[0]["message"] = f"read {SECRET_TEXT} and {SECRET_TEXT}"
        result = parse_posture(_body(_posture_dict(checks=checks)), SERVER_KEY)
        assert SECRET_TEXT not in result.message


class TestValidatePosture:
    """The contract checks run in a fixed order and every violation names a reason code."""

    def test_conforming_posture_is_accepted(self) -> None:
        result = validate_posture(_posture(), expected_server_key=SERVER_KEY)
        assert result.accepted is True
        assert result.reason_code == REASON_OK

    def test_server_key_mismatch_is_rejected_under_the_probed_key(self) -> None:
        posture = _posture(server_key="file_read")
        result = validate_posture(posture, expected_server_key=SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_SERVER_KEY_MISMATCH
        assert result.server_key == SERVER_KEY

    def test_contract_version_mismatch_is_rejected(self) -> None:
        result = validate_posture(
            _posture(contract_version="2"),
            expected_server_key=SERVER_KEY,
        )
        assert result.accepted is False
        assert result.reason_code == REASON_CONTRACT_VERSION_MISMATCH

    def test_missing_required_check_is_rejected_and_named(self) -> None:
        omitted = REQUIRED_CHECK_IDS[SERVER_KEY][0]
        checks = [entry for entry in _checks() if entry["id"] != omitted]
        posture = SecurityPosture.from_dict(_posture_dict(checks=checks))
        result = validate_posture(posture, expected_server_key=SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_CHECK_SET_MISMATCH
        assert omitted in result.message

    def test_extra_checks_are_allowed(self) -> None:
        checks = _checks() + [
            {
                "id": "server.extra_check",
                "status": "ok",
                "reason_code": "ok",
                "message": "extra",
            }
        ]
        posture = SecurityPosture.from_dict(_posture_dict(checks=checks))
        result = validate_posture(posture, expected_server_key=SERVER_KEY)
        assert result.accepted is True

    def test_a_server_key_the_contract_does_not_define_is_rejected(self) -> None:
        data = _posture_dict()
        data["server_key"] = "unknown_server"
        result = validate_posture(
            SecurityPosture.from_dict(data),
            expected_server_key="unknown_server",
        )
        assert result.accepted is False
        assert result.reason_code == REASON_CHECK_SET_MISMATCH

    def test_bad_fingerprint_shape_is_rejected(self) -> None:
        result = parse_posture(
            _body(_posture_dict(fingerprint="not-a-fingerprint")), SERVER_KEY
        )
        assert result.accepted is False
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_ready_without_validation_is_rejected(self) -> None:
        result = parse_posture(_body(_posture_dict(validated=False)), SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_validate_posture_rechecks_shape_and_consistency_itself(self) -> None:
        # object.__setattr__ bypasses the constructor guards, which proves the validator does not
        # rely on them: a posture built in-process must fail the same checks a published one does.
        posture = _posture()
        object.__setattr__(posture, "fingerprint", "short")
        assert (
            validate_posture(posture, expected_server_key=SERVER_KEY).reason_code
            == REASON_CONFIG_INVALID
        )
        object.__setattr__(posture, "fingerprint", FINGERPRINT)
        object.__setattr__(posture, "validated", False)
        assert (
            validate_posture(posture, expected_server_key=SERVER_KEY).reason_code
            == REASON_CONFIG_INVALID
        )

    def test_a_warning_only_posture_is_still_accepted(self) -> None:
        checks = _checks()
        checks[0]["status"] = "warning"
        checks[0]["reason_code"] = "not_applicable"
        posture = SecurityPosture.from_dict(_posture_dict(checks=checks))
        result = validate_posture(posture, expected_server_key=SERVER_KEY)
        assert result.accepted is True

    def test_a_failed_check_makes_the_published_posture_unreadable(self) -> None:
        checks = _checks()
        checks[0]["status"] = "failed"
        checks[0]["reason_code"] = "allowlist_empty"
        result = parse_posture(_body(_posture_dict(checks=checks)), SERVER_KEY)
        assert result.accepted is False
        assert result.reason_code == REASON_CONFIG_INVALID


class TestCompareFingerprint:
    """Drift is detected between two postures for the same server key, never across keys."""

    def setup_method(self) -> None:
        reset_fingerprint_state()

    def test_the_first_posture_for_a_key_is_accepted(self) -> None:
        result = compare_fingerprint(SERVER_KEY, _posture())
        assert result.accepted is True
        assert result.reason_code == REASON_OK

    def test_an_unchanged_fingerprint_is_accepted(self) -> None:
        compare_fingerprint(SERVER_KEY, _posture())
        result = compare_fingerprint(SERVER_KEY, _posture())
        assert result.accepted is True

    def test_a_changed_fingerprint_is_reported(self) -> None:
        compare_fingerprint(SERVER_KEY, _posture())
        result = compare_fingerprint(SERVER_KEY, _posture(fingerprint="b" * 64))
        assert result.accepted is False
        assert result.reason_code == REASON_FINGERPRINT_MISMATCH

    def test_the_drift_message_carries_no_fingerprint_value(self) -> None:
        compare_fingerprint(SERVER_KEY, _posture())
        result = compare_fingerprint(SERVER_KEY, _posture(fingerprint="b" * 64))
        assert "a" * 64 not in result.message
        assert "b" * 64 not in result.message

    def test_each_server_key_tracks_its_own_fingerprint(self) -> None:
        compare_fingerprint(SERVER_KEY, _posture())
        result = compare_fingerprint("file_read", _posture(server_key="file_read"))
        assert result.accepted is True

    def test_reset_clears_the_process_local_map(self) -> None:
        compare_fingerprint(SERVER_KEY, _posture())
        reset_fingerprint_state()
        result = compare_fingerprint(SERVER_KEY, _posture(fingerprint="c" * 64))
        assert result.accepted is True


class TestModuleContract:
    """The validator stays pure: no probing, no server config, no mcp_servers import."""

    def test_module_imports_nothing_under_mcp_servers(self) -> None:
        source = inspect.getsource(posture_validator)
        assert "mcp_servers" not in source

    def test_module_performs_no_http_or_file_io(self) -> None:
        source = inspect.getsource(posture_validator)
        for forbidden in ("httpx", "open(", "ConfigLoader", "logger"):
            assert forbidden not in source

    def test_every_required_server_key_has_a_required_check_set(self) -> None:
        expected_keys = {
            "shell",
            "git",
            "github",
            "cicd",
            "file_read",
            "file_write",
            "file_delete",
            "rag_pipeline",
            "mdq",
            "web_search",
        }
        assert expected_keys <= set(REQUIRED_CHECK_IDS)
        for server_key, required in REQUIRED_CHECK_IDS.items():
            assert required, server_key
            assert set(required) >= set(COMMON_CHECK_IDS), server_key

    def test_the_validator_needs_no_configuration(self) -> None:
        source = Path(posture_validator.__file__).read_text(encoding="utf-8")
        assert "os.environ" not in source
        assert "toml" not in source
