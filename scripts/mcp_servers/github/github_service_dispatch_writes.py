#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_service_dispatch_writes.py — Write-tool dispatch formatters and the dry-run funnel.

The nine github write tools build their request model, render the preview text a dry
run would report, and hand both to _execute_with_dry_run(), which checks repository
authorization and writes the intent audit before a real run executes; a dry run audits
nothing and calls no API. Read-only display formatters and
get_dispatch_table() stay in service_dispatch, which composes this class.

Dependency direction: service_dispatch_writes -> service_business, models
Import from here:  from mcp_servers.github.github_service_dispatch_writes import WriteDispatchOps
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from pydantic import BaseModel, ValidationError
from shared.json_utils import dumps as _json_dumps

from mcp_servers.github.github_models import (
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
from mcp_servers.github.github_models_config import GitHubValidationError
from mcp_servers.github.github_service_business import (
    GitHubService as _GitHubServiceCore,
)
from mcp_servers.server import ToolArgs


class _DryRunRequest(Protocol):
    """Contract for the request models the dry-run funnel accepts.

    Every write request model handled below carries the repository identity and the
    dry-run flag. Naming that here removes the repeated `req.owner, req.repo,
    req.dry_run` triple from all nine call sites.
    """

    owner: str
    repo: str
    dry_run: bool


_PREVIEW_BODY_LIMIT = 80


def _fmt_body_field(body: str) -> str:
    """Render the body an update would send, capped so the preview stays one line.

    The real run sends the whole body. The preview reports the size and the start of
    the first line, which is what a caller needs to confirm the right text is set.
    """
    first_line = body.splitlines()[0] if body else ""
    if len(first_line) > _PREVIEW_BODY_LIMIT:
        return f"body='{first_line[:_PREVIEW_BODY_LIMIT]}...' ({len(body)} chars)"
    return f"body='{first_line}' ({len(body)} chars)"


def _validate_request[ModelT: BaseModel](
    model_cls: type[ModelT], args: ToolArgs
) -> ModelT:
    """Build one request model from the raw argument dict, or raise the domain error.

    The dict is passed unchanged: no copying, no key injection, no per-key fallback.
    `extra="forbid"` on the strict request base therefore sees exactly what the caller
    sent, so the runtime rejects the same inputs the published `inputSchema` advertises,
    and every default comes from the model rather than from a dispatch-side `args.get`.

    `pydantic.ValidationError` is converted to `GitHubValidationError` here and nowhere
    else in the GitHub dispatch, so `exception_handlers.py` and `dispatch_tool` keep
    classifying the failure through the domain exception type. The message names the
    model and the offending field paths, never the values: argument text can contain
    file content, and the audit layer owns request recording.
    """
    try:
        return model_cls.model_validate(args)
    except ValidationError as exc:
        fields = ", ".join(
            ".".join(str(part) for part in err["loc"]) or "<root>"
            for err in exc.errors()
        )
        raise GitHubValidationError(
            f"{model_cls.__name__}: {exc.error_count()} invalid field(s): {fields}"
        ) from exc


class WriteDispatchOps(_GitHubServiceCore):
    """Write-tool dispatch formatters (extends service_business.GitHubService)."""

    @staticmethod
    def _dry_run_preview(preview: str) -> str:
        """Return a JSON dry-run preview response string."""
        return _json_dumps({"preview": preview, "dry_run": True})

    async def _execute_with_dry_run(
        self,
        req: _DryRunRequest,
        preview_callback: Callable[[], str],
        execute_callback: Callable[[], Awaitable[str]],
        *,
        op: str,
    ) -> str:
        """Execute a GitHub operation with optional dry-run mode.

        Authorization is checked first for both modes, so a denied repository fails
        identically whether or not the call is a dry run. For a real run, the intent
        audit is written after authorization and before the callback: a denied
        repository audits nothing, and an unwritable audit path fails the call before
        anything is applied. A dry run writes no audit and calls no API.
        """
        self._assert_allowed_repo(req.owner, req.repo)
        if req.dry_run:
            return self._dry_run_preview(preview_callback())
        self._write_intent_audit(op, repo=f"{req.owner}/{req.repo}")
        return await execute_callback()

    async def fmt_create_branch(self, args: ToolArgs) -> str:
        """Format create branch operation result with optional dry-run support."""
        req = _validate_request(CreateBranchRequest, args)
        from_b = req.from_branch or "(default branch)"

        async def _execute() -> str:
            """Create a new branch on GitHub."""
            result = await self.create_branch(req)
            return f"Branch created: {result.branch_name} (SHA: {result.sha[:8]})"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would create branch '{req.branch_name}' from '{from_b}' in {req.owner}/{req.repo}"
            ),
            _execute,
            op="create_branch",
        )

    async def fmt_create_or_update_file(self, args: ToolArgs) -> str:
        """Format create or update file operation result with optional dry-run support."""
        req = _validate_request(CreateOrUpdateFileRequest, args)
        op = "update" if req.sha else "create"
        branch = req.branch or "(default branch)"

        async def _execute() -> str:
            """Create or update a file on GitHub."""
            result = await self.create_or_update_file(req)
            return (
                f"{result.operation}: {result.path} (commit: {result.commit_sha[:8]})"
            )

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would {op} file '{req.path}' on branch '{branch}' in {req.owner}/{req.repo}"
            ),
            _execute,
            op="create_or_update_file",
        )

    async def fmt_push_files(self, args: ToolArgs) -> str:
        """Format push files operation result with optional dry-run support."""
        req = _validate_request(PushFilesRequest, args)
        paths = [f.path for f in req.files]

        async def _execute() -> str:
            """Push multiple files to a branch on GitHub."""
            result = await self.push_files(req)
            sha_short = result.commit_sha[:8]
            return f"Pushed: branch={result.branch} files={result.files_pushed} commit={sha_short}"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would push {len(paths)} file(s) to branch '{req.branch}' in {req.owner}/{req.repo}: {paths}"
            ),
            _execute,
            op="push_files",
        )

    async def fmt_delete_file(self, args: ToolArgs) -> str:
        """Format delete file operation result with optional dry-run support."""
        req = _validate_request(DeleteRepoFileRequest, args)
        branch = req.branch or "(default branch)"

        async def _execute() -> str:
            """Delete a file from a GitHub repository."""
            result = await self.delete_repo_file(req)
            return f"Deleted: {result.path} (commit: {result.commit_sha[:8]})"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would delete '{req.path}' from branch '{branch}' in {req.owner}/{req.repo}"
            ),
            _execute,
            op="delete_repo_file",
        )

    async def fmt_create_issue(self, args: ToolArgs) -> str:
        """Format create issue operation result with optional dry-run support."""
        req = _validate_request(CreateIssueRequest, args)
        labels = f" labels={req.labels}" if req.labels else ""

        async def _execute() -> str:
            """Create a new issue on GitHub."""
            result = await self.create_issue(req)
            i = result.issue
            return f"Created: #{i.number} {i.title}\n{i.url}"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would create issue '{req.title}'{labels} in {req.owner}/{req.repo}"
            ),
            _execute,
            op="create_issue",
        )

    async def fmt_add_issue_comment(self, args: ToolArgs) -> str:
        """Format add issue comment operation result with optional dry-run support."""
        req = _validate_request(AddIssueCommentRequest, args)

        async def _execute() -> str:
            """Post a comment on an existing GitHub issue."""
            result = await self.add_issue_comment(req)
            return f"Comment posted: #{result.issue_number} {result.comment_url}"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would post comment on issue #{req.issue_number} in {req.owner}/{req.repo}"
            ),
            _execute,
            op="add_issue_comment",
        )

    async def fmt_create_pull_request(self, args: ToolArgs) -> str:
        """Format create pull request operation result with optional dry-run support."""
        req = _validate_request(CreatePullRequestRequest, args)

        async def _execute() -> str:
            """Create a new pull request on GitHub."""
            result = await self.create_pull_request(req)
            pr = result.pull_request
            return f"Created: #{pr.number} {pr.title}\nhead: {pr.head_ref} → base: {pr.base_ref}\nURL: {pr.url}"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would create PR '{req.title}' ({req.head} → {req.base}) in {req.owner}/{req.repo}"
            ),
            _execute,
            op="create_pull_request",
        )

    async def fmt_update_pull_request(self, args: ToolArgs) -> str:
        """Format update pull request operation result with optional dry-run support.

        The preview lists every field the real run would change, `body` included: a
        dry run that omitted it would report "(no changes)" for a body-only update.
        """
        req = _validate_request(UpdatePullRequestRequest, args)
        fields: list[str] = []
        if req.title is not None:
            fields.append(f"title='{req.title}'")
        if req.body is not None:
            fields.append(_fmt_body_field(req.body))
        if req.state is not None:
            fields.append(f"state={req.state}")
        # The model validator (UpdatePullRequestRequest._require_a_change) guarantees at
        # least one non-None change, so `fields` is never empty here.
        changes = ", ".join(fields)

        async def _execute() -> str:
            """Update a pull request's title or state on GitHub."""
            result = await self.update_pull_request(req)
            pr = result.pull_request
            return f"Updated: #{pr.number} [{pr.state}] {pr.title}\n{pr.url}"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would update PR #{req.pr_number} in {req.owner}/{req.repo}: {changes}"
            ),
            _execute,
            op="update_pull_request",
        )

    async def fmt_merge_pull_request(self, args: ToolArgs) -> str:
        """Format merge pull request operation result with optional dry-run support."""
        req = _validate_request(MergePullRequestRequest, args)

        async def _execute() -> str:
            """Merge a pull request on GitHub."""
            result = await self.merge_pull_request(req)
            sha_short = result.sha[:8] if result.sha else "N/A"
            return f"Merged: #{result.pr_number} merged={result.merged} sha={sha_short}\n{result.message}"

        return await self._execute_with_dry_run(
            req,
            lambda: (
                f"Would merge PR #{req.pr_number} in {req.owner}/{req.repo} using method='{req.merge_method}'"
            ),
            _execute,
            op="merge_pull_request",
        )
