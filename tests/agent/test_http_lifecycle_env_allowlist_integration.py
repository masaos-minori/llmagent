"""tests/agent/test_http_lifecycle_env_allowlist_integration.py

Integration gate for the per-server subprocess environment (cliplc006 REQ-006, REQ-007).

Two questions the unit tests in test_http_lifecycle_command_validator.py cannot answer:

1. Does each shipped subprocess server receive exactly its own environment: the fixed
   runtime set, its own two derived tokens, and the credentials its config declares —
   and nothing another server or another process reads?
2. Is that minimal environment actually sufficient to start the server? A builder that
   is merely narrower than before can stop every subprocess from starting.

The gates below answer both against `config/agent.toml`, and the startup gate starts a
real child process per configured subprocess server under its own minimal environment.
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
from agent.http_lifecycle_command_validator import _DEFAULT_PROTECTED_ENV_VARS
from agent.http_lifecycle_launch_spec import build_child_env
from shared.mcp_config import _ENV_KEY_DENYLIST, McpServerConfig, _build_mcp_servers

pytestmark = pytest.mark.contract

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_CONFIG_DIR = _REPO_ROOT / "config"

_ENV_REF_RE = re.compile(r"\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}")

# The REQ-006 fixed runtime set, restated here as the gate's own expectation: a child
# inherits these from the Agent process and nothing else besides its own credentials.
_FIXED_RUNTIME_PATTERNS: frozenset[str] = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "SHELL",
        "TMPDIR",
        "TMP",
        "TEMP",
        "LANG",
        "LC_*",
        "LLMAGENT_CONFIG_DIR",
        "LLMAGENT_SUDACHI_DICT",
    }
)

# Loader/interpreter variables that must never reach a subprocess, asserted here so a
# future runtime set cannot admit them by accident.
_LOADER_ENV_VARS = ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")

# Configuration files whose `${ENV:...}` references a subprocess server actually reads: the
# servers load agent.toml plus their own *_mcp_server.toml (which carries the server's
# [dedup] table, mcpdl003 REQ-001), and the rag_pipeline server imports
# scripts/rag/ingestion, which reads the three ingestion files below.
_SUBPROCESS_REACHABLE_CONFIGS: frozenset[str] = frozenset(
    {
        "agent.toml",
        "crawler.toml",
        "chunk_splitter.toml",
        "ingester.toml",
    }
)
_SUBPROCESS_REACHABLE_PATTERNS: tuple[str, ...] = ("*_mcp_server.toml",)

# Configuration files no subprocess server reads: eventbus.toml is read by eventbus.app, which
# deploy/setup_services.sh starts directly, and documentation_canonical_sources.toml and
# adr_authority.toml are read only by tools/. Their references must not widen what a child
# process is given.
_OTHER_PROCESS_CONFIGS: frozenset[str] = frozenset(
    {
        "eventbus.toml",
        "documentation_canonical_sources.toml",
        "adr_authority.toml",
        # Static ownership/capability registry (REQ-004/005). Loaded in-process by
        # mcp_tool_discovery.py::_load_tool_catalog() at startup; no subprocess server
        # reads it, so it is not subprocess-reachable.
        "tool_catalog.toml",
    }
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


def _server_configs() -> dict[str, McpServerConfig]:
    """The shipped subprocess servers as the Agent parses them."""
    return _build_mcp_servers({"mcp_servers": _subprocess_servers()})


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


def _derived_token_names(server_key: str) -> set[str]:
    """The two token names the Agent derives for one server key."""
    upper = server_key.upper()
    return {
        f"MCP_{upper}_AUTH_TOKEN",
        f"MCP_{upper}_CONTROL_TOKEN",
    }


def _parent_env(*, with_tokens: bool) -> dict[str, str]:
    """A deterministic parent environment: the runtime basics plus the config tokens.

    `clear=True` keeps the gate independent of the developer's or CI runner's own
    variables, so a passing run means the per-server builder itself is sufficient.
    """
    parent: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/root"),
    }
    if with_tokens:
        parent.update(
            {name: "integration-test-token" for name in _all_config_env_refs()}
        )
        parent.update(
            {
                name: "integration-test-token"
                for cfg in _server_configs().values()
                for name in cfg.credential_env
            }
        )
    return parent


def _expected_child_keys(
    server_key: str, cfg: McpServerConfig, parent: dict[str, str]
) -> set[str]:
    """The exact key set one server's child environment must hold."""
    expected = {
        name
        for name in parent
        if any(fnmatch.fnmatch(name, pattern) for pattern in _FIXED_RUNTIME_PATTERNS)
    }
    expected |= {name for name in _derived_token_names(server_key) if name in parent}
    expected |= {name for name in cfg.credential_env if name in parent}
    for name in cfg.env:
        if any(fnmatch.fnmatch(name, pattern) for pattern in _ENV_KEY_DENYLIST):
            continue
        if name in _DEFAULT_PROTECTED_ENV_VARS:
            continue
        expected.add(name)
    return expected


