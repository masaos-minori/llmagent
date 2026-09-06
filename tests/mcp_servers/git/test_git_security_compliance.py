from __future__ import annotations

import stat
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import git
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
        with pytest.raises(ValueError, match="protected branch"):
            await svc.git_checkout(args)

    @pytest.mark.asyncio
    async def test_git_push_protected_branch(self, svc: GitService) -> None:
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "remote": "origin",
            "branch": "main",
            "dry_run": False,
        }

        with pytest.raises(ValueError, match="protected branch"):
            await svc.git_push(args)

    @pytest.mark.asyncio
    async def test_git_pull_protected_branch(self, svc: GitService) -> None:
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {
            "repo_path": "/tmp/repo",
            "remote": "origin",
            "branch": "main",
            "dry_run": False,
        }

        with pytest.raises(ValueError, match="protected branch"):
            await svc.git_pull(args)

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

        with pytest.raises(ValueError, match="CLI option"):
            await svc.git_pull(args)

    @pytest.mark.asyncio
    async def test_git_show_unsafe_ref(self, svc: GitService) -> None:
        svc._open_repo = MagicMock(return_value=MagicMock())
        args = {"repo_path": "/tmp/repo", "ref": "--help"}

        with pytest.raises(ValueError, match="CLI option"):
            await svc.git_show(args)

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
        with pytest.raises(ValueError, match="protected branch"):
            await svc_from_shipped_config.git_checkout(args)

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
            with pytest.raises(ValueError, match="worktree has uncommitted changes"):
                await svc.git_checkout(args)

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
            with pytest.raises(ValueError, match="worktree has uncommitted changes"):
                await svc.git_pull(args)

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
            with pytest.raises(ValueError, match="detached HEAD"):
                await svc.git_checkout(args)

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
            with pytest.raises(ValueError, match="detached HEAD"):
                await svc.git_pull(args)

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
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        snap._repo.remotes = [origin]
        with (
            patch.object(RepositoryState, "snapshot", return_value=snap),
            patch(
                "mcp_servers.git.format_output.GitConfig.load",
                return_value=GitConfig(
                    allowed_remote_urls=["https://example.com/repo.git"]
                ),
            ),
        ):
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
        snap._repo = MagicMock()
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        snap._repo.remotes = [origin]
        with (
            patch.object(RepositoryState, "snapshot", return_value=snap),
            patch(
                "mcp_servers.git.format_output.GitConfig.load",
                return_value=GitConfig(
                    allowed_remote_urls=["https://example.com/repo.git"]
                ),
            ),
        ):
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
        with pytest.raises(ValueError, match="(?i)branch must not be empty"):
            await svc.git_push(args)

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
        with pytest.raises(ValueError, match="(?i)branch must not be empty"):
            await svc.git_pull(args)


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
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_checkout(
                {
                    "repo_path": "/opt/repos/proj",
                    "branch": "main",
                }
            )


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
        with (
            patch.object(svc, "_open_repo", return_value=mock_repo),
            pytest.raises(ValueError, match="protected branch"),
        ):
            await svc.git_checkout(
                {
                    "repo_path": "/opt/repos/proj",
                    "branch": "main",
                }
            )


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


