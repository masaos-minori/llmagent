"""tests/shared/test_mcp_health_contract.py
Strict-parse coverage for the shared `/health` body contract: full body, legacy
body, wrong-typed field, out-of-vocabulary reason code, and unknown capability state.
"""

from __future__ import annotations

import pytest
from shared.mcp_health_contract import (
    CAPABILITY_STATE_OK,
    HEALTH_DEGRADED_REASON_CODES,
    HEALTH_REASON_CONFIG_MISSING,
    HEALTH_SCHEMA_VERSION,
    LEGACY_HEALTH_SCHEMA_VERSION,
    CapabilityState,
    HealthReport,
    parse_health_body,
)


class TestFullBodyParse:
    """A version-1 body with the capability block parses field by field."""

    def test_full_body_keeps_every_contract_field(self) -> None:
        body = {
            "health_schema_version": 1,
            "liveness": True,
            "ready": False,
            "degraded_reasons": [HEALTH_REASON_CONFIG_MISSING],
            "capabilities": {
                "github.operations": "ok",
                "github.api": {
                    "state": "degraded",
                    "reason_code": HEALTH_REASON_CONFIG_MISSING,
                },
            },
        }
        report = parse_health_body(body)

        assert isinstance(report, HealthReport)
        assert report.health_schema_version == HEALTH_SCHEMA_VERSION
        assert report.liveness is True
        assert report.ready is False
        assert report.degraded_reasons == (HEALTH_REASON_CONFIG_MISSING,)
        assert report.capabilities["github.operations"] == CapabilityState(
            CAPABILITY_STATE_OK
        )
        assert report.capabilities["github.api"].state == "degraded"
        assert (
            report.capabilities["github.api"].reason_code
            == HEALTH_REASON_CONFIG_MISSING
        )
        assert report.is_legacy is False

    def test_capability_block_is_read_only(self) -> None:
        report = parse_health_body(
            {"liveness": True, "ready": True, "capabilities": {}}
        )
        with pytest.raises(TypeError):
            report.capabilities["x"] = CapabilityState(CAPABILITY_STATE_OK)


class TestLegacyBodyParse:
    """A body with only `liveness`/`ready` stays parseable (D-6 legacy branch)."""

    def test_legacy_body_parses_with_defaults(self) -> None:
        report = parse_health_body({"status": "ok", "ready": True, "liveness": True})

        assert report.health_schema_version == LEGACY_HEALTH_SCHEMA_VERSION
        assert report.liveness is True
        assert report.ready is True
        assert report.degraded_reasons == ()
        assert report.capabilities == {}
        assert report.is_legacy is True

    def test_empty_capability_block_reads_as_legacy(self) -> None:
        report = parse_health_body(
            {"ready": False, "liveness": True, "capabilities": {}}
        )
        assert report.is_legacy is True


class TestStrictFieldTypes:
    """A present field of the wrong type is rejected, never coerced."""

    def test_wrong_typed_bool_field_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="liveness"):
            parse_health_body({"liveness": "true", "ready": True})

    def test_boolean_is_not_an_integer_schema_version(self) -> None:
        with pytest.raises(ValueError, match="health_schema_version"):
            parse_health_body({"health_schema_version": True, "ready": True})

    def test_non_object_body_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="body"):
            parse_health_body(["not", "an", "object"])

    def test_degraded_reasons_must_be_a_list_of_codes(self) -> None:
        with pytest.raises(ValueError, match="degraded_reasons"):
            parse_health_body({"ready": True, "degraded_reasons": "config_missing"})


class TestClosedVocabulary:
    """Reason codes and capability states are closed sets; unknown values are rejected."""

    def test_reason_code_outside_the_vocabulary_is_rejected(self) -> None:
        assert HEALTH_DEGRADED_REASON_CODES == {
            HEALTH_REASON_CONFIG_MISSING,
            "server_unavailable",
            "half_open_trial_in_progress",
        }
        with pytest.raises(ValueError, match="degraded_reasons"):
            parse_health_body(
                {"ready": True, "degraded_reasons": ["dependency_failure"]}
            )

    def test_capability_reason_code_outside_the_vocabulary_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="capabilities.github.api"):
            parse_health_body(
                {
                    "ready": True,
                    "capabilities": {
                        "github.api": {
                            "state": "degraded",
                            "reason_code": "token_missing",
                        }
                    },
                }
            )

    def test_unknown_capability_state_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="capabilities.github.api"):
            parse_health_body({"ready": True, "capabilities": {"github.api": "broken"}})

    def test_capability_entry_must_be_a_state_or_an_object(self) -> None:
        with pytest.raises(ValueError, match="capabilities.github.api"):
            parse_health_body({"ready": True, "capabilities": {"github.api": 1}})
