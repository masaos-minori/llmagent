#!/usr/bin/env python3
"""mcp/github/service_business.py
GitHubService: core business operations assembled from domain modules.

Combines GitHubSecurityGuards (security mixin) with all domain operation
classes via multiple inheritance. Static formatters (_fmt_issue_line,
_fmt_pr_line) stay here for access by service_dispatch.fmt_* methods.

Dependency direction: service_business → all domain modules
Import from here:  from mcp.github.service_business import GitHubService
"""

from __future__ import annotations

from typing import Any

from github import Github
from mcp.github.models_base import IssueInfo, PullRequestInfo
from mcp.github.service_file import FileOps
from mcp.github.service_issues import IssuesOps
from mcp.github.service_pull_requests import PullRequestOps
from mcp.github.service_repository import RepositoryOps


class GitHubService(
    RepositoryOps,
    FileOps,
    IssuesOps,
    PullRequestOps,
):
    """GitHubService: security + all domain operations."""

    def __init__(self, gh: Github, cfg: Any) -> None:  # noqa: ANN401
        super().__init__(gh, cfg)

    # ── Static formatters (defined on base class for dispatch access) ──

    @staticmethod
    def _fmt_issue_line(i: IssueInfo) -> str:
        """Format one issue as a single display line with state, labels, and URL."""
        label_str = f" labels=[{', '.join(i.labels)}]" if i.labels else ""
        return f"#{i.number} [{i.state}]{label_str} {i.title}\n{i.url}"

    @staticmethod
    def _fmt_pr_line(pr: PullRequestInfo) -> str:
        """Format one pull request with state, head→base branch, and URL."""
        draft_str = " [draft]" if pr.draft else ""
        return (
            f"#{pr.number} [{pr.state}]{draft_str} {pr.title}"
            f" ({pr.head_ref}->{pr.base_ref})\n{pr.url}"
        )
