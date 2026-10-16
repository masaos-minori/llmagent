"""tests/shared/test_shadow_validation.py

Tests for scripts/shared/security/shadow_validation.py: the six Shadow Validation outcomes, the
check-set difference that blocks canonicalization, and the non-secret shadow report.
"""

from __future__ import annotations

from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_AUTH_TOKEN_MISSING,
    REASON_OK,
    REASON_SANDBOX_BACKEND_MISSING,
    SecurityCheckResult,
    SecurityCheckStatus,
)
from shared.security.shadow_validation import (
    ShadowComparison,
    ShadowOutcome,
    compare_shadow_results,
    format_shadow_report,
)

AUDIT_SANDBOX = "shell sandbox_backend is missing"
AUDIT_ALLOWLIST = "shell command_allowlist is empty"
AUDIT_CHECK_IDS = {
    AUDIT_SANDBOX: "server.sandbox_backend",
    AUDIT_ALLOWLIST: "server.command_allowlist",
}
AUDIT_IDS = ("server.command_allowlist", "server.sandbox_backend")


def _check(
    check_id: str,
    status: SecurityCheckStatus = SecurityCheckStatus.OK,
    reason_code: str = REASON_OK,
) -> SecurityCheckResult:
    """One server-side check result."""
    return SecurityCheckResult(
        check_id=check_id,
        status=status,
        reason_code=reason_code,
        message=f"{check_id} checked",
    )


def _posture(
    checks: tuple[SecurityCheckResult, ...],
    *,
    server_key: str = "shell",
    contract_version: str = SECURITY_CONTRACT_VERSION,
    policy_version: str = "1",
) -> SecurityPosture:
    """A posture whose validated and ready flags follow its checks."""
    validated = not any(check.status is SecurityCheckStatus.FAILED for check in checks)
    return SecurityPosture(
        contract_version=contract_version,
        server_key=server_key,
        policy_version=policy_version,
        validated=validated,
        ready=validated,
        fingerprint="0" * 64,
        checks=checks,
    )


def _clean_posture() -> SecurityPosture:
    return _posture(
        (
            _check("server.sandbox_backend"),
            _check("server.command_allowlist"),
        )
    )


