"""mcp/github/service_dispatch.py
GitHubService dispatch formatters and dispatch table builder.

Extends the business-class GitHubService from service_business with
fmt_* display methods and get_dispatch_table().

Dependency direction: service_dispatch -> service_business, models, mapper
Import from here:  from mcp.github.service_dispatch import GitHubService
"""

from __future__ import annotations

import logging

from shared.formatters import fmt_md_link

from mcp.github.models import (
    AddIssueCommentRequest,
    CreateBranchRequest,
    CreateIssueRequest,
    CreateOrUpdateFileRequest,
    CreatePullRequestRequest,
    DeleteRepoFileRequest,
    MergePullRequestRequest,
    PushFilesRequest,
    UpdatePullRequestRequest,
)
from mcp.github.service_business import GitHubService as _GitHubServiceCore

logger = logging.getLogger(__name__)


class GitHubService(_GitHubServiceCore):
    """GitHubService with dispatch formatters (extends service_business.GitHubService)."""

    async def fmt_search_repositories(self, args: dict) -> str:
        result = await self.search_repositories(args)  # type: ignore[arg-type]
        lines = [
            f"{fmt_md_link(r.full_name, r.url)} ★{r.stars}\n{r.description or ''}"
            for r in result.results
        ]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_list_branches(self, args: dict) -> str:
        result = await self.list_branches(args)  # type: ignore[arg-type]
        lines = [
            f"{b.name} ({b.sha[:8]}){' [protected]' if b.protected else ''}"
            for b in result.branches
        ]
        return "\n".join(lines) if lines else "No branches found."

    @staticmethod
    def _dry_run_preview(preview: str) -> str:
        """Return a JSON dry-run preview response string."""
        from shared.json_utils import dumps as _json_dumps

        return _json_dumps({"preview": preview, "dry_run": True})

    async def fmt_create_branch(self, args: dict) -> str:
        req = CreateBranchRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            from_b = req.from_branch or "(default branch)"
            return self._dry_run_preview(
                f"Would create branch '{req.branch_name}' from '{from_b}'"
                f" in {req.owner}/{req.repo}"
            )
        result = await self.create_branch(req)
        return f"Branch created: {result.branch_name} (SHA: {result.sha[:8]})"

    async def fmt_list_commits(self, args: dict) -> str:
        result = await self.list_commits(args)  # type: ignore[arg-type]
        lines = [f"{c.sha[:8]} {c.message} ({c.author})" for c in result.commits]
        return "\n".join(lines) if lines else "No commits found."

    async def fmt_get_commit(self, args: dict) -> str:
        result = await self.get_commit(args)  # type: ignore[arg-type]
        c = result.commit
        return (
            f"{c.sha[:8]} {c.message}\n"
            f"Author: {c.author} ({c.authored_at})\n"
            f"Files changed: {c.files_changed}\nURL: {c.url}"
        )

    async def fmt_search_code(self, args: dict) -> str:
        result = await self.search_code(args)  # type: ignore[arg-type]
        lines = [f"[{r.repository}/{r.path}]({r.url})" for r in result.results]
        return "\n".join(lines) if lines else "No results found."

    async def fmt_get_file_contents(self, args: dict) -> str:
        result = await self.get_file_contents(args)  # type: ignore[arg-type]
        return result.content

    async def fmt_create_or_update_file(self, args: dict) -> str:
        req = CreateOrUpdateFileRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            op = "update" if req.sha else "create"
            branch = req.branch or "(default branch)"
            return self._dry_run_preview(
                f"Would {op} file '{req.path}' on branch '{branch}'"
                f" in {req.owner}/{req.repo}"
            )
        result = await self.create_or_update_file(req)
        return f"{result.operation}: {result.path} (commit: {result.commit_sha[:8]})"

    async def fmt_push_files(self, args: dict) -> str:
        req = PushFilesRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            paths = [f.path for f in req.files]
            return self._dry_run_preview(
                f"Would push {len(paths)} file(s) to branch '{req.branch}'"
                f" in {req.owner}/{req.repo}: {paths}"
            )
        result = await self.push_files(req)
        sha_short = result.commit_sha[:8]
        return (
            f"Pushed: branch={result.branch}"
            f" files={result.files_pushed} commit={sha_short}"
        )

    async def fmt_delete_file(self, args: dict) -> str:
        req = DeleteRepoFileRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            branch = req.branch or "(default branch)"
            return self._dry_run_preview(
                f"Would delete '{req.path}' from branch '{branch}'"
                f" in {req.owner}/{req.repo}"
            )
        result = await self.delete_repo_file(req)
        return f"Deleted: {result.path} (commit: {result.commit_sha[:8]})"

    async def fmt_list_issues(self, args: dict) -> str:
        result = await self.list_issues(args)  # type: ignore[arg-type]
        lines = [GitHubService._fmt_issue_line(i) for i in result.issues]
        return "\n\n".join(lines) if lines else "No issues found."

    async def fmt_get_issue(self, args: dict) -> str:
        result = await self.get_issue(args)  # type: ignore[arg-type]
        i = result.issue
        return f"#{i.number} [{i.state}] {i.title}\n{i.body or ''}\nURL: {i.url}"

    async def fmt_create_issue(self, args: dict) -> str:
        req = CreateIssueRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            labels = f" labels={req.labels}" if req.labels else ""
            return self._dry_run_preview(
                f"Would create issue '{req.title}'{labels} in {req.owner}/{req.repo}"
            )
        result = await self.create_issue(req)
        i = result.issue
        return f"Created: #{i.number} {i.title}\n{i.url}"

    async def fmt_search_issues(self, args: dict) -> str:
        result = await self.search_issues(args)  # type: ignore[arg-type]
        lines = [GitHubService._fmt_issue_line(i) for i in result.results]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_add_issue_comment(self, args: dict) -> str:
        req = AddIssueCommentRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            return self._dry_run_preview(
                f"Would post comment on issue #{req.issue_number}"
                f" in {req.owner}/{req.repo}"
            )
        result = await self.add_issue_comment(req)
        return f"Comment posted: #{result.issue_number} {result.comment_url}"

    async def fmt_list_pull_requests(self, args: dict) -> str:
        result = await self.list_pull_requests(args)  # type: ignore[arg-type]
        lines = [GitHubService._fmt_pr_line(pr) for pr in result.pull_requests]
        return "\n\n".join(lines) if lines else "No pull requests found."

    async def fmt_get_pull_request(self, args: dict) -> str:
        result = await self.get_pull_request(args)  # type: ignore[arg-type]
        pr = result.pull_request
        return (
            f"#{pr.number} [{pr.state}] {pr.title}\n"
            f"head: {pr.head_ref} → base: {pr.base_ref}\n"
            f"{pr.body or ''}\nURL: {pr.url}"
        )

    async def fmt_create_pull_request(self, args: dict) -> str:
        req = CreatePullRequestRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            return self._dry_run_preview(
                f"Would create PR '{req.title}' ({req.head} → {req.base})"
                f" in {req.owner}/{req.repo}"
            )
        result = await self.create_pull_request(req)
        pr = result.pull_request
        return (
            f"Created: #{pr.number} {pr.title}\n"
            f"head: {pr.head_ref} → base: {pr.base_ref}\n"
            f"URL: {pr.url}"
        )

    async def fmt_search_pull_requests(self, args: dict) -> str:
        result = await self.search_pull_requests(args)  # type: ignore[arg-type]
        lines = [GitHubService._fmt_issue_line(i) for i in result.results]
        return "\n\n".join(lines) if lines else "No results found."

    async def fmt_update_pull_request(self, args: dict) -> str:
        req = UpdatePullRequestRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            fields: list[str] = []
            if req.title is not None:
                fields.append(f"title='{req.title}'")
            if req.state is not None:
                fields.append(f"state={req.state}")
            changes = ", ".join(fields) or "(no changes)"
            return self._dry_run_preview(
                f"Would update PR #{req.pr_number} in {req.owner}/{req.repo}: {changes}"
            )
        result = await self.update_pull_request(req)
        pr = result.pull_request
        return f"Updated: #{pr.number} [{pr.state}] {pr.title}\n{pr.url}"

    async def fmt_merge_pull_request(self, args: dict) -> str:
        req = MergePullRequestRequest(**args)
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            return self._dry_run_preview(
                f"Would merge PR #{req.pr_number} in {req.owner}/{req.repo}"
                f" using method='{req.merge_method}'"
            )
        result = await self.merge_pull_request(req)
        sha_short = result.sha[:8] if result.sha else "N/A"
        return (
            f"Merged: #{result.pr_number} merged={result.merged}"
            f" sha={sha_short}\n{result.message}"
        )

    def get_dispatch_table(
        self,
    ) -> dict[str, callable]:  # type: ignore[valid-type]
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
