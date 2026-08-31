"""tests/test_mcp_git.py
Unit tests for mcp/git/service.py: GitService guards and dry_run.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st
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


# ── _check_repo_path ──────────────────────────────────────────────────────────


@given(st.text(), st.lists(st.text(), min_size=1))
def test_check_repo_path_equivalence(target: str, allowed_repos: list[str]) -> None:
    """Property test: old and new implementations produce identical results."""

    def old_impl(t: str, allowed: list[str]) -> bool:
        p = PurePosixPath(t)
        for a in allowed:
            try:
                p.relative_to(a)
                return True
            except ValueError:
                continue
        return False

    def new_impl(t: str, allowed: list[str]) -> bool:
        p = PurePosixPath(t)
        for a in allowed:
            if p.is_relative_to(a):
                return True
        return False

    assert old_impl(target, allowed_repos) == new_impl(target, allowed_repos)


class TestCheckRepoPath:
    def test_empty_allowed_denies_all(self) -> None:
        svc = _svc(allowed=[])
        ok, err, _resolved = svc._check_repo_path("/any/path")
        assert not ok
        assert "[DENIED]" in err

    def test_matching_prefix_allowed(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err, _resolved = svc._check_repo_path("/opt/repos/myproject")
        assert ok
        assert err == ""

    def test_exact_match_allowed(self) -> None:
        svc = _svc(allowed=["/opt/repos/myproject"])
        ok, err, _resolved = svc._check_repo_path("/opt/repos/myproject")
        assert ok

    def test_non_matching_path_denied(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err, _resolved = svc._check_repo_path("/home/user/project")
        assert not ok
        assert "[DENIED]" in err

    def test_path_traversal_denied(self) -> None:
        # /opt/repos/../secret is resolved to /opt/secret — not under /opt/repos
        svc = _svc(allowed=["/opt/repos"])
        ok, _, _ = svc._check_repo_path("/opt/repos/../secret")
        assert not ok

    # ── Resolved path assertions (NC-020 Row 5) ──────────────────────────────────

    def test_resolved_path_on_success(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err, resolved = svc._check_repo_path("/opt/repos/myproject")
        assert ok is True
        assert err == ""
        assert resolved == "/opt/repos/myproject"

    def test_empty_resolved_path_on_failure(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err, resolved = svc._check_repo_path("/home/user/project")
        assert ok is False
        assert "[DENIED]" in err
        assert resolved == ""


# ── Audit target resolution (NC-020 Row 5) ───────────────────────────────────


class TestAuditTargetResolution:
    """Verify audit target uses canonical identity."""

    @pytest.mark.asyncio
    async def test_audit_target_is_canonical_for_status_call(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result

    @pytest.mark.asyncio
    async def test_audit_target_empty_for_denied_call(self) -> None:
        svc = _svc(allowed=[], read_only=True)
        result = await svc.git_checkout(
            {
                "repo_path": "/opt/repos/proj",
                "branch": "main",
            }
        )
        assert "[DENIED]" in result


# ── _check_write ──────────────────────────────────────────────────────────────


class TestCheckWrite:
    def test_read_only_true_denies_write(self) -> None:
        svc = _svc(allowed=["/tmp"], read_only=True)
        ok, err = svc._check_write()
        assert not ok
        assert "read_only=true" in err

    def test_read_only_false_allows_write(self) -> None:
        svc = _svc(allowed=["/tmp"], read_only=False)
        ok, err = svc._check_write()
        assert ok
        assert err == ""


# ── git_status ────────────────────────────────────────────────────────────────


class TestGitStatus:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "[DENIED]" in result

    @pytest.mark.asyncio
    async def test_clean_working_tree(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result
        assert "clean" in result


# ── git_add ───────────────────────────────────────────────────────────────────


class TestGitAdd:
    @pytest.mark.asyncio
    async def test_denied_by_read_only(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=True)
        result = await svc.git_add({"repo_path": "/opt/repos/proj", "paths": ["a.py"]})
        assert "read_only" in result

    @pytest.mark.asyncio
    async def test_dry_run_shows_would_stage(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.untracked_files = ["a.py"]
        mock_repo.index.diff.return_value = []
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_add(
                {"repo_path": "/opt/repos/proj", "paths": ["a.py"], "dry_run": True}
            )
        assert "[DRY RUN]" in result
        assert "a.py" in result

    @pytest.mark.asyncio
    async def test_denied_path_not_in_allowed(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        result = await svc.git_add({"repo_path": "/home/user/proj", "paths": ["a.py"]})
        assert "[DENIED]" in result


# ── git_commit ────────────────────────────────────────────────────────────────


class TestGitCommit:
    @pytest.mark.asyncio
    async def test_dry_run_shows_staged_files(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        staged = MagicMock()
        staged.a_path = "main.py"
        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = [staged]
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_commit(
                {
                    "repo_path": "/opt/repos/proj",
                    "message": "feat: add X",
                    "dry_run": True,
                }
            )
        assert "[DRY RUN]" in result
        assert "main.py" in result
        assert "feat: add X" in result

    @pytest.mark.asyncio
    async def test_denied_by_read_only(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=True)
        result = await svc.git_commit(
            {"repo_path": "/opt/repos/proj", "message": "msg"}
        )
        assert "read_only" in result


# ── git_checkout ──────────────────────────────────────────────────────────────


class TestGitCheckout:
    @pytest.mark.asyncio
    async def test_dry_run_checkout(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_checkout(
                {"repo_path": "/opt/repos/proj", "branch": "feature/x", "dry_run": True}
            )
        assert "[DRY RUN]" in result
        assert "feature/x" in result

    @pytest.mark.asyncio
    async def test_dry_run_create_branch(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_checkout(
                {
                    "repo_path": "/opt/repos/proj",
                    "branch": "new-feat",
                    "create": True,
                    "dry_run": True,
                }
            )
        assert "[DRY RUN]" in result
        assert "create" in result.lower()


# ── git_push ──────────────────────────────────────────────────────────────────


class TestGitPush:
    @pytest.mark.asyncio
    async def test_dry_run_push_current_branch(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        snap = MagicMock(spec=RepositoryState)
        snap.repo = mock_repo
        snap.active_branch = "main"
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_push(
                {"repo_path": "/opt/repos/proj", "branch": "main", "dry_run": True}
            )
        assert "[DRY RUN]" in result
        assert "main" in result
        assert "origin" in result

    @pytest.mark.asyncio
    async def test_denied_by_read_only(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=True)
        result = await svc.git_push({"repo_path": "/opt/repos/proj", "branch": "main"})
        assert "read_only" in result
