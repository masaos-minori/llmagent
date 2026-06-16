#!/usr/bin/env python3
"""mcp/github/models_pull_requests.py
Pydantic request/response models for pull request operations.

Dependency direction: mcp.github.models_pull_requests → (no local deps)
"""

from __future__ import annotations

import dataclasses

from pydantic import BaseModel, Field

from .models_base import IssueInfo


class ListPullRequestsRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    state: str = Field(default="open", pattern="^(open|closed|all)$")
    per_page: int = Field(default=10, ge=1)


class PullRequestInfo(BaseModel):
    number: int
    title: str
    state: str
    url: str
    body: str | None
    head_ref: str
    base_ref: str
    created_at: str
    updated_at: str
    draft: bool


class ListPullRequestsResponse(BaseModel):
    pull_requests: list[PullRequestInfo]


class GetPullRequestRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number")


class GetPullRequestResponse(BaseModel):
    pull_request: PullRequestInfo


class CreatePullRequestRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Pull request title")
    body: str = Field(default="", description="Pull request body (Markdown)")
    head: str = Field(..., description="Source branch name for the PR")
    base: str = Field(..., description="Target branch name to merge into")
    dry_run: bool = Field(default=False, description="Preview only; no PR is created")


class CreatePullRequestResponse(BaseModel):
    pull_request: PullRequestInfo


class UpdatePullRequestRequest(BaseModel):
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
    pull_request: PullRequestInfo


class MergePullRequestRequest(BaseModel):
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


@dataclasses.dataclass
class MergePullRequestResponse(BaseModel):
    pr_number: int
    merged: bool
    sha: str
    message: str


class SearchPullRequestsRequest(BaseModel):
    query: str = Field(
        ...,
        description="GitHub search query (is:pr is appended automatically)",
    )
    per_page: int = Field(default=10, ge=1)


class SearchPullRequestsResponse(BaseModel):
    query: str
    results: list[IssueInfo]  # Search API returns Issue objects
