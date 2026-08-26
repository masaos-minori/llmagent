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
from collections.abc import Awaitable, Callable

import git
import git.exc

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
        protected_branches: list[str] | None = None,
        allow_detached_head: bool = False,
    ) -> None:
        """Initialize with security guards and configuration parameters."""
        GitSecurityGuards.__init__(
            self,
            allowed_repo_paths,
            read_only,
            protected_branches or [],
            allow_detached_head,
        )
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

    def _validate_ref(self, ref: str) -> tuple[bool, str]:
        """Check if a ref is safe (not an option)."""
        if not ref:
            return True, ""
        if not self._is_safe_ref(ref):
            return False, f"[DENIED] Ref {ref!r} looks like a CLI option"
        return True, ""

    def _validate_protected(self, branch: str) -> tuple[bool, str]:
        """Check if a branch is protected."""
        if not branch:
            return True, ""
        return self._check_protected_branch(branch)

    def _wrap_git_op(self, tool_name: str, func: Callable[[], str]) -> str:
        """Execute a git operation with error wrapping."""
        try:
            return func()
        except _GIT_ERRORS as e:
            logger.error("%s error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

    async def _run_tool(
        self, tool_name: str, repo_path: str, op: Callable[[git.Repo], str]
    ) -> str:
        """Validate repo/write guards, open the repo, and run op with error wrapping.

        Shared by every git_* handler below: build the request model, then
        delegate validation + repo opening + error wrapping to this helper.
        """
        result = await self._validate_repo(repo_path, tool_name)
        if result.error_message:
            return result.error_message
        repo = self._open_repo(repo_path)
        return self._wrap_git_op(tool_name, lambda: op(repo))

    # ── Read-only tools ───────────────────────────────────────────────────────

    async def git_status(self, args: ToolArgs) -> str:
        """Return the current status of files in the repository."""
        req = GitStatusRequest(repo_path=args["repo_path"])
        return await self._run_tool(
            "git_status", req.repo_path, lambda repo: format_status(repo)
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
            lambda repo: format_log(repo, req, self._max_log_entries),
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
            "git_diff", req.repo_path, lambda repo: format_diff(repo, req)
        )

    async def git_branch(self, args: ToolArgs) -> str:
        """List branches in the repository."""
        req = GitBranchRequest(repo_path=args["repo_path"])
        return await self._run_tool(
            "git_branch", req.repo_path, lambda repo: format_branch(repo)
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
            "git_show", req.repo_path, lambda repo: format_show(repo, req)
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
            "git_add", req.repo_path, lambda repo: format_add(repo, req)
        )

    async def git_commit(self, args: ToolArgs) -> str:
        """Create a new commit from staged changes."""
        req = GitCommitRequest(
            repo_path=args["repo_path"],
            message=args["message"],
            dry_run=args.get("dry_run", False),
        )
        return await self._run_tool(
            "git_commit", req.repo_path, lambda repo: format_commit(repo, req)
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

        def _checkout_op(repo: git.Repo) -> str:
            if not req.dry_run:
                ok, err = self._check_dirty_worktree(repo)
                if not ok:
                    return err
                ok, err = self._check_detached_head(repo)
                if not ok:
                    return err
            return format_checkout(
                repo, req, allow_detached_head=self._allow_detached_head
            )

        return await self._run_tool("git_checkout", req.repo_path, _checkout_op)

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

        def _pull_op(repo: git.Repo) -> str:
            if not req.dry_run:
                ok, err = self._check_dirty_worktree(repo)
                if not ok:
                    return err
                ok, err = self._check_detached_head(repo)
                if not ok:
                    return err
            return format_pull(repo, req)

        return await self._run_tool("git_pull", req.repo_path, _pull_op)

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
        return await self._run_tool(
            "git_push", req.repo_path, lambda repo: format_push(repo, req)
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
    )
