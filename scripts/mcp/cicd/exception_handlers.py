#!/usr/bin/env python3
"""mcp/cicd/exception_handlers.py

Domain exception → HTTP status handlers for cicd-mcp.

Dependency direction: mcp.cicd.exception_handlers → fastapi, mcp.cicd.models
Import from here:  from mcp.cicd.exception_handlers import setup_exception_handlers
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse
from mcp.cicd.models import (
    CicdAuthorizationError,
    CicdNotFoundError,
    CicdUpstreamError,
    CicdValidationError,
)


def setup_exception_handlers(app: object) -> None:
    """Register domain exception handlers on the FastAPI app."""

    @app.exception_handler(CicdAuthorizationError)  # type: ignore[attr-defined]
    async def _on_cicd_auth_error(
        _req: Any, exc: CicdAuthorizationError
    ) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=403)

    @app.exception_handler(CicdNotFoundError)  # type: ignore[attr-defined]
    async def _on_cicd_not_found(_req: Any, exc: CicdNotFoundError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(CicdValidationError)  # type: ignore[attr-defined]
    async def _on_cicd_validation_error(
        _req: Any, exc: CicdValidationError
    ) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.exception_handler(CicdUpstreamError)  # type: ignore[attr-defined]
    async def _on_cicd_upstream_error(
        _req: Any, exc: CicdUpstreamError
    ) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=502)
