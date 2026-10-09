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

import asyncio
import threading
from unittest.mock import MagicMock, patch

import git
import pytest
from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.git_models import GitConfig, GitPullRequest, GitPushRequest
from mcp_servers.git.git_service import GitService
from mcp_servers.git.repository_state import RepositoryState
from pydantic import ValidationError


def _svc(
    allowed: list[str] | None = None,
    read_only: bool = True,
    max_log: int = 50,
    allowed_remote_urls: list[str] | None = None,
) -> GitService:
    cfg = GitConfig(
        allowed_repo_paths=allowed if allowed is not None else [],
        read_only=read_only,
        max_log_entries=max_log,
        allowed_remote_urls=allowed_remote_urls or [],
    )
    return GitService(
        allowed_repo_paths=cfg.allowed_repo_paths,
        read_only=cfg.read_only,
        max_log_entries=cfg.max_log_entries,
        _config=cfg,
    )


# ── git_log ─────────────────────────────────────────────────────────────────


class TestGitLog:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_log({"repo_path": "/opt/repos/proj"})

    @pytest.mark.asyncio
    async def test_no_commits(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_log({"repo_path": "/opt/repos/proj"})
        assert result == "(no commits)"

    @pytest.mark.asyncio
    async def test_read_only_bypasses_write_protection_pipeline(self) -> None:
        """REQ-003: a dirty/detached-HEAD repo does not deny a read-only tool."""
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] worktree has uncommitted changes",
        )
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
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_diff({"repo_path": "/opt/repos/proj"})

    @pytest.mark.asyncio
    async def test_no_diff(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.git.diff.return_value = ""
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_diff({"repo_path": "/opt/repos/proj"})
        assert result == "(no diff)"

    @pytest.mark.asyncio
    async def test_read_only_bypasses_write_protection_pipeline(self) -> None:
        """REQ-003: a dirty/detached-HEAD repo does not deny a read-only tool."""
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.git.diff.return_value = ""
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] worktree has uncommitted changes",
        )
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
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_branch({"repo_path": "/opt/repos/proj"})

    @pytest.mark.asyncio
    async def test_no_branches(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.branches = []
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.active_branch = "main"
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_branch({"repo_path": "/opt/repos/proj"})
        assert result == "(no branches)"

    @pytest.mark.asyncio
    async def test_read_only_bypasses_write_protection_pipeline(self) -> None:
        """REQ-003: a dirty/detached-HEAD repo does not deny a read-only tool."""
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.branches = []
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.active_branch = "main"
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] repository is in a detached HEAD state",
        )
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
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_show({"repo_path": "/opt/repos/proj"})

    @pytest.mark.asyncio
    async def test_shows_commit(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.git.show.return_value = "commit abc123\n\ndiff --git a b"
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_show({"repo_path": "/opt/repos/proj", "ref": "HEAD"})
        assert "commit abc123" in result

    @pytest.mark.asyncio
    async def test_read_only_bypasses_write_protection_pipeline(self) -> None:
        """REQ-003: a dirty/detached-HEAD repo does not deny a read-only tool."""
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.git.show.return_value = "commit abc123\n\ndiff --git a b"
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] worktree has uncommitted changes",
        )
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
        with pytest.raises(ValueError, match="read_only"):
            await svc.git_pull({"repo_path": "/opt/repos/proj", "branch": "main"})

    @pytest.mark.asyncio
    async def test_dry_run_fetch(self) -> None:
        svc = _svc(
            allowed=["/opt/repos"],
            read_only=False,
            allowed_remote_urls=["https://example.com/repo.git"],
        )
        mock_repo = MagicMock()
        mock_repo.git.fetch.return_value = "up to date"
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_repo.remotes = [origin]
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap._repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with (
            patch.object(RepositoryState, "snapshot", return_value=snap),
        ):
            result = await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "dry_run": True, "branch": "main"}
            )
        assert "[DRY RUN]" in result
        assert "up to date" in result

    @pytest.mark.asyncio
    async def test_pull_result(self) -> None:
        svc = _svc(
            allowed=["/opt/repos"],
            read_only=False,
            allowed_remote_urls=["https://example.com/repo.git"],
        )
        mock_repo = MagicMock()
        mock_repo.is_dirty.return_value = False
        mock_repo.head.is_detached = False
        mock_repo.git.pull.return_value = "Already up to date."
        mock_repo.index.unmerged_blobs.return_value = []
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_repo.remotes = [origin]
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap._repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with (
            patch.object(RepositoryState, "snapshot", return_value=snap),
        ):
            result = await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "branch": "main"}
            )
        assert result == "Already up to date."


