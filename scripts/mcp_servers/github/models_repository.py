#!/usr/bin/env python3
"""mcp_servers/github/models_repository.py

Pydantic request/response models for repository/branch/commit operations.

Dependency direction: mcp_servers.github.models_repository → mcp_servers.github.models_config
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .models_config import DEFAULT_PER_PAGE


class SearchRepositoriesRequest(BaseModel):
    """Request model for searching GitHub repositories."""

    query: str = Field(
        ...,
        description="GitHub repository search query (GitHub Search syntax)",
    )
    per_page: int = Field(
        default=DEFAULT_PER_PAGE,
        ge=1,
        description="Maximum number of results to return",
    )


class RepositoryInfo(BaseModel):
    """A single result from GitHub repository search."""

    full_name: str
    description: str | None
    url: str
    stars: int
    forks: int
    language: str | None
    updated_at: str


class SearchRepositoriesResponse(BaseModel):
    """Response from searching GitHub repositories."""

    query: str
    results: list[RepositoryInfo]


class ListCommitsRequest(BaseModel):
    """Request model for listing commits in a repository."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(default="", description="Branch name (default: default branch)")
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class CommitInfo(BaseModel):
    """A single commit returned by list_commits."""

    sha: str
    message: str
    author: str
    authored_at: str
    url: str


class ListCommitsResponse(BaseModel):
    """Response containing a list of commits."""

    commits: list[CommitInfo]


class SearchCodeRequest(BaseModel):
    """Request model for searching GitHub code."""

    query: str = Field(
        ...,
        description="Code search query (e.g. 'filename:agent.py repo:owner/repo')",
    )
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class CodeSearchResult(BaseModel):
    """A single result from GitHub code search."""

    repository: str
    path: str
    url: str
    score: float


class SearchCodeResponse(BaseModel):
    """Response from searching GitHub code."""

    query: str
    results: list[CodeSearchResult]


class ListBranchesRequest(BaseModel):
    """Request model for listing branches in a repository."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class BranchInfo(BaseModel):
    """Information about a single branch."""

    name: str
    sha: str
    protected: bool


class ListBranchesResponse(BaseModel):
    """Response containing a list of branches."""

    branches: list[BranchInfo]


class GetCommitRequest(BaseModel):
    """Request model for getting detailed commit information."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    sha: str = Field(..., description="Commit SHA (full or abbreviated)")


class CommitDetail(BaseModel):
    """Detailed information about a single commit."""

    sha: str
    message: str
    author: str
    authored_at: str
    url: str
    files_changed: int


class GetCommitResponse(BaseModel):
    """Response containing detailed commit information."""

    commit: CommitDetail


class CreateBranchRequest(BaseModel):
    """Request model for creating a new branch."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    branch_name: str = Field(..., description="Name of the new branch to create")
    from_branch: str = Field(
        default="",
        description="Base branch to derive from (default: default branch)",
    )
    dry_run: bool = Field(
        default=False, description="Preview only; no branch is created"
    )


class CreateBranchResponse(BaseModel):
    """Response indicating whether a branch was created."""

    branch_name: str
    sha: str
