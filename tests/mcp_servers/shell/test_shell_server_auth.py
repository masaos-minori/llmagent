"""tests/mcp_servers/shell/test_shell_server_auth.py

Bearer authentication and fail-closed startup of shell-mcp (REQ-003, REQ-004, REQ-006).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from mcp_servers.shell.shell_models import ShellConfig

_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "scripts"
_MODULE = "mcp_servers.shell.shell_server"
_ENV_VAR = "MCP_SHELL_AUTH_TOKEN"
_TOKEN = "unit-test-token"

pytestmark = pytest.mark.usefixtures("firejail_on_path")

_APP_SCRIPT = """
import json
import sys
from importlib import import_module

from fastapi.testclient import TestClient

mod = import_module(sys.argv[1])
client = TestClient(mod.app, client=("127.0.0.1", 50000), raise_server_exceptions=False)
good = {"Authorization": "Bearer " + sys.argv[2]}
wrong = {"Authorization": "Bearer some-other-token"}
call = {"name": "no_such_tool", "args": {}}
print(json.dumps({
    "tools_without_token": client.get("/v1/tools").status_code,
    "tools_wrong_token": client.get("/v1/tools", headers=wrong).status_code,
    "tools_good_token": client.get("/v1/tools", headers=good).status_code,
    "health_without_token": client.get("/health").status_code,
    "health_wrong_token": client.get("/health", headers=wrong).status_code,
    "health_good_token_is_401": client.get("/health", headers=good).status_code == 401,
    "call_without_token": client.post("/v1/call_tool", json=call).status_code,
    "call_good_token_is_401": client.post("/v1/call_tool", headers=good, json=call).status_code == 401,
}))
"""


def _run(args: list[str], token: str | None) -> subprocess.CompletedProcess[str]:
    """Run python in a separate interpreter with the server variable set, empty, or unset."""
    env = {**os.environ, "PYTHONPATH": str(_SCRIPTS)}
    if token is None:
        env.pop(_ENV_VAR, None)
    else:
        env[_ENV_VAR] = token
    return subprocess.run(
        [sys.executable, *args],
        env=env,
        cwd=str(_SCRIPTS),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


class TestRealAppAuthentication:
    def test_requests_require_the_token(self) -> None:
        proc = _run(["-c", _APP_SCRIPT, _MODULE, _TOKEN], token=_TOKEN)
        assert proc.returncode == 0, proc.stderr[-500:]
        codes = json.loads(proc.stdout.strip().splitlines()[-1])
        assert codes == {
            "tools_without_token": 401,
            "tools_wrong_token": 401,
            "tools_good_token": 200,
            "health_without_token": 401,
            "health_wrong_token": 401,
            "health_good_token_is_401": False,
            "call_without_token": 401,
            "call_good_token_is_401": False,
        }


class TestFailClosedStartup:
    def test_empty_token_refuses_to_start(self) -> None:
        proc = _run(["-c", f"import {_MODULE}"], token="")
        assert proc.returncode != 0
        assert "RuntimeError" in proc.stderr
        assert "shell-mcp: auth_token is empty" in proc.stderr

    def test_unset_variable_fails_fast(self) -> None:
        proc = _run(["-c", f"import {_MODULE}"], token=None)
        assert proc.returncode != 0
        assert "ValueError" in proc.stderr
        assert _ENV_VAR in proc.stderr

    def test_non_empty_token_imports(self) -> None:
        assert _run(["-c", f"import {_MODULE}"], token=_TOKEN).returncode == 0


class TestShellConfigAuthToken:
    def test_default_is_empty(self) -> None:
        assert ShellConfig.from_dict({}).auth_token == ""

    def test_env_reference_is_resolved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_ENV_VAR, "abc")
        cfg = ShellConfig.from_dict({"auth_token": "${ENV:" + _ENV_VAR + "}"})
        assert cfg.auth_token == "abc"

    def test_unset_reference_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(_ENV_VAR, raising=False)
        with pytest.raises(ValueError):
            ShellConfig.from_dict({"auth_token": "${ENV:" + _ENV_VAR + "}"})

    def test_shipped_toml_uses_the_agent_variable(self) -> None:
        text = (_REPO / "config" / "shell_mcp_server.toml").read_text(encoding="utf-8")
        assert tomllib.loads(text)["auth_token"] == "${ENV:" + _ENV_VAR + "}"
        agent = (_REPO / "config" / "agent.toml").read_text(encoding="utf-8")
        assert "${ENV:" + _ENV_VAR + "}" in agent
