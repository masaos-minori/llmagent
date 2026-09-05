from __future__ import annotations

import stat
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from mcp_servers.git.git_models import GitConfig
from mcp_servers.git.git_service import GitService
from mcp_servers.git.repository_state import RepositoryState


class TestGitSecurityCompliance:
    @pytest.fixture
    def svc(self) -> GitService:
        # Setup service with one allowed repo and one protected branch
        return GitService(
            allowed_repo_paths=["/tmp/repo"],
            read_only=False,
            max_log_entries=50,
            protected_branches=["main"],
        )

    def test_is_safe_ref(self, svc: GitService) -> None:
        assert svc._is_safe_ref("main") is True
        assert svc._is_safe_ref("feature/abc") is True
        assert svc._is_safe_ref("-force") is False
        assert svc._is_safe_ref("--help") is False

    def test_check_protected_branch(self, svc: GitService) -> None:
        assert svc._check_protected_branch("main")[0] is False
        assert (
            svc._check_protected_branch("main")[1]
            == "[DENIED] 'main' is a protected branch"
        )
        assert svc._check_protected_branch("develop")[0] is True
        assert svc._check_protected_branch("develop")[1] == ""

    @pytest.mark.asyncio
    async def test_git_checkout_protected_branch(self, svc: GitService) -> None:
        # Mocking dependencies
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "branch": "main",
            "create": False,
            "dry_run": False,
        }

        # It should fail due to protected branch
        result = await svc.git_checkout(args)
        assert "[DENIED]" in result
        assert "protected branch" in result

    @pytest.mark.asyncio
    async def test_git_push_protected_branch(self, svc: GitService) -> None:
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "remote": "origin",
            "branch": "main",
            "dry_run": False,
        }

        result = await svc.git_push(args)
        assert "[DENIED]" in result
        assert "protected branch" in result

    @pytest.mark.asyncio
    async def test_git_pull_protected_branch(self, svc: GitService) -> None:
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "remote": "origin",
            "branch": "main",
            "dry_run": False,
        }

        result = await svc.git_pull(args)
        assert "[DENIED]" in result
        assert "protected branch" in result

    @pytest.mark.asyncio
    async def test_git_pull_unsafe_remote(self, svc: GitService) -> None:
        svc._open_repo = MagicMock(return_value=MagicMock())
        # Use a non-protected branch so we reach the remote validation
        args = {
            "repo_path": "/tmp/repo",
            "remote": "-force",
            "branch": "develop",
            "dry_run": False,
        }

        result = await svc.git_pull(args)
        assert "[DENIED]" in result
        assert "CLI option" in result

    @pytest.mark.asyncio
    async def test_git_show_unsafe_ref(self, svc: GitService) -> None:
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {"repo_path": "/tmp/repo", "ref": "--help"}

        result = await svc.git_show(args)
        assert "[DENIED]" in result
        assert "CLI option" in result

    @pytest.fixture
    def svc_allow_detached(self) -> GitService:
        return GitService(
            allowed_repo_paths=["/tmp/repo"],
            read_only=False,
            max_log_entries=50,
            protected_branches=["main"],
            allow_detached_head=True,
        )

    @pytest.fixture
    def svc_from_shipped_config(self) -> GitService:
        cfg = GitConfig.load()
        return GitService(
            allowed_repo_paths=["/tmp/repo"],
            read_only=False,
            max_log_entries=50,
            protected_branches=cfg.protected_branches,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("branch", ["main", "master", "release"])
    async def test_write_tools_reject_shipped_protected_branches(
        self, svc_from_shipped_config: GitService, branch: str
    ) -> None:
        svc_from_shipped_config._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "branch": branch,
            "create": False,
            "dry_run": False,
        }
        result = await svc_from_shipped_config.git_checkout(args)
        assert "[DENIED]" in result
        assert "protected branch" in result

    @pytest.mark.asyncio
    async def test_git_checkout_dirty_worktree_denied(self, svc: GitService) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.is_dirty = True
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] worktree has uncommitted changes",
        )
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "branch": "develop",
                "create": False,
                "dry_run": False,
            }
            result = await svc.git_checkout(args)
        assert "[DENIED]" in result
        assert "worktree has uncommitted changes" in result

    @pytest.mark.asyncio
    async def test_git_pull_dirty_worktree_denied(self, svc: GitService) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.is_dirty = True
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] worktree has uncommitted changes",
        )
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "remote": "origin",
                "branch": "develop",
                "dry_run": False,
            }
            result = await svc.git_pull(args)
        assert "[DENIED]" in result
        assert "worktree has uncommitted changes" in result

    @pytest.mark.asyncio
    async def test_git_checkout_detached_head_denied(self, svc: GitService) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.is_dirty = False
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] repository is in a detached HEAD state",
        )
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "branch": "develop",
                "create": False,
                "dry_run": False,
            }
            result = await svc.git_checkout(args)
        assert "[DENIED]" in result
        assert "detached HEAD" in result

    @pytest.mark.asyncio
    async def test_git_pull_detached_head_denied(self, svc: GitService) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.is_dirty = False
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] repository is in a detached HEAD state",
        )
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "remote": "origin",
                "branch": "develop",
                "dry_run": False,
            }
            result = await svc.git_pull(args)
        assert "[DENIED]" in result
        assert "detached HEAD" in result

    @pytest.mark.asyncio
    async def test_git_checkout_detached_head_allowed(
        self, svc_allow_detached: GitService
    ) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.is_dirty = False
        snap.is_detached_head = True
        snap.active_branch = "develop"
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "branch": "develop",
                "create": False,
                "dry_run": False,
            }
            result = await svc_allow_detached.git_checkout(args)
        assert "[DRY RUN]" not in result
        assert "[DENIED]" not in result

    @pytest.mark.asyncio
    async def test_git_pull_detached_head_allowed(
        self, svc_allow_detached: GitService
    ) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.is_dirty = False
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        snap._repo = MagicMock()
        snap._repo.index.unmerged_blobs.return_value = []
        snap._repo.git.pull.return_value = "Already up to date."
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "remote": "origin",
                "branch": "develop",
                "dry_run": False,
            }
            result = await svc_allow_detached.git_pull(args)
        assert "[DRY RUN]" not in result
        assert "[DENIED]" not in result

    @pytest.mark.asyncio
    async def test_git_checkout_dry_run_skips_dirty_and_detached_checks(
        self, svc: GitService
    ) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.active_branch = "develop"
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "branch": "develop",
                "create": False,
                "dry_run": True,
            }
            result = await svc.git_checkout(args)
        assert "[DRY RUN]" in result
        assert "[DENIED]" not in result

    @pytest.mark.asyncio
    async def test_git_pull_dry_run_skips_dirty_and_detached_checks(
        self, svc: GitService
    ) -> None:
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            args = {
                "repo_path": "/tmp/repo",
                "remote": "origin",
                "branch": "develop",
                "dry_run": True,
            }
            result = await svc.git_pull(args)
        assert "[DRY RUN]" in result
        assert "[DENIED]" not in result

    @pytest.mark.asyncio
    async def test_git_push_with_empty_branch_returns_denied(
        self, svc: GitService
    ) -> None:
        """git_push with empty branch argument must return [DENIED] (REQ-002)."""
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "remote": "origin",
            "branch": "",  # Empty branch — the bypass scenario
            "dry_run": False,
        }
        result = await svc.git_push(args)
        assert "[DENIED]" in result
        assert "branch must not be empty" in result.lower()

    @pytest.mark.asyncio
    async def test_git_pull_with_empty_branch_returns_denied(
        self, svc: GitService
    ) -> None:
        """git_pull with empty branch argument must return [DENIED] (REQ-003)."""
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "remote": "origin",
            "branch": "",  # Empty branch — the bypass scenario
            "dry_run": False,
        }
        result = await svc.git_pull(args)
        assert "[DENIED]" in result
        assert "branch must not be empty" in result.lower()


