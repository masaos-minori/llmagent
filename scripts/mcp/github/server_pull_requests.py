#!/usr/bin/env python3
"""mcp/github/server_pull_requests.py

FastAPI routes for GitHub pull request operations.

Endpoints: list_pull_requests, get_pull_request, create_pull_request, search_pull_requests, update_pull_request, merge_pull_request
"""

import time

from fastapi import APIRouter, Depends

from mcp.github.models import (
    CreatePullRequestRequest,
    CreatePullRequestResponse,
    GetPullRequestRequest,
    GetPullRequestResponse,
    ListPullRequestsRequest,
    ListPullRequestsResponse,
    MergePullRequestRequest,
    MergePullRequestResponse,
    SearchPullRequestsRequest,
    SearchPullRequestsResponse,
    UpdatePullRequestRequest,
    UpdatePullRequestResponse,
)
from mcp.github.server_common import _get_service, _info
from mcp.github.service_dispatch import GitHubService

router = APIRouter()


@router.post("/list_pull_requests", response_model=ListPullRequestsResponse)
async def list_pull_requests(
    req: ListPullRequestsRequest,
    svc: GitHubService = Depends(_get_service),
) -> ListPullRequestsResponse:
    t0 = time.perf_counter()
    result = await svc.list_pull_requests(req)
    _info(
        "list_pull_requests",
        repo=f"{req.owner}/{req.repo}",
        state=req.state,
        n=len(result.pull_requests),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/get_pull_request", response_model=GetPullRequestResponse)
async def get_pull_request(
    req: GetPullRequestRequest,
    svc: GitHubService = Depends(_get_service),
) -> GetPullRequestResponse:
    t0 = time.perf_counter()
    result = await svc.get_pull_request(req)
    _info(
        "get_pull_request",
        repo=f"{req.owner}/{req.repo}",
        pr=req.pr_number,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/create_pull_request", response_model=CreatePullRequestResponse)
async def create_pull_request(
    req: CreatePullRequestRequest,
    svc: GitHubService = Depends(_get_service),
) -> CreatePullRequestResponse:
    t0 = time.perf_counter()
    result = await svc.create_pull_request(req)
    _info(
        "create_pull_request",
        repo=f"{req.owner}/{req.repo}",
        pr=result.pull_request.number,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/search_pull_requests", response_model=SearchPullRequestsResponse)
async def search_pull_requests(
    req: SearchPullRequestsRequest,
    svc: GitHubService = Depends(_get_service),
) -> SearchPullRequestsResponse:
    t0 = time.perf_counter()
    result = await svc.search_pull_requests(req)
    _info(
        "search_pull_requests",
        q=req.query[:80],
        n=len(result.results),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/update_pull_request", response_model=UpdatePullRequestResponse)
async def update_pull_request(
    req: UpdatePullRequestRequest,
    svc: GitHubService = Depends(_get_service),
) -> UpdatePullRequestResponse:
    t0 = time.perf_counter()
    result = await svc.update_pull_request(req)
    _info(
        "update_pull_request",
        repo=f"{req.owner}/{req.repo}",
        pr=req.pr_number,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/merge_pull_request", response_model=MergePullRequestResponse)
async def merge_pull_request(
    req: MergePullRequestRequest,
    svc: GitHubService = Depends(_get_service),
) -> MergePullRequestResponse:
    t0 = time.perf_counter()
    result = await svc.merge_pull_request(req)
    _info(
        "merge_pull_request",
        repo=f"{req.owner}/{req.repo}",
        pr=req.pr_number,
        merged=result.merged,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result
