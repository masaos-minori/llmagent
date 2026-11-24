"""scripts/mcp_servers/github/github_service_dispatch.py

GitHubService dispatch formatters and dispatch table builder.

Extends WriteDispatchOps (service_dispatch_writes, which extends the business-class
GitHubService from service_business) with the read-only fmt_* display methods and
get_dispatch_table().

Dependency direction: service_dispatch -> service_dispatch_writes -> service_business, models, mapper
Import from here:  from mcp_servers.github.github_service_dispatch import GitHubService
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from shared.formatters import fmt_md_link

from mcp_servers.github.github_models import (
    GetCommitRequest,
    GetFileContentsRequest,
    GetIssueRequest,
    GetPullRequestRequest,
    ListBranchesRequest,
    ListCommitsRequest,
    ListIssuesRequest,
    ListPullRequestsRequest,
    SearchCodeRequest,
    SearchIssuesRequest,
    SearchPullRequestsRequest,
    SearchRepositoriesRequest,
)
from mcp_servers.github.github_service_dispatch_writes import (
    WriteDispatchOps,
    _validate_request,
)
from mcp_servers.server import ToolArgs


class GitHubService(WriteDispatchOps):
    """GitHubService with dispatch formatters (extends service_dispatch_writes.WriteDispatchOps)."""

    async def fmt_search_repositories(self, args: ToolArgs) -> str:
        """Format search repositories results as markdown links with star counts."""
        req = _validate_request(SearchRepositoriesRequest, args)
        result = await self.search_repositories(req)
        lines = [
            f"{fmt_md_link(r.full_name, r.url)} ★{r.stars}\n{r.description or ''}"
            for r in result.results
        ]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_list_branches(self, args: ToolArgs) -> str:
        """Format list branches results showing branch names and SHAs."""
        req = _validate_request(ListBranchesRequest, args)
        result = await self.list_branches(req)
        lines = [
            f"{b.name} ({b.sha[:8]}){' [protected]' if b.protected else ''}"
            for b in result.branches
        ]
        return "\n".join(lines) if lines else "No branches found."

    async def fmt_list_commits(self, args: ToolArgs) -> str:
        """Format list commits results showing SHA, message, and author."""
        req = _validate_request(ListCommitsRequest, args)
        result = await self.list_commits(req)
        lines = [f"{c.sha[:8]} {c.message} ({c.author})" for c in result.commits]
        return "\n".join(lines) if lines else "No commits found."

    async def fmt_get_commit(self, args: ToolArgs) -> str:
        """Format get commit details including SHA, message, author, and files changed."""
        req = _validate_request(GetCommitRequest, args)
        result = await self.get_commit(req)
        c = result.commit
        return (
            f"{c.sha[:8]} {c.message}\n"
            f"Author: {c.author} ({c.authored_at})\n"
            f"Files changed: {c.files_changed}\nURL: {c.url}"
        )

    async def fmt_search_code(self, args: ToolArgs) -> str:
        """Format search code results as repository/path links."""
        req = _validate_request(SearchCodeRequest, args)
        result = await self.search_code(req)
        lines = [f"[{r.repository}/{r.path}]({r.url})" for r in result.results]
        return "\n".join(lines) if lines else "No results found."

    async def fmt_get_file_contents(self, args: ToolArgs) -> str:
        """Get raw file contents from GitHub."""
        req = _validate_request(GetFileContentsRequest, args)
        result = await self.get_file_contents(req)
        return result.content

    async def fmt_list_issues(self, args: ToolArgs) -> str:
        """Format list issues results showing issue numbers, states, and titles."""
        req = _validate_request(ListIssuesRequest, args)
        result = await self.list_issues(req)
        lines = [self._fmt_issue_line(i) for i in result.issues]
        return "\n\n".join(lines) if lines else "No issues found."

    async def fmt_get_issue(self, args: ToolArgs) -> str:
        """Format get issue details including number, state, title, body, and URL."""
        req = _validate_request(GetIssueRequest, args)
        result = await self.get_issue(req)
        i = result.issue
        return f"#{i.number} [{i.state}] {i.title}\n{i.body or ''}\nURL: {i.url}"

    async def fmt_search_issues(self, args: ToolArgs) -> str:
        """Format search issues results showing issue numbers, states, and titles."""
        req = _validate_request(SearchIssuesRequest, args)
        result = await self.search_issues(req)
        lines = [self._fmt_issue_line(i) for i in result.results]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_list_pull_requests(self, args: ToolArgs) -> str:
        """Format list pull requests results showing PR numbers, states, and titles."""
        req = _validate_request(ListPullRequestsRequest, args)
        result = await self.list_pull_requests(req)
        lines = [self._fmt_pr_line(pr) for pr in result.pull_requests]
        return "\n\n".join(lines) if lines else "No pull requests found."

    async def fmt_get_pull_request(self, args: ToolArgs) -> str:
        """Format get pull request details including number, state, title, refs, body, and URL."""
        req = _validate_request(GetPullRequestRequest, args)
        result = await self.get_pull_request(req)
        pr = result.pull_request
        return (
            f"#{pr.number} [{pr.state}] {pr.title}\n"
            f"head: {pr.head_ref} → base: {pr.base_ref}\n"
            f"{pr.body or ''}\nURL: {pr.url}"
        )

    async def fmt_search_pull_requests(self, args: ToolArgs) -> str:
        """Format search results as pull-request lines, identical to `fmt_list_pull_requests`."""
        req = _validate_request(SearchPullRequestsRequest, args)
        result = await self.search_pull_requests(req)
        lines = [self._fmt_pr_line(i) for i in result.results]
        return "\n\n".join(lines) if lines else "No results found."

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
