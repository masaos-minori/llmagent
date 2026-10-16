#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_service_security.py

GitHubSecurityGuards — security policy enforcement mixin for GitHubService.

validate_github_security() is the startup-time entry point: it reports this server's own policy
as a Security Posture from its config object alone, so github-mcp validates itself before HTTP
bind instead of being audited by the Agent.

Methods: _clamp_per_page, _assert_allowed_*, _write_github_audit_log,
         _resolve_and_check_branch, _get_repo, _handle_github_error, _run_github

Dependency direction: service_security → models_config, models_base, mapper
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import os
from collections.abc import Callable
from http import HTTPStatus
from typing import Any, NoReturn, TypeVar

from github import GithubException
from shared.json_utils import now_iso_raw
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_DESTRUCTIVE_GUARD_MISSING,
    REASON_FORCE_PUSH_ENABLED,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.github.github_models_config import GitHubConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GitHubSecurityGuards:
    """Mixin providing security policy enforcement for GitHubService."""

    def __init__(self, gh: Any, cfg: GitHubConfig) -> None:  # noqa: ANN401 — config type varies by server
        """Initialize with GitHub client and config for security guard operations."""
        self._gh = gh
        self._cfg = cfg
        self._default_per_page = cfg.default_per_page
        self._max_per_page = cfg.max_per_page

    def _clamp_per_page(self, per_page: int) -> int:
        """Clamp per_page to the configured maximum to prevent oversized API calls."""
        clamped: int = min(per_page, self._max_per_page)
        return clamped

    def _assert_allowed_repo(self, owner: str, repo: str) -> None:
        """Raise GitHubAuthorizationError if owner/repo is not permitted.

        Empty allowed_repos denies all repositories (fail-closed).
        """
        from mcp_servers.github.github_models_config import (
            GitHubAuthorizationError,
        )

        allowed = self._cfg.allowed_repos
        slug = f"{owner}/{repo}"
        if not allowed:
            raise GitHubAuthorizationError(
                f"Repository '{slug}' is denied: allowed_repos is empty"
            )
        if slug not in allowed:
            raise GitHubAuthorizationError(f"Repository not in allowed_repos: {slug}")

    def _assert_allowed_path(self, path: str) -> None:
        """Raise GitHubAuthorizationError if path matches a denied glob pattern."""
        from mcp_servers.github.github_models_config import (
            GitHubAuthorizationError,
        )

        for pattern in self._cfg.path_denylist:
            if fnmatch.fnmatch(path, pattern):
                raise GitHubAuthorizationError(
                    f"Path '{path}' is denied by path_denylist pattern '{pattern}'"
                )

    def _assert_max_file_size(self, content: str, path: str) -> None:
        """Raise GitHubValidationError if file content exceeds max_file_size_kb."""
        from mcp_servers.github.github_models_config import (
            GitHubValidationError,
        )

        max_kb = self._cfg.max_file_size_kb
        if max_kb <= 0:
            return  # 0 = disabled
        size_kb = len(content.encode("utf-8")) / 1024
        if size_kb > max_kb:
            raise GitHubValidationError(
                f"File '{path}' exceeds max_file_size_kb: {size_kb:.1f} KB > {max_kb} KB"
            )

    def _write_github_audit_log(self, op: str, **kwargs: Any) -> None:
        """Append one structured audit record to the GitHub audit log file.

        Raises GitHubAuditError when audit_log_path is configured and write fails.
        Skips silently when audit_log_path is empty.
        """
        from mcp_servers.github.github_models_config import (
            GitHubAuditError,
        )

        if not self._cfg.audit_log_path:
            return
        ts = now_iso_raw()
        fields = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
        record = f"{ts} op={op} {fields}\n"
        try:
            with open(self._cfg.audit_log_path, "a", encoding="utf-8") as fh:
                fh.write(record)
        except OSError as e:
            raise GitHubAuditError(
                f"Audit log write failed ({self._cfg.audit_log_path}): {e}"
            ) from e

    def _assert_allowed_branch(self, owner: str, repo: str, branch: str) -> None:
        """Raise GitHubAuthorizationError if branch matches a protected_branches pattern.

        Patterns follow fnmatch glob syntax: 'main' matches exactly, 'release/*'
        matches any release branch. An empty list means no branch restrictions.
        """
        from mcp_servers.github.github_models_config import (
            GitHubAuthorizationError,
        )

        for pattern in self._cfg.protected_branches:
            if fnmatch.fnmatch(branch, pattern):
                raise GitHubAuthorizationError(
                    f"Branch '{branch}' is protected in {owner}/{repo} (matches pattern '{pattern}')"
                )

    def _get_repo(self, owner: str, repo: str) -> Any:  # noqa: ANN401 — config type varies by server
        """Return a PyGithub Repository object for the given owner/repo slug."""
        return self._gh.get_repo(f"{owner}/{repo}")

    async def _resolve_and_check_branch(
        self, owner: str, repo: str, branch: str
    ) -> None:
        """Resolve the effective branch and apply protected_branches check.

        When branch is "" (unspecified), the default branch is fetched via GitHub API.
        Skips entirely when protected_branches is empty (no restrictions configured).
        """
        if not self._cfg.protected_branches:
            return
        if branch:
            self._assert_allowed_branch(owner, repo, branch)
            return
        # branch="" (unspecified): resolve default branch via GitHub API then check
        default_branch: str = await self._run_github(
            lambda: self._get_repo(owner, repo).default_branch
        )
        self._assert_allowed_branch(owner, repo, default_branch)

    @staticmethod
    def _handle_github_error(e: GithubException) -> NoReturn:
        """Convert a GithubException to a domain exception and raise it.

        Declared as NoReturn so callers do not need to write their own raise.
        """
        from mcp_servers.github.github_models_config import (
            GitHubAuthorizationError,
            GitHubConflictError,
            GitHubNotFoundError,
            GitHubUpstreamError,
            GitHubValidationError,
        )

        status_map: dict[int, type[BaseException]] = {
            HTTPStatus.NOT_FOUND: GitHubNotFoundError,
            HTTPStatus.FORBIDDEN: GitHubAuthorizationError,
            HTTPStatus.CONFLICT: GitHubConflictError,
            HTTPStatus.BAD_REQUEST: GitHubValidationError,
            HTTPStatus.UNPROCESSABLE_ENTITY: GitHubValidationError,
        }
        error_cls = status_map.get(e.status)
        if error_cls is not None:
            msg = "GitHub API error"
            if e.status == HTTPStatus.NOT_FOUND:
                msg = "Resource not found"
            elif e.status == HTTPStatus.FORBIDDEN:
                msg = "GitHub API rate limit exceeded or access denied"
            elif e.status in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY):
                msg = f"GitHub API validation error (status={e.status})"
            elif e.status == HTTPStatus.CONFLICT:
                msg = f"GitHub API conflict (status={e.status})"
            raise error_cls(msg)
        raise GitHubUpstreamError(f"GitHub API error (status={e.status})")

    async def _run_github(self, func: Callable[[], T]) -> T:
        """Run a synchronous PyGithub call in the thread pool.

        Converts GithubException to domain exceptions so endpoints stay free of
        try/except boilerplate.
        """
        try:
            return await asyncio.to_thread(func)
        except GithubException as e:
            GitHubSecurityGuards._handle_github_error(e)


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


