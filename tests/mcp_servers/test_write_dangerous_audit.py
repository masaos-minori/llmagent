"""tests/mcp_servers/test_write_dangerous_audit.py

Cross-server audit-coverage guard for every WRITE_DANGEROUS tool (REQ-002, AC-2).

Two layers:
  1. A parametrized test over the 13 WRITE_DANGEROUS tools mapped to their five
     hosting servers. Each case drives the server's own ``POST /v1/call_tool``
     with the service stubbed (``_service`` replaced, per the existing
     per-server endpoint tests) and asserts exactly one ``mcp_tool_exec`` audit
     record with the correct ``tool``, ``server_key``, and ``outcome``. The
     external service is never exercised: the stubbed dispatch table returns a
     plain success string.
  2. A completeness test that derives the WRITE_DANGEROUS set from
     ``config/agent.toml`` ``[tool_safety_tiers]`` and asserts it equals the
     parametrized set — drift in either direction fails.

Servers whose own logger also emits non-JSON kvlog info lines (git-mcp) are
filtered by ``event == "mcp_tool_exec"`` so the assertion counts audit
records only, mirroring tests/mcp_servers/file/test_file_server_audit_records.py's
logger-capture approach.
"""

from __future__ import annotations

import dataclasses
import json
import tomllib
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import git
import pytest
from fastapi.testclient import TestClient
from mcp_servers.cicd import cicd_server
from mcp_servers.cicd.cicd_models import CicdConfig
from mcp_servers.file import delete_server
from mcp_servers.git import git_server
from mcp_servers.git.git_security import _resolve_repo_path
from mcp_servers.github import github_server
from mcp_servers.rag_pipeline import rag_pipeline_server

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

_REPO_ROOT = Path(__file__).resolve().parents[2]

# server_key -> the WRITE_DANGEROUS tools it hosts. The keys match the
# server_key value each server stamps into its audit records.
_SERVER_TOOLS: dict[str, list[str]] = {
    "file_delete": ["delete_file", "delete_directory"],
    "github": [
        "github_push_files",
        "github_create_or_update_file",
        "github_delete_file",
        "github_create_pull_request",
        "github_update_pull_request",
        "github_merge_pull_request",
    ],
    "rag_pipeline": ["rag_delete_document"],
    "cicd": ["trigger_workflow"],
    "git": ["git_checkout", "git_pull", "git_push"],
}

_SERVER_MODULES: dict[str, Any] = {
    "file_delete": delete_server,
    "github": github_server,
    "rag_pipeline": rag_pipeline_server,
    "cicd": cicd_server,
    "git": git_server,
}

_CASES: list[tuple[str, str]] = [
    (server_key, tool) for server_key, tools in _SERVER_TOOLS.items() for tool in tools
]


class _FakeService:
    """Stand-in for a server's service singleton, exposing only get_dispatch_table.

    Handlers return a plain success string, matching the handler contract
    documented in dispatch_tool (the DispatchResult wrapper is built there).
    """

    def __init__(self, tool_names: list[str]) -> None:
        self._table: dict[str, Any] = {
            name: AsyncMock(return_value="stubbed success") for name in tool_names
        }

    def get_dispatch_table(self) -> dict[str, Any]:
        return self._table


def _capture_logger(monkeypatch: pytest.MonkeyPatch, module: Any) -> MagicMock:
    """Replace the server module's logger so emitted records can be read back."""
    fake = MagicMock()
    monkeypatch.setattr(module, "logger", fake)
    return fake


def _audit_records(logger: MagicMock) -> list[dict[str, Any]]:
    """Parse only the JSON-lines audit records the mocked logger received.

    Servers such as git-mcp also log non-JSON kvlog info lines around the
    audit call; those are skipped here so the assertion counts audit records.
    """
    records: list[dict[str, Any]] = []
    for call in logger.info.call_args_list:
        try:
            payload = json.loads(call.args[0])
        except (TypeError, ValueError):
            continue
        if isinstance(payload, dict) and payload.get("event") == "mcp_tool_exec":
            records.append(payload)
    return records


