"""tests/agent/test_http_lifecycle_env_allowlist_integration.py

Integration gate for the default-deny subprocess environment allowlist.

Two questions the unit tests in test_http_lifecycle_command_validator.py cannot answer:

1. Is `_DEFAULT_ALLOWED_ENV_VARS` still aligned with what the shipped config and the
   child processes actually read? A static allowlist drifts the moment a server is
   added or a config starts referencing a new `${ENV:...}` variable.
2. Is the filtered environment actually sufficient to start a server? A filter that is
   merely narrower than before can stop every subprocess from starting.

The gates below answer both against `config/agent.toml`, and the startup gate starts a
real child process per configured subprocess server.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from agent.http_lifecycle_command_validator import (
    _DEFAULT_ALLOWED_ENV_VARS,
    CommandValidator,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_CONFIG_DIR = _REPO_ROOT / "config"

_ENV_REF_RE = re.compile(r"\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}")

# Loader/interpreter variables that must never reach a subprocess, asserted here so a
# future allowlist pattern cannot admit them by accident.
_LOADER_ENV_VARS = ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")

# Entry module for each `startup_mode = "subprocess"` server in config/agent.toml.
# The repository holds no binary-name to module build manifest (the binaries are built
# on the deployment host), so this table is the mapping, and
# test_server_entry_mapping_covers_every_subprocess_server fails loudly when a server
# is added to the config without extending it.
_SERVER_ENTRY_MODULES: dict[str, str] = {
    "shell": "mcp_servers.shell.shell_server",
    "git": "mcp_servers.git.git_server",
    "web_search": "mcp_servers.web_search.web_search_server",
    "file_read": "mcp_servers.file.read_server",
    "file_write": "mcp_servers.file.write_server",
    "file_delete": "mcp_servers.file.delete_server",
    "github": "mcp_servers.github.github_server",
    "cicd": "mcp_servers.cicd.cicd_server",
    "rag_pipeline": "mcp_servers.rag_pipeline.rag_pipeline_server",
    "mdq": "mcp_servers.mdq.mdq_server",
}


def _configured_servers() -> dict[str, Any]:
    """Return the raw `[mcp_servers.*]` sections of config/agent.toml."""
    data = tomllib.loads((_CONFIG_DIR / "agent.toml").read_text(encoding="utf-8"))
    servers = data.get("mcp_servers") or {}
    assert servers, "config/agent.toml defines no [mcp_servers.*] section"
    return servers


def _subprocess_servers() -> dict[str, Any]:
    return {
        key: cfg
        for key, cfg in _configured_servers().items()
        if cfg.get("startup_mode") == "subprocess"
    }


def _config_env_refs() -> set[str]:
    """Every `${ENV:VAR}` variable name referenced by the shipped config."""
    refs: set[str] = set()
    for path in sorted(_CONFIG_DIR.glob("*.toml")):
        refs.update(_ENV_REF_RE.findall(path.read_text(encoding="utf-8")))
    return refs


def _is_allowed(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in _DEFAULT_ALLOWED_ENV_VARS)


def _parent_env(*, with_tokens: bool) -> dict[str, str]:
    """A deterministic parent environment: the runtime basics plus the config tokens.

    `clear=True` keeps the gate independent of the developer's or CI runner's own
    variables, so a passing run means the allowlist itself is sufficient.
    """
    parent: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/root"),
    }
    if with_tokens:
        parent.update({name: "integration-test-token" for name in _config_env_refs()})
    return parent


def _start_child(
    entry_module: str, parent: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Start a real child process with exactly the environment filter_env produces.

    `cwd=scripts/` is required: PYTHONPATH is denylisted, and `python -c` puts the
    working directory at sys.path[0], which is how a compiled binary resolves its
    modules without any path variable.
    """
    with patch.dict(os.environ, parent, clear=True):
        env = CommandValidator().filter_env({})
    return subprocess.run(
        [sys.executable, "-c", f"import {entry_module}; print('IMPORT_OK')"],
        env=env,
        cwd=str(_SCRIPTS_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )


class TestAllowlistCoversShippedConfig:
    """The allowlist must cover every variable the shipped config asks the child to read."""

    def test_config_env_refs_are_all_allowlisted(self) -> None:
        refs = _config_env_refs()
        assert refs, "no ${ENV:...} reference found in config/*.toml"
        uncovered = sorted(name for name in refs if not _is_allowed(name))
        assert not uncovered, (
            "config references ${ENV:...} variables the allowlist does not admit: "
            + ", ".join(uncovered)
        )

    def test_allowlist_does_not_admit_denylisted_loader_vars(self) -> None:
        admitted = [name for name in _LOADER_ENV_VARS if _is_allowed(name)]
        assert not admitted, (
            f"allowlist admits loader/interpreter variables: {admitted}"
        )

    def test_server_entry_mapping_covers_every_subprocess_server(self) -> None:
        missing = sorted(set(_subprocess_servers()) - set(_SERVER_ENTRY_MODULES))
        assert not missing, (
            "subprocess servers with no entry module in _SERVER_ENTRY_MODULES: "
            + ", ".join(missing)
        )
        for key, module in _SERVER_ENTRY_MODULES.items():
            if key not in _subprocess_servers():
                continue
            source = _SCRIPTS_DIR / (module.replace(".", "/") + ".py")
            assert source.is_file(), (
                f"{key}: entry module {module} not found at {source}"
            )


@pytest.mark.integration
class TestFilteredEnvironmentStartsEveryServer:
    """A real child process per configured subprocess server, started with the filtered env."""

    def test_each_subprocess_server_starts_under_filtered_env(self) -> None:
        failures: list[str] = []
        for key, cfg in sorted(_subprocess_servers().items()):
            result = _start_child(
                _SERVER_ENTRY_MODULES[key], _parent_env(with_tokens=True)
            )
            if result.returncode != 0 or "IMPORT_OK" not in (result.stdout or ""):
                tail = (result.stderr or "").strip().splitlines()
                failures.append(
                    f"{key}: rc={result.returncode} {tail[-1] if tail else ''}"
                )
        assert not failures, (
            "servers that cannot start under the filtered environment:\n"
            + "\n".join(failures)
        )

    def test_missing_token_breaks_the_child_import(self) -> None:
        """Negative control: without the token pattern the gate must fail, not pass vacuously."""
        result = _start_child(
            _SERVER_ENTRY_MODULES["shell"], _parent_env(with_tokens=False)
        )
        assert result.returncode != 0, (
            "child started successfully with no MCP_*_AUTH_TOKEN in the parent: "
            "the gate no longer detects a missing allowlist entry"
        )
        assert "MCP_SHELL_AUTH_TOKEN" in (result.stderr or "")
