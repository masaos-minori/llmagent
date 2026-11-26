#!/usr/bin/env python3
"""tests/mcp_servers/git/test_git_write_postconditions.py

Integration suite for the write path: each Git write runs on a real temporary
repository and the Stage 7 postcondition is verified against the fresh
post-operation snapshot the pipeline produces (REQ-006, AC-1, AC-2), plus the
handle-release cases for the five execution paths (REQ-005, AC-5).
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest
from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.format_output import (
    format_add,
    format_checkout,
    format_commit,
    format_pull,
    format_push,
)
from mcp_servers.git.git_models import (
    GitAddRequest,
    GitCheckoutRequest,
    GitCommitRequest,
    GitConfig,
    GitPullRequest,
    GitPushRequest,
)
from mcp_servers.git.git_service import GitService, WriteOutcomeError
from mcp_servers.git.repository_state import RepositoryState
from mcp_servers.git.write_protection_pipeline import (
    PipelineResult,
    WriteProtectionPipeline,
)
from shared.write_outcome import CONFIRMED_NOT_APPLIED, OUTCOME_UNKNOWN

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def repo_dir(tmp_path: Path) -> str:
    """A working repository with one commit and a repository-local author."""
    root = tmp_path / "repo"
    root.mkdir()
    repo = git.Repo.init(str(root))
    with repo.config_writer() as writer:
        writer.set_value("user", "name", "Test Author")
        writer.set_value("user", "email", "test@example.com")
    (root / "README.md").write_text("# test")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    return str(root)


@pytest.fixture()
def origin_remote(repo_dir: str) -> str:
    """A bare repository registered as `origin`; no network access is used."""
    remote_dir = Path(repo_dir).parent / "origin.git"
    git.Repo.init(str(remote_dir), bare=True)
    git.Repo(repo_dir).create_remote("origin", str(remote_dir))
    return str(remote_dir)


def _config(repo_dir: str, remote_url: str) -> GitConfig:
    """Config that allows the test repository and the local bare remote."""
    return GitConfig(
        allowed_repo_paths=[repo_dir],
        read_only=False,
        allowed_remote_urls=[remote_url],
    )


def _run(
    repo_dir: str,
    tool: str,
    make_op: Callable[[RepositoryState], Callable[[], str]],
    *,
    requested_branch: str = "",
    protected_branches: list[str] | None = None,
) -> PipelineResult:
    """Run the pipeline on a real repository and return the result.

    The pre-operation snapshot is closed by this helper, so a handle that is still
    open after the call is the pipeline's own leak, not the caller's.
    """
    with RepositoryState.snapshot(
        repo_dir, protected_branches=protected_branches
    ) as state:
        result = WriteProtectionPipeline(state).run(
            tool,
            make_op(state),
            requested_branch=requested_branch,
            protected_branches=protected_branches,
        )
    assert result.post_state is None or result.post_state._repo is None
    return result


def _assert_rejected_at_stage_7(result: PipelineResult) -> None:
    """Every designed postcondition failure rejects at Stage 7 with the vocabulary outcome."""
    assert result.ok is False
    assert result.rejected_at_stage == "Stage 7"
    assert result.outcome == CONFIRMED_NOT_APPLIED


# ── Per-tool postcondition cases (REQ-006, AC-1, AC-2) ────────────────────────


class TestAddPostcondition:
    def test_passes_when_a_file_is_staged(self, repo_dir: str) -> None:
        req = GitAddRequest(repo_path=repo_dir, paths=["staged.txt"])

        def make_op(state: RepositoryState) -> Callable[[], str]:
            def op() -> str:
                (Path(repo_dir) / "staged.txt").write_text("x")
                return format_add(state.repo, req)

            return op

        result = _run(repo_dir, "git_add", make_op)
        assert result.ok is True
        assert result.post_state is not result.repository_state

    def test_fails_when_nothing_is_staged(self, repo_dir: str) -> None:
        """The designed failure case: the operation reports success, the state shows no staged entry.

        An unchanged tracked file is used so Stage 5's clean-worktree guard still
        passes: staging a new file would make the pre-operation snapshot dirty.
        """
        req = GitAddRequest(repo_path=repo_dir, paths=["README.md"])
        result = _run(
            repo_dir, "git_add", lambda state: lambda: format_add(state.repo, req)
        )
        _assert_rejected_at_stage_7(result)


class TestCommitPostcondition:
    def test_passes_when_head_advances(self, repo_dir: str) -> None:
        req = GitCommitRequest(repo_path=repo_dir, message="second")

        def make_op(state: RepositoryState) -> Callable[[], str]:
            def op() -> str:
                (Path(repo_dir) / "c.txt").write_text("x")
                state.repo.index.add(["c.txt"])
                return format_commit(state.repo, req)

            return op

        result = _run(repo_dir, "git_commit", make_op)
        assert result.ok is True
        assert result.post_state is not result.repository_state

    def test_fails_when_head_does_not_advance(self, repo_dir: str) -> None:
        """The designed failure case: HEAD still points at the pre-operation commit.

        `format_commit` refuses an empty index before the postcondition can run, so
        the failing case is proven by an operation that leaves HEAD unchanged.
        """
        result = _run(repo_dir, "git_commit", lambda state: lambda: "no commit made")
        _assert_rejected_at_stage_7(result)


class TestCheckoutPostcondition:
    def test_passes_when_head_moves_to_the_requested_branch(
        self, repo_dir: str
    ) -> None:
        repo = git.Repo(repo_dir)
        repo.git.branch("develop")
        req = GitCheckoutRequest(repo_path=repo_dir, branch="develop")
        result = _run(
            repo_dir,
            "git_checkout",
            lambda state: lambda: format_checkout(state, req),
            requested_branch="develop",
        )
        assert result.ok is True
        assert result.post_state is not result.repository_state

    def test_fails_when_head_stays_on_the_original_branch(self, repo_dir: str) -> None:
        """The designed failure case: the operation reports success without switching."""
        git.Repo(repo_dir).git.branch("develop")
        result = _run(
            repo_dir,
            "git_checkout",
            lambda state: lambda: "no switch performed",
            requested_branch="develop",
        )
        _assert_rejected_at_stage_7(result)


class TestPullPostcondition:
    def _conflicting_setup(self, repo_dir: str, origin_remote: str) -> str:
        """Put the same file at different commits on the local branch and on origin."""
        repo = git.Repo(repo_dir)
        branch = repo.active_branch.name
        path = Path(repo_dir) / "conflict.txt"
        path.write_text("base")
        repo.index.add(["conflict.txt"])
        repo.index.commit("base")
        repo.git.push("origin", branch)

        clone_dir = Path(repo_dir).parent / "clone"
        clone = git.Repo.clone_from(origin_remote, str(clone_dir))
        (Path(clone.working_dir) / "conflict.txt").write_text("theirs")
        clone.index.add(["conflict.txt"])
        clone.index.commit("theirs")
        clone.git.push("origin", branch)

        path.write_text("ours")
        repo.index.add(["conflict.txt"])
        repo.index.commit("ours")
        return branch

    def test_passes_without_conflicts(self, repo_dir: str, origin_remote: str) -> None:
        repo = git.Repo(repo_dir)
        branch = repo.active_branch.name
        repo.git.push("origin", branch)
        req = GitPullRequest(repo_path=repo_dir, remote="origin", branch=branch)
        cfg = _config(repo_dir, origin_remote)
        result = _run(
            repo_dir,
            "git_pull",
            lambda state: lambda: format_pull(state, req, cfg),
            requested_branch=branch,
        )
        assert result.ok is True
        assert result.post_state is not result.repository_state

    def test_fails_on_unmerged_blobs(self, repo_dir: str, origin_remote: str) -> None:
        """The designed failure case: a conflicted merge leaves unmerged blobs.

        `git pull` exits non-zero on a conflict, so `format_pull` raises before Stage 7
        can run; the conflicted index is created through the same remote and Stage 7 is
        what proves the postcondition branch.
        """
        branch = self._conflicting_setup(repo_dir, origin_remote)

        def make_op(state: RepositoryState) -> Callable[[], str]:
            def op() -> str:
                state.repo.git.fetch("origin")
                try:
                    state.repo.git.merge("--no-commit", f"origin/{branch}")
                except git.exc.GitCommandError:
                    pass
                return "conflicted merge"

            return op

        result = _run(repo_dir, "git_pull", make_op, requested_branch=branch)
        _assert_rejected_at_stage_7(result)

    def test_pull_raises_when_the_merge_conflicts(
        self, repo_dir: str, origin_remote: str
    ) -> None:
        """The formatter path reports the conflict as an execution failure, not a Stage 7 rejection."""
        branch = self._conflicting_setup(repo_dir, origin_remote)
        req = GitPullRequest(repo_path=repo_dir, remote="origin", branch=branch)
        cfg = _config(repo_dir, origin_remote)
        with RepositoryState.snapshot(repo_dir) as state:
            with pytest.raises(GitServiceError):
                format_pull(state, req, cfg)


class TestPushPostcondition:
    def test_passes_when_the_remote_ref_equals_local_head(
        self, repo_dir: str, origin_remote: str
    ) -> None:
        req = GitPushRequest(repo_path=repo_dir, remote="origin", branch="master")
        cfg = _config(repo_dir, origin_remote)
        result = _run(
            repo_dir,
            "git_push",
            lambda state: lambda: format_push(state, req, cfg),
            requested_branch="master",
        )
        assert result.ok is True
        assert result.post_state is not result.repository_state

    def test_fails_when_the_remote_ref_differs_from_local_head(
        self, repo_dir: str, origin_remote: str
    ) -> None:
        """The designed failure case: local HEAD advances past the pushed ref."""
        repo = git.Repo(repo_dir)
        branch = repo.active_branch.name
        repo.git.push("origin", branch)
        (Path(repo_dir) / "next.txt").write_text("x")
        repo.index.add(["next.txt"])
        repo.index.commit("second")
        result = _run(
            repo_dir,
            "git_push",
            lambda state: lambda: "no push performed",
            requested_branch=branch,
        )
        _assert_rejected_at_stage_7(result)


# ── Handle release on the five execution paths (REQ-005, AC-5) ────────────────


def _snapshot_spy() -> tuple[list[RepositoryState], patch]:
    """Record every RepositoryState the service opens during a call."""
    recorded: list[RepositoryState] = []
    real = RepositoryState.snapshot

    def spy(*args, **kwargs) -> RepositoryState:
        state = real(*args, **kwargs)
        recorded.append(state)
        return state

    return recorded, patch.object(RepositoryState, "snapshot", staticmethod(spy))


def _service(repo_dir: str, remote_url: str) -> GitService:
    cfg = _config(repo_dir, remote_url)
    return GitService(
        allowed_repo_paths=cfg.allowed_repo_paths,
        read_only=cfg.read_only,
        max_log_entries=cfg.max_log_entries,
        _config=cfg,
    )


class TestHandleReleaseOnEveryPath:
    """Each path must release the handle the service opened (AC-5).

    The write tools require a clean worktree at Stage 5, so the passing path uses a
    branch switch rather than staging a new file: staging would make the
    pre-operation snapshot dirty.
    """

    @pytest.mark.asyncio
    async def test_success_path_releases_the_handle(self, repo_dir: str) -> None:
        git.Repo(repo_dir).git.branch("develop")
        recorded, spy = _snapshot_spy()
        svc = _service(repo_dir, "")
        with spy:
            result = await svc.git_checkout(
                {"repo_path": repo_dir, "branch": "develop"}
            )
        assert "[DENIED]" not in result
        assert recorded
        assert all(state._repo is None for state in recorded)

    @pytest.mark.asyncio
    async def test_policy_rejection_releases_the_handle(self, repo_dir: str) -> None:
        recorded, spy = _snapshot_spy()
        cfg = _config(repo_dir, "")
        svc = GitService(
            allowed_repo_paths=cfg.allowed_repo_paths,
            read_only=cfg.read_only,
            max_log_entries=cfg.max_log_entries,
            protected_branches=["master"],
            _config=cfg,
        )
        with spy:
            with pytest.raises(ValueError, match="DENIED"):
                await svc.git_commit({"repo_path": repo_dir, "message": "denied"})
        assert recorded
        assert all(state._repo is None for state in recorded)

    @pytest.mark.asyncio
    async def test_dry_run_releases_the_handle(self, repo_dir: str) -> None:
        recorded, spy = _snapshot_spy()
        svc = _service(repo_dir, "")
        with spy:
            result = await svc.git_commit(
                {"repo_path": repo_dir, "message": "dry", "dry_run": True}
            )
        assert "[DRY RUN]" in result
        assert recorded
        assert all(state._repo is None for state in recorded)

    @pytest.mark.asyncio
    async def test_exception_path_releases_the_handle(self, repo_dir: str) -> None:
        recorded, spy = _snapshot_spy()
        svc = _service(repo_dir, "")
        with spy:
            # Nothing staged: the formatter raises before Stage 7 can run.
            with pytest.raises(GitServiceError):
                await svc.git_commit({"repo_path": repo_dir, "message": "empty"})
        assert recorded
        assert all(state._repo is None for state in recorded)

    @pytest.mark.asyncio
    async def test_timeout_path_releases_the_handle(
        self, repo_dir: str, origin_remote: str
    ) -> None:
        """The deadline path releases the handle and reports the outcome as unknown.

        The process-group termination itself is covered by
        `test_git_service_dispatch.py` (procedure 09); this case asserts the handle
        lifecycle on the timeout path.
        """
        recorded, spy = _snapshot_spy()
        cfg = _config(repo_dir, origin_remote)
        svc = GitService(
            allowed_repo_paths=cfg.allowed_repo_paths,
            read_only=cfg.read_only,
            max_log_entries=cfg.max_log_entries,
            _config=cfg,
        )
        proc = MagicMock()
        proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=1)
        proc.pid = 4242
        proc.returncode = -15
        with (
            spy,
            patch("mcp_servers.git.format_output.subprocess.Popen", return_value=proc),
            patch("mcp_servers.git.format_output.os.killpg") as killpg,
        ):
            with pytest.raises(WriteOutcomeError) as exc_info:
                await svc.git_pull(
                    {"repo_path": repo_dir, "remote": "origin", "branch": "master"}
                )
        assert killpg.call_args[0][0] == proc.pid
        assert exc_info.value.outcome == OUTCOME_UNKNOWN
        assert recorded
        assert all(state._repo is None for state in recorded)

    @pytest.mark.asyncio
    async def test_repeated_execution_does_not_accumulate_handles(
        self, repo_dir: str
    ) -> None:
        """Running the same write ten times leaves no open handle."""
        git.Repo(repo_dir).git.branch("develop")
        recorded, spy = _snapshot_spy()
        svc = _service(repo_dir, "")
        with spy:
            for _ in range(10):
                await svc.git_checkout({"repo_path": repo_dir, "branch": "develop"})
        # Each call opens the pre-operation snapshot, the refreshed read inside
        # `format_checkout`, and Stage 7's post-operation snapshot.
        assert len(recorded) >= 10
        assert all(state._repo is None for state in recorded)
