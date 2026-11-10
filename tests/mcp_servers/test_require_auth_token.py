"""tests/mcp_servers/test_require_auth_token.py — Every MCP server refuses an empty auth token."""

from __future__ import annotations

import ast
import glob
import os
import re
import subprocess  # nosec B404 — fresh-interpreter import checks use a fixed argv
import sys
import tomllib
from pathlib import Path

import pytest
from mcp_servers.server import require_auth_token

# Fresh interpreters bypass the conftest shutil.which shim; give them a stub firejail.
pytestmark = pytest.mark.usefixtures("firejail_on_path")

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
_CONFIG_TOML = _SCRIPTS.parent / "config" / "agent.toml"
_SERVER_SOURCE_GLOB = str(_SCRIPTS / "mcp_servers" / "*" / "*_server.py")
_ENV_REF_RE = re.compile(r"^\$\{ENV:(\w+)\}$")


def _server_source_modules() -> dict[str, str]:
    """Map each ``scripts/mcp_servers/<dir>/<stem>_server.py`` to its config key.

    Key is ``<stem>`` when it equals ``<dir>`` (``shell/shell_server.py`` ->
    ``shell``), otherwise ``<dir>_<stem>`` (``file/delete_server.py`` ->
    ``file_delete``).
    """
    mapping: dict[str, str] = {}
    for path_str in sorted(glob.glob(_SERVER_SOURCE_GLOB)):
        path = Path(path_str)
        stem = path.stem
        if not stem.endswith("_server"):
            continue
        dir_name = path.parent.name
        short = stem[: -len("_server")]
        key = short if short == dir_name else f"{dir_name}_{short}"
        mapping[key] = f"mcp_servers.{dir_name}.{stem}"
    return mapping


def _configured_servers() -> list[tuple[str, str, str]]:
    """Derive ``(key, module, env_var)`` for every ``[mcp_servers.*]`` table.

    Reads the committed ``config/agent.toml`` (not the deployed copy, not
    ``ConfigLoader``) so the test list tracks the config file itself (REQ-005).
    Raises on a table whose ``auth_token`` is not a single ``${ENV:NAME}``
    reference or that has no matching server module — never skips silently.
    """
    with _CONFIG_TOML.open("rb") as handle:
        tables = tomllib.load(handle).get("mcp_servers", {})
    modules = _server_source_modules()
    derived: list[tuple[str, str, str]] = []
    for key, table in tables.items():
        token = str(table.get("auth_token", ""))
        match = _ENV_REF_RE.match(token)
        if match is None:
            raise ValueError(
                f"mcp_servers.{key}: auth_token {token!r} is not a single "
                "${ENV:NAME} reference"
            )
        module = modules.get(key)
        if module is None:
            raise ValueError(
                f"mcp_servers.{key}: no matching scripts/mcp_servers/*/*_server.py"
            )
        derived.append((key, module, match.group(1)))
    derived.sort()
    return derived


_CONFIGURED_SERVERS = _configured_servers()
_SERVERS = [(module, env) for _key, module, env in _CONFIGURED_SERVERS]
_ALL_TOKEN_VARS = [env for _key, _module, env in _CONFIGURED_SERVERS]


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


def test_every_configured_server_resolves_to_a_module_and_token_variable() -> None:
    """REQ-005: every ``[mcp_servers.*]`` table yields exactly one derived server."""
    with _CONFIG_TOML.open("rb") as handle:
        tables = tomllib.load(handle).get("mcp_servers", {})
    assert len(_CONFIGURED_SERVERS) == len(tables)
    for key, module, env_var in _CONFIGURED_SERVERS:
        assert key in tables
        assert module.startswith("mcp_servers.")
        assert module.endswith("_server")
        assert _ENV_REF_RE.match(str(tables[key].get("auth_token", ""))) is not None
        assert tables[key].get("auth_token") == f"${{ENV:{env_var}}}"


def test_every_server_module_is_configured() -> None:
    """Converse check: a ``*_server.py`` module without a config table is a failure."""
    assert set(_server_source_modules()) == {
        key for key, _module, _env in _CONFIGURED_SERVERS
    }


def _routes_through_enforcement_point(source: str) -> bool:
    """True iff the module calls ``require_auth_token()`` somewhere in its AST.

    AST-based (not a substring scan) so comments or string literals named
    ``require_auth_token`` do not produce a false positive.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "require_auth_token"
        ):
            return True
    return False


@pytest.mark.parametrize("path", sorted(glob.glob(_SERVER_SOURCE_GLOB)))
def test_every_server_routes_through_shared_enforcement_point(path: str) -> None:
    with open(path, encoding="utf-8") as handle:
        assert _routes_through_enforcement_point(handle.read()) is True


def test_attach_middleware_without_enforcement_point_is_flagged() -> None:
    synthetic = (
        "from mcp_servers.server import attach_auth_middleware\n"
        "attach_auth_middleware(app, '')\n"
    )
    assert _routes_through_enforcement_point(synthetic) is False
