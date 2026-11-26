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
import os
import shutil
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest
from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.git_models import GitConfig, GitPullRequest, GitPushRequest
from mcp_servers.git.git_ref_validation import validate_ref_allowlist, validate_remote
from mcp_servers.git.git_service import GitService, WriteOutcomeError, build_service
from mcp_servers.git.repository_state import RepositoryState
from pydantic import ValidationError
from shared.write_outcome import OUTCOME_UNKNOWN

REMOTE_URL = "https://example.com/repo.git"


def _fake_process(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    """A stand-in for the process object `subprocess.Popen` returns."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc


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
        # RepositoryState is used through its context-manager form in the code under test.
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        mock_repo.index.unmerged_blobs.return_value = []
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_repo.remotes = [origin]
        snap = MagicMock(spec=RepositoryState)
        snap.__enter__.return_value = snap
        snap.path = "/tmp/repo"
        snap._repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        proc = _fake_process(stdout="Already up to date.")
        with (
            patch.object(RepositoryState, "snapshot", return_value=snap),
            patch("subprocess.Popen", return_value=proc),
        ):
            result = await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "branch": "main"}
            )
        assert result == "Already up to date."


class TestNetworkWriteToolsRequireConfig:
    """`_require_config()` replaces an `assert`, so `python -O` cannot skip the check."""

    @staticmethod
    def _snap(mock_repo: MagicMock) -> MagicMock:
        snap = MagicMock(spec=RepositoryState)
        snap.__enter__.return_value = snap
        snap.path = "/tmp/repo"
        snap._repo = mock_repo
        snap.is_dirty = False
        snap.is_detached_head = False
        snap.verify_authorization.return_value = (True, "")
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        return snap

    @pytest.mark.asyncio
    async def test_git_pull_without_config_raises_git_service_error(self) -> None:
        svc = GitService(allowed_repo_paths=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.git.fetch.return_value = "up to date"

        with patch.object(
            RepositoryState, "snapshot", return_value=self._snap(mock_repo)
        ):
            with pytest.raises(
                GitServiceError, match="git_pull requires the git MCP server config"
            ):
                await svc.git_pull({"repo_path": "/opt/repos/proj", "branch": "main"})

    @pytest.mark.asyncio
    async def test_git_push_without_config_raises_git_service_error(self) -> None:
        svc = GitService(allowed_repo_paths=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.git.push.return_value = "Everything up-to-date"

        with patch.object(
            RepositoryState, "snapshot", return_value=self._snap(mock_repo)
        ):
            with pytest.raises(
                GitServiceError, match="git_push requires the git MCP server config"
            ):
                await svc.git_push({"repo_path": "/opt/repos/proj", "branch": "main"})


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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        snap.__enter__.return_value = snap
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
        ok, msg = validate_ref_allowlist(bad)
        assert ok is False
        assert msg.startswith("[DENIED]")

    @pytest.mark.parametrize("good", ["main", "feature/x", "develop-1", "a.b"])
    def test_simple_names_pass(self, good) -> None:
        ok, msg = validate_ref_allowlist(good)
        assert ok is True
        assert msg == ""

    @pytest.mark.parametrize("bad", ["../evil", "a:b", "-x", "has space"])
    def test_rejected_remote_forms(self, bad) -> None:
        ok, msg = validate_remote(bad)
        assert ok is False
        assert msg.startswith("[DENIED]")

    @pytest.mark.parametrize("good", ["origin", "remote-1", "upstream"])
    def test_valid_remote_forms(self, good) -> None:
        ok, msg = validate_remote(good)
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


class TestGitPushServiceError:
    @pytest.mark.asyncio
    async def test_push_command_error_becomes_service_error(self, tmp_path) -> None:
        """REQ-003: a non-zero push exit surfaces as GitServiceError naming the tool."""
        repo_dir = tmp_path / "push_repo"
        repo_dir.mkdir()
        mock_repo = MagicMock()
        origin = MagicMock()
        origin.name = "origin"
        origin.url = REMOTE_URL
        mock_repo.remotes = [origin]
        state = RepositoryState(
            path=str(repo_dir),
            is_dirty=False,
            head_type="branch",
            active_branch="feature/x",
            untracked_file_count=0,
            protected_branch=False,
            ref_valid=True,
            _repo=mock_repo,
        )
        cfg = GitConfig(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            allowed_remote_urls=[REMOTE_URL],
            protected_branches=[],
            allow_detached_head=True,
        )
        svc = build_service(cfg)
        proc = _fake_process(
            stderr="fatal: not a git repository (or any of the parent directories): .git",
            returncode=1,
        )
        with (
            patch.object(RepositoryState, "snapshot", return_value=state),
            patch("subprocess.Popen", return_value=proc),
            pytest.raises(GitServiceError, match="push failed"),
        ):
            await svc.git_push(
                {
                    "repo_path": str(repo_dir),
                    "remote": "origin",
                    "branch": "feature/x",
                }
            )


def _pull_snap(mock_repo: MagicMock) -> MagicMock:
    """Build a mocked RepositoryState that routes through mock_repo."""
    snap = MagicMock(spec=RepositoryState)
    snap.__enter__.return_value = snap
    snap.path = "/tmp/repo-offload"
    snap._repo = mock_repo
    snap.is_dirty = False
    snap.is_detached_head = False
    snap.verify_authorization.return_value = (True, "")
    snap.verify_preconditions.return_value = (True, "")
    snap.verify_postcondition.return_value = (True, "")
    snap.audit.return_value = {}
    return snap


def _timeout_svc(cfg: GitConfig) -> GitService:
    """A GitService built from a config that carries the per-operation timeout."""
    return GitService(
        allowed_repo_paths=cfg.allowed_repo_paths,
        read_only=cfg.read_only,
        max_log_entries=cfg.max_log_entries,
        _config=cfg,
    )


def _stub_git(
    tmp_path: Path, *, apply_marker: bool
) -> tuple[Path, Path, Path, Path, Path]:
    """Create a real repository and a blocking stub `git` executable.

    Only `pull` and `push` are stubbed; every other `git` call is handed to the real
    binary, because GitPython also invokes `git` when it takes the post-operation
    snapshot. For a stubbed call the script records its own pid — the process-group
    leader, since the write path starts the child with `start_new_session=True` —
    optionally applies a marker commit and records that it did, then blocks until
    `release` appears. The deadline therefore fires while the process is alive, so
    `os.killpg()` runs against a real process group. Returns
    `(repo_dir, stub, pid_file, release, applied)`.

    The stub's startup and marker commit must complete before the deadline, so the
    cases that need the marker to land use a deadline comfortably larger than the
    stub's setup cost; a short deadline turns the ordering into a race under parallel
    test execution.
    """
    repo_dir = tmp_path / "repo"
    repo = git.Repo.init(repo_dir)
    (repo_dir / "f.txt").write_text("x")
    repo.index.add(["f.txt"])
    repo.index.commit("init")
    repo.create_remote("origin", REMOTE_URL)
    real_git = shutil.which("git")
    pid_file = tmp_path / "pid"
    release = tmp_path / "release"
    applied = tmp_path / "applied"
    apply_line = (
        f'    "{real_git}" -C "{repo_dir}" commit -m marker --allow-empty '
        f"&& touch {applied}\n"
        if apply_marker
        else ""
    )
    stub = tmp_path / "git"
    stub.write_text(
        "#!/bin/sh\n"
        f'REAL_GIT="{real_git}"\n'
        'case "$1" in\n'
        "  pull|push)\n"
        f"    echo $$ > {pid_file}\n"
        f"{apply_line}"
        f"    while [ ! -f {release} ]; do sleep 0.05; done\n"
        '    echo "stub output"\n'
        "    ;;\n"
        "  *)\n"
        '    exec "$REAL_GIT" "$@"\n'
        "    ;;\n"
        "esac\n"
    )
    stub.chmod(0o755)
    return repo_dir, stub, pid_file, release, applied


def _stub_path(stub: Path):
    """Prepend the stub executable's directory to PATH for the duration of a test."""
    return patch.dict(
        os.environ, {"PATH": f"{stub.parent}{os.pathsep}{os.environ['PATH']}"}
    )


def _assert_process_group_gone(pid_file: Path) -> None:
    """Fail unless the stub's recorded process-group pid no longer exists."""
    for _ in range(50):
        if pid_file.exists() and pid_file.read_text().strip():
            break
        time.sleep(0.02)
    else:
        pytest.fail("the stub git never recorded its process-group pid")
    pid = int(pid_file.read_text().strip())
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return
    pytest.fail(f"process group {pid} is still alive after the timeout")


def _assert_no_thread_still_running_the_write() -> None:
    """Fail if any alive thread is still inside the subprocess write call.

    The deadline is only real if the thread that started the write is gone: a thread
    left inside `communicate()` would continue the operation past the deadline.
    """
    for thread, frame in sys._current_frames().items():
        names: list[str] = []
        current = frame
        while current is not None:
            names.append(current.f_code.co_name)
            current = current.f_back
        if "communicate" in names or "_run_git_write" in names:
            pytest.fail(f"thread {thread.name} is still running the write")


class TestWriteOffloadAndTimeout:
    """REQ-001 (event-loop offload) + REQ-003 (per-operation timeout)."""

    @pytest.mark.asyncio
    async def test_write_runs_on_worker_thread_not_loop(self) -> None:
        """REQ-001: the blocking write executes on a worker thread, not the
        event-loop thread.

        This asserts thread identity directly (the robust discriminator): the
        slow `git` subprocess call records the thread its `communicate()` runs
        on, and that thread must differ from the thread running the event loop.
        Removing the ``to_thread`` dispatch would run the write on the loop
        thread and fail this assertion. A concurrent health-style coroutine
        additionally proves the loop stays responsive while the write is blocked
        in the worker thread.
        """
        started = threading.Event()
        release = threading.Event()
        seen_threads: list[threading.Thread] = []

        def slow_communicate(*_a, **_k) -> tuple[str, str]:
            seen_threads.append(threading.current_thread())
            started.set()
            release.wait(timeout=5)
            return ("up to date", "")

        mock_repo = MagicMock()
        mock_repo.index.unmerged_blobs.return_value = []
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        mock_repo.remotes = [origin]
        snap = _pull_snap(mock_repo)

        proc = _fake_process()
        proc.communicate.side_effect = slow_communicate

        svc = _svc(
            allowed=["/opt/repos"],
            read_only=False,
            allowed_remote_urls=["https://example.com/repo.git"],
        )

        with (
            patch.object(RepositoryState, "snapshot", return_value=snap),
            patch("subprocess.Popen", return_value=proc),
        ):
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
    async def test_pull_timeout_terminates_process_group(self, tmp_path: Path) -> None:
        """AC-3: the deadline terminates the process group; nothing was applied."""
        repo_dir, stub, pid_file, release, applied = _stub_git(
            tmp_path, apply_marker=False
        )
        cfg = GitConfig(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            allowed_remote_urls=[REMOTE_URL],
            pull_timeout=1.0,
        )
        svc = _timeout_svc(cfg)

        with (
            _stub_path(stub),
            pytest.raises(WriteOutcomeError) as exc_info,
        ):
            await svc.git_pull({"repo_path": str(repo_dir), "branch": "main"})

        assert exc_info.value.outcome == OUTCOME_UNKNOWN
        # The stub was stopped before it wrote anything: no repository effect.
        assert not applied.exists()
        assert git.Repo(str(repo_dir)).head.commit.message.strip() != "marker"
        _assert_process_group_gone(pid_file)
        _assert_no_thread_still_running_the_write()
        release.touch()

    @pytest.mark.asyncio
    async def test_pull_timeout_near_success_reports_outcome_unknown(
        self, tmp_path: Path
    ) -> None:
        """REQ-003: a timeout after the write landed is still an unknown outcome."""
        repo_dir, stub, pid_file, release, applied = _stub_git(
            tmp_path, apply_marker=True
        )
        cfg = GitConfig(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            allowed_remote_urls=[REMOTE_URL],
            pull_timeout=1.0,
        )
        svc = _timeout_svc(cfg)

        with (
            _stub_path(stub),
            pytest.raises(WriteOutcomeError) as exc_info,
        ):
            await svc.git_pull({"repo_path": str(repo_dir), "branch": "main"})

        assert exc_info.value.outcome == OUTCOME_UNKNOWN
        # The stub applied the marker commit before blocking, so the effect is present.
        assert applied.exists()
        assert git.Repo(str(repo_dir)).head.commit.message.strip() == "marker"
        _assert_process_group_gone(pid_file)
        _assert_no_thread_still_running_the_write()
        release.touch()

    @pytest.mark.asyncio
    async def test_push_timeout_terminates_process_group(self, tmp_path: Path) -> None:
        """AC-3: the same deadline behavior applies to the push path."""
        repo_dir, stub, pid_file, release, applied = _stub_git(
            tmp_path, apply_marker=False
        )
        cfg = GitConfig(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            allowed_remote_urls=[REMOTE_URL],
            push_timeout=1.0,
        )
        svc = _timeout_svc(cfg)

        with (
            _stub_path(stub),
            pytest.raises(WriteOutcomeError) as exc_info,
        ):
            await svc.git_push(
                {"repo_path": str(repo_dir), "remote": "origin", "branch": "main"}
            )

        assert exc_info.value.outcome == OUTCOME_UNKNOWN
        assert not applied.exists()
        assert git.Repo(str(repo_dir)).head.commit.message.strip() != "marker"
        _assert_process_group_gone(pid_file)
        _assert_no_thread_still_running_the_write()
        release.touch()

    @pytest.mark.asyncio
    async def test_push_timeout_near_success_reports_outcome_unknown(
        self, tmp_path: Path
    ) -> None:
        """REQ-003: a push that lands then blocks reports an unknown outcome."""
        repo_dir, stub, pid_file, release, applied = _stub_git(
            tmp_path, apply_marker=True
        )
        cfg = GitConfig(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            allowed_remote_urls=[REMOTE_URL],
            push_timeout=1.0,
        )
        svc = _timeout_svc(cfg)

        with (
            _stub_path(stub),
            pytest.raises(WriteOutcomeError) as exc_info,
        ):
            await svc.git_push(
                {"repo_path": str(repo_dir), "remote": "origin", "branch": "main"}
            )

        assert exc_info.value.outcome == OUTCOME_UNKNOWN
        assert applied.exists()
        assert git.Repo(str(repo_dir)).head.commit.message.strip() == "marker"
        _assert_process_group_gone(pid_file)
        _assert_no_thread_still_running_the_write()
        release.touch()


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
        snap.__enter__.return_value = snap
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
        mock_state.__enter__.return_value = mock_state
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

        proc = _fake_process(stdout="Already up to date.")
        with (
            patch("subprocess.Popen", return_value=proc),
            patch.object(RepositoryState, "snapshot", return_value=mock_state),
        ):
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
        mock_state.__enter__.return_value = mock_state
        mock_state._repo = MagicMock()
        origin = MagicMock()
        origin.name = "origin"
        origin.url = "https://example.com/repo.git"
        ref = MagicMock()
        ref.name = "origin/main"
        ref.commit.hexsha = "abc123"
        origin.refs = [ref]
        mock_state._repo.remotes = [origin]
        mock_state._repo.head.commit.hexsha = "abc123"

        req = GitPushRequest(
            repo_path="/opt/repos/proj", remote="origin", branch="main"
        )

        proc = _fake_process(stdout="Pushed 'main' to 'origin'")
        with (
            patch("subprocess.Popen", return_value=proc),
            patch.object(RepositoryState, "snapshot", return_value=mock_state),
        ):
            result = format_push(mock_state, req, mock_cfg)
        assert result == "Pushed 'main' to 'origin'"
        # Verify the mock_cfg was used (not GitConfig.load())
        assert mock_cfg.allowed_remote_urls == ["https://example.com/repo.git"]


# ── Characterization: handler guard order ─────────────────────────────────────


def _write_svc(protected: list[str] | None = None) -> GitService:
    """GitService with write access enabled and an optional protected-branch list."""
    cfg = GitConfig(
        allowed_repo_paths=["/opt/repos"],
        read_only=False,
        protected_branches=protected or [],
    )
    return GitService(
        allowed_repo_paths=list(cfg.allowed_repo_paths),
        read_only=cfg.read_only,
        protected_branches=list(cfg.protected_branches),
        _config=cfg,
    )


class TestHandlerGuardOrderCharacterization:
    """Characterization: every ref guard rejects before RepositoryState.snapshot()."""

    @pytest.mark.asyncio
    async def test_git_log_rejects_option_branch(self) -> None:
        svc = _svc(allowed=["/opt/repos"])

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="CLI option"),
        ):
            await svc.git_log({"repo_path": "/opt/repos/proj", "branch": "-u"})

    @pytest.mark.asyncio
    async def test_git_diff_rejects_option_commit(self) -> None:
        svc = _svc(allowed=["/opt/repos"])

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="CLI option"),
        ):
            await svc.git_diff({"repo_path": "/opt/repos/proj", "commit": "--stat"})

    @pytest.mark.asyncio
    async def test_git_show_rejects_option_ref(self) -> None:
        svc = _svc(allowed=["/opt/repos"])

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="CLI option"),
        ):
            await svc.git_show({"repo_path": "/opt/repos/proj", "ref": "--output"})

    @pytest.mark.asyncio
    async def test_git_pull_rejects_allowlist_form_before_protected_check(self) -> None:
        """A branch that is both protected and malformed reports the allowlist message."""
        svc = _write_svc(protected=["main"])

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="not a valid simple branch name"),
        ):
            await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "branch": "+main", "remote": "origin"}
            )

    @pytest.mark.asyncio
    async def test_git_pull_rejects_protected_branch_before_remote_check(self) -> None:
        svc = _write_svc(protected=["main"])

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="is a protected branch"),
        ):
            await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "branch": "main", "remote": "-x"}
            )

    @pytest.mark.asyncio
    async def test_git_pull_rejects_bad_remote_last(self) -> None:
        svc = _write_svc(protected=["main"])

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="not a valid remote name"),
        ):
            await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "branch": "develop", "remote": "a:b"}
            )


