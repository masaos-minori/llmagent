#!/usr/bin/env python3
"""mcp/git/service.py
GitService: local git operations via GitPython with repo-path allowlist and read_only guard.

Dependency direction: git_models -> git_security -> service

Split layout:
  git_security.py — GitSecurityGuards mixin (repo-path + read-only guards)
  service.py      — GitService class + dispatch table factory + build_service
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Awaitable, Callable, Coroutine

import git

from mcp.git.models import (
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
from mcp.server import ToolArgs

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

    async def _handle_git_error(self, e: BaseException, tool_name: str) -> GitServiceError:
        """Log and wrap a git error in GitServiceError."""
        logger.error("%s error: %s", tool_name, e)
        raise GitServiceError(f"{tool_name} failed: {e}") from e

    async def _validate_and_open(self, req_repo_path: str, tool_name: str) -> RepoValidationResult:
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

        req = GitStatusRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_status")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_status", lambda: self._format_status(repo))

    def _format_status(self, repo: git.Repo) -> str:
        lines: list[str] = []
        lines.append(f"On branch {repo.active_branch.name}")
        if repo.is_dirty(untracked_files=True):
            lines.append("Changes present:")
            for item in repo.index.diff(None):
                lines.append(f"  modified: {item.a_path}")
            for item in repo.index.diff("HEAD"):
                lines.append(f"  staged:   {item.a_path}")
            for path in repo.untracked_files:
                lines.append(f"  untracked: {path}")
        else:
            lines.append("Nothing to commit, working tree clean")
        return "\n".join(lines)

    def _format_log(self, repo: git.Repo, req: GitLogRequest) -> str:
        limit = min(req.max_entries, self._max_log_entries)
        rev = req.branch or repo.head.commit
        commits = list(repo.iter_commits(rev=rev, max_count=limit))
        lines: list[str] = []
        for c in commits:
            raw_msg: str = (
                c.message.decode("utf-8", errors="replace")
                if isinstance(c.message, bytes)
                else c.message
            )
            short_msg = raw_msg.split("\n")[0][:80]
            lines.append(
                f"{c.hexsha[:8]} {c.author.name} {c.committed_datetime.strftime('%Y-%m-%d')} {short_msg}",
            )
        return "\n".join(lines) if lines else "(no commits)"

    async def git_log(self, args: ToolArgs) -> str:

        req = GitLogRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_log")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_log", lambda: self._format_log(repo, req))

    async def git_diff(self, args: ToolArgs) -> str:

        req = GitDiffRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_diff")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_diff", lambda: self._format_diff(repo, req))

    def _format_diff(self, repo: git.Repo, req: GitDiffRequest) -> str:
        if req.commit:
            diff = repo.git.diff(req.commit)
        elif req.staged:
            diff = repo.git.diff("--cached")
        else:
            diff = repo.git.diff()
        return diff or "(no diff)"

    async def git_branch(self, args: ToolArgs) -> str:

        req = GitBranchRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_branch")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_branch", lambda: self._format_branch(repo))

    def _format_branch(self, repo: git.Repo) -> str:
        current = repo.active_branch.name
        branches = [
            f"* {b.name}" if b.name == current else f"  {b.name}"
            for b in repo.branches
        ]
        return "\n".join(branches) if branches else "(no branches)"

    async def git_show(self, args: ToolArgs) -> str:

        req = GitShowRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_show")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_show", lambda: self._format_show(repo, req))

    def _format_show(self, repo: git.Repo, req: GitShowRequest) -> str:
        output: str = repo.git.show(req.ref, "--stat", "--patch")
        if len(output) > GIT_SHOW_OUTPUT_MAX_CHARS:
            return output[:GIT_SHOW_OUTPUT_MAX_CHARS]
        return output

    # ── Write tools ───────────────────────────────────────────────────────────

    async def git_add(self, args: ToolArgs) -> str:

        req = GitAddRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_add")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_add", lambda: self._format_add(repo, req))

    def _format_add(self, repo: git.Repo, req: GitAddRequest) -> str:
        if req.dry_run:
            untracked = {p for p in repo.untracked_files if p in req.paths}
            modified = {
                i.a_path for i in repo.index.diff(None) if i.a_path in req.paths
            }
            to_stage = untracked | modified
            return f"[DRY RUN] Would stage: {sorted(to_stage)}"
        repo.index.add(req.paths)
        return f"Staged: {req.paths}"

    async def git_commit(self, args: ToolArgs) -> str:

        req = GitCommitRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_commit")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_commit", lambda: self._format_commit(repo, req))

    def _format_commit(self, repo: git.Repo, req: GitCommitRequest) -> str:
        staged = [i.a_path for i in repo.index.diff("HEAD")]
        if req.dry_run:
            return f"[DRY RUN] Would commit {len(staged)} file(s): {staged}\nMessage: {req.message!r}"
        if not staged:
            raise GitServiceError("nothing staged to commit")
        commit = repo.index.commit(req.message)
        return f"Committed: {commit.hexsha[:8]} {req.message!r}"

    async def git_checkout(self, args: ToolArgs) -> str:

        req = GitCheckoutRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_checkout")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_checkout", lambda: self._format_checkout(repo, req))

    def _format_checkout(self, repo: git.Repo, req: GitCheckoutRequest) -> str:
        if req.dry_run:
            action = (
                f"create and checkout '{req.branch}'"
                if req.create
                else f"checkout '{req.branch}'"
            )
            return f"[DRY RUN] Would {action}"
        if req.create:
            new_branch = repo.create_head(req.branch)
            new_branch.checkout()
        else:
            repo.git.checkout(req.branch)
        return f"Switched to branch '{req.branch}'"

    async def git_pull(self, args: ToolArgs) -> str:

        req = GitPullRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_pull")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_pull", lambda: self._format_pull(repo, req))

    def _format_pull(self, repo: git.Repo, req: GitPullRequest) -> str:
        if req.dry_run:
            fetch_info = repo.git.fetch("--dry-run", req.remote)
            return f"[DRY RUN] fetch --dry-run result:\n{fetch_info or '(nothing to fetch)'}"
        pull_args = [req.remote]
        if req.branch:
            pull_args.append(req.branch)
        result = repo.git.pull(*pull_args)
        return result or "Already up to date."

    async def git_push(self, args: ToolArgs) -> str:

        req = GitPushRequest(**args)
        result = await self._validate_repo(req.repo_path, "git_push")
        if result.error_message:
            return result.error_message
        repo = self._open_repo(req.repo_path)
        return self._wrap_git_op("git_push", lambda: self._format_push(repo, req))

    def _format_push(self, repo: git.Repo, req: GitPushRequest) -> str:
        branch = req.branch or repo.active_branch.name
        if req.dry_run:
            return f"[DRY RUN] Would push branch '{branch}' to '{req.remote}'"
        result = repo.git.push(req.remote, branch)
        return result or f"Pushed '{branch}' to '{req.remote}'"

    # ── Dispatch table ────────────────────────────────────────────────────────

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
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
