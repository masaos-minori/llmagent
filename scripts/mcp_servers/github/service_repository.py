#!/usr/bin/env python3
"""mcp_servers/github/service_repository.py

Repository/branch/commit/code search operations for GitHubService.

Dependency direction: service_repository → service_security, models
"""

from __future__ import annotations

import itertools
from typing import Any

from github import Github

from mcp_servers.github.models_repository import (
    BranchInfo,
    CodeSearchResult,
    CommitDetail,
    CommitInfo,
    CreateBranchRequest,
    CreateBranchResponse,
    GetCommitRequest,
    GetCommitResponse,
    ListBranchesRequest,
    ListBranchesResponse,
    ListCommitsRequest,
    ListCommitsResponse,
    RepositoryInfo,
    SearchCodeRequest,
    SearchCodeResponse,
    SearchRepositoriesRequest,
    SearchRepositoriesResponse,
)
from mcp_servers.github.service_security import GitHubSecurityGuards


class RepositoryOps(GitHubSecurityGuards):
    """Repository search, branch, commit, and code search operations."""

    def __init__(self, gh: Github, cfg: Any) -> None:  # noqa: ANN401
        """Initialize with GitHub client and config, inheriting security guards."""
        super().__init__(gh, cfg)

    async def search_repositories(
        self,
        req: SearchRepositoriesRequest,
    ) -> SearchRepositoriesResponse:
        """Search GitHub repositories by query string."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[RepositoryInfo]:
            """Synchronously search repositories via GitHub API."""
            results_iter = self._gh.search_repositories(query=req.query)
            return [
                RepositoryInfo(
                    full_name=r.full_name,
                    description=r.description,
                    url=r.html_url,
                    stars=r.stargazers_count,
                    forks=r.forks_count,
                    language=r.language,
                    updated_at=r.updated_at.isoformat(),
                )
                for r in itertools.islice(results_iter, per_page)
            ]

        repos = await self._run_github(_sync)
        return SearchRepositoriesResponse(query=req.query, results=repos)

    async def list_branches(self, req: ListBranchesRequest) -> ListBranchesResponse:
        """Retrieve the list of branches for a repository."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[BranchInfo]:
            """Synchronously fetch branches via GitHub API."""
            repo = self._get_repo(req.owner, req.repo)
            return [
                BranchInfo(name=b.name, sha=b.commit.sha, protected=b.protected)
                for b in itertools.islice(repo.get_branches(), per_page)
            ]

        branches = await self._run_github(_sync)
        return ListBranchesResponse(branches=branches)

    async def create_branch(self, req: CreateBranchRequest) -> CreateBranchResponse:
        """Create a branch; when from_branch is omitted, derives from default branch."""
        self._assert_allowed_repo(req.owner, req.repo)

        def _sync() -> CreateBranchResponse:
            """Execute the GitHub API call synchronously inside the thread pool."""
            repo = self._get_repo(req.owner, req.repo)
            # Resolve source branch; fall back to default branch when omitted
            source_name = req.from_branch or repo.default_branch
            source = repo.get_branch(source_name)
            repo.create_git_ref(
                ref=f"refs/heads/{req.branch_name}",
                sha=source.commit.sha,
            )
            return CreateBranchResponse(
                branch_name=req.branch_name,
                sha=source.commit.sha,
            )

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "create_branch",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch_name,
            from_branch=req.from_branch or "(default)",
            sha=result.sha[:8],
        )
        return result

    async def list_commits(self, req: ListCommitsRequest) -> ListCommitsResponse:
        """Retrieve the commit history for a repository."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[CommitInfo]:
            """Execute the GitHub API call synchronously inside the thread pool."""
            repo = self._get_repo(req.owner, req.repo)
            # sha kwarg selects a specific branch; omit to use the default branch
            kwargs: dict[str, object] = {"sha": req.branch} if req.branch else {}
            return [
                CommitInfo(
                    sha=c.sha,
                    message=c.commit.message.split("\n")[0],
                    author=c.commit.author.name,
                    authored_at=c.commit.author.date.isoformat(),
                    url=c.html_url,
                )
                for c in itertools.islice(repo.get_commits(**kwargs), per_page)
            ]

        commits = await self._run_github(_sync)
        return ListCommitsResponse(commits=commits)

    async def get_commit(self, req: GetCommitRequest) -> GetCommitResponse:
        """Retrieve details of a specific commit."""

        def _sync() -> GetCommitResponse:
            """Execute the GitHub API call synchronously inside the thread pool."""
            repo = self._get_repo(req.owner, req.repo)
            commit = repo.get_commit(req.sha)
            return GetCommitResponse(
                commit=CommitDetail(
                    sha=commit.sha,
                    message=commit.commit.message.split("\n")[0],
                    author=commit.commit.author.name,
                    authored_at=commit.commit.author.date.isoformat(),
                    url=commit.html_url,
                    files_changed=len(commit.files),
                ),
            )

        return await self._run_github(_sync)

    async def search_code(self, req: SearchCodeRequest) -> SearchCodeResponse:
        """Search code on GitHub by full-text query."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[CodeSearchResult]:
            """Execute the GitHub API call synchronously inside the thread pool."""
            results_iter = self._gh.search_code(query=req.query)
            return [
                CodeSearchResult(
                    repository=r.repository.full_name,
                    path=r.path,
                    url=r.html_url,
                    score=r.score,
                )
                for r in itertools.islice(results_iter, per_page)
            ]

        results = await self._run_github(_sync)
        return SearchCodeResponse(query=req.query, results=results)
