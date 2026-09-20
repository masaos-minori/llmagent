#!/usr/bin/env python3
"""Replace TestLiveCallToolAuthorization class with a clean version."""

filepath = "/home/sugimoto/llmagent/tests/mcp_servers/git/test_git_security_compliance.py"

with open(filepath, "r") as f:
    lines = f.readlines()

# Class spans lines 925-1510 (0-indexed: 924-1509)
class_start = 924  # 0-indexed
class_end = 1510   # 0-indexed (exclusive)

new_class = '''class TestLiveCallToolAuthorization:
    """TestClient-based regression tests for POST /v1/call_tool path.

    Covers checkout/pull/push against protected and non-protected branches,
    including implicit (empty branch) targets — closing the coverage gap where
    all existing tests exercise only the dead-code GitService path.
    """

    @pytest.fixture
    def client(self):
        from scripts.mcp_servers.git.git_server import app

        return TestClient(app)

    @pytest.fixture
    def mock_validate_pre_snapshot(self, monkeypatch):
        from scripts.mcp_servers.git import git_server

        monkeypatch.setattr(
            git_server, "_validate_pre_snapshot", lambda path: (True, "")
        )

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_checkout + branch=main must deny when main is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = ["main"]
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "branch": "main",
                        "create": False,
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "[DENIED]" in str(body.get("result", ""))
            assert "protected branch" in str(body.get("result", "")).lower()
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_checkout_non_protected_branch_allowed(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_checkout + branch=develop must allow when develop is not protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = []
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "branch": "develop",
                        "create": False,
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            # Non-protected branch should not be denied by authorization
            assert "protected branch" not in str(body.get("result", "")).lower()
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_pull_protected_branch_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_pull + branch=master must deny when master is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = ["master"]
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_pull",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "remote": "origin",
                        "branch": "master",
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "[DENIED]" in str(body.get("result", ""))
            assert "protected branch" in str(body.get("result", "")).lower()
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_pull_non_protected_branch_allowed(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_pull + branch=develop must allow when develop is not protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = []
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_pull",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "remote": "origin",
                        "branch": "develop",
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "protected branch" not in str(body.get("result", "")).lower()
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_push_protected_branch_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_push + branch=release must deny when release is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = ["release"]
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_push",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "remote": "origin",
                        "branch": "release",
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "[DENIED]" in str(body.get("result", ""))
            assert "protected branch" in str(body.get("result", "")).lower()
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_push_non_protected_branch_allowed(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_push + branch=develop must allow when develop is not protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = []
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_push",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "remote": "origin",
                        "branch": "develop",
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "protected branch" not in str(body.get("result", "")).lower()
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_checkout_implicit_target_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_checkout + empty branch must deny/resolution (REQ-007)."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = []
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "branch": "",
                        "create": False,
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            # Empty branch should be rejected or resolved to current branch before authorization
            result_str = str(body.get("result", ""))
            assert (
                "protected branch" not in result_str.lower()
                or "branch must not be empty" in result_str.lower()
            )
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_pull_implicit_target_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_pull + empty branch must deny/resolution (REQ-007)."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = []
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_pull",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "remote": "origin",
                        "branch": "",
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            result_str = str(body.get("result", ""))
            assert (
                "protected branch" not in result_str.lower()
                or "branch must not be empty" in result_str.lower()
            )
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_push_implicit_target_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """POST /v1/call_tool with git_push + empty branch must deny/resolution (REQ-007)."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = []
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_push",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "remote": "origin",
                        "branch": "",
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            result_str = str(body.get("result", ""))
            assert (
                "protected branch" not in result_str.lower()
                or "branch must not be empty" in result_str.lower()
            )
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    @pytest.mark.parametrize("branch", ["main", "refs/heads/main"])
    async def test_parametrized_main_vs_refs_heads_main(
        self,
        client,
        branch,
        monkeypatch,
        mock_validate_pre_snapshot,
    ):
        """Parametrized test asserting both main and refs/heads/main deny checkout when main is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg
        from scripts.mcp_servers.git.git_server import _service as server_service

        original_read_only = server_cfg.read_only
        original_svc_read_only = server_service._read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_svc_allowed = server_service._allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_service._read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
            server_service._allowed_repo_paths = ["/tmp/allowed"]
            server_cfg.protected_branches = ["main"]
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": "/tmp/allowed/repo",
                        "branch": branch,
                        "create": False,
                        "dry_run": False,
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            result_str = str(body.get("result", ""))
            assert "[DENIED]" in result_str
            assert "protected branch" in result_str.lower()
        finally:
            server_cfg.read_only = original_read_only
            server_service._read_only = original_svc_read_only
            server_cfg.allowed_repo_paths = original_allowed
            server_service._allowed_repo_paths = original_svc_allowed
            server_cfg.protected_branches = original_protected

'''

# Replace the class
new_lines = lines[:class_start] + [new_class] + lines[class_end:]

with open(filepath, "w") as f:
    f.writelines(new_lines)

print("Done")