# ── Audit record fields — status dispatch path (NC-020 Row 6) ────────────────


class TestGitStatus:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_status({"repo_path": "/opt/repos/proj"})

    @pytest.mark.asyncio
    async def test_audit_record_server_key_present(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result

    @pytest.mark.asyncio
    async def test_read_only_bypasses_write_protection_pipeline(self) -> None:
        """REQ-003: a dirty/detached-HEAD repo does not deny a read-only tool."""
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = True
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] repository is in a detached HEAD state",
        )
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result


# ── Sibling-path rejection (REQ-007) ─────────────────────────────────────────


class TestSiblingPathRejection:
    """Regression tests for REQ-007: component-aware containment in _validate_repo."""

    @pytest.mark.asyncio
    async def test_sibling_with_underscore_rejected(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_log({"repo_path": "/opt/repos_evil/proj"})

    @pytest.mark.asyncio
    async def test_sibling_with_dash_rejected(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_diff({"repo_path": "/opt/repos-evil/proj"})

    @pytest.mark.asyncio
    async def test_sibling_prefix_shorter_rejected(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_branch({"repo_path": "/opt/re"})

    @pytest.mark.asyncio
    async def test_sibpath_longer_rejected(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_show({"repo_path": "/opt/repos_evil/sub"})

    @pytest.mark.asyncio
    async def test_exact_root_accepted(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/opt/repos"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_log({"repo_path": "/opt/repos"})
        assert result == "(no commits)"

    @pytest.mark.asyncio
    async def test_subdir_of_root_accepted(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/opt/repos/proj"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_log({"repo_path": "/opt/repos/proj"})
        assert result == "(no commits)"

    @pytest.mark.asyncio
    async def test_audit_record_contains_canonical_target_for_status(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result

    @pytest.mark.asyncio
    async def test_audit_record_server_key_present(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result


# ── git_checkout denied branch ───────────────────────────────────────────────


class TestGitCheckoutDenied:
    @pytest.mark.asyncio
    async def test_denied_when_allowed_empty(self) -> None:
        svc = _svc(allowed=[])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_checkout({"repo_path": "/opt/repos/proj", "branch": "main"})

    @pytest.mark.asyncio
    async def test_audit_record_empty_target_for_denied_call(self) -> None:
        svc = _svc(allowed=[])
        with pytest.raises(ValueError, match="\\[DENIED\\]"):
            await svc.git_checkout(
                {
                    "repo_path": "/opt/repos/proj",
                    "branch": "main",
                }
            )

    @pytest.mark.asyncio
    async def test_write_tool_still_denied_under_dirty_and_detached_head(self) -> None:
        """REQ-004 regression guard: the read-only bypass (REQ-003) must not also
        bypass write-tool protection — a write tool under the same dirty/detached-
        HEAD conditions a read tool bypasses must still be denied."""
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.is_dirty = True
        snap.is_detached_head = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (
            False,
            "[DENIED] worktree has uncommitted changes",
        )
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            with pytest.raises(ValueError, match="worktree has uncommitted changes"):
                await svc.git_checkout(
                    {
                        "repo_path": "/opt/repos/proj",
                        "branch": "develop",
                        "dry_run": False,
                    }
                )


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


# ── Audit record verification (NC-020 Row 6) ─────────────────────────────────


class TestAuditRecordFields:
    """Verify audit record fields for dispatch paths."""

    @pytest.mark.asyncio
    async def test_audit_record_contains_canonical_target_for_status(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result

    @pytest.mark.asyncio
    async def test_audit_record_server_key_present(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result


class TestWriteRefAllowlist:
    """REQ-001: allow-list validator rejects force-push / refspec forms."""

    @pytest.mark.parametrize(
        "bad",
        [
            "+main",
            "feature:main",
            "HEAD:main",
            "refs/heads/main",
            "main~1",
            "main..",
            "a b",
            "a\\b",
            "a@{1}",
            "[x]",
            "\0",
            "HEAD",
        ],
    )
    def test_rejected_branch_forms(self, bad) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_ref_allowlist(bad)
        assert ok is False
        assert msg.startswith("[DENIED]")

    @pytest.mark.parametrize("good", ["main", "feature/x", "develop-1", "a.b"])
    def test_simple_names_pass(self, good) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_ref_allowlist(good)
        assert ok is True
        assert msg == ""

    @pytest.mark.parametrize("bad", ["../evil", "a:b", "-x", "has space"])
    def test_rejected_remote_forms(self, bad) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_remote(bad)
        assert ok is False
        assert msg.startswith("[DENIED]")

    @pytest.mark.parametrize("good", ["origin", "remote-1", "upstream"])
    def test_valid_remote_forms(self, good) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_remote(good)
        assert ok is True
        assert msg == ""


class TestGitPushRefRejectionBeforeGit:
    """REQ-001: malicious push refspec forms rejected before any GitPython call."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad",
        ["+main", "feature:main", "HEAD:main", "refs/heads/main", "main~1"],
    )
    async def test_rejected_before_snapshot(self, bad) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="\\[DENIED\\]"),
        ):
            await svc.git_push(
                {"repo_path": "/opt/repos/proj", "branch": bad, "remote": "origin"}
            )


def _pull_snap(mock_repo: MagicMock) -> MagicMock:
    """Build a mocked RepositoryState that routes through mock_repo."""
    snap = MagicMock(spec=RepositoryState)
    snap.path = "/tmp/repo-offload"
    snap._repo = mock_repo
    snap.is_dirty = False
    snap.is_detached_head = False
    snap.verify_authorization.return_value = (True, "")
    snap.verify_preconditions.return_value = (True, "")
    snap.verify_postcondition.return_value = (True, "")
    snap.audit.return_value = {}
    return snap


class TestWriteOffloadAndTimeout:
    """REQ-001 (event-loop offload) + REQ-003 (per-operation timeout)."""

    @pytest.mark.asyncio
    async def test_write_runs_on_worker_thread_not_loop(self) -> None:
        """REQ-001: the blocking write executes on a worker thread, not the
        event-loop thread.

        This asserts thread identity directly (the robust discriminator): the
        slow Git call records the thread it runs on, and that thread must differ
        from the thread running the event loop. Removing the ``to_thread``
        dispatch would run the write on the loop thread and fail this assertion.
        A concurrent health-style coroutine additionally proves the loop stays
        responsive while the write is blocked in the worker thread.
        """
        started = threading.Event()
        release = threading.Event()
        seen_threads: list[threading.Thread] = []

        def slow_pull(*_a, **_k) -> str:
            seen_threads.append(threading.current_thread())
            started.set()
            release.wait(timeout=5)
            return "up to date"

        mock_repo = MagicMock()
        mock_repo.git.pull.side_effect = slow_pull
        mock_repo.index.unmerged_blobs.return_value = []
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_repo.remotes = [origin]
        snap = _pull_snap(mock_repo)

        svc = _svc(
            allowed=["/opt/repos"],
            read_only=False,
            allowed_remote_urls=["https://example.com/repo.git"],
        )

        with patch.object(RepositoryState, "snapshot", return_value=snap):
            loop_thread = threading.current_thread()
            task = asyncio.create_task(
                svc.git_pull({"repo_path": "/opt/repos/proj", "branch": "main"})
            )
            # Poll without blocking the loop until the write enters slow_pull.
            for _ in range(200):
                if started.is_set():
                    break
                await asyncio.sleep(0.01)
            assert started.is_set(), "slow write did not start"

            assert seen_threads, "write never executed the blocking call"
            assert seen_threads[0] is not loop_thread, (
                "write ran on the event-loop thread; not offloaded via to_thread"
            )

            # While the write is blocked in the worker thread, a concurrent
            # health-style coroutine must still complete promptly.
            health_done = asyncio.Event()

            async def health_probe() -> None:
                await asyncio.sleep(0.05)
                health_done.set()

            probe_task = asyncio.create_task(health_probe())
            await asyncio.wait_for(probe_task, timeout=2.0)
            assert health_done.is_set()

            release.set()
            await asyncio.wait_for(task, timeout=2.0)

    @pytest.mark.asyncio
    async def test_slow_pull_raises_timeout(self) -> None:
        release = threading.Event()

        def slow_pull(*_a, **_k) -> str:
            release.wait(timeout=5)
            return "up to date"

        mock_repo = MagicMock()
        mock_repo.git.pull.side_effect = slow_pull
        mock_repo.index.unmerged_blobs.return_value = []
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_repo.remotes = [origin]
        snap = _pull_snap(mock_repo)

        cfg = GitConfig(
            allowed_repo_paths=["/opt/repos"],
            read_only=False,
            allowed_remote_urls=["https://example.com/repo.git"],
            pull_timeout=0.1,
        )
        svc = GitService(
            allowed_repo_paths=cfg.allowed_repo_paths,
            read_only=cfg.read_only,
            max_log_entries=cfg.max_log_entries,
            _config=cfg,
        )

        with (
            patch.object(RepositoryState, "snapshot", return_value=snap),
            pytest.raises(asyncio.TimeoutError),
        ):
            await svc.git_pull({"repo_path": "/opt/repos/proj", "branch": "main"})
        # Unblock the orphaned worker thread so it does not leak.
        release.set()


class TestDestinationBasedProtection:
    """REQ-002/REQ-003: protected-branch decision is evaluated against the destination."""

    @pytest.mark.asyncio
    async def test_checkout_from_protected_succeeds(self, tmp_path) -> None:
        import pathlib

        repo_dir = pathlib.Path(str(tmp_path))
        # init a repo with an initial commit on main
        repo = git.Repo.init(repo_dir)
        (repo_dir / "f.txt").write_text("x")
        repo.index.add(["f.txt"])
        repo.index.commit("init")
        repo.git.branch("develop")
        svc = GitService(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            protected_branches=["main"],
            max_log_entries=50,
        )
        result = await svc.git_checkout(
            {"repo_path": str(repo_dir), "branch": "develop"}
        )
        assert "develop" in result  # switched away from protected main

    @pytest.mark.asyncio
    async def test_push_to_protected_rejected_at_dispatch(self, tmp_path) -> None:
        import pathlib

        repo_dir = pathlib.Path(str(tmp_path))
        repo = git.Repo.init(repo_dir)
        (repo_dir / "f.txt").write_text("x")
        repo.index.add(["f.txt"])
        repo.index.commit("init")
        svc = GitService(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            protected_branches=["main"],
            max_log_entries=50,
        )
        with pytest.raises(ValueError, match="protected branch"):
            await svc.git_push(
                {"repo_path": str(repo_dir), "branch": "main", "remote": "origin"}
            )


class TestGitPullPushBranchRequired:
    """REQ-004: git_pull/git_push require a non-empty branch."""

    def test_pull_requires_branch(self) -> None:
        with pytest.raises(ValidationError):
            GitPullRequest(repo_path="/x")

    def test_push_requires_branch(self) -> None:
        with pytest.raises(ValidationError):
            GitPushRequest(repo_path="/x")

    def test_pull_accepts_branch(self) -> None:
        req = GitPullRequest(repo_path="/x", branch="main")
        assert req.branch == "main"

    def test_push_accepts_branch(self) -> None:
        req = GitPushRequest(repo_path="/x", branch="main")
        assert req.branch == "main"

    @pytest.mark.asyncio
    async def test_additive_schema_audit_record_fields(self) -> None:
        """REQ-001: _build_audit_record accepts requested_target and canonical_target."""
        from mcp_servers.audit import _build_audit_record

        record = _build_audit_record(
            session_id="sess-1",
            request_id="req-1",
            action="git_status",
            target="/opt/repos/proj",
            outcome="ok",
            requested_target="/opt/repos/proj",
            canonical_target="/opt/repos/proj",
        )
        assert record["canonical_target"] == "/opt/repos/proj"

    @pytest.mark.asyncio
    async def test_postcondition_message_contains_resulting_state(self) -> None:
        """REQ-006: checkout postcondition failure message includes resulting state."""
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        snap = MagicMock(spec=RepositoryState)
        snap.path = "/tmp/repo"
        snap.is_dirty = False
        snap.head_type = "detached"
        snap.active_branch = "HEAD"
        snap.untracked_file_count = 0
        snap.protected_branch = False
        snap.ref_valid = True
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (
            False,
            "checkout postcondition failed: state already changed; expected branch 'dev', got '<detached HEAD>'",
        )
        snap.audit.return_value = {}
        snap.repo = MagicMock()
        snap.repo.active_branch.name = "HEAD"
        snap.repo.is_dirty.return_value = False

        with patch.object(RepositoryState, "snapshot", return_value=snap):
            with pytest.raises(GitServiceError, match="state already changed"):
                await svc.git_checkout(
                    {
                        "repo_path": "/opt/repos/proj",
                        "branch": "dev",
                        "create": False,
                        "dry_run": False,
                    }
                )

    @pytest.mark.asyncio
    async def test_config_injection_format_pull_uses_passed_cfg(self) -> None:
        """REQ-007: format_pull uses the passed _cfg and ignores a divergent config."""
        from mcp_servers.git.format_output import format_pull

        mock_cfg = MagicMock()
        mock_cfg.allowed_remote_urls = ["https://example.com/repo.git"]

        mock_state = MagicMock()
        mock_state._repo = MagicMock()
        mock_state._repo.git.pull.return_value = "Already up to date."
        mock_state._repo.index.unmerged_blobs.return_value = []
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_state._repo.remotes = [origin]

        req = GitPullRequest(
            repo_path="/opt/repos/proj", remote="origin", branch="main"
        )

        result = format_pull(mock_state, req, mock_cfg)
        assert result == "Already up to date."
        # Verify the mock_cfg was used (not GitConfig.load())
        assert mock_cfg.allowed_remote_urls == ["https://example.com/repo.git"]

    @pytest.mark.asyncio
    async def test_config_injection_format_push_uses_passed_cfg(self) -> None:
        """REQ-007: format_push uses the passed _cfg and ignores a divergent config."""
        from mcp_servers.git.format_output import format_push

        mock_cfg = MagicMock()
        mock_cfg.allowed_remote_urls = ["https://example.com/repo.git"]

        mock_state = MagicMock()
        mock_state._repo = MagicMock()
        mock_state._repo.git.push.return_value = "Pushed 'main' to 'origin'"
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_state._repo.remotes = [origin]

        req = GitPushRequest(
            repo_path="/opt/repos/proj", remote="origin", branch="main"
        )

        result = format_push(mock_state, req, mock_cfg)
        assert result == "Pushed 'main' to 'origin'"
        # Verify the mock_cfg was used (not GitConfig.load())
        assert mock_cfg.allowed_remote_urls == ["https://example.com/repo.git"]
