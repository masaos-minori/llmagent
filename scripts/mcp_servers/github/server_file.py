#!/usr/bin/env python3
"""mcp_servers/github/server_file.py

FastAPI routes for GitHub file operations.

Endpoints: get_file_contents, create_or_update_file, push_files, delete_repo_file
"""

import time

from fastapi import APIRouter, Depends

from mcp_servers.github.github_models import (
    CreateOrUpdateFileRequest,
    CreateOrUpdateFileResponse,
    DeleteRepoFileRequest,
    DeleteRepoFileResponse,
    GetFileContentsRequest,
    GetFileContentsResponse,
    PushFilesRequest,
    PushFilesResponse,
)
from mcp_servers.github.server_common import _get_service, _info
from mcp_servers.github.service_dispatch import GitHubService

router = APIRouter()


@router.post("/get_file_contents", response_model=GetFileContentsResponse)
async def get_file_contents(
    req: GetFileContentsRequest,
    svc: GitHubService = Depends(_get_service),
) -> GetFileContentsResponse:
    """Retrieve the contents of a file from a repository."""
    t0 = time.perf_counter()
    result = await svc.get_file_contents(req)
    _info(
        "get_file_contents",
        repo=f"{req.owner}/{req.repo}",
        path=req.path,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/create_or_update_file", response_model=CreateOrUpdateFileResponse)
async def create_or_update_file(
    req: CreateOrUpdateFileRequest,
    svc: GitHubService = Depends(_get_service),
) -> CreateOrUpdateFileResponse:
    """Create or update a single file in a repository."""
    t0 = time.perf_counter()
    result = await svc.create_or_update_file(req)
    _info(
        "create_or_update_file",
        repo=f"{req.owner}/{req.repo}",
        path=req.path,
        operation=result.operation,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/push_files", response_model=PushFilesResponse)
async def push_files(
    req: PushFilesRequest,
    svc: GitHubService = Depends(_get_service),
) -> PushFilesResponse:
    """Push multiple files to a repository in a single commit."""
    t0 = time.perf_counter()
    result = await svc.push_files(req)
    _info(
        "push_files",
        repo=f"{req.owner}/{req.repo}",
        branch=req.branch,
        n=result.files_pushed,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result


@router.post("/delete_repo_file", response_model=DeleteRepoFileResponse)
async def delete_repo_file(
    req: DeleteRepoFileRequest,
    svc: GitHubService = Depends(_get_service),
) -> DeleteRepoFileResponse:
    """Delete a file from a repository."""
    t0 = time.perf_counter()
    result = await svc.delete_repo_file(req)
    _info(
        "delete_repo_file",
        repo=f"{req.owner}/{req.repo}",
        path=req.path,
        ms=f"{(time.perf_counter() - t0) * 1000:.0f}",
    )
    return result
