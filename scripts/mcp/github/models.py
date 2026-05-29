#!/usr/bin/env python3
"""
mcp/github/models.py
Config loading and Pydantic request/response models for mcp/github/server.py.

Dependency direction: mcp.github.models → (no local deps)
"""

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.logger import Logger

# ──────────────────────────────────────────────────────────────────────────────
# Config loading (config/github_mcp_server.toml)
# ──────────────────────────────────────────────────────────────────────────────
# Logger is defined here only for config-load warnings; the main log path lives
# in mcp/github/server.py (where Logger("/opt/llm/logs/github-mcp.log") is set).
_models_logger = Logger(__name__, "/opt/llm/logs/github-mcp.log")

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("github_mcp_server.toml")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


# DEFAULT_PER_PAGE must be available at Pydantic schema definition time.
# MAX_PER_PAGE is accessed lazily via _get_cfg() inside _LazyGitHubService.
DEFAULT_PER_PAGE: int = _get_cfg().get("default_per_page", 10)


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────
class SearchRepositoriesRequest(BaseModel):
    query: str = Field(
        ..., description="GitHub repository search query (GitHub Search syntax)"
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
        ..., description="Repository owner name (username or organization name)"
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
        default_factory=list, description="List of assignee GitHub usernames"
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


class CreatePullRequestResponse(BaseModel):
    pull_request: PullRequestInfo


class CreateBranchRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    branch_name: str = Field(..., description="Name of the new branch to create")
    from_branch: str = Field(
        default="", description="Base branch to derive from (default: default branch)"
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
        default="", description="Target branch name (default: default branch)"
    )
    sha: str = Field(
        default="",
        description="Current SHA when updating an existing file (empty for new files)",
    )


class CreateOrUpdateFileResponse(BaseModel):
    path: str
    commit_sha: str
    operation: str  # "created" or "updated"


class AddIssueCommentRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number to add the comment to")
    body: str = Field(..., description="Comment body (Markdown)")


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


class PushFilesResponse(BaseModel):
    branch: str
    commit_sha: str
    files_pushed: int


class DeleteRepoFileRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    path: str = Field(
        ..., description="File path to delete (relative to repository root)"
    )
    message: str = Field(..., description="Commit message")
    sha: str = Field(
        ...,
        description="Current SHA of the file to delete (required to prevent conflicts)",
    )
    branch: str = Field(
        default="", description="Target branch name (default: default branch)"
    )


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
        ..., description="GitHub search query (is:pr is appended automatically)"
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


class UpdatePullRequestResponse(BaseModel):
    pull_request: PullRequestInfo


class MergePullRequestRequest(BaseModel):
    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number to merge")
    commit_title: str = Field(
        default="", description="Merge commit title (default: GitHub default)"
    )
    commit_message: str = Field(
        default="", description="Merge commit body (default: GitHub default)"
    )
    merge_method: str = Field(
        default="merge",
        pattern="^(merge|squash|rebase)$",
        description="Merge method: merge / squash / rebase",
    )


class MergePullRequestResponse(BaseModel):
    pr_number: int
    merged: bool
    sha: str
    message: str
