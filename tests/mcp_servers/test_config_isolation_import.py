"""tests/mcp_servers/test_config_isolation_import.py — Each MCP server reads only its own config file."""

from __future__ import annotations

import importlib
import json
import re
import subprocess  # nosec B404 — fresh-interpreter import checks use a fixed argv
import sys
from collections.abc import Callable, Sequence
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


def _run(
    script: str,
    log_dir: Path,
    build_env: Callable[..., dict[str, str]],
    args: Sequence[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = build_env(
        {
            **{var: "test-token" for var in _TOKEN_VARS},
            "PYTHONPATH": str(_SCRIPTS),
            "LLMAGENT_LOG_DIR": str(log_dir),
        }
    )
    cmd = [sys.executable, "-c", script]
    if args:
        cmd += args
    return subprocess.run(  # nosec B603 — fixed argv, no shell
        cmd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


# Fresh-interpreter record script for the single-execution regression. It runs the
# real run_http() (only uvicorn.Config is stubbed) and counts how many times the
# target module is imported under its real name AFTER runpy executes ENTRY as
# __main__. Any such re-import re-runs the module body, so this counts second
# executions precisely — independent of how many config-load sites the target has
# internally. The posture gate is forced to pass so run_http() proceeds to the
# uvicorn.Config stub.
_ONCE_RECORD = """
import importlib, json, runpy, sys
from types import SimpleNamespace
ENTRY = sys.argv[1]
TARGET = sys.argv[2]
_second = []
_orig_import_module = importlib.import_module
def counting_import(name, *a, **k):
    result = _orig_import_module(name, *a, **k)
    if name == TARGET:
        _second.append(result)
    return result
importlib.import_module = counting_import
from shared.config_loader import ConfigLoader
_loaded = []
_orig_load = ConfigLoader.load
def rec_load(self, name, *a, **k):
    _loaded.append(name)
    return _orig_load(self, name, *a, **k)
ConfigLoader.load = rec_load
import shared.security.startup_flow as flow
flow.run_startup_validation = lambda *a, **k: SimpleNamespace(validated=True, checks=[])
class _Reached(Exception):
    pass
def _stub_config(*a, **k):
    raise _Reached
import uvicorn
uvicorn.Config = _stub_config
try:
    runpy.run_module(ENTRY, run_name="__main__", alter_sys=True)
except _Reached:
    pass
except SystemExit:
    pass
print(json.dumps({"entry": ENTRY, "target": TARGET, "second_imports": len(_second), "config_loads": sorted(set(_loaded))}))
"""

# (entry, target, config_file): ENTRY is passed to runpy as __main__; TARGET is the
# module whose real-name re-import signals a second body execution. For the mdq
# entry point the entry module is mcp_servers.mdq (__main__.py) and the gated
# module is its mdq_server submodule.
_ONCE_SERVERS: list[tuple[str, str, str]] = [
    (
        "mcp_servers.shell.shell_server",
        "mcp_servers.shell.shell_server",
        "shell_mcp_server.toml",
    ),
    ("mcp_servers.git.git_server", "mcp_servers.git.git_server", "git_mcp_server.toml"),
    (
        "mcp_servers.web_search.web_search_server",
        "mcp_servers.web_search.web_search_server",
        "web_search_mcp_server.toml",
    ),
    (
        "mcp_servers.file.delete_server",
        "mcp_servers.file.delete_server",
        "file_delete_mcp_server.toml",
    ),
    (
        "mcp_servers.file.write_server",
        "mcp_servers.file.write_server",
        "file_write_mcp_server.toml",
    ),
    (
        "mcp_servers.file.read_server",
        "mcp_servers.file.read_server",
        "file_read_mcp_server.toml",
    ),
    (
        "mcp_servers.github.github_server",
        "mcp_servers.github.github_server",
        "github_mcp_server.toml",
    ),
    (
        "mcp_servers.cicd.cicd_server",
        "mcp_servers.cicd.cicd_server",
        "cicd_mcp_server.toml",
    ),
    (
        "mcp_servers.rag_pipeline.rag_pipeline_server",
        "mcp_servers.rag_pipeline.rag_pipeline_server",
        "rag_pipeline_mcp_server.toml",
    ),
    ("mcp_servers.mdq", "mcp_servers.mdq.mdq_server", "mdq_mcp_server.toml"),
]


def _record(
    prelude: str,
    body: str,
    log_dir: Path,
    build_env: Callable[..., dict[str, str]],
) -> dict[str, list[str]]:
    result = _run(
        _RECORD_SCRIPT.format(prelude=prelude, body=body),
        log_dir,
        build_env=build_env,
    )
    assert result.returncode == 0, result.stderr
    parsed: dict[str, list[str]] = json.loads(result.stdout.strip().splitlines()[-1])
    return parsed


@pytest.mark.parametrize(("module", "config_file"), _SERVERS)
def test_restrict_first_import_loads_only_the_own_config(
    module: str,
    config_file: str,
    tmp_path: Path,
    isolated_subprocess_env: Callable[..., dict[str, str]],
) -> None:
    recorded = _record(
        f"ConfigLoader.restrict_to({config_file!r})",
        f"import {module}",
        tmp_path,
        isolated_subprocess_env,
    )
    assert recorded["loaded"] == [config_file]


def test_importing_one_file_server_does_not_import_its_siblings(
    tmp_path: Path,
    isolated_subprocess_env: Callable[..., dict[str, str]],
) -> None:
    recorded = _record(
        "",
        "import mcp_servers.file.read_server",
        tmp_path,
        isolated_subprocess_env,
    )
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


@pytest.mark.parametrize(("entry", "target", "config_file"), _ONCE_SERVERS)
def test_a_server_module_executes_once_under_python_m(
    entry: str,
    target: str,
    config_file: str,
    tmp_path: Path,
    isolated_subprocess_env: Callable[..., dict[str, str]],
) -> None:
    """Run the real run_http() (only uvicorn.Config stubbed) and assert the server
    module body executes exactly once under `python -m` / runpy.

    Measures the target module's real-name re-import count after runpy executes
    ENTRY as __main__: 0 means executed once, >=1 means the posture gate re-imported
    a second copy. Fails on current code (gate re-imports) and passes after the
    server.py fix (gate resolves the already-running instance). Also asserts only
    the server's own config file is loaded (REQ-001, REQ-004).
    """
    result = _run(
        _ONCE_RECORD,
        tmp_path,
        build_env=isolated_subprocess_env,
        args=[entry, target],
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout.strip().splitlines()[-1])
    assert parsed["second_imports"] == 0, (
        f"{entry} executed more than once under python -m "
        f"(re-imported {parsed['second_imports']} time(s))"
    )
    assert parsed["config_loads"] == [config_file]


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
