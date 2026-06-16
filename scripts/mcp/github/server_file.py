#!/usr/bin/env python3
"""mcp/github/server_file.py

FastAPI routes for GitHub file operations.

Endpoints: get_file_contents, create_or_update_file, push_files, delete_repo_file
"""

import time
from typing import Any

from fastapi import APIRouter, Depends
from shared.formatters import fmt_kvlog

from mcp.github.models import (
    CreateOrUpdateFileRequest,
    CreateOrUpdateFileResponse,
    DeleteRepoFileRequest,
    DeleteRepoFileResponse,
    GetFileContentsRequest,
    GetFileContentsResponse,
    PushFilesRequest,
    PushFilesResponse,
)
from mcp.github.service import GitHubService

router = APIRouter()


def _info(msg: str, **kwargs: Any) -> None:
    from mcp.github.server import logger as srv_logger

    srv_logger.info(fmt_kvlog(msg, **kwargs))


def _get_service() -> GitHubService:
    """Dependency that returns the singleton GitHubService instance."""
    from mcp.github.server import _service  # noqa: PLC0415

    return _service


@router.post("/get_file_contents", response_model=GetFileContentsResponse)
async def get_file_contents(
    req: GetFileContentsRequest,
    svc: GitHubService = Depends(_get_service),
) -> GetFileContentsResponse:
    t0 = time.perf_counter()
    result = await svc.get_file_contents(req)
    _info("get_file_contents", repo=f"{req.owner}/{req.repo}", path=req.path, ms=f"{(time.perf_counter() - t0) * 1000:.0f}")
    return result


@router.post("/create_or_update_file", response_model=CreateOrUpdateFileResponse)
async def create_or_update_file(
    req: CreateOrUpdateFileRequest,
    svc: GitHubService = Depends(_get_service),
) -> CreateOrUpdateFileResponse:
    t0 = time.perf_counter()
    result = await svc.create_or_update_file(req)
    _info("create_or_update_file", repo=f"{req.owner}/{req.repo}", path=req.path, operation=result.operation, ms=f"{(time.perf_counter() - t0) * 1000:.0f}")
    return result


@router.post("/push_files", response_model=PushFilesResponse)
async def push_files(
    req: PushFilesRequest,
    svc: GitHubService = Depends(_get_service),
) -> PushFilesResponse:
    t0 = time.perf_counter()
    result = await svc.push_files(req)
    _info("push_files", repo=f"{req.owner}/{req.repo}", branch=req.branch, n=result.files_pushed, ms=f"{(time.perf_counter() - t0) * 1000:.0f}")
    return result


@router.post("/delete_repo_file", response_model=DeleteRepoFileResponse)
async def delete_repo_file(
    req: DeleteRepoFileRequest,
    svc: GitHubService = Depends(_get_service),
) -> DeleteRepoFileResponse:
    t0 = time.perf_counter()
    result = await svc.delete_repo_file(req)
    _info("delete_repo_file", repo=f"{req.owner}/{req.repo}", path=req.path, ms=f"{(time.perf_counter() - t0) * 1000:.0f}")
    return result
