#!/usr/bin/env python3
"""scripts/mcp_servers/github/exception_handlers.py

Domain exception → HTTP status handlers for github-mcp.

Dependency direction: mcp_servers.github.exception_handlers → fastapi, mcp_servers.github.models
Import from here:  from mcp_servers.github.exception_handlers import setup_exception_handlers
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.write_outcome import OUTCOME_UNKNOWN

from mcp_servers.github.github_models import (
    GitHubAuditError,
    GitHubAuthorizationError,
    GitHubConflictError,
    GitHubNotFoundError,
    GitHubUpstreamError,
    GitHubValidationError,
)
from mcp_servers.github.github_models_config import GitHubOutcomeUnknownError


def setup_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers on the FastAPI app."""

    @app.exception_handler(GitHubAuthorizationError)
    async def _handle_auth_error(
        request: Request, exc: GitHubAuthorizationError
    ) -> JSONResponse:
        """Return 403 for authorization failures."""
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(GitHubNotFoundError)
    async def _handle_not_found(
        request: Request, exc: GitHubNotFoundError
    ) -> JSONResponse:
        """Return 404 for resource-not-found errors."""
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(GitHubValidationError)
    async def _handle_validation(
        request: Request, exc: GitHubValidationError
    ) -> JSONResponse:
        """Return 400 for validation errors."""
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(GitHubConflictError)
    async def _handle_conflict(
        request: Request, exc: GitHubConflictError
    ) -> JSONResponse:
        """Return 409 for conflict errors (e.g., duplicate PR)."""
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(GitHubUpstreamError)
    async def _handle_upstream(
        request: Request, exc: GitHubUpstreamError
    ) -> JSONResponse:
        """Return 502 for upstream API failures."""
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(GitHubOutcomeUnknownError)
    async def _handle_outcome_unknown(
        request: Request, exc: GitHubOutcomeUnknownError
    ) -> JSONResponse:
        """Return 504 for an ambiguous write outcome.

        502 already carries definite upstream failures, so 504 is the status the
        Agent transport reads as an outcome that cannot be retried.
        """
        return JSONResponse(
            status_code=504,
            content={"detail": str(exc), "outcome": OUTCOME_UNKNOWN},
        )

    @app.exception_handler(GitHubAuditError)
    async def _handle_audit(request: Request, exc: GitHubAuditError) -> JSONResponse:
        """Return 500 for audit logging failures, naming the outcome.

        A pre-write audit failure means nothing was applied, so the body reports
        audit_failed rather than an ambiguous outcome. An applied write whose
        completion audit failed is converted by the dispatcher before it reaches
        here.
        """
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "outcome": "audit_failed"},
        )
