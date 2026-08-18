"""tests/mcp_servers/cicd/test_cicd_exception_handlers.py

Characterization tests for mcp_servers/cicd/exception_handlers.py.

Locks the domain-exception -> HTTP-status-code -> JSON-body mapping registered by
`setup_exception_handlers` before any refactor of that module. Builds an isolated
FastAPI app (not the shared `cicd_server.app` singleton) so these tests do not
mutate global server state shared with other test modules.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdNotFoundError,
    CicdUpstreamError,
    CicdValidationError,
)
from mcp_servers.cicd.exception_handlers import setup_exception_handlers


def _build_test_app() -> FastAPI:
    """Build a throwaway FastAPI app wired with the cicd exception handlers."""
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/raise-auth")
    async def _raise_auth() -> None:
        raise CicdAuthorizationError("not authorized")

    @app.get("/raise-not-found")
    async def _raise_not_found() -> None:
        raise CicdNotFoundError("workflow not found")

    @app.get("/raise-validation")
    async def _raise_validation() -> None:
        raise CicdValidationError("bad ref")

    @app.get("/raise-upstream")
    async def _raise_upstream() -> None:
        raise CicdUpstreamError("upstream failed")

    return app


class TestSetupExceptionHandlers:
    """Verify each registered handler returns the expected status code and body."""

    def test_authorization_error_returns_403(self) -> None:
        client = TestClient(_build_test_app())
        response = client.get("/raise-auth")
        assert response.status_code == 403
        assert response.json() == {"detail": "not authorized"}

    def test_not_found_error_returns_404(self) -> None:
        client = TestClient(_build_test_app())
        response = client.get("/raise-not-found")
        assert response.status_code == 404
        assert response.json() == {"detail": "workflow not found"}

    def test_validation_error_returns_422(self) -> None:
        client = TestClient(_build_test_app())
        response = client.get("/raise-validation")
        assert response.status_code == 422
        assert response.json() == {"detail": "bad ref"}

    def test_upstream_error_returns_502(self) -> None:
        client = TestClient(_build_test_app())
        response = client.get("/raise-upstream")
        assert response.status_code == 502
        assert response.json() == {"detail": "upstream failed"}