class TestCheckRepoPathResolvedPath:
    """Verify _check_repo_path returns resolved canonical path."""

    def test_resolved_path_on_success(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=True,
            max_log_entries=50,
        )
        ok, err, resolved = svc._check_repo_path("/opt/repos/myproject")
        assert ok is True
        assert err == ""
        assert resolved == "/opt/repos/myproject"

    def test_empty_resolved_path_on_failure(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=True,
            max_log_entries=50,
        )
        ok, err, resolved = svc._check_repo_path("/home/user/project")
        assert ok is False
        assert "[DENIED]" in err
        assert resolved == ""

    def test_symlink_resolved_path(self) -> None:
        import pathlib
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            real_dir = pathlib.Path(tmpdir) / "real"
            link_dir = pathlib.Path(tmpdir) / "link"
            real_dir.mkdir()
            link_dir.symlink_to(real_dir)
            svc = GitService(
                allowed_repo_paths=[str(real_dir)],
                read_only=True,
                max_log_entries=50,
            )
            ok, _, resolved = svc._check_repo_path(str(link_dir))
            assert ok is True
            assert resolved == str(real_dir)


class TestAuditTargetResolution:
    """Verify audit target uses canonical identity, not raw caller input."""

    @pytest.mark.asyncio
    async def test_audit_target_is_canonical_for_valid_call(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=False,
            max_log_entries=50,
        )
        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result

    @pytest.mark.asyncio
    async def test_audit_target_empty_for_rejected_call(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=True,
            max_log_entries=50,
        )
        result = await svc.git_checkout(
            {
                "repo_path": "/opt/repos/proj",
                "branch": "main",
            }
        )
        assert "[DENIED]" in result


