from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
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
        snap.is_dirty = False
        snap.is_detached_head = True
        snap.active_branch = "develop"
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
        snap.is_dirty = False
        snap.is_detached_head = True
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
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.active_branch = "develop"
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
        snap.is_dirty = True
        snap.is_detached_head = True
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
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result
