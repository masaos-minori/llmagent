"""tests/mcp_servers/shell/test_shell_security_validation.py

Tests for scripts/mcp_servers/shell/shell_service_static_helpers.py: init_sandbox() refuses every
backend it cannot prove safe, and validate_shell_security() reports the same rules as posture checks.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from mcp_servers.shell.shell_service_static_helpers import (
    init_sandbox,
    validate_shell_security,
)
from shared.security.posture_contract import COMMON_CHECK_IDS, REQUIRED_CHECK_IDS
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    REASON_SANDBOX_BACKEND_MISSING,
    REASON_SANDBOX_BACKEND_UNSUPPORTED,
    SecurityCheckResult,
    SecurityCheckStatus,
)

SHELL_SERVER_CHECK_IDS = (
    "server.sandbox_backend",
    "server.sandbox_binary",
    "server.command_allowlist",
    "server.resource_limits",
)
_WHICH_TARGET = "mcp_servers.shell.shell_service_static_helpers.shutil.which"


@pytest.fixture(autouse=True)
def _firejail_present() -> Iterator[None]:
    """Make the firejail binary present for every test here, so no test depends on the host."""
    with patch(_WHICH_TARGET, return_value="/usr/bin/firejail"):
        yield


def _results(
    backend: str,
    command_allowlist: tuple[str, ...] = ("ls",),
) -> dict[str, SecurityCheckResult]:
    """Shell's check results keyed by check id."""
    return {
        result.check_id: result
        for result in validate_shell_security(backend, command_allowlist)
    }


class TestInitSandboxFailClosed:
    """No backend value reaches the caller without being proven safe (REQ-005)."""

    def test_none_backend_raises(self) -> None:
        with pytest.raises(RuntimeError, match="not a sandboxing backend"):
            init_sandbox("none")

    def test_empty_backend_raises(self) -> None:
        with pytest.raises(RuntimeError, match="not a sandboxing backend"):
            init_sandbox("")

    def test_unrecognized_backend_raises(self) -> None:
        with pytest.raises(RuntimeError, match="not a sandboxing backend"):
            init_sandbox("firejail-lite")

    def test_refusal_message_names_the_backend_value(self) -> None:
        with pytest.raises(RuntimeError) as excinfo:
            init_sandbox("none")

        assert "backend='none'" in str(excinfo.value)

    def test_firejail_with_binary_present_returns_the_backend(self) -> None:
        assert init_sandbox("firejail") == "firejail"

    def test_firejail_with_missing_binary_raises(self) -> None:
        with patch(_WHICH_TARGET, return_value=None):
            with pytest.raises(RuntimeError, match="not found in PATH"):
                init_sandbox("firejail")


class TestValidateShellSecurityChecks:
    """The same rules as reportable posture checks, in a fixed order."""

    def test_returns_only_check_results(self) -> None:
        results = validate_shell_security("firejail", ("ls",))

        assert results
        assert all(isinstance(result, SecurityCheckResult) for result in results)

    def test_emits_the_four_finalized_check_ids_in_order(self) -> None:
        results = validate_shell_security("firejail", ("ls",))

        assert [result.check_id for result in results] == list(SHELL_SERVER_CHECK_IDS)

    def test_check_ids_match_the_frozen_shell_contract(self) -> None:
        required = REQUIRED_CHECK_IDS["shell"]

        assert set(required) - set(COMMON_CHECK_IDS) == set(SHELL_SERVER_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        results = validate_shell_security("none", ())

        assert len(results) == len(SHELL_SERVER_CHECK_IDS)

    def test_all_checks_pass_for_a_valid_configuration(self) -> None:
        results = _results("firejail", ("ls", "echo"))

        assert [results[check_id].status for check_id in SHELL_SERVER_CHECK_IDS] == [
            SecurityCheckStatus.OK,
            SecurityCheckStatus.OK,
            SecurityCheckStatus.OK,
            SecurityCheckStatus.OK,
        ]
        assert all(result.reason_code == REASON_OK for result in results.values())


class TestSandboxBackendChecks:
    """server.sandbox_backend and server.sandbox_binary carry the same rule init_sandbox enforces."""

    def test_unsupported_backend_fails_the_backend_check(self) -> None:
        results = _results("none")

        assert results["server.sandbox_backend"].status is SecurityCheckStatus.FAILED
        assert (
            results["server.sandbox_backend"].reason_code
            == REASON_SANDBOX_BACKEND_UNSUPPORTED
        )

    def test_unsupported_backend_makes_the_binary_check_not_applicable(self) -> None:
        results = _results("none")

        assert (
            results["server.sandbox_binary"].status
            is SecurityCheckStatus.NOT_APPLICABLE
        )
        assert results["server.sandbox_binary"].reason_code == REASON_NOT_APPLICABLE

    def test_missing_binary_fails_only_the_binary_check(self) -> None:
        with patch(_WHICH_TARGET, return_value=None):
            results = _results("firejail")

        assert results["server.sandbox_backend"].status is SecurityCheckStatus.OK
        assert results["server.sandbox_binary"].status is SecurityCheckStatus.FAILED
        assert (
            results["server.sandbox_binary"].reason_code
            == REASON_SANDBOX_BACKEND_MISSING
        )

    def test_backend_message_names_the_backend_not_the_allowlist(self) -> None:
        results = _results("none", ("curl",))
        message = results["server.sandbox_backend"].message

        assert "none" in message
        assert "curl" not in message


class TestCommandAllowlistCheck:
    """An empty allowlist is FAILED with no suppression flag, matching Shell's refusal behavior."""

    def test_empty_allowlist_fails_with_allowlist_empty(self) -> None:
        results = _results("firejail", ())

        assert results["server.command_allowlist"].status is SecurityCheckStatus.FAILED
        assert results["server.command_allowlist"].reason_code == REASON_ALLOWLIST_EMPTY

    def test_non_empty_allowlist_passes_and_hides_its_entries(self) -> None:
        results = _results("firejail", ("curl", "wget"))
        message = results["server.command_allowlist"].message

        assert results["server.command_allowlist"].status is SecurityCheckStatus.OK
        assert "2" in message
        assert "curl" not in message
        assert "wget" not in message


class TestResourceLimitsCheck:
    """server.resource_limits is the technical-safety check Shell owns."""

    def test_shipped_constants_pass(self) -> None:
        results = _results("firejail")

        assert results["server.resource_limits"].status is SecurityCheckStatus.OK

    def test_a_non_positive_constant_fails_the_check(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "mcp_servers.shell.shell_service_static_helpers._MAX_SUBPROCESS_COUNT",
            0,
        )
        results = _results("firejail")

        assert results["server.resource_limits"].status is SecurityCheckStatus.FAILED
        assert "_MAX_SUBPROCESS_COUNT" in results["server.resource_limits"].message