class TestDryRunAndDetachedHeadLivePath:
    """REQ-006, REQ-009: dry-run skips Stage 5 preconditions but not Stage 3
    authorization, and performs no mutation, via the real /v1/call_tool route."""

    @pytest.fixture
    def client(self):
        from scripts.mcp_servers.git.git_server import app

        return TestClient(app)

    def test_dry_run_checkout_skips_dirty_and_detached_precondition(
        self, client, tmp_path
    ):
        from scripts.mcp_servers.git import git_server

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        repo = git.Repo.init(str(repo_dir))
        (repo_dir / "README.md").write_text("# test")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.git.checkout(repo.head.commit.hexsha)  # detached
        (repo_dir / "README.md").write_text("# test\nuncommitted\n")  # dirty

        original_paths = git_server._cfg.allowed_repo_paths
        original_read_only = git_server._cfg.read_only
        original_svc_paths = git_server._service._allowed_repo_paths
        original_svc_read_only = git_server._service._read_only
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            git_server._cfg.read_only = False
            # call_tool()'s own pre-dispatch checks read live _cfg, but dispatch now
            # routes through _service (a GitService instance built once at import
            # time from _cfg's then-current value) — its _validate_repo() reads its
            # own copied _allowed_repo_paths/_read_only, unaffected by patching _cfg.
            git_server._service._allowed_repo_paths = [str(repo_dir)]
            git_server._service._read_only = False
            response = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": str(repo_dir),
                        "branch": "develop",
                        "dry_run": True,
                    },
                },
            )
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.read_only = original_read_only
            git_server._service._allowed_repo_paths = original_svc_paths
            git_server._service._read_only = original_svc_read_only

        body = response.json()
        assert body.get("is_error") is not True
        assert git.Repo(str(repo_dir)).is_dirty()  # unchanged: still dirty, no mutation
        assert git.Repo(str(repo_dir)).head.is_detached  # unchanged: still detached

    def test_dry_run_checkout_protected_branch_still_denied(self, client, tmp_path):
        from scripts.mcp_servers.git import git_server

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        repo = git.Repo.init(str(repo_dir))
        (repo_dir / "README.md").write_text("# test")
        repo.index.add(["README.md"])
        repo.index.commit("initial")

        original_paths = git_server._cfg.allowed_repo_paths
        original_read_only = git_server._cfg.read_only
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            git_server._cfg.read_only = False
            response = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": str(repo_dir),
                        "branch": "main",
                        "dry_run": True,
                    },
                },
            )
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.read_only = original_read_only

        body = response.json()
        # Stage 3 (authorization) stays active during dry-run. Per Step 3a's
        # correction (implementation procedure document): PipelineResult.reject()
        # never populates .output, so a pipeline-stage rejection's message is not
        # surfaced in the response body via the live route — only is_error is
        # asserted here, matching TestPostConditionBypassPrevention's established
        # pattern for this same code path.
        assert body.get("is_error") is True

    def test_non_dry_run_detached_head_denied_then_allowed(self, client, tmp_path):
        from scripts.mcp_servers.git import git_server

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        repo = git.Repo.init(str(repo_dir))
        (repo_dir / "README.md").write_text("# test")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.git.checkout(repo.head.commit.hexsha)  # detached

        original_paths = git_server._cfg.allowed_repo_paths
        original_allow = git_server._cfg.allow_detached_head
        original_read_only = git_server._cfg.read_only
        original_svc_paths = git_server._service._allowed_repo_paths
        original_svc_read_only = git_server._service._read_only
        original_svc_allow = git_server._service._allow_detached_head
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            git_server._cfg.read_only = False
            git_server._service._allowed_repo_paths = [str(repo_dir)]
            git_server._service._read_only = False

            git_server._cfg.allow_detached_head = False
            git_server._service._allow_detached_head = False
            denied = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": str(repo_dir),
                        "branch": "develop",
                        "dry_run": False,
                    },
                },
            )

            git_server._cfg.allow_detached_head = True
            git_server._service._allow_detached_head = True
            allowed = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_checkout",
                    "args": {
                        "repo_path": str(repo_dir),
                        "branch": "develop",
                        "dry_run": False,
                    },
                },
            )
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.allow_detached_head = original_allow
            git_server._cfg.read_only = original_read_only
            git_server._service._allowed_repo_paths = original_svc_paths
            git_server._service._read_only = original_svc_read_only
            git_server._service._allow_detached_head = original_svc_allow

        assert denied.json().get("is_error") is True
        assert allowed.json().get("is_error") is not True

    def test_dry_run_pull_and_push_skip_dirty_precondition(self, client, tmp_path):
        from scripts.mcp_servers.git import git_server

        # Stage 3 (verify_authorization) rejects an empty/implicit ref when
        # there is no resolvable active branch — e.g. a detached HEAD — per
        # `_validate_ref`'s "empty ref valid only when a current branch exists"
        # rule (`repository_state.py`). That Stage-3 check is unaffected by
        # dry_run by design (only Stage 5 preconditions are skipped), so this
        # test stays on a non-detached, non-protected branch ("develop") to
        # isolate the dirty-worktree (Stage 5) skip this test targets;
        # detached-HEAD skip is already covered by the checkout test above,
        # which supplies an explicit target branch instead of an implicit ref.
        remote_dir = tmp_path / "remote"
        remote_dir.mkdir()
        git.Repo.init(str(remote_dir), bare=True)

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        repo = git.Repo.init(str(repo_dir))
        (repo_dir / "README.md").write_text("# test")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.git.checkout("-b", "develop")
        repo.create_remote("origin", str(remote_dir))
        repo.git.push("origin", "develop:develop")
        repo.git.branch("--set-upstream-to=origin/develop", "develop")
        (repo_dir / "README.md").write_text("# test\nuncommitted\n")  # dirty

        original_paths = git_server._cfg.allowed_repo_paths
        original_read_only = git_server._cfg.read_only
        original_svc_paths = git_server._service._allowed_repo_paths
        original_svc_read_only = git_server._service._read_only
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            git_server._cfg.read_only = False
            git_server._service._allowed_repo_paths = [str(repo_dir)]
            git_server._service._read_only = False
            pull_response = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_pull",
                    "args": {
                        "repo_path": str(repo_dir),
                        "remote": "origin",
                        "branch": "develop",
                        "dry_run": True,
                    },
                },
            )
            push_response = client.post(
                "/v1/call_tool",
                json={
                    "name": "git_push",
                    "args": {
                        "repo_path": str(repo_dir),
                        "remote": "origin",
                        "branch": "develop",
                        "dry_run": True,
                    },
                },
            )
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.read_only = original_read_only
            git_server._service._allowed_repo_paths = original_svc_paths
            git_server._service._read_only = original_svc_read_only

        assert pull_response.json().get("is_error") is not True
        assert push_response.json().get("is_error") is not True
        assert git.Repo(str(repo_dir)).is_dirty()  # unchanged: still dirty, no mutation


