#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_security.py

Shared security guards for GitService: repo-path allowlist, read-only check, and protected-branch enforcement.
"""

from __future__ import annotations

import os
from pathlib import Path

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

    ok, err, resolved = _resolve_repo_path(repo_path)
    if not ok:
        return False, err

    normalized = os.path.normpath(resolved)

    # Fail-closed-empty-list convention: callers must enforce non-empty
    # allowed_repo_paths before calling this function.
    if not allowed_repo_paths:
        return True, ""

    for allowed in allowed_repo_paths:
        try:
            PurePosixPath(normalized).relative_to(PurePosixPath(allowed))
            return True, ""
        except ValueError:
            continue

    return False, "[DENIED] repo_path not in allowed paths"


class GitSecurityGuards:
    """Repository access and write-permission guards.
    Mixed into GitService via inheritance so tests can still call
    svc._check_repo_path() and svc._check_write().
    """

    def __init__(
        self,
        repo_state: repository_state.RepositoryState,
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
