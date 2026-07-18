#!/usr/bin/env python3
"""mcp_servers/github/service_security.py

GitHubSecurityGuards: security policy enforcement mixin for GitHubService.

Methods: _clamp_per_page, _assert_allowed_*, _write_github_audit_log,
         _resolve_and_check_branch, _get_repo, _handle_github_error, _run_github

Dependency direction: service_security → models_config, models_base, mapper
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
from collections.abc import Callable
from http import HTTPStatus
from typing import Any, NoReturn, TypeVar

from github import GithubException
from shared.json_utils import now_iso_raw

from mcp_servers.github.models_config import GitHubConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GitHubSecurityGuards:
    """Mixin providing security policy enforcement for GitHubService."""

    def __init__(self, gh: Any, cfg: GitHubConfig) -> None:  # noqa: ANN401
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
        from mcp_servers.github.models_config import (  # noqa: PLC0415
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
        from mcp_servers.github.models_config import (  # noqa: PLC0415
            GitHubAuthorizationError,
        )

        for pattern in self._cfg.path_denylist:
            if fnmatch.fnmatch(path, pattern):
                raise GitHubAuthorizationError(
                    f"Path '{path}' is denied by path_denylist pattern '{pattern}'"
                )

    def _assert_max_file_size(self, content: str, path: str) -> None:
        """Raise GitHubValidationError if file content exceeds max_file_size_kb."""
        from mcp_servers.github.models_config import (  # noqa: PLC0415
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
        from mcp_servers.github.models_config import (  # noqa: PLC0415
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
        from mcp_servers.github.models_config import (  # noqa: PLC0415
            GitHubAuthorizationError,
        )

        for pattern in self._cfg.protected_branches:
            if fnmatch.fnmatch(branch, pattern):
                raise GitHubAuthorizationError(
                    f"Branch '{branch}' is protected in {owner}/{repo} (matches pattern '{pattern}')"
                )

    def _get_repo(self, owner: str, repo: str) -> Any:  # noqa: ANN401
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
        from mcp_servers.github.models_config import (  # noqa: PLC0415
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
