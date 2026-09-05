#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_service.py

GitService: local git operations via GitPython with repo-path allowlist and read_only guard.

Dependency direction: git_models -> git_security -> service
Split layout:
  git_security.py — GitSecurityGuards mixin (repo-path + read-only guards)
  service.py      — GitService class + dispatch table factory + build_service
"""

from __future__ import annotations

import dataclasses
import logging
import os
import warnings
from collections.abc import Awaitable, Callable

import git
import git.exc

from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.git_models import (
    GitAddRequest,
    GitBranchRequest,
    GitCheckoutRequest,
    GitCommitRequest,
    GitConfig,
    GitDiffRequest,
    GitLogRequest,
    GitPullRequest,
    GitPushRequest,
    GitShowRequest,
    GitStatusRequest,
)
from mcp_servers.git.git_security import _resolve_repo_path
from mcp_servers.git.repository_state import RepositoryState, WriteProtectionPipeline
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


@dataclasses.dataclass(frozen=True)
class RepoValidationResult:
    """Result of repo path and write guard validation.

    error_message is empty string when validation passes.
    """

    error_message: str

    def __post_init__(self) -> None:
        warnings.warn(
            "RepoValidationResult is deprecated; use RepositoryState instead",
            DeprecationWarning,
            stacklevel=2,
        )


# All git tool handlers catch this union; git.exc.GitError is the base for all
# GitPython exceptions; OSError covers filesystem errors; ValueError covers
# bad argument formats (e.g. invalid ref names).
_GIT_ERRORS = (git.exc.GitError, OSError, ValueError)

logger = logging.getLogger(__name__)

_WRITE_TOOLS: frozenset[str] = frozenset(
    {"git_add", "git_commit", "git_checkout", "git_pull", "git_push"},
)


class GitService:
    """Executes local git operations against an allowlisted set of repositories."""

    def __init__(
        self,
        allowed_repo_paths: list[str],
        read_only: bool = True,
        max_log_entries: int = 50,
        protected_branches: list[str] | None = None,
        allow_detached_head: bool = False,
        _config: GitConfig | None = None,
    ) -> None:
        """Initialize with security guards and configuration parameters."""
        self._allowed_repo_paths = allowed_repo_paths
        self._read_only = read_only
        self._protected_branches = protected_branches or []
        self._allow_detached_head = allow_detached_head
        self._max_log_entries = max_log_entries
        self._config = _config

    def _open_repo(self, repo_path: str) -> git.Repo:
        """Open a git.Repo at repo_path; raises git.InvalidGitRepositoryError on failure."""
        return git.Repo(repo_path, search_parent_directories=False)

    async def _validate_repo(
        self, req_repo_path: str, tool_name: str
    ) -> RepoValidationResult:
        """Check repo_path and write guard; return result with error_message (empty on success)."""
        if not any(req_repo_path.startswith(p) for p in self._allowed_repo_paths):
            return RepoValidationResult(
                error_message="[DENIED] repo_path not in allowed paths"
            )
        if tool_name in _WRITE_TOOLS and self._read_only:
            return RepoValidationResult(
                error_message="[DENIED] git-mcp is configured with read_only=true"
            )
        return RepoValidationResult(error_message="")

    def _validate_ref(self, ref: str) -> tuple[bool, str]:
        """Check if a ref is safe (not an option)."""
        if not ref:
            return True, ""
        if ref.startswith("-"):
            return False, f"[DENIED] Ref {ref!r} looks like a CLI option"
        return True, ""

    def _validate_protected(self, branch: str) -> tuple[bool, str]:
        """Check if a branch is protected."""
        if not branch:
            return False, "[DENIED] branch must not be empty"
        if branch in self._protected_branches:
            return False, "[DENIED] branch is a protected branch"
        return True, ""

    # ── Backward-compatible guards (used by tests) ────────────────────────────

    def _check_repo_path(self, repo_path: str) -> tuple[bool, str, str]:
        """Return (ok, error, resolved_path).

        ok=True when repo_path is within an allowed path prefix.
        When ok=True, resolved_path contains the canonical (symlink-resolved) path.
        When ok=False, resolved_path is empty string.
        """
        from pathlib import PurePosixPath

        ok, err, resolved = _resolve_repo_path(repo_path)
        if not ok:
            return False, err, ""
        normalized = os.path.normpath(resolved)
        for allowed in self._allowed_repo_paths:
            try:
                PurePosixPath(normalized).relative_to(PurePosixPath(allowed))
                return True, "", resolved
            except ValueError:
                continue
        return False, "[DENIED] repo_path not in allowed paths", ""

    def _check_write(self) -> tuple[bool, str]:
        """Return (ok, error); ok=True when write operations are permitted."""
        if self._read_only:
            return False, "[DENIED] git-mcp is configured with read_only=true"
        return True, ""

    def _is_safe_ref(self, ref: str) -> bool:
        """Return True if ref is safe (not a CLI option)."""
        return not ref.startswith("-")

    def _check_protected_branch(self, branch: str) -> tuple[bool, str]:
        """Return (ok, error); ok=True if branch is NOT protected."""
        if branch in self._protected_branches:
            return False, "[DENIED] 'main' is a protected branch"
        return True, ""

    def _wrap_git_op(self, tool_name: str, func: Callable[[], str]) -> str:
        """Execute a git operation with error wrapping."""
        try:
            return func()
        except _GIT_ERRORS as e:
            logger.error("%s error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

    async def _run_tool(
        self,
        tool_name: str,
        repo_path: str,
        op: Callable[[git.Repo, RepositoryState], str],
        active_ref: str = "",
    ) -> str:
        """Validate repo/write guards, open the repo, and run op with error wrapping.

        Shared by every git_* handler below: build the request model, then
        delegate validation + repo opening + error wrapping to this helper.
        """
        result = await self._validate_repo(repo_path, tool_name)
        if result.error_message:
            return result.error_message
        state = RepositoryState.snapshot(repo_path, active_ref=active_ref)
        pipeline = WriteProtectionPipeline(state)
        pipeline_result = pipeline.run(tool_name, lambda: op(state.repo, state))
        if pipeline_result.ok:
            return pipeline_result.output
        return pipeline_result.rejection_message

    # ── Read-only tools ───────────────────────────────────────────────────────

    async def git_status(self, args: ToolArgs) -> str:
        """Return the current status of files in the repository."""
        req = GitStatusRequest(repo_path=args["repo_path"])
        return await self._run_tool(
            "git_status", req.repo_path, lambda repo, _state: format_status(repo)
        )

    async def git_log(self, args: ToolArgs) -> str:
        """Return recent commit log entries for the repository."""
        req = GitLogRequest(
            repo_path=args["repo_path"],
            max_entries=args.get("max_entries", 20),
            branch=args.get("branch", ""),
        )
        ok, err = self._validate_ref(req.branch)
        if not ok:
            return err
        return await self._run_tool(
            "git_log",
            req.repo_path,
            lambda repo, _state: format_log(repo, req, self._max_log_entries),
        )

    async def git_diff(self, args: ToolArgs) -> str:
        """Return the diff between working tree and index or two commits."""
        req = GitDiffRequest(
            repo_path=args["repo_path"],
            staged=args.get("staged", False),
            commit=args.get("commit", ""),
        )
        ok, err = self._validate_ref(req.commit)
        if not ok:
            return err
        return await self._run_tool(
            "git_diff", req.repo_path, lambda repo, _state: format_diff(repo, req)
        )

    async def git_branch(self, args: ToolArgs) -> str:
        """List branches in the repository."""
        req = GitBranchRequest(repo_path=args["repo_path"])
        return await self._run_tool(
            "git_branch", req.repo_path, lambda repo, _state: format_branch(repo)
        )

    async def git_show(self, args: ToolArgs) -> str:
        """Show details of a commit, blob, or tree object."""
        req = GitShowRequest(
            repo_path=args["repo_path"],
            ref=args.get("ref", "HEAD"),
        )
        ok, err = self._validate_ref(req.ref)
        if not ok:
            return err
        return await self._run_tool(
            "git_show", req.repo_path, lambda repo, _state: format_show(repo, req)
        )

    # ── Write tools ───────────────────────────────────────────────────────────

    async def git_add(self, args: ToolArgs) -> str:
        """Stage files for commit."""
        req = GitAddRequest(
            repo_path=args["repo_path"],
            paths=args["paths"],
            dry_run=args.get("dry_run", False),
        )
        return await self._run_tool(
            "git_add", req.repo_path, lambda repo, _state: format_add(repo, req)
        )

    async def git_commit(self, args: ToolArgs) -> str:
        """Create a new commit from staged changes."""
        req = GitCommitRequest(
            repo_path=args["repo_path"],
            message=args["message"],
            dry_run=args.get("dry_run", False),
        )
        return await self._run_tool(
            "git_commit", req.repo_path, lambda repo, _state: format_commit(repo, req)
        )

    async def git_checkout(self, args: ToolArgs) -> str:
        """Switch branches or restore working tree files."""
        req = GitCheckoutRequest(
            repo_path=args["repo_path"],
            branch=args["branch"],
            create=args.get("create", False),
            dry_run=args.get("dry_run", False),
        )
        ok, err = self._validate_ref(req.branch)
        if not ok:
            return err
        ok, err = self._validate_protected(req.branch)
        if not ok:
            return err

        def _checkout_op(repo: git.Repo, state: RepositoryState) -> str:
            if not req.dry_run:
                if state.is_dirty:
                    return "[DENIED] worktree has uncommitted changes (dirty worktree)"
                if state.is_detached_head and not self._allow_detached_head:
                    return "[DENIED] repository is in a detached HEAD state"
            return format_checkout(
                state, req, allow_detached_head=self._allow_detached_head
            )

        return await self._run_tool(
            "git_checkout", req.repo_path, _checkout_op, active_ref=req.branch
        )

    async def git_pull(self, args: ToolArgs) -> str:
        """Fetch and merge changes from a remote repository."""
        req = GitPullRequest(
            repo_path=args["repo_path"],
            remote=args.get("remote", "origin"),
            branch=args.get("branch", ""),
            dry_run=args.get("dry_run", False),
        )
        ok, err = self._validate_ref(req.branch)
        if not ok:
            return err
        ok, err = self._validate_protected(req.branch)
        if not ok:
            return err
        ok, err = self._validate_ref(req.remote)
        if not ok:
            return err

        def _pull_op(repo: git.Repo, state: RepositoryState) -> str:
            if not req.dry_run:
                if state.is_dirty:
                    return "[DENIED] worktree has uncommitted changes (dirty worktree)"
                if state.is_detached_head and not self._allow_detached_head:
                    return "[DENIED] repository is in a detached HEAD state"
            return format_pull(state, req)

        return await self._run_tool(
            "git_pull", req.repo_path, _pull_op, active_ref=req.branch
        )

    async def git_push(self, args: ToolArgs) -> str:
        """Push local commits to a remote repository."""
        req = GitPushRequest(
            repo_path=args["repo_path"],
            remote=args.get("remote", "origin"),
            branch=args.get("branch", ""),
            dry_run=args.get("dry_run", False),
        )
        ok, err = self._validate_ref(req.branch)
        if not ok:
            return err
        ok, err = self._validate_protected(req.branch)
        if not ok:
            return err
        ok, err = self._validate_ref(req.remote)
        if not ok:
            return err

        def _push_op(repo: git.Repo, state: RepositoryState) -> str:
            if not req.dry_run:
                if state.is_dirty:
                    return "[DENIED] worktree has uncommitted changes (dirty worktree)"
                if state.is_detached_head and not self._allow_detached_head:
                    return "[DENIED] repository is in a detached HEAD state"
            return format_push(state, req)

        return await self._run_tool(
            "git_push", req.repo_path, _push_op, active_ref=req.branch
        )

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
    protected_branches = list(cfg.protected_branches)
    allow_detached_head = bool(cfg.allow_detached_head)
    if read_only:
        logger.info("git-mcp: read_only=true — write tools are disabled")
    if not allowed:
        logger.warning("git-mcp: allowed_repo_paths is empty — all repo access denied")
    return GitService(
        allowed_repo_paths=allowed,
        read_only=read_only,
        max_log_entries=max_log,
        protected_branches=protected_branches,
        allow_detached_head=allow_detached_head,
        _config=cfg,
    )