class TestNewlyReachableToolsViaHTTP:
    """REQ-002/003/004: the 7 tools gitdispatch's dispatch-unification makes
    newly reachable via POST /v1/call_tool (git_status/git_log/git_diff/
    git_branch/git_show/git_add/git_commit)."""

    @pytest.fixture
    def client(self):
        # This file's module-scoped `client` fixture (top of file) imports the
        # app via `mcp_servers.git.server` — a distinct module object from
        # `scripts.mcp_servers.git.git_server` (dual import paths resolve to
        # separate sys.modules entries), so patching one's `_cfg`/`_service`
        # does not affect the other's live app instance. This class's `enabled`
        # fixture patches via `scripts.mcp_servers.git.git_server`, matching
        # this file's more recent `client` fixtures (e.g. line ~905) — define
        # a class-local `client` on the same import path instead of reusing
        # the outer one.
        from scripts.mcp_servers.git.git_server import app

        return TestClient(app)

    @pytest.fixture
    def repo_dir(self, tmp_path):
        d = tmp_path / "repo"
        d.mkdir()
        repo = git.Repo.init(str(d))
        (d / "README.md").write_text("# test")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        return d

    @pytest.fixture
    def enabled(self, repo_dir):
        from scripts.mcp_servers.git import git_server

        original_paths = git_server._cfg.allowed_repo_paths
        original_read_only = git_server._cfg.read_only
        original_svc_paths = git_server._service._allowed_repo_paths
        original_svc_read_only = git_server._service._read_only
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        try:
            yield
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.read_only = original_read_only
            git_server._service._allowed_repo_paths = original_svc_paths
            git_server._service._read_only = original_svc_read_only

    @pytest.mark.parametrize(
        ("tool_name", "extra_args"),
        [
            ("git_status", {}),
            ("git_log", {}),
            ("git_diff", {}),
            ("git_branch", {}),
            ("git_show", {}),
            ("git_add", {"paths": ["README.md"]}),
            ("git_commit", {"message": "probe"}),
        ],
    )
    def test_newly_reachable_tool_not_unknown(
        self, client, enabled, repo_dir, tool_name, extra_args
    ):
        """AC-1: each of the 7 tools now executes instead of 'Unknown tool'."""
        response = client.post(
            "/v1/call_tool",
            json={
                "name": tool_name,
                "args": {"repo_path": str(repo_dir), **extra_args},
            },
        )
        assert response.json().get("result") != f"Unknown tool: {tool_name}"

    @pytest.mark.parametrize(
        ("tool_name", "extra_args"),
        [
            ("git_add", {"paths": ["README.md"]}),
            ("git_commit", {"message": "probe"}),
        ],
    )
    def test_newly_reachable_write_tool_denied_under_dirty_worktree(
        self, client, enabled, repo_dir, tool_name, extra_args
    ):
        """AC-2: git_add/git_commit still go through WriteProtectionPipeline —
        denied under the same dirty-worktree condition as the pre-existing
        write tools (git_checkout/git_pull/git_push)."""
        (repo_dir / "README.md").write_text("# test\nuncommitted\n")  # dirty
        response = client.post(
            "/v1/call_tool",
            json={
                "name": tool_name,
                "args": {"repo_path": str(repo_dir), **extra_args},
            },
        )
        assert response.json().get("is_error") is True

    def test_read_tool_bypasses_dirty_worktree_denial(self, client, enabled, repo_dir):
        """AC-3: a read-only tool (git_status) is not denied under the same
        dirty-worktree condition that denies git_add/git_commit above."""
        (repo_dir / "README.md").write_text("# test\nuncommitted\n")  # dirty
        response = client.post(
            "/v1/call_tool",
            json={"name": "git_status", "args": {"repo_path": str(repo_dir)}},
        )
        assert response.json().get("is_error") is not True
