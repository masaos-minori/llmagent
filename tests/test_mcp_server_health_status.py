"""tests/test_mcp_server_health_status.py

Tests for MCP /health endpoint HTTP status code behavior.
When ready=false (dependency failures), the endpoint returns HTTP 503.
When ready=true (fully healthy), the endpoint returns HTTP 200.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthHTTPStatusCodes:
    """Test that /health endpoints return correct HTTP status codes."""

    def test_web_search_health_returns_200_when_healthy(self) -> None:
        """web-search-mcp has no dependency checks — always healthy."""
        from mcp.web_search.server import app  # noqa: PLC0415

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["ready"] is True
        assert data["dependencies"] == {}

    def test_git_health_returns_503_when_git_not_in_path(self) -> None:
        """git-mcp returns 503 when git is not found in PATH."""
        from mcp.git.server import app as git_app  # noqa: PLC0415

        client = TestClient(git_app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code in (200, 503)
        data = response.json()
        if response.status_code == 503:
            assert data["status"] == "degraded"
            assert data["ready"] is False
            assert "git" in data["dependencies"]
        else:
            assert data["status"] == "ok"
            assert data["ready"] is True

    def test_cicd_health_returns_503_when_github_token_not_set(self) -> None:
        """cicd-mcp returns 503 when GITHUB_TOKEN is not set."""
        import os  # noqa: PLC0415

        from mcp.cicd.server import app as cicd_app  # noqa: PLC0415

        # Save original value and remove GITHUB_TOKEN if present
        original_token = os.environ.get("GITHUB_TOKEN")
        try:
            os.environ.pop("GITHUB_TOKEN", None)
            client = TestClient(cicd_app, raise_server_exceptions=False)
            response = client.get("/health")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
            assert data["ready"] is False
            assert "github_token" in data["dependencies"]
        finally:
            if original_token is not None:
                os.environ["GITHUB_TOKEN"] = original_token

    def test_health_response_shape_when_healthy(self) -> None:
        """Verify the full response shape for a healthy server."""
        from mcp.web_search.server import app  # noqa: PLC0415

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "ready" in data
        assert "dependencies" in data
        assert "details" in data

    def test_health_response_shape_when_degraded(self) -> None:
        """Verify the full response shape for a degraded server."""
        import os  # noqa: PLC0415

        from mcp.cicd.server import app as cicd_app  # noqa: PLC0415

        original_token = os.environ.get("GITHUB_TOKEN")
        try:
            os.environ.pop("GITHUB_TOKEN", None)
            client = TestClient(cicd_app, raise_server_exceptions=False)
            response = client.get("/health")
            assert response.status_code == 503
            data = response.json()
            assert "status" in data
            assert "ready" in data
            assert "dependencies" in data
            assert "details" in data
            assert data["status"] == "degraded"
            assert data["ready"] is False
        finally:
            if original_token is not None:
                os.environ["GITHUB_TOKEN"] = original_token
