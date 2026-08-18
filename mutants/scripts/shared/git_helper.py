#!/usr/bin/env python3
"""scripts/shared/git_helper.py

Local git repository metadata utilities using GitPython.
Returns branch and last commit info for display in /context output.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


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
mutants_x_get_repo_info__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_repo_info__mutmut)
def get_repo_info(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_orig(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_1(path: str = "XX.XX") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_2(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug(None)
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_3(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("XXget_repo_info: GitPython not installedXX")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_4(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: gitpython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_5(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("GET_REPO_INFO: GITPYTHON NOT INSTALLED")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_6(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(None)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_7(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = None
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_8(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(None, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_9(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=None)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_10(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_11(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, )
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_12(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=False)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_13(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = None
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_14(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = None
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


def x_get_repo_info__mutmut_15(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if head.is_detached else "HEAD (detached)"
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


def x_get_repo_info__mutmut_16(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "XXHEAD (detached)XX"
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


def x_get_repo_info__mutmut_17(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "head (detached)"
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


def x_get_repo_info__mutmut_18(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (DETACHED)"
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


def x_get_repo_info__mutmut_19(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=None,
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


def x_get_repo_info__mutmut_20(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data=None,
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


def x_get_repo_info__mutmut_21(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
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


def x_get_repo_info__mutmut_22(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
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


def x_get_repo_info__mutmut_23(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=False,
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


def x_get_repo_info__mutmut_24(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "XXbranchXX": branch,
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


def x_get_repo_info__mutmut_25(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "BRANCH": branch,
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


def x_get_repo_info__mutmut_26(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "XXcommitXX": head.commit.hexsha[:8],
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


def x_get_repo_info__mutmut_27(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "COMMIT": head.commit.hexsha[:8],
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


def x_get_repo_info__mutmut_28(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:9],
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


def x_get_repo_info__mutmut_29(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "XXmessageXX": str(head.commit.message).strip().splitlines()[0],
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


def x_get_repo_info__mutmut_30(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "MESSAGE": str(head.commit.message).strip().splitlines()[0],
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


def x_get_repo_info__mutmut_31(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "message": str(None).strip().splitlines()[0],
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


def x_get_repo_info__mutmut_32(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "message": str(head.commit.message).strip().splitlines()[1],
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


def x_get_repo_info__mutmut_33(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "message": str(head.commit.message).strip().splitlines()[0],
                "XXauthorXX": str(head.commit.author),
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


def x_get_repo_info__mutmut_34(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "message": str(head.commit.message).strip().splitlines()[0],
                "AUTHOR": str(head.commit.author),
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


def x_get_repo_info__mutmut_35(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
        return RepoInfoResult(
            success=True,
            data={
                "branch": branch,
                "commit": head.commit.hexsha[:8],
                "message": str(head.commit.message).strip().splitlines()[0],
                "author": str(None),
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


def x_get_repo_info__mutmut_36(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(None, path)
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


def x_get_repo_info__mutmut_37(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: not a git repo at %s", None)
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


def x_get_repo_info__mutmut_38(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(path)
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


def x_get_repo_info__mutmut_39(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: not a git repo at %s", )
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


def x_get_repo_info__mutmut_40(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("XXget_repo_info: not a git repo at %sXX", path)
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


def x_get_repo_info__mutmut_41(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("GET_REPO_INFO: NOT A GIT REPO AT %S", path)
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


def x_get_repo_info__mutmut_42(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        return _failure(None)
    except PermissionError as e:
        logger.debug("get_repo_info: permission error: %s", e)
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_43(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(None, e)
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_44(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: permission error: %s", None)
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_45(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(e)
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_46(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: permission error: %s", )
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_47(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("XXget_repo_info: permission error: %sXX", e)
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_48(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("GET_REPO_INFO: PERMISSION ERROR: %S", e)
        return _failure(FailureReason.PERMISSION_DENIED)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_49(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        return _failure(None)
    except git.exc.GitError as e:
        logger.debug("get_repo_info: git error: %s", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_50(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(None, e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_51(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: git error: %s", None)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_52(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_53(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: git error: %s", )
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_54(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("XXget_repo_info: git error: %sXX", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_55(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("GET_REPO_INFO: GIT ERROR: %S", e)
        return _failure(FailureReason.GIT_ERROR)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_56(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        return _failure(None)
    except (OSError, AttributeError, ValueError) as e:
        logger.debug("get_repo_info: %s: %s", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_57(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(None, type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_58(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: %s: %s", None, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_59(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: %s: %s", type(e).__name__, None)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_60(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug(type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_61(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: %s: %s", e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_62(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: %s: %s", type(e).__name__, )
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_63(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("XXget_repo_info: %s: %sXX", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_64(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("GET_REPO_INFO: %S: %S", type(e).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_65(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        logger.debug("get_repo_info: %s: %s", type(None).__name__, e)
        return _failure(FailureReason.OTHER_ERROR)


def x_get_repo_info__mutmut_66(path: str = ".") -> RepoInfoResult:
    """Return current branch and last commit info, or a RepoInfoResult with failure_reason on error."""
    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        logger.debug("get_repo_info: GitPython not installed")
        return _failure(FailureReason.GITPYTHON_NOT_INSTALLED)
    try:
        repo = git.Repo(path, search_parent_directories=True)
        head = repo.head
        branch = head.ref.name if not head.is_detached else "HEAD (detached)"
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
        return _failure(None)

mutants_x_get_repo_info__mutmut['_mutmut_orig'] = x_get_repo_info__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_1'] = x_get_repo_info__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_2'] = x_get_repo_info__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_3'] = x_get_repo_info__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_4'] = x_get_repo_info__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_5'] = x_get_repo_info__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_6'] = x_get_repo_info__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_7'] = x_get_repo_info__mutmut_7 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_8'] = x_get_repo_info__mutmut_8 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_9'] = x_get_repo_info__mutmut_9 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_10'] = x_get_repo_info__mutmut_10 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_11'] = x_get_repo_info__mutmut_11 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_12'] = x_get_repo_info__mutmut_12 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_13'] = x_get_repo_info__mutmut_13 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_14'] = x_get_repo_info__mutmut_14 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_15'] = x_get_repo_info__mutmut_15 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_16'] = x_get_repo_info__mutmut_16 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_17'] = x_get_repo_info__mutmut_17 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_18'] = x_get_repo_info__mutmut_18 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_19'] = x_get_repo_info__mutmut_19 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_20'] = x_get_repo_info__mutmut_20 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_21'] = x_get_repo_info__mutmut_21 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_22'] = x_get_repo_info__mutmut_22 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_23'] = x_get_repo_info__mutmut_23 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_24'] = x_get_repo_info__mutmut_24 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_25'] = x_get_repo_info__mutmut_25 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_26'] = x_get_repo_info__mutmut_26 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_27'] = x_get_repo_info__mutmut_27 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_28'] = x_get_repo_info__mutmut_28 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_29'] = x_get_repo_info__mutmut_29 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_30'] = x_get_repo_info__mutmut_30 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_31'] = x_get_repo_info__mutmut_31 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_32'] = x_get_repo_info__mutmut_32 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_33'] = x_get_repo_info__mutmut_33 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_34'] = x_get_repo_info__mutmut_34 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_35'] = x_get_repo_info__mutmut_35 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_36'] = x_get_repo_info__mutmut_36 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_37'] = x_get_repo_info__mutmut_37 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_38'] = x_get_repo_info__mutmut_38 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_39'] = x_get_repo_info__mutmut_39 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_40'] = x_get_repo_info__mutmut_40 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_41'] = x_get_repo_info__mutmut_41 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_42'] = x_get_repo_info__mutmut_42 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_43'] = x_get_repo_info__mutmut_43 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_44'] = x_get_repo_info__mutmut_44 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_45'] = x_get_repo_info__mutmut_45 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_46'] = x_get_repo_info__mutmut_46 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_47'] = x_get_repo_info__mutmut_47 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_48'] = x_get_repo_info__mutmut_48 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_49'] = x_get_repo_info__mutmut_49 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_50'] = x_get_repo_info__mutmut_50 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_51'] = x_get_repo_info__mutmut_51 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_52'] = x_get_repo_info__mutmut_52 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_53'] = x_get_repo_info__mutmut_53 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_54'] = x_get_repo_info__mutmut_54 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_55'] = x_get_repo_info__mutmut_55 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_56'] = x_get_repo_info__mutmut_56 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_57'] = x_get_repo_info__mutmut_57 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_58'] = x_get_repo_info__mutmut_58 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_59'] = x_get_repo_info__mutmut_59 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_60'] = x_get_repo_info__mutmut_60 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_61'] = x_get_repo_info__mutmut_61 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_62'] = x_get_repo_info__mutmut_62 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_63'] = x_get_repo_info__mutmut_63 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_64'] = x_get_repo_info__mutmut_64 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_65'] = x_get_repo_info__mutmut_65 # type: ignore # mutmut generated
mutants_x_get_repo_info__mutmut['x_get_repo_info__mutmut_66'] = x_get_repo_info__mutmut_66 # type: ignore # mutmut generated
mutants_x__failure__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__failure__mutmut)
def _failure(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(success=False, failure_reason=reason)


def x__failure__mutmut_orig(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(success=False, failure_reason=reason)


def x__failure__mutmut_1(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(success=None, failure_reason=reason)


def x__failure__mutmut_2(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(success=False, failure_reason=None)


def x__failure__mutmut_3(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(failure_reason=reason)


def x__failure__mutmut_4(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(success=False, )


def x__failure__mutmut_5(reason: FailureReason) -> RepoInfoResult:
    """Return a failure RepoInfoResult for the given reason."""
    return RepoInfoResult(success=True, failure_reason=reason)

mutants_x__failure__mutmut['_mutmut_orig'] = x__failure__mutmut_orig # type: ignore # mutmut generated
mutants_x__failure__mutmut['x__failure__mutmut_1'] = x__failure__mutmut_1 # type: ignore # mutmut generated
mutants_x__failure__mutmut['x__failure__mutmut_2'] = x__failure__mutmut_2 # type: ignore # mutmut generated
mutants_x__failure__mutmut['x__failure__mutmut_3'] = x__failure__mutmut_3 # type: ignore # mutmut generated
mutants_x__failure__mutmut['x__failure__mutmut_4'] = x__failure__mutmut_4 # type: ignore # mutmut generated
mutants_x__failure__mutmut['x__failure__mutmut_5'] = x__failure__mutmut_5 # type: ignore # mutmut generated
