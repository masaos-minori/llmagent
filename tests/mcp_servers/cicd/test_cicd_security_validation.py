"""tests/mcp_servers/cicd/test_cicd_security_validation.py

Tests for scripts/mcp_servers/cicd/cicd_service_guards.py: validate_cicd_security() reports the
CI/CD server's own allowlist configuration as posture checks before HTTP bind, keeps the empty
allowlists fatal, and never echoes an allowlist entry.
"""

from __future__ import annotations

from collections.abc import Generator

from mcp_servers.cicd.cicd_service_guards import validate_cicd_security
from shared.security.posture_contract import COMMON_CHECK_IDS, REQUIRED_CHECK_IDS
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

CICD_SERVER_CHECK_IDS = (
    "server.repo_allowlist",
    "server.workflow_allowlist",
    "server.workflow_pattern_valid",
    "server.backend_available",
)
_REPO = "octocat/hello-world"
_SLASH_PATTERN = "workflows/build.yml"
_BACKSLASH_PATTERN = "build\\release"


class _NoProbeBackend:
    """A backend that exposes no availability probe, which is what CiBackend requires today."""


class _NonCallableProbeBackend:
    """A backend whose probe attribute exists but cannot be called."""

    is_available = "yes"


class _AwaitableResult:
    """A probe result that can only be awaited, never evaluated synchronously."""

    def __await__(self) -> Generator[None, None, bool]:
        return iter((True,))


class _AsyncProbeBackend:
    """A backend whose probe needs an event loop the startup stage does not have."""

    def is_available(self) -> _AwaitableResult:
        return _AwaitableResult()


class _AvailableBackend:
    """A backend that reports itself available."""

    def is_available(self) -> bool:
        return True


class _UnavailableBackend:
    """A backend that reports itself unavailable."""

    def is_available(self) -> bool:
        return False


def _results(
    repo_allowlist: tuple[str, ...],
    workflow_allowlist: tuple[str, ...],
    backend: object = _NoProbeBackend(),
) -> dict[str, SecurityCheckResult]:
    """CI/CD's check results keyed by check id."""
    return {
        result.check_id: result
        for result in validate_cicd_security(
            backend,
            repo_allowlist,
            workflow_allowlist,
        )
    }


class TestRepoAllowlist:
    """An empty repo_allowlist denies every operation: a startup failure (REQ-008)."""

    def test_empty_allowlist_fails(self) -> None:
        result = _results((), ("build",))["server.repo_allowlist"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY

    def test_non_empty_allowlist_is_ok(self) -> None:
        result = _results((_REPO,), ("build",))["server.repo_allowlist"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestWorkflowAllowlist:
    """An empty workflow_allowlist denies every trigger, so it is fatal, not a warning."""

    def test_empty_allowlist_fails(self) -> None:
        result = _results((_REPO,), ())["server.workflow_allowlist"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY

    def test_non_empty_allowlist_is_ok(self) -> None:
        result = _results((_REPO,), ("build",))["server.workflow_allowlist"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestWorkflowPatternValid:
    """An entry the runtime guard can never match is unreachable configuration."""

    def test_entry_with_a_forward_separator_fails(self) -> None:
        result = _results((_REPO,), (_SLASH_PATTERN,))["server.workflow_pattern_valid"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_entry_with_a_back_separator_fails(self) -> None:
        result = _results((_REPO,), (_BACKSLASH_PATTERN,))[
            "server.workflow_pattern_valid"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_clean_entries_are_ok(self) -> None:
        result = _results((_REPO,), ("build", "release"))[
            "server.workflow_pattern_valid"
        ]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_empty_allowlist_is_not_applicable(self) -> None:
        result = _results((_REPO,), ())["server.workflow_pattern_valid"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_failure_reports_the_count_and_not_the_entries(self) -> None:
        patterns = (_SLASH_PATTERN, _BACKSLASH_PATTERN, "build")
        result = _results((_REPO,), patterns)["server.workflow_pattern_valid"]
        assert "2 entry" in result.message
        for pattern in patterns:
            assert pattern not in result.message


class TestBackendAvailable:
    """The backend check is reported even when the injected backend cannot be probed."""

    def test_backend_without_a_probe_is_not_applicable(self) -> None:
        result = _results((_REPO,), ("build",), _NoProbeBackend())[
            "server.backend_available"
        ]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_non_callable_probe_is_not_applicable(self) -> None:
        result = _results(
            (_REPO,),
            ("build",),
            _NonCallableProbeBackend(),
        )["server.backend_available"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_async_probe_is_not_applicable(self) -> None:
        result = _results((_REPO,), ("build",), _AsyncProbeBackend())[
            "server.backend_available"
        ]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_available_backend_is_ok(self) -> None:
        result = _results((_REPO,), ("build",), _AvailableBackend())[
            "server.backend_available"
        ]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_unavailable_backend_fails(self) -> None:
        result = _results((_REPO,), ("build",), _UnavailableBackend())[
            "server.backend_available"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE


class TestCheckSet:
    """The check set is identical for every configuration so row 05 can compare it."""

    def test_ids_match_the_frozen_contract(self) -> None:
        expected = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["cicd"]
            if check_id not in COMMON_CHECK_IDS
        )
        assert expected == CICD_SERVER_CHECK_IDS

    def test_order_is_fixed(self) -> None:
        produced = validate_cicd_security(_NoProbeBackend(), (), ())
        assert [result.check_id for result in produced] == list(CICD_SERVER_CHECK_IDS)

    def test_check_set_is_identical_across_configurations(self) -> None:
        configurations = (
            ((), (), _NoProbeBackend()),
            ((_REPO,), ("build",), _AvailableBackend()),
            ((_REPO,), (_SLASH_PATTERN,), _UnavailableBackend()),
            ((), (), _AsyncProbeBackend()),
        )
        for repo_allowlist, workflow_allowlist, backend in configurations:
            produced = validate_cicd_security(
                backend, repo_allowlist, workflow_allowlist
            )
            assert [result.check_id for result in produced] == list(
                CICD_SERVER_CHECK_IDS
            )
            assert len(produced) == len(CICD_SERVER_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_cicd_security(_NoProbeBackend(), (), ())
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestMessages:
    """Allowlist entries are raw allowlist values (REQ-002)."""

    def test_no_message_names_an_allowlist_entry(self) -> None:
        produced = validate_cicd_security(
            _NoProbeBackend(),
            (_REPO,),
            (_SLASH_PATTERN, _BACKSLASH_PATTERN),
        )
        for result in produced:
            assert _REPO not in result.message
            assert _SLASH_PATTERN not in result.message
            assert _BACKSLASH_PATTERN not in result.message