def _working_repo(tmp_path: Path) -> str:
    """Create a working git repo with one commit (mirrors test_repository_state.py)."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    repo = git.Repo.init(str(repo_dir))
    f = repo_dir / "README.md"
    f.write_text("# test")
    repo.index.add([str(f)])
    repo.index.commit("initial")
    return str(repo_dir)


def _prepare_server(
    server_key: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Any]:
    """Stub the server's service/config surface and return valid call args for its tool.

    Returns the args dict to POST. Only what each server's call_tool path
    touches before audit emission is replaced; no external service is called.
    """
    if server_key == "file_delete":
        monkeypatch.setattr(
            delete_server,
            "_cfg",
            dataclasses.replace(delete_server._cfg, allowed_dirs=[str(tmp_path)]),
        )
        monkeypatch.setattr(
            delete_server, "_service", _FakeService(_SERVER_TOOLS[server_key])
        )
        return {"path": str(tmp_path / "target.txt")}
    if server_key == "github":
        monkeypatch.setattr(
            github_server, "_service", _FakeService(_SERVER_TOOLS[server_key])
        )
        # The disabled-tool gate checks the module token before dispatch.
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "fake-token")
        return {
            "owner": "acme",
            "repo": "widgets",
            "branch": "feature-x",
            "message": "msg",
            "path": "docs/a.md",
            "content": "x",
            "title": "pr title",
            "head": "feature-x",
            "base": "trunk",
            "pull_number": 1,
        }
    if server_key == "rag_pipeline":
        monkeypatch.setattr(
            rag_pipeline_server, "_service", _FakeService(_SERVER_TOOLS[server_key])
        )
        return {"url": "https://example.com/doc"}
    if server_key == "cicd":
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=["ci.yml"]),
        )
        monkeypatch.setattr(
            cicd_server, "_service", _FakeService(_SERVER_TOOLS[server_key])
        )
        return {"repo": "acme/widgets", "workflow_id": "ci.yml"}
    if server_key == "git":
        repo_path = _working_repo(tmp_path)
        _, _, resolved = _resolve_repo_path(repo_path)
        monkeypatch.setattr(
            git_server,
            "_cfg",
            dataclasses.replace(
                git_server._cfg,
                allowed_repo_paths=[resolved],
                read_only=False,
            ),
        )
        monkeypatch.setattr(
            git_server, "_service", _FakeService(_SERVER_TOOLS[server_key])
        )
        return {"repo_path": resolved, "branch": "feature-x", "remote": "origin"}
    raise AssertionError(f"unknown server_key {server_key!r}")


@pytest.mark.parametrize(
    ("server_key", "tool"),
    _CASES,
    ids=[f"{server_key}::{tool}" for server_key, tool in _CASES],
)
def test_write_dangerous_tool_emits_audit_record(
    server_key: str,
    tool: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Each WRITE_DANGEROUS tool must produce exactly one audit record on its server."""
    module = _SERVER_MODULES[server_key]
    args = _prepare_server(server_key, monkeypatch, tmp_path)
    logger = _capture_logger(monkeypatch, module)
    client = TestClient(module.app, headers=MCP_TEST_AUTH_HEADERS)

    resp = client.post("/v1/call_tool", json={"name": tool, "args": args})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_error"] is False, body["result"]

    records = _audit_records(logger)
    assert len(records) == 1, records
    record = records[0]
    assert record["tool"] == tool
    assert record["server_key"] == server_key
    assert record["outcome"] == "ok"


def test_parametrization_matches_config_write_dangerous() -> None:
    """The parametrized (server, tool) set must equal the config's WRITE_DANGEROUS set."""
    data = tomllib.loads(
        (_REPO_ROOT / "config" / "agent.toml").read_text(encoding="utf-8")
    )
    config_tools = {
        name
        for name, tier in data["tool_safety_tiers"].items()
        if tier == "WRITE_DANGEROUS"
    }
    parametrized_tools = {tool for _, tool in _CASES}
    assert parametrized_tools == config_tools
    # Every tool maps to exactly one server (no duplicates in the map).
    flat = [tool for tools in _SERVER_TOOLS.values() for tool in tools]
    assert len(flat) == len(set(flat))
