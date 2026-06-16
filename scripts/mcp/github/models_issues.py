#!/usr/bin/env python3
"""mcp/github/models_issues.py
Pydantic request/response models for issues operations.

Dependency direction: mcp.github.models_issues → (no local deps)
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .models_base import IssueInfo


class ListIssuesRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    state: str = Field(
        default="open",
        pattern="^(open|closed|all)$",
        description="Issue state (open/closed/all)",
    )
    per_page: int = Field(default=10, ge=1)


class ListIssuesResponse(BaseModel):
    issues: list[IssueInfo]


class GetIssueRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number")


class GetIssueResponse(BaseModel):
    issue: IssueInfo


class CreateIssueRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Issue title")
    body: str = Field(default="", description="Issue body (Markdown)")
    labels: list[str] = Field(default_factory=list, description="List of label names")
    assignees: list[str] = Field(
        default_factory=list,
        description="List of assignee GitHub usernames",
    )
    dry_run: bool = Field(
        default=False, description="Preview only; no issue is created"
    )


class CreateIssueResponse(BaseModel):
    issue: IssueInfo


class AddIssueCommentRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number to add the comment to")
    body: str = Field(..., description="Comment body (Markdown)")
    dry_run: bool = Field(
        default=False, description="Preview only; no comment is posted"
    )


class AddIssueCommentResponse(BaseModel):
    issue_number: int
    comment_url: str


class SearchIssuesRequest(BaseModel):
    query: str = Field(
        ...,
        description="GitHub search query (e.g. 'repo:owner/repo is:issue label:bug')",
    )
    per_page: int = Field(default=10, ge=1)


class SearchIssuesResponse(BaseModel):
    query: str
    results: list[IssueInfo]
