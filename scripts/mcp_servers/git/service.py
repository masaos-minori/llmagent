#!/usr/bin/env python3
"""mcp_servers/git/service.py

GitService: local git operations via GitPython with repo-path allowlist and read_only guard.

Dependency direction: git_models -> git_security -> service

Split layout:
  git_security.py — GitSecurityGuards mixin (repo-path + read-only guards)
  service.py      — GitService class + dispatch table factory + build_service
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Awaitable, Callable

import git

from mcp_servers.git.models import (
    GitAddRequest,
    GitBranchRequest,
    GitCheckoutRequest,
    GitCommitRequest,
    GitConfig,
    GitDiffRequest,
    GitLogRequest,
    GitPullRequest,
    GitPushRequest,
    GitServiceError,
    GitShowRequest,
    GitStatusRequest,
)
from mcp_servers.server import ToolArgs

from .format_output import (
    format_add,
    format_branch,
    format_checkout,
    format_commit,
    format_diff,
    format_log,
    format_pull,
    format_push,
    format_show,
    format_status,
)
from .git_security import GitSecurityGuards


@dataclasses.dataclass(frozen=True)
class RepoValidationResult:
    """Result of repo path and write guard validation.

    error_message is empty string when validation passes.
    """

    error_message: str


# All git tool handlers catch this union; git.exc.GitError is the base for all
# GitPython exceptions; OSError covers filesystem errors; ValueError covers
# bad argument formats (e.g. invalid ref names).
_GIT_ERRORS = (git.exc.GitError, OSError, ValueError)

logger = logging.getLogger(__name__)

GIT_SHOW_OUTPUT_MAX_CHARS = 8000

_WRITE_TOOLS: frozenset[str] = frozenset(
    {"git_add", "git_commit", "git_checkout", "git_pull", "git_push"},
)


class GitService(GitSecurityGuards):
    """Executes local git operations against an allowlisted set of repositories."""

    def __init__(
        self,
        allowed_repo_paths: list[str],
        read_only: bool = True,
        max_log_entries: int = 50,
    ) -> None:
        GitSecurityGuards.__init__(self, allowed_repo_paths, read_only)
        self._max_log_entries = max_log_entries

    def _open_repo(self, repo_path: str) -> git.Repo:
        """Open a git.Repo at repo_path; raises git.InvalidGitRepositoryError on failure."""
        return git.Repo(repo_path, search_parent_directories=False)

    async def _validate_repo(
        self, req_repo_path: str, tool_name: str
    ) -> RepoValidationResult:
        """Check repo_path and write guard; return result with error_message (empty on success)."""
        ok, err = self._check_repo_path(req_repo_path)
        if not ok:
            return RepoValidationResult(error_message=err)
        if tool_name in _WRITE_TOOLS:
            ok, err = self._check_write()
            if not ok:
                return RepoValidationResult(error_message=err)
        return RepoValidationResult(error_message="")

    async def _handle_git_error(
        self, e: BaseException, tool_name: str
    ) -> GitServiceError:
        """Log and wrap a git error in GitServiceError."""
        logger.error("%s error: %s", tool_name, e)
        raise GitServiceError(f"{tool_name} failed: {e}") from e

    async def _validate_and_open(
        self, req_repo_path: str, tool_name: str
    ) -> RepoValidationResult:
        """Validate repo and write guard; return early error or empty result."""
        result = await self._validate_repo(req_repo_path, tool_name)
        if result.error_message:
            return result
        return RepoValidationResult(error_message="")

    def _wrap_git_op(self, tool_name: str, func: Callable[[], str]) -> str:
        """Execute a git operation with error wrapping."""
        try:
            return func()
        except _GIT_ERRORS as e:
            logger.error("%s error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

    # ── Read-only tools ───────────────────────────────────────────────────────

    async def git_status(self, args: ToolArgs) -> str:
        """Return the current status of files in the repository."""
        req = GitStatusRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_status")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_status", lambda: format_status(repo))

    async def git_log(self, args: ToolArgs) -> str:
        """Return recent commit log entries for the repository."""
        req = GitLogRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_log")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op(
            "git_log", lambda: format_log(repo, req, self._max_log_entries)
        )

    async def git_diff(self, args: ToolArgs) -> str:
        """Return the diff between working tree and index or two commits."""
        req = GitDiffRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_diff")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_diff", lambda: format_diff(repo, req))

    async def git_branch(self, args: ToolArgs) -> str:
        """List branches in the repository."""
        req = GitBranchRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_branch")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_branch", lambda: format_branch(repo))

    async def git_show(self, args: ToolArgs) -> str:
        """Show details of a commit, blob, or tree object."""
        req = GitShowRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_show")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_show", lambda: format_show(repo, req))

    # ── Write tools ───────────────────────────────────────────────────────────

    async def git_add(self, args: ToolArgs) -> str:
        """Stage files for commit."""
        req = GitAddRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_add")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_add", lambda: format_add(repo, req))

    async def git_commit(self, args: ToolArgs) -> str:
        """Create a new commit from staged changes."""
        req = GitCommitRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_commit")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_commit", lambda: format_commit(repo, req))

    async def git_checkout(self, args: ToolArgs) -> str:
        """Switch branches or restore working tree files."""
        req = GitCheckoutRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_checkout")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_checkout", lambda: format_checkout(repo, req))

    async def git_pull(self, args: ToolArgs) -> str:
        """Fetch and merge changes from a remote repository."""
        req = GitPullRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_pull")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_pull", lambda: format_pull(repo, req))

    async def git_push(self, args: ToolArgs) -> str:
        """Push local commits to a remote repository."""
        req = GitPushRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_push")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_push", lambda: format_push(repo, req))

    # ── Dispatch table ────────────────────────────────────────────────────────

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Return the dispatch table mapping tool names to handler methods."""
        return {
            "git_status": self.git_status,
            "git_log": self.git_log,
            "git_diff": self.git_diff,
            "git_branch": self.git_branch,
            "git_show": self.git_show,
            "git_add": self.git_add,
            "git_commit": self.git_commit,
            "git_checkout": self.git_checkout,
            "git_pull": self.git_pull,
            "git_push": self.git_push,
        }


def build_service(cfg: GitConfig) -> GitService:
    """Construct GitService from a typed GitConfig (injected by server.py)."""
    allowed = list(cfg.allowed_repo_paths)
    read_only = bool(cfg.read_only)
    max_log = int(cfg.max_log_entries)
    if read_only:
        logger.info("git-mcp: read_only=true — write tools are disabled")
    if not allowed:
        logger.warning("git-mcp: allowed_repo_paths is empty — all repo access denied")
    return GitService(
        allowed_repo_paths=allowed,
        read_only=read_only,
        max_log_entries=max_log,
    )
