#!/usr/bin/env python3
"""mcp/github/models.py
Config loading and Pydantic request/response models for mcp/github/server.py.

Dependency direction: mcp.github.models → (no local deps)
"""

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_PER_PAGE: int = 10


@dataclasses.dataclass
class GitHubConfig:
    """Typed configuration for the GitHub MCP server."""

    allowed_repos: list[str] = dataclasses.field(default_factory=list)
    allowed_repos_mode: str = "fail_closed"
    path_denylist: list[str] = dataclasses.field(default_factory=list)
    protected_branches: list[str] = dataclasses.field(default_factory=list)
    max_file_size_kb: int = 0
    audit_log_path: str = ""
    allow_force_push: bool = True
    require_pr_review: bool = False
    default_per_page: int = DEFAULT_PER_PAGE
    max_per_page: int = 100
    llm_url: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GitHubConfig":
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            allowed_repos=list(d.get("allowed_repos", [])),
            allowed_repos_mode=str(d.get("allowed_repos_mode", "fail_closed")),
            path_denylist=list(d.get("path_denylist", [])),
            protected_branches=list(d.get("protected_branches", [])),
            max_file_size_kb=int(d.get("max_file_size_kb", 0)),
            audit_log_path=str(d.get("audit_log_path", "")),
            allow_force_push=bool(d.get("allow_force_push", True)),
            require_pr_review=bool(d.get("require_pr_review", False)),
            default_per_page=int(d.get("default_per_page", DEFAULT_PER_PAGE)),
            max_per_page=int(d.get("max_per_page", 100)),
            llm_url=str(d.get("llm_url", "")),
        )

    @classmethod
    def load(cls) -> "GitHubConfig":
        """Load from github_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("github_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class GitHubAuthorizationError(RuntimeError):
    """Raised when a repo/path/branch policy check fails (HTTP 403)."""


class GitHubNotFoundError(RuntimeError):
    """Raised when a GitHub resource is not found (HTTP 404)."""


class GitHubValidationError(ValueError):
    """Raised on invalid input (HTTP 400/422)."""


class GitHubConflictError(RuntimeError):
    """Raised on a GitHub conflict (HTTP 409)."""


class GitHubUpstreamError(RuntimeError):
    """Raised on GitHub API 5xx or unexpected upstream failures."""


class GitHubAuditError(RuntimeError):
    """Raised when audit log writing fails and audit_log_path is configured."""


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────
class SearchRepositoriesRequest(BaseModel):
    query: str = Field(
        ...,
        description="GitHub repository search query (GitHub Search syntax)",
    )
    per_page: int = Field(
        default=DEFAULT_PER_PAGE,
        ge=1,
        description="Maximum number of results to return",
    )


class RepositoryInfo(BaseModel):
    full_name: str
    description: str | None
    url: str
    stars: int
    forks: int
    language: str | None
    updated_at: str


class SearchRepositoriesResponse(BaseModel):
    query: str
    results: list[RepositoryInfo]


class GetFileContentsRequest(BaseModel):
    owner: str = Field(
        ...,
        description="Repository owner name (username or organization name)",
    )
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path (relative to repository root)")
    ref: str = Field(
        default="",
        description="Branch name, tag name, or commit SHA (default: default branch)",
    )


class GetFileContentsResponse(BaseModel):
    path: str
    content: str
    sha: str
    size: int
    encoding: str


class ListIssuesRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    state: str = Field(
        default="open",
        pattern="^(open|closed|all)$",
        description="Issue state (open/closed/all)",
    )
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


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


class ListIssuesResponse(BaseModel):
    issues: list[IssueInfo]


class GetIssueRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number")


class GetIssueResponse(BaseModel):
    issue: IssueInfo


class CreateIssueRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Issue title")
    body: str = Field(default="", description="Issue body (Markdown)")
    labels: list[str] = Field(default_factory=list, description="List of label names")
    assignees: list[str] = Field(
        default_factory=list,
        description="List of assignee GitHub usernames",
    )
    dry_run: bool = Field(
        default=False, description="Preview only; no issue is created"
    )


class CreateIssueResponse(BaseModel):
    issue: IssueInfo


class ListPullRequestsRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    state: str = Field(default="open", pattern="^(open|closed|all)$")
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


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


class ListPullRequestsResponse(BaseModel):
    pull_requests: list[PullRequestInfo]


class GetPullRequestRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number")


class GetPullRequestResponse(BaseModel):
    pull_request: PullRequestInfo


class ListCommitsRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(default="", description="Branch name (default: default branch)")
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class CommitInfo(BaseModel):
    sha: str
    message: str
    author: str
    authored_at: str
    url: str


class ListCommitsResponse(BaseModel):
    commits: list[CommitInfo]


class SearchCodeRequest(BaseModel):
    query: str = Field(
        ...,
        description="Code search query (e.g. 'filename:agent.py repo:owner/repo')",
    )
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class CodeSearchResult(BaseModel):
    repository: str
    path: str
    url: str
    score: float


class SearchCodeResponse(BaseModel):
    query: str
    results: list[CodeSearchResult]


class CreatePullRequestRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Pull request title")
    body: str = Field(default="", description="Pull request body (Markdown)")
    head: str = Field(..., description="Source branch name for the PR")
    base: str = Field(..., description="Target branch name to merge into")
    dry_run: bool = Field(default=False, description="Preview only; no PR is created")


class CreatePullRequestResponse(BaseModel):
    pull_request: PullRequestInfo


class CreateBranchRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    branch_name: str = Field(..., description="Name of the new branch to create")
    from_branch: str = Field(
        default="",
        description="Base branch to derive from (default: default branch)",
    )
    dry_run: bool = Field(
        default=False, description="Preview only; no branch is created"
    )


class CreateBranchResponse(BaseModel):
    branch_name: str
    sha: str


class CreateOrUpdateFileRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path (relative to repository root)")
    content: str = Field(..., description="File content (UTF-8 text)")
    message: str = Field(..., description="Commit message")
    branch: str = Field(
        default="",
        description="Target branch name (default: default branch)",
    )
    sha: str = Field(
        default="",
        description="Current SHA when updating an existing file (empty for new files)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no file is written")


class CreateOrUpdateFileResponse(BaseModel):
    path: str
    commit_sha: str
    operation: str  # "created" or "updated"


class AddIssueCommentRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number to add the comment to")
    body: str = Field(..., description="Comment body (Markdown)")
    dry_run: bool = Field(
        default=False, description="Preview only; no comment is posted"
    )


class AddIssueCommentResponse(BaseModel):
    issue_number: int
    comment_url: str


class PushFile(BaseModel):
    """One file entry for push_files."""

    path: str = Field(..., description="File path (relative to repository root)")
    content: str = Field(..., description="File content (UTF-8 text)")


class PushFilesRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Branch name to push to")
    files: list[PushFile] = Field(..., description="List of files to push")
    message: str = Field(..., description="Commit message")
    dry_run: bool = Field(
        default=False, description="Preview only; no files are pushed"
    )


class PushFilesResponse(BaseModel):
    branch: str
    commit_sha: str
    files_pushed: int


class DeleteRepoFileRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    path: str = Field(
        ...,
        description="File path to delete (relative to repository root)",
    )
    message: str = Field(..., description="Commit message")
    sha: str = Field(
        ...,
        description="Current SHA of the file to delete (required to prevent conflicts)",
    )
    branch: str = Field(
        default="",
        description="Target branch name (default: default branch)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no file is deleted")


class DeleteRepoFileResponse(BaseModel):
    path: str
    commit_sha: str


class ListBranchesRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class BranchInfo(BaseModel):
    name: str
    sha: str
    protected: bool


class ListBranchesResponse(BaseModel):
    branches: list[BranchInfo]


class GetCommitRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    sha: str = Field(..., description="Commit SHA (full or abbreviated)")


class CommitDetail(BaseModel):
    sha: str
    message: str
    author: str
    authored_at: str
    url: str
    files_changed: int


class GetCommitResponse(BaseModel):
    commit: CommitDetail


class SearchIssuesRequest(BaseModel):
    query: str = Field(
        ...,
        description="GitHub search query (e.g. 'repo:owner/repo is:issue label:bug')",
    )
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class SearchIssuesResponse(BaseModel):
    query: str
    results: list[IssueInfo]


class SearchPullRequestsRequest(BaseModel):
    query: str = Field(
        ...,
        description="GitHub search query (is:pr is appended automatically)",
    )
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)


class SearchPullRequestsResponse(BaseModel):
    query: str
    results: list[IssueInfo]  # Search API returns Issue objects


class UpdatePullRequestRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number to update")
    title: str | None = Field(default=None, description="New title (omit to keep)")
    body: str | None = Field(default=None, description="New body (omit to keep)")
    state: str | None = Field(
        default=None,
        pattern="^(open|closed)$",
        description="New state: open / closed (omit to keep unchanged)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no PR is updated")


class UpdatePullRequestResponse(BaseModel):
    pull_request: PullRequestInfo


class MergePullRequestRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number to merge")
    commit_title: str = Field(
        default="",
        description="Merge commit title (default: GitHub default)",
    )
    commit_message: str = Field(
        default="",
        description="Merge commit body (default: GitHub default)",
    )
    merge_method: str = Field(
        default="merge",
        pattern="^(merge|squash|rebase)$",
        description="Merge method: merge / squash / rebase",
    )
    dry_run: bool = Field(default=False, description="Preview only; no PR is merged")


class MergePullRequestResponse(BaseModel):
    pr_number: int
    merged: bool
    sha: str
    message: str
