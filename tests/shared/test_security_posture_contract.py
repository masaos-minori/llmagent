"""tests/shared/test_security_posture_contract.py

Tests for scripts/shared/security/posture_contract.py: the REQ-002 posture envelope,
the non-secret config fingerprint, and the per-server required-check-id table.
"""

from __future__ import annotations

import pytest
from shared.security.posture_contract import (
    CHECK_ID_AUTH_TOKEN,
    CHECK_ID_OWN_CONFIG_ONLY,
    CHECK_ID_PUBLISHED_TOOLS,
    COMMON_CHECK_IDS,
    REQUIRED_CHECK_IDS,
    SECURITY_CONTRACT_VERSION,
    SecurityPosture,
    compute_config_fingerprint,
)
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

VALID_FINGERPRINT = compute_config_fingerprint(
    {"allowlist_size": 3, "sandbox": "firejail"}
)

# The check ids each server row finalizes, mirrored here so a change to the table is a decision.
SERVER_CHECK_IDS: dict[str, tuple[str, ...]] = {
    "shell": (
        "server.sandbox_backend",
        "server.sandbox_binary",
        "server.command_allowlist",
        "server.resource_limits",
    ),
    "git": (
        "server.repo_allowlist",
        "server.repo_allowlist_resolvable",
        "server.read_only_mode",
        "server.protected_branch_config",
    ),
    "github": (
        "server.repo_allowlist",
        "server.force_push_policy",
        "server.pr_review_required",
        "server.protected_branches",
        "server.path_denylist",
        "server.max_file_size",
        "server.audit_log_writable",
        "server.per_page_bounds",
    ),
    "cicd": (
        "server.repo_allowlist",
        "server.workflow_allowlist",
        "server.workflow_pattern_valid",
        "server.backend_available",
    ),
    "file_read": (
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.max_read_bytes",
    ),
    "file_write": (
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.max_write_bytes",
        "server.write_dirs_writable",
        "server.supported_extensions",
    ),
    "file_delete": (
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.allowed_root_protected",
        "server.audit_log_writable",
    ),
    "rag_pipeline": (
        "server.embed_url_configured",
        "server.llm_url_configured",
        "server.rag_db_path_configured",
        "server.sqlite_vec_available",
        "server.top_k_bounds",
        "server.min_score_valid",
        "server.refiner_limits",
    ),
    "mdq": (
        "server.auth_token_configured",
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.db_path_valid",
        "server.schema_valid",
        "server.index_available",
    ),
    "web_search": (
        "server.results_bounds",
        "server.search_timeout_valid",
        "server.browser_timeout_valid",
        "server.browser_response_limit",
        "server.browser_allowlist",
    ),
}


def _check(
    check_id: str = "server.command_allowlist",
    status: SecurityCheckStatus = SecurityCheckStatus.OK,
    reason_code: str = REASON_OK,
) -> SecurityCheckResult:
    """One check result, with the posture-level fields left at their defaults."""
    return SecurityCheckResult(
        check_id=check_id,
        status=status,
        reason_code=reason_code,
        message="shell command allowlist present",
    )


def _posture(
    checks: tuple[SecurityCheckResult, ...] | list[SecurityCheckResult] | None = None,
    *,
    validated: bool = True,
    ready: bool = True,
    server_key: str = "shell",
    fingerprint: str = VALID_FINGERPRINT,
) -> SecurityPosture:
    """A minimal valid posture for the assertions below."""
    return SecurityPosture(
        contract_version=SECURITY_CONTRACT_VERSION,
        server_key=server_key,
        policy_version="1",
        validated=validated,
        ready=ready,
        fingerprint=fingerprint,
        checks=tuple(checks) if checks is not None else (_check(),),
    )


class TestEnvelopeRoundTrip:
    """to_dict()/from_dict() preserve a posture, and the shape is the /health security block."""

    def test_from_dict_to_dict_round_trips(self) -> None:
        posture = _posture(
            (
                _check(),
                _check(
                    "server.sandbox_binary",
                    SecurityCheckStatus.WARNING,
                    REASON_ALLOWLIST_EMPTY,
                ),
            )
        )

        assert SecurityPosture.from_dict(posture.to_dict()) == posture

    def test_to_dict_emits_the_contract_keys(self) -> None:
        payload = _posture().to_dict()

        assert set(payload) == {
            "contract_version",
            "server_key",
            "policy_version",
            "validated",
            "ready",
            "fingerprint",
            "checks",
        }
        assert payload["contract_version"] == SECURITY_CONTRACT_VERSION
        assert payload["checks"][0] == {
            "id": "server.command_allowlist",
            "status": "ok",
            "reason_code": "ok",
            "message": "shell command allowlist present",
        }

    @pytest.mark.parametrize(
        "dropped",
        [
            "contract_version",
            "server_key",
            "policy_version",
            "validated",
            "ready",
            "fingerprint",
            "checks",
        ],
    )
    def test_from_dict_rejects_a_payload_missing_a_key(self, dropped: str) -> None:
        payload = _posture().to_dict()
        payload.pop(dropped)

        with pytest.raises(ValueError, match="missing keys"):
            SecurityPosture.from_dict(payload)

    def test_from_dict_rejects_a_malformed_checks_value(self) -> None:
        payload = _posture().to_dict()
        payload["checks"] = ["server.command_allowlist"]

        with pytest.raises(ValueError, match="check entry must be a mapping"):
            SecurityPosture.from_dict(payload)

    def test_checks_supplied_as_a_list_are_normalized_to_a_tuple(self) -> None:
        posture = _posture([_check()])

        assert isinstance(posture.checks, tuple)


