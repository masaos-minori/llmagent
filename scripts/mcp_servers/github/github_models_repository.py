#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_models_repository.py

Pydantic request/response models for repository/branch/commit operations.

Dependency direction: mcp_servers.github.github_models_repository → mcp_servers.request_contract
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from mcp_servers.request_contract import StrictRequestModel


class SearchRepositoriesRequest(StrictRequestModel):
    """Request model for searching GitHub repositories."""

    query: str = Field(
        ...,
        min_length=1,
        description="GitHub repository search query (GitHub Search syntax)",
    )
    per_page: int = Field(
        default=30,
        ge=1,
        le=100,
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


class ListCommitsRequest(StrictRequestModel):
    """Request model for listing commits in a repository."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    branch: str = Field(default="", description="Branch name (default: default branch)")
    per_page: int = Field(default=30, ge=1, le=100)

    @model_validator(mode="after")
    def _reject_empty_branch(self) -> Self:
        """Reject an explicitly supplied empty `branch`; omitting it means default branch."""
        if "branch" in self.model_fields_set and self.branch == "":
            raise ValueError(
                "branch must not be empty; omit it to use the default branch"
            )
        return self


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


class SearchCodeRequest(StrictRequestModel):
    """Request model for searching GitHub code."""

    query: str = Field(
        ...,
        min_length=1,
        description="Code search query (e.g. 'filename:agent.py repo:owner/repo')",
    )
    per_page: int = Field(default=30, ge=1, le=100)


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


class ListBranchesRequest(StrictRequestModel):
    """Request model for listing branches in a repository."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    per_page: int = Field(default=30, ge=1, le=100)


class BranchInfo(BaseModel):
    """Information about a single branch."""

    name: str
    sha: str
    protected: bool


class ListBranchesResponse(BaseModel):
    """Response containing a list of branches."""

    branches: list[BranchInfo]


class GetCommitRequest(StrictRequestModel):
    """Request model for getting detailed commit information."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    sha: str = Field(..., min_length=1, description="Commit SHA (full or abbreviated)")


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


class CreateBranchRequest(StrictRequestModel):
    """Request model for creating a new branch."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    branch_name: str = Field(
        ..., min_length=1, description="Name of the new branch to create"
    )
    from_branch: str = Field(
        default="",
        description="Base branch to derive from (default: default branch)",
    )
    dry_run: bool = Field(
        default=False, description="Preview only; no branch is created"
    )

    @model_validator(mode="after")
    def _reject_empty_from_branch(self) -> Self:
        """Reject an explicitly supplied empty `from_branch`; omitting it means default branch."""
        if "from_branch" in self.model_fields_set and self.from_branch == "":
            raise ValueError(
                "from_branch must not be empty; omit it to use the default branch"
            )
        return self


class CreateBranchResponse(BaseModel):
    """Response indicating whether a branch was created."""

    branch_name: str
    sha: str
