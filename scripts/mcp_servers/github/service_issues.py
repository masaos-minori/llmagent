#!/usr/bin/env python3
"""mcp_servers/github/service_issues.py
Issues, comments, and search issues operations for GitHubService.

Dependency direction: service_issues → service_security, models
"""

from __future__ import annotations

import itertools
from typing import Any

from github import Github
from mcp_servers.github.models_issues import (
    AddIssueCommentRequest,
    AddIssueCommentResponse,
    CreateIssueRequest,
    CreateIssueResponse,
    GetIssueRequest,
    GetIssueResponse,
    IssueInfo,
    ListIssuesRequest,
    ListIssuesResponse,
    SearchIssuesRequest,
    SearchIssuesResponse,
)
from mcp_servers.github.service_security import GitHubSecurityGuards


class IssuesOps(GitHubSecurityGuards):
    """Issues, comments, and search operations."""

    def __init__(self, gh: Github, cfg: Any) -> None:  # noqa: ANN401
        super().__init__(gh, cfg)

    async def list_issues(self, req: ListIssuesRequest) -> ListIssuesResponse:
        """Retrieve the list of issues for a repository."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[IssueInfo]:
            repo = self._get_repo(req.owner, req.repo)
            issues_slice = itertools.islice(repo.get_issues(state=req.state), per_page)
            return [self._issue_to_info(i) for i in issues_slice]

        issues = await self._run_github(_sync)
        return ListIssuesResponse(issues=issues)

    async def get_issue(self, req: GetIssueRequest) -> GetIssueResponse:
        """Retrieve a specific issue by number."""

        def _sync() -> IssueInfo:
            repo = self._get_repo(req.owner, req.repo)
            return self._issue_to_info(repo.get_issue(number=req.issue_number))

        issue = await self._run_github(_sync)
        return GetIssueResponse(issue=issue)

    async def create_issue(self, req: CreateIssueRequest) -> CreateIssueResponse:
        """Create a new issue in a repository."""
        self._assert_allowed_repo(req.owner, req.repo)

        def _sync() -> IssueInfo:
            repo = self._get_repo(req.owner, req.repo)
            issue = repo.create_issue(
                title=req.title,
                body=req.body or None,
                labels=req.labels or [],
                assignees=req.assignees or [],
            )
            return self._issue_to_info(issue)

        issue = await self._run_github(_sync)
        self._write_github_audit_log(
            "create_issue",
            repo=f"{req.owner}/{req.repo}",
            number=issue.number,
            title=req.title,
        )
        return CreateIssueResponse(issue=issue)

    async def search_issues(self, req: SearchIssuesRequest) -> SearchIssuesResponse:
        """Keyword search for issues/PRs across all of GitHub."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[IssueInfo]:
            issues_slice = itertools.islice(
                self._gh.search_issues(query=req.query),
                per_page,
            )
            return [self._issue_to_info(i) for i in issues_slice]

        issues = await self._run_github(_sync)
        return SearchIssuesResponse(query=req.query, results=issues)

    async def add_issue_comment(
        self,
        req: AddIssueCommentRequest,
    ) -> AddIssueCommentResponse:
        """Post a comment to an existing issue."""
        self._assert_allowed_repo(req.owner, req.repo)

        def _sync() -> AddIssueCommentResponse:
            repo = self._get_repo(req.owner, req.repo)
            comment = repo.get_issue(number=req.issue_number).create_comment(req.body)
            return AddIssueCommentResponse(
                issue_number=req.issue_number,
                comment_url=comment.html_url,
            )

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "add_issue_comment",
            repo=f"{req.owner}/{req.repo}",
            issue=req.issue_number,
        )
        return result
