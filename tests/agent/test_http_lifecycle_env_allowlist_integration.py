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

# Configuration files whose `${ENV:...}` references a subprocess server actually reads: the
# servers load agent.toml plus their own *_mcp_server.toml, and the rag_pipeline server imports
# scripts/rag/ingestion, which reads the three ingestion files below.
_SUBPROCESS_REACHABLE_CONFIGS: frozenset[str] = frozenset(
    {"agent.toml", "crawler.toml", "chunk_splitter.toml", "ingester.toml"}
)
_SUBPROCESS_REACHABLE_PATTERNS: tuple[str, ...] = ("*_mcp_server.toml",)

# Configuration files no subprocess server reads: eventbus.toml is read by eventbus.app, which
# deploy/setup_services.sh starts directly, and documentation_canonical_sources.toml and
# adr_authority.toml are read only by tools/. Their references must not widen what a child
# process is given.
_OTHER_PROCESS_CONFIGS: frozenset[str] = frozenset(
    {"eventbus.toml", "documentation_canonical_sources.toml", "adr_authority.toml"}
)

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


def _shipped_config_files() -> list[Path]:
    """Every shipped configuration file under config/."""
    return sorted(_CONFIG_DIR.glob("*.toml"))


def _is_subprocess_reachable(name: str) -> bool:
    """Whether a configuration file is one an agent subprocess server reads."""
    return name in _SUBPROCESS_REACHABLE_CONFIGS or any(
        fnmatch.fnmatch(name, pattern) for pattern in _SUBPROCESS_REACHABLE_PATTERNS
    )


def _config_files_by_class() -> tuple[list[Path], list[Path]]:
    """Shipped configuration files split into (subprocess-reachable, other-process)."""
    reachable: list[Path] = []
    other: list[Path] = []
    for path in _shipped_config_files():
        if _is_subprocess_reachable(path.name):
            reachable.append(path)
        else:
            other.append(path)
    return reachable, other


def _env_refs_in(paths: list[Path]) -> set[str]:
    """`${ENV:VAR}` variable names referenced by the given files."""
    refs: set[str] = set()
    for path in paths:
        refs.update(_ENV_REF_RE.findall(path.read_text(encoding="utf-8")))
    return refs


def _config_env_refs() -> set[str]:
    """`${ENV:VAR}` names in the configurations an agent subprocess server reads."""
    return _env_refs_in(_config_files_by_class()[0])


def _all_config_env_refs() -> set[str]:
    """`${ENV:VAR}` names in every shipped configuration file."""
    return _env_refs_in(_shipped_config_files())


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
        parent.update(
            {name: "integration-test-token" for name in _all_config_env_refs()}
        )
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
        assert refs, (
            "no ${ENV:...} reference found in the config files a subprocess server reads"
        )
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
@pytest.mark.usefixtures("firejail_on_path")
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


class TestSubprocessConfigClassification:
    """What the allowlist must cover, and what it must never be asked to cover."""

    def test_every_shipped_config_is_in_exactly_one_class(self) -> None:
        files = _shipped_config_files()
        assert files, "no configuration files found under config/"
        reachable, other = _config_files_by_class()
        assert {path.name for path in reachable}.isdisjoint(
            {path.name for path in other}
        )
        unclassified = sorted(
            path.name
            for path in files
            if not _is_subprocess_reachable(path.name)
            and path.name not in _OTHER_PROCESS_CONFIGS
        )
        assert not unclassified, (
            "config/*.toml files in neither class; adding a configuration is a decision "
            "about whether a subprocess server reads it: " + ", ".join(unclassified)
        )
        for name in sorted(_SUBPROCESS_REACHABLE_CONFIGS | _OTHER_PROCESS_CONFIGS):
            assert (_CONFIG_DIR / name).is_file(), (
                f"classified configuration does not exist: {name}"
            )

    def test_other_process_references_are_not_allowlisted(self) -> None:
        refs = _env_refs_in(_config_files_by_class()[1])
        assert refs, "the other-process configurations reference no ${ENV:...} variable"
        admitted = sorted(name for name in refs if _is_allowed(name))
        assert not admitted, (
            "the subprocess allowlist admits variables no subprocess server reads: "
            + ", ".join(admitted)
        )

    def test_filter_env_keeps_other_process_tokens_out_of_the_child(self) -> None:
        reachable_refs = _config_env_refs()
        other_refs = _env_refs_in(_config_files_by_class()[1])
        assert reachable_refs and other_refs, "classification produced an empty set"
        with patch.dict(os.environ, _parent_env(with_tokens=True), clear=True):
            filtered = CommandValidator().filter_env({})
        assert filtered is not None
        leaked = sorted(name for name in other_refs if name in filtered)
        assert not leaked, (
            "the filtered child environment carries a credential only another process reads: "
            + ", ".join(leaked)
        )
        missing = sorted(name for name in reachable_refs if name not in filtered)
        assert not missing, (
            "the filtered child environment lost a credential a server reads: "
            + ", ".join(missing)
        )