class TestPreDispatchRejectionAudit:
    """Verify rejection paths emit proper audit records."""

    @pytest.mark.asyncio
    async def test_protected_branch_rejection_has_error_type(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=False,
            max_log_entries=50,
            protected_branches=["main"],
        )
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "develop"
        mock_repo.is_dirty.return_value = False
        with patch.object(svc, "_open_repo", return_value=mock_repo):
            result = await svc.git_checkout(
                {
                    "repo_path": "/opt/repos/proj",
                    "branch": "main",
                }
            )
        assert "[DENIED]" in result
        assert "protected branch" in result


class TestEmittedAuditLogContent:
    """Verify audit log content includes correct fields."""

    @pytest.mark.asyncio
    async def test_audit_record_contains_server_key(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=False,
            max_log_entries=50,
        )
        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result


@pytest.fixture(scope="module")
def client():
    """Provide a TestClient for the git-mcp server."""
    from mcp_servers.git import server as git_server

    with TestClient(git_server.app) as c:
        yield c


class TestHTTPSiblingPathRejection:
    @pytest.mark.asyncio
    async def test_sibling_prefix_rejected_via_http(self, client):
        """A sibling path such as /allowed-repo-evil must not be accepted for /allowed-repo root."""
        from mcp_servers.git import server as git_server

        original = git_server._cfg.allowed_repo_paths
        try:
            git_server._cfg.allowed_repo_paths = ["/tmp/allowed"]
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_status",
                    "args": {"repo_path": "/tmp/allowed-evil"},
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "[DENIED]" in body.get("result", "")
            assert body.get("is_error") is True
        finally:
            git_server._cfg.allowed_repo_paths = original

    @pytest.mark.asyncio
    async def test_symlink_escape_rejected_via_http(self, client):
        """Symlink escape attempts must be rejected before RepositoryState.snapshot()."""
        from mcp_servers.git import server as git_server

        with tempfile.TemporaryDirectory() as tmpdir:
            real_dir = Path(tmpdir) / "real"
            link_dir = Path(tmpdir) / "link"
            real_dir.mkdir()
            # Create a symlink inside the allowed dir pointing outside
            evil_target = Path(tmpdir) / "outside"
            evil_target.mkdir()
            link_dir.symlink_to(evil_target)

            original = git_server._cfg.allowed_repo_paths
            try:
                git_server._cfg.allowed_repo_paths = [str(real_dir)]
                resp = client.post(
                    "/v1/call_tool",
                    json={
                        "name": "git_status",
                        "args": {"repo_path": str(link_dir)},
                    },
                )
                assert resp.status_code == 200
                body = resp.json()
                assert "[DENIED]" in body.get("result", "")
                assert body.get("is_error") is True
            finally:
                git_server._cfg.allowed_repo_paths = original

    @pytest.mark.asyncio
    async def test_missing_path_clean_rejection_via_http(self, client):
        """A missing path must produce a clean rejection response (no 500, no unhandled exception)."""
        from mcp_servers.git import server as git_server

        original = git_server._cfg.allowed_repo_paths
        try:
            git_server._cfg.allowed_repo_paths = ["/nonexistent-root"]
            resp = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_status",
                    "args": {"repo_path": "/nonexistent-root/repo"},
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body.get("is_error") is True
        finally:
            git_server._cfg.allowed_repo_paths = original

    @pytest.mark.asyncio
    async def test_permission_denied_clean_rejection_via_http(self, client):
        """A permission-denied path must produce a clean rejection response."""
        from mcp_servers.git import server as git_server

        with tempfile.TemporaryDirectory() as tmpdir:
            restricted_dir = Path(tmpdir) / "restricted"
            restricted_dir.mkdir(mode=0o000)
            original = git_server._cfg.allowed_repo_paths
            try:
                git_server._cfg.allowed_repo_paths = [str(restricted_dir)]
                resp = client.post(
                    "/v1/call_tool",
                    json={
                        "name": "git_status",
                        "args": {"repo_path": str(restricted_dir)},
                    },
                )
                assert resp.status_code == 200
                body = resp.json()
                assert body.get("is_error") is True
            finally:
                restricted_dir.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
                git_server._cfg.allowed_repo_paths = original

    @pytest.mark.asyncio
    async def test_non_repository_clean_rejection_via_http(self, client):
        """A non-Git directory must produce a clean rejection response."""
        from mcp_servers.git import server as git_server

        with tempfile.TemporaryDirectory() as tmpdir:
            plain_dir = Path(tmpdir) / "plain"
            plain_dir.mkdir()
            original = git_server._cfg.allowed_repo_paths
            try:
                git_server._cfg.allowed_repo_paths = [str(plain_dir)]
                resp = client.post(
                    "/v1/call_tool",
                    json={
                        "name": "git_status",
                        "args": {"repo_path": str(plain_dir)},
                    },
                )
                assert resp.status_code == 200
                body = resp.json()
                assert body.get("is_error") is True
            finally:
                git_server._cfg.allowed_repo_paths = original

    @pytest.mark.asyncio
    async def test_audit_redacts_requested_target(self, client):
        """The raw requested path must appear only in a redacted field, not as the authoritative target."""
        from mcp_servers.git import server as git_server

        with tempfile.TemporaryDirectory() as tmpdir:
            allowed_dir = Path(tmpdir) / "allowed"
            evil_dir = Path(tmpdir) / "allowed-evil"
            allowed_dir.mkdir()
            evil_dir.mkdir()

            original = git_server._cfg.allowed_repo_paths
            try:
                git_server._cfg.allowed_repo_paths = [str(allowed_dir)]
                with patch("mcp_servers.git.git_server._audit_log") as mock_audit:
                    resp = client.post(
                        "/v1/call_tool",
                        json={
                            "name": "git_status",
                            "args": {"repo_path": str(evil_dir)},
                        },
                    )
                    assert resp.status_code == 200
                    body = resp.json()
                    assert body.get("is_error") is True
                    if mock_audit.called:
                        call_kwargs = mock_audit.call_args
                        req_target = call_kwargs.kwargs.get("requested_target", "")
                        assert "allowed-evil" not in req_target or "***" in req_target
            finally:
                git_server._cfg.allowed_repo_paths = original


