#!/usr/bin/env python3
"""mcp/github/models_base.py
Shared Pydantic models used across multiple domain modules.

Dependency direction: mcp.github.models_base → (no local deps)
"""

from __future__ import annotations

from pydantic import BaseModel


class IssueInfo(BaseModel):
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
