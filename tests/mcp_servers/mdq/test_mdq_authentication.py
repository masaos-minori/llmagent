"""tests/mcp_servers/mdq/test_mdq_authentication.py

Bearer authentication of mdq-mcp (ADR-007): every protected request needs the
server token, and `allowed_dirs` path authorization applies only afterwards.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 — runs the current interpreter on a fixed import statement
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mcp_servers.mdq.mdq_server import app

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS, MCP_TEST_TOKEN

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
_OUTSIDE_PATH = "/etc/passwd"
_CALL_OUTLINE = {"name": "outline", "args": {"path": _OUTSIDE_PATH}}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestAuthentication:
    @pytest.mark.parametrize(
        "headers",
        [
            {},
            {"Authorization": ""},
            {"Authorization": "Bearer "},
            {"Authorization": f"Basic {MCP_TEST_TOKEN}"},
            {"Authorization": MCP_TEST_TOKEN},
            {"Authorization": "Bearer wrong-token"},
        ],
        ids=["missing", "empty", "empty-bearer", "wrong-scheme", "no-scheme", "wrong"],
    )
    def test_protected_endpoints_reject_bad_credentials(
        self, client: TestClient, headers: dict[str, str]
    ) -> None:
        assert client.get("/v1/tools", headers=headers).status_code == 401
        assert (
            client.post(
                "/v1/call_tool", json=_CALL_OUTLINE, headers=headers
            ).status_code
            == 401
        )
        assert client.get("/health", headers=headers).status_code == 401

    def test_correct_token_passes_authentication(self, client: TestClient) -> None:
        assert client.get("/v1/tools", headers=MCP_TEST_AUTH_HEADERS).status_code == 200
        assert client.get("/health", headers=MCP_TEST_AUTH_HEADERS).status_code in (
            200,
            503,
        )

    def test_401_response_does_not_expose_the_token(self, client: TestClient) -> None:
        resp = client.get("/v1/tools", headers={"Authorization": "Bearer wrong-token"})
        assert MCP_TEST_TOKEN not in resp.text
        assert "wrong-token" not in resp.text


class TestAuthenticationBeforeAuthorization:
    def test_wrong_token_with_disallowed_path_is_401_without_path_details(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/call_tool",
            json=_CALL_OUTLINE,
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 401
        assert _OUTSIDE_PATH not in resp.text
        assert "allowed" not in resp.text.lower()

    def test_correct_token_with_disallowed_path_is_an_authorization_error(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/call_tool", json=_CALL_OUTLINE, headers=MCP_TEST_AUTH_HEADERS
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "outside allowed directories" in body["result"]


class TestStartupRequiresToken:
    def _import_server(self, token: str | None) -> subprocess.CompletedProcess[str]:
        env = {k: v for k, v in os.environ.items() if k != "MCP_MDQ_AUTH_TOKEN"}
        if token is not None:
            env["MCP_MDQ_AUTH_TOKEN"] = token
        env["PYTHONPATH"] = str(_SCRIPTS_DIR)
        return subprocess.run(  # nosec B603 — fixed argv: current interpreter, constant import statement
            [sys.executable, "-c", "import mcp_servers.mdq.mdq_server"],
            cwd=_SCRIPTS_DIR.parent,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_empty_token_refuses_to_start(self) -> None:
        result = self._import_server("")
        assert result.returncode != 0
        assert "auth_token is empty" in result.stderr

    def test_unset_token_variable_refuses_to_start(self) -> None:
        result = self._import_server(None)
        assert result.returncode != 0
        assert "MCP_MDQ_AUTH_TOKEN" in result.stderr

    def test_non_empty_token_starts_and_is_not_logged(self) -> None:
        result = self._import_server("secret-value-123")
        assert result.returncode == 0, result.stderr
        assert "secret-value-123" not in result.stdout + result.stderr
