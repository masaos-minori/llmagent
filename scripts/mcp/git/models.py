#!/usr/bin/env python3
"""mcp/git/models.py
Config loading and Pydantic request models for git-mcp.
"""

from __future__ import annotations

import dataclasses
import logging

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


def _get_str(d: dict[str, object], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


@dataclasses.dataclass
class GitConfig:
    """Typed configuration for the Git MCP server."""

    allowed_repo_paths: list[str] = dataclasses.field(default_factory=list)
    read_only: bool = True
    auth_token: str = ""
    max_log_entries: int = 50
    audit_log_path: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> GitConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        allowed = d.get("allowed_repo_paths")
        if not isinstance(allowed, list):
            raise ValueError("'allowed_repo_paths' must be a list")
        read_only = d.get("read_only")
        if not isinstance(read_only, bool):
            raise ValueError("'read_only' must be a boolean")
        max_log = d.get("max_log_entries")
        if not isinstance(max_log, int):
            raise ValueError("'max_log_entries' must be an integer")
        return cls(
            allowed_repo_paths=list(allowed),
            read_only=read_only,
            auth_token=_get_str(d, "auth_token"),
            max_log_entries=max_log,
            audit_log_path=_get_str(d, "audit_log_path"),
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

# ── Read-only tool request models ────────────────────────────────────────────


class GitStatusRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")


class GitLogRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    max_entries: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Max commits to return",
    )
    branch: str = Field(default="", description="Branch name; empty = current HEAD")


class GitDiffRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    staged: bool = Field(
        default=False,
        description="When True, show staged diff (git diff --cached)",
    )
    commit: str = Field(
        default="",
        description="Commit ref to diff against; empty = working tree",
    )


class GitBranchRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")


class GitShowRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    ref: str = Field(default="HEAD", description="Commit ref or tag to show")


# ── Write tool request models ─────────────────────────────────────────────────


class GitAddRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    paths: list[str] = Field(
        ...,
        min_length=1,
        description="File paths to stage (relative to repo root)",
    )
    dry_run: bool = Field(
        default=False,
        description="When True, preview only without staging",
    )


class GitCommitRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    message: str = Field(..., min_length=1, description="Commit message")
    dry_run: bool = Field(
        default=False,
        description="When True, preview staged files without committing",
    )


class GitCheckoutRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    branch: str = Field(..., description="Branch name to checkout or create")
    create: bool = Field(default=False, description="When True, create new branch (-b)")
    dry_run: bool = Field(
        default=False,
        description="When True, preview only without switching",
    )


class GitPullRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    remote: str = Field(default="origin", description="Remote name")
    branch: str = Field(
        default="",
        description="Branch name; empty = current tracking branch",
    )
    dry_run: bool = Field(
        default=False,
        description="When True, perform fetch --dry-run only",
    )


class GitPushRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the git repository")
    remote: str = Field(default="origin", description="Remote name")
    branch: str = Field(default="", description="Branch name; empty = current branch")
    dry_run: bool = Field(
        default=False,
        description="When True, preview only without pushing",
    )
