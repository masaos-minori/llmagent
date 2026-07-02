#!/usr/bin/env python3
"""mcp/github/server_repository.py

FastAPI routes for GitHub repository operations.

Endpoints: search_repositories, list_branches, create_branch, list_commits, get_commit, search_code
"""

import time

from fastapi import APIRouter, Depends

from mcp.github.models import (
    CreateBranchRequest,
    CreateBranchResponse,
    GetCommitRequest,
    GetCommitResponse,
    ListBranchesRequest,
    ListBranchesResponse,
    ListCommitsRequest,
    ListCommitsResponse,
    SearchCodeRequest,
    SearchCodeResponse,
    SearchRepositoriesRequest,
    SearchRepositoriesResponse,
)
from mcp.github.server_common import _get_service, _info
from mcp.github.service_dispatch import GitHubService

router = APIRouter()


@router.post("/search_repositories", response_model=SearchRepositoriesResponse)
async def search_repositories(
    req: SearchRepositoriesRequest,
    svc: GitHubService = Depends(_get_service),
) -> SearchRepositoriesResponse:
    t0 = time.perf_counter()
    result = await svc.search_repositories(req)
    _info(
        "search_repositories",
        q=req.query[:80],
        n=len(result.results),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/list_branches", response_model=ListBranchesResponse)
async def list_branches(
    req: ListBranchesRequest,
    svc: GitHubService = Depends(_get_service),
) -> ListBranchesResponse:
    t0 = time.perf_counter()
    result = await svc.list_branches(req)
    _info(
        "list_branches",
        repo=f"{req.owner}/{req.repo}",
        n=len(result.branches),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/create_branch", response_model=CreateBranchResponse)
async def create_branch(
    req: CreateBranchRequest,
    svc: GitHubService = Depends(_get_service),
) -> CreateBranchResponse:
    t0 = time.perf_counter()
    result = await svc.create_branch(req)
    _info(
        "create_branch",
        repo=f"{req.owner}/{req.repo}",
        branch=req.branch_name,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/list_commits", response_model=ListCommitsResponse)
async def list_commits(
    req: ListCommitsRequest,
    svc: GitHubService = Depends(_get_service),
) -> ListCommitsResponse:
    t0 = time.perf_counter()
    result = await svc.list_commits(req)
    _info(
        "list_commits",
        repo=f"{req.owner}/{req.repo}",
        n=len(result.commits),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/get_commit", response_model=GetCommitResponse)
async def get_commit(
    req: GetCommitRequest,
    svc: GitHubService = Depends(_get_service),
) -> GetCommitResponse:
    t0 = time.perf_counter()
    result = await svc.get_commit(req)
    _info(
        "get_commit",
        repo=f"{req.owner}/{req.repo}",
        sha=req.sha[:8],
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/search_code", response_model=SearchCodeResponse)
async def search_code(
    req: SearchCodeRequest,
    svc: GitHubService = Depends(_get_service),
) -> SearchCodeResponse:
    t0 = time.perf_counter()
    result = await svc.search_code(req)
    _info(
        "search_code",
        q=req.query[:80],
        n=len(result.results),
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result