class TestOutcomeMatrix:
    """Each of the six Plan outcomes is produced by its own fixture."""

    def test_the_enum_carries_the_six_plan_outcomes(self) -> None:
        assert [outcome.value for outcome in ShadowOutcome] == [
            "match_pass",
            "match_fail",
            "agent_only_fail",
            "server_only_fail",
            "checkset_mismatch",
            "contract_error",
        ]

    def test_both_sides_flagging_nothing_is_match_pass(self) -> None:
        comparison = compare_shadow_results((), _clean_posture(), AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.MATCH_PASS
        assert comparison.matched_check_ids == AUDIT_IDS
        assert comparison.status_conflicts == ()

    def test_both_sides_flagging_the_same_check_is_match_fail(self) -> None:
        posture = _posture(
            (
                _check(
                    "server.sandbox_backend",
                    SecurityCheckStatus.WARNING,
                    REASON_SANDBOX_BACKEND_MISSING,
                ),
                _check("server.command_allowlist"),
            )
        )
        comparison = compare_shadow_results((AUDIT_SANDBOX,), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.MATCH_FAIL
        assert comparison.status_conflicts == ()

    def test_only_the_audit_flagging_a_check_is_agent_only_fail(self) -> None:
        comparison = compare_shadow_results(
            (AUDIT_ALLOWLIST,), _clean_posture(), AUDIT_CHECK_IDS
        )

        assert comparison.outcome is ShadowOutcome.AGENT_ONLY_FAIL
        assert comparison.status_conflicts == ("server.command_allowlist",)

    def test_only_the_server_flagging_a_check_is_server_only_fail(self) -> None:
        posture = _posture(
            (
                _check("server.sandbox_backend"),
                _check(
                    "server.command_allowlist",
                    SecurityCheckStatus.FAILED,
                    REASON_ALLOWLIST_EMPTY,
                ),
            )
        )
        comparison = compare_shadow_results((), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.SERVER_ONLY_FAIL
        assert comparison.status_conflicts == ("server.command_allowlist",)

    def test_a_check_the_server_added_is_checkset_mismatch(self) -> None:
        posture = _posture(
            (
                _check("server.sandbox_backend"),
                _check("server.command_allowlist"),
                _check("server.protected_branch"),
            )
        )
        comparison = compare_shadow_results((), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CHECKSET_MISMATCH
        assert comparison.server_only_check_ids == ("server.protected_branch",)

    def test_a_check_only_the_audit_covers_is_checkset_mismatch(self) -> None:
        audit_ids = dict(AUDIT_CHECK_IDS)
        audit_ids["shell auth_token is default"] = "common.auth_token"
        comparison = compare_shadow_results((), _clean_posture(), audit_ids)

        assert comparison.outcome is ShadowOutcome.CHECKSET_MISMATCH
        assert comparison.agent_only_check_ids == ("common.auth_token",)

    def test_a_posture_on_another_contract_version_is_contract_error(self) -> None:
        posture = _posture(((_check("server.sandbox_backend"),)), contract_version="2")
        comparison = compare_shadow_results((), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CONTRACT_ERROR

    def test_a_check_that_drifted_from_its_posture_version_is_contract_error(
        self,
    ) -> None:
        drifted = SecurityCheckResult(
            check_id="server.sandbox_backend",
            status=SecurityCheckStatus.OK,
            reason_code=REASON_OK,
            message="server.sandbox_backend checked",
            contract_version="2",
        )
        comparison = compare_shadow_results((), _posture((drifted,)), AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CONTRACT_ERROR

    def test_duplicate_check_ids_are_contract_error(self) -> None:
        posture = _posture(
            (
                _check("server.sandbox_backend"),
                _check("server.sandbox_backend"),
            )
        )
        comparison = compare_shadow_results((), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CONTRACT_ERROR

    def test_an_audit_check_id_that_is_not_non_secret_is_contract_error(self) -> None:
        audit_ids = {AUDIT_SANDBOX: "/opt/llm/config/shell_mcp_server.toml"}
        comparison = compare_shadow_results((), _clean_posture(), audit_ids)

        assert comparison.outcome is ShadowOutcome.CONTRACT_ERROR

    def test_a_server_key_that_is_not_non_secret_is_contract_error(self) -> None:
        posture = _posture(
            ((_check("server.sandbox_backend"),)), server_key="sk-abcdefghijklmnop"
        )
        comparison = compare_shadow_results((), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CONTRACT_ERROR
        assert comparison.server_key == "unknown"
        assert "sk-abcdefghijklmnop" not in format_shadow_report(comparison)


class TestBlockingCondition:
    """A check-set difference decides the outcome whatever the pass/fail verdict is."""

    def test_a_checkset_difference_wins_over_a_matching_pass(self) -> None:
        posture = _posture(
            (
                _check("server.sandbox_backend"),
                _check("server.command_allowlist"),
                _check("common.published_tools"),
            )
        )
        comparison = compare_shadow_results((), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CHECKSET_MISMATCH

    def test_a_checkset_difference_wins_over_a_matching_failure(self) -> None:
        posture = _posture(
            (
                _check(
                    "server.sandbox_backend",
                    SecurityCheckStatus.WARNING,
                    REASON_SANDBOX_BACKEND_MISSING,
                ),
                _check("server.command_allowlist"),
                _check(
                    "common.auth_token",
                    SecurityCheckStatus.WARNING,
                    REASON_AUTH_TOKEN_MISSING,
                ),
            )
        )
        comparison = compare_shadow_results((AUDIT_SANDBOX,), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CHECKSET_MISMATCH
        assert comparison.matched_check_ids == AUDIT_IDS

    def test_a_contract_error_wins_over_a_checkset_difference(self) -> None:
        posture = _posture(
            (
                _check("server.sandbox_backend"),
                _check("server.command_allowlist"),
                _check("common.auth_token"),
            ),
            contract_version="2",
        )
        comparison = compare_shadow_results((), posture, AUDIT_CHECK_IDS)

        assert comparison.outcome is ShadowOutcome.CONTRACT_ERROR


class TestNonSecretReport:
    """The report carries ids and outcome only (REQ-016 / REQ-004)."""

    def test_audit_message_text_never_reaches_the_report(self) -> None:
        secret_text = "shell auth_token = sk-abcdefghijklmnop for /opt/llm/config/shell_mcp_server.toml"
        audit_ids = {
            secret_text: "common.auth_token",
            AUDIT_SANDBOX: "server.sandbox_backend",
        }
        posture = _posture(
            (
                _check(
                    "common.auth_token",
                    SecurityCheckStatus.WARNING,
                    REASON_AUTH_TOKEN_MISSING,
                ),
                _check("server.sandbox_backend"),
            )
        )
        comparison = compare_shadow_results((secret_text,), posture, audit_ids)
        report = format_shadow_report(comparison)

        assert "sk-abcdefghijklmnop" not in report
        assert "/opt/llm" not in report
        assert report == (
            "shadow shell: outcome=match_fail"
            " matched=common.auth_token,server.sandbox_backend"
            " agent_only= server_only= conflicts="
        )

    def test_the_report_is_one_line_naming_the_server_and_outcome(self) -> None:
        comparison = compare_shadow_results(
            (AUDIT_ALLOWLIST,), _clean_posture(), AUDIT_CHECK_IDS
        )
        report = format_shadow_report(comparison)

        assert "\n" not in report
        assert "shell" in report
        assert "agent_only_fail" in report

    def test_the_comparison_carries_sorted_id_tuples(self) -> None:
        posture = _posture((_check("server.z_tool"), _check("server.a_tool")))
        audit_ids = {"z warning": "server.z_tool", "a warning": "server.a_tool"}
        comparison = compare_shadow_results(("a warning",), posture, audit_ids)

        assert comparison.outcome is ShadowOutcome.AGENT_ONLY_FAIL
        assert comparison.matched_check_ids == ("server.a_tool", "server.z_tool")
        assert comparison.status_conflicts == ("server.a_tool",)

    def test_a_comparison_without_checks_carries_empty_id_tuples(self) -> None:
        comparison = ShadowComparison(
            outcome=ShadowOutcome.CONTRACT_ERROR, server_key="git"
        )

        assert comparison.matched_check_ids == ()
        assert comparison.status_conflicts == ()
