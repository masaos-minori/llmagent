#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_service_guards.py

CiCdService security guard mixin — repo_allowlist + workflow_allowlist enforcement.

validate_cicd_security() is the startup-time entry point: it reports this server's own allowlist
configuration as a Security Posture, so cicd-mcp validates itself before HTTP bind instead of
being audited by the Agent.

Dependency direction: service_guards → models, service_defs
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Sequence

from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.cicd.cicd_models import CicdAuthorizationError
from mcp_servers.cicd.cicd_service_defs import CiBackend

logger = logging.getLogger(__name__)


class CiCdGuards:
    """Mixin providing repo/workflow allowlist guards for CiCdService."""

    def __init__(
        self,
        backend: CiBackend,
        repo_allowlist: list[str],
        workflow_allowlist: list[str],
    ) -> None:
        """Initialize the CI/CD guard mixin with backend and allowlists for repos and workflows."""
        self._backend = backend
        # Empty allowlist = deny all (fail-closed, U-3)
        self._repo_allowlist: list[str] = list(repo_allowlist)
        # Empty allowlist = deny all (fail-closed, same as repo_allowlist)
        self._workflow_allowlist: list[str] = list(workflow_allowlist)

        if not self._repo_allowlist:
            logger.warning(
                "cicd-mcp: repo_allowlist is empty — all repository operations will be denied",
            )
        if not self._workflow_allowlist:
            logger.warning(
                "cicd-mcp: workflow_allowlist is empty — all workflow triggers will be denied",
            )

    def _assert_allowed_repo(self, repo: str) -> None:
        """Raise CicdAuthorizationError when repo is not in the allowlist.

        Empty allowlist = deny all (fail-closed per U-3).
        """
        if not self._repo_allowlist:
            raise CicdAuthorizationError(
                f"Repository '{repo}' is denied: repo_allowlist is empty (fail-closed mode)",
            )
        if repo not in self._repo_allowlist:
            raise CicdAuthorizationError(
                f"Repository not in repo_allowlist: {repo}",
            )

    def _assert_allowed_workflow(self, workflow: str) -> None:
        """Raise CicdAuthorizationError when workflow is not in workflow_allowlist.

        Empty allowlist = deny all (fail-closed).
        """
        if not self._workflow_allowlist:
            raise CicdAuthorizationError(
                "workflow_allowlist is empty — all workflow triggers denied (fail-closed). "
                "Add allowed workflow patterns to config."
            )
        if "/" in workflow or "\\" in workflow:
            raise CicdAuthorizationError(
                f"Workflow value contains a path separator and is rejected: {workflow}",
            )
        if workflow not in self._workflow_allowlist:
            raise CicdAuthorizationError(
                f"Workflow not in workflow_allowlist: {workflow}",
            )


def _check(
    check_id: str,
    status: SecurityCheckStatus,
    reason_code: str,
    message: str,
) -> SecurityCheckResult:
    """One posture check result carrying the shared default versions."""
    return SecurityCheckResult(
        check_id=check_id,
        status=status,
        reason_code=reason_code,
        message=message,
    )


def _invalid_workflow_patterns(workflow_allowlist: Sequence[str]) -> list[str]:
    """Return the configured entries the runtime guard can never match.

    The test is the one _assert_allowed_workflow() applies to every call, so an entry that
    contains a path separator is unreachable configuration and the startup check and the runtime
    rejection cannot diverge.
    """
    return [
        pattern for pattern in workflow_allowlist if "/" in pattern or "\\" in pattern
    ]


def _backend_availability_reason(backend: CiBackend) -> str:
    """Return the reason code for the injected backend's own availability probe.

    CiBackend is a duck-typed injected object and this row does not add a protocol method to it,
    so a backend without a callable probe is reported not_applicable rather than skipped. A probe
    that returns an awaitable cannot be evaluated in the synchronous startup stage, so it is
    reported not_applicable instead of a truthy coroutine object.
    """
    probe = getattr(backend, "is_available", None)
    if not callable(probe):
        return REASON_NOT_APPLICABLE
    result = probe()
    if inspect.isawaitable(result):
        return REASON_NOT_APPLICABLE
    if result:
        return REASON_OK
    return REASON_DEPENDENCY_UNREACHABLE


def validate_cicd_security(
    backend: CiBackend,
    repo_allowlist: Sequence[str],
    workflow_allowlist: Sequence[str],
) -> list[SecurityCheckResult]:
    """CI/CD's own configuration checks, in the fixed order the posture contract expects.

    Pure function of the values the guard constructor already receives, so it runs in the
    SERVER_SECURITY_VALIDATION stage before HTTP bind, and it never raises for a policy
    violation. The four check ids are always present, with not_applicable used instead of
    omitting a check.

    Messages report setting names and counts: allowlist entries are raw allowlist values.
    """
    if repo_allowlist:
        repo_check = _check(
            "server.repo_allowlist",
            SecurityCheckStatus.OK,
            REASON_OK,
            "configured repository allowlist is non-empty",
        )
    else:
        repo_check = _check(
            "server.repo_allowlist",
            SecurityCheckStatus.FAILED,
            REASON_ALLOWLIST_EMPTY,
            "repo_allowlist is empty so every repository operation is denied",
        )

    if workflow_allowlist:
        workflow_check = _check(
            "server.workflow_allowlist",
            SecurityCheckStatus.OK,
            REASON_OK,
            "configured workflow allowlist is non-empty",
        )
    else:
        workflow_check = _check(
            "server.workflow_allowlist",
            SecurityCheckStatus.FAILED,
            REASON_ALLOWLIST_EMPTY,
            "workflow_allowlist is empty so every workflow trigger is denied",
        )

    invalid = _invalid_workflow_patterns(workflow_allowlist)
    if not workflow_allowlist:
        pattern_check = _check(
            "server.workflow_pattern_valid",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "no workflow pattern is configured to validate",
        )
    elif invalid:
        pattern_check = _check(
            "server.workflow_pattern_valid",
            SecurityCheckStatus.FAILED,
            REASON_CONFIG_INVALID,
            f"workflow_allowlist contains {len(invalid)} entry with a path separator",
        )
    else:
        pattern_check = _check(
            "server.workflow_pattern_valid",
            SecurityCheckStatus.OK,
            REASON_OK,
            "no configured workflow pattern contains a path separator",
        )

    backend_reason = _backend_availability_reason(backend)
    backend_status = (
        SecurityCheckStatus.FAILED
        if backend_reason == REASON_DEPENDENCY_UNREACHABLE
        else SecurityCheckStatus.OK
        if backend_reason == REASON_OK
        else SecurityCheckStatus.NOT_APPLICABLE
    )
    backend_check = _check(
        "server.backend_available",
        backend_status,
        backend_reason,
        {
            REASON_OK: "the injected backend reports itself available",
            REASON_DEPENDENCY_UNREACHABLE: "the injected backend reports itself unavailable",
            REASON_NOT_APPLICABLE: "the injected backend exposes no availability probe",
        }[backend_reason],
    )

    return [repo_check, workflow_check, pattern_check, backend_check]
