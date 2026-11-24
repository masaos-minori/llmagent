#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_models_pull_requests.py

Pydantic request/response models for pull request operations.

Dependency direction: mcp_servers.github.github_models_pull_requests → mcp_servers.request_contract,
mcp_servers.github.github_models_base
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from mcp_servers.request_contract import StrictRequestModel

from .github_models_base import IssueInfo, PullRequestInfo


class ListPullRequestsRequest(StrictRequestModel):
    """Request model for listing pull requests."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    state: str = Field(default="open", pattern="^(open|closed|all)$")
    per_page: int = Field(default=10, ge=1, le=100)


class ListPullRequestsResponse(BaseModel):
    """Response containing a list of pull requests."""

    pull_requests: list[PullRequestInfo]


class GetPullRequestRequest(StrictRequestModel):
    """Request model for getting a single pull request."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    pr_number: int = Field(..., ge=1, description="Pull request number")


class GetPullRequestResponse(BaseModel):
    """Response containing a single pull request."""

    pull_request: PullRequestInfo


class CreatePullRequestRequest(StrictRequestModel):
    """Request model for creating a new pull request."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    title: str = Field(
        ..., min_length=1, max_length=256, description="Pull request title"
    )
    body: str = Field(
        default="", max_length=65536, description="Pull request body (Markdown)"
    )
    head: str = Field(..., min_length=1, description="Source branch name for the PR")
    base: str = Field(..., min_length=1, description="Target branch name to merge into")
    dry_run: bool = Field(default=False, description="Preview only; no PR is created")


class CreatePullRequestResponse(BaseModel):
    """Response containing the created pull request."""

    pull_request: PullRequestInfo


class UpdatePullRequestRequest(StrictRequestModel):
    """Request model for updating an existing pull request."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    pr_number: int = Field(..., ge=1, description="Pull request number to update")
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="New title (omit to keep)",
    )
    body: str | None = Field(
        default=None, max_length=65536, description="New body (omit to keep)"
    )
    state: str | None = Field(
        default=None,
        pattern="^(open|closed)$",
        description="New state: open / closed (omit to keep unchanged)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no PR is updated")

    @model_validator(mode="after")
    def _require_a_change(self) -> Self:
        """Reject an update that supplies none of the fields it would change.

        `model_fields_set` is the authoritative 'explicitly supplied' signal, and an
        explicit `None` means 'keep', so only a supplied non-`None` value counts. An
        empty `body` counts: it clears the body, which is a change.
        """
        if not any(
            name in self.model_fields_set and getattr(self, name) is not None
            for name in ("title", "body", "state")
        ):
            raise ValueError(
                "update_pull_request requires at least one of title, body, state"
            )
        return self


class UpdatePullRequestResponse(BaseModel):
    """Response containing the updated pull request."""

    pull_request: PullRequestInfo


class MergePullRequestRequest(StrictRequestModel):
    """Request model for merging a pull request."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    pr_number: int = Field(..., ge=1, description="Pull request number to merge")
    commit_title: str = Field(
        default="",
        max_length=256,
        description="Merge commit title (default: GitHub default)",
    )
    commit_message: str = Field(
        default="",
        max_length=65536,
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


class SearchPullRequestsRequest(StrictRequestModel):
    """Request model for searching pull requests via GitHub API."""

    query: str = Field(
        ...,
        min_length=1,
        description="GitHub search query (is:pr is appended automatically)",
    )
    per_page: int = Field(default=10, ge=1, le=100)


class SearchPullRequestsResponse(BaseModel):
    """Response containing search results for pull requests."""

    query: str
    results: list[IssueInfo]  # Search API returns Issue objects
