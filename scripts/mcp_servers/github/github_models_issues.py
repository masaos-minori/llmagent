#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_models_issues.py

Pydantic request/response models for issues operations.

Dependency direction: mcp_servers.github.github_models_issues → mcp_servers.request_contract,
mcp_servers.github.github_models_base
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from mcp_servers.request_contract import StrictRequestModel

from .github_models_base import IssueInfo


class ListIssuesRequest(StrictRequestModel):
    """Request model for listing issues."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    state: str = Field(
        default="open",
        pattern="^(open|closed|all)$",
        description="Issue state (open/closed/all)",
    )
    per_page: int = Field(default=10, ge=1, le=100)


class ListIssuesResponse(BaseModel):
    """Response containing a list of issues."""

    issues: list[IssueInfo]


class GetIssueRequest(StrictRequestModel):
    """Request model for getting a single issue."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    issue_number: int = Field(..., ge=1, description="Issue number")


class GetIssueResponse(BaseModel):
    """Response containing a single issue."""

    issue: IssueInfo


class CreateIssueRequest(StrictRequestModel):
    """Request model for creating a new issue."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    title: str = Field(..., min_length=1, max_length=256, description="Issue title")
    body: str = Field(default="", max_length=65536, description="Issue body (Markdown)")
    labels: list[str] = Field(
        default_factory=list, max_length=100, description="List of label names"
    )
    assignees: list[str] = Field(
        default_factory=list,
        max_length=100,
        description="List of assignee GitHub usernames",
    )
    dry_run: bool = Field(
        default=False, description="Preview only; no issue is created"
    )


class CreateIssueResponse(BaseModel):
    """Response containing the created issue."""

    issue: IssueInfo


class AddIssueCommentRequest(StrictRequestModel):
    """Request model for adding a comment to an issue."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    issue_number: int = Field(
        ..., ge=1, description="Issue number to add the comment to"
    )
    body: str = Field(
        ..., min_length=1, max_length=65536, description="Comment body (Markdown)"
    )
    dry_run: bool = Field(
        default=False, description="Preview only; no comment is posted"
    )


class AddIssueCommentResponse(BaseModel):
    """Response containing the result of adding a comment."""

    issue_number: int
    comment_url: str


class SearchIssuesRequest(StrictRequestModel):
    """Request model for searching issues via GitHub API."""

    query: str = Field(
        ...,
        min_length=1,
        description="GitHub search query (e.g. 'repo:owner/repo is:issue label:bug')",
    )
    per_page: int = Field(default=10, ge=1, le=100)


class SearchIssuesResponse(BaseModel):
    """Response containing search results for issues."""

    query: str
    results: list[IssueInfo]
