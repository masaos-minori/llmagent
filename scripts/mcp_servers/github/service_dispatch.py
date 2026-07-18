"""mcp_servers/github/service_dispatch.py

GitHubService dispatch formatters and dispatch table builder.

Extends the business-class GitHubService from service_business with
fmt_* display methods and get_dispatch_table().

Dependency direction: service_dispatch -> service_business, models, mapper
Import from here:  from mcp_servers.github.service_dispatch import GitHubService
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from shared.formatters import fmt_md_link
from shared.json_utils import dumps as _json_dumps

from mcp_servers.github.models import (
    AddIssueCommentRequest,
    CreateBranchRequest,
    CreateIssueRequest,
    CreateOrUpdateFileRequest,
    CreatePullRequestRequest,
    DeleteRepoFileRequest,
    GetCommitRequest,
    GetFileContentsRequest,
    GetIssueRequest,
    GetPullRequestRequest,
    ListBranchesRequest,
    ListCommitsRequest,
    ListIssuesRequest,
    ListPullRequestsRequest,
    MergePullRequestRequest,
    PushFilesRequest,
    SearchCodeRequest,
    SearchIssuesRequest,
    SearchPullRequestsRequest,
    SearchRepositoriesRequest,
    UpdatePullRequestRequest,
)
from mcp_servers.github.service_business import GitHubService as _GitHubServiceCore

logger = logging.getLogger(__name__)


class GitHubService(_GitHubServiceCore):
    """GitHubService with dispatch formatters (extends service_business.GitHubService)."""

    async def fmt_search_repositories(self, args: dict) -> str:
        """Format search repositories results as markdown links with star counts."""
        result = await self.search_repositories(SearchRepositoriesRequest(**args))
        lines = [
            f"{fmt_md_link(r.full_name, r.url)} ★{r.stars}\n{r.description or ''}"
            for r in result.results
        ]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_list_branches(self, args: dict) -> str:
        """Format list branches results showing branch names and SHAs."""
        result = await self.list_branches(ListBranchesRequest(**args))
        lines = [
            f"{b.name} ({b.sha[:8]}){' [protected]' if b.protected else ''}"
            for b in result.branches
        ]
        return "\n".join(lines) if lines else "No branches found."

    @staticmethod
    def _dry_run_preview(preview: str) -> str:
        """Return a JSON dry-run preview response string."""
        result: str = _json_dumps({"preview": preview, "dry_run": True})
        return result

    async def _execute_with_dry_run(
        self,
        owner: str,
        repo: str,
        dry_run: bool,
        preview_callback: Callable[[], str],
        execute_callback: Callable[[], Awaitable[str]],
    ) -> str:
        """Execute a GitHub operation with optional dry-run mode."""
        self._assert_allowed_repo(owner, repo)
        if dry_run:
            return self._dry_run_preview(preview_callback())
        return await execute_callback()

    async def _execute_with_dry_run_preview(
        self,
        owner: str,
        repo: str,
        dry_run: bool,
        preview_str: str,
        execute_callback: Callable[[], Awaitable[str]],
    ) -> str:
        """Execute a GitHub operation with optional dry-run mode (string preview)."""
        return await self._execute_with_dry_run(
            owner, repo, dry_run, lambda: preview_str, execute_callback
        )

    async def fmt_create_branch(self, args: dict) -> str:
        """Format create branch operation result with optional dry-run support."""
        req = CreateBranchRequest(**args)
        from_b = req.from_branch or "(default branch)"

        async def _execute() -> str:
            """Create a new branch on GitHub."""
            result = await self.create_branch(req)
            return f"Branch created: {result.branch_name} (SHA: {result.sha[:8]})"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would create branch '{req.branch_name}' from '{from_b}' in {req.owner}/{req.repo}"
            ),
            _execute,
        )

    async def fmt_list_commits(self, args: dict) -> str:
        """Format list commits results showing SHA, message, and author."""
        result = await self.list_commits(ListCommitsRequest(**args))
        lines = [f"{c.sha[:8]} {c.message} ({c.author})" for c in result.commits]
        return "\n".join(lines) if lines else "No commits found."

    async def fmt_get_commit(self, args: dict) -> str:
        """Format get commit details including SHA, message, author, and files changed."""
        result = await self.get_commit(GetCommitRequest(**args))
        c = result.commit
        return (
            f"{c.sha[:8]} {c.message}\n"
            f"Author: {c.author} ({c.authored_at})\n"
            f"Files changed: {c.files_changed}\nURL: {c.url}"
        )

    async def fmt_search_code(self, args: dict) -> str:
        """Format search code results as repository/path links."""
        result = await self.search_code(SearchCodeRequest(**args))
        lines = [f"[{r.repository}/{r.path}]({r.url})" for r in result.results]
        return "\n".join(lines) if lines else "No results found."

    async def fmt_get_file_contents(self, args: dict) -> str:
        """Get raw file contents from GitHub."""
        result = await self.get_file_contents(GetFileContentsRequest(**args))
        content: str = result.content
        return content

    async def fmt_create_or_update_file(self, args: dict) -> str:
        """Format create or update file operation result with optional dry-run support."""
        req = CreateOrUpdateFileRequest(**args)
        op = "update" if req.sha else "create"
        branch = req.branch or "(default branch)"

        async def _execute() -> str:
            """Create or update a file on GitHub."""
            result = await self.create_or_update_file(req)
            return (
                f"{result.operation}: {result.path} (commit: {result.commit_sha[:8]})"
            )

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would {op} file '{req.path}' on branch '{branch}' in {req.owner}/{req.repo}"
            ),
            _execute,
        )

    async def fmt_push_files(self, args: dict) -> str:
        """Format push files operation result with optional dry-run support."""
        req = PushFilesRequest(**args)
        paths = [f.path for f in req.files]

        async def _execute() -> str:
            """Push multiple files to a branch on GitHub."""
            result = await self.push_files(req)
            sha_short = result.commit_sha[:8]
            return f"Pushed: branch={result.branch} files={result.files_pushed} commit={sha_short}"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would push {len(paths)} file(s) to branch '{req.branch}' in {req.owner}/{req.repo}: {paths}"
            ),
            _execute,
        )

    async def fmt_delete_file(self, args: dict) -> str:
        """Format delete file operation result with optional dry-run support."""
        req = DeleteRepoFileRequest(**args)
        branch = req.branch or "(default branch)"

        async def _execute() -> str:
            """Delete a file from a GitHub repository."""
            result = await self.delete_repo_file(req)
            return f"Deleted: {result.path} (commit: {result.commit_sha[:8]})"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would delete '{req.path}' from branch '{branch}' in {req.owner}/{req.repo}"
            ),
            _execute,
        )

    async def fmt_list_issues(self, args: dict) -> str:
        """Format list issues results showing issue numbers, states, and titles."""
        result = await self.list_issues(ListIssuesRequest(**args))
        lines = [GitHubService._fmt_issue_line(i) for i in result.issues]
        return "\n\n".join(lines) if lines else "No issues found."

    async def fmt_get_issue(self, args: dict) -> str:
        """Format get issue details including number, state, title, body, and URL."""
        result = await self.get_issue(GetIssueRequest(**args))
        i = result.issue
        return f"#{i.number} [{i.state}] {i.title}\n{i.body or ''}\nURL: {i.url}"

    async def fmt_create_issue(self, args: dict) -> str:
        """Format create issue operation result with optional dry-run support."""
        req = CreateIssueRequest(**args)
        labels = f" labels={req.labels}" if req.labels else ""

        async def _execute() -> str:
            """Create a new issue on GitHub."""
            result = await self.create_issue(req)
            i = result.issue
            return f"Created: #{i.number} {i.title}\n{i.url}"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would create issue '{req.title}'{labels} in {req.owner}/{req.repo}"
            ),
            _execute,
        )

    async def fmt_search_issues(self, args: dict) -> str:
        """Format search issues results showing issue numbers, states, and titles."""
        result = await self.search_issues(SearchIssuesRequest(**args))
        lines = [GitHubService._fmt_issue_line(i) for i in result.results]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_add_issue_comment(self, args: dict) -> str:
        """Format add issue comment operation result with optional dry-run support."""
        req = AddIssueCommentRequest(**args)

        async def _execute() -> str:
            """Post a comment on an existing GitHub issue."""
            result = await self.add_issue_comment(req)
            return f"Comment posted: #{result.issue_number} {result.comment_url}"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would post comment on issue #{req.issue_number} in {req.owner}/{req.repo}"
            ),
            _execute,
        )

    async def fmt_list_pull_requests(self, args: dict) -> str:
        """Format list pull requests results showing PR numbers, states, and titles."""
        result = await self.list_pull_requests(ListPullRequestsRequest(**args))
        lines = [GitHubService._fmt_pr_line(pr) for pr in result.pull_requests]
        return "\n\n".join(lines) if lines else "No pull requests found."

    async def fmt_get_pull_request(self, args: dict) -> str:
        """Format get pull request details including number, state, title, refs, body, and URL."""
        result = await self.get_pull_request(GetPullRequestRequest(**args))
        pr = result.pull_request
        return (
            f"#{pr.number} [{pr.state}] {pr.title}\n"
            f"head: {pr.head_ref} → base: {pr.base_ref}\n"
            f"{pr.body or ''}\nURL: {pr.url}"
        )

    async def fmt_create_pull_request(self, args: dict) -> str:
        """Format create pull request operation result with optional dry-run support."""
        req = CreatePullRequestRequest(**args)

        async def _execute() -> str:
            """Create a new pull request on GitHub."""
            result = await self.create_pull_request(req)
            pr = result.pull_request
            return f"Created: #{pr.number} {pr.title}\nhead: {pr.head_ref} → base: {pr.base_ref}\nURL: {pr.url}"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would create PR '{req.title}' ({req.head} → {req.base}) in {req.owner}/{req.repo}"
            ),
            _execute,
        )

    async def fmt_search_pull_requests(self, args: dict) -> str:
        """Format search pull requests results showing PR numbers, states, and titles."""
        result = await self.search_pull_requests(SearchPullRequestsRequest(**args))
        lines = [GitHubService._fmt_issue_line(i) for i in result.results]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_update_pull_request(self, args: dict) -> str:
        """Format update pull request operation result with optional dry-run support."""
        req = UpdatePullRequestRequest(**args)
        fields: list[str] = []
        if req.title is not None:
            fields.append(f"title='{req.title}'")
        if req.state is not None:
            fields.append(f"state={req.state}")
        changes = ", ".join(fields) or "(no changes)"

        async def _execute() -> str:
            """Update a pull request's title or state on GitHub."""
            result = await self.update_pull_request(req)
            pr = result.pull_request
            return f"Updated: #{pr.number} [{pr.state}] {pr.title}\n{pr.url}"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would update PR #{req.pr_number} in {req.owner}/{req.repo}: {changes}"
            ),
            _execute,
        )

    async def fmt_merge_pull_request(self, args: dict) -> str:
        """Format merge pull request operation result with optional dry-run support."""
        req = MergePullRequestRequest(**args)

        async def _execute() -> str:
            """Merge a pull request on GitHub."""
            result = await self.merge_pull_request(req)
            sha_short = result.sha[:8] if result.sha else "N/A"
            return f"Merged: #{result.pr_number} merged={result.merged} sha={sha_short}\n{result.message}"

        return await self._execute_with_dry_run(
            req.owner,
            req.repo,
            req.dry_run,
            lambda: (
                f"Would merge PR #{req.pr_number} in {req.owner}/{req.repo} using method='{req.merge_method}'"
            ),
            _execute,
        )

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[..., Awaitable[str]]]:
        """Build and return the MCP tool dispatch table keyed by tool name."""
        return {
            "github_search_repositories": self.fmt_search_repositories,
            "github_get_file_contents": self.fmt_get_file_contents,
            "github_list_issues": self.fmt_list_issues,
            "github_search_code": self.fmt_search_code,
            "github_get_issue": self.fmt_get_issue,
            "github_create_issue": self.fmt_create_issue,
            "github_list_pull_requests": self.fmt_list_pull_requests,
            "github_get_pull_request": self.fmt_get_pull_request,
            "github_list_commits": self.fmt_list_commits,
            "github_create_pull_request": self.fmt_create_pull_request,
            "github_create_branch": self.fmt_create_branch,
            "github_create_or_update_file": self.fmt_create_or_update_file,
            "github_add_issue_comment": self.fmt_add_issue_comment,
            "github_push_files": self.fmt_push_files,
            "github_delete_file": self.fmt_delete_file,
            "github_list_branches": self.fmt_list_branches,
            "github_get_commit": self.fmt_get_commit,
            "github_search_issues": self.fmt_search_issues,
            "github_search_pull_requests": self.fmt_search_pull_requests,
            "github_update_pull_request": self.fmt_update_pull_request,
            "github_merge_pull_request": self.fmt_merge_pull_request,
        }
