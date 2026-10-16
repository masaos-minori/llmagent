"""tests/shared/test_security_startup_flow.py

Tests for scripts/shared/security/startup_flow.py: the REQ-003 stage ordering, the three
built-in common checks, and the fail-closed posture a failed validation run produces.
"""

from __future__ import annotations

import hashlib

from shared.security.posture_contract import (
    CHECK_ID_AUTH_TOKEN,
    CHECK_ID_OWN_CONFIG_ONLY,
    CHECK_ID_PUBLISHED_TOOLS,
    REQUIRED_CHECK_IDS,
    SECURITY_CONTRACT_VERSION,
    SecurityPosture,
    compute_config_fingerprint,
)
from shared.security.result_dto import (
    REASON_AUTH_TOKEN_MISSING,
    REASON_CONFIG_INVALID,
    REASON_CONFIG_MISSING,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)
from shared.security.startup_flow import (
    EXECUTED_STAGES,
    FLOW_VERSION,
    OWN_CONFIG_FILE_VIEW_KEY,
    StageCallable,
    StageOutcome,
    StartupStage,
    check_auth_token_present,
    check_own_config_only,
    check_published_tools_declared,
    run_startup_validation,
)

SHELL_VIEW: dict[str, object] = {
    OWN_CONFIG_FILE_VIEW_KEY: "shell_mcp_server.toml",
    "sandbox_backend": "firejail",
    "command_allowlist_count": 3,
}
SHELL_TOOLS = ("shell_execute", "shell_read")


def _check(
    check_id: str,
    status: SecurityCheckStatus = SecurityCheckStatus.OK,
    reason_code: str = REASON_OK,
    message: str = "stage check passed",
) -> SecurityCheckResult:
    """One stage-supplied check result."""
    return SecurityCheckResult(
        check_id=check_id,
        status=status,
        reason_code=reason_code,
        message=message,
    )


def _failed_check(check_id: str, reason_code: str) -> SecurityCheckResult:
    return _check(
        check_id, SecurityCheckStatus.FAILED, reason_code, "stage check failed"
    )


def _validate(
    *,
    server_key: str = "shell",
    own_config_file: str = "shell_mcp_server.toml",
    config_view: dict[str, object] | None = None,
    auth_token: str | None = "token-value",
    declared_tools: tuple[str, ...] = SHELL_TOOLS,
    schema_checks: StageCallable | None = None,
    server_checks: StageCallable | None = None,
    dependency_checks: StageCallable | None = None,
    tool_capability_checks: StageCallable | None = None,
) -> SecurityPosture:
    """Run the flow with the optional stages left out unless a test supplies them."""
    return run_startup_validation(
        server_key,
        own_config_file=own_config_file,
        config_view=SHELL_VIEW if config_view is None else config_view,
        auth_token=auth_token,
        declared_tools=declared_tools,
        schema_checks=schema_checks,
        server_checks=server_checks,
        dependency_checks=dependency_checks,
        tool_capability_checks=tool_capability_checks,
    )


class TestStageOrdering:
    """The flow runs the REQ-003 stages in one fixed order."""

    def test_the_enum_carries_the_nine_stages_in_order(self) -> None:
        assert [stage.value for stage in StartupStage] == [
            "config_load",
            "schema_validation",
            "common_security_validation",
            "server_security_validation",
            "dependency_validation",
            "tool_capability_validation",
            "runtime_state_installation",
            "http_bind",
            "ready",
        ]

    def test_the_flow_executes_only_the_stages_a_server_can_delegate(self) -> None:
        assert EXECUTED_STAGES == (
            StartupStage.SCHEMA_VALIDATION,
            StartupStage.COMMON_SECURITY_VALIDATION,
            StartupStage.SERVER_SECURITY_VALIDATION,
            StartupStage.DEPENDENCY_VALIDATION,
            StartupStage.TOOL_CAPABILITY_VALIDATION,
        )

    def test_checks_appear_in_stage_order(self) -> None:
        posture = _validate(
            schema_checks=lambda: [_check("schema.config_schema")],
            server_checks=lambda: [_check("server.sandbox_backend")],
            dependency_checks=lambda: [_check("dependency.sandbox_binary")],
            tool_capability_checks=lambda: [_check("tool.command_allowlist")],
        )

        assert [check.check_id for check in posture.checks] == [
            "schema.config_schema",
            CHECK_ID_OWN_CONFIG_ONLY,
            CHECK_ID_AUTH_TOKEN,
            CHECK_ID_PUBLISHED_TOOLS,
            "server.sandbox_backend",
            "dependency.sandbox_binary",
            "tool.command_allowlist",
        ]

    def test_the_flow_stops_at_the_first_failed_stage(self) -> None:
        posture = _validate(
            server_checks=lambda: [
                _failed_check("server.command_allowlist", REASON_CONFIG_INVALID)
            ],
            dependency_checks=lambda: [_check("dependency.sandbox_binary")],
            tool_capability_checks=lambda: [_check("tool.command_allowlist")],
        )

        assert [check.check_id for check in posture.checks] == [
            CHECK_ID_OWN_CONFIG_ONLY,
            CHECK_ID_AUTH_TOKEN,
            CHECK_ID_PUBLISHED_TOOLS,
            "server.command_allowlist",
        ]

    def test_a_failed_schema_stage_prevents_the_common_checks(self) -> None:
        posture = _validate(
            schema_checks=lambda: [
                _failed_check("schema.config_schema", REASON_CONFIG_INVALID)
            ]
        )

        assert [check.check_id for check in posture.checks] == ["schema.config_schema"]


