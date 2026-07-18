#!/usr/bin/env python3
"""mcp_servers/github/models_pull_requests.py

Pydantic request/response models for pull request operations.

Dependency direction: mcp_servers.github.models_pull_requests → (no local deps)
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .models_base import IssueInfo, PullRequestInfo


class ListPullRequestsRequest(BaseModel):
    """Request model for listing pull requests."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    state: str = Field(default="open", pattern="^(open|closed|all)$")
    per_page: int = Field(default=10, ge=1)


class ListPullRequestsResponse(BaseModel):
    """Response containing a list of pull requests."""

    pull_requests: list[PullRequestInfo]


class GetPullRequestRequest(BaseModel):
    """Request model for getting a single pull request."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number")


class GetPullRequestResponse(BaseModel):
    """Response containing a single pull request."""

    pull_request: PullRequestInfo


class CreatePullRequestRequest(BaseModel):
    """Request model for creating a new pull request."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Pull request title")
    body: str = Field(default="", description="Pull request body (Markdown)")
    head: str = Field(..., description="Source branch name for the PR")
    base: str = Field(..., description="Target branch name to merge into")
    dry_run: bool = Field(default=False, description="Preview only; no PR is created")


class CreatePullRequestResponse(BaseModel):
    """Response containing the created pull request."""

    pull_request: PullRequestInfo


class UpdatePullRequestRequest(BaseModel):
    """Request model for updating an existing pull request."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number to update")
    title: str | None = Field(default=None, description="New title (omit to keep)")
    body: str | None = Field(default=None, description="New body (omit to keep)")
    state: str | None = Field(
        default=None,
        pattern="^(open|closed)$",
        description="New state: open / closed (omit to keep unchanged)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no PR is updated")


class UpdatePullRequestResponse(BaseModel):
    """Response containing the updated pull request."""

    pull_request: PullRequestInfo


class MergePullRequestRequest(BaseModel):
    """Request model for merging a pull request."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number to merge")
    commit_title: str = Field(
        default="",
        description="Merge commit title (default: GitHub default)",
    )
    commit_message: str = Field(
        default="",
        description="Merge commit body (default: GitHub default)",
    )
    merge_method: str = Field(
        default="merge",
        pattern="^(merge|squash|rebase)$",
        description="Merge method: merge / squash / rebase",
    )
    dry_run: bool = Field(default=False, description="Preview only; no PR is merged")


class MergePullRequestResponse(BaseModel):
    """Response containing the result of a merge operation."""

    pr_number: int
    merged: bool
    sha: str
    message: str


class SearchPullRequestsRequest(BaseModel):
    """Request model for searching pull requests via GitHub API."""

    query: str = Field(
        ...,
        description="GitHub search query (is:pr is appended automatically)",
    )
    per_page: int = Field(default=10, ge=1)


class SearchPullRequestsResponse(BaseModel):
    """Response containing search results for pull requests."""

    query: str
    results: list[IssueInfo]  # Search API returns Issue objects
