#!/usr/bin/env python3
"""git_helper.py
Local git repository metadata utilities using GitPython.
Returns branch and last commit info for display in /context output.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_repo_info(path: str = ".") -> dict[str, Any] | None:
    """Return current branch and last commit info, or None outside a git repo; uses search_parent_directories and catches all GitPython exceptions."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused

        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        commit = head.commit
        branch = head.ref.name if not repo.head.is_detached else "HEAD (detached)"
        return {
            "branch": branch,
            "commit": commit.hexsha[:8],
            "message": commit.message.strip().splitlines()[0],
            "author": str(commit.author),
        }
    except Exception as e:
        logger.debug(f"get_repo_info: {e}")
        return None
