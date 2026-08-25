"""tests/test_tools_endpoint.py

Live /v1/tools endpoint validation for file-server and git-server MCP tools.

Asserts every tool in GET /v1/tools responses carries enabled: bool and
disabled_reason: str, and that the two correlate (enabled=True <=> disabled_reason == "").

See also tests/test_mcp_tools_validation.py (requirement 15) for sibling tests
validating exact disabled_reason string values and computation-level correctness;
this file validates the contract shape against malformed-metadata reaching Agent-side discovery.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

_FILE_SERVERS: list[tuple[str, str, str]] = [
    ("mcp_servers.file.read_server", "FileReadConfig", "mcp_servers.file.read_models"),
    (
        "mcp_servers.file.write_server",
        "FileWriteConfig",
        "mcp_servers.file.write_models",
    ),
    (
        "mcp_servers.file.delete_server",
        "FileDeleteConfig",
        "mcp_servers.file.delete_models",
    ),
]

# All three file servers now wire include_disabled/disabled_code through
# build_tools_response() (REQ-005: read_server.py, write_server.py, delete_server.py
# all migrated) — the include_disabled/disabled_code-specific tests below can use
# the full _FILE_SERVERS list.
_FILE_SERVERS_REQ_005 = _FILE_SERVERS


@pytest.mark.parametrize("server_mod_path, cfg_cls_name, cfg_mod_path", _FILE_SERVERS)
def test_file_server_tools_disabled_when_allowed_dirs_empty(
    server_mod_path: str,
    cfg_cls_name: str,
    cfg_mod_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All tools are disabled when allowed_dirs is empty.

    include_disabled=true: once a file server switches its /v1/tools handler to
    build_tools_response() (REQ-005), the default include_disabled=False would
    filter this response down to an empty list and this assertion would pass
    vacuously instead of exercising the disabled state.
    """
    server_mod = importlib.import_module(server_mod_path)
    cfg_mod = importlib.import_module(cfg_mod_path)
    cfg_cls = getattr(cfg_mod, cfg_cls_name)
    monkeypatch.setattr(server_mod, "_cfg", cfg_cls(allowed_dirs=[]))
    client = TestClient(server_mod.app)
    data = client.get("/v1/tools?include_disabled=true").json()
    assert data["tools"]
    for tool in data["tools"]:
        assert tool["enabled"] is False
        assert (
            isinstance(tool["disabled_reason"], str) and tool["disabled_reason"] != ""
        )


@pytest.mark.parametrize("server_mod_path, cfg_cls_name, cfg_mod_path", _FILE_SERVERS)
def test_file_server_tools_enabled_when_allowed_dirs_set(
    server_mod_path: str,
    cfg_cls_name: str,
    cfg_mod_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All tools are enabled when allowed_dirs is non-empty."""
    server_mod = importlib.import_module(server_mod_path)
    cfg_mod = importlib.import_module(cfg_mod_path)
    cfg_cls = getattr(cfg_mod, cfg_cls_name)
    monkeypatch.setattr(server_mod, "_cfg", cfg_cls(allowed_dirs=["/tmp"]))
    client = TestClient(server_mod.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        assert tool["enabled"] is True
        assert (
            isinstance(tool["disabled_reason"], str) and tool["disabled_reason"] == ""
        )


@pytest.mark.parametrize(
    "server_mod_path, cfg_cls_name, cfg_mod_path", _FILE_SERVERS_REQ_005
)
def test_file_server_include_disabled_false_omits_disabled_tools(
    server_mod_path: str,
    cfg_cls_name: str,
    cfg_mod_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """include_disabled=false (the default) omits disabled tools (REQ-005)."""
    server_mod = importlib.import_module(server_mod_path)
    cfg_mod = importlib.import_module(cfg_mod_path)
    cfg_cls = getattr(cfg_mod, cfg_cls_name)
    monkeypatch.setattr(server_mod, "_cfg", cfg_cls(allowed_dirs=[]))
    client = TestClient(server_mod.app)
    data = client.get("/v1/tools?include_disabled=false").json()
    assert data["tools"] == []


@pytest.mark.parametrize(
    "server_mod_path, cfg_cls_name, cfg_mod_path", _FILE_SERVERS_REQ_005
)
def test_file_server_disabled_code_filters_to_matching_tools(
    server_mod_path: str,
    cfg_cls_name: str,
    cfg_mod_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """disabled_code filters the response to tools matching that reason (REQ-005)."""
    server_mod = importlib.import_module(server_mod_path)
    cfg_mod = importlib.import_module(cfg_mod_path)
    cfg_cls = getattr(cfg_mod, cfg_cls_name)
    monkeypatch.setattr(server_mod, "_cfg", cfg_cls(allowed_dirs=[]))
    client = TestClient(server_mod.app)
    data = client.get(
        "/v1/tools?include_disabled=true&disabled_code=allowed_dirs+is+empty"
    ).json()
    assert data["tools"]
    for tool in data["tools"]:
        assert tool["disabled_reason"] == "allowed_dirs is empty"


def test_git_tools_all_disabled_when_allowed_repo_paths_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All git tools are disabled when allowed_repo_paths is empty.

    include_disabled=true: since REQ-005, git_server.py's /v1/tools now filters
    out disabled tools by default (via build_tools_response()) — without this
    parameter the response would be an empty list and this assertion would pass
    vacuously instead of exercising the disabled state.
    """
    from mcp_servers.git import server as git_server
    from mcp_servers.git.git_models import GitConfig

    monkeypatch.setattr(
        git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=True)
    )
    client = TestClient(git_server.app)
    data = client.get("/v1/tools?include_disabled=true").json()
    assert data["tools"]
    for tool in data["tools"]:
        assert tool["enabled"] is False
        assert (
            isinstance(tool["disabled_reason"], str) and tool["disabled_reason"] != ""
        )


