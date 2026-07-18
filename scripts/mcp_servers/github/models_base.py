#!/usr/bin/env python3
"""mcp_servers/github/models_base.py

Shared Pydantic models used across multiple domain modules.

Dependency direction: mcp_servers.github.models_base → (no local deps)
"""

from __future__ import annotations

from pydantic import BaseModel


class IssueInfo(BaseModel):
    """Base information about a GitHub issue."""

    number: int
    title: str
    state: str
    url: str
    body: str | None
    created_at: str
    updated_at: str
    labels: list[str]
    assignees: list[str]


class PullRequestInfo(BaseModel):
    """Base information about a GitHub pull request."""

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
