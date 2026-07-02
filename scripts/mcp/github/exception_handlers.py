#!/usr/bin/env python3
"""mcp/github/exception_handlers.py

Domain exception → HTTP status handlers for github-mcp.

Dependency direction: mcp.github.exception_handlers → fastapi, mcp.github.models
Import from here:  from mcp.github.exception_handlers import setup_exception_handlers
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp.github.models import (
    GitHubAuditError,
    GitHubAuthorizationError,
    GitHubConflictError,
    GitHubNotFoundError,
    GitHubUpstreamError,
    GitHubValidationError,
)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers on the FastAPI app."""

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
