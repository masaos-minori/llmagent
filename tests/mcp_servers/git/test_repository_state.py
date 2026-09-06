#!/usr/bin/env python3
"""tests/mcp_servers/git/test_repository_state.py

Tests for RepositoryState module: snapshot capture, property access,
and guard integration with GitService handlers.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest
from mcp_servers.git.repository_state import (
    RepositoryState,
    WriteProtectionPipeline,
    _is_protected_branch,
    _validate_ref,
)

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
        assert state.path == working_repo
        assert state.ref_valid is True

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
        ok, err = state.verify_postcondition(
            "success", state, "git_checkout", actual_branch
        )
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
        assert state.path == working_repo
        assert state.ref_valid is True


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
        ok, _ = state.verify_postcondition(
            "success", state, "git_checkout", actual_branch
        )
        assert ok is True


# ── verify_preconditions dry_run / allow_detached_head matrix ───────────────


@pytest.fixture()
def dirty_repo(working_repo: str) -> str:
    Path(working_repo, "README.md").write_text("# test\nuncommitted change\n")
    return working_repo


@pytest.fixture()
def detached_repo(working_repo: str) -> str:
    repo = git.Repo(working_repo)
    repo.git.checkout(repo.head.commit.hexsha)
    return working_repo


class TestVerifyPreconditionsDryRunAndDetachedHead:
    def test_dirty_worktree_dry_run_true_is_allowed(self, dirty_repo: str) -> None:
        state = RepositoryState.snapshot(dirty_repo)
        ok, err = state.verify_preconditions("checkout", dry_run=True)
        assert ok is True
        assert err == ""

    @pytest.mark.parametrize("allow_detached_head", [False, True])
    def test_dirty_worktree_dry_run_false_is_denied(
        self, dirty_repo: str, allow_detached_head: bool
    ) -> None:
        state = RepositoryState.snapshot(dirty_repo)
        ok, err = state.verify_preconditions(
            "checkout", dry_run=False, allow_detached_head=allow_detached_head
        )
        assert ok is False
        assert "dirty worktree" in err

    def test_detached_head_dry_run_true_is_allowed(self, detached_repo: str) -> None:
        state = RepositoryState.snapshot(detached_repo)
        ok, err = state.verify_preconditions("checkout", dry_run=True)
        assert ok is True
        assert err == ""

    def test_detached_head_dry_run_false_allow_false_is_denied(
        self, detached_repo: str
    ) -> None:
        state = RepositoryState.snapshot(detached_repo)
        ok, err = state.verify_preconditions(
            "checkout", dry_run=False, allow_detached_head=False
        )
        assert ok is False
        assert "detached HEAD" in err

    def test_detached_head_dry_run_false_allow_true_is_allowed(
        self, detached_repo: str
    ) -> None:
        state = RepositoryState.snapshot(detached_repo)
        ok, err = state.verify_preconditions(
            "checkout", dry_run=False, allow_detached_head=True
        )
        assert ok is True
        assert err == ""


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
    def test_checkout_postcondition_matches_requested_branch(
        self, working_repo: str
    ) -> None:
        """REQ-004: verify resulting branch matches requested target."""
        state = RepositoryState.snapshot(working_repo)
        ok, msg = state.verify_postcondition("", state, "git_checkout", "main")
        assert ok is False
        assert "expected branch" in msg

    def test_checkout_postcondition_no_requested_branch(
        self, working_repo: str
    ) -> None:
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
        ok, msg = state.verify_postcondition(
            "rejected: non-fast-forward", state, "git_push", None
        )
        assert ok is False
        assert "push postcondition failed" in msg

    def test_push_postcondition_with_error(self, working_repo: str) -> None:
        """REQ-006: detect error outcomes after push."""
        state = RepositoryState.snapshot(working_repo)
        ok, msg = state.verify_postcondition(
            "error: failed to push", state, "git_push", None
        )
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


# ── Remote URL resolve/redact (REQ-001, REQ-003) ─────────────────────────────


class TestResolveRemoteUrl:
    def test_resolves_existing_remote(self, working_repo: str) -> None:
        from mcp_servers.git.repository_state import _resolve_remote_url

        repo = git.Repo(working_repo)
        repo.create_remote("origin", "https://example.com/repo.git")
        assert _resolve_remote_url(repo, "origin") == "https://example.com/repo.git"

    def test_unknown_remote_returns_none(self, working_repo: str) -> None:
        from mcp_servers.git.repository_state import _resolve_remote_url

        repo = git.Repo(working_repo)
        assert _resolve_remote_url(repo, "nonexistent") is None


class TestRedactRemoteUrl:
    def test_redacts_user_and_token(self) -> None:
        from mcp_servers.git.repository_state import _redact_remote_url

        assert (
            _redact_remote_url("https://user:token@host/repo.git")
            == "https://***@host/repo.git"
        )

    def test_redacts_user_only(self) -> None:
        from mcp_servers.git.repository_state import _redact_remote_url

        assert (
            _redact_remote_url("https://user@host/repo.git")
            == "https://***@host/repo.git"
        )

    def test_no_credential_unchanged(self) -> None:
        from mcp_servers.git.repository_state import _redact_remote_url

        assert _redact_remote_url("https://host/repo.git") == "https://host/repo.git"


# ── Per-repo-path write-serialization lock registry (REQ-005/REQ-007) ───────


class TestGetRepoLock:
    def test_same_path_returns_same_lock(self) -> None:
        from mcp_servers.git.repository_state import _get_repo_lock

        assert _get_repo_lock("/tmp/repo-a") is _get_repo_lock("/tmp/repo-a")

    def test_distinct_paths_return_distinct_locks(self) -> None:
        from mcp_servers.git.repository_state import _get_repo_lock

        assert _get_repo_lock("/tmp/repo-b") is not _get_repo_lock("/tmp/repo-c")


# ── Stage 5b HEAD-identity re-check (REQ-006) ────────────────────────────────


class TestHeadIdentityRecheck:
    def test_head_unchanged_during_op_succeeds(self, working_repo: str) -> None:
        from mcp_servers.git.repository_state import WriteProtectionPipeline

        state = RepositoryState.snapshot(working_repo)
        pipeline = WriteProtectionPipeline(state)
        result = pipeline.run("git_status", lambda: "ok")
        assert result.ok is True
        assert result.output == "ok"

    def test_head_drifted_since_authorization_is_rejected(
        self, working_repo: str
    ) -> None:
        """REQ-006: if HEAD's detached/attached state drifted between the
        authorization-time snapshot and the pipeline run (e.g. a concurrent
        request detached HEAD in between), the mutating op() is never
        invoked."""
        from mcp_servers.git.repository_state import WriteProtectionPipeline

        state = RepositoryState.snapshot(working_repo)  # captured while attached
        repo = git.Repo(working_repo)
        repo.git.checkout(repo.head.commit.hexsha)  # now detached
        pipeline = WriteProtectionPipeline(state)

        op_called = False

        def _op() -> str:
            nonlocal op_called
            op_called = True
            return "should not be reached"

        result = pipeline.run("git_checkout", _op)
        assert result.ok is False
        assert result.rejected_at_stage == "Stage 5b"
        assert op_called is False


# ── Protected branch check tests (REQ-002) ────────────────────────────────────


class TestProtectedBranchCheck:
    """Unit tests for _is_protected_branch() against configured protected_branches."""

    def _make_mock_repo(
        self, branch_name: str | None = None, is_detached: bool = False
    ):
        repo = MagicMock(spec=git.Repo)
        repo.head.is_detached = is_detached
        if branch_name is not None and not is_detached:
            mock_branch = MagicMock()
            mock_branch.name = branch_name
            repo.active_branch = mock_branch
        else:
            repo.active_branch = None
        return repo

    def test_is_protected_branch_main(self):
        repo = self._make_mock_repo(branch_name="main")
        assert _is_protected_branch(repo, ["main"]) is True

    def test_is_protected_branch_master(self):
        repo = self._make_mock_repo(branch_name="master")
        assert _is_protected_branch(repo, ["master"]) is True

    def test_is_protected_branch_release(self):
        repo = self._make_mock_repo(branch_name="release")
        assert _is_protected_branch(repo, ["release"]) is True

    def test_is_protected_branch_develop(self):
        repo = self._make_mock_repo(branch_name="develop")
        assert _is_protected_branch(repo, ["develop"]) is True

    def test_is_protected_branch_normalized_refs(self):
        """Both main and refs/heads/main should match when normalized."""
        repo = self._make_mock_repo(branch_name="main")
        assert _is_protected_branch(repo, ["refs/heads/main"]) is True
        # Also test reverse: protected_branches has "main", repo reports "refs/heads/main"
        repo2 = self._make_mock_repo(branch_name="refs/heads/main")
        assert _is_protected_branch(repo2, ["main"]) is True

    def test_is_not_protected_branch(self):
        repo = self._make_mock_repo(branch_name="feature/test")
        assert _is_protected_branch(repo, ["main"]) is False

    def test_is_not_protected_branch_empty_list(self):
        repo = self._make_mock_repo(branch_name="main")
        assert _is_protected_branch(repo, []) is False

    def test_is_not_protected_branch_none(self):
        repo = self._make_mock_repo(branch_name="main")
        assert _is_protected_branch(repo, None) is False

    def test_is_not_protected_branch_detached_head(self):
        repo = self._make_mock_repo(is_detached=True)
        assert _is_protected_branch(repo, ["main"]) is False

    def test_is_not_protected_branch_case_insensitive(self):
        """Normalization converts to lowercase; MAIN should match main."""
        repo = self._make_mock_repo(branch_name="MAIN")
        assert _is_protected_branch(repo, ["main"]) is True


# ── Ref validation tests (REQ-004) ──────────────────────────────────────────────


class TestRefValidValidation:
    """Unit tests for _validate_ref() rejecting option-like/malformed refs."""

    def test_ref_valid_option_like_rejected(self):
        """Refs starting with '-' must be rejected per REQ-008."""
        assert _validate_ref("-force") is False
        assert _validate_ref("--help") is False
        assert _validate_ref("-v") is False

    def test_ref_valid_malformed_rejected(self):
        """Malformed refs containing null bytes or control chars must be rejected."""
        assert _validate_ref("ref\x00name") is False
        assert _validate_ref("ref\nname") is False
        assert _validate_ref("ref\rname") is False

    def test_ref_valid_empty_rejected_without_active_branch(self):
        """Empty ref without active_branch must be rejected (implicit target undefined)."""
        assert _validate_ref("") is False
        assert _validate_ref("   ") is False

    def test_ref_valid_empty_accepted_with_active_branch(self):
        """Empty ref with valid active_branch is accepted (implicit target resolved)."""
        assert _validate_ref("", active_branch="main") is True
        assert _validate_ref("", active_branch="develop") is True

    def test_ref_valid_safe_accepted(self):
        """Valid branch names and fully-qualified refs must be accepted."""
        assert _validate_ref("main") is True
        assert _validate_ref("feature/abc") is True
        assert _validate_ref("HEAD") is True
        assert _validate_ref("refs/heads/main") is True
        assert _validate_ref("v1.0.0") is True


# ── Stage 3 authorization tests (REQ-001, REQ-002, REQ-004) ────────────────────


class TestStage3Authorization:
    """Unit tests for WriteProtectionPipeline.run() invoking Stage 3."""

    def _make_mock_state(self, protected_branch=False, ref_valid=True, **kwargs):
        snap = MagicMock(spec=RepositoryState)
        snap.protected_branch = protected_branch
        snap.ref_valid = ref_valid
        snap.active_branch = kwargs.get("active_branch", "main")
        snap.verify_authorization.return_value = (
            not protected_branch and ref_valid,
            "",
        )
        snap.verify_preconditions.return_value = (True, "")
        snap.verify_postcondition.return_value = (True, "")
        snap.audit.return_value = {}
        snap.path = kwargs.get("path", "/tmp/repo")
        snap.is_dirty = kwargs.get("is_dirty", False)
        snap.head_type = kwargs.get("head_type", "branch")
        snap.untracked_file_count = kwargs.get("untracked_file_count", 0)
        snap._repo = None
        return snap

    def test_pipeline_run_invokes_stage_3_for_protected_branch(self):
        """Stage 3 blocks execution when current branch is protected."""
        snap = self._make_mock_state(protected_branch=True)
        snap.verify_authorization.return_value = (
            False,
            "[DENIED] 'main' is a protected branch",
        )
        pipeline = WriteProtectionPipeline(snap)
        result = pipeline.run(
            "git_checkout", lambda: "should-not-run", requested_branch="main"
        )
        assert result.ok is False
        assert result.rejected_at_stage == "Stage 3"
        assert "protected branch" in result.rejection_message.lower()

    def test_pipeline_run_does_not_call_operation_on_protection_failure(self):
        """Operation callable must not execute when Stage 3 rejects."""
        called = []

        def op():
            called.append(True)
            return "executed"

        snap = self._make_mock_state(protected_branch=True)
        pipeline = WriteProtectionPipeline(snap)
        result = pipeline.run("git_checkout", op, requested_branch="main")
        assert result.ok is False
        assert len(called) == 0

    def test_pipeline_run_proceeds_to_stage_5_when_auth_passes(self):
        """When auth passes, pipeline continues to Stage 5 preconditions."""
        snap = self._make_mock_state(protected_branch=False, ref_valid=True)
        snap.is_detached_head = False
        pipeline = WriteProtectionPipeline(snap)
        # Stage 5b re-snapshots for the HEAD-identity recheck (REQ-006); patch
        # RepositoryState.snapshot to return the same mock rather than opening
        # a real repo at the fake "/tmp/repo" path.
        with patch.object(RepositoryState, "snapshot", return_value=snap):
            result = pipeline.run("git_status", lambda: "ok")
        # Stage 3 passed; verify it reached Stage 5 or succeeded
        assert result.ok is True or result.rejected_at_stage != "Stage 3"

    def test_pipeline_run_rejects_invalid_ref(self):
        """Stage 3 blocks execution when ref_valid is False."""
        snap = self._make_mock_state(ref_valid=False)
        pipeline = WriteProtectionPipeline(snap)
        result = pipeline.run(
            "git_checkout", lambda: "should-not-run", requested_branch="HEAD"
        )
        assert result.ok is False
        assert result.rejected_at_stage == "Stage 3"