class TestFailClosedPosture:
    """A posture from a failing run cannot report validated or ready (REQ-003, AC-003)."""

    def test_a_failing_security_stage_clears_validated_and_ready(self) -> None:
        posture = _validate(
            server_checks=lambda: [
                _failed_check("server.sandbox_backend", REASON_CONFIG_INVALID)
            ]
        )

        assert posture.validated is False
        assert posture.ready is False

    def test_a_warning_stage_keeps_validated_and_ready(self) -> None:
        posture = _validate(
            auth_token=None,
            server_checks=lambda: [
                _check(
                    "server.force_push_policy",
                    SecurityCheckStatus.WARNING,
                    REASON_CONFIG_INVALID,
                )
            ],
        )

        assert posture.validated is True
        assert posture.ready is True

    def test_a_clean_run_yields_a_validated_ready_posture(self) -> None:
        posture = _validate(server_checks=lambda: [_check("server.sandbox_backend")])

        assert posture.validated is True
        assert posture.ready is True
        assert posture.server_key == "shell"
        assert posture.contract_version == SECURITY_CONTRACT_VERSION
        assert posture.fingerprint == compute_config_fingerprint(SHELL_VIEW)

    def test_the_flow_never_raises_when_a_stage_raises(self) -> None:
        def boom() -> list[SecurityCheckResult]:
            raise RuntimeError("config body must not travel")

        posture = _validate(server_checks=boom)

        assert posture.validated is False
        assert posture.checks[-1].check_id == "server.stage_error"
        assert posture.checks[-1].reason_code == REASON_CONFIG_INVALID

    def test_a_raising_schema_stage_maps_to_config_invalid(self) -> None:
        def boom() -> list[SecurityCheckResult]:
            raise ValueError("bad value")

        posture = _validate(schema_checks=boom)

        assert posture.checks[-1].check_id == "schema.stage_error"
        assert posture.checks[-1].reason_code == REASON_CONFIG_INVALID

    def test_a_raising_dependency_stage_maps_to_dependency_unreachable(self) -> None:
        def boom() -> list[SecurityCheckResult]:
            raise ConnectionError("unreachable")

        posture = _validate(dependency_checks=boom)

        assert posture.checks[-1].check_id == "dependency.stage_error"
        assert posture.checks[-1].reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_a_raising_tool_capability_stage_maps_to_config_invalid(self) -> None:
        def boom() -> list[SecurityCheckResult]:
            raise KeyError("tool")

        posture = _validate(tool_capability_checks=boom)

        assert posture.checks[-1].check_id == "tool.stage_error"
        assert posture.checks[-1].reason_code == REASON_CONFIG_INVALID

    def test_the_raised_exception_text_is_not_echoed(self) -> None:
        secret_text = (
            "/opt/llm/config/shell_mcp_server.toml auth_token = sk-abcdefghijklmnop"
        )

        def boom() -> list[SecurityCheckResult]:
            raise RuntimeError(secret_text)

        posture = _validate(server_checks=boom)

        assert secret_text not in posture.checks[-1].message
        assert (
            posture.checks[-1].message
            == "server_security_validation stage raised RuntimeError"
        )

    def test_a_stage_returning_a_bad_check_is_reported_as_a_failed_stage(self) -> None:
        def bad() -> list[SecurityCheckResult]:
            return [_check("server.x", SecurityCheckStatus.OK, REASON_CONFIG_INVALID)]

        posture = _validate(server_checks=bad)

        assert posture.checks[-1].check_id == "server.stage_error"
        assert posture.validated is False


