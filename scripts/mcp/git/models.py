#!/usr/bin/env python3
"""mcp/git/models.py
Config loading and Pydantic request models for git-mcp.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.logger import Logger

_models_logger = Logger(__name__, "/opt/llm/logs/git-mcp.log")

_cfg: dict[str, Any] | None = None


def load_git_config() -> dict[str, Any]:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("git_mcp_server.toml")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


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
