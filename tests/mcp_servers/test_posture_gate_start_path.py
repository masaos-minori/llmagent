"""tests/mcp_servers/test_posture_gate_start_path.py — Posture gate on every MCP server launch path."""

from __future__ import annotations

import importlib
import runpy
import sys
import types
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from mcp_servers.server import MCPServer

_SERVERS = [
    ("mcp_servers.shell.shell_server", "ShellMCPServer"),
    ("mcp_servers.git.git_server", "GitMCPServer"),
    ("mcp_servers.web_search.web_search_server", "WebSearchMCPServer"),
    ("mcp_servers.file.delete_server", "FileDeleteMCPServer"),
    ("mcp_servers.file.write_server", "FileWriteMCPServer"),
    ("mcp_servers.file.read_server", "FileReadMCPServer"),
    ("mcp_servers.github.github_server", "GithubMCPServer"),
    ("mcp_servers.cicd.cicd_server", "CiCdMCPServer"),
    ("mcp_servers.rag_pipeline.rag_pipeline_server", "RagPipelineMCPServer"),
    ("mcp_servers.mdq.mdq_server", "MdqMCPServer"),
]
_FAILED = SimpleNamespace(validated=False, checks=[])
_OK = SimpleNamespace(validated=True, checks=[])


class _Reached(Exception):
    """Raised by the patched uvicorn.Config to show the gate let the start proceed."""


@pytest.mark.parametrize(("module_name", "class_name"), _SERVERS)
def test_failed_posture_exits_before_binding(
    module_name: str, class_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(module_name)
    monkeypatch.setattr(module, "_security_posture", _FAILED)
    server = getattr(module, class_name)()
    with (
        patch("shared.config_loader.ConfigLoader.restrict_to"),
        patch("uvicorn.Config", side_effect=AssertionError("uvicorn was built")),
        pytest.raises(SystemExit) as excinfo,
    ):
        server.run_http()
    assert excinfo.value.code == 1


def test_validated_posture_reaches_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("mcp_servers.shell.shell_server")
    monkeypatch.setattr(module, "_security_posture", _OK)
    with (
        patch("shared.config_loader.ConfigLoader.restrict_to"),
        patch("uvicorn.Config", side_effect=_Reached),
        pytest.raises(_Reached),
    ):
        module.ShellMCPServer().run_http()


@pytest.mark.parametrize(("module_name", "_class_name"), _SERVERS)
def test_every_server_module_defines_the_gate(
    module_name: str, _class_name: str
) -> None:
    assert callable(importlib.import_module(module_name)._enforce_posture_gate)


def test_module_without_a_gate_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.ModuleType("mcp_servers.fake_missing_gate")
    monkeypatch.setitem(sys.modules, "mcp_servers.fake_missing_gate", fake)

    class _NoGate(MCPServer):
        server_name = "no-gate-mcp"
        server_version = "1.0"
        http_port = 9999
        app_module = "mcp_servers.fake_missing_gate:app"
        own_config_file = "test_mcp_server.toml"

    with (
        patch("shared.config_loader.ConfigLoader.restrict_to"),
        pytest.raises(RuntimeError, match="_enforce_posture_gate"),
    ):
        _NoGate().run_http()


def test_importing_the_mdq_entry_module_starts_nothing() -> None:
    with patch.object(MCPServer, "run_http", side_effect=AssertionError("started")):
        sys.modules.pop("mcp_servers.mdq.__main__", None)
        importlib.import_module("mcp_servers.mdq.__main__")


def test_running_the_mdq_entry_module_goes_through_run_http() -> None:
    with patch.object(MCPServer, "run_http", autospec=True) as run_http:
        sys.modules.pop("mcp_servers.mdq.__main__", None)
        runpy.run_module("mcp_servers.mdq", run_name="__main__")
    assert run_http.call_count == 1
