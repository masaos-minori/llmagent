#!/usr/bin/env python3
"""github_mcp_server.py
GitHub operations MCP server equivalent to @modelcontextprotocol/server-github.
Provides an HTTP API via FastAPI. Listens on port 8006.

Authentication: Uses GITHUB_TOKEN environment variable (Personal Access Token).
               Configure in /etc/conf.d/github-mcp.

Available endpoints:
  POST /search_repositories    Search repositories
  POST /get_file_contents      Retrieve file contents from a repository
  POST /push_files             Push multiple files as a single commit
  POST /delete_repo_file       Delete a file from a repository
  POST /list_branches          List branches
  POST /get_commit             Retrieve details of a specific commit
  POST /list_issues            List issues
  POST /get_issue              Retrieve a specific issue
  POST /create_issue           Create an issue
  POST /search_issues          Keyword search for issues/PRs
  POST /list_pull_requests     List pull requests
  POST /get_pull_request       Retrieve a specific pull request
  POST /search_pull_requests   Keyword search for pull requests
  POST /update_pull_request    Update pull request title/body/state
  POST /merge_pull_request     Merge a pull request
  POST /list_commits           List commits
  POST /search_code            Search code
  POST /create_pull_request    Create a pull request
  POST /create_branch          Create a branch
  POST /create_or_update_file  Create or update a file
  POST /add_issue_comment      Post a comment to an issue
  GET  /health                 Health check
"""

