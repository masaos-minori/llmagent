#!/usr/bin/env python3
"""mcp_servers/git/git_security.py

Shared security guards for GitService: repo-path allowlist and read-only check.

Extracted from git/service.py to reduce file size.
"""

from __future__ import annotations

from pathlib import Path


def _repo_denied_msg(repo_path: str) -> str:
    """Build a denial message for unauthorized repository paths."""
    return f"[DENIED] repo_path {repo_path!r} is not in allowed_repo_paths"


class GitSecurityGuards:
    """Repository access and write-permission guards.

    Mixed into GitService via inheritance so tests can still call
    svc._check_repo_path() and svc._check_write().
    """

    def __init__(self, allowed_repo_paths: list[str], read_only: bool) -> None:
        self._allowed: list[Path] = [Path(p).resolve() for p in allowed_repo_paths]
        self._read_only = read_only

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