def test_git_write_tools_disabled_when_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only write tools are disabled when read_only=true with valid repo paths.

    include_disabled=true: see test_git_tools_all_disabled_when_allowed_repo_paths_empty
    for why this is required post-REQ-005.
    """
    from mcp_servers.git import server as git_server
    from mcp_servers.git.git_models import GitConfig
    from shared.tool_constants import GIT_WRITE_TOOLS

    monkeypatch.setattr(
        git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=True)
    )
    client = TestClient(git_server.app)
    data = client.get("/v1/tools?include_disabled=true").json()
    assert data["tools"]
    for tool in data["tools"]:
        expect_disabled = tool["name"] in GIT_WRITE_TOOLS
        assert tool["enabled"] is (not expect_disabled)
        assert (tool["disabled_reason"] != "") is expect_disabled


def test_git_tools_all_enabled_when_repo_paths_set_and_not_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All git tools are enabled when allowed_repo_paths is set and read_only=false."""
    from mcp_servers.git import server as git_server
    from mcp_servers.git.git_models import GitConfig

    monkeypatch.setattr(
        git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=False)
    )
    client = TestClient(git_server.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        assert tool["enabled"] is True
        assert (
            isinstance(tool["disabled_reason"], str) and tool["disabled_reason"] == ""
        )


def test_git_include_disabled_false_omits_disabled_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """include_disabled=false (the default) omits disabled tools (REQ-005)."""
    from mcp_servers.git import server as git_server
    from mcp_servers.git.git_models import GitConfig

    monkeypatch.setattr(
        git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=True)
    )
    client = TestClient(git_server.app)
    data = client.get("/v1/tools?include_disabled=false").json()
    assert data["tools"] == []


def test_git_disabled_code_filters_to_matching_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """disabled_code filters the response to tools matching that reason (REQ-005)."""
    from mcp_servers.git import server as git_server
    from mcp_servers.git.git_models import GitConfig

    monkeypatch.setattr(
        git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=True)
    )
    client = TestClient(git_server.app)
    data = client.get(
        "/v1/tools?include_disabled=true&disabled_code=allowed_repo_paths+is+empty"
    ).json()
    assert data["tools"]
    for tool in data["tools"]:
        assert tool["disabled_reason"] == "allowed_repo_paths is empty"


def test_enabled_and_disabled_reason_types_across_all_servers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assert type-correctness of enabled/disabled_reason across all four servers' fully-enabled state."""
    from mcp_servers.git import server as git_server
    from mcp_servers.git.git_models import GitConfig

    # File servers
    for server_mod_path, cfg_cls_name, cfg_mod_path in _FILE_SERVERS:
        server_mod = importlib.import_module(server_mod_path)
        cfg_mod = importlib.import_module(cfg_mod_path)
        cfg_cls = getattr(cfg_mod, cfg_cls_name)
        monkeypatch.setattr(server_mod, "_cfg", cfg_cls(allowed_dirs=["/tmp"]))
        client = TestClient(server_mod.app)
        data = client.get("/v1/tools").json()
        for tool in data["tools"]:
            assert isinstance(tool["enabled"], bool)
            assert isinstance(tool["disabled_reason"], str)

    # Git server
    monkeypatch.setattr(
        git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=False)
    )
    client = TestClient(git_server.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        assert isinstance(tool["enabled"], bool)
        assert isinstance(tool["disabled_reason"], str)