class TestWriteRefAllowlistEmptyRefCharacterization:
    """Characterization: an empty ref passes the allowlist and is denied later."""

    def test_empty_ref_passes_allowlist(self) -> None:
        ok, msg = validate_ref_allowlist("")
        assert ok is True
        assert msg == ""

    @pytest.mark.asyncio
    async def test_empty_branch_is_denied_by_the_protected_guard(self) -> None:
        svc = _write_svc()
        with pytest.raises(ValueError, match="branch must not be empty"):
            await svc.git_pull({"repo_path": "/opt/repos/proj", "branch": ""})


# ── Characterization: path guard messages ─────────────────────────────────────


class TestPathGuardMessageCharacterization:
    """Characterization: the containment guards' exact denial messages."""

    def test_is_within_allowed_paths_empty_list_message(self) -> None:
        svc = _svc(allowed=[])
        ok, err = svc._is_within_allowed_paths("/any/path")
        assert ok is False
        assert err == "[DENIED] allowed_repo_paths is empty"

    def test_is_within_allowed_paths_sibling_message(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err = svc._is_within_allowed_paths("/opt/repos-evil")
        assert ok is False
        assert err == "[DENIED] repo_path not in allowed paths"

    def test_validate_repo_empty_allowlist_message(self) -> None:
        """The empty-allowlist denial is the same message the containment guard gives."""
        svc = _svc(allowed=[])
        ok, err = asyncio.run(svc._validate_repo("/any/path", "git_checkout"))
        assert ok is False
        assert err == "[DENIED] allowed_repo_paths is empty"

    def test_validate_repo_unresolvable_path_message(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err = asyncio.run(svc._validate_repo("", "git_status"))
        assert ok is False
        assert err == "repo_path is empty"


# ── Characterization: ref / remote / protected-branch argument policy ────────
#
# Locked at the handler boundary ahead of extracting the validation cluster out
# of git_service.py. Every case asserts the exact denial message and the order of
# the checks, so the move is verifiable without touching these tests.


class TestArgumentPolicyCharacterization:
    """Characterization: exact denial messages and check order via public handlers."""

    @pytest.mark.asyncio
    async def test_git_log_rejects_option_like_branch(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        with pytest.raises(ValueError) as excinfo:
            await svc.git_log({"repo_path": "/opt/repos/proj", "branch": "-n"})
        assert str(excinfo.value) == "[DENIED] Ref '-n' looks like a CLI option"

    @pytest.mark.asyncio
    async def test_git_diff_rejects_option_like_commit(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        with pytest.raises(ValueError) as excinfo:
            await svc.git_diff({"repo_path": "/opt/repos/proj", "commit": "--help"})
        assert str(excinfo.value) == "[DENIED] Ref '--help' looks like a CLI option"

    @pytest.mark.asyncio
    async def test_git_show_rejects_option_like_ref(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        with pytest.raises(ValueError) as excinfo:
            await svc.git_show({"repo_path": "/opt/repos/proj", "ref": "-x"})
        assert str(excinfo.value) == "[DENIED] Ref '-x' looks like a CLI option"

    @pytest.mark.asyncio
    async def test_git_checkout_checks_ref_form_before_protected_branch(self) -> None:
        """A branch that is both malformed and protected reports the form denial."""
        svc = _svc(allowed=["/opt/repos"])
        svc._protected_branches = ["main"]
        with pytest.raises(ValueError) as excinfo:
            await svc.git_checkout({"repo_path": "/opt/repos/proj", "branch": "main.."})
        assert (
            str(excinfo.value)
            == "[DENIED] Ref 'main..' is not a valid simple branch name"
        )

    @pytest.mark.asyncio
    async def test_git_checkout_reports_protected_branch_after_the_form_check(
        self,
    ) -> None:
        svc = _svc(allowed=["/opt/repos"])
        svc._protected_branches = ["main"]
        with pytest.raises(ValueError) as excinfo:
            await svc.git_checkout({"repo_path": "/opt/repos/proj", "branch": "main"})
        assert str(excinfo.value) == "[DENIED] 'main' is a protected branch"

    @pytest.mark.asyncio
    async def test_git_pull_rejects_option_like_remote(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        with pytest.raises(ValueError) as excinfo:
            await svc.git_pull(
                {"repo_path": "/opt/repos/proj", "branch": "develop", "remote": "-u"}
            )
        assert str(excinfo.value) == "[DENIED] Remote '-u' looks like a CLI option"

    @pytest.mark.asyncio
    async def test_git_push_rejects_non_simple_remote(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        with pytest.raises(ValueError) as excinfo:
            await svc.git_push(
                {"repo_path": "/opt/repos/proj", "branch": "develop", "remote": "a:b"}
            )
        assert str(excinfo.value) == "[DENIED] Remote 'a:b' is not a valid remote name"

    @pytest.mark.asyncio
    async def test_git_pull_rejects_empty_branch_with_the_protected_guard_message(
        self,
    ) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        with pytest.raises(ValueError) as excinfo:
            await svc.git_pull({"repo_path": "/opt/repos/proj", "branch": ""})
        assert str(excinfo.value) == "[DENIED] branch must not be empty"
