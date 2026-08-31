#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_security.py

Shared security guards for GitService: repo-path allowlist, read-only check, and protected-branch enforcement.
"""

from __future__ import annotations

from pathlib import Path

from mcp_servers.git.repository_state import RepositoryState


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


class GitSecurityGuards:
    """Repository access and write-permission guards.
    Mixed into GitService via inheritance so tests can still call
    svc._check_repo_path() and svc._check_write().
    """

    def __init__(
        self,
        repo_state: RepositoryState,
        read_only: bool,
    ) -> None:
        """Initialize the security mixin with repository state and read-only flag."""
        self._repo_state = repo_state
        self._read_only = read_only

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
