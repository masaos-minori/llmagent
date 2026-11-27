"""tests/mcp_servers/cicd/test_cicd_security_validation.py

Tests for scripts/mcp_servers/cicd/cicd_service_guards.py: validate_cicd_security() reports the
CI/CD server's own allowlist configuration and the effective credential as posture checks before
HTTP bind, keeps the empty allowlists fatal, rejects wildcard entries, and never echoes an
allowlist entry or the token. probe_check() maps the lifespan probe outcome to a posture check.
"""

from __future__ import annotations

from collections.abc import Generator

from mcp_servers.cicd.cicd_service_guards import (
    ProbeOutcome,
    probe_check,
    validate_cicd_security,
)
from shared.security.posture_contract import COMMON_CHECK_IDS, REQUIRED_CHECK_IDS
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_AUTH_TOKEN_MISSING,
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
    assert_non_secret,
)

# The four ids the frozen contract requires, plus the credential check this row adds.
# Extra checks are allowed by the contract, so the credential check is listed at the
# position validate_cicd_security() emits it, which is after the required ids.
CICD_SERVER_CHECK_IDS = (
    "server.repo_allowlist",
    "server.workflow_allowlist",
    "server.workflow_pattern_valid",
    "server.backend_available",
    "server.github_credential",
)
_CREDENTIAL = "effective-credential"
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
    effective_credential: str = _CREDENTIAL,
) -> dict[str, SecurityCheckResult]:
    """CI/CD's check results keyed by check id."""
    return {
        result.check_id: result
        for result in validate_cicd_security(
            backend,
            repo_allowlist,
            workflow_allowlist,
            effective_credential,
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

    def test_wildcard_entry_fails(self) -> None:
        result = _results((_REPO,), ("*",))["server.workflow_pattern_valid"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_percent_encoded_entry_fails(self) -> None:
        result = _results((_REPO,), ("%63i.yml",))["server.workflow_pattern_valid"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

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
        required = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["cicd"]
            if check_id not in COMMON_CHECK_IDS
        )
        # The contract requires these ids in this order and allows extra checks, so the
        # credential check is compared at the position validate_cicd_security() emits it.
        assert CICD_SERVER_CHECK_IDS[: len(required)] == required
        assert CICD_SERVER_CHECK_IDS[len(required) :] == ("server.github_credential",)

    def test_order_is_fixed(self) -> None:
        produced = validate_cicd_security(_NoProbeBackend(), (), (), _CREDENTIAL)
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
                backend,
                repo_allowlist,
                workflow_allowlist,
                _CREDENTIAL,
            )
            assert [result.check_id for result in produced] == list(
                CICD_SERVER_CHECK_IDS
            )
            assert len(produced) == len(CICD_SERVER_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_cicd_security(_NoProbeBackend(), (), (), "")
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestMessages:
    """Allowlist entries are raw allowlist values (REQ-002)."""

    def test_no_message_names_an_allowlist_entry(self) -> None:
        produced = validate_cicd_security(
            _NoProbeBackend(),
            (_REPO,),
            (_SLASH_PATTERN, _BACKSLASH_PATTERN),
            _CREDENTIAL,
        )
        for result in produced:
            assert _REPO not in result.message
            assert _SLASH_PATTERN not in result.message
            assert _BACKSLASH_PATTERN not in result.message

    def test_every_message_is_a_non_secret_summary(self) -> None:
        produced = validate_cicd_security(
            _NoProbeBackend(),
            (_REPO,),
            ("*",),
            _CREDENTIAL,
        )
        for result in produced:
            assert_non_secret(result.message, "message")
            assert _CREDENTIAL not in result.message


class TestCredentialCheck:
    """The credential check reports the effective value, never the token (REQ-002, AC-2)."""

    def test_missing_credential_fails(self) -> None:
        result = _results((_REPO,), ("build",), effective_credential="")[
            "server.github_credential"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_AUTH_TOKEN_MISSING

    def test_effective_credential_is_ok(self) -> None:
        result = _results((_REPO,), ("build",), effective_credential=_CREDENTIAL)[
            "server.github_credential"
        ]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_message_does_not_name_the_credential(self) -> None:
        result = _results((_REPO,), ("build",), effective_credential=_CREDENTIAL)[
            "server.github_credential"
        ]
        assert _CREDENTIAL not in result.message


class TestProbeCheck:
    """The lifespan probe outcome is mapped to a posture check by the guard policy (REQ-003)."""

    def test_read_permission_ok(self) -> None:
        result = probe_check(
            ProbeOutcome(
                read_permission=REASON_OK,
                reachability=REASON_OK,
                rate_limit=REASON_OK,
            )
        )
        assert result.check_id == "server.credential_probe"
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_read_permission_denied_fails(self) -> None:
        result = probe_check(
            ProbeOutcome(
                read_permission=REASON_AUTH_TOKEN_MISSING,
                reachability=REASON_OK,
                rate_limit=REASON_OK,
            )
        )
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_AUTH_TOKEN_MISSING

    def test_unreachable_api_fails(self) -> None:
        result = probe_check(
            ProbeOutcome(
                read_permission=REASON_DEPENDENCY_UNREACHABLE,
                reachability=REASON_DEPENDENCY_UNREACHABLE,
                rate_limit=REASON_OK,
            )
        )
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_no_probe_run_is_not_applicable(self) -> None:
        result = probe_check(
            ProbeOutcome(
                read_permission=REASON_NOT_APPLICABLE,
                reachability=REASON_NOT_APPLICABLE,
                rate_limit=REASON_NOT_APPLICABLE,
            )
        )
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_dispatch_permission_is_reported_not_applicable(self) -> None:
        result = probe_check(
            ProbeOutcome(
                read_permission=REASON_OK,
                reachability=REASON_OK,
                rate_limit=REASON_OK,
            )
        )
        assert REASON_NOT_APPLICABLE in result.message

    def test_message_stays_a_non_secret_summary(self) -> None:
        outcome = ProbeOutcome(
            read_permission=REASON_OK,
            reachability=REASON_OK,
            rate_limit="near_limit",
        )
        result = probe_check(outcome)
        assert len(result.message) <= 120
        assert_non_secret(result.message, "message")