class TestPostureValidationRules:
    """An envelope that cannot be published as a contract is refused at construction."""

    @pytest.mark.parametrize(
        ("field", "value"),
        [("contract_version", ""), ("server_key", ""), ("policy_version", "")],
    )
    def test_empty_identity_field_raises(self, field: str, value: str) -> None:
        envelope = {
            "contract_version": SECURITY_CONTRACT_VERSION,
            "server_key": "shell",
            "policy_version": "1",
        }
        envelope[field] = value
        with pytest.raises(ValueError, match=f"{field} must not be empty"):
            SecurityPosture(
                contract_version=envelope["contract_version"],
                server_key=envelope["server_key"],
                policy_version=envelope["policy_version"],
                validated=True,
                ready=True,
                fingerprint=VALID_FINGERPRINT,
                checks=(_check(),),
            )

    def test_empty_check_list_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one check"):
            _posture(checks=())

    @pytest.mark.parametrize("fingerprint", ["", "0" * 63, "0" * 65, "F" * 64])
    def test_malformed_fingerprint_raises(self, fingerprint: str) -> None:
        with pytest.raises(ValueError, match="64 lowercase hex"):
            _posture(fingerprint=fingerprint)

    def test_validated_with_a_failed_check_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be validated with a FAILED check"):
            _posture((_check(status=SecurityCheckStatus.FAILED),), validated=True)

    def test_failed_check_is_accepted_when_not_validated(self) -> None:
        posture = _posture(
            (_check(status=SecurityCheckStatus.FAILED),), validated=False, ready=False
        )

        assert posture.validated is False
        assert posture.ready is False

    def test_ready_without_validation_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be ready without validation"):
            _posture(
                (_check(status=SecurityCheckStatus.FAILED),),
                validated=False,
                ready=True,
            )

    def test_warning_and_not_applicable_keep_validated(self) -> None:
        posture = _posture(
            (
                _check(
                    "server.force_push_policy",
                    SecurityCheckStatus.WARNING,
                    REASON_ALLOWLIST_EMPTY,
                ),
                _check(
                    "server.path_denylist",
                    SecurityCheckStatus.NOT_APPLICABLE,
                    REASON_NOT_APPLICABLE,
                ),
            )
        )

        assert posture.validated is True
        assert posture.ready is True


class TestConfigFingerprint:
    """The fingerprint is deterministic, scalar-only, and never hashes a Secret or a path."""

    def test_same_mapping_yields_the_same_digest(self) -> None:
        first = compute_config_fingerprint({"sandbox": "firejail", "allowlist_size": 3})
        second = compute_config_fingerprint(
            {"allowlist_size": 3, "sandbox": "firejail"}
        )

        assert first == second
        assert len(first) == 64

    def test_a_changed_value_changes_the_digest(self) -> None:
        before = compute_config_fingerprint({"allowlist_size": 3})
        after = compute_config_fingerprint({"allowlist_size": 4})

        assert before != after

    def test_a_short_scalar_tuple_is_hashed(self) -> None:
        assert compute_config_fingerprint(
            {"limits": (1, 2, 3)}
        ) == compute_config_fingerprint({"limits": (1, 2, 3)})

    @pytest.mark.parametrize(
        "values",
        [
            {"auth_token": "sk-abcdefghijklmnop"},
            {"config_path": "/opt/llm/config/shell_mcp_server.toml"},
            {"blob": "x" * 121},
            {"allowed_dirs": ["/opt/llm/data"]},
            {"allowed_dirs": {"/opt/llm/data"}},
            {"limits": {"soft": 1, "hard": 2}},
            {"limits": tuple(range(9))},
            {"limits": (1, {"nested": 2})},
            {"handler": object()},
        ],
    )
    def test_rejected_input_raises(self, values: dict[str, object]) -> None:
        with pytest.raises(ValueError):
            compute_config_fingerprint(values)

    def test_rejected_value_is_not_echoed(self) -> None:
        secret = "sk-abcdefghijklmnop"
        with pytest.raises(ValueError) as excinfo:
            compute_config_fingerprint({"auth_token": secret})

        assert secret not in str(excinfo.value)

    def test_empty_key_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty string keys"):
            compute_config_fingerprint({"": 1})

    def test_an_empty_mapping_still_hashes(self) -> None:
        assert len(compute_config_fingerprint({})) == 64


class TestRequiredCheckIds:
    """Every server the Agent configures has a required-check list made of namespaced ids."""

    def test_server_keys_cover_the_agent_mcp_keys(self) -> None:
        assert set(REQUIRED_CHECK_IDS) == set(SERVER_CHECK_IDS)

    @pytest.mark.parametrize("server_key", sorted(REQUIRED_CHECK_IDS))
    def test_required_list_is_the_common_checks_plus_that_servers_checks(
        self, server_key: str
    ) -> None:
        assert (
            REQUIRED_CHECK_IDS[server_key]
            == COMMON_CHECK_IDS + SERVER_CHECK_IDS[server_key]
        )

    @pytest.mark.parametrize("server_key", sorted(REQUIRED_CHECK_IDS))
    def test_every_required_id_is_namespaced_and_unique(self, server_key: str) -> None:
        ids = REQUIRED_CHECK_IDS[server_key]

        assert len(ids) == len(set(ids))
        assert all(cid.startswith(("common.", "server.")) for cid in ids)

    def test_the_three_builtin_common_checks_are_required_everywhere(self) -> None:
        assert COMMON_CHECK_IDS == (
            CHECK_ID_OWN_CONFIG_ONLY,
            CHECK_ID_AUTH_TOKEN,
            CHECK_ID_PUBLISHED_TOOLS,
        )
        for ids in REQUIRED_CHECK_IDS.values():
            assert set(COMMON_CHECK_IDS) <= set(ids)
