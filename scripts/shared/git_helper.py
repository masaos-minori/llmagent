#!/usr/bin/env python3
"""git_helper.py
Local git repository metadata utilities using GitPython.
Returns branch and last commit info for display in /context output.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_repo_info(path: str = ".") -> dict[str, str] | None:
    """Return current branch and last commit info, or None outside a git repo."""
    try:
        import git  # noqa: PLC0415 — lazy import keeps startup fast when gitpython is unused

        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not repo.head.is_detached else "HEAD (detached)"
        return {
            "branch": branch,
            "commit": head.commit.hexsha[:8],
            "message": str(head.commit.message).strip().splitlines()[0],
            "author": str(head.commit.author),
        }
    except (ImportError, ValueError, OSError) as e:
        logger.debug("get_repo_info: %s", e)
        return None
