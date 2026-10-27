"""tests/mcp_servers/test_config_isolation_import.py — Each MCP server reads only its own config file."""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess  # nosec B404 — fresh-interpreter import checks use a fixed argv
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _ROOT / "scripts"

# Fresh interpreters bypass the conftest shutil.which shim; give them a stub firejail.
pytestmark = pytest.mark.usefixtures("firejail_on_path")

_SERVERS = [
    ("mcp_servers.shell.shell_server", "shell_mcp_server.toml"),
    ("mcp_servers.git.git_server", "git_mcp_server.toml"),
    ("mcp_servers.web_search.web_search_server", "web_search_mcp_server.toml"),
    ("mcp_servers.file.delete_server", "file_delete_mcp_server.toml"),
    ("mcp_servers.file.write_server", "file_write_mcp_server.toml"),
    ("mcp_servers.file.read_server", "file_read_mcp_server.toml"),
    ("mcp_servers.github.github_server", "github_mcp_server.toml"),
    ("mcp_servers.cicd.cicd_server", "cicd_mcp_server.toml"),
    ("mcp_servers.rag_pipeline.rag_pipeline_server", "rag_pipeline_mcp_server.toml"),
    ("mcp_servers.mdq.mdq_server", "mdq_mcp_server.toml"),
]
_TOKEN_VARS = [
    "MCP_SHELL_AUTH_TOKEN",
    "MCP_GIT_AUTH_TOKEN",
    "MCP_WEB_SEARCH_AUTH_TOKEN",
    "MCP_FILE_DELETE_AUTH_TOKEN",
    "MCP_FILE_WRITE_AUTH_TOKEN",
    "MCP_FILE_READ_AUTH_TOKEN",
    "MCP_GITHUB_AUTH_TOKEN",
    "MCP_CICD_AUTH_TOKEN",
    "MCP_RAG_PIPELINE_AUTH_TOKEN",
    "MCP_MDQ_AUTH_TOKEN",
]

_RECORD_SCRIPT = """
import json, sys
from shared.config_loader import ConfigLoader
loaded = []
original = ConfigLoader.load
def record(self, name, *args, **kwargs):
    loaded.append(name)
    return original(self, name, *args, **kwargs)
ConfigLoader.load = record
{prelude}
{body}
print(json.dumps({{"loaded": sorted(set(loaded)), "modules": sorted(m for m in sys.modules if m.startswith("mcp_servers.file."))}}))
"""


def _run(script: str, log_dir: Path) -> subprocess.CompletedProcess[str]:
    env = {key: os.environ[key] for key in ("PATH", "HOME") if key in os.environ}
    env.update({var: "test-token" for var in _TOKEN_VARS})
    env["PYTHONPATH"] = str(_SCRIPTS)
    env["LLMAGENT_LOG_DIR"] = str(log_dir)
    return subprocess.run(  # nosec B603 — fixed argv, no shell
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def _record(prelude: str, body: str, log_dir: Path) -> dict[str, list[str]]:
    result = _run(_RECORD_SCRIPT.format(prelude=prelude, body=body), log_dir)
    assert result.returncode == 0, result.stderr
    parsed: dict[str, list[str]] = json.loads(result.stdout.strip().splitlines()[-1])
    return parsed


@pytest.mark.parametrize(("module", "config_file"), _SERVERS)
def test_restrict_first_import_loads_only_the_own_config(
    module: str, config_file: str, tmp_path: Path
) -> None:
    recorded = _record(
        f"ConfigLoader.restrict_to({config_file!r})", f"import {module}", tmp_path
    )
    assert recorded["loaded"] == [config_file]


def test_importing_one_file_server_does_not_import_its_siblings(
    tmp_path: Path,
) -> None:
    recorded = _record("", "import mcp_servers.file.read_server", tmp_path)
    assert recorded["loaded"] == ["file_read_mcp_server.toml"]
    assert "mcp_servers.file.delete_server" not in recorded["modules"]
    assert "mcp_servers.file.write_server" not in recorded["modules"]


@pytest.mark.parametrize(
    ("package", "alias", "submodule"),
    [
        ("git", "server", "git_server"),
        ("cicd", "server", "cicd_server"),
        ("mdq", "models", "mdq_models"),
        ("mdq", "tools", "mdq_tools"),
        ("rag_pipeline", "service", "rag_pipeline_service"),
        ("web_search", "models", "web_search_models"),
    ],
)
def test_lazy_aliases_resolve_to_the_submodules(
    package: str, alias: str, submodule: str
) -> None:
    pkg = importlib.import_module(f"mcp_servers.{package}")
    assert getattr(pkg, alias) is importlib.import_module(
        f"mcp_servers.{package}.{submodule}"
    )


def test_unknown_package_attribute_raises() -> None:
    pkg = importlib.import_module("mcp_servers.git")
    with pytest.raises(AttributeError):
        pkg.not_an_alias  # noqa: B018 — attribute access is the behavior under test


def test_a_server_module_executes_once_under_python_m(tmp_path: Path) -> None:
    prelude = (
        "from mcp_servers.server import MCPServer\n"
        "MCPServer.run_http = lambda self: None\n"
        "import runpy"
    )
    body = 'runpy.run_module("mcp_servers.git.git_server", run_name="__main__")'
    script = _RECORD_SCRIPT.format(prelude=prelude, body=body).replace(
        'print(json.dumps({"loaded": sorted(set(loaded))',
        'print(json.dumps({"loaded": loaded',
    )
    result = _run(script, tmp_path)
    assert result.returncode == 0, result.stderr
    loaded = json.loads(result.stdout.strip().splitlines()[-1])["loaded"]
    assert loaded.count("git_mcp_server.toml") == 1


def _entries() -> list[tuple[str, str, str]]:
    text = (_ROOT / "deploy" / "build_binaries.sh").read_text(encoding="utf-8")
    block = text[text.index("ENTRIES=(") : text.index("\n)\n", text.index("ENTRIES=("))]
    rows = re.findall(r'"([^"]+)"', block)
    parsed = []
    for row in rows:
        module, _name, cls, cfg = row.split(":")
        if cls:
            parsed.append((module, cls, cfg))
    return parsed


def test_entries_table_matches_the_server_classes() -> None:
    entries = _entries()
    assert len(entries) == len(_SERVERS)
    for module, class_name, config_file in entries:
        server_cls = getattr(importlib.import_module(module), class_name)
        assert server_cls.own_config_file == config_file


def test_launcher_template_restricts_config_before_the_server_import() -> None:
    text = (_ROOT / "deploy" / "build_binaries.sh").read_text(encoding="utf-8")
    restrict = text.index('ConfigLoader.restrict_to("${cfg}")')
    server_import = text.index("from ${module} import ${cls}")
    assert restrict < server_import
