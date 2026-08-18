#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/exception_handlers.py

Domain exception → HTTP status handlers for cicd-mcp.

Dependency direction: mcp_servers.cicd.exception_handlers → fastapi, mcp_servers.cicd.models
Import from here:  from mcp_servers.cicd.exception_handlers import setup_exception_handlers
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdNotFoundError,
    CicdUpstreamError,
    CicdValidationError,
)


def _make_json_error_handler(
    status_code: int,
) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    """Build a handler returning `{"detail": str(exc)}` with the given status code."""

    async def _handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=status_code)

    return _handler


def setup_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers on the FastAPI app."""
    app.exception_handler(CicdAuthorizationError)(_make_json_error_handler(403))
    app.exception_handler(CicdNotFoundError)(_make_json_error_handler(404))
    app.exception_handler(CicdValidationError)(_make_json_error_handler(422))
    app.exception_handler(CicdUpstreamError)(_make_json_error_handler(502))
