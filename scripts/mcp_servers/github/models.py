#!/usr/bin/env python3
"""mcp_servers/github/models.py
Re-export stub for github-mcp server models.

Split layout (single-responsibility modules):
  models_config.py        — GitHubConfig dataclass, domain exceptions, DEFAULT_PER_PAGE
  models_base.py          — Shared IssueInfo (used by issues + pull_requests)
  models_repository.py    — Repository search, code search, branches, commits
  models_file.py          — File operations (get/create/update/push/delete)
  models_issues.py        — Issues, comments, search issues
  models_pull_requests.py — Pull requests, update, merge, search PRs

Dependency direction: models_config → (none) · models_base → (none)
  models_repository/file/issues/pull_requests → models_config or models_base
  models.py → all submodules (re-export only, no business logic)
"""

from .models_base import IssueInfo
from .models_config import (
    DEFAULT_PER_PAGE,
    GitHubAuditError,
    GitHubAuthorizationError,
    GitHubConfig,
    GitHubConflictError,
    GitHubNotFoundError,
    GitHubUpstreamError,
    GitHubValidationError,
)
from .models_file import (
    CreateOrUpdateFileRequest,
    CreateOrUpdateFileResponse,
    DeleteRepoFileRequest,
    DeleteRepoFileResponse,
    GetFileContentsRequest,
    GetFileContentsResponse,
    PushFile,
    PushFilesRequest,
    PushFilesResponse,
)
from .models_issues import (
    AddIssueCommentRequest,
    AddIssueCommentResponse,
    CreateIssueRequest,
    CreateIssueResponse,
    GetIssueRequest,
    GetIssueResponse,
    ListIssuesRequest,
    ListIssuesResponse,
    SearchIssuesRequest,
    SearchIssuesResponse,
)
from .models_pull_requests import (
    CreatePullRequestRequest,
    CreatePullRequestResponse,
    GetPullRequestRequest,
    GetPullRequestResponse,
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
from .models_repository import (
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

__all__: list[str] = [
    # Config & exceptions
    "DEFAULT_PER_PAGE",
    "GitHubConfig",
    "GitHubAuthorizationError",
    "GitHubNotFoundError",
    "GitHubValidationError",
    "GitHubConflictError",
    "GitHubUpstreamError",
    "GitHubAuditError",
    # Shared
    "IssueInfo",
    # Repository
    "SearchRepositoriesRequest",
    "RepositoryInfo",
    "SearchRepositoriesResponse",
    "ListCommitsRequest",
    "CommitInfo",
    "ListCommitsResponse",
    "SearchCodeRequest",
    "CodeSearchResult",
    "SearchCodeResponse",
    "ListBranchesRequest",
    "BranchInfo",
    "ListBranchesResponse",
    "CreateBranchRequest",
    "CreateBranchResponse",
    "GetCommitRequest",
    "CommitDetail",
    "GetCommitResponse",
    # File
    "GetFileContentsRequest",
    "GetFileContentsResponse",
    "CreateOrUpdateFileRequest",
    "CreateOrUpdateFileResponse",
    "PushFile",
    "PushFilesRequest",
    "PushFilesResponse",
    "DeleteRepoFileRequest",
    "DeleteRepoFileResponse",
    # Issues
    "ListIssuesRequest",
    "ListIssuesResponse",
    "GetIssueRequest",
    "GetIssueResponse",
    "CreateIssueRequest",
    "CreateIssueResponse",
    "AddIssueCommentRequest",
    "AddIssueCommentResponse",
    "SearchIssuesRequest",
    "SearchIssuesResponse",
    # Pull requests
    "ListPullRequestsRequest",
    "PullRequestInfo",
    "ListPullRequestsResponse",
    "GetPullRequestRequest",
    "GetPullRequestResponse",
    "CreatePullRequestRequest",
    "CreatePullRequestResponse",
    "UpdatePullRequestRequest",
    "UpdatePullRequestResponse",
    "MergePullRequestRequest",
    "MergePullRequestResponse",
    "SearchPullRequestsRequest",
    "SearchPullRequestsResponse",
]