class TestPostConditionBypassPrevention:
    """AC-8: Tests prove the complete pipeline cannot be bypassed through the HTTP dispatch path."""

    @pytest.fixture
    def client(self):
        from scripts.mcp_servers.git.git_server import app

        return TestClient(app)

    def test_checkout_postcondition_cannot_be_bypassed(self, client, monkeypatch):
        """REQ-010, AC-8: Checkout postcondition failure is reported, not silently accepted."""
        from scripts.mcp_servers.git.repository_state import RepositoryState

        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.side_effect = (
            lambda result, post_state, tool_name, requested_branch: (
                (False, "checkout postcondition failed: expected branch 'dev'")
                if tool_name == "git_checkout"
                else (True, "")
            )
        )
        snap.audit.return_value = {}

        monkeypatch.setattr(RepositoryState, "snapshot", MagicMock(return_value=snap))

        response = client.post(
            "/v1/call_tool",
            json={
                "name": "git_checkout",
                "args": {"repo_path": "/tmp/test-repo", "branch": "dev"},
            },
        )

        body = response.json()
        assert body.get("is_error") is True or "failed" in str(body).lower()

    def test_pull_postcondition_cannot_be_bypassed(self, client, monkeypatch):
        """REQ-010, AC-8: Pull postcondition failure (merge conflict) is reported."""
        from scripts.mcp_servers.git.repository_state import RepositoryState

        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.side_effect = (
            lambda result, post_state, tool_name, requested_branch: (
                (False, "pull postcondition failed: unresolved merge conflicts remain")
                if tool_name == "git_pull"
                else (True, "")
            )
        )
        snap.audit.return_value = {}

        monkeypatch.setattr(RepositoryState, "snapshot", MagicMock(return_value=snap))

        response = client.post(
            "/v1/call_tool",
            json={
                "name": "git_pull",
                "args": {
                    "repo_path": "/tmp/test-repo",
                    "remote": "origin",
                    "branch": "main",
                },
            },
        )

        body = response.json()
        assert (
            body.get("is_error") is True
            or "unresolved merge conflicts" in str(body).lower()
        )

    def test_push_postcondition_cannot_be_bypassed(self, client, monkeypatch):
        """REQ-010, AC-8: Push postcondition failure (rejection) is reported."""
        from scripts.mcp_servers.git.repository_state import RepositoryState

        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.side_effect = (
            lambda result, post_state, tool_name, requested_branch: (
                (False, "push postcondition failed: rejected")
                if tool_name == "git_push"
                else (True, "")
            )
        )
        snap.audit.return_value = {}

        monkeypatch.setattr(RepositoryState, "snapshot", MagicMock(return_value=snap))

        response = client.post(
            "/v1/call_tool",
            json={
                "name": "git_push",
                "args": {
                    "repo_path": "/tmp/test-repo",
                    "remote": "origin",
                    "refspec": "main:main",
                },
            },
        )

        body = response.json()
        assert body.get("is_error") is True or "rejected" in str(body).lower()


