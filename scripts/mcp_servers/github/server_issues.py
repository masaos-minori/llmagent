#!/usr/bin/env python3
"""mcp_servers/github/server_issues.py

FastAPI routes for GitHub issues operations.

Endpoints: list_issues, get_issue, create_issue, search_issues, add_issue_comment
"""

import time

from fastapi import APIRouter, Depends

from mcp_servers.github.models import (
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
from mcp_servers.github.server_common import _get_service, _info
from mcp_servers.github.service_dispatch import GitHubService

router = APIRouter()


@router.post("/list_issues", response_model=ListIssuesResponse)
async def list_issues(
    req: ListIssuesRequest,
    svc: GitHubService = Depends(_get_service),
) -> ListIssuesResponse:
    t0 = time.perf_counter()
    result = await svc.list_issues(req)
    _info(
        "list_issues",
        repo=f"{req.owner}/{req.repo}",
        state=req.state,
        n=len(result.issues),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/get_issue", response_model=GetIssueResponse)
async def get_issue(
    req: GetIssueRequest,
    svc: GitHubService = Depends(_get_service),
) -> GetIssueResponse:
    t0 = time.perf_counter()
    result = await svc.get_issue(req)
    _info(
        "get_issue",
        repo=f"{req.owner}/{req.repo}",
        issue=req.issue_number,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/create_issue", response_model=CreateIssueResponse)
async def create_issue(
    req: CreateIssueRequest,
    svc: GitHubService = Depends(_get_service),
) -> CreateIssueResponse:
    t0 = time.perf_counter()
    result = await svc.create_issue(req)
    _info(
        "create_issue",
        repo=f"{req.owner}/{req.repo}",
        issue=result.issue.number,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/search_issues", response_model=SearchIssuesResponse)
async def search_issues(
    req: SearchIssuesRequest,
    svc: GitHubService = Depends(_get_service),
) -> SearchIssuesResponse:
    t0 = time.perf_counter()
    result = await svc.search_issues(req)
    _info(
        "search_issues",
        q=req.query[:80],
        n=len(result.results),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/add_issue_comment", response_model=AddIssueCommentResponse)
async def add_issue_comment(
    req: AddIssueCommentRequest,
    svc: GitHubService = Depends(_get_service),
) -> AddIssueCommentResponse:
    t0 = time.perf_counter()
    result = await svc.add_issue_comment(req)
    _info(
        "add_issue_comment",
        repo=f"{req.owner}/{req.repo}",
        issue=req.issue_number,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result
