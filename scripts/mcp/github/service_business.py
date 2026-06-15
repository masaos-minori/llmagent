#!/usr/bin/env python3
"""mcp/github/service_business.py
GitHubService: core business operations (search, file ops, issues, PRs).

Dependency direction: service_business -> models, mapper
Import from here:  from mcp.github.service_business import GitHubService
"""

from __future__ import annotations

import asyncio
import fnmatch
import itertools
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any, NoReturn, TypeVar

from github import Github, GithubException, InputGitTreeElement

from mcp.github.mapper import issue_to_info, pr_to_info
from mcp.github.models import (
    AddIssueCommentRequest,
    AddIssueCommentResponse,
    BranchInfo,
    CodeSearchResult,
    CommitDetail,
    CommitInfo,
    CreateBranchRequest,
    CreateBranchResponse,
    CreateIssueRequest,
    CreateIssueResponse,
    CreateOrUpdateFileRequest,
    CreateOrUpdateFileResponse,
    CreatePullRequestRequest,
    CreatePullRequestResponse,
    DeleteRepoFileRequest,
    DeleteRepoFileResponse,
    GetCommitRequest,
    GetCommitResponse,
    GetFileContentsRequest,
    GetFileContentsResponse,
    GetIssueRequest,
    GetIssueResponse,
    GetPullRequestRequest,
    GetPullRequestResponse,
    GitHubAuditError,
    GitHubAuthorizationError,
    GitHubConfig,
    GitHubConflictError,
    GitHubNotFoundError,
    GitHubUpstreamError,
    GitHubValidationError,
    IssueInfo,
    ListBranchesRequest,
    ListBranchesResponse,
    ListCommitsRequest,
    ListCommitsResponse,
    ListIssuesRequest,
    ListIssuesResponse,
    ListPullRequestsRequest,
    ListPullRequestsResponse,
    MergePullRequestRequest,
    MergePullRequestResponse,
    PullRequestInfo,
    PushFilesRequest,
    PushFilesResponse,
    RepositoryInfo,
    SearchCodeRequest,
    SearchCodeResponse,
    SearchIssuesRequest,
    SearchIssuesResponse,
    SearchPullRequestsRequest,
    SearchPullRequestsResponse,
    SearchRepositoriesRequest,
    SearchRepositoriesResponse,
    UpdatePullRequestRequest,
    UpdatePullRequestResponse,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

class GitHubService:
    """Encapsulates GitHub API operations via PyGithub."""

    def __init__(self, gh: Github, cfg: GitHubConfig) -> None:
        self._gh = gh
        self._cfg = cfg
        self._default_per_page = cfg.default_per_page
        self._max_per_page = cfg.max_per_page

    def _clamp_per_page(self, per_page: int) -> int:
        """Clamp per_page to the configured maximum to prevent oversized API calls."""
        return min(per_page, self._max_per_page)

    def _assert_allowed_repo(self, owner: str, repo: str) -> None:
        """Raise GitHubAuthorizationError if owner/repo is not permitted.

        Behavior when allowed_repos is empty depends on allowed_repos_mode:
          fail_open:    empty list = allow all repositories
          fail_closed:  empty list = deny all repositories
        """
        allowed = self._cfg.allowed_repos
        mode = self._cfg.allowed_repos_mode
        slug = f"{owner}/{repo}"
        if not allowed:
            if mode == "fail_closed":
                raise GitHubAuthorizationError(
                    f"Repository '{slug}' is denied:"
                    " allowed_repos is empty (fail_closed mode)"
                )
            return  # fail_open: empty list = allow all
        if slug not in allowed:
            raise GitHubAuthorizationError(f"Repository not in allowed_repos: {slug}")

    def _assert_allowed_path(self, path: str) -> None:
        """Raise GitHubAuthorizationError if path matches a denied glob pattern."""
        for pattern in self._cfg.path_denylist:
            if fnmatch.fnmatch(path, pattern):
                raise GitHubAuthorizationError(
                    f"Path '{path}' is denied by path_denylist pattern '{pattern}'"
                )

    def _assert_max_file_size(self, content: str, path: str) -> None:
        """Raise GitHubValidationError if file content exceeds max_file_size_kb."""
        max_kb = self._cfg.max_file_size_kb
        if max_kb <= 0:
            return  # 0 = disabled
        size_kb = len(content.encode("utf-8")) / 1024
        if size_kb > max_kb:
            raise GitHubValidationError(
                f"File '{path}' exceeds max_file_size_kb:"
                f" {size_kb:.1f} KB > {max_kb} KB"
            )

    def _write_github_audit_log(self, op: str, **kwargs: Any) -> None:
        """Append one structured audit record to the GitHub audit log file.

        Raises GitHubAuditError when audit_log_path is configured and write fails.
        Skips silently when audit_log_path is empty.
        """
        if not self._cfg.audit_log_path:
            return
        ts = datetime.now(tz=UTC).isoformat()
        fields = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
        record = f"{ts} op={op} {fields}\n"
        try:
            with open(self._cfg.audit_log_path, "a", encoding="utf-8") as fh:
                fh.write(record)
        except OSError as e:
            raise GitHubAuditError(
                f"Audit log write failed ({self._cfg.audit_log_path}): {e}"
            ) from e

    def _assert_allowed_branch(self, owner: str, repo: str, branch: str) -> None:
        """Raise GitHubAuthorizationError if branch matches a protected_branches pattern.

        Patterns follow fnmatch glob syntax: 'main' matches exactly, 'release/*'
        matches any release branch. An empty list means no branch restrictions.
        """
        for pattern in self._cfg.protected_branches:
            if fnmatch.fnmatch(branch, pattern):
                raise GitHubAuthorizationError(
                    f"Branch '{branch}' is protected in {owner}/{repo}"
                    f" (matches pattern '{pattern}')"
                )

    def _get_repo(self, owner: str, repo: str) -> Any:
        """Return a PyGithub Repository object for the given owner/repo slug."""
        return self._gh.get_repo(f"{owner}/{repo}")

    async def _resolve_and_check_branch(
        self, owner: str, repo: str, branch: str
    ) -> None:
        """Resolve the effective branch and apply protected_branches check.

        When branch is "" (unspecified), the default branch is fetched via GitHub API.
        Skips entirely when protected_branches is empty (no restrictions configured).
        """
        if not self._cfg.protected_branches:
            return
        if branch:
            self._assert_allowed_branch(owner, repo, branch)
            return
        # branch="" (unspecified): resolve default branch via GitHub API then check
        default_branch: str = await self._run_github(
            lambda: self._get_repo(owner, repo).default_branch
        )
        self._assert_allowed_branch(owner, repo, default_branch)

    @staticmethod
    def _handle_github_error(e: GithubException) -> NoReturn:
        """Convert a GithubException to a domain exception and raise it.
        Declared as NoReturn so callers do not need to write their own raise.
        """
        if e.status == HTTPStatus.NOT_FOUND:
            raise GitHubNotFoundError("Resource not found")
        if e.status == HTTPStatus.FORBIDDEN:
            raise GitHubAuthorizationError(
                "GitHub API rate limit exceeded or access denied"
            )
        if e.status == HTTPStatus.CONFLICT:
            raise GitHubConflictError(f"GitHub API conflict (status={e.status})")
        if e.status in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY):
            raise GitHubValidationError(
                f"GitHub API validation error (status={e.status})"
            )
        raise GitHubUpstreamError(f"GitHub API error (status={e.status})")

    async def _run_github(self, func: Callable[[], T]) -> T:
        """Run a synchronous PyGithub call in the thread pool.
        Converts GithubException to domain exceptions so endpoints stay free of
        try/except boilerplate.
        """
        try:
            return await asyncio.to_thread(func)
        except GithubException as e:
            GitHubService._handle_github_error(e)

    # _issue_to_info and _pr_to_info moved to mcp.github.mapper; aliases for backward compat
    _issue_to_info = staticmethod(issue_to_info)
    _pr_to_info = staticmethod(pr_to_info)

    # ── Business operation methods ──

    async def search_repositories(
        self,
        req: SearchRepositoriesRequest,
    ) -> SearchRepositoriesResponse:
        """Search GitHub repositories by query string."""
        per_page = self._clamp_per_page(req.per_page)

        # PyGithub is synchronous; run in thread pool to avoid blocking the event loop
        def _sync() -> list[RepositoryInfo]:
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
            repo = self._get_repo(req.owner, req.repo)
            # sha kwarg selects a specific branch; omit to use the default branch
            kwargs: dict[str, Any] = {"sha": req.branch} if req.branch else {}
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

    async def get_file_contents(
        self,
        req: GetFileContentsRequest,
    ) -> GetFileContentsResponse:
        """Retrieve the contents of a single file in a repository."""

        def _sync() -> GetFileContentsResponse:
            repo = self._get_repo(req.owner, req.repo)
            # ref kwarg selects branch/tag/SHA; omit to use the default branch
            kwargs: dict[str, Any] = {"ref": req.ref} if req.ref else {}
            file_content = repo.get_contents(req.path, **kwargs)
            # Guard: path points to a directory, not a file
            if isinstance(file_content, list):
                raise GitHubValidationError(
                    f"Path is a directory, not a file: {req.path}"
                )
            decoded = file_content.decoded_content.decode("utf-8", errors="replace")
            return GetFileContentsResponse(
                path=file_content.path,
                content=decoded,
                sha=file_content.sha,
                size=file_content.size,
                encoding="utf-8",
            )

        return await self._run_github(_sync)

    async def create_or_update_file(
        self,
        req: CreateOrUpdateFileRequest,
    ) -> CreateOrUpdateFileResponse:
        """Create or update a file; providing sha updates an existing file."""
        self._assert_allowed_repo(req.owner, req.repo)
        await self._resolve_and_check_branch(req.owner, req.repo, req.branch)
        self._assert_allowed_path(req.path)
        self._assert_max_file_size(req.content, req.path)

        def _sync() -> CreateOrUpdateFileResponse:
            repo = self._get_repo(req.owner, req.repo)
            # Branch kwarg is optional; omit to use the default branch
            kwargs: dict[str, Any] = {}
            if req.branch:
                kwargs["branch"] = req.branch
            encoded = req.content.encode("utf-8")
            if req.sha:
                # sha is required to update an existing file (prevents conflicts)
                raw = repo.update_file(
                    req.path,
                    req.message,
                    encoded,
                    req.sha,
                    **kwargs,
                )
                operation = "updated"
            else:
                raw = repo.create_file(req.path, req.message, encoded, **kwargs)
                operation = "created"
            commit_sha = raw["commit"].sha
            return CreateOrUpdateFileResponse(
                path=req.path,
                commit_sha=commit_sha,
                operation=operation,
            )

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "create_or_update_file",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch or "(default)",
            path=req.path,
            operation=result.operation,
            commit=result.commit_sha[:8],
        )
        return result

    async def push_files(self, req: PushFilesRequest) -> PushFilesResponse:
        """Push multiple files as a single atomic commit via the Git Tree API."""
        self._assert_allowed_repo(req.owner, req.repo)
        self._assert_allowed_branch(req.owner, req.repo, req.branch)
        for f in req.files:
            self._assert_allowed_path(f.path)
            self._assert_max_file_size(f.content, f.path)

        def _sync() -> PushFilesResponse:
            repo = self._get_repo(req.owner, req.repo)
            branch_ref = repo.get_git_ref(f"heads/{req.branch}")
            parent_commit = repo.get_git_commit(branch_ref.object.sha)
            # Create individual blobs then assemble them into a single tree
            tree_elements = [
                InputGitTreeElement(
                    path=f.path,
                    mode="100644",
                    type="blob",
                    sha=repo.create_git_blob(f.content, "utf-8").sha,
                )
                for f in req.files
            ]
            new_tree = repo.create_git_tree(tree_elements, parent_commit.tree)
            new_commit = repo.create_git_commit(req.message, new_tree, [parent_commit])
            branch_ref.edit(new_commit.sha)
            return PushFilesResponse(
                branch=req.branch,
                commit_sha=new_commit.sha,
                files_pushed=len(req.files),
            )

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "push_files",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch,
            paths=[f.path for f in req.files],
            commit=result.commit_sha[:8],
        )
        return result

    async def delete_repo_file(
        self,
        req: DeleteRepoFileRequest,
    ) -> DeleteRepoFileResponse:
        """Delete a file from a repository; sha required to prevent conflicts."""
        self._assert_allowed_repo(req.owner, req.repo)
        await self._resolve_and_check_branch(req.owner, req.repo, req.branch)
        self._assert_allowed_path(req.path)

        def _sync() -> DeleteRepoFileResponse:
            repo = self._get_repo(req.owner, req.repo)
            # Branch kwarg is optional; omit to use the default branch
            kwargs: dict[str, Any] = {}
            if req.branch:
                kwargs["branch"] = req.branch
            raw = repo.delete_file(req.path, req.message, req.sha, **kwargs)
            return DeleteRepoFileResponse(path=req.path, commit_sha=raw["commit"].sha)

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "delete_repo_file",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch or "(default)",
            path=req.path,
            commit=result.commit_sha[:8],
        )
        return result

    async def list_issues(self, req: ListIssuesRequest) -> ListIssuesResponse:
        """Retrieve the list of issues for a repository."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[IssueInfo]:
            repo = self._get_repo(req.owner, req.repo)
            issues_slice = itertools.islice(repo.get_issues(state=req.state), per_page)
            return [GitHubService._issue_to_info(i) for i in issues_slice]

        issues = await self._run_github(_sync)
        return ListIssuesResponse(issues=issues)

    async def get_issue(self, req: GetIssueRequest) -> GetIssueResponse:
        """Retrieve a specific issue by number."""

        def _sync() -> IssueInfo:
            repo = self._get_repo(req.owner, req.repo)
            return GitHubService._issue_to_info(repo.get_issue(number=req.issue_number))

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
            return GitHubService._issue_to_info(issue)

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
            return [GitHubService._issue_to_info(i) for i in issues_slice]

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

    async def list_pull_requests(
        self,
        req: ListPullRequestsRequest,
    ) -> ListPullRequestsResponse:
        """Retrieve the list of pull requests for a repository."""
        per_page = self._clamp_per_page(req.per_page)

        def _sync() -> list[PullRequestInfo]:
            repo = self._get_repo(req.owner, req.repo)
            prs_slice = itertools.islice(repo.get_pulls(state=req.state), per_page)
            return [GitHubService._pr_to_info(pr) for pr in prs_slice]

        prs = await self._run_github(_sync)
        return ListPullRequestsResponse(pull_requests=prs)

    async def get_pull_request(
        self,
        req: GetPullRequestRequest,
    ) -> GetPullRequestResponse:
        """Retrieve a specific pull request by number."""

        def _sync() -> PullRequestInfo:
            repo = self._get_repo(req.owner, req.repo)
            return GitHubService._pr_to_info(repo.get_pull(number=req.pr_number))

        pr = await self._run_github(_sync)
        return GetPullRequestResponse(pull_request=pr)

    async def create_pull_request(
        self,
        req: CreatePullRequestRequest,
    ) -> CreatePullRequestResponse:
        """Create a new pull request in a repository."""
        self._assert_allowed_repo(req.owner, req.repo)

        def _sync() -> PullRequestInfo:
            repo = self._get_repo(req.owner, req.repo)
            pr = repo.create_pull(
                title=req.title,
                body=req.body,
                head=req.head,
                base=req.base,
            )
            return GitHubService._pr_to_info(pr)

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
            # Append is:pr automatically to filter for pull requests only
            query = req.query if "is:pr" in req.query else f"{req.query} is:pr"
            issues_slice = itertools.islice(
                self._gh.search_issues(query=query),
                per_page,
            )
            return [GitHubService._issue_to_info(i) for i in issues_slice]

        results = await self._run_github(_sync)
        return SearchPullRequestsResponse(query=req.query, results=results)

    async def update_pull_request(
        self,
        req: UpdatePullRequestRequest,
    ) -> UpdatePullRequestResponse:
        """Update the title, body, or state of a pull request."""
        self._assert_allowed_repo(req.owner, req.repo)

        def _sync() -> PullRequestInfo:
            repo = self._get_repo(req.owner, req.repo)
            pr = repo.get_pull(number=req.pr_number)
            # Build edit kwargs only for fields that were explicitly provided
            kwargs: dict[str, Any] = {}
            if req.title is not None:
                kwargs["title"] = req.title
            if req.body is not None:
                kwargs["body"] = req.body
            if req.state is not None:
                kwargs["state"] = req.state
            if kwargs:
                pr.edit(**kwargs)
            return GitHubService._pr_to_info(pr)

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
        # Block rebase merge when allow_force_push is false (rebase rewrites history)
        if not self._cfg.allow_force_push and req.merge_method == "rebase":
            raise GitHubAuthorizationError(
                "Rebase merge is disabled (allow_force_push=false)"
            )

        def _sync() -> MergePullRequestResponse:
            repo = self._get_repo(req.owner, req.repo)
            pr = repo.get_pull(number=req.pr_number)
            # Block merge into protected base branch
            self._assert_allowed_branch(req.owner, req.repo, pr.base.ref)
            # Require at least one approved review when require_pr_review is true
            if self._cfg.require_pr_review:
                reviews = pr.get_reviews()
                if not any(r.state == "APPROVED" for r in reviews):
                    raise GitHubAuthorizationError(
                        f"PR #{req.pr_number} has no approved review"
                        " (require_pr_review=true)"
                    )
            # Build merge kwargs; title/message are optional overrides
            kwargs: dict[str, Any] = {"merge_method": req.merge_method}
            if req.commit_title:
                kwargs["commit_title"] = req.commit_title
            if req.commit_message:
                kwargs["commit_message"] = req.commit_message
            # merge() returns a MergedStatus object
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

    # ── Static formatters ──

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
            f" ({pr.head_ref}→{pr.base_ref})\n{pr.url}"
        )

    # ── Dispatch handlers: call service methods and format results as plain text ──