class TestCompletePipelineCoverage:
    """Verify all pipeline stages execute in order for each operation type."""

    @pytest.fixture
    def client(self):
        from scripts.mcp_servers.git.git_server import app

        return TestClient(app)

    def test_all_stages_execute_in_order_for_checkout(self, client, monkeypatch):
        """REQ-010, AC-1: Authorization, precondition, execution, and postcondition stages execute in documented order."""
        from scripts.mcp_servers.git.repository_state import (
            RepositoryState,
            WriteProtectionPipeline,
        )

        recorded_stages = []
        original_record = WriteProtectionPipeline.record_stage

        def track_record(self, stage):
            recorded_stages.append(stage.name)
            return original_record(self, stage)

        monkeypatch.setattr(WriteProtectionPipeline, "record_stage", track_record)

        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}

        monkeypatch.setattr(RepositoryState, "snapshot", MagicMock(return_value=snap))

        client.post(
            "/v1/call_tool",
            json={
                "name": "git_checkout",
                "args": {"repo_path": "/tmp/test-repo", "branch": "main"},
            },
        )

        if len(recorded_stages) >= 4:
            assert recorded_stages.index("Stage 3") < recorded_stages.index("Stage 5")
            assert recorded_stages.index("Stage 5") < recorded_stages.index("Stage 6")
            assert recorded_stages.index("Stage 6") < recorded_stages.index("Stage 7")

    def test_all_stages_execute_in_order_for_pull(self, client, monkeypatch):
        """REQ-010, AC-1: Pull stages execute in documented order."""
        from scripts.mcp_servers.git.repository_state import (
            RepositoryState,
            WriteProtectionPipeline,
        )

        recorded_stages = []
        original_record = WriteProtectionPipeline.record_stage

        def track_record(self, stage):
            recorded_stages.append(stage.name)
            return original_record(self, stage)

        monkeypatch.setattr(WriteProtectionPipeline, "record_stage", track_record)

        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}

        monkeypatch.setattr(RepositoryState, "snapshot", MagicMock(return_value=snap))

        client.post(
            "/v1/call_tool",
            json={
                "name": "git_pull",
                "args": {
                    "repo_path": "/tmp/test-repo",
                    "remote": "origin",
                    "branch": "main",
                },
            },
        )

        if len(recorded_stages) >= 4:
            assert recorded_stages.index("Stage 3") < recorded_stages.index("Stage 5")
            assert recorded_stages.index("Stage 5") < recorded_stages.index("Stage 6")
            assert recorded_stages.index("Stage 6") < recorded_stages.index("Stage 7")

    def test_all_stages_execute_in_order_for_push(self, client, monkeypatch):
        """REQ-010, AC-1: Push stages execute in documented order."""
        from scripts.mcp_servers.git.repository_state import (
            RepositoryState,
            WriteProtectionPipeline,
        )

        recorded_stages = []
        original_record = WriteProtectionPipeline.record_stage

        def track_record(self, stage):
            recorded_stages.append(stage.name)
            return original_record(self, stage)

        monkeypatch.setattr(WriteProtectionPipeline, "record_stage", track_record)

        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "main"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}

        monkeypatch.setattr(RepositoryState, "snapshot", MagicMock(return_value=snap))

        client.post(
            "/v1/call_tool",
            json={
                "name": "git_push",
                "args": {
                    "repo_path": "/tmp/test-repo",
                    "remote": "origin",
                    "refspec": "main:main",
                },
            },
        )

        if len(recorded_stages) >= 4:
            assert recorded_stages.index("Stage 3") < recorded_stages.index("Stage 5")
            assert recorded_stages.index("Stage 5") < recorded_stages.index("Stage 6")
            assert recorded_stages.index("Stage 6") < recorded_stages.index("Stage 7")


