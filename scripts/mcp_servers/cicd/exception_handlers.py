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
    EXCEPTION_ERROR_CODES,
    CicdAuthorizationError,
    CicdConflictError,
    CicdNotFoundError,
    CicdRateLimitError,
    CicdUpstreamError,
    CicdValidationError,
)

# Handler registrations (mcpci004): the four existing status codes are unchanged;
# the conflict and rate-limit types join at 409 and 429.
_HANDLER_STATUS_CODES: dict[type[Exception], int] = {
    CicdAuthorizationError: 403,
    CicdNotFoundError: 404,
    CicdValidationError: 422,
    CicdUpstreamError: 502,
    CicdConflictError: 409,
    CicdRateLimitError: 429,
}


def _make_json_error_handler(
    status_code: int,
    error_code: str,
) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    """Build a handler returning the machine-readable body with the given status code.

    The `detail` key keeps its value; the body gains the stable `error_code` from the
    models row's mapping, plus the preserved metadata fields when the exception
    carries them (REQ-004). The handler does not re-derive the status from the
    message.
    """

    async def _handler(_request: Request, exc: Exception) -> JSONResponse:
        body: dict[str, object] = {"detail": str(exc), "error_code": error_code}
        retry_after = getattr(exc, "retry_after", None)
        rate_limit_reset = getattr(exc, "rate_limit_reset", None)
        if retry_after is not None:
            body["retry_after"] = retry_after
        if rate_limit_reset is not None:
            body["rate_limit_reset"] = rate_limit_reset
        return JSONResponse(body, status_code=status_code)

    return _handler


def setup_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers on the FastAPI app."""
    for exc_type, status_code in _HANDLER_STATUS_CODES.items():
        app.exception_handler(exc_type)(
            _make_json_error_handler(status_code, EXCEPTION_ERROR_CODES[exc_type])
        )
