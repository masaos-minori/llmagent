"""tests/test_call_tool_validation.py

Disabled-tool gate + validate_args coverage for POST /v1/call_tool on
file-read/write/delete and git servers.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestFileReadCallToolDisabledGate:
    def test_disabled_when_allowed_dirs_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import read_server
        from mcp_servers.file.read_models import FileReadConfig

        monkeypatch.setattr(read_server, "_cfg", FileReadConfig(allowed_dirs=[]))
        client = TestClient(read_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "list_directory", "args": {"path": "/tmp"}}
        )
        data = resp.json()
        assert data["is_error"] is True
        assert data["result"] == "Tool disabled: allowed_dirs is empty"

    def test_dispatch_not_reached_when_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import read_server
        from mcp_servers.file.read_models import FileReadConfig

        def _spy(name: str, args: object) -> None:
            raise AssertionError("dispatch must not be called for a disabled tool")

        monkeypatch.setattr(read_server, "_cfg", FileReadConfig(allowed_dirs=[]))
        monkeypatch.setattr(read_server, "_dispatch_read_tool", _spy)
        client = TestClient(read_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "list_directory", "args": {"path": "/tmp"}}
        )
        data = resp.json()
        assert data["is_error"] is True

    def test_enabled_with_nonempty_allowed_dirs_does_not_get_disabled_gate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import read_server
        from mcp_servers.file.read_models import FileReadConfig

        monkeypatch.setattr(read_server, "_cfg", FileReadConfig(allowed_dirs=["/tmp"]))
        client = TestClient(read_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "list_directory", "args": {"path": "/tmp"}}
        )
        data = resp.json()
        assert "Tool disabled" not in data.get("result", "")


class TestFileWriteCallToolDisabledGate:
    def test_disabled_when_allowed_dirs_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import write_server
        from mcp_servers.file.write_models import FileWriteConfig

        monkeypatch.setattr(write_server, "_cfg", FileWriteConfig(allowed_dirs=[]))
        client = TestClient(write_server.app)
        resp = client.post(
            "/v1/call_tool",
            json={"name": "write_file", "args": {"path": "/tmp/x", "content": ""}},
        )
        data = resp.json()
        assert data["is_error"] is True
        assert data["result"] == "Tool disabled: allowed_dirs is empty"

    def test_dispatch_not_reached_when_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import write_server
        from mcp_servers.file.write_models import FileWriteConfig

        def _spy(name: str, args: object) -> None:
            raise AssertionError("dispatch must not be called for a disabled tool")

        monkeypatch.setattr(write_server, "_cfg", FileWriteConfig(allowed_dirs=[]))
        monkeypatch.setattr(write_server, "_dispatch_write_tool", _spy)
        client = TestClient(write_server.app)
        resp = client.post(
            "/v1/call_tool",
            json={"name": "write_file", "args": {"path": "/tmp/x", "content": ""}},
        )
        data = resp.json()
        assert data["is_error"] is True

    def test_enabled_with_nonempty_allowed_dirs_does_not_get_disabled_gate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import write_server
        from mcp_servers.file.write_models import FileWriteConfig

        monkeypatch.setattr(
            write_server, "_cfg", FileWriteConfig(allowed_dirs=["/tmp"])
        )
        client = TestClient(write_server.app)
        resp = client.post(
            "/v1/call_tool",
            json={"name": "write_file", "args": {"path": "/tmp/x", "content": ""}},
        )
        data = resp.json()
        assert "Tool disabled" not in data.get("result", "")


class TestFileDeleteCallToolDisabledGate:
    def test_disabled_when_allowed_dirs_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import delete_server
        from mcp_servers.file.delete_models import FileDeleteConfig

        monkeypatch.setattr(delete_server, "_cfg", FileDeleteConfig(allowed_dirs=[]))
        client = TestClient(delete_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "delete_file", "args": {"path": "/tmp/x"}}
        )
        data = resp.json()
        assert data["is_error"] is True
        assert data["result"] == "Tool disabled: allowed_dirs is empty"

    def test_dispatch_not_reached_when_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import delete_server
        from mcp_servers.file.delete_models import FileDeleteConfig

        def _spy(name: str, args: object) -> None:
            raise AssertionError("dispatch must not be called for a disabled tool")

        monkeypatch.setattr(delete_server, "_cfg", FileDeleteConfig(allowed_dirs=[]))
        monkeypatch.setattr(delete_server, "_dispatch_delete_tool", _spy)
        client = TestClient(delete_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "delete_file", "args": {"path": "/tmp/x"}}
        )
        data = resp.json()
        assert data["is_error"] is True

    def test_enabled_with_nonempty_allowed_dirs_does_not_get_disabled_gate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.file import delete_server
        from mcp_servers.file.delete_models import FileDeleteConfig

        monkeypatch.setattr(
            delete_server, "_cfg", FileDeleteConfig(allowed_dirs=["/tmp"])
        )
        client = TestClient(delete_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "delete_file", "args": {"path": "/tmp/x"}}
        )
        data = resp.json()
        assert "Tool disabled" not in data.get("result", "")


class TestGitCallToolDisabledGate:
    def test_disabled_when_repo_paths_empty_even_if_read_only_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.git import server as git_server
        from mcp_servers.git.models import GitConfig

        monkeypatch.setattr(
            git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=False)
        )
        client = TestClient(git_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "git_status", "args": {"repo_path": "/tmp"}}
        )
        data = resp.json()
        assert data["is_error"] is True
        assert data["result"] == "Tool disabled: allowed_repo_paths is empty"

    def test_disabled_when_repo_paths_empty_and_read_only_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.git import server as git_server
        from mcp_servers.git.models import GitConfig

        monkeypatch.setattr(
            git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=True)
        )
        client = TestClient(git_server.app)
        resp = client.post(
            "/v1/call_tool",
            json={"name": "git_commit", "args": {"repo_path": "/tmp", "message": "x"}},
        )
        data = resp.json()
        assert data["is_error"] is True
        assert data["result"] == "Tool disabled: allowed_repo_paths is empty"

    def test_write_tool_disabled_when_read_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.git import server as git_server
        from mcp_servers.git.models import GitConfig

        monkeypatch.setattr(
            git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=True)
        )
        client = TestClient(git_server.app)
        resp = client.post(
            "/v1/call_tool",
            json={"name": "git_commit", "args": {"repo_path": "/tmp", "message": "x"}},
        )
        data = resp.json()
        assert data["is_error"] is True
        assert data["result"] == "Tool disabled: read_only=true"

    def test_read_tool_not_disabled_when_read_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.git import server as git_server
        from mcp_servers.git.models import GitConfig

        monkeypatch.setattr(
            git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=True)
        )
        client = TestClient(git_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "git_status", "args": {"repo_path": "/tmp"}}
        )
        data = resp.json()
        assert "Tool disabled:" not in data.get("result", "")

    def test_enabled_with_nonempty_repo_paths_and_read_only_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from mcp_servers.git import server as git_server
        from mcp_servers.git.models import GitConfig

        monkeypatch.setattr(
            git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=False)
        )
        client = TestClient(git_server.app)
        resp = client.post(
            "/v1/call_tool",
            json={"name": "git_commit", "args": {"repo_path": "/tmp", "message": "x"}},
        )
        data = resp.json()
        assert "Tool disabled:" not in data.get("result", "")
