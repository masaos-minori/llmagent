#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_service_guards.py

CiCdService security guard mixin — repo_allowlist + workflow_allowlist enforcement.

validate_cicd_security() is the startup-time entry point: it reports this server's own allowlist
configuration and the effective credential as a Security Posture, so cicd-mcp validates itself
before HTTP bind instead of being audited by the Agent. The read-permission probe result is
mapped to a posture check here; the probe itself runs in the server's lifespan, because this
module stays pure and synchronous.

Dependency direction: service_guards → models, credential, service_defs
"""

from __future__ import annotations

import dataclasses
import inspect
import logging
from collections.abc import Callable, Sequence

from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_AUTH_TOKEN_MISSING,
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdValidationError,
    canonical_repo_key,
    canonical_workflow_id,
)
from mcp_servers.cicd.cicd_service_defs import CiBackend

logger = logging.getLogger(__name__)


def _canonical_entry(value: str, canonicalizer: Callable[[str], str]) -> str:
    """Return the canonical form of a stored allowlist entry.

    An entry the canonicalizer rejects is returned unchanged, so the guard still
    sees it as unreachable configuration instead of rewriting the operator's
    setting; the startup pattern check reports it separately.
    """
    try:
        return canonicalizer(value)
    except ValueError:
        return value


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

        The request value and the stored entries are compared as canonical
        `owner/repo` keys, so a request that differs from an entry only by case
        cannot slip past the guard. A slug the canonicalizer rejects is denied.
        Empty allowlist = deny all (fail-closed per U-3).
        """
        if not self._repo_allowlist:
            raise CicdAuthorizationError(
                f"Repository '{repo}' is denied: repo_allowlist is empty (fail-closed mode)",
            )
        try:
            key = canonical_repo_key(repo)
        except CicdValidationError as exc:
            raise CicdAuthorizationError(str(exc)) from exc
        entries = {
            _canonical_entry(entry, canonical_repo_key)
            for entry in self._repo_allowlist
        }
        if key not in entries:
            raise CicdAuthorizationError(
                f"Repository not in repo_allowlist: {repo}",
            )

    def _assert_allowed_workflow(self, workflow: str) -> None:
        """Raise CicdAuthorizationError when workflow is not in workflow_allowlist.

        The request value and the stored entries are compared as canonical
        workflow identifiers produced by `canonical_workflow_id()`, so the guard
        and the request path cannot diverge. A value the canonicalizer rejects —
        a path separator, percent-encoding, or a wildcard — is denied.
        Empty allowlist = deny all (fail-closed).
        """
        if not self._workflow_allowlist:
            raise CicdAuthorizationError(
                "workflow_allowlist is empty — all workflow triggers denied (fail-closed). "
                "Add allowed workflow patterns to config."
            )
        try:
            canonical = canonical_workflow_id(workflow)
        except CicdValidationError as exc:
            raise CicdAuthorizationError(str(exc)) from exc
        entries = {
            _canonical_entry(entry, canonical_workflow_id)
            for entry in self._workflow_allowlist
        }
        if canonical not in entries:
            raise CicdAuthorizationError(
                f"Workflow not in workflow_allowlist: {workflow}",
            )


@dataclasses.dataclass(frozen=True)
class ProbeOutcome:
    """One side-effect-free read-permission probe result (REQ-003).

    The server's lifespan runs the probe with the shared client and hands the
    outcome here; this module only maps it to a posture check, so the pure
    startup function stays synchronous.
    """

    read_permission: str
    reachability: str
    rate_limit: str
    dispatch_permission: str = REASON_NOT_APPLICABLE


_PROBE_READ_REASONS = {
    REASON_OK: REASON_OK,
    REASON_AUTH_TOKEN_MISSING: REASON_AUTH_TOKEN_MISSING,
    REASON_DEPENDENCY_UNREACHABLE: REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE: REASON_NOT_APPLICABLE,
}


def probe_check(outcome: ProbeOutcome) -> SecurityCheckResult:
    """Map a probe outcome to the `server.credential_probe` posture check.

    The status follows the read-permission dimension: OK when the credential
    reads, FAILED when it is invalid or the API is unreachable, NOT_APPLICABLE
    when no probe ran. Dispatch permission is reported `not_applicable` because
    no side-effect-free endpoint exposes write permission (REQ-003). Messages
    carry dimension statuses only, never the token.
    """
    reason = _PROBE_READ_REASONS.get(outcome.read_permission, REASON_NOT_APPLICABLE)
    status = (
        SecurityCheckStatus.OK
        if reason == REASON_OK
        else SecurityCheckStatus.FAILED
        if reason in (REASON_AUTH_TOKEN_MISSING, REASON_DEPENDENCY_UNREACHABLE)
        else SecurityCheckStatus.NOT_APPLICABLE
    )
    message = (
        f"read {outcome.read_permission}; "
        f"reachability {outcome.reachability}; "
        f"rate limit {outcome.rate_limit}; "
        f"dispatch {outcome.dispatch_permission}"
    )
    return _check("server.credential_probe", status, reason, message)


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

    The test is the one the runtime guard applies to every call through
    `canonical_workflow_id()`, so an entry with a path separator or a wildcard is
    unreachable configuration and the startup check and the runtime rejection
    cannot diverge.
    """
    return [
        pattern
        for pattern in workflow_allowlist
        if "/" in pattern or "\\" in pattern or "%" in pattern or "*" in pattern
    ]


def _backend_availability_reason(backend: CiBackend | None) -> str:
    """Return the reason code for the injected backend's own availability probe.

    CiBackend is a duck-typed injected object and this row does not add a protocol method to it,
    so a backend without a callable probe is reported not_applicable rather than skipped. A probe
    that returns an awaitable cannot be evaluated in the synchronous startup stage, so it is
    reported not_applicable instead of a truthy coroutine object. The bind gate runs before the
    lifespan builds the service, so the pre-bind stage passes None and this stays not_applicable.
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
    backend: CiBackend | None,
    repo_allowlist: Sequence[str],
    workflow_allowlist: Sequence[str],
    effective_credential: str,
) -> list[SecurityCheckResult]:
    """CI/CD's own configuration checks, in the fixed order the posture contract expects.

    Pure function of the values the guard constructor already receives plus the
    effective credential resolved by the credential module, so it runs in the
    SERVER_SECURITY_VALIDATION stage before HTTP bind, and it never raises for a
    policy violation. The check ids are always present, with not_applicable used
    instead of omitting a check.

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
            f"workflow_allowlist contains {len(invalid)} entry with a rejected form",
        )
    else:
        pattern_check = _check(
            "server.workflow_pattern_valid",
            SecurityCheckStatus.OK,
            REASON_OK,
            "no configured workflow pattern carries a rejected form",
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

    # The credential check is config-only: the effective value is supplied by the
    # caller through resolve_effective_credential(), so this module never reads the
    # environment itself. A write-capable start without a credential is FAILED,
    # which keeps the posture unvalidated and the bind gate closed (REQ-002).
    if effective_credential:
        credential_check = _check(
            "server.github_credential",
            SecurityCheckStatus.OK,
            REASON_OK,
            "an effective credential is available for the write-capable start",
        )
    else:
        credential_check = _check(
            "server.github_credential",
            SecurityCheckStatus.FAILED,
            REASON_AUTH_TOKEN_MISSING,
            "no effective credential is available for the write-capable start",
        )

    return [
        repo_check,
        workflow_check,
        pattern_check,
        backend_check,
        credential_check,
    ]
