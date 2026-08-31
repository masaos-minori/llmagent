#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_models.py

Config loading and Pydantic request models for git-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.config_utils import get_str, get_typed

from mcp_servers.git.repository_state import RepositoryState

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class GitConfig:
    """Typed configuration for the Git MCP server."""

    allowed_repo_paths: list[str] = dataclasses.field(default_factory=list)
    read_only: bool = True
    auth_token: str = ""
    max_log_entries: int = 50
    protected_branches: list[str] = dataclasses.field(default_factory=list)
    audit_log_path: str = ""
    allow_detached_head: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GitConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        allowed = get_typed(d, "allowed_repo_paths", list, "a list", default=[])
        read_only = get_typed(d, "read_only", bool, "a boolean", default=True)
        max_log = get_typed(d, "max_log_entries", int, "an integer", default=50)
        auth_token = get_str(d, "auth_token")
        audit_log_path = get_str(d, "audit_log_path")
        protected_branches = get_typed(
            d, "protected_branches", list, "a list", default=[]
        )
        allow_detached_head = get_typed(
            d, "allow_detached_head", bool, "a boolean", default=False
        )
        return cls(
            allowed_repo_paths=list(allowed),
            read_only=read_only,
            auth_token=auth_token,
            max_log_entries=max_log,
            audit_log_path=audit_log_path,
            protected_branches=list(protected_branches),
            allow_detached_head=allow_detached_head,
        )

    @classmethod
    def load(cls) -> GitConfig:
        """Load from git_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("git_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class GitServiceError(RuntimeError):
    """Raised on general git service errors."""


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────

_REPO_PATH_DESC = "Absolute path to the git repository"


class RepoPathMixin(BaseModel):
    """Mixin providing the common repo_path field."""

    repo_path: str = Field(..., description=_REPO_PATH_DESC)


class RepositoryStateMixin(BaseModel):
    """Mixin providing the common repository_state field."""

    repository_state: RepositoryState | None = Field(
        default=None, description="Repository state snapshot for write operations"
    )


# ── Read-only tool request models ────────────────────────────────────────────


class GitStatusRequest(RepoPathMixin):
    """Request model for git_status — read-only status of a repository."""


class GitLogRequest(RepoPathMixin):
    """Request model for git_log — recent commit log entries."""

    max_entries: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Max commits to return",
    )
    branch: str = Field(default="", description="Branch name; empty = current HEAD")


class GitDiffRequest(RepoPathMixin):
    """Request model for git_diff — diff between working tree and index or two commits."""

    staged: bool = Field(
        default=False,
        description="When True, show staged diff (git diff --cached)",
    )
    commit: str = Field(
        default="",
        description="Commit ref to diff against; empty = working tree",
    )


class GitBranchRequest(RepoPathMixin):
    """Request model for git_branch — list branches in a repository."""


class GitShowRequest(RepoPathMixin):
    """Request model for git_show — show details of a commit, blob, or tree object."""

    ref: str = Field(default="HEAD", description="Commit ref or tag to show")


# ── Write tool request models ─────────────────────────────────────────────────


class GitAddRequest(RepoPathMixin):
    """Request model for git_add — stage files for commit."""

    paths: list[str] = Field(
        ...,
        min_length=1,
        description="File paths to stage (relative to repo root)",
    )
    dry_run: bool = Field(
        default=False,
        description="When True, preview only without staging",
    )


class GitCommitRequest(RepoPathMixin):
    """Request model for git_commit — create a new commit from staged changes."""

    message: str = Field(..., min_length=1, description="Commit message")
    dry_run: bool = Field(
        default=False,
        description="When True, preview staged files without committing",
    )


class GitCheckoutRequest(RepoPathMixin):
    """Request model for git_checkout — switch branches or restore working tree files."""

    branch: str = Field(..., description="Branch name to checkout or create")
    create: bool = Field(default=False, description="When True, create new branch (-b)")
    dry_run: bool = Field(
        default=False,
        description="When True, preview only without switching",
    )


class GitPullRequest(RepoPathMixin):
    """Request model for git_pull — fetch and merge changes from a remote repository."""

    remote: str = Field(default="origin", description="Remote name")
    branch: str = Field(
        default="",
        description="Branch name; empty = current tracking branch",
    )
    dry_run: bool = Field(
        default=False,
        description="When True, perform fetch --dry-run only",
    )


class GitPushRequest(RepoPathMixin):
    """Request model for git_push — push local commits to a remote repository."""

    remote: str = Field(default="origin", description="Remote name")
    branch: str = Field(default="", description="Branch name; empty = current branch")
    dry_run: bool = Field(
        default=False,
        description="When True, preview only without pushing",
    )