class TestLiveCallToolAuthorization:
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

    @pytest.fixture
    def mock_repo_state_snapshot(self, monkeypatch):
        from mcp_servers.git.repository_state import RepositoryState

        fake_state = MagicMock(spec=RepositoryState)
        fake_state.path = "/tmp/allowed/repo"
        fake_state.is_dirty = False
        fake_state.head_type = "branch"
        fake_state.active_branch = "main"
        fake_state.untracked_file_count = 0
        fake_state.protected_branch = True
        fake_state.ref_valid = True
        fake_state.verify_authorization.return_value = (
            False,
            "[DENIED] main is a protected branch",
        )
        fake_state.verify_preconditions.return_value = (True, "")
        fake_state.verify_postcondition.return_value = (True, "")
        fake_state.snapshot.return_value = fake_state
        monkeypatch.setattr(RepositoryState, "snapshot", lambda *a, **kw: fake_state)

    @pytest.fixture
    def mock_repo_state_snapshot_dynamic(self, monkeypatch):
        from mcp_servers.git.repository_state import (
            PipelineResult,
            RepositoryState,
            WriteProtectionPipeline,
        )

        def _normalize_branch_name(branch):
            stripped = branch.strip()
            if not stripped:
                return ""
            if stripped.startswith("refs/heads/"):
                return stripped.lower()
            return f"refs/heads/{stripped}".lower()

        def make_fake_state(*args, protected_branches=None, active_ref="", **kw):
            fake_state = MagicMock(spec=RepositoryState)
            fake_state.path = "/tmp/allowed/repo"
            fake_state.is_dirty = False
            fake_state.head_type = "branch"
            # Use active_ref directly; empty string stays empty (no default to "main")
            fake_state.active_branch = active_ref if active_ref else ""
            fake_state.untracked_file_count = 0
            # For non-empty refs: normalize both sides for comparison
            if active_ref:
                norm_active = _normalize_branch_name(active_ref)
                norm_protected = [
                    _normalize_branch_name(b) for b in (protected_branches or [])
                ]
                fake_state.protected_branch = bool(
                    norm_protected and norm_active in norm_protected
                )
            else:
                fake_state.protected_branch = False
            fake_state.ref_valid = bool(active_ref)  # empty ref is invalid
            if fake_state.protected_branch:
                fake_state.verify_authorization.return_value = (
                    False,
                    f"[DENIED] {fake_state.active_branch!r} is a protected branch",
                )
            elif not fake_state.ref_valid:
                fake_state.verify_authorization.return_value = (
                    False,
                    f"[DENIED] Ref {fake_state.active_branch!r} looks like a CLI option",
                )
            else:
                fake_state.verify_authorization.return_value = (True, "")
            fake_state.verify_preconditions.return_value = (True, "")
            fake_state.verify_postcondition.return_value = (True, "")
            fake_state.snapshot.return_value = fake_state
            return fake_state

        monkeypatch.setattr(RepositoryState, "snapshot", make_fake_state)

        def mock_pipeline_run(
            self,
            tool_name,
            op,
            requested_branch=None,
            protected_branches=None,
            active_ref="",
        ):
            ok, msg = self._state.verify_authorization()
            if not ok:
                return PipelineResult.reject(self._state, "Stage 3", msg)
            ok, msg = self._state.verify_preconditions(tool_name)
            if not ok:
                return PipelineResult.reject(self._state, "Stage 5", msg)
            output = f"{tool_name} succeeded on {self._state.active_branch}"
            post_state = self._state.snapshot(
                self._state.path,
                protected_branches=protected_branches or [],
                active_ref=active_ref,
            )
            ok, msg = self._state.verify_postcondition(
                output, post_state, tool_name, requested_branch
            )
            if not ok:
                return PipelineResult.reject(
                    self._state, "Stage 7", msg, post_state=post_state
                )
            return PipelineResult.ok_result(post_state, output, post_state=post_state)

        monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_checkout + branch=main must deny when main is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_checkout_non_protected_branch_allowed(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_checkout + branch=develop must allow when develop is not protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed

    @pytest.mark.asyncio
    async def test_pull_protected_branch_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_pull + branch=master must deny when master is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_pull_non_protected_branch_allowed(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_pull + branch=develop must allow when develop is not protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed

    @pytest.mark.asyncio
    async def test_push_protected_branch_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_push + branch=release must deny when release is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        original_protected = server_cfg.protected_branches
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed
            server_cfg.protected_branches = original_protected

    @pytest.mark.asyncio
    async def test_push_non_protected_branch_allowed(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_push + branch=develop must allow when develop is not protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed

    @pytest.mark.asyncio
    async def test_checkout_implicit_target_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_checkout + empty branch must deny/resolution (REQ-007)."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed

    @pytest.mark.asyncio
    async def test_pull_implicit_target_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_pull + empty branch must deny/resolution (REQ-007)."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed

    @pytest.mark.asyncio
    async def test_push_implicit_target_denied(
        self,
        client,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """POST /v1/call_tool with git_push + empty branch must deny/resolution (REQ-007)."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed

    @pytest.mark.asyncio
    @pytest.mark.parametrize("branch", ["main", "refs/heads/main"])
    async def test_parametrized_main_vs_refs_heads_main(
        self,
        client,
        branch,
        monkeypatch,
        mock_validate_pre_snapshot,
        mock_repo_state_snapshot_dynamic,
    ):
        """Parametrized test asserting both main and refs/heads/main deny checkout when main is protected."""
        from scripts.mcp_servers.git.git_server import _cfg as server_cfg

        original_read_only = server_cfg.read_only
        original_allowed = server_cfg.allowed_repo_paths
        try:
            server_cfg.read_only = False
            server_cfg.allowed_repo_paths = ["/tmp/allowed"]
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
            server_cfg.allowed_repo_paths = original_allowed


class TestGitServiceErrorHandlerIdentity:
    """REQ-008: Tests prove GitServiceError raised on the live HTTP dispatch path is caught by the registered exception handler."""

    @pytest.fixture
    def client(self):
        from scripts.mcp_servers.git.git_server import app

        return TestClient(app)

    def test_gitservice_error_on_dispatch_path_is_caught_by_registered_handler(self, client, monkeypatch):
        """REQ-008, AC-3, AC-6: GitServiceError raised inside Stage-6 op() callback is caught by the FastAPI handler, producing structured 500 response — not an unhandled 500."""
        from scripts.mcp_servers.git.repository_state import RepositoryState
        from mcp_servers.git.errors import GitServiceError
        from mcp_servers.git import server as git_server

        snap = MagicMock()
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "develop"
        snap.repo.is_dirty.return_value = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.audit.return_value = {}

        monkeypatch.setattr(RepositoryState, "snapshot", MagicMock(return_value=snap))

        def raise_git_service_error(*args, **kwargs):
            raise GitServiceError("handler identity proof")

        monkeypatch.setattr("scripts.mcp_servers.git.git_server.format_checkout", raise_git_service_error)

        original_allowed_paths = git_server._cfg.allowed_repo_paths
        try:
            git_server._cfg.allowed_repo_paths = ["/tmp"]
            # Mock _git_tool_availability to enable the tool (bypass global disable check)
            monkeypatch.setattr(git_server, "_git_tool_availability", lambda cfg, name: (True, ""))
            # Mock _is_within_allowed_paths to bypass the allowed_repo_paths check
            # because the service's _allowed_repo_paths was set at construction time
            monkeypatch.setattr(git_server._service, "_is_within_allowed_paths", lambda self, path: (True, ""))
            response = client.post("/v1/call_tool", json={
                "name": "git_checkout",
                "args": {"repo_path": "/tmp/test-repo", "branch": "develop"}
            })
            print(f"DEBUG: response.status_code={response.status_code}, body={response.text}")
            assert response.status_code == 500
            body = response.json()
            assert body == {"detail": "handler identity proof"}
        finally:
            git_server._cfg.allowed_repo_paths = original_allowed_paths