def _audit_log_reason(cfg: GitHubConfig) -> str:
    """Return the reason code for the configured audit log path without writing to it.

    An empty path means auditing is disabled, which is the skip _write_github_audit_log()
    already performs; the posture makes that skip visible instead of changing it. A configured
    path is checked by its parent directory so validation stays side-effect free.
    """
    path = cfg.audit_log_path
    if not path:
        return REASON_NOT_APPLICABLE
    parent = os.path.dirname(path) or "."
    if not os.path.isdir(parent) or not os.access(parent, os.W_OK):
        return REASON_DEPENDENCY_UNREACHABLE
    if os.path.isdir(path):
        return REASON_DEPENDENCY_UNREACHABLE
    return REASON_OK


def validate_github_security(cfg: GitHubConfig) -> list[SecurityCheckResult]:
    """GitHub's own policy checks, in the fixed order the posture contract expects.

    Pure function of the server's own config object: no network call, no filesystem write, and
    no raise for a policy violation. Warning-only policy settings stay WARNING so a currently
    working configuration can still start, exactly as the removed Agent audit left them.

    Messages name the setting and its state. Repository identifiers and denylist patterns are
    raw allowlist values, so only their counts may appear.
    """
    if cfg.allowed_repos:
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
            "allowed_repos is empty so every repository operation is denied",
        )

    if cfg.allow_force_push:
        force_push_check = _check(
            "server.force_push_policy",
            SecurityCheckStatus.WARNING,
            REASON_FORCE_PUSH_ENABLED,
            "allow_force_push=true so destructive pushes are permitted",
        )
    else:
        force_push_check = _check(
            "server.force_push_policy",
            SecurityCheckStatus.OK,
            REASON_OK,
            "allow_force_push=false so force pushes are refused",
        )

    if cfg.require_pr_review:
        pr_review_check = _check(
            "server.pr_review_required",
            SecurityCheckStatus.OK,
            REASON_OK,
            "require_pr_review=true so the review guard is enforced",
        )
    else:
        pr_review_check = _check(
            "server.pr_review_required",
            SecurityCheckStatus.WARNING,
            REASON_DESTRUCTIVE_GUARD_MISSING,
            "require_pr_review=false so no review guard is configured",
        )

    if cfg.protected_branches:
        branch_check = _check(
            "server.protected_branches",
            SecurityCheckStatus.OK,
            REASON_OK,
            f"protected_branches is configured with {len(cfg.protected_branches)} patterns",
        )
    else:
        branch_check = _check(
            "server.protected_branches",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "protected_branches is empty so no branch restriction applies",
        )

    if cfg.path_denylist:
        path_check = _check(
            "server.path_denylist",
            SecurityCheckStatus.OK,
            REASON_OK,
            f"path_denylist is configured with {len(cfg.path_denylist)} patterns",
        )
    else:
        path_check = _check(
            "server.path_denylist",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "path_denylist is empty so no path is denied by pattern",
        )

    if cfg.max_file_size_kb > 0:
        size_check = _check(
            "server.max_file_size",
            SecurityCheckStatus.OK,
            REASON_OK,
            "max_file_size_kb is positive so oversized writes are refused",
        )
    else:
        size_check = _check(
            "server.max_file_size",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "max_file_size_kb is zero or negative so the size limit is disabled",
        )

    audit_reason = _audit_log_reason(cfg)
    audit_status = (
        SecurityCheckStatus.FAILED
        if audit_reason == REASON_DEPENDENCY_UNREACHABLE
        else SecurityCheckStatus.OK
        if audit_reason == REASON_OK
        else SecurityCheckStatus.NOT_APPLICABLE
    )
    audit_check = _check(
        "server.audit_log_writable",
        audit_status,
        audit_reason,
        {
            REASON_OK: "configured audit log path has a writable parent directory",
            REASON_DEPENDENCY_UNREACHABLE: (
                "the audit log path parent directory is missing or not writable"
            ),
            REASON_NOT_APPLICABLE: "audit_log_path is empty so audit records are not written",
        }[audit_reason],
    )

    if cfg.max_per_page <= 0 or cfg.default_per_page > cfg.max_per_page:
        per_page_check = _check(
            "server.per_page_bounds",
            SecurityCheckStatus.FAILED,
            REASON_CONFIG_INVALID,
            "max_per_page must be positive and default_per_page must not exceed it",
        )
    else:
        per_page_check = _check(
            "server.per_page_bounds",
            SecurityCheckStatus.OK,
            REASON_OK,
            "default_per_page is within max_per_page so clamping never hides a reversed bound",
        )

    return [
        repo_check,
        force_push_check,
        pr_review_check,
        branch_check,
        path_check,
        size_check,
        audit_check,
        per_page_check,
    ]
