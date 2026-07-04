"""tests/test_mcp_server_health_status.py

Tests for MCP /health endpoint HTTP status code behavior.
When ready=false (dependency failures), the endpoint returns HTTP 503.
When ready=true (fully healthy), the endpoint returns HTTP 200.
"""

from __future__ import annotations

from unittest.mock import patch

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
        assert data["liveness"] is True
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is False

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
            assert data["restart_recommended"] is False
            assert data["operator_action_required"] is True
        else:
            assert data["status"] == "ok"
            assert data["ready"] is True
            assert data["liveness"] is True
            assert data["restart_recommended"] is False
            assert data["operator_action_required"] is False

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
            assert data["restart_recommended"] is False
            assert data["operator_action_required"] is True
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
        assert "liveness" in data
        assert "restart_recommended" in data
        assert "operator_action_required" in data
        assert data["liveness"] is True
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is False

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
            assert "liveness" in data
            assert "restart_recommended" in data
            assert "operator_action_required" in data
            assert data["status"] == "degraded"
            assert data["ready"] is False
            assert data["restart_recommended"] is False
            assert data["operator_action_required"] is True
        finally:
            if original_token is not None:
                os.environ["GITHUB_TOKEN"] = original_token


class TestFileServerHealth:
    """Test /health endpoints for file-read, file-write, file-delete servers."""

    def test_file_read_health_ok_when_workspace_exists(self) -> None:
        """file-read-mcp returns 200 when workspace dependency is healthy."""
        from mcp.file.read_server import app as read_app  # noqa: PLC0415

        with patch("mcp.file.read_server._build_health_deps", return_value={}):
            client = TestClient(read_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["status"] == "ok"
        assert data["liveness"] is True
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is False

    def test_file_read_health_degraded_when_workspace_missing(self) -> None:
        """file-read-mcp returns 503 when workspace directory is absent."""
        from mcp.file.read_server import app as read_app  # noqa: PLC0415

        with patch(
            "mcp.file.read_server._build_health_deps",
            return_value={"filesystem": "/workspace not found"},
        ):
            client = TestClient(read_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False
        assert "filesystem" in data["dependencies"]
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is True

    def test_file_write_health_ok_when_workspace_exists(self) -> None:
        """file-write-mcp returns 200 when workspace dependency is healthy."""
        from mcp.file.write_server import app as write_app  # noqa: PLC0415

        with patch("mcp.file.write_server._build_health_deps", return_value={}):
            client = TestClient(write_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["liveness"] is True
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is False

    def test_file_write_health_degraded_when_workspace_missing(self) -> None:
        """file-write-mcp returns 503 when workspace directory is absent."""
        from mcp.file.write_server import app as write_app  # noqa: PLC0415

        with patch(
            "mcp.file.write_server._build_health_deps",
            return_value={"filesystem": "/workspace not found"},
        ):
            client = TestClient(write_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is True

    def test_file_delete_health_ok_when_workspace_exists(self) -> None:
        """file-delete-mcp returns 200 when workspace dependency is healthy."""
        from mcp.file.delete_server import app as delete_app  # noqa: PLC0415

        with patch("mcp.file.delete_server._build_health_deps", return_value={}):
            client = TestClient(delete_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["liveness"] is True
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is False

    def test_file_delete_health_degraded_when_workspace_missing(self) -> None:
        """file-delete-mcp returns 503 when workspace directory is absent."""
        from mcp.file.delete_server import app as delete_app  # noqa: PLC0415

        with patch(
            "mcp.file.delete_server._build_health_deps",
            return_value={"filesystem": "/workspace not found"},
        ):
            client = TestClient(delete_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is True


class TestRagPipelineServerHealth:
    """Test /health endpoint for rag-pipeline-mcp."""

    def test_degraded_when_embed_url_not_configured(self) -> None:
        """rag-pipeline-mcp returns 503 when embed_url is absent from config."""
        from mcp.rag_pipeline.server import app as rag_app  # noqa: PLC0415

        cfg: dict = {}
        with patch("shared.config_loader.ConfigLoader.load_all", return_value=cfg):
            client = TestClient(rag_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False
        assert data["status"] == "degraded"
        assert "embed_url" in data["dependencies"]
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is True

    def test_ok_when_embed_url_configured(self) -> None:
        """rag-pipeline-mcp returns 200 when embed_url is present in config."""
        from mcp.rag_pipeline.server import app as rag_app  # noqa: PLC0415

        cfg = {"common": {"embed_url": "http://localhost:11434/api/embeddings"}}
        with patch("shared.config_loader.ConfigLoader.load_all", return_value=cfg):
            client = TestClient(rag_app, raise_server_exceptions=False)
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["status"] == "ok"
        assert data["liveness"] is True
        assert data["restart_recommended"] is False
        assert data["operator_action_required"] is False
