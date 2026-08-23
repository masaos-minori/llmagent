from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from mcp_servers.git.git_service import GitService


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
