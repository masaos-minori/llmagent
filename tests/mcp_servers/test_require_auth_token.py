"""tests/mcp_servers/test_require_auth_token.py — Every MCP server refuses an empty auth token."""

from __future__ import annotations

import os
import subprocess  # nosec B404 — fresh-interpreter import checks use a fixed argv
import sys
from pathlib import Path

import pytest
from mcp_servers.server import require_auth_token

# Fresh interpreters bypass the conftest shutil.which shim; give them a stub firejail.
pytestmark = pytest.mark.usefixtures("firejail_on_path")

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"

_SERVERS = [
    ("mcp_servers.shell.shell_server", "MCP_SHELL_AUTH_TOKEN"),
    ("mcp_servers.git.git_server", "MCP_GIT_AUTH_TOKEN"),
    ("mcp_servers.web_search.web_search_server", "MCP_WEB_SEARCH_AUTH_TOKEN"),
    ("mcp_servers.file.delete_server", "MCP_FILE_DELETE_AUTH_TOKEN"),
    ("mcp_servers.file.write_server", "MCP_FILE_WRITE_AUTH_TOKEN"),
    ("mcp_servers.file.read_server", "MCP_FILE_READ_AUTH_TOKEN"),
    ("mcp_servers.github.github_server", "MCP_GITHUB_AUTH_TOKEN"),
    ("mcp_servers.cicd.cicd_server", "MCP_CICD_AUTH_TOKEN"),
    ("mcp_servers.rag_pipeline.rag_pipeline_server", "MCP_RAG_PIPELINE_AUTH_TOKEN"),
    ("mcp_servers.mdq.mdq_server", "MCP_MDQ_AUTH_TOKEN"),
]
_ALL_TOKEN_VARS = [env for _module, env in _SERVERS]


class TestRequireAuthToken:
    @pytest.mark.parametrize("token", ["", None])
    def test_empty_token_raises(self, token: str | None) -> None:
        with pytest.raises(RuntimeError, match="auth_token is empty"):
            require_auth_token("demo-mcp", "MCP_DEMO_AUTH_TOKEN", token)

    def test_message_names_the_server_and_variable(self) -> None:
        with pytest.raises(RuntimeError) as excinfo:
            require_auth_token("demo-mcp", "MCP_DEMO_AUTH_TOKEN", "")
        assert "demo-mcp" in str(excinfo.value)
        assert "MCP_DEMO_AUTH_TOKEN" in str(excinfo.value)

    def test_non_empty_token_is_returned_unchanged(self) -> None:
        assert require_auth_token("demo-mcp", "MCP_DEMO_AUTH_TOKEN", "abc") == "abc"


def _import_in_fresh_interpreter(
    module: str, empty_var: str | None, log_dir: Path
) -> subprocess.CompletedProcess[str]:
    env = {key: os.environ[key] for key in ("PATH", "HOME") if key in os.environ}
    env.update({var: "test-token" for var in _ALL_TOKEN_VARS})
    if empty_var is not None:
        env[empty_var] = ""
    env["PYTHONPATH"] = str(_SCRIPTS)
    env["LLMAGENT_LOG_DIR"] = str(log_dir)
    return subprocess.run(  # nosec B603 — fixed argv, no shell
        [sys.executable, "-c", f"import {module}"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


@pytest.mark.parametrize(("module", "env_var"), _SERVERS)
def test_empty_token_prevents_every_server_from_importing(
    module: str, env_var: str, tmp_path: Path
) -> None:
    result = _import_in_fresh_interpreter(module, env_var, tmp_path)
    assert result.returncode != 0
    assert "auth_token is empty" in result.stderr


def test_non_empty_tokens_let_a_server_import(tmp_path: Path) -> None:
    result = _import_in_fresh_interpreter("mcp_servers.git.git_server", None, tmp_path)
    assert result.returncode == 0, result.stderr
