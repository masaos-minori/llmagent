#!/usr/bin/env python3
"""git_helper.py

Local git repository metadata utilities using GitPython.
Returns branch and last commit info for display in /context output.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)


class FailureReason(StrEnum):
    """Reason why git repository inspection failed."""

    GITPYTHON_NOT_INSTALLED = "gitpython_not_installed"
    NOT_A_GIT_REPO = "not_a_git_repo"
    PERMISSION_DENIED = "permission_denied"
    GIT_ERROR = "git_error"
    OTHER_ERROR = "other_error"


@dataclass(frozen=True)
class RepoInfoResult:
    """Result of git repository inspection containing success flag and optional data."""

    success: bool
    data: dict[str, str] | None = None
    failure_reason: FailureReason | None = None


def get_repo_info(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # noqa: PLC0415 — lazy import keeps startup fast when gitpython is unused
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not repo.head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "message": str(head.commit.message).strip().splitlines()[0],
                "author": str(head.commit.author),
            },
        )
    except git.exc.InvalidGitRepositoryError:
        logger.debug("get_repo_info: not a git repo at %s", path)
        return _failure(FailureReason.NOT_A_GIT_REPO)
    except PermissionError as e:
        logger.debug("get_repo_info: permission error: %s", e)
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def _failure(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(success=False, failure_reason=reason)
