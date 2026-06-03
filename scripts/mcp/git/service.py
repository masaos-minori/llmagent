#!/usr/bin/env python3
"""mcp/git/service.py
GitService: local git operations via GitPython with repo-path allowlist and read_only guard.

Security guards:
  - allowed_repo_paths: only listed absolute path prefixes are accessible (empty = deny all)
  - read_only: when True, all write tools (add/commit/checkout/pull/push) are rejected
  - dry_run: supported by all write tools; returns preview without side effects
  - max_log_entries: caps git_log output to prevent large dumps
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

import git

from mcp.server import ToolArgs

# All git tool handlers catch this union; git.exc.GitError is the base for all
# GitPython exceptions; OSError covers filesystem errors; ValueError covers
# bad argument formats (e.g. invalid ref names).
_GIT_ERRORS = (git.exc.GitError, OSError, ValueError)

logger = logging.getLogger(__name__)

_WRITE_TOOLS: frozenset[str] = frozenset(
    {"git_add", "git_commit", "git_checkout", "git_pull", "git_push"},
)


def _repo_denied_msg(repo_path: str) -> str:
    return f"[DENIED] repo_path {repo_path!r} is not in allowed_repo_paths"


class GitService:
    """Executes local git operations against an allowlisted set of repositories."""

    def __init__(
        self,
        allowed_repo_paths: list[str],
        read_only: bool = True,
        max_log_entries: int = 50,
    ) -> None:
        # Normalize to resolved absolute paths for consistent comparison.
        self._allowed: list[Path] = [Path(p).resolve() for p in allowed_repo_paths]
        self._read_only = read_only
        self._max_log_entries = max_log_entries

    # ── Guards ────────────────────────────────────────────────────────────────

    def _check_repo_path(self, repo_path: str) -> tuple[bool, str]:
        """Return (ok, error); ok=True when repo_path is within an allowed path prefix."""
        if not self._allowed:
            return False, _repo_denied_msg(repo_path)
        target = Path(repo_path).resolve()
        for allowed in self._allowed:
            try:
                target.relative_to(allowed)
                return True, ""
            except ValueError:
                continue
        return False, _repo_denied_msg(repo_path)

    def _check_write(self) -> tuple[bool, str]:
        """Return (ok, error); ok=True when write operations are permitted."""
        if self._read_only:
            return False, "[DENIED] git-mcp is configured with read_only=true"
        return True, ""

    def _open_repo(self, repo_path: str) -> git.Repo:
        """Open a git.Repo at repo_path; raises git.InvalidGitRepositoryError on failure."""
        return git.Repo(repo_path, search_parent_directories=False)

    # ── Read-only tools ───────────────────────────────────────────────────────

    async def git_status(self, args: ToolArgs) -> str:
        from mcp.git.models import GitStatusRequest  # noqa: PLC0415

        req = GitStatusRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
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
        except _GIT_ERRORS as e:
            logger.error(f"git_status error: {e}")
            return f"[ERROR] git_status: {e}"

    async def git_log(self, args: ToolArgs) -> str:
        from mcp.git.models import GitLogRequest  # noqa: PLC0415

        req = GitLogRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
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
        except _GIT_ERRORS as e:
            logger.error(f"git_log error: {e}")
            return f"[ERROR] git_log: {e}"

    async def git_diff(self, args: ToolArgs) -> str:
        from mcp.git.models import GitDiffRequest  # noqa: PLC0415

        req = GitDiffRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
            if req.commit:
                diff = repo.git.diff(req.commit)
            elif req.staged:
                diff = repo.git.diff("--cached")
            else:
                diff = repo.git.diff()
            return diff or "(no diff)"
        except _GIT_ERRORS as e:
            logger.error(f"git_diff error: {e}")
            return f"[ERROR] git_diff: {e}"

    async def git_branch(self, args: ToolArgs) -> str:
        from mcp.git.models import GitBranchRequest  # noqa: PLC0415

        req = GitBranchRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
            current = repo.active_branch.name
            branches = [
                f"* {b.name}" if b.name == current else f"  {b.name}"
                for b in repo.branches
            ]
            return "\n".join(branches) if branches else "(no branches)"
        except _GIT_ERRORS as e:
            logger.error(f"git_branch error: {e}")
            return f"[ERROR] git_branch: {e}"

    async def git_show(self, args: ToolArgs) -> str:
        from mcp.git.models import GitShowRequest  # noqa: PLC0415

        req = GitShowRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
            output: str = repo.git.show(req.ref, "--stat", "--patch")
            return output[:8000] if len(output) > 8000 else output
        except _GIT_ERRORS as e:
            logger.error(f"git_show error: {e}")
            return f"[ERROR] git_show: {e}"

    # ── Write tools ───────────────────────────────────────────────────────────

    async def git_add(self, args: ToolArgs) -> str:
        from mcp.git.models import GitAddRequest  # noqa: PLC0415

        req = GitAddRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        ok, err = self._check_write()
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
            if req.dry_run:
                untracked = {p for p in repo.untracked_files if p in req.paths}
                modified = {
                    i.a_path for i in repo.index.diff(None) if i.a_path in req.paths
                }
                to_stage = untracked | modified
                return f"[DRY RUN] Would stage: {sorted(to_stage)}"
            repo.index.add(req.paths)
            return f"Staged: {req.paths}"
        except _GIT_ERRORS as e:
            logger.error(f"git_add error: {e}")
            return f"[ERROR] git_add: {e}"

    async def git_commit(self, args: ToolArgs) -> str:
        from mcp.git.models import GitCommitRequest  # noqa: PLC0415

        req = GitCommitRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        ok, err = self._check_write()
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
            staged = [i.a_path for i in repo.index.diff("HEAD")]
            if req.dry_run:
                return f"[DRY RUN] Would commit {len(staged)} file(s): {staged}\nMessage: {req.message!r}"
            if not staged:
                return "[ERROR] Nothing staged to commit"
            commit = repo.index.commit(req.message)
            return f"Committed: {commit.hexsha[:8]} {req.message!r}"
        except _GIT_ERRORS as e:
            logger.error(f"git_commit error: {e}")
            return f"[ERROR] git_commit: {e}"

    async def git_checkout(self, args: ToolArgs) -> str:
        from mcp.git.models import GitCheckoutRequest  # noqa: PLC0415

        req = GitCheckoutRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        ok, err = self._check_write()
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
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
        except _GIT_ERRORS as e:
            logger.error(f"git_checkout error: {e}")
            return f"[ERROR] git_checkout: {e}"

    async def git_pull(self, args: ToolArgs) -> str:
        from mcp.git.models import GitPullRequest  # noqa: PLC0415

        req = GitPullRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        ok, err = self._check_write()
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
            if req.dry_run:
                fetch_info = repo.git.fetch("--dry-run", req.remote)
                return f"[DRY RUN] fetch --dry-run result:\n{fetch_info or '(nothing to fetch)'}"
            pull_args = [req.remote]
            if req.branch:
                pull_args.append(req.branch)
            result = repo.git.pull(*pull_args)
            return result or "Already up to date."
        except _GIT_ERRORS as e:
            logger.error(f"git_pull error: {e}")
            return f"[ERROR] git_pull: {e}"

    async def git_push(self, args: ToolArgs) -> str:
        from mcp.git.models import GitPushRequest  # noqa: PLC0415

        req = GitPushRequest(**args)
        ok, err = self._check_repo_path(req.repo_path)
        if not ok:
            return err
        ok, err = self._check_write()
        if not ok:
            return err
        try:
            repo = self._open_repo(req.repo_path)
            branch = req.branch or repo.active_branch.name
            if req.dry_run:
                return f"[DRY RUN] Would push branch '{branch}' to '{req.remote}'"
            result = repo.git.push(req.remote, branch)
            return result or f"Pushed '{branch}' to '{req.remote}'"
        except _GIT_ERRORS as e:
            logger.error(f"git_push error: {e}")
            return f"[ERROR] git_push: {e}"

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


def build_service(cfg: dict) -> GitService:
    """Construct GitService from a config dict (injected by server.py)."""
    allowed = list(cfg.get("allowed_repo_paths", []))
    read_only = bool(cfg.get("read_only", True))
    max_log = int(cfg.get("max_log_entries", 50))
    if read_only:
        logger.info("git-mcp: read_only=true — write tools are disabled")
    if not allowed:
        logger.warning("git-mcp: allowed_repo_paths is empty — all repo access denied")
    return GitService(
        allowed_repo_paths=allowed,
        read_only=read_only,
        max_log_entries=max_log,
    )
