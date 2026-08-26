#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_security.py

Shared security guards for GitService: repo-path allowlist, read-only check, and protected-branch enforcement.
"""

from __future__ import annotations

from pathlib import Path

import git


def _repo_denied_msg(repo_path: str) -> str:
    """Build a denial message for unauthorized repository paths."""
    return f"[DENIED] repo_path {repo_path!r} is not in allowed_repo_paths"


class GitSecurityGuards:
    """Repository access and write-permission guards.
    Mixed into GitService via inheritance so tests can still call
    svc._check_repo_path() and svc._check_write().
    """

    def __init__(
        self,
        allowed_repo_paths: list[str],
        read_only: bool,
        protected_branches: list[str] | None = None,
        allow_detached_head: bool = False,
    ) -> None:
        """Initialize the security mixin with allowed repository paths, read-only flag, and protected branches."""
        self._allowed: list[Path] = [Path(p).resolve() for p in allowed_repo_paths]
        self._read_only = read_only
        self._protected_branches = protected_branches or []
        self._allow_detached_head = allow_detached_head

    def _check_repo_path(self, repo_path: str) -> tuple[bool, str]:
        """Return (ok, error); ok=True when repo_path is within an allowed path prefix."""
        if not self._allowed:
            return False, _repo_denied_msg(repo_path)
        target = Path(repo_path).resolve()
        for allowed in self._allowed:
            if target.is_relative_to(allowed):
                return True, ""
        return False, _repo_denied_msg(repo_path)

    def _check_write(self) -> tuple[bool, str]:
        """Return (ok, error); ok=True when write operations are permitted."""
        if self._read_only:
            return False, "[DENIED] git-mcp is configured with read_only=true"
        return True, ""

    def _is_safe_ref(self, ref: str) -> bool:
        """Return True if ref does not look like a CLI option (doesn't start with '-')."""
        return not ref.startswith("-")

    def _check_protected_branch(self, branch: str) -> tuple[bool, str]:
        """Return (ok, error); ok=True if branch is NOT in protected_branches."""
        if branch in self._protected_branches:
            return False, f"[DENIED] {branch!r} is a protected branch"
        return True, ""

    def _check_dirty_worktree(self, repo: git.Repo) -> tuple[bool, str]:
        """Return (ok, error); ok=True when worktree has no uncommitted changes."""
        if repo.is_dirty(untracked_files=True):
            return (
                False,
                "[DENIED] worktree has uncommitted changes (dirty worktree) — commit, stash, or discard changes first",
            )
        return True, ""

    def _check_detached_head(self, repo: git.Repo) -> tuple[bool, str]:
        """Return (ok, error); ok=True when HEAD is attached or allow_detached_head is True."""
        if repo.head.is_detached and not self._allow_detached_head:
            return (
                False,
                "[DENIED] repository is in a detached HEAD state — checkout a branch first, or set allow_detached_head=true in git_mcp_server.toml",
            )
        return True, ""
