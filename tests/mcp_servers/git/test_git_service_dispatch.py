"""tests/mcp_servers/git/test_git_service_dispatch.py

Characterization tests for GitService dispatch paths not covered by
test_mcp_git.py: git_log, git_diff, git_branch, git_show, git_pull,
the git_checkout denied branch, the _wrap_git_op error-wrap branch, and
the real (unpatched) _open_repo body.

These lock current behavior ahead of a structural refactor of
scripts/mcp_servers/git/git_service.py (extraction of the shared
validate->open->wrap pattern); they must pass unchanged before and after.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import git
import pytest
from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.git_service import GitService
from mcp_servers.git.repository_state import RepositoryState


def _svc(
    allowed: list[str] | None = None,
    read_only: bool = True,
    max_log: int = 50,
) -> GitService:
    return GitService(
        allowed_repo_paths=allowed if allowed is not None else [],
        read_only=read_only,
        max_log_entries=max_log,
    )


# ── git_log ─────────────────────────────────────────────────────────────────


class TestGitLog:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        result = await svc.git_log({"repo_path": "/opt/repos/proj"})
        assert "[DENIED]" in result

    @pytest.mark.asyncio
    async def test_no_commits(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_log({"repo_path": "/opt/repos/proj"})
        assert result == "(no commits)"


# ── git_diff ────────────────────────────────────────────────────────────────


class TestGitDiff:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        result = await svc.git_diff({"repo_path": "/opt/repos/proj"})
        assert "[DENIED]" in result

    @pytest.mark.asyncio
    async def test_no_diff(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.git.diff.return_value = ""
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_diff({"repo_path": "/opt/repos/proj"})
        assert result == "(no diff)"


# ── git_branch ──────────────────────────────────────────────────────────────


class TestGitBranch:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        result = await svc.git_branch({"repo_path": "/opt/repos/proj"})
        assert "[DENIED]" in result

    @pytest.mark.asyncio
    async def test_no_branches(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.branches = []
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.active_branch = "main"
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_branch({"repo_path": "/opt/repos/proj"})
        assert result == "(no branches)"


# ── git_show ────────────────────────────────────────────────────────────────


class TestGitShow:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        result = await svc.git_show({"repo_path": "/opt/repos/proj"})
        assert "[DENIED]" in result

    @pytest.mark.asyncio
    async def test_shows_commit(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.git.show.return_value = "commit abc123\n\ndiff --git a b"
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_show({"repo_path": "/opt/repos/proj", "ref": "HEAD"})
        assert "commit abc123" in result


# ── git_pull ────────────────────────────────────────────────────────────────


class TestGitPull:
    @pytest.mark.asyncio
    async def test_denied_by_read_only(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=True)
        result = await svc.git_pull({"repo_path": "/opt/repos/proj"})
        assert "read_only" in result

    @pytest.mark.asyncio
    async def test_dry_run_fetch(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.git.fetch.return_value = "up to date"
        snap = MagicMock(spec=RepositoryState)
        snap._repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "dry_run": True}
            )
        assert "[DRY RUN]" in result
        assert "up to date" in result

    @pytest.mark.asyncio
    async def test_pull_result(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.is_dirty.return_value = False
        mock_repo.head.is_detached = False
        mock_repo.git.pull.return_value = "Already up to date."
        mock_repo.index.unmerged_blobs.return_value = []
        snap = MagicMock(spec=RepositoryState)
        snap._repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_pull({"repo_path": "/opt/repos/proj"})
        assert result == "Already up to date."


# ── git_checkout denied branch ───────────────────────────────────────────────


class TestGitCheckoutDenied:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        result = await svc.git_checkout(
            {"repo_path": "/opt/repos/proj", "branch": "main"}
        )
        assert "[DENIED]" in result


# ── _wrap_git_op error branch ────────────────────────────────────────────────


class TestWrapGitOp:
    def test_wraps_git_error(self) -> None:
        svc = _svc(allowed=["/opt/repos"])

        def _boom() -> str:
            raise git.exc.GitCommandError(["git", "status"], 1)

        with pytest.raises(GitServiceError, match="boom_tool failed"):
            svc._wrap_git_op("boom_tool", _boom)

    def test_wraps_os_error(self) -> None:
        svc = _svc(allowed=["/opt/repos"])

        def _boom() -> str:
            raise OSError("disk full")

        with pytest.raises(GitServiceError, match="boom_tool failed"):
            svc._wrap_git_op("boom_tool", _boom)

    def test_passes_through_on_success(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        assert svc._wrap_git_op("ok_tool", lambda: "result") == "result"


# ── _open_repo (real, unpatched) ─────────────────────────────────────────────


class TestOpenRepoReal:
    def test_opens_real_repo(self, tmp_path: object) -> None:
        import pathlib

        repo_dir = pathlib.Path(str(tmp_path))
        git.Repo.init(repo_dir)
        svc = _svc(allowed=[str(repo_dir)])
        repo = svc._open_repo(str(repo_dir))
        assert isinstance(repo, git.Repo)
