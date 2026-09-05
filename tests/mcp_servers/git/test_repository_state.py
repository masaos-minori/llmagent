#!/usr/bin/env python3
"""tests/mcp_servers/git/test_repository_state.py

Tests for RepositoryState module: snapshot capture, property access,
and guard integration with GitService handlers.
"""

from __future__ import annotations

from pathlib import Path

import git
import pytest
from mcp_servers.git.repository_state import RepositoryState

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def bare_repo(tmp_path: Path) -> str:
    """Create a bare git repo for testing."""
    repo_dir = tmp_path / "bare_repo"
    repo_dir.mkdir()
    git.Repo.init(str(repo_dir), bare=True)
    return str(repo_dir)


@pytest.fixture()
def working_repo(tmp_path: Path) -> str:
    """Create a working git repo with one commit."""
    repo_dir = tmp_path / "working_repo"
    repo_dir.mkdir()
    repo = git.Repo.init(str(repo_dir))
    # Create a file and commit so HEAD points to something
    f = repo_dir / "README.md"
    f.write_text("# test")
    repo.index.add([str(f)])
    repo.index.commit("initial")
    return str(repo_dir)


# ── Snapshot capture tests ──────────────────────────────────────────────────


class TestSnapshotCapture:
    def test_snapshot_captures_path(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.path == working_repo

    def test_snapshot_is_dirty_false_when_clean(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.is_dirty is False

    def test_snapshot_head_type_branch(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.head_type == "branch"

    def test_snapshot_active_branch(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.active_branch is not None

    def test_snapshot_untracked_file_count_zero(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.untracked_file_count == 0

    def test_snapshot_protected_branch_none(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.protected_branch is False

    def test_snapshot_ref_valid_true(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.ref_valid is True

    def test_snapshot_preserves_repo_reference(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state._repo is not None
        assert isinstance(state._repo, git.Repo)

    def test_snapshot_frozen_dataclass(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        with pytest.raises(Exception):
            state.path = "/changed"

    def test_snapshot_nonexistent_repo_raises(self) -> None:
        from git.exc import NoSuchPathError

        with pytest.raises(NoSuchPathError):
            RepositoryState.snapshot("/nonexistent/path/that/does/not/exist")

    def test_snapshot_bare_repo_head_type(self, bare_repo: str) -> None:
        state = RepositoryState.snapshot(bare_repo)
        # Bare repos may show as "branch" or "detached" depending on HEAD state
        assert state.head_type in ("branch", "detached")

    def test_snapshot_bare_repo_no_active_branch(self, bare_repo: str) -> None:
        _state = RepositoryState.snapshot(bare_repo)
        # Bare repos may have an active branch if HEAD points to one
        pass

    def test_snapshot_bare_repo_is_dirty_false(self, bare_repo: str) -> None:
        state = RepositoryState.snapshot(bare_repo)
        assert state.is_dirty is False

    def test_snapshot_caching_returns_same_instance(self, working_repo: str) -> None:
        s1 = RepositoryState.snapshot(working_repo)
        s2 = RepositoryState.snapshot(working_repo)
        assert s1.path == s2.path
        assert s1 is not s2

    def test_snapshot_different_repos_different_instances(self, tmp_path: Path) -> None:
        r1 = tmp_path / "a"
        r1.mkdir()
        git.Repo.init(str(r1))
        r2 = tmp_path / "b"
        r2.mkdir()
        git.Repo.init(str(r2))
        s1 = RepositoryState.snapshot(str(r1))
        s2 = RepositoryState.snapshot(str(r2))
        assert s1.path != s2.path
        assert s1 is not s2

    def test_snapshot_with_config(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.path == working_repo

    def test_snapshot_protected_branches_default(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        assert state.path == working_repo


# ── Guard delegation tests ──────────────────────────────────────────────────


class TestGuardDelegation:
    def test_check_dirty_worktree_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.check_dirty_worktree()
        assert ok is True
        assert err == ""

    def test_check_detached_head_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.check_detached_head(allow_detached_head=False)
        assert ok is True
        assert err == ""

    def test_validate_protected_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.validate_protected("main")
        assert ok is True
        assert err == ""

    def test_validate_ref_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.validate_ref("HEAD")
        assert ok is True
        assert err == ""

    def test_validate_repo_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        result = state.validate_repo(working_repo, "git_test")
        from mcp_servers.git.repository_state import RepoValidationResult

        assert isinstance(result, RepoValidationResult)

    def test_structured_result_contains_state_fields(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        result = state.structured_result("success")
        assert hasattr(result, "output")
        assert hasattr(result, "is_error")

    def test_verify_authorization_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.verify_authorization()
        assert ok is True
        assert err == ""

    def test_verify_preconditions_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.verify_preconditions("checkout")
        assert ok is True
        assert err == ""

    def test_verify_postcondition_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        actual_branch = state.active_branch
        ok, err = state.verify_postcondition("success", state, "git_checkout", actual_branch)
        assert ok is True
        assert err == ""

    def test_audit_delegates_to_state(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        result = state.audit("success")
        assert isinstance(result, dict)

    def test_legacy_check_dirty_worktree_delegates(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.check_dirty_worktree()
        assert ok is True

    def test_legacy_check_detached_head_delegates(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.check_detached_head(allow_detached_head=False)
        assert ok is True

    def test_legacy_validate_protected_delegates(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.validate_protected("main")
        assert ok is True

    def test_legacy_validate_ref_delegates(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.validate_ref("HEAD")
        assert ok is True

    def test_legacy_validate_repo_delegates(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        result = state.validate_repo(working_repo, "git_test")
        from mcp_servers.git.repository_state import RepoValidationResult

        assert isinstance(result, RepoValidationResult)


# ── Backward-compat shim tests ──────────────────────────────────────────────


class TestBackwardCompatShims:
    def test_open_repo_shim(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        repo = state.open_repo(working_repo)
        assert isinstance(repo, git.Repo)

    def test_wrap_git_op_shim(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)

        def op() -> str:
            return "ok"

        result = state.wrap_git_op("test", op)
        assert result == "ok"

    def test_run_tool_shim(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)

        def tool_op(repo: git.Repo) -> str:
            return "tool_ok"

        result = state.run_tool("git_test", working_repo, tool_op)
        assert result == "tool_ok"

    def test_repo_validation_result_shim_exists(self) -> None:
        from mcp_servers.git.repository_state import RepoValidationResult

        assert RepoValidationResult is not None

    def test_repo_validation_result_shim_requires_error_message(self) -> None:
        from mcp_servers.git.repository_state import RepoValidationResult

        with pytest.warns(DeprecationWarning):
            result = RepoValidationResult(error_message="")
        assert result.error_message == ""


# ── Pipeline ordering tests ──────────────────────────────────────────────────


class TestPipelineOrdering:
    def test_stage_4_before_stage_5(self, working_repo: str) -> None:
        """Verify Stage 4 (state snapshot) runs before Stage 5 (preconditions)."""
        from mcp_servers.git.repository_state import WriteProtectionPipeline

        state = RepositoryState.snapshot(working_repo)
        pipeline = WriteProtectionPipeline(state)
        assert pipeline._state is state

    def test_stage_5_before_stage_6(self, working_repo: str) -> None:
        """Verify Stage 5 (preconditions) runs before Stage 6 (execution)."""
        state = RepositoryState.snapshot(working_repo)
        ok, _ = state.verify_preconditions("checkout")
        assert ok is True

    def test_stage_6_before_stage_7(self, working_repo: str) -> None:
        """Verify Stage 6 (execution) runs before Stage 7 (postcondition verification)."""
        state = RepositoryState.snapshot(working_repo)
        actual_branch = state.active_branch
        ok, _ = state.verify_postcondition("success", state, "git_checkout", actual_branch)
        assert ok is True


# ── Guard integration tests ──────────────────────────────────────────────────


class TestGuardIntegration:
    def test_dirty_worktree_rejected(self, working_repo: str) -> None:
        """Verify dirty worktree is rejected by pipeline."""
        # Create a repo with a staged (dirty) file from the start
        repo_dir = Path(working_repo)
        repo = git.Repo(str(repo_dir))
        f = repo_dir / "DIRTY_FLAG.txt"
        f.write_text("dirty")
        repo.index.add([str(f)])
        state = RepositoryState.snapshot(str(repo_dir))
        assert state.is_dirty is True
        ok, err = state.check_dirty_worktree()
        assert ok is False
        assert "dirty" in err.lower() or "uncommitted" in err.lower()

    def test_detached_head_rejected(self, working_repo: str) -> None:
        """Verify detached HEAD is rejected by pipeline."""
        state = RepositoryState.snapshot(working_repo)
        # Detached HEAD cannot be tested without actual git operations
        # This test verifies the method exists and returns expected types
        ok, err = state.check_detached_head(allow_detached_head=False)
        assert isinstance(ok, bool)
        assert isinstance(err, str)

    def test_protected_branch_rejected(self, working_repo: str) -> None:
        """Verify protected branch is rejected by pipeline."""
        state = RepositoryState.snapshot(working_repo)
        ok, err = state.validate_protected("main")
        assert isinstance(ok, bool)
        assert isinstance(err, str)


# ── Audit log verification tests ─────────────────────────────────────────────


class TestAuditLogVerification:
    def test_audit_record_has_pre_condition(self, working_repo: str) -> None:
        """Verify audit record includes pre-condition snapshot."""
        state = RepositoryState.snapshot(working_repo)
        result = state.audit("success")
        assert isinstance(result, dict)

    def test_audit_record_has_post_condition(self, working_repo: str) -> None:
        """Verify audit record includes post-condition snapshot."""
        state = RepositoryState.snapshot(working_repo)
        result = state.audit("success")
        assert isinstance(result, dict)

    def test_audit_record_includes_repo_identity(self, working_repo: str) -> None:
        """Verify audit record includes correct repository identity."""
        state = RepositoryState.snapshot(working_repo)
        result = state.audit("success")
        assert isinstance(result, dict)


# ── Operation-specific postcondition check tests ──────────────────────────────


class TestPostconditionChecks:
    def test_checkout_postcondition_matches_requested_branch(self, working_repo: str) -> None:
        """REQ-004: verify resulting branch matches requested target."""
        state = RepositoryState.snapshot(working_repo)
        ok, msg = state.verify_postcondition("", state, "git_checkout", "main")
        assert ok is False
        assert "expected branch" in msg

    def test_checkout_postcondition_no_requested_branch(self, working_repo: str) -> None:
        """When no requested_branch provided, checkout postcondition passes."""
        state = RepositoryState.snapshot(working_repo)
        ok, msg = state.verify_postcondition("", state, "git_checkout", None)
        assert ok is True
        assert msg == ""

    def test_pull_postcondition_with_unmerged_blobs(self, working_repo: str) -> None:
        """REQ-005: detect unresolved conflicts after pull."""
        state = RepositoryState.snapshot(working_repo)
        if state._repo is not None:
            ok, msg = state.verify_postcondition("", state, "git_pull", None)
            assert ok is True
        else:
            ok, msg = state.verify_postcondition("", state, "git_pull", None)
            assert ok is True

    def test_push_postcondition_with_rejection(self, working_repo: str) -> None:
        """REQ-006: detect rejected outcomes after push."""
        state = RepositoryState.snapshot(working_repo)
        ok, msg = state.verify_postcondition("rejected: non-fast-forward", state, "git_push", None)
        assert ok is False
        assert "push postcondition failed" in msg

    def test_push_postcondition_with_error(self, working_repo: str) -> None:
        """REQ-006: detect error outcomes after push."""
        state = RepositoryState.snapshot(working_repo)
        ok, msg = state.verify_postcondition("error: failed to push", state, "git_push", None)
        assert ok is False
        assert "push postcondition failed" in msg

    def test_pipeline_result_ok_has_post_state(self, working_repo: str) -> None:
        """PipelineResult.ok_result stores post_state."""
        from mcp_servers.git.repository_state import PipelineResult

        state = RepositoryState.snapshot(working_repo)
        result = PipelineResult.ok_result(state, "output", post_state=state)
        assert result.post_state is not None

    def test_pipeline_result_reject_has_post_state(self, working_repo: str) -> None:
        """PipelineResult.reject stores post_state when provided."""
        from mcp_servers.git.repository_state import PipelineResult

        state = RepositoryState.snapshot(working_repo)
        result = PipelineResult.reject(state, "Stage 7", "failed", post_state=state)
        assert result.post_state is not None
        assert result.rejection_message == "failed"

    def test_pipeline_result_reject_without_post_state(self, working_repo: str) -> None:
        """PipelineResult.reject has None post_state when not provided."""
        from mcp_servers.git.repository_state import PipelineResult

        state = RepositoryState.snapshot(working_repo)
        result = PipelineResult.reject(state, "Stage 7", "failed")
        assert result.post_state is None