def _child_env(
    server_key: str, cfg: McpServerConfig, parent: dict[str, str]
) -> dict[str, str]:
    """Build one server's child environment against a deterministic parent."""
    with patch.dict(os.environ, parent, clear=True):
        return build_child_env(server_key, cfg)


def _start_child(
    server_key: str,
    cfg: McpServerConfig,
    entry_module: str,
    parent: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    """Start a real child process with exactly the environment build_child_env produces.

    `cwd=scripts/` is required: PYTHONPATH is denylisted, and `python -c` puts the
    working directory at sys.path[0], which is how a compiled binary resolves its
    modules without any path variable.
    """
    env = _child_env(server_key, cfg, parent)
    return subprocess.run(
        [sys.executable, "-c", f"import {entry_module}; print('IMPORT_OK')"],
        env=env,
        cwd=str(_SCRIPTS_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )


class TestPerServerEnvironmentIsExact:
    """Each shipped server receives exactly its own minimal environment."""

    def test_each_shipped_server_env_is_exactly_its_own(self) -> None:
        parent = _parent_env(with_tokens=True)
        mismatches: list[str] = []
        for key, cfg in sorted(_server_configs().items()):
            env = _child_env(key, cfg, parent)
            expected = _expected_child_keys(key, cfg, parent)
            if set(env) != expected:
                missing = sorted(expected - set(env))
                extra = sorted(set(env) - expected)
                mismatches.append(f"{key}: missing={missing} extra={extra}")
        assert not mismatches, (
            "server environments are not exactly the fixed runtime set plus the "
            "server's own credentials:\n" + "\n".join(mismatches)
        )

    def test_github_token_only_for_designated_servers(self) -> None:
        """REQ-007: GITHUB_TOKEN reaches github and cicd, and no other server."""
        cfgs = _server_configs()
        designated = {
            key for key, cfg in cfgs.items() if "GITHUB_TOKEN" in cfg.credential_env
        }
        assert designated == {"github", "cicd"}, (
            "config/agent.toml declares GITHUB_TOKEN for a different server set: "
            + ", ".join(sorted(designated))
        )
        parent = {**_parent_env(with_tokens=True), "GITHUB_TOKEN": "ght-token"}
        for key, cfg in sorted(cfgs.items()):
            env = _child_env(key, cfg, parent)
            assert ("GITHUB_TOKEN" in env) is (key in designated), (
                f"{key}: GITHUB_TOKEN presence does not match its credential_env"
            )

    def test_no_server_receives_another_servers_token(self) -> None:
        """AC-3: with every server's tokens in the parent, each child holds only its own."""
        cfgs = _server_configs()
        all_tokens = {name for key in cfgs for name in _derived_token_names(key)}
        parent = {
            **_parent_env(with_tokens=True),
            **{name: "integration-test-token" for name in all_tokens},
        }
        leaked: list[str] = []
        for key, cfg in sorted(cfgs.items()):
            env = _child_env(key, cfg, parent)
            others = all_tokens - _derived_token_names(key)
            found = sorted(others & set(env))
            if found:
                leaked.append(f"{key}: {found}")
        assert not leaked, (
            "a server environment carries another server's credential:\n"
            + "\n".join(leaked)
        )

    def test_each_server_holds_its_own_declared_credentials(self) -> None:
        """Every `${ENV:...}` token a server's own config reads reaches that server."""
        cfgs = _server_configs()
        parent = _parent_env(with_tokens=True)
        missing: list[str] = []
        for key, cfg in sorted(cfgs.items()):
            env = _child_env(key, cfg, parent)
            own = {name for name in _derived_token_names(key) if name in parent}
            absent = sorted(own - set(env))
            if absent:
                missing.append(f"{key}: {absent}")
        assert not missing, (
            "a server environment lost a credential its own config reads:\n"
            + "\n".join(missing)
        )

    def test_loader_variables_never_reach_a_child(self) -> None:
        """The narrowed runtime set cannot admit a loader/interpreter variable."""
        parent = {
            **_parent_env(with_tokens=True),
            **{name: "/tmp/evil" for name in _LOADER_ENV_VARS},
        }
        admitted = [
            name
            for key, cfg in sorted(_server_configs().items())
            for name in _LOADER_ENV_VARS
            if name in _child_env(key, cfg, parent)
        ]
        assert not admitted, (
            f"a child environment carries a loader variable: {admitted}"
        )

    def test_startup_audit_names_keys_not_values(self, caplog) -> None:
        """REQ-007: the launch audit records environment key names, never their values."""
        cfgs = _server_configs()
        parent = _parent_env(with_tokens=True)
        with caplog.at_level("INFO"):
            for key, cfg in sorted(cfgs.items()):
                _child_env(key, cfg, parent)
        assert "MCP_SHELL_AUTH_TOKEN" in caplog.text
        assert "integration-test-token" not in caplog.text


class TestSubprocessConfigClassification:
    """What the per-server environment must cover, and what it must never be asked to cover."""

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

    def test_other_process_references_are_not_in_the_runtime_set(self) -> None:
        refs = _env_refs_in(_config_files_by_class()[1])
        assert refs, "the other-process configurations reference no ${ENV:...} variable"
        admitted = sorted(
            name
            for name in refs
            if any(
                fnmatch.fnmatch(name, pattern) for pattern in _FIXED_RUNTIME_PATTERNS
            )
        )
        assert not admitted, (
            "the fixed runtime set admits variables no subprocess server reads: "
            + ", ".join(admitted)
        )

    def test_child_env_keeps_other_process_tokens_out(self) -> None:
        """The per-server equivalent of the old filter gate: no other-process credential."""
        reachable_refs = _config_env_refs()
        other_refs = _env_refs_in(_config_files_by_class()[1])
        assert reachable_refs and other_refs, "classification produced an empty set"
        cfgs = _server_configs()
        leaked: list[str] = []
        missing: list[str] = []
        parent = _parent_env(with_tokens=True)
        for key, cfg in sorted(cfgs.items()):
            env = _child_env(key, cfg, parent)
            found = sorted(other_refs & set(env))
            if found:
                leaked.append(f"{key}: {found}")
            own = {name for name in _derived_token_names(key) if name in reachable_refs}
            absent = sorted(own - set(env))
            if absent:
                missing.append(f"{key}: {absent}")
        assert not leaked, (
            "a child environment carries a credential only another process reads:\n"
            + "\n".join(leaked)
        )
        assert not missing, (
            "a child environment lost a credential its own server reads:\n"
            + "\n".join(missing)
        )


@pytest.mark.integration
@pytest.mark.usefixtures("firejail_on_path")
class TestMinimalEnvironmentStartsEveryServer:
    """A real child process per configured subprocess server, started with its own env."""

    def test_each_subprocess_server_starts_under_filtered_env(self) -> None:
        failures: list[str] = []
        cfgs = _server_configs()
        parent = _parent_env(with_tokens=True)
        for key, cfg in sorted(cfgs.items()):
            module = _SERVER_ENTRY_MODULES.get(key)
            if module is None:
                failures.append(f"{key}: no entry module in _SERVER_ENTRY_MODULES")
                continue
            result = _start_child(key, cfg, module, parent)
            if result.returncode != 0 or "IMPORT_OK" not in (result.stdout or ""):
                tail = (result.stderr or "").strip().splitlines()
                failures.append(
                    f"{key}: rc={result.returncode} {tail[-1] if tail else ''}"
                )
        assert not failures, (
            "servers that cannot start under their minimal environment:\n"
            + "\n".join(failures)
        )

    def test_missing_token_breaks_the_child_import(self) -> None:
        """Negative control: without the server's own token the gate must fail, not pass vacuously."""
        cfgs = _server_configs()
        result = _start_child(
            "shell",
            cfgs["shell"],
            _SERVER_ENTRY_MODULES["shell"],
            _parent_env(with_tokens=False),
        )
        assert result.returncode != 0, (
            "child started successfully with no MCP_SHELL_AUTH_TOKEN in the parent: "
            "the gate no longer detects a missing credential"
        )
        assert "MCP_SHELL_AUTH_TOKEN" in (result.stderr or "")
