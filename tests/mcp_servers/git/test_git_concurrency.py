#!/usr/bin/env python3
"""tests/mcp_servers/git/test_git_concurrency.py

Tests for WriteProtectionPipeline.run()'s per-repo-path write-serialization
lock (REQ-005) and Stage 5b HEAD-identity re-check (REQ-006).
"""

from __future__ import annotations

import threading
from pathlib import Path

import git
import pytest
from mcp_servers.git.repository_state import RepositoryState, WriteProtectionPipeline

# ── Fixtures ────────────────────────────────────────────────────────────────


def _make_repo(path: Path) -> str:
    """Create a working repo on a non-protected branch ("develop"), clean."""
    path.mkdir()
    repo = git.Repo.init(str(path))
    (path / "README.md").write_text("# test")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    repo.git.checkout("-b", "develop")
    return str(path)


@pytest.fixture()
def repo_a(tmp_path: Path) -> str:
    return _make_repo(tmp_path / "repo_a")


@pytest.fixture()
def repo_b(tmp_path: Path) -> str:
    return _make_repo(tmp_path / "repo_b")


# ── Same-repo-path serialization (REQ-005, AC-4) ─────────────────────────────


class TestSameRepoPathSerialization:
    def test_second_thread_op_waits_for_first(self, repo_a: str) -> None:
        events: list[str] = []
        lock = threading.Lock()
        first_started = threading.Event()
        release_first = threading.Event()

        def _op_first() -> str:
            with lock:
                events.append("first-start")
            first_started.set()
            release_first.wait(timeout=5)
            with lock:
                events.append("first-end")
            return "first"

        def _op_second() -> str:
            with lock:
                events.append("second-start")
            with lock:
                events.append("second-end")
            return "second"

        def _run_first() -> None:
            state = RepositoryState.snapshot(repo_a)
            WriteProtectionPipeline(state).run("git_status", _op_first)

        def _run_second() -> None:
            first_started.wait(timeout=5)
            state = RepositoryState.snapshot(repo_a)
            WriteProtectionPipeline(state).run("git_status", _op_second)

        t1 = threading.Thread(target=_run_first)
        t2 = threading.Thread(target=_run_second)
        t1.start()
        t2.start()
        # Give t2 a moment to reach and block on the same repo-path lock
        # before releasing t1 — proves t2's op() cannot start until t1's
        # pipeline body (holding the lock) completes.
        first_started.wait(timeout=5)
        import time

        time.sleep(0.05)
        with lock:
            assert "second-start" not in events
        release_first.set()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert events.index("first-start") < events.index("first-end")
        assert events.index("first-end") < events.index("second-start")
        assert events.index("second-start") < events.index("second-end")


# ── Cross-repo-path independence (REQ-005, AC-5) ─────────────────────────────


class TestCrossRepoPathIndependence:
    def test_distinct_repo_paths_are_not_serialized(
        self, repo_a: str, repo_b: str
    ) -> None:
        both_running = threading.Event()
        a_started = threading.Event()
        b_started = threading.Event()
        release = threading.Event()
        results: dict[str, bool] = {}

        def _op(started: threading.Event) -> str:
            started.set()
            # Wait until the other thread has also started, proving neither
            # blocked on the other's lock (they are keyed by distinct paths).
            release.wait(timeout=5)
            return "ok"

        def _run(repo_path: str, started: threading.Event) -> None:
            state = RepositoryState.snapshot(repo_path)
            result = WriteProtectionPipeline(state).run(
                "git_status", lambda: _op(started)
            )
            results[repo_path] = result.ok

        t1 = threading.Thread(target=_run, args=(repo_a, a_started))
        t2 = threading.Thread(target=_run, args=(repo_b, b_started))
        t1.start()
        t2.start()
        a_started.wait(timeout=5)
        b_started.wait(timeout=5)
        both_running.set()
        assert a_started.is_set() and b_started.is_set()
        release.set()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert results == {repo_a: True, repo_b: True}


# ── Stage 5b HEAD-identity drift rejection (REQ-006, AC-6, AC-7) ─────────────


class TestHeadDriftRejectionPerTool:
    @pytest.mark.parametrize("tool_name", ["git_pull", "git_push"])
    def test_head_drift_since_authorization_rejects_before_op(
        self, repo_a: str, tool_name: str
    ) -> None:
        state = RepositoryState.snapshot(repo_a)  # captured while attached
        repo = git.Repo(repo_a)
        repo.git.checkout(repo.head.commit.hexsha)  # detach after authorization

        op_called = False

        def _op() -> str:
            nonlocal op_called
            op_called = True
            return "should not run"

        result = WriteProtectionPipeline(state).run(tool_name, _op)
        assert result.ok is False
        assert result.rejected_at_stage == "Stage 5b"
        assert op_called is False