class TestCommonChecks:
    """Every posture carries the three built-in common check ids."""

    def test_the_three_builtin_common_checks_are_always_present(self) -> None:
        posture = _validate()

        assert {check.check_id for check in posture.checks} >= {
            CHECK_ID_OWN_CONFIG_ONLY,
            CHECK_ID_AUTH_TOKEN,
            CHECK_ID_PUBLISHED_TOOLS,
        }
        assert set(REQUIRED_CHECK_IDS["shell"][:3]) == {
            CHECK_ID_OWN_CONFIG_ONLY,
            CHECK_ID_AUTH_TOKEN,
            CHECK_ID_PUBLISHED_TOOLS,
        }

    def test_a_matching_own_config_file_passes(self) -> None:
        result = check_own_config_only("shell", "shell_mcp_server.toml", SHELL_VIEW)

        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_a_missing_own_config_file_fails(self) -> None:
        result = check_own_config_only("shell", "", SHELL_VIEW)

        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_MISSING

    def test_an_own_config_file_that_is_not_the_servers_own_file_fails(self) -> None:
        result = check_own_config_only(
            "shell", "agent.toml", {"own_config_file": "agent.toml"}
        )

        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_a_view_that_does_not_carry_the_restricted_name_fails(self) -> None:
        result = check_own_config_only(
            "shell", "shell_mcp_server.toml", {"sandbox_backend": "firejail"}
        )

        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_a_view_carrying_a_secret_shaped_value_fails(self) -> None:
        view = {
            OWN_CONFIG_FILE_VIEW_KEY: "shell_mcp_server.toml",
            "auth_token": "sk-abcdefghijklmnop",
        }
        result = check_own_config_only("shell", "shell_mcp_server.toml", view)

        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID
        assert "sk-abcdefghijklmnop" not in result.message

    def test_an_empty_auth_token_is_a_warning_not_a_failure(self) -> None:
        result = check_auth_token_present("shell", "")

        assert result.status is SecurityCheckStatus.WARNING
        assert result.reason_code == REASON_AUTH_TOKEN_MISSING
        assert "token-value" not in result.message

    def test_a_configured_auth_token_passes(self) -> None:
        result = check_auth_token_present("shell", "token-value")

        assert result.status is SecurityCheckStatus.OK

    def test_an_empty_declared_tool_set_fails(self) -> None:
        result = check_published_tools_declared("shell", ())

        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_a_declared_tool_set_passes(self) -> None:
        result = check_published_tools_declared("shell", SHELL_TOOLS)

        assert result.status is SecurityCheckStatus.OK
        assert result.message == "shell declares 2 tool name(s)"

    def test_an_unhashable_view_fails_and_yields_a_deterministic_fingerprint(
        self,
    ) -> None:
        view = {
            OWN_CONFIG_FILE_VIEW_KEY: "shell_mcp_server.toml",
            "allowed_dirs": ["/opt/llm/data"],
        }
        first = _validate(config_view=view)
        second = _validate(config_view=view)

        assert first.validated is False
        assert first.fingerprint == second.fingerprint
        assert len(first.fingerprint) == 64
        assert first.fingerprint != compute_config_fingerprint(SHELL_VIEW)

    def test_the_fallback_fingerprint_is_derived_from_the_server_key_only(self) -> None:
        view = {OWN_CONFIG_FILE_VIEW_KEY: "shell_mcp_server.toml", "blob": "x" * 121}
        posture = _validate(config_view=view)
        expected = hashlib.sha256(b"shell:config_view_rejected").hexdigest()

        assert posture.fingerprint == expected


class TestStageOutcome:
    """StageOutcome records one stage's checks and whether it is fatal."""

    def test_a_failed_check_makes_the_outcome_fatal(self) -> None:
        outcome = StageOutcome(
            stage=StartupStage.SERVER_SECURITY_VALIDATION,
            checks=(_failed_check("server.command_allowlist", REASON_CONFIG_INVALID),),
            fatal=True,
        )

        assert outcome.stage is StartupStage.SERVER_SECURITY_VALIDATION
        assert outcome.fatal is True

    def test_the_flow_version_is_recorded_as_a_string(self) -> None:
        assert FLOW_VERSION == "1"
