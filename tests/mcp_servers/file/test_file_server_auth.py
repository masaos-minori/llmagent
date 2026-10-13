"""tests/mcp_servers/file/test_file_server_auth.py

Bearer authentication and fail-closed startup of the file-read, file-write, and
file-delete servers (REQ-003, REQ-004, REQ-006).

mcp_servers/file/__init__.py imports all three server modules, so importing any
one of them also runs the other two: an empty token for one server makes every
import fail, and the message names the server whose token is empty.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from mcp_servers.file.delete_models import FileDeleteConfig
from mcp_servers.file.read_models import FileReadConfig
from mcp_servers.file.write_models import FileWriteConfig

_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "scripts"
_TOKEN = "unit-test-token"

# (id, module, variable, server name used in the message, config class, TOML file)
_SERVERS = [
    (
        "read",
        "mcp_servers.file.read_server",
        "MCP_FILE_READ_AUTH_TOKEN",
        "file-read-mcp",
        FileReadConfig,
        "file_read_mcp_server.toml",
    ),
    (
        "write",
        "mcp_servers.file.write_server",
        "MCP_FILE_WRITE_AUTH_TOKEN",
        "file-write-mcp",
        FileWriteConfig,
        "file_write_mcp_server.toml",
    ),
    (
        "delete",
        "mcp_servers.file.delete_server",
        "MCP_FILE_DELETE_AUTH_TOKEN",
        "file-delete-mcp",
        FileDeleteConfig,
        "file_delete_mcp_server.toml",
    ),
]
_IDS = [s[0] for s in _SERVERS]

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


def _run(
    args: list[str], env_var: str, token: str | None
) -> subprocess.CompletedProcess[str]:
    """Run python in a separate interpreter; set, empty, or unset only the given variable."""
    env = {**os.environ, "PYTHONPATH": str(_SCRIPTS)}
    if token is None:
        env.pop(env_var, None)
    else:
        env[env_var] = token
    return subprocess.run(
        [sys.executable, *args],
        env=env,
        cwd=str(_SCRIPTS),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize(
    "_id, module, env_var, name, cfg_cls, toml", _SERVERS, ids=_IDS
)
class TestFileServerAuth:
    def test_requests_require_the_token(
        self, _id, module, env_var, name, cfg_cls, toml
    ) -> None:
        proc = _run(["-c", _APP_SCRIPT, module, _TOKEN], env_var, _TOKEN)
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

    def test_empty_token_refuses_to_start(
        self, _id, module, env_var, name, cfg_cls, toml
    ) -> None:
        proc = _run(["-c", f"import {module}"], env_var, "")
        assert proc.returncode != 0
        assert "RuntimeError" in proc.stderr
        assert f"{name}: auth_token is empty" in proc.stderr

    def test_unset_variable_fails_fast(
        self, _id, module, env_var, name, cfg_cls, toml
    ) -> None:
        proc = _run(["-c", f"import {module}"], env_var, None)
        assert proc.returncode != 0
        assert "ValueError" in proc.stderr
        assert env_var in proc.stderr

    def test_model_loads_the_token(
        self, _id, module, env_var, name, cfg_cls, toml, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert cfg_cls.from_dict({}).auth_token == ""
        monkeypatch.setenv(env_var, "abc")
        assert (
            cfg_cls.from_dict({"auth_token": "${ENV:" + env_var + "}"}).auth_token
            == "abc"
        )
        monkeypatch.delenv(env_var, raising=False)
        with pytest.raises(ValueError):
            cfg_cls.from_dict({"auth_token": "${ENV:" + env_var + "}"})

    def test_shipped_toml_uses_the_agent_variable(
        self, _id, module, env_var, name, cfg_cls, toml
    ) -> None:
        text = (_REPO / "config" / toml).read_text(encoding="utf-8")
        assert tomllib.loads(text)["auth_token"] == "${ENV:" + env_var + "}"
        agent = (_REPO / "config" / "agent.toml").read_text(encoding="utf-8")
        assert "${ENV:" + env_var + "}" in agent
