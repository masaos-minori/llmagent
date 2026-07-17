#!/usr/bin/env python3
"""mcp_servers/github/service_pull_requests.py

Pull request, update, merge, and search PR operations for GitHubService.

Dependency direction: service_pull_requests → service_security, models
"""

from __future__ import annotations

import itertools
from typing import Any

from github import Github

from mcp_servers.github.mapper import issue_to_info, pr_to_info
from mcp_servers.github.models_config import GitHubAuthorizationError
from mcp_servers.github.models_pull_requests import (
    CreatePullRequestRequest,
    CreatePullRequestResponse,
    GetPullRequestRequest,
    GetPullRequestResponse,
    IssueInfo,
    ListPullRequestsRequest,
    ListPullRequestsResponse,
    MergePullRequestRequest,
    MergePullRequestResponse,
    PullRequestInfo,
    SearchPullRequestsRequest,
    SearchPullRequestsResponse,
    UpdatePullRequestRequest,
    UpdatePullRequestResponse,
)
from mcp_servers.github.service_security import GitHubSecurityGuards


class PullRequestOps(GitHubSecurityGuards):
    """Pull request management operations."""

    def __init__(self, gh: Github, cfg: Any) -> None:  # noqa: ANN401
        """Initialize with GitHub client and config, inheriting security guards."""
        super().__init__(gh, cfg)

    async def list_pull_requests(
        self,
        req: ListPullRequestsRequest,
    ) -> ListPullRequestsResponse:
        """Retrieve the list of pull requests for a repository."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[PullRequestInfo]:
            """Synchronously fetch pull requests from GitHub API."""
            repo = self._get_repo(req.owner, req.repo)
            prs_slice = itertools.islice(repo.get_pulls(state=req.state), per_page)
            return [pr_to_info(pr) for pr in prs_slice]

        prs = await self._run_github(_sync)
        return ListPullRequestsResponse(pull_requests=prs)

    async def get_pull_request(
        self,
        req: GetPullRequestRequest,
    ) -> GetPullRequestResponse:
        """Retrieve a specific pull request by number."""

        def _sync() -> PullRequestInfo:
            """Synchronously fetch a single pull request from GitHub API."""
            repo = self._get_repo(req.owner, req.repo)
            return pr_to_info(repo.get_pull(number=req.pr_number))

        pr = await self._run_github(_sync)
        return GetPullRequestResponse(pull_request=pr)

    async def create_pull_request(
        self,
        req: CreatePullRequestRequest,
    ) -> CreatePullRequestResponse:
        """Create a new pull request in a repository."""
        self._assert_allowed_repo(req.owner, req.repo)

        def _sync() -> PullRequestInfo:
            """Synchronously create a pull request via GitHub API."""
            repo = self._get_repo(req.owner, req.repo)
            pr = repo.create_pull(
                title=req.title,
                body=req.body,
                head=req.head,
                base=req.base,
            )
            return pr_to_info(pr)

        pr = await self._run_github(_sync)
        self._write_github_audit_log(
            "create_pull_request",
            repo=f"{req.owner}/{req.repo}",
            pr=pr.number,
            head=req.head,
            base=req.base,
            title=req.title,
        )
        return CreatePullRequestResponse(pull_request=pr)

    async def search_pull_requests(
        self,
        req: SearchPullRequestsRequest,
    ) -> SearchPullRequestsResponse:
        """Keyword search for PRs across GitHub (is:pr appended automatically)."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[IssueInfo]:
            """Synchronously search for pull requests via GitHub search API."""
            query = req.query if "is:pr" in req.query else f"{req.query} is:pr"
            issues_slice = itertools.islice(
                self._gh.search_issues(query=query),
                per_page,
            )
            return [issue_to_info(i) for i in issues_slice]

        results = await self._run_github(_sync)
        return SearchPullRequestsResponse(query=req.query, results=results)

    async def update_pull_request(
        self,
        req: UpdatePullRequestRequest,
    ) -> UpdatePullRequestResponse:
        """Update the title, body, or state of a pull request."""
        self._assert_allowed_repo(req.owner, req.repo)

        def _sync() -> PullRequestInfo:
            """Synchronously update a pull request via GitHub API."""
            repo = self._get_repo(req.owner, req.repo)
            pr = repo.get_pull(number=req.pr_number)
            kwargs: dict[str, object] = {}
            if req.title is not None:
                kwargs["title"] = req.title
            if req.body is not None:
                kwargs["body"] = req.body
            if req.state is not None:
                kwargs["state"] = req.state
            if kwargs:
                pr.edit(**kwargs)
            return pr_to_info(pr)

        pr = await self._run_github(_sync)
        self._write_github_audit_log(
            "update_pull_request",
            repo=f"{req.owner}/{req.repo}",
            pr=req.pr_number,
        )
        return UpdatePullRequestResponse(pull_request=pr)

    async def merge_pull_request(
        self,
        req: MergePullRequestRequest,
    ) -> MergePullRequestResponse:
        """Merge a pull request using the specified merge method."""
        self._assert_allowed_repo(req.owner, req.repo)
        if not self._cfg.allow_force_push and req.merge_method == "rebase":
            raise GitHubAuthorizationError(
                "Rebase merge is disabled (allow_force_push=false)"
            )

        def _sync() -> MergePullRequestResponse:
            """Synchronously merge a pull request via GitHub API."""
            repo = self._get_repo(req.owner, req.repo)
            pr = repo.get_pull(number=req.pr_number)
            self._assert_allowed_branch(req.owner, req.repo, pr.base.ref)
            if self._cfg.require_pr_review:
                reviews = pr.get_reviews()
                if not any(r.state == "APPROVED" for r in reviews):
                    raise GitHubAuthorizationError(
                        f"PR #{req.pr_number} has no approved review (require_pr_review=true)"
                    )
            kwargs: dict[str, object] = {"merge_method": req.merge_method}
            if req.commit_title:
                kwargs["commit_title"] = req.commit_title
            if req.commit_message:
                kwargs["commit_message"] = req.commit_message
            status = pr.merge(**kwargs)
            return MergePullRequestResponse(
                pr_number=req.pr_number,
                merged=status.merged,
                sha=status.sha or "",
                message=status.message or "",
            )

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "merge_pull_request",
            repo=f"{req.owner}/{req.repo}",
            pr=req.pr_number,
            method=req.merge_method,
            merged=result.merged,
            sha=result.sha[:8] if result.sha else "",
        )
        return result
