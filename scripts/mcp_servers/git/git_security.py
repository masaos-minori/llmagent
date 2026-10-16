#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_security.py

Shared security guards for GitService — repo-path allowlist, read-only check, and protected-branch enforcement.

validate_git_security() is the startup-time entry point: it reports Git's own Security Posture
from config values alone, so git-mcp validates its own configuration before HTTP bind instead of
being audited by the Agent.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from shared.security.result_dto import (
    REASON_ALLOWED_DIR_INVALID,
    REASON_ALLOWLIST_EMPTY,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.git import repository_state


def _resolve_repo_path(repo_path: str) -> tuple[bool, str, str]:
    """Resolve the canonical (symlink-resolved) path for a repository.

    Returns (ok, error, resolved_path).
    When ok=True, resolved_path contains the canonical path.
    When ok=False, resolved_path is empty string.
    """
    if not repo_path:
        return False, "repo_path is empty", ""
    try:
        resolved = str(Path(repo_path).resolve())
    except OSError:
        return False, f"cannot resolve path: {repo_path}", ""
    return True, "", resolved


def is_within_allowed_paths(
    repo_path: str, allowed_repo_paths: list[str]
) -> tuple[bool, str]:
    """Check whether repo_path is within one of the allowed repository roots.

    Uses PurePosixPath.relative_to() for component-aware containment,
    rejecting sibling paths like /allowed-repo-evil for an /allowed-repo root.
    Returns (ok, error) where ok=True means the path is authorized.
    """
    from pathlib import PurePosixPath

    # Fail-closed-empty-list convention: callers must enforce non-empty
    # allowed_repo_paths before calling this function.
    if not allowed_repo_paths:
        return False, "[DENIED] allowed_repo_paths is empty"

    ok, err, resolved = _resolve_repo_path(repo_path)
    if not ok:
        return False, err

    normalized = os.path.normpath(resolved)

    for allowed in allowed_repo_paths:
        try:
            PurePosixPath(normalized).relative_to(PurePosixPath(allowed))
            return True, ""
        except ValueError:
            continue

    return False, "[DENIED] repo_path not in allowed paths"


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


def _unusable_roots(allowed_repo_paths: Sequence[str]) -> list[str]:
    """Return the configured roots that cannot serve as their own boundary.

    A root must resolve and must be contained in the allowlist it belongs to. Probing each
    root with is_within_allowed_paths() is what keeps the startup check and the runtime check
    from diverging: a root the runtime would deny is reported before HTTP bind.
    """
    paths = list(allowed_repo_paths)
    unusable: list[str] = []
    for root in paths:
        if not _resolve_repo_path(root)[0]:
            unusable.append(root)
            continue
        within, _ = is_within_allowed_paths(root, paths)
        if not within:
            unusable.append(root)
    return unusable


def validate_git_security(
    allowed_repo_paths: Sequence[str],
    read_only: bool,
) -> list[SecurityCheckResult]:
    """Git's own security checks, in the fixed order the posture contract expects.

    Pure function of config values: it runs before any repository state exists and before HTTP
    bind, and never raises for a policy violation. The four check ids are always present, with
    not_applicable used instead of omitting a check.

    The protected-branch rule is installed by construction in GitSecurityGuards, so the
    config-only view reports it ok; GitSecurityGuards.validate_security() is where a missing
    repository state source becomes a failed dependency_unreachable check.

    Messages report counts only: configured repository roots are sensitive paths.
    """
    allowlist_present = len(allowed_repo_paths) > 0
    unusable = _unusable_roots(allowed_repo_paths)

    if allowlist_present:
        allowlist_check = _check(
            "server.repo_allowlist",
            SecurityCheckStatus.OK,
            REASON_OK,
            "configured repository allowlist is non-empty",
        )
    else:
        allowlist_check = _check(
            "server.repo_allowlist",
            SecurityCheckStatus.FAILED,
            REASON_ALLOWLIST_EMPTY,
            "allowed_repo_paths is empty so every repository operation is denied",
        )

    if not allowlist_present:
        resolvable_check = _check(
            "server.repo_allowlist_resolvable",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "no configured repository root exists to resolve",
        )
    elif unusable:
        resolvable_check = _check(
            "server.repo_allowlist_resolvable",
            SecurityCheckStatus.FAILED,
            REASON_ALLOWED_DIR_INVALID,
            f"{len(unusable)} of {len(allowed_repo_paths)} configured roots are not usable",
        )
    else:
        resolvable_check = _check(
            "server.repo_allowlist_resolvable",
            SecurityCheckStatus.OK,
            REASON_OK,
            "every configured root resolves and is contained in the allowlist",
        )

    if read_only:
        read_only_check = _check(
            "server.read_only_mode",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "read_only=true disables write operations so the write guard is not evaluated",
        )
    else:
        read_only_check = _check(
            "server.read_only_mode",
            SecurityCheckStatus.OK,
            REASON_OK,
            "read_only=false so write operations are permitted and the write guard is evaluated",
        )

    protected_check = _check(
        "server.protected_branch_config",
        SecurityCheckStatus.OK,
        REASON_OK,
        "protected-branch rule is installed in the git security guards",
    )

    return [allowlist_check, resolvable_check, read_only_check, protected_check]


class GitSecurityGuards:
    """Repository access and write-permission guards.
    Mixed into GitService via inheritance so tests can still call
    svc._check_repo_path() and svc._check_write().

    A host service that installs this mixin provides _allowed_repo_paths; the class-level
    default is empty so a guard set that was never installed reports the fail-closed reading.
    """

    _allowed_repo_paths: Sequence[str] = ()

    def __init__(
        self,
        repo_state: repository_state.RepositoryState,
        read_only: bool,
    ) -> None:
        """Initialize the security mixin with repository state and read-only flag."""
        self._repo_state = repo_state
        self._read_only = read_only

    def validate_security(self) -> list[SecurityCheckResult]:
        """The guards' own posture: the same four check ids, read from installed state.

        A service that already holds its configuration calls this instead of re-reading
        git_mcp_server.toml. The allowlist and read-only checks come from validate_git_security();
        the protected-branch check reports dependency_unreachable when no repository state
        source is wired, because _check_protected_branch() would then answer "not protected"
        without evidence.
        """
        checks = validate_git_security(self._allowed_repo_paths, self._read_only)
        if self._repo_state is not None:
            return checks
        return [
            check
            if check.check_id != "server.protected_branch_config"
            else _check(
                "server.protected_branch_config",
                SecurityCheckStatus.FAILED,
                REASON_DEPENDENCY_UNREACHABLE,
                "no repository state source is wired so the protected-branch rule has no evidence",
            )
            for check in checks
        ]

    def _check_repo_path(self, repo_path: str) -> tuple[bool, str, str]:
        """Return (ok, error, resolved_path).

        ok=True when repo_path is within an allowed path prefix.
        When ok=True, resolved_path contains the canonical (symlink-resolved) path.
        When ok=False, resolved_path is empty string.
        """
        # Resolve the canonical path first — used by callers for audit logging.
        ok, err, resolved = _resolve_repo_path(repo_path)
        if not ok:
            return False, err, ""
        # Allowlist check is delegated to subclasses that know the allowed paths.
        return True, "", resolved

    def _check_write(self) -> tuple[bool, str]:
        """Return (ok, error); ok=True when write operations are permitted."""
        if self._read_only:
            return False, "[DENIED] git-mcp is configured with read_only=true"
        return True, ""

    def _check_protected_branch(self) -> tuple[bool, str]:
        """Return (ok, error); ok=True if branch is NOT protected."""
        if self._repo_state.protected_branch:
            return False, "[DENIED] branch is a protected branch"
        return True, ""