import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.audit import _audit_log
from mcp.dispatch import dispatch_tool
from mcp.github.models import (
    AddIssueCommentRequest,
    AddIssueCommentResponse,
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
    PushFilesRequest,
    PushFilesResponse,
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
from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service
from mcp.github.tools import TOOL_LIST
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs

# Log path is owned here; service module uses logging.getLogger(__name__)
logger = Logger(__name__, "/opt/llm/logs/github-mcp.log")

_cfg = GitHubConfig.load()
_service: GitHubService = build_service(_cfg)

app = FastAPI(
    title="github-mcp",
    version="1.0.0",
    description="MCP server equivalent to @modelcontextprotocol/server-github",
)


# ──────────────────────────────────────────────────────────────────────────────
# Domain exception → HTTP status handlers
# ──────────────────────────────────────────────────────────────────────────────


@app.exception_handler(GitHubAuthorizationError)
async def _handle_auth_error(
    request: Request, exc: GitHubAuthorizationError
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(GitHubNotFoundError)
async def _handle_not_found(request: Request, exc: GitHubNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(GitHubValidationError)
async def _handle_validation(
    request: Request, exc: GitHubValidationError
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(GitHubConflictError)
async def _handle_conflict(request: Request, exc: GitHubConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(GitHubUpstreamError)
async def _handle_upstream(request: Request, exc: GitHubUpstreamError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(GitHubAuditError)
async def _handle_audit(request: Request, exc: GitHubAuditError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint definitions — Repository operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/search_repositories", response_model=SearchRepositoriesResponse)
async def search_repositories(
    req: SearchRepositoriesRequest,
) -> SearchRepositoriesResponse:
    """Search GitHub repositories by query string."""
    t0 = time.perf_counter()
    result = await _service.search_repositories(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "search_repositories",
            q=req.query[:80],
            n=len(result.results),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/list_branches", response_model=ListBranchesResponse)
async def list_branches(req: ListBranchesRequest) -> ListBranchesResponse:
    """Retrieve the list of branches for a repository."""
    t0 = time.perf_counter()
    result = await _service.list_branches(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_branches",
            repo=f"{req.owner}/{req.repo}",
            n=len(result.branches),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/create_branch", response_model=CreateBranchResponse)
async def create_branch(req: CreateBranchRequest) -> CreateBranchResponse:
    """Create a branch; when from_branch is omitted, derives from the default branch."""
    t0 = time.perf_counter()
    result = await _service.create_branch(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "create_branch",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch_name,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/list_commits", response_model=ListCommitsResponse)
async def list_commits(req: ListCommitsRequest) -> ListCommitsResponse:
    """Retrieve the commit history for a repository."""
    t0 = time.perf_counter()
    result = await _service.list_commits(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_commits",
            repo=f"{req.owner}/{req.repo}",
            n=len(result.commits),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/get_commit", response_model=GetCommitResponse)
async def get_commit(req: GetCommitRequest) -> GetCommitResponse:
    """Retrieve details of a specific commit."""
    t0 = time.perf_counter()
    result = await _service.get_commit(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "get_commit",
            repo=f"{req.owner}/{req.repo}",
            sha=req.sha[:8],
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/search_code", response_model=SearchCodeResponse)
async def search_code(req: SearchCodeRequest) -> SearchCodeResponse:
    """Search code on GitHub by full-text query."""
    t0 = time.perf_counter()
    result = await _service.search_code(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "search_code",
            q=req.query[:80],
            n=len(result.results),
            ms=f"{ms:.0f}",
        ),
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint definitions — File operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/get_file_contents", response_model=GetFileContentsResponse)
async def get_file_contents(req: GetFileContentsRequest) -> GetFileContentsResponse:
    """Retrieve the contents of a single file in a repository."""
    t0 = time.perf_counter()
    result = await _service.get_file_contents(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "get_file_contents",
            repo=f"{req.owner}/{req.repo}",
            path=req.path,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/create_or_update_file", response_model=CreateOrUpdateFileResponse)
async def create_or_update_file(
    req: CreateOrUpdateFileRequest,
) -> CreateOrUpdateFileResponse:
    """Create or update a file; providing sha updates an existing file."""
    t0 = time.perf_counter()
    result = await _service.create_or_update_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "create_or_update_file",
            repo=f"{req.owner}/{req.repo}",
            path=req.path,
            operation=result.operation,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/push_files", response_model=PushFilesResponse)
async def push_files(req: PushFilesRequest) -> PushFilesResponse:
    """Push multiple files as a single atomic commit via the Git Tree API."""
    t0 = time.perf_counter()
    result = await _service.push_files(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "push_files",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch,
            n=result.files_pushed,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/delete_repo_file", response_model=DeleteRepoFileResponse)
async def delete_repo_file(req: DeleteRepoFileRequest) -> DeleteRepoFileResponse:
    """Delete a file from a repository; sha is required to prevent conflicts."""
    t0 = time.perf_counter()
    result = await _service.delete_repo_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "delete_repo_file",
            repo=f"{req.owner}/{req.repo}",
            path=req.path,
            ms=f"{ms:.0f}",
        ),
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint definitions — Issues operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/list_issues", response_model=ListIssuesResponse)
async def list_issues(req: ListIssuesRequest) -> ListIssuesResponse:
    """Retrieve the list of issues for a repository."""
    t0 = time.perf_counter()
    result = await _service.list_issues(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_issues",
            repo=f"{req.owner}/{req.repo}",
            state=req.state,
            n=len(result.issues),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/get_issue", response_model=GetIssueResponse)
async def get_issue(req: GetIssueRequest) -> GetIssueResponse:
    """Retrieve a specific issue by number."""
    t0 = time.perf_counter()
    result = await _service.get_issue(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "get_issue",
            repo=f"{req.owner}/{req.repo}",
            issue=req.issue_number,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/create_issue", response_model=CreateIssueResponse)
async def create_issue(req: CreateIssueRequest) -> CreateIssueResponse:
    """Create a new issue in a repository."""
    t0 = time.perf_counter()
    result = await _service.create_issue(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "create_issue",
            repo=f"{req.owner}/{req.repo}",
            issue=result.issue.number,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/search_issues", response_model=SearchIssuesResponse)
async def search_issues(req: SearchIssuesRequest) -> SearchIssuesResponse:
    """Keyword search for issues/PRs across all of GitHub."""
    t0 = time.perf_counter()
    result = await _service.search_issues(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "search_issues",
            q=req.query[:80],
            n=len(result.results),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/add_issue_comment", response_model=AddIssueCommentResponse)
async def add_issue_comment(req: AddIssueCommentRequest) -> AddIssueCommentResponse:
    """Post a comment to an existing issue."""
    t0 = time.perf_counter()
    result = await _service.add_issue_comment(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "add_issue_comment",
            repo=f"{req.owner}/{req.repo}",
            issue=req.issue_number,
            ms=f"{ms:.0f}",
        ),
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint definitions — Pull Request operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/list_pull_requests", response_model=ListPullRequestsResponse)
async def list_pull_requests(
    req: ListPullRequestsRequest,
) -> ListPullRequestsResponse:
    """Retrieve the list of pull requests for a repository."""
    t0 = time.perf_counter()
    result = await _service.list_pull_requests(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_pull_requests",
            repo=f"{req.owner}/{req.repo}",
            state=req.state,
            n=len(result.pull_requests),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/get_pull_request", response_model=GetPullRequestResponse)
async def get_pull_request(req: GetPullRequestRequest) -> GetPullRequestResponse:
    """Retrieve a specific pull request by number."""
    t0 = time.perf_counter()
    result = await _service.get_pull_request(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "get_pull_request",
            repo=f"{req.owner}/{req.repo}",
            pr=req.pr_number,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/create_pull_request", response_model=CreatePullRequestResponse)
async def create_pull_request(
    req: CreatePullRequestRequest,
) -> CreatePullRequestResponse:
    """Create a new pull request in a repository."""
    t0 = time.perf_counter()
    result = await _service.create_pull_request(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "create_pull_request",
            repo=f"{req.owner}/{req.repo}",
            pr=result.pull_request.number,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/search_pull_requests", response_model=SearchPullRequestsResponse)
async def search_pull_requests(
    req: SearchPullRequestsRequest,
) -> SearchPullRequestsResponse:
    """Keyword search for PRs across GitHub (is:pr appended automatically)."""
    t0 = time.perf_counter()
    result = await _service.search_pull_requests(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "search_pull_requests",
            q=req.query[:80],
            n=len(result.results),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/update_pull_request", response_model=UpdatePullRequestResponse)
async def update_pull_request(
    req: UpdatePullRequestRequest,
) -> UpdatePullRequestResponse:
    """Update the title, body, or state of a pull request."""
    t0 = time.perf_counter()
    result = await _service.update_pull_request(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "update_pull_request",
            repo=f"{req.owner}/{req.repo}",
            pr=req.pr_number,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/merge_pull_request", response_model=MergePullRequestResponse)
async def merge_pull_request(req: MergePullRequestRequest) -> MergePullRequestResponse:
    """Merge a pull request using the specified merge method."""
    t0 = time.perf_counter()
    result = await _service.merge_pull_request(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "merge_pull_request",
            repo=f"{req.owner}/{req.repo}",
            pr=req.pr_number,
            merged=result.merged,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint. Returns GitHub token availability."""
    token_status = "set" if _GITHUB_TOKEN else "not_set"
    return {"status": "ok", "github_token": token_status}


# ──────────────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch function
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_github_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    """Route a tool call to GitHubService via its dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Tool listing endpoint (for client-side definition validation)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """Return tool names and descriptions for agent.json definition validation."""
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in TOOL_LIST
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Unified tool call endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: "Request") -> CallToolResponse:
    """Execute a GitHub tool by name and return the formatted text result."""
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    result, is_error = await _dispatch_github_tool(req.name, req.args)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=f"repo={req.args.get('owner', '')}/{req.args.get('repo', '')}",
        outcome="error" if is_error else "ok",
    )
    return CallToolResponse(result=result, is_error=is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
class GithubMCPServer(MCPServer):
    """MCPServer subclass for github-mcp."""

    server_name = "github-mcp"
    server_version = "1.0.0"
    http_port = 8006
    app_module = "github_mcp_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_github_tool(name, args)


if __name__ == "__main__":
    import sys

    server = GithubMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
